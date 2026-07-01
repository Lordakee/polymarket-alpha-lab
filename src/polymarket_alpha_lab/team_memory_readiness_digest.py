"""Pure reducer for team memory readiness digest reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.team_diagnostics_snapshot_history_gate import (
    TeamDiagnosticsSnapshotHistoryGateReport,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_TEAM_MEMORY_READINESS_DIGEST_CONFIG_VERSION = (
    "team-memory-readiness-digest-v0"
)

PASS_REASON = "team_memory_readiness_digest_passed"
WATCH_REASON = "team_memory_readiness_digest_watch_sources_present"
BLOCKED_REASON = "team_memory_readiness_digest_blocked_sources_present"
EMPTY_REASON = "team_memory_readiness_digest_empty_sources"

REASON_CODES = (PASS_REASON, WATCH_REASON, BLOCKED_REASON, EMPTY_REASON)

NEXT_STEPS = {
    "pass": "allow_team_memory_readiness_use",
    "watch": "throttle_team_memory_readiness_use",
    "blocked": "block_team_memory_readiness_use",
}

__all__ = (
    "DEFAULT_TEAM_MEMORY_READINESS_DIGEST_CONFIG_VERSION",
    "TeamMemoryReadinessDigestConfig",
    "TeamMemoryReadinessDigestSource",
    "TeamMemoryReadinessDigestSourceStatus",
    "TeamMemoryReadinessDigestReasonCodeCount",
    "TeamMemoryReadinessDigestReport",
    "build_team_memory_readiness_digest_report",
)


@dataclass(frozen=True)
class TeamMemoryReadinessDigestConfig:
    config_version: str = DEFAULT_TEAM_MEMORY_READINESS_DIGEST_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class TeamMemoryReadinessDigestSource:
    team_id: str
    gate_report: TeamDiagnosticsSnapshotHistoryGateReport
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamMemoryReadinessDigestSource:
            raise ValueError("source must be exactly TeamMemoryReadinessDigestSource")
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        if type(self.gate_report) is not TeamDiagnosticsSnapshotHistoryGateReport:
            raise ValueError(
                "gate_report must be exactly TeamDiagnosticsSnapshotHistoryGateReport"
            )
        _require_hard_flags("gate_report", self.gate_report)
        _require_hard_flags("source", self)


@dataclass(frozen=True)
class TeamMemoryReadinessDigestSourceStatus:
    team_id: str
    gate_status: str
    recommended_next_step: str
    source_config_version: str
    latest_snapshot_age_seconds: int | None
    source_snapshot_count: int
    source_required_snapshot_count: int
    source_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_digest_status("gate_status", self.gate_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_canonical_string("source_config_version", self.source_config_version)
        if self.latest_snapshot_age_seconds is not None:
            _require_nonnegative_int(
                "latest_snapshot_age_seconds",
                self.latest_snapshot_age_seconds,
            )
        _require_nonnegative_int("source_snapshot_count", self.source_snapshot_count)
        _require_positive_int(
            "source_required_snapshot_count",
            self.source_required_snapshot_count,
        )
        _require_canonical_string("source_status", self.source_status)
        _require_hard_flags("source_status", self)


@dataclass(frozen=True)
class TeamMemoryReadinessDigestReasonCodeCount:
    reason_code: str
    count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_digest_reason_code("reason_code", self.reason_code)
        _require_positive_int("count", self.count)
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class TeamMemoryReadinessDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    team_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    source_statuses: tuple[TeamMemoryReadinessDigestSourceStatus, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[TeamMemoryReadinessDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_nonnegative_int("team_count", self.team_count)
        _require_nonnegative_int("pass_count", self.pass_count)
        _require_nonnegative_int("watch_count", self.watch_count)
        _require_nonnegative_int("blocked_count", self.blocked_count)
        object.__setattr__(
            self,
            "source_statuses",
            _normalize_source_statuses(self.source_statuses),
        )
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_team_memory_readiness_digest_report(
    sources: list[TeamMemoryReadinessDigestSource]
    | tuple[TeamMemoryReadinessDigestSource, ...],
    *,
    config: TeamMemoryReadinessDigestConfig,
    generated_at: datetime,
) -> TeamMemoryReadinessDigestReport:
    if type(config) is not TeamMemoryReadinessDigestConfig:
        raise ValueError("config must be a TeamMemoryReadinessDigestConfig")
    _require_hard_flags("config", config)

    normalized_sources = _normalize_sources(sources)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_statuses = _source_statuses(normalized_sources)
    pass_count = sum(1 for source in source_statuses if source.gate_status == "pass")
    watch_count = sum(1 for source in source_statuses if source.gate_status == "watch")
    blocked_count = sum(
        1 for source in source_statuses if source.gate_status == "blocked"
    )
    reason_codes = _digest_reason_codes(
        team_count=len(source_statuses),
        watch_count=watch_count,
        blocked_count=blocked_count,
    )
    digest_status = _expected_digest_status(reason_codes)

    return TeamMemoryReadinessDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        team_count=len(source_statuses),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        source_statuses=source_statuses,
        source_config_versions=_source_config_versions(source_statuses),
        reason_code_counts=_reason_code_counts(reason_codes),
        reason_codes=reason_codes,
    )


def _normalize_sources(
    sources: list[TeamMemoryReadinessDigestSource]
    | tuple[TeamMemoryReadinessDigestSource, ...],
) -> tuple[TeamMemoryReadinessDigestSource, ...]:
    if type(sources) not in (list, tuple):
        raise ValueError("sources must be a list or tuple")
    normalized_sources = tuple(sources)
    seen_team_ids: set[str] = set()
    for source in normalized_sources:
        if type(source) is not TeamMemoryReadinessDigestSource:
            raise ValueError("sources must contain TeamMemoryReadinessDigestSource")
        _require_hard_flags("source", source)
        _require_hard_flags("gate_report", source.gate_report)
        if source.team_id in seen_team_ids:
            raise ValueError("sources team_id values must be unique")
        seen_team_ids.add(source.team_id)
    return normalized_sources


def _source_statuses(
    sources: tuple[TeamMemoryReadinessDigestSource, ...],
) -> tuple[TeamMemoryReadinessDigestSourceStatus, ...]:
    return tuple(
        TeamMemoryReadinessDigestSourceStatus(
            team_id=source.team_id,
            gate_status=source.gate_report.gate_status,
            recommended_next_step=source.gate_report.recommended_next_step,
            source_config_version=source.gate_report.source_config_version,
            latest_snapshot_age_seconds=(
                source.gate_report.latest_snapshot_age_seconds
            ),
            source_snapshot_count=source.gate_report.source_snapshot_count,
            source_required_snapshot_count=(
                source.gate_report.source_required_snapshot_count
            ),
            source_status=source.gate_report.source_status,
        )
        for source in sources
    )


def _source_config_versions(
    source_statuses: tuple[TeamMemoryReadinessDigestSourceStatus, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (
                source_status.team_id,
                source_status.source_config_version,
            )
            for source_status in source_statuses
        )
    )


def _digest_reason_codes(
    *,
    team_count: int,
    watch_count: int,
    blocked_count: int,
) -> tuple[str, ...]:
    if team_count == 0:
        return (EMPTY_REASON,)
    if blocked_count > 0:
        return (BLOCKED_REASON,)
    if watch_count > 0:
        return (WATCH_REASON,)
    return (PASS_REASON,)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[TeamMemoryReadinessDigestReasonCodeCount, ...]:
    return tuple(
        TeamMemoryReadinessDigestReasonCodeCount(
            reason_code=reason_code,
            count=sum(1 for item in reason_codes if item == reason_code),
        )
        for reason_code in sorted(set(reason_codes))
    )


def _validate_report_consistency(report: TeamMemoryReadinessDigestReport) -> None:
    if report.team_count != len(report.source_statuses):
        raise ValueError("team_count must match source_statuses")
    expected_pass_count = sum(
        1 for source_status in report.source_statuses if source_status.gate_status == "pass"
    )
    expected_watch_count = sum(
        1
        for source_status in report.source_statuses
        if source_status.gate_status == "watch"
    )
    expected_blocked_count = sum(
        1
        for source_status in report.source_statuses
        if source_status.gate_status == "blocked"
    )
    if report.pass_count != expected_pass_count:
        raise ValueError("pass_count must match source_statuses")
    if report.watch_count != expected_watch_count:
        raise ValueError("watch_count must match source_statuses")
    if report.blocked_count != expected_blocked_count:
        raise ValueError("blocked_count must match source_statuses")
    expected_reason_codes = _digest_reason_codes(
        team_count=report.team_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match digest status inputs")
    expected_digest_status = _expected_digest_status(report.reason_codes)
    if report.digest_status != expected_digest_status:
        raise ValueError("digest_status must match reason_codes")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    expected_source_config_versions = _source_config_versions(report.source_statuses)
    if report.source_config_versions != expected_source_config_versions:
        raise ValueError("source_config_versions must match source_statuses")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must summarize reason_codes")


def _expected_digest_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if reason_codes == (WATCH_REASON,):
        return "watch"
    if reason_codes in ((BLOCKED_REASON,), (EMPTY_REASON,)):
        return "blocked"
    raise ValueError("reason_codes must contain known digest reasons")


def _normalize_source_statuses(
    source_statuses: tuple[TeamMemoryReadinessDigestSourceStatus, ...],
) -> tuple[TeamMemoryReadinessDigestSourceStatus, ...]:
    if type(source_statuses) not in (list, tuple):
        raise ValueError("source_statuses must be a list or tuple")
    statuses = tuple(source_statuses)
    seen_team_ids: set[str] = set()
    for status in statuses:
        if type(status) is not TeamMemoryReadinessDigestSourceStatus:
            raise ValueError("source_statuses must contain source status rows")
        _require_hard_flags("source_status", status)
        if status.team_id in seen_team_ids:
            raise ValueError("source_statuses team_id values must be unique")
        seen_team_ids.add(status.team_id)
    return statuses


def _normalize_source_config_versions(
    source_config_versions: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(source_config_versions) not in (list, tuple):
        raise ValueError("source_config_versions must be a list or tuple")
    versions = tuple(source_config_versions)
    seen_team_ids: set[str] = set()
    for item in versions:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("source_config_versions entries must be team/version pairs")
        team_id, source_config_version = item
        require_team_id("source_config_versions team_id", team_id)
        _require_canonical_string(
            "source_config_versions source_config_version",
            source_config_version,
        )
        if team_id in seen_team_ids:
            raise ValueError("source_config_versions team_id values must be unique")
        seen_team_ids.add(team_id)
    if versions != tuple(sorted(versions)):
        raise ValueError("source_config_versions must be sorted by team_id")
    return versions


def _normalize_reason_code_counts(
    reason_code_counts: tuple[TeamMemoryReadinessDigestReasonCodeCount, ...],
) -> tuple[TeamMemoryReadinessDigestReasonCodeCount, ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(reason_code_counts)
    seen_reason_codes: set[str] = set()
    for count in counts:
        if type(count) is not TeamMemoryReadinessDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    if tuple(count.reason_code for count in counts) != tuple(
        sorted(count.reason_code for count in counts)
    ):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(reason_codes)
    if not codes:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in codes:
        _require_digest_reason_code("reason_codes", reason_code)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    return codes


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_digest_status(name: str, value: object) -> None:
    if type(value) is not str or value not in NEXT_STEPS:
        raise ValueError(f"{name} must be pass, watch, or blocked")


def _require_digest_reason_code(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{name} must contain known digest reason codes")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_nonnegative_int(name: str, value: object) -> None:
    _require_int(name, value)
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")


def _require_positive_int(name: str, value: object) -> None:
    _require_int(name, value)
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def _require_int(name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{name} must be an int")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")
