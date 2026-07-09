"""Pure report-only cross-team resolution authority gap report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION = (
    "research-strategy-cross-team-resolution-authority-gap-report-v0"
)
RESEARCH_STRATEGY_CROSS_TEAM_RESOLUTION_AUTHORITY_GAP_STATUSES = (
    "pass",
    "watch",
    "block",
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")

REASON_EMPTY = "resolution_authority_gap_empty"
REASON_PASS = "resolution_authority_gap_pass"
REASON_WATCH = "resolution_authority_gap_watch"
REASON_BLOCK = "resolution_authority_gap_block"

ROW_REASON_CODES = (
    REASON_PASS,
    "team_coverage_block",
    "alignment_block",
    "rule_mapping_block",
    "conflict_severity_block",
    "latest_observed_age_block",
    "unresolved_dependency_block",
    "team_coverage_watch",
    "alignment_watch",
    "rule_mapping_watch",
    "conflict_severity_watch",
    "latest_observed_age_watch",
    "unresolved_dependency_watch",
)
REPORT_REASON_CODES = (REASON_EMPTY, REASON_BLOCK, REASON_WATCH, REASON_PASS)
STATUS_VALUES = frozenset(RESEARCH_STRATEGY_CROSS_TEAM_RESOLUTION_AUTHORITY_GAP_STATUSES)
FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
UNSAFE_PUBLIC_FRAGMENTS = (
    "can" "didate",
    "mar" "ket",
    "slug",
    "quest" "ion",
    "sou" "rce",
    "url",
    "raw",
    "text",
    "http" "://",
    "http" "s://",
    "d" "sn",
    "data" "base",
    "table" "_" "name",
    "tok" "en",
    "sec" "ret",
    "pass" "word",
    "cred" "ential",
    "private" "_" "key",
    "api" "_" "key",
    "bear" "er",
    "wal" "let",
    "or" "der",
    "tra" "de",
    "tra" "ding",
    "li" "ve",
    "pos" "ition",
    "siz" "ing",
    "recom" "mend",
)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_CROSS_TEAM_RESOLUTION_AUTHORITY_GAP_STATUSES",
    "ResearchStrategyCrossTeamResolutionAuthorityGapConfig",
    "ResearchStrategyCrossTeamResolutionAuthorityGapEvidence",
    "ResearchStrategyCrossTeamResolutionAuthorityGapReasonCodeCount",
    "ResearchStrategyCrossTeamResolutionAuthorityGapReport",
    "ResearchStrategyCrossTeamResolutionAuthorityGapRow",
    "build_research_strategy_cross_team_resolution_authority_gap_report",
    "research_strategy_cross_team_resolution_authority_gap_report_payload",
)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamResolutionAuthorityGapConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION
    )
    min_pass_team_coverage_ratio: Decimal = Decimal("0.750000")
    min_watch_team_coverage_ratio: Decimal = Decimal("0.500000")
    min_pass_alignment_score: Decimal = Decimal("0.700000")
    min_watch_alignment_score: Decimal = Decimal("0.450000")
    min_pass_rule_mapping_score: Decimal = Decimal("0.750000")
    min_watch_rule_mapping_score: Decimal = Decimal("0.500000")
    max_pass_conflict_severity: Decimal = Decimal("0.200000")
    max_watch_conflict_severity: Decimal = Decimal("0.500000")
    max_pass_latest_observed_age_seconds: Decimal = Decimal("3600.000000")
    max_watch_latest_observed_age_seconds: Decimal = Decimal("86400.000000")
    max_pass_unresolved_dependency_count: Decimal = Decimal("0.000000")
    max_watch_unresolved_dependency_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchStrategyCrossTeamResolutionAuthorityGapConfig)
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in (
            "min_pass_team_coverage_ratio",
            "min_watch_team_coverage_ratio",
            "min_pass_alignment_score",
            "min_watch_alignment_score",
            "min_pass_rule_mapping_score",
            "min_watch_rule_mapping_score",
            "max_pass_conflict_severity",
            "max_watch_conflict_severity",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        for name in (
            "max_pass_latest_observed_age_seconds",
            "max_watch_latest_observed_age_seconds",
            "max_pass_unresolved_dependency_count",
            "max_watch_unresolved_dependency_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        _require_floor_pair(
            "min_pass_team_coverage_ratio",
            self.min_pass_team_coverage_ratio,
            "min_watch_team_coverage_ratio",
            self.min_watch_team_coverage_ratio,
        )
        _require_floor_pair(
            "min_pass_alignment_score",
            self.min_pass_alignment_score,
            "min_watch_alignment_score",
            self.min_watch_alignment_score,
        )
        _require_floor_pair(
            "min_pass_rule_mapping_score",
            self.min_pass_rule_mapping_score,
            "min_watch_rule_mapping_score",
            self.min_watch_rule_mapping_score,
        )
        _require_ceiling_pair(
            "max_pass_conflict_severity",
            self.max_pass_conflict_severity,
            "max_watch_conflict_severity",
            self.max_watch_conflict_severity,
        )
        _require_ceiling_pair(
            "max_pass_latest_observed_age_seconds",
            self.max_pass_latest_observed_age_seconds,
            "max_watch_latest_observed_age_seconds",
            self.max_watch_latest_observed_age_seconds,
        )
        _require_ceiling_pair(
            "max_pass_unresolved_dependency_count",
            self.max_pass_unresolved_dependency_count,
            "max_watch_unresolved_dependency_count",
            self.max_watch_unresolved_dependency_count,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamResolutionAuthorityGapEvidence:
    resolution_ref: str
    team_ref: str
    resolver_ref: str
    observed_at: datetime
    team_coverage_ratio: Decimal
    alignment_score: Decimal
    rule_mapping_score: Decimal
    conflict_severity: Decimal
    unresolved_dependency_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("evidence", self, ResearchStrategyCrossTeamResolutionAuthorityGapEvidence)
        for name in ("resolution_ref", "team_ref", "resolver_ref"):
            _require_nonempty_text(name, getattr(self, name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in (
            "team_coverage_ratio",
            "alignment_score",
            "rule_mapping_score",
            "conflict_severity",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "unresolved_dependency_count",
            _require_nonnegative_decimal(
                "unresolved_dependency_count",
                self.unresolved_dependency_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamResolutionAuthorityGapRow:
    resolution_ref: str
    evidence_count: Decimal
    team_count: Decimal
    resolver_count: Decimal
    latest_observed_at: datetime
    latest_observed_age_seconds: Decimal
    average_team_coverage_ratio: Decimal
    average_alignment_score: Decimal
    average_rule_mapping_score: Decimal
    conflict_severity: Decimal
    unresolved_dependency_count: Decimal
    resolution_gap_score: Decimal
    team_refs: tuple[str, ...]
    resolver_refs: tuple[str, ...]
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchStrategyCrossTeamResolutionAuthorityGapRow)
        _require_nonempty_text("resolution_ref", self.resolution_ref)
        for name in ("evidence_count", "team_count", "resolver_count"):
            object.__setattr__(self, name, _require_nonnegative_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for name in (
            "latest_observed_age_seconds",
            "unresolved_dependency_count",
            "resolution_gap_score",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "average_team_coverage_ratio",
            "average_alignment_score",
            "average_rule_mapping_score",
            "conflict_severity",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        for name in ("team_refs", "resolver_refs"):
            object.__setattr__(self, name, _normalize_ref_tuple(name, getattr(self, name)))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamResolutionAuthorityGapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamResolutionAuthorityGapReport:
    generated_at: datetime
    config_version: str
    resolution_count: Decimal
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_resolution_gap_score: Decimal | None
    highest_resolution_gap_score: Decimal
    oldest_latest_observed_age_seconds: Decimal
    status: str
    rows: tuple[ResearchStrategyCrossTeamResolutionAuthorityGapRow, ...]
    reason_code_counts: tuple[ResearchStrategyCrossTeamResolutionAuthorityGapReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchStrategyCrossTeamResolutionAuthorityGapReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in (
            "resolution_count",
            "evidence_count",
            "pass_count",
            "watch_count",
            "block_count",
            "highest_resolution_gap_score",
            "oldest_latest_observed_age_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "average_resolution_gap_score",
            _require_optional_ratio_decimal(
                "average_resolution_gap_score",
                self.average_resolution_gap_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != digest:
                raise ValueError("derived_validation_digest does not match public payload")
        else:
            object.__setattr__(self, "derived_validation_digest", digest)


def build_research_strategy_cross_team_resolution_authority_gap_report(
    evidence: Iterable[object],
    *,
    config: ResearchStrategyCrossTeamResolutionAuthorityGapConfig,
    generated_at: datetime,
) -> ResearchStrategyCrossTeamResolutionAuthorityGapReport:
    if type(config) is not ResearchStrategyCrossTeamResolutionAuthorityGapConfig:
        raise ValueError(
            "config must be ResearchStrategyCrossTeamResolutionAuthorityGapConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_evidence(evidence)
    for item in evidence_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must be at or before generated_at")

    grouped: dict[str, list[ResearchStrategyCrossTeamResolutionAuthorityGapEvidence]] = {}
    for item in evidence_items:
        grouped.setdefault(item.resolution_ref, []).append(item)

    rows = tuple(
        _row_from_resolution(
            resolution_ref=resolution_ref,
            items=tuple(grouped[resolution_ref]),
            config=config,
            generated_at=generated_at_utc,
        )
        for resolution_ref in sorted(grouped)
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchStrategyCrossTeamResolutionAuthorityGapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        resolution_count=_decimal_count(len(rows)),
        evidence_count=sum((row.evidence_count for row in rows), ZERO),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_resolution_gap_score=_average_gap_score(rows),
        highest_resolution_gap_score=max(
            (row.resolution_gap_score for row in rows),
            default=ZERO,
        ),
        oldest_latest_observed_age_seconds=max(
            (row.latest_observed_age_seconds for row in rows),
            default=ZERO,
        ),
        status=_report_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_cross_team_resolution_authority_gap_report_payload(
    report: ResearchStrategyCrossTeamResolutionAuthorityGapReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyCrossTeamResolutionAuthorityGapReport:
        raise ValueError(
            "report must be ResearchStrategyCrossTeamResolutionAuthorityGapReport",
        )
    _require_hard_flags("report", report)
    payload = _public_payload_base(report)
    digest = _payload_digest(payload)
    if report.derived_validation_digest != digest:
        raise ValueError("derived_validation_digest does not match public payload")
    payload["derived_validation_digest"] = digest
    _reject_unsafe_public_payload(payload)
    return payload


def _row_from_resolution(
    *,
    resolution_ref: str,
    items: tuple[ResearchStrategyCrossTeamResolutionAuthorityGapEvidence, ...],
    config: ResearchStrategyCrossTeamResolutionAuthorityGapConfig,
    generated_at: datetime,
) -> ResearchStrategyCrossTeamResolutionAuthorityGapRow:
    values = tuple(
        sorted(
            items,
            key=lambda item: (item.team_ref, item.resolver_ref, item.observed_at.isoformat()),
        ),
    )
    latest = max(values, key=lambda item: item.observed_at)
    latest_age = _age_seconds(generated_at, latest.observed_at)
    coverage = _average(tuple(item.team_coverage_ratio for item in values))
    alignment = _average(tuple(item.alignment_score for item in values))
    rule_mapping = _average(tuple(item.rule_mapping_score for item in values))
    conflict = max(item.conflict_severity for item in values)
    unresolved = max(item.unresolved_dependency_count for item in values)
    gap_score = _resolution_gap_score(
        coverage,
        alignment,
        rule_mapping,
        conflict,
        latest_age,
        unresolved,
        config,
    )
    status = _row_status(
        coverage,
        alignment,
        rule_mapping,
        conflict,
        latest_age,
        unresolved,
        config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        team_coverage_ratio=coverage,
        alignment_score=alignment,
        rule_mapping_score=rule_mapping,
        conflict_severity=conflict,
        latest_observed_age_seconds=latest_age,
        unresolved_dependency_count=unresolved,
        config=config,
        input_reason_codes=tuple(reason for item in values for reason in item.reason_codes),
    )
    return ResearchStrategyCrossTeamResolutionAuthorityGapRow(
        resolution_ref=resolution_ref,
        evidence_count=_decimal_count(len(values)),
        team_count=_decimal_count(len({item.team_ref for item in values})),
        resolver_count=_decimal_count(len({item.resolver_ref for item in values})),
        latest_observed_at=latest.observed_at,
        latest_observed_age_seconds=latest_age,
        average_team_coverage_ratio=coverage,
        average_alignment_score=alignment,
        average_rule_mapping_score=rule_mapping,
        conflict_severity=conflict,
        unresolved_dependency_count=unresolved,
        resolution_gap_score=gap_score,
        team_refs=tuple(sorted({item.team_ref for item in values})),
        resolver_refs=tuple(sorted({item.resolver_ref for item in values})),
        status=status,
        reason_codes=reason_codes,
    )


def _normalize_evidence(
    evidence: Iterable[object],
) -> tuple[ResearchStrategyCrossTeamResolutionAuthorityGapEvidence, ...]:
    if isinstance(evidence, (str, bytes)):
        raise ValueError("evidence must be an iterable")
    try:
        values = tuple(evidence)
    except TypeError as exc:
        raise ValueError("evidence must be an iterable") from exc
    normalized: list[ResearchStrategyCrossTeamResolutionAuthorityGapEvidence] = []
    for item in values:
        if type(item) is not ResearchStrategyCrossTeamResolutionAuthorityGapEvidence:
            raise ValueError(
                "evidence must contain ResearchStrategyCrossTeamResolutionAuthorityGapEvidence",
            )
        normalized.append(item)
    return tuple(normalized)


def _resolution_gap_score(
    team_coverage_ratio: Decimal,
    alignment_score: Decimal,
    rule_mapping_score: Decimal,
    conflict_severity: Decimal,
    latest_observed_age_seconds: Decimal,
    unresolved_dependency_count: Decimal,
    config: ResearchStrategyCrossTeamResolutionAuthorityGapConfig,
) -> Decimal:
    components = (
        ONE - team_coverage_ratio,
        ONE - alignment_score,
        ONE - rule_mapping_score,
        conflict_severity,
        _ceiling_pressure(
            latest_observed_age_seconds,
            config.max_pass_latest_observed_age_seconds,
            config.max_watch_latest_observed_age_seconds,
        ),
        _ceiling_pressure(
            unresolved_dependency_count,
            config.max_pass_unresolved_dependency_count,
            config.max_watch_unresolved_dependency_count,
        ),
    )
    return _average(components)


def _ceiling_pressure(value: Decimal, pass_ceiling: Decimal, watch_ceiling: Decimal) -> Decimal:
    if value <= pass_ceiling:
        return ZERO
    if value >= watch_ceiling:
        return ONE
    if watch_ceiling == pass_ceiling:
        return ONE
    return _q((value - pass_ceiling) / (watch_ceiling - pass_ceiling))


def _row_status(
    team_coverage_ratio: Decimal,
    alignment_score: Decimal,
    rule_mapping_score: Decimal,
    conflict_severity: Decimal,
    latest_observed_age_seconds: Decimal,
    unresolved_dependency_count: Decimal,
    config: ResearchStrategyCrossTeamResolutionAuthorityGapConfig,
) -> str:
    if (
        team_coverage_ratio < config.min_watch_team_coverage_ratio
        or alignment_score < config.min_watch_alignment_score
        or rule_mapping_score < config.min_watch_rule_mapping_score
        or conflict_severity > config.max_watch_conflict_severity
        or latest_observed_age_seconds > config.max_watch_latest_observed_age_seconds
        or unresolved_dependency_count > config.max_watch_unresolved_dependency_count
    ):
        return "block"
    if (
        team_coverage_ratio < config.min_pass_team_coverage_ratio
        or alignment_score < config.min_pass_alignment_score
        or rule_mapping_score < config.min_pass_rule_mapping_score
        or conflict_severity > config.max_pass_conflict_severity
        or latest_observed_age_seconds > config.max_pass_latest_observed_age_seconds
        or unresolved_dependency_count > config.max_pass_unresolved_dependency_count
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    team_coverage_ratio: Decimal,
    alignment_score: Decimal,
    rule_mapping_score: Decimal,
    conflict_severity: Decimal,
    latest_observed_age_seconds: Decimal,
    unresolved_dependency_count: Decimal,
    config: ResearchStrategyCrossTeamResolutionAuthorityGapConfig,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if status == "pass":
        reasons = [REASON_PASS]
    else:
        suffix = status
        reasons = []
        if _floor_breach(team_coverage_ratio, config.min_pass_team_coverage_ratio, config.min_watch_team_coverage_ratio, status):
            reasons.append(f"team_coverage_{suffix}")
        if _floor_breach(alignment_score, config.min_pass_alignment_score, config.min_watch_alignment_score, status):
            reasons.append(f"alignment_{suffix}")
        if _floor_breach(rule_mapping_score, config.min_pass_rule_mapping_score, config.min_watch_rule_mapping_score, status):
            reasons.append(f"rule_mapping_{suffix}")
        if _ceiling_breach(conflict_severity, config.max_pass_conflict_severity, config.max_watch_conflict_severity, status):
            reasons.append(f"conflict_severity_{suffix}")
        if _ceiling_breach(latest_observed_age_seconds, config.max_pass_latest_observed_age_seconds, config.max_watch_latest_observed_age_seconds, status):
            reasons.append(f"latest_observed_age_{suffix}")
        if _ceiling_breach(unresolved_dependency_count, config.max_pass_unresolved_dependency_count, config.max_watch_unresolved_dependency_count, status):
            reasons.append(f"unresolved_dependency_{suffix}")
    for reason in input_reason_codes:
        reasons.append(f"input_{reason}")
    return _normalize_reason_codes("reason_codes", tuple(reasons), allow_empty=False)


def _floor_breach(value: Decimal, pass_floor: Decimal, watch_floor: Decimal, status: str) -> bool:
    if status == "block":
        return value < watch_floor
    return value < pass_floor


def _ceiling_breach(value: Decimal, pass_ceiling: Decimal, watch_ceiling: Decimal, status: str) -> bool:
    if status == "block":
        return value > watch_ceiling
    return value > pass_ceiling


def _report_reason_codes(
    rows: tuple[ResearchStrategyCrossTeamResolutionAuthorityGapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_EMPTY,)
    reasons = []
    if any(row.status == "block" for row in rows):
        reasons.append(REASON_BLOCK)
    if any(row.status == "watch" for row in rows):
        reasons.append(REASON_WATCH)
    if any(row.status == "pass" for row in rows):
        reasons.append(REASON_PASS)
    return tuple(reasons)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if REASON_BLOCK in reason_codes or REASON_EMPTY in reason_codes:
        return "block"
    if REASON_WATCH in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchStrategyCrossTeamResolutionAuthorityGapRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyCrossTeamResolutionAuthorityGapReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyCrossTeamResolutionAuthorityGapReasonCodeCount(
                reason_code=report_reason_codes[0],
                count=ONE,
            ),
        )
    counts = Counter(reason for row in rows for reason in row.reason_codes)
    return tuple(
        ResearchStrategyCrossTeamResolutionAuthorityGapReasonCodeCount(
            reason_code=reason,
            count=_decimal_count(counts[reason]),
        )
        for reason in sorted(counts)
    )


def _status_count(rows: tuple[ResearchStrategyCrossTeamResolutionAuthorityGapRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_gap_score(
    rows: tuple[ResearchStrategyCrossTeamResolutionAuthorityGapRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _average(tuple(row.resolution_gap_score for row in rows))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("cannot average empty values")
    return _q(sum(values, ZERO) / Decimal(len(values)))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    value = (
        Decimal(delta.days * 86400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _require_nonnegative_decimal("latest_observed_age_seconds", value)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyCrossTeamResolutionAuthorityGapRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchStrategyCrossTeamResolutionAuthorityGapRow] = []
    for row in rows:
        if type(row) is not ResearchStrategyCrossTeamResolutionAuthorityGapRow:
            raise ValueError("rows must contain ResearchStrategyCrossTeamResolutionAuthorityGapRow")
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.resolution_ref))


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchStrategyCrossTeamResolutionAuthorityGapReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchStrategyCrossTeamResolutionAuthorityGapReasonCodeCount] = []
    for count in counts:
        if type(count) is not ResearchStrategyCrossTeamResolutionAuthorityGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyCrossTeamResolutionAuthorityGapReasonCodeCount",
            )
        normalized.append(count)
    return tuple(sorted(normalized, key=lambda count: count.reason_code))


def _normalize_ref_tuple(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not value:
        raise ValueError(f"{name} must not be empty")
    normalized = tuple(_require_nonempty_text(name, item) for item in value)
    return tuple(sorted(normalized))


def _validate_row(row: ResearchStrategyCrossTeamResolutionAuthorityGapRow) -> None:
    if row.team_count != _decimal_count(len(row.team_refs)):
        raise ValueError("team_count must match team_refs")
    if row.resolver_count != _decimal_count(len(row.resolver_refs)):
        raise ValueError("resolver_count must match resolver_refs")
    if row.status == "pass" and row.reason_codes != (REASON_PASS,):
        raise ValueError("pass rows must use pass reason code only")


def _validate_report(report: ResearchStrategyCrossTeamResolutionAuthorityGapReport) -> None:
    if report.resolution_count != _decimal_count(len(report.rows)):
        raise ValueError("resolution_count must match rows")
    if report.evidence_count != sum((row.evidence_count for row in report.rows), ZERO):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_resolution_gap_score != _average_gap_score(report.rows):
        raise ValueError("average_resolution_gap_score must match rows")
    if report.highest_resolution_gap_score != max(
        (row.resolution_gap_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("highest_resolution_gap_score must match rows")
    if report.oldest_latest_observed_age_seconds != max(
        (row.latest_observed_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("oldest_latest_observed_age_seconds must match rows")
    if report.status != _report_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _public_payload_base(
    report: ResearchStrategyCrossTeamResolutionAuthorityGapReport,
) -> dict[str, Any]:
    return {
        "report_type": "research_strategy_cross_team_resolution_authority_gap_report",
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "resolution_count": str(report.resolution_count),
        "evidence_count": str(report.evidence_count),
        "pass_count": str(report.pass_count),
        "watch_count": str(report.watch_count),
        "block_count": str(report.block_count),
        "average_gap_score": _optional_decimal_payload(
            report.average_resolution_gap_score,
        ),
        "highest_gap_score": str(report.highest_resolution_gap_score),
        "oldest_latest_observed_age_seconds": str(
            report.oldest_latest_observed_age_seconds,
        ),
        "status": report.status,
        "rows": [_public_row_payload(row) for row in report.rows],
        "reason_code_counts": [
            {
                "reason_code": count.reason_code,
                "count": str(count.count),
                "paper_only": count.paper_only,
                "report_only": count.report_only,
                "readonly": count.readonly,
            }
            for count in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _public_row_payload(
    row: ResearchStrategyCrossTeamResolutionAuthorityGapRow,
) -> dict[str, Any]:
    return {
        "resolution_key": _public_key("resolution", row.resolution_ref),
        "evidence_count": str(row.evidence_count),
        "team_count": str(row.team_count),
        "resolver_count": str(row.resolver_count),
        "latest_observed_at": row.latest_observed_at.isoformat(),
        "latest_observed_age_seconds": str(row.latest_observed_age_seconds),
        "team_coverage_ratio": str(row.average_team_coverage_ratio),
        "alignment_score": str(row.average_alignment_score),
        "rule_mapping_score": str(row.average_rule_mapping_score),
        "conflict_severity": str(row.conflict_severity),
        "unresolved_dependency_count": str(row.unresolved_dependency_count),
        "gap_score": str(row.resolution_gap_score),
        "team_keys": [_public_key("team", item) for item in row.team_refs],
        "resolver_keys": [_public_key("resolver", item) for item in row.resolver_refs],
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest(report: ResearchStrategyCrossTeamResolutionAuthorityGapReport) -> str:
    return _payload_digest(_public_payload_base(report))


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _public_key(prefix: str, value: str) -> str:
    digest = sha256(f"{prefix}\0{value}".encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _optional_decimal_payload(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _reject_unsafe_public_payload(payload: dict[str, Any]) -> None:
    for value in _walk_payload(payload):
        if isinstance(value, str):
            lowered = value.lower()
            if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError("unsafe public payload value")
        elif type(value) in (int, float, Decimal):
            raise ValueError("unsafe public payload numeric value")


def _walk_payload(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for key, item in value.items():
            values.append(key)
            values.extend(_walk_payload(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_payload(item))
        return tuple(values)
    return (value,)


def _normalize_reason_codes(
    name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{name} must not be empty")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        reason = _require_reason_code(name, item)
        if reason not in seen:
            normalized.append(reason)
            seen.add(reason)
    if not allow_empty and not normalized:
        raise ValueError(f"{name} must not be empty")
    return tuple(normalized)


def _require_reason_code(name: str, value: object) -> str:
    text = _require_public_text(name, value)
    if any(fragment in text for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} includes unsafe public payload text")
    return text


def _require_public_text(name: str, value: object) -> str:
    text = _require_nonempty_text(name, value)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_:-.")
    if any(char not in allowed for char in text):
        raise ValueError(f"{name} must be lowercase public text")
    return text


def _require_nonempty_text(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must not be empty")
    return value


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in STATUS_VALUES:
        raise ValueError(f"{name} must be one of pass, watch, block")


def _require_hard_flags(label: str, value: object) -> None:
    for flag in FLAG_FIELDS:
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{label} {flag} must be True")


def _require_exact_type(name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_floor_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{pass_name} must be at least {watch_name}")


def _require_ceiling_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{pass_name} must not exceed {watch_name}")


def _require_optional_ratio_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(name, value)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value > ONE:
        raise ValueError(f"{name} must be at most 1")
    return decimal_value


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    try:
        return _q(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be finite") from exc


def _q(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("decimal values must be finite")
    with localcontext() as context:
        context.prec = 64
        return value.quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _q(Decimal(value))


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")
