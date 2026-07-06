"""Read-only official source anchor score report for research packets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_ANCHOR_SCORE_V2_CONFIG_VERSION = (
    "research-packet-official-source-anchor-score-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ONE_RATIO = Decimal("1").quantize(RATIO_QUANTUM)
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

OFFICIAL_STRENGTH_WEIGHT = Decimal("0.250000")
RESOLUTION_RELEVANCE_WEIGHT = Decimal("0.250000")
FRESHNESS_WEIGHT = Decimal("0.100000")
SOURCE_FAMILY_INDEPENDENCE_WEIGHT = Decimal("0.150000")
AMBIGUITY_COVERAGE_WEIGHT = Decimal("0.100000")
CONTRADICTION_HANDLING_WEIGHT = Decimal("0.150000")

STATUSES = ("pass", "watch", "blocked")
ROW_STATUS_RANK = {
    "blocked": 0,
    "watch": 1,
    "pass": 2,
}
STATUS_REASON_CODES = (
    "official_source_anchor_score_pass",
    "official_source_anchor_score_watch",
    "official_source_anchor_score_blocked",
)
DETAIL_REASON_CODES = (
    "low_official_strength",
    "low_resolution_relevance",
    "stale_source_anchor",
    "thin_source_family_independence",
    "thin_ambiguity_coverage",
    "weak_contradiction_handling",
)
EMPTY_REASON_CODE = "no_official_source_anchor_rows_supplied"
REASON_CODES = (EMPTY_REASON_CODE, *STATUS_REASON_CODES, *DETAIL_REASON_CODES)
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
UNSAFE_PUBLIC_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
SHA256_HEX_LENGTH = 64


@dataclass(frozen=True)
class ResearchPacketOfficialSourceAnchorScoreConfig:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_ANCHOR_SCORE_V2_CONFIG_VERSION
    )
    max_source_age_seconds: Decimal = Decimal("288000.000000")
    official_strength_watch_threshold: Decimal = Decimal("0.750000")
    official_strength_block_threshold: Decimal = Decimal("0.500000")
    resolution_relevance_watch_threshold: Decimal = Decimal("0.750000")
    resolution_relevance_block_threshold: Decimal = Decimal("0.500000")
    min_source_family_independence: Decimal = Decimal("0.500000")
    ambiguity_coverage_watch_threshold: Decimal = Decimal("0.750000")
    ambiguity_coverage_block_threshold: Decimal = Decimal("0.500000")
    contradiction_handling_watch_threshold: Decimal = Decimal("0.750000")
    contradiction_handling_block_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchPacketOfficialSourceAnchorScoreConfig,
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_ANCHOR_SCORE_V2_CONFIG_VERSION
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
        for name in (
            "official_strength_watch_threshold",
            "official_strength_block_threshold",
            "resolution_relevance_watch_threshold",
            "resolution_relevance_block_threshold",
            "min_source_family_independence",
            "ambiguity_coverage_watch_threshold",
            "ambiguity_coverage_block_threshold",
            "contradiction_handling_watch_threshold",
            "contradiction_handling_block_threshold",
        ):
            object.__setattr__(self, name, _require_ratio(name, getattr(self, name)))
        _require_ordered_thresholds(
            "official_strength",
            self.official_strength_block_threshold,
            self.official_strength_watch_threshold,
        )
        _require_ordered_thresholds(
            "resolution_relevance",
            self.resolution_relevance_block_threshold,
            self.resolution_relevance_watch_threshold,
        )
        _require_ordered_thresholds(
            "ambiguity_coverage",
            self.ambiguity_coverage_block_threshold,
            self.ambiguity_coverage_watch_threshold,
        )
        _require_ordered_thresholds(
            "contradiction_handling",
            self.contradiction_handling_block_threshold,
            self.contradiction_handling_watch_threshold,
        )
        require_paper_only_flags(
            "ResearchPacketOfficialSourceAnchorScoreConfig",
            self,
        )


@dataclass(frozen=True)
class ResearchPacketOfficialSourceAnchorInput:
    packet_id: str
    event_id: str
    anchor_id: str
    source_family: str
    source_title: str
    observed_at: datetime
    official_strength_score: Decimal
    resolution_relevance: Decimal
    ambiguity_coverage: Decimal
    contradiction_handling: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchPacketOfficialSourceAnchorInput)
        for name in (
            "packet_id",
            "event_id",
            "anchor_id",
            "source_family",
            "source_title",
        ):
            _require_public_text(name, getattr(self, name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in (
            "official_strength_score",
            "resolution_relevance",
            "ambiguity_coverage",
            "contradiction_handling",
        ):
            object.__setattr__(self, name, _require_ratio(name, getattr(self, name)))
        require_paper_only_flags("ResearchPacketOfficialSourceAnchorInput", self)


@dataclass(frozen=True)
class ResearchPacketOfficialSourceAnchorScoreRow:
    packet_id: str
    event_id: str
    anchor_id: str
    source_family: str
    source_title: str
    observed_at: datetime
    source_age_seconds: Decimal
    official_strength_score: Decimal
    resolution_relevance: Decimal
    freshness_score: Decimal
    source_family_independence: Decimal
    ambiguity_coverage: Decimal
    contradiction_handling: Decimal
    anchor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchPacketOfficialSourceAnchorScoreRow)
        for name in (
            "packet_id",
            "event_id",
            "anchor_id",
            "source_family",
            "source_title",
        ):
            _require_public_text(name, getattr(self, name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_seconds("source_age_seconds", self.source_age_seconds),
        )
        for name in (
            "official_strength_score",
            "resolution_relevance",
            "freshness_score",
            "source_family_independence",
            "ambiguity_coverage",
            "contradiction_handling",
            "anchor_score",
        ):
            object.__setattr__(self, name, _require_ratio(name, getattr(self, name)))
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("ResearchPacketOfficialSourceAnchorScoreRow", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketOfficialSourceAnchorScoreReport:
    generated_at: datetime
    config_version: str
    status: str
    anchor_count: Decimal
    packet_count: Decimal
    event_count: Decimal
    source_family_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    low_official_strength_count: Decimal
    low_resolution_relevance_count: Decimal
    stale_anchor_count: Decimal
    thin_source_family_independence_count: Decimal
    ambiguity_gap_count: Decimal
    contradiction_handling_gap_count: Decimal
    average_anchor_score: Decimal
    min_anchor_score: Decimal
    max_anchor_score: Decimal
    max_source_age_seconds: Decimal
    rows: tuple[ResearchPacketOfficialSourceAnchorScoreRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchPacketOfficialSourceAnchorScoreReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_ANCHOR_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_member("status", self.status, STATUSES)
        for name in (
            "anchor_count",
            "packet_count",
            "event_count",
            "source_family_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "low_official_strength_count",
            "low_resolution_relevance_count",
            "stale_anchor_count",
            "thin_source_family_independence_count",
            "ambiguity_gap_count",
            "contradiction_handling_gap_count",
        ):
            object.__setattr__(self, name, _require_nonnegative_count(name, getattr(self, name)))
        for name in ("average_anchor_score", "min_anchor_score", "max_anchor_score"):
            object.__setattr__(self, name, _require_ratio(name, getattr(self, name)))
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_nonnegative_seconds(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("ResearchPacketOfficialSourceAnchorScoreReport", self)
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


def build_research_packet_official_source_anchor_score_v2_report(
    rows: object,
    *,
    config: ResearchPacketOfficialSourceAnchorScoreConfig,
    generated_at: datetime,
) -> ResearchPacketOfficialSourceAnchorScoreReport:
    if type(config) is not ResearchPacketOfficialSourceAnchorScoreConfig:
        raise ValueError("config must be a ResearchPacketOfficialSourceAnchorScoreConfig")
    require_paper_only_flags("ResearchPacketOfficialSourceAnchorScoreConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_source_rows(rows)
    _validate_source_times(source_rows, generated_at_utc)
    score_rows = tuple(
        _score_row(
            row,
            config=config,
            generated_at=generated_at_utc,
            source_rows=source_rows,
        )
        for row in source_rows
    )
    reason_codes = _report_reason_codes(score_rows, len(source_rows))

    return ResearchPacketOfficialSourceAnchorScoreReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(reason_codes),
        anchor_count=_count(len(source_rows)),
        packet_count=_count(len({row.packet_id for row in source_rows})),
        event_count=_count(len({row.event_id for row in source_rows})),
        source_family_count=_count(len({row.source_family for row in source_rows})),
        pass_count=_status_count(score_rows, "pass"),
        watch_count=_status_count(score_rows, "watch"),
        blocked_count=_status_count(score_rows, "blocked"),
        low_official_strength_count=_reason_count(
            score_rows,
            "low_official_strength",
        ),
        low_resolution_relevance_count=_reason_count(
            score_rows,
            "low_resolution_relevance",
        ),
        stale_anchor_count=_reason_count(score_rows, "stale_source_anchor"),
        thin_source_family_independence_count=_reason_count(
            score_rows,
            "thin_source_family_independence",
        ),
        ambiguity_gap_count=_reason_count(score_rows, "thin_ambiguity_coverage"),
        contradiction_handling_gap_count=_reason_count(
            score_rows,
            "weak_contradiction_handling",
        ),
        average_anchor_score=_average_anchor_score(score_rows),
        min_anchor_score=_min_anchor_score(score_rows),
        max_anchor_score=_max_anchor_score(score_rows),
        max_source_age_seconds=_max_source_age_seconds(score_rows),
        rows=score_rows,
        reason_codes=reason_codes,
    )


def research_packet_official_source_anchor_score_v2_payload(
    report: ResearchPacketOfficialSourceAnchorScoreReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketOfficialSourceAnchorScoreReport:
        require_paper_only_flags("ResearchPacketOfficialSourceAnchorScoreReport", report)
        _validate_report_derived_validation_digest(report)
        payload = json_ready_no_floats(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_public_payload(payload)
        return payload
    if type(report) is dict:
        _validate_public_payload(report)
        return report
    raise ValueError("report must be a ResearchPacketOfficialSourceAnchorScoreReport or payload")


def _normalize_source_rows(
    rows: object,
) -> tuple[ResearchPacketOfficialSourceAnchorInput, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchPacketOfficialSourceAnchorInput:
            raise ValueError("rows must contain ResearchPacketOfficialSourceAnchorInput values")
        require_paper_only_flags("ResearchPacketOfficialSourceAnchorInput", row)
        key = (row.packet_id, row.anchor_id)
        if key in seen:
            raise ValueError("rows must be unique by packet_id and anchor_id")
        seen.add(key)
    return normalized


def _validate_source_times(
    rows: tuple[ResearchPacketOfficialSourceAnchorInput, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _score_row(
    row: ResearchPacketOfficialSourceAnchorInput,
    *,
    config: ResearchPacketOfficialSourceAnchorScoreConfig,
    generated_at: datetime,
    source_rows: tuple[ResearchPacketOfficialSourceAnchorInput, ...],
) -> ResearchPacketOfficialSourceAnchorScoreRow:
    source_age_seconds = _duration_seconds(row.observed_at, generated_at)
    freshness_score = _freshness_score(source_age_seconds, config.max_source_age_seconds)
    source_family_independence = _source_family_independence(row, source_rows)
    anchor_score = _anchor_score(
        official_strength_score=row.official_strength_score,
        resolution_relevance=row.resolution_relevance,
        freshness_score=freshness_score,
        source_family_independence=source_family_independence,
        ambiguity_coverage=row.ambiguity_coverage,
        contradiction_handling=row.contradiction_handling,
    )
    reason_codes = _row_reason_codes(
        row,
        config=config,
        source_age_seconds=source_age_seconds,
        source_family_independence=source_family_independence,
    )
    return ResearchPacketOfficialSourceAnchorScoreRow(
        packet_id=row.packet_id,
        event_id=row.event_id,
        anchor_id=row.anchor_id,
        source_family=row.source_family,
        source_title=row.source_title,
        observed_at=row.observed_at,
        source_age_seconds=source_age_seconds,
        official_strength_score=row.official_strength_score,
        resolution_relevance=row.resolution_relevance,
        freshness_score=freshness_score,
        source_family_independence=source_family_independence,
        ambiguity_coverage=row.ambiguity_coverage,
        contradiction_handling=row.contradiction_handling,
        anchor_score=anchor_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchPacketOfficialSourceAnchorInput,
    *,
    config: ResearchPacketOfficialSourceAnchorScoreConfig,
    source_age_seconds: Decimal,
    source_family_independence: Decimal,
) -> tuple[str, ...]:
    detail_reasons: list[str] = []
    if row.official_strength_score < config.official_strength_watch_threshold:
        detail_reasons.append("low_official_strength")
    if row.resolution_relevance < config.resolution_relevance_watch_threshold:
        detail_reasons.append("low_resolution_relevance")
    if source_age_seconds > config.max_source_age_seconds:
        detail_reasons.append("stale_source_anchor")
    if source_family_independence < config.min_source_family_independence:
        detail_reasons.append("thin_source_family_independence")
    if row.ambiguity_coverage < config.ambiguity_coverage_watch_threshold:
        detail_reasons.append("thin_ambiguity_coverage")
    if row.contradiction_handling < config.contradiction_handling_watch_threshold:
        detail_reasons.append("weak_contradiction_handling")
    status = _status_from_detail_reasons(row, config, tuple(detail_reasons))
    return (f"official_source_anchor_score_{status}", *detail_reasons)


def _status_from_detail_reasons(
    row: ResearchPacketOfficialSourceAnchorInput,
    config: ResearchPacketOfficialSourceAnchorScoreConfig,
    detail_reasons: tuple[str, ...],
) -> str:
    if not detail_reasons:
        return "pass"
    if (
        row.official_strength_score < config.official_strength_block_threshold
        or row.resolution_relevance < config.resolution_relevance_block_threshold
        or row.ambiguity_coverage < config.ambiguity_coverage_block_threshold
        or row.contradiction_handling < config.contradiction_handling_block_threshold
        or "stale_source_anchor" in detail_reasons
    ):
        return "blocked"
    return "watch"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == "official_source_anchor_score_blocked":
        return "blocked"
    if reason_codes[0] == "official_source_anchor_score_watch":
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketOfficialSourceAnchorScoreRow, ...],
    source_row_count: int,
) -> tuple[str, ...]:
    if source_row_count == 0:
        return (EMPTY_REASON_CODE,)
    status = _rollup_status(rows)
    if status == "pass":
        return ("official_source_anchor_score_pass",)
    details = tuple(
        reason
        for reason in DETAIL_REASON_CODES
        if any(reason in row.reason_codes for row in rows)
    )
    return (f"official_source_anchor_score_{status}", *details)


def _rollup_status(rows: tuple[ResearchPacketOfficialSourceAnchorScoreRow, ...]) -> str:
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == "official_source_anchor_score_blocked":
        return "blocked"
    if reason_codes[0] == "official_source_anchor_score_watch":
        return "watch"
    return "pass"


def _source_family_independence(
    row: ResearchPacketOfficialSourceAnchorInput,
    rows: tuple[ResearchPacketOfficialSourceAnchorInput, ...],
) -> Decimal:
    family_count = sum(
        1
        for candidate in rows
        if candidate.packet_id == row.packet_id
        and candidate.source_family == row.source_family
    )
    if family_count <= 0:
        raise ValueError("source family count must be positive")
    return _ratio(Decimal("1"), Decimal(family_count))


def _freshness_score(source_age_seconds: Decimal, max_source_age_seconds: Decimal) -> Decimal:
    if source_age_seconds >= max_source_age_seconds:
        return ZERO_RATIO
    return _ratio(max_source_age_seconds - source_age_seconds, max_source_age_seconds)


def _anchor_score(
    *,
    official_strength_score: Decimal,
    resolution_relevance: Decimal,
    freshness_score: Decimal,
    source_family_independence: Decimal,
    ambiguity_coverage: Decimal,
    contradiction_handling: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            official_strength_score * OFFICIAL_STRENGTH_WEIGHT
            + resolution_relevance * RESOLUTION_RELEVANCE_WEIGHT
            + freshness_score * FRESHNESS_WEIGHT
            + source_family_independence * SOURCE_FAMILY_INDEPENDENCE_WEIGHT
            + ambiguity_coverage * AMBIGUITY_COVERAGE_WEIGHT
            + contradiction_handling * CONTRADICTION_HANDLING_WEIGHT
        ).quantize(RATIO_QUANTUM)


def _status_count(
    rows: tuple[ResearchPacketOfficialSourceAnchorScoreRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchPacketOfficialSourceAnchorScoreRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_anchor_score(
    rows: tuple[ResearchPacketOfficialSourceAnchorScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (
            sum((row.anchor_score for row in rows), ZERO_RATIO) / Decimal(len(rows))
        ).quantize(RATIO_QUANTUM)


def _min_anchor_score(rows: tuple[ResearchPacketOfficialSourceAnchorScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return min(row.anchor_score for row in rows)


def _max_anchor_score(rows: tuple[ResearchPacketOfficialSourceAnchorScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(row.anchor_score for row in rows)


def _max_source_age_seconds(
    rows: tuple[ResearchPacketOfficialSourceAnchorScoreRow, ...],
) -> Decimal:
    if not rows:
        return Decimal("0").quantize(SECONDS_QUANTUM)
    return max(row.source_age_seconds for row in rows)


def _require_rows(value: object) -> tuple[ResearchPacketOfficialSourceAnchorScoreRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPacketOfficialSourceAnchorScoreRow:
            raise ValueError("rows must contain ResearchPacketOfficialSourceAnchorScoreRow values")
        require_paper_only_flags("ResearchPacketOfficialSourceAnchorScoreRow", row)
        key = (row.packet_id, row.anchor_id)
        if key in seen:
            raise ValueError("rows must be unique by packet_id and anchor_id")
        seen.add(key)
    return rows


def _validate_row(row: ResearchPacketOfficialSourceAnchorScoreRow) -> None:
    details = tuple(reason for reason in row.reason_codes if reason in DETAIL_REASON_CODES)
    if row.reason_codes[0] != f"official_source_anchor_score_{row.status}":
        raise ValueError("reason_codes must match status")
    if row.status == "pass" and details:
        raise ValueError("pass rows must not include detail reason codes")
    if row.status != "pass" and not details:
        raise ValueError("non-pass rows must include detail reason codes")


def _validate_report(report: ResearchPacketOfficialSourceAnchorScoreReport) -> None:
    if report.anchor_count != _count(len(report.rows)):
        raise ValueError("anchor_count must match rows")
    if report.packet_count != _count(len({row.packet_id for row in report.rows})):
        raise ValueError("packet_count must match rows")
    if report.event_count != _count(len({row.event_id for row in report.rows})):
        raise ValueError("event_count must match rows")
    if report.source_family_count != _count(len({row.source_family for row in report.rows})):
        raise ValueError("source_family_count must match rows")
    expected_counts = {
        "pass_count": _status_count(report.rows, "pass"),
        "watch_count": _status_count(report.rows, "watch"),
        "blocked_count": _status_count(report.rows, "blocked"),
        "low_official_strength_count": _reason_count(
            report.rows,
            "low_official_strength",
        ),
        "low_resolution_relevance_count": _reason_count(
            report.rows,
            "low_resolution_relevance",
        ),
        "stale_anchor_count": _reason_count(report.rows, "stale_source_anchor"),
        "thin_source_family_independence_count": _reason_count(
            report.rows,
            "thin_source_family_independence",
        ),
        "ambiguity_gap_count": _reason_count(report.rows, "thin_ambiguity_coverage"),
        "contradiction_handling_gap_count": _reason_count(
            report.rows,
            "weak_contradiction_handling",
        ),
    }
    for name, expected in expected_counts.items():
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")
    if report.average_anchor_score != _average_anchor_score(report.rows):
        raise ValueError("average_anchor_score must match rows")
    if report.min_anchor_score != _min_anchor_score(report.rows):
        raise ValueError("min_anchor_score must match rows")
    if report.max_anchor_score != _max_anchor_score(report.rows):
        raise ValueError("max_anchor_score must match rows")
    if report.max_source_age_seconds != _max_source_age_seconds(report.rows):
        raise ValueError("max_source_age_seconds must match rows")
    expected_reason_codes = _report_reason_codes(report.rows, int(report.anchor_count))
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_derived_validation_digest(
    report: ResearchPacketOfficialSourceAnchorScoreReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _report_derived_validation_digest(
    report: ResearchPacketOfficialSourceAnchorScoreReport,
) -> str:
    return _public_payload_derived_validation_digest(_public_payload_for_digest(report))


def _public_payload_for_digest(
    report: ResearchPacketOfficialSourceAnchorScoreReport,
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
    if value is None or type(value) in (bool, int):
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


def _require_sha256_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _duration_seconds(started_at: datetime, generated_at: datetime) -> Decimal:
    delta = _as_utc("generated_at", generated_at) - _as_utc("started_at", started_at)
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        ).quantize(SECONDS_QUANTUM)
    if seconds < Decimal("0").quantize(SECONDS_QUANTUM):
        raise ValueError("source_age_seconds must be nonnegative")
    return seconds


def _ratio(part: Decimal, whole: Decimal) -> Decimal:
    if whole == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (part / whole).quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_ordered_thresholds(name: str, block: Decimal, watch: Decimal) -> None:
    if block > watch:
        raise ValueError(f"{name} block threshold must be at most watch threshold")


def _require_positive_seconds(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_seconds(name, value)
    if normalized <= Decimal("0").quantize(SECONDS_QUANTUM):
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_nonnegative_seconds(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value).quantize(SECONDS_QUANTUM)
    if normalized < Decimal("0").quantize(SECONDS_QUANTUM):
        raise ValueError(f"{name} must be nonnegative")
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
    if normalized != value:
        raise ValueError(f"{name} must use 0.000001 precision")
    return normalized


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return +value
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be finite") from exc


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{name} must be single line")
    _reject_unsafe_public_text("public value", value)


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}")


def _require_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    previous_index: int | None = None
    for reason_code in reason_codes:
        _require_member("reason_code", reason_code, REASON_CODES)
        index = REASON_CODES.index(reason_code)
        if previous_index is not None and index <= previous_index:
            raise ValueError("reason_codes must follow reason code rank")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        previous_index = index
        seen.add(reason_code)
    return reason_codes


def _require_exact_type(name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise TypeError(f"{name} must be exactly {expected_type.__name__}")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_ANCHOR_SCORE_V2_CONFIG_VERSION",
    "ResearchPacketOfficialSourceAnchorInput",
    "ResearchPacketOfficialSourceAnchorScoreConfig",
    "ResearchPacketOfficialSourceAnchorScoreReport",
    "ResearchPacketOfficialSourceAnchorScoreRow",
    "build_research_packet_official_source_anchor_score_v2_report",
    "research_packet_official_source_anchor_score_v2_payload",
)
