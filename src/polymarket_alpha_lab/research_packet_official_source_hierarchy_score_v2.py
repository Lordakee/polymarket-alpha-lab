"""Pure in-memory official source hierarchy scoring for Phase 1 packets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_HIERARCHY_SCORE_V2_CONFIG_VERSION = (
    "research-packet-official-source-hierarchy-score-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE_COUNT = Decimal("1").quantize(COUNT_QUANTUM)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ONE_RATIO = Decimal("1").quantize(RATIO_QUANTUM)
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

OFFICIAL_PRIMARY_WEIGHT = Decimal("0.300000")
SECONDARY_SOURCE_WEIGHT = Decimal("0.150000")
INDEPENDENT_CONFIRMATION_WEIGHT = Decimal("0.200000")
FRESHNESS_WEIGHT = Decimal("0.100000")
CONTRADICTION_WEIGHT = Decimal("0.150000")
RESOLUTION_RULE_ALIGNMENT_WEIGHT = Decimal("0.100000")

SOURCE_ROLES = (
    "official_primary",
    "secondary",
    "independent_confirmation",
)
STATUSES = ("pass", "watch", "blocked")
STATUS_REASON_CODES = (
    "official_source_hierarchy_score_pass",
    "official_source_hierarchy_score_watch",
    "official_source_hierarchy_score_blocked",
)
DETAIL_REASON_CODES = (
    "missing_official_primary_source",
    "missing_secondary_source",
    "thin_independent_confirmations",
    "stale_hierarchy_source",
    "contradictory_hierarchy_source",
    "missing_resolution_rule_alignment",
)
EMPTY_REASON_CODE = "no_official_source_hierarchy_rows_supplied"
REASON_CODES = (EMPTY_REASON_CODE, *STATUS_REASON_CODES, *DETAIL_REASON_CODES)
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
UNSAFE_PUBLIC_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wa" "llet",
    "or" "der",
    "net" "work",
    "data" "base",
    "per" "sist",
    "sign" "ing",
    "muta" "tion",
    "bu" "y",
    "se" "ll",
    "tra" "de",
)
SHA256_HEX_LENGTH = 64


@dataclass(frozen=True)
class ResearchPacketOfficialSourceHierarchyScoreConfig:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_HIERARCHY_SCORE_V2_CONFIG_VERSION
    )
    max_source_age_seconds: Decimal = Decimal("259200.000000")
    minimum_independent_confirmation_count: Decimal = Decimal("2")
    pass_score_threshold: Decimal = Decimal("0.850000")
    block_score_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchPacketOfficialSourceHierarchyScoreConfig,
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_HIERARCHY_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_positive_seconds(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "minimum_independent_confirmation_count",
            _require_positive_count(
                "minimum_independent_confirmation_count",
                self.minimum_independent_confirmation_count,
            ),
        )
        for name in ("pass_score_threshold", "block_score_threshold"):
            object.__setattr__(self, name, _require_ratio(name, getattr(self, name)))
        _require_threshold_pair(
            "score",
            self.block_score_threshold,
            self.pass_score_threshold,
        )
        require_paper_only_flags(
            "ResearchPacketOfficialSourceHierarchyScoreConfig",
            self,
        )


@dataclass(frozen=True)
class ResearchPacketOfficialSourceHierarchyInput:
    packet_id: str
    event_id: str
    source_id: str
    source_role: str
    source_family: str
    source_title: str
    observed_at: datetime
    supports_resolution_rule: bool
    contradicts_resolution: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchPacketOfficialSourceHierarchyInput)
        for name in (
            "packet_id",
            "event_id",
            "source_id",
            "source_family",
            "source_title",
        ):
            _require_public_text(name, getattr(self, name))
        _require_source_role("source_role", self.source_role)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_bool("supports_resolution_rule", self.supports_resolution_rule)
        _require_bool("contradicts_resolution", self.contradicts_resolution)
        require_paper_only_flags("ResearchPacketOfficialSourceHierarchyInput", self)


@dataclass(frozen=True)
class ResearchPacketOfficialSourceHierarchyScoreRow:
    packet_id: str
    event_id: str
    source_count: Decimal
    official_primary_source_count: Decimal
    secondary_source_count: Decimal
    independent_confirmation_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    contradictory_source_count: Decimal
    resolution_rule_aligned_source_count: Decimal
    official_primary_score: Decimal
    secondary_source_score: Decimal
    independent_confirmation_score: Decimal
    freshness_score: Decimal
    contradiction_score: Decimal
    resolution_rule_alignment_score: Decimal
    hierarchy_score: Decimal
    score_band: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchPacketOfficialSourceHierarchyScoreRow)
        for name in ("packet_id", "event_id"):
            _require_public_text(name, getattr(self, name))
        for name in (
            "source_count",
            "official_primary_source_count",
            "secondary_source_count",
            "independent_confirmation_count",
            "fresh_source_count",
            "stale_source_count",
            "contradictory_source_count",
            "resolution_rule_aligned_source_count",
        ):
            object.__setattr__(self, name, _require_nonnegative_count(name, getattr(self, name)))
        for name in (
            "official_primary_score",
            "secondary_source_score",
            "independent_confirmation_score",
            "freshness_score",
            "contradiction_score",
            "resolution_rule_alignment_score",
            "hierarchy_score",
        ):
            object.__setattr__(self, name, _require_ratio(name, getattr(self, name)))
        _require_member("score_band", self.score_band, STATUSES)
        object.__setattr__(self, "reason_codes", _require_reason_codes(self.reason_codes))
        require_paper_only_flags("ResearchPacketOfficialSourceHierarchyScoreRow", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketOfficialSourceHierarchyScoreReport:
    generated_at: datetime
    config_version: str
    status: str
    packet_count: Decimal
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    missing_official_primary_source_count: Decimal
    missing_secondary_source_count: Decimal
    thin_independent_confirmation_count: Decimal
    stale_source_count: Decimal
    contradictory_source_count: Decimal
    missing_resolution_rule_alignment_count: Decimal
    average_hierarchy_score: Decimal
    min_hierarchy_score: Decimal
    max_hierarchy_score: Decimal
    rows: tuple[ResearchPacketOfficialSourceHierarchyScoreRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchPacketOfficialSourceHierarchyScoreReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_HIERARCHY_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_member("status", self.status, STATUSES)
        for name in (
            "packet_count",
            "source_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "missing_official_primary_source_count",
            "missing_secondary_source_count",
            "thin_independent_confirmation_count",
            "stale_source_count",
            "contradictory_source_count",
            "missing_resolution_rule_alignment_count",
        ):
            object.__setattr__(self, name, _require_nonnegative_count(name, getattr(self, name)))
        for name in (
            "average_hierarchy_score",
            "min_hierarchy_score",
            "max_hierarchy_score",
        ):
            object.__setattr__(self, name, _require_ratio(name, getattr(self, name)))
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(self, "reason_codes", _require_reason_codes(self.reason_codes))
        require_paper_only_flags("ResearchPacketOfficialSourceHierarchyScoreReport", self)
        _validate_report(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                DERIVED_VALIDATION_DIGEST_FIELD,
                self.derived_validation_digest,
            )
            _validate_report_derived_validation_digest(self)


def build_research_packet_official_source_hierarchy_score_v2_report(
    rows: object,
    *,
    config: ResearchPacketOfficialSourceHierarchyScoreConfig,
    generated_at: datetime,
) -> ResearchPacketOfficialSourceHierarchyScoreReport:
    if type(config) is not ResearchPacketOfficialSourceHierarchyScoreConfig:
        raise ValueError("config must be a ResearchPacketOfficialSourceHierarchyScoreConfig")
    require_paper_only_flags("ResearchPacketOfficialSourceHierarchyScoreConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_source_rows(rows)
    _validate_source_times(source_rows, generated_at_utc)
    score_rows = tuple(
        _score_packet(
            packet_rows,
            config=config,
            generated_at=generated_at_utc,
        )
        for packet_rows in _packet_groups(source_rows)
    )
    reason_codes = _report_reason_codes(score_rows, len(source_rows))
    return ResearchPacketOfficialSourceHierarchyScoreReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(reason_codes),
        packet_count=_count(len(score_rows)),
        source_count=_count(len(source_rows)),
        pass_count=_band_count(score_rows, "pass"),
        watch_count=_band_count(score_rows, "watch"),
        blocked_count=_band_count(score_rows, "blocked"),
        missing_official_primary_source_count=_reason_count(
            score_rows,
            "missing_official_primary_source",
        ),
        missing_secondary_source_count=_reason_count(score_rows, "missing_secondary_source"),
        thin_independent_confirmation_count=_reason_count(
            score_rows,
            "thin_independent_confirmations",
        ),
        stale_source_count=_row_count_total(score_rows, "stale_source_count"),
        contradictory_source_count=_row_count_total(score_rows, "contradictory_source_count"),
        missing_resolution_rule_alignment_count=_reason_count(
            score_rows,
            "missing_resolution_rule_alignment",
        ),
        average_hierarchy_score=_average_hierarchy_score(score_rows),
        min_hierarchy_score=_min_hierarchy_score(score_rows),
        max_hierarchy_score=_max_hierarchy_score(score_rows),
        rows=score_rows,
        reason_codes=reason_codes,
    )


def research_packet_official_source_hierarchy_score_v2_payload(
    report: ResearchPacketOfficialSourceHierarchyScoreReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketOfficialSourceHierarchyScoreReport:
        require_paper_only_flags("ResearchPacketOfficialSourceHierarchyScoreReport", report)
        _validate_report_derived_validation_digest(report)
        payload = json_ready_no_floats(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_public_payload(payload)
        return payload
    if type(report) is dict:
        _validate_public_payload(report)
        return report
    raise ValueError("report must be a ResearchPacketOfficialSourceHierarchyScoreReport or payload")


def _score_packet(
    rows: tuple[ResearchPacketOfficialSourceHierarchyInput, ...],
    *,
    config: ResearchPacketOfficialSourceHierarchyScoreConfig,
    generated_at: datetime,
) -> ResearchPacketOfficialSourceHierarchyScoreRow:
    if not rows:
        raise ValueError("packet rows must not be empty")
    packet_id = rows[0].packet_id
    event_id = rows[0].event_id
    source_count = _count(len(rows))
    official_primary_source_count = _count(
        sum(1 for row in rows if row.source_role == "official_primary"),
    )
    secondary_source_count = _count(sum(1 for row in rows if row.source_role == "secondary"))
    independent_confirmation_count = _count(
        len(
            {
                row.source_family
                for row in rows
                if row.source_role == "independent_confirmation"
            },
        ),
    )
    stale_source_count = _count(
        sum(
            1
            for row in rows
            if _duration_seconds(row.observed_at, generated_at) > config.max_source_age_seconds
        ),
    )
    fresh_source_count = source_count - stale_source_count
    contradictory_source_count = _count(sum(1 for row in rows if row.contradicts_resolution))
    resolution_rule_aligned_source_count = _count(
        sum(
            1
            for row in rows
            if row.source_role == "official_primary" and row.supports_resolution_rule
        ),
    )
    official_primary_score = ONE_RATIO if official_primary_source_count > ZERO_COUNT else ZERO_RATIO
    secondary_source_score = ONE_RATIO if secondary_source_count > ZERO_COUNT else ZERO_RATIO
    independent_confirmation_score = min(
        ONE_RATIO,
        _ratio(
            independent_confirmation_count,
            config.minimum_independent_confirmation_count,
        ),
    )
    freshness_score = _ratio(fresh_source_count, source_count)
    contradiction_score = _ratio(source_count - contradictory_source_count, source_count)
    resolution_rule_alignment_score = (
        ONE_RATIO if resolution_rule_aligned_source_count > ZERO_COUNT else ZERO_RATIO
    )
    hierarchy_score = _hierarchy_score(
        official_primary_score=official_primary_score,
        secondary_source_score=secondary_source_score,
        independent_confirmation_score=independent_confirmation_score,
        freshness_score=freshness_score,
        contradiction_score=contradiction_score,
        resolution_rule_alignment_score=resolution_rule_alignment_score,
    )
    detail_reasons = _row_detail_reasons(
        official_primary_source_count=official_primary_source_count,
        secondary_source_count=secondary_source_count,
        independent_confirmation_count=independent_confirmation_count,
        stale_source_count=stale_source_count,
        contradictory_source_count=contradictory_source_count,
        resolution_rule_aligned_source_count=resolution_rule_aligned_source_count,
        config=config,
    )
    score_band = _score_band(
        hierarchy_score=hierarchy_score,
        detail_reasons=detail_reasons,
        config=config,
    )
    return ResearchPacketOfficialSourceHierarchyScoreRow(
        packet_id=packet_id,
        event_id=event_id,
        source_count=source_count,
        official_primary_source_count=official_primary_source_count,
        secondary_source_count=secondary_source_count,
        independent_confirmation_count=independent_confirmation_count,
        fresh_source_count=fresh_source_count,
        stale_source_count=stale_source_count,
        contradictory_source_count=contradictory_source_count,
        resolution_rule_aligned_source_count=resolution_rule_aligned_source_count,
        official_primary_score=official_primary_score,
        secondary_source_score=secondary_source_score,
        independent_confirmation_score=independent_confirmation_score,
        freshness_score=freshness_score,
        contradiction_score=contradiction_score,
        resolution_rule_alignment_score=resolution_rule_alignment_score,
        hierarchy_score=hierarchy_score,
        score_band=score_band,
        reason_codes=(f"official_source_hierarchy_score_{score_band}", *detail_reasons),
    )


def _row_detail_reasons(
    *,
    official_primary_source_count: Decimal,
    secondary_source_count: Decimal,
    independent_confirmation_count: Decimal,
    stale_source_count: Decimal,
    contradictory_source_count: Decimal,
    resolution_rule_aligned_source_count: Decimal,
    config: ResearchPacketOfficialSourceHierarchyScoreConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if official_primary_source_count == ZERO_COUNT:
        reasons.append("missing_official_primary_source")
    if secondary_source_count == ZERO_COUNT:
        reasons.append("missing_secondary_source")
    if independent_confirmation_count < config.minimum_independent_confirmation_count:
        reasons.append("thin_independent_confirmations")
    if stale_source_count > ZERO_COUNT:
        reasons.append("stale_hierarchy_source")
    if contradictory_source_count > ZERO_COUNT:
        reasons.append("contradictory_hierarchy_source")
    if resolution_rule_aligned_source_count == ZERO_COUNT:
        reasons.append("missing_resolution_rule_alignment")
    return tuple(reasons)


def _score_band(
    *,
    hierarchy_score: Decimal,
    detail_reasons: tuple[str, ...],
    config: ResearchPacketOfficialSourceHierarchyScoreConfig,
) -> str:
    if not detail_reasons and hierarchy_score >= config.pass_score_threshold:
        return "pass"
    if (
        "missing_official_primary_source" in detail_reasons
        or "contradictory_hierarchy_source" in detail_reasons
        or "missing_resolution_rule_alignment" in detail_reasons
        or hierarchy_score < config.block_score_threshold
    ):
        return "blocked"
    return "watch"


def _hierarchy_score(
    *,
    official_primary_score: Decimal,
    secondary_source_score: Decimal,
    independent_confirmation_score: Decimal,
    freshness_score: Decimal,
    contradiction_score: Decimal,
    resolution_rule_alignment_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            official_primary_score * OFFICIAL_PRIMARY_WEIGHT
            + secondary_source_score * SECONDARY_SOURCE_WEIGHT
            + independent_confirmation_score * INDEPENDENT_CONFIRMATION_WEIGHT
            + freshness_score * FRESHNESS_WEIGHT
            + contradiction_score * CONTRADICTION_WEIGHT
            + resolution_rule_alignment_score * RESOLUTION_RULE_ALIGNMENT_WEIGHT
        ).quantize(RATIO_QUANTUM)


def _normalize_source_rows(
    rows: object,
) -> tuple[ResearchPacketOfficialSourceHierarchyInput, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchPacketOfficialSourceHierarchyInput:
            raise ValueError("rows must contain ResearchPacketOfficialSourceHierarchyInput values")
        require_paper_only_flags("ResearchPacketOfficialSourceHierarchyInput", row)
        key = (row.packet_id, row.source_id)
        if key in seen:
            raise ValueError("rows must be unique by packet_id and source_id")
        seen.add(key)
    return tuple(sorted(normalized, key=_source_row_key))


def _packet_groups(
    rows: tuple[ResearchPacketOfficialSourceHierarchyInput, ...],
) -> tuple[tuple[ResearchPacketOfficialSourceHierarchyInput, ...], ...]:
    packet_ids = tuple(sorted({row.packet_id for row in rows}))
    groups: list[tuple[ResearchPacketOfficialSourceHierarchyInput, ...]] = []
    for packet_id in packet_ids:
        packet_rows = tuple(row for row in rows if row.packet_id == packet_id)
        event_ids = {row.event_id for row in packet_rows}
        if len(event_ids) != 1:
            raise ValueError("rows for a packet must share one event_id")
        groups.append(packet_rows)
    return tuple(groups)


def _source_row_key(row: ResearchPacketOfficialSourceHierarchyInput) -> tuple[str, int, str]:
    return (row.packet_id, SOURCE_ROLES.index(row.source_role), row.source_id)


def _validate_source_times(
    rows: tuple[ResearchPacketOfficialSourceHierarchyInput, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _report_reason_codes(
    rows: tuple[ResearchPacketOfficialSourceHierarchyScoreRow, ...],
    source_row_count: int,
) -> tuple[str, ...]:
    if source_row_count == 0:
        return (EMPTY_REASON_CODE,)
    status = _rollup_status(rows)
    if status == "pass":
        return ("official_source_hierarchy_score_pass",)
    detail_reasons = tuple(
        reason
        for reason in DETAIL_REASON_CODES
        if any(reason in row.reason_codes for row in rows)
    )
    return (f"official_source_hierarchy_score_{status}", *detail_reasons)


def _rollup_status(rows: tuple[ResearchPacketOfficialSourceHierarchyScoreRow, ...]) -> str:
    if any(row.score_band == "blocked" for row in rows):
        return "blocked"
    if any(row.score_band == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == EMPTY_REASON_CODE:
        return "blocked"
    if reason_codes[0] == "official_source_hierarchy_score_blocked":
        return "blocked"
    if reason_codes[0] == "official_source_hierarchy_score_watch":
        return "watch"
    return "pass"


def _band_count(
    rows: tuple[ResearchPacketOfficialSourceHierarchyScoreRow, ...],
    band: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.score_band == band))


def _reason_count(
    rows: tuple[ResearchPacketOfficialSourceHierarchyScoreRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _row_count_total(
    rows: tuple[ResearchPacketOfficialSourceHierarchyScoreRow, ...],
    field_name: str,
) -> Decimal:
    return _count(sum(int(getattr(row, field_name)) for row in rows))


def _average_hierarchy_score(
    rows: tuple[ResearchPacketOfficialSourceHierarchyScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (
            sum((row.hierarchy_score for row in rows), ZERO_RATIO) / Decimal(len(rows))
        ).quantize(RATIO_QUANTUM)


def _min_hierarchy_score(
    rows: tuple[ResearchPacketOfficialSourceHierarchyScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return min(row.hierarchy_score for row in rows)


def _max_hierarchy_score(
    rows: tuple[ResearchPacketOfficialSourceHierarchyScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(row.hierarchy_score for row in rows)


def _require_rows(
    value: object,
) -> tuple[ResearchPacketOfficialSourceHierarchyScoreRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketOfficialSourceHierarchyScoreRow:
            raise ValueError("rows must contain ResearchPacketOfficialSourceHierarchyScoreRow values")
        require_paper_only_flags("ResearchPacketOfficialSourceHierarchyScoreRow", row)
        if row.packet_id in seen:
            raise ValueError("rows must be unique by packet_id")
        seen.add(row.packet_id)
    if rows != tuple(sorted(rows, key=lambda row: row.packet_id)):
        raise ValueError("rows must use deterministic packet sequence")
    return rows


def _validate_row(row: ResearchPacketOfficialSourceHierarchyScoreRow) -> None:
    if row.source_count == ZERO_COUNT:
        raise ValueError("source_count must be positive")
    detail_reasons = tuple(reason for reason in row.reason_codes if reason in DETAIL_REASON_CODES)
    if row.reason_codes[0] != f"official_source_hierarchy_score_{row.score_band}":
        raise ValueError("reason_codes must match score_band")
    if row.score_band == "pass" and detail_reasons:
        raise ValueError("pass rows must not include detail reason codes")
    if row.score_band != "pass" and not detail_reasons:
        raise ValueError("non-pass rows must include detail reason codes")
    if row.fresh_source_count + row.stale_source_count != row.source_count:
        raise ValueError("fresh_source_count and stale_source_count must match source_count")


def _validate_report(report: ResearchPacketOfficialSourceHierarchyScoreReport) -> None:
    if report.packet_count != _count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.source_count != _row_count_total(report.rows, "source_count"):
        raise ValueError("source_count must match rows")
    expected_counts = {
        "pass_count": _band_count(report.rows, "pass"),
        "watch_count": _band_count(report.rows, "watch"),
        "blocked_count": _band_count(report.rows, "blocked"),
        "missing_official_primary_source_count": _reason_count(
            report.rows,
            "missing_official_primary_source",
        ),
        "missing_secondary_source_count": _reason_count(
            report.rows,
            "missing_secondary_source",
        ),
        "thin_independent_confirmation_count": _reason_count(
            report.rows,
            "thin_independent_confirmations",
        ),
        "stale_source_count": _row_count_total(report.rows, "stale_source_count"),
        "contradictory_source_count": _row_count_total(
            report.rows,
            "contradictory_source_count",
        ),
        "missing_resolution_rule_alignment_count": _reason_count(
            report.rows,
            "missing_resolution_rule_alignment",
        ),
    }
    for name, expected in expected_counts.items():
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")
    if report.average_hierarchy_score != _average_hierarchy_score(report.rows):
        raise ValueError("average_hierarchy_score must match rows")
    if report.min_hierarchy_score != _min_hierarchy_score(report.rows):
        raise ValueError("min_hierarchy_score must match rows")
    if report.max_hierarchy_score != _max_hierarchy_score(report.rows):
        raise ValueError("max_hierarchy_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.source_count)):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_derived_validation_digest(
    report: ResearchPacketOfficialSourceHierarchyScoreReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _report_derived_validation_digest(
    report: ResearchPacketOfficialSourceHierarchyScoreReport,
) -> str:
    return _public_payload_derived_validation_digest(_public_payload_for_digest(report))


def _public_payload_for_digest(
    report: ResearchPacketOfficialSourceHierarchyScoreReport,
) -> dict[str, Any]:
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop(DERIVED_VALIDATION_DIGEST_FIELD, None)
    return payload


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop(DERIVED_VALIDATION_DIGEST_FIELD, None)
    encoded = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload(payload)
    _require_public_payload_flags(payload)
    digest_value = payload.get(DERIVED_VALIDATION_DIGEST_FIELD)
    _require_sha256_digest(DERIVED_VALIDATION_DIGEST_FIELD, digest_value)
    expected = _public_payload_derived_validation_digest(payload)
    if digest_value != expected:
        raise ValueError("derived_validation_digest must match public payload")


def _reject_unsafe_public_payload(value: Any) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text("public key", key)
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_public_text("public value", value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        _decimal("public Decimal value", value)
        return
    raise ValueError("public payload value is not supported")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe {label}: {value}")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for flag in HARD_FLAG_FIELDS:
        if payload.get(flag) is not True:
            raise ValueError(f"{flag} must be True for public payload")
    _require_nested_public_payload_flags(payload)


def _require_nested_public_payload_flags(value: Any) -> None:
    if isinstance(value, dict):
        if any(flag in value for flag in HARD_FLAG_FIELDS):
            for flag in HARD_FLAG_FIELDS:
                if value.get(flag) is not True:
                    raise ValueError(f"{flag} must be True for public payload")
        for item in value.values():
            _require_nested_public_payload_flags(item)
    elif isinstance(value, list):
        for item in value:
            _require_nested_public_payload_flags(item)


def _duration_seconds(started_at: datetime, generated_at: datetime) -> Decimal:
    delta = _as_utc("generated_at", generated_at) - _as_utc("started_at", started_at)
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        ).quantize(SECONDS_QUANTUM)
    if seconds < ZERO_COUNT:
        raise ValueError("source_age_seconds must be nonnegative")
    return seconds


def _ratio(part: Decimal, whole: Decimal) -> Decimal:
    if whole == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (part / whole).quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_threshold_pair(name: str, lower: Decimal, upper: Decimal) -> None:
    if lower > upper:
        raise ValueError(f"{name} lower threshold must be at most upper threshold")


def _require_exact_type(name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be a {expected_type.__name__}")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_source_role(name: str, value: object) -> None:
    _require_public_text(name, value)
    _require_member(name, value, SOURCE_ROLES)


def _require_member(name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in choices:
        raise ValueError(f"{name} must be one of {choices}")


def _require_positive_seconds(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_seconds(name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_nonnegative_seconds(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value).quantize(SECONDS_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_positive_count(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count(name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{name} must be an integral Decimal")
    return normalized


def _require_ratio(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{name} must be between zero and one")
    return normalized


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return +value


def _require_public_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{name} must be single line")
    _reject_unsafe_public_text("public value", value)


def _require_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason in reason_codes:
        _require_member("reason_code", reason, REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    expected_sequence = tuple(reason for reason in REASON_CODES if reason in reason_codes)
    if reason_codes != expected_sequence:
        raise ValueError("reason_codes must use deterministic sequence")
    return reason_codes


def _require_sha256_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_HIERARCHY_SCORE_V2_CONFIG_VERSION",
    "ResearchPacketOfficialSourceHierarchyInput",
    "ResearchPacketOfficialSourceHierarchyScoreConfig",
    "ResearchPacketOfficialSourceHierarchyScoreReport",
    "ResearchPacketOfficialSourceHierarchyScoreRow",
    "build_research_packet_official_source_hierarchy_score_v2_report",
    "research_packet_official_source_hierarchy_score_v2_payload",
)
