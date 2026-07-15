"""Paper-only team research coverage map for operations summaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_TEAM_RESEARCH_COVERAGE_MAP_CONFIG_VERSION = "team-research-coverage-map-v0"
PERCENT_QUANT = Decimal("0.000001")
ZERO_PERCENT = Decimal("0.000000")
RESEARCH_DOMAINS = ("politics", "finance", "sports", "general")
EVIDENCE_STATUSES = ("covered", "watch", "gap", "blocked")
COVERAGE_STATUSES = ("safe", "watch", "blocked")
SUMMARY_DIMENSIONS = (
    "research_domain",
    "source_family",
    "team_id",
    "evidence_status",
)


@dataclass(frozen=True)
class TeamResearchCoverageMapConfig:
    config_version: str = DEFAULT_TEAM_RESEARCH_COVERAGE_MAP_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        require_paper_only_flags("TeamResearchCoverageMapConfig", self)


@dataclass(frozen=True)
class TeamResearchCoverageMapObservation:
    research_domain: str
    source_family: str
    team_id: str
    evidence_status: str
    public_identifier: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("research_domain", self.research_domain, RESEARCH_DOMAINS)
        _require_canonical_string("source_family", self.source_family)
        _require_canonical_string("team_id", self.team_id)
        _require_member("evidence_status", self.evidence_status, EVIDENCE_STATUSES)
        _require_canonical_string("public_identifier", self.public_identifier)
        require_paper_only_flags("TeamResearchCoverageMapObservation", self)

    def __repr__(self) -> str:
        return (
            "TeamResearchCoverageMapObservation("
            f"research_domain={self.research_domain!r}, "
            f"source_family={self.source_family!r}, "
            f"team_id={self.team_id!r}, "
            f"evidence_status={self.evidence_status!r}, "
            f"redacted_public_identifier="
            f"{redact_team_research_coverage_map_identifier(self.public_identifier)!r}, "
            f"paper_only={self.paper_only!r}, "
            f"report_only={self.report_only!r}, "
            f"readonly={self.readonly!r})"
        )


@dataclass(frozen=True)
class TeamResearchCoverageMapSummary:
    dimension: str
    value: str
    observation_count: int
    observation_pct: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("dimension", self.dimension, SUMMARY_DIMENSIONS)
        _require_canonical_string("value", self.value)
        _require_positive_int("observation_count", self.observation_count)
        object.__setattr__(
            self,
            "observation_pct",
            _quantize_percent("observation_pct", self.observation_pct),
        )
        require_paper_only_flags("TeamResearchCoverageMapSummary", self)


@dataclass(frozen=True)
class TeamResearchCoverageMapTeamEvidenceSummary:
    team_id: str
    observation_count: int
    covered_observation_count: int
    watch_observation_count: int
    gap_observation_count: int
    blocked_observation_count: int
    covered_observation_pct: Decimal | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_positive_int("observation_count", self.observation_count)
        for field_name in (
            "covered_observation_count",
            "watch_observation_count",
            "gap_observation_count",
            "blocked_observation_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.covered_observation_pct is None:
            object.__setattr__(
                self,
                "covered_observation_pct",
                _percent(self.covered_observation_count, self.observation_count),
            )
        else:
            object.__setattr__(
                self,
                "covered_observation_pct",
                _quantize_percent("covered_observation_pct", self.covered_observation_pct),
            )
        _validate_team_evidence_summary_consistency(self)
        require_paper_only_flags("TeamResearchCoverageMapTeamEvidenceSummary", self)


@dataclass(frozen=True)
class TeamResearchCoverageMapRow:
    research_domain: str
    source_family: str
    team_id: str
    evidence_status: str
    observation_count: int
    total_observation_count: int
    redacted_public_identifiers: tuple[str, ...]
    observation_pct: Decimal | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("research_domain", self.research_domain, RESEARCH_DOMAINS)
        _require_canonical_string("source_family", self.source_family)
        _require_canonical_string("team_id", self.team_id)
        _require_member("evidence_status", self.evidence_status, EVIDENCE_STATUSES)
        _require_positive_int("observation_count", self.observation_count)
        _require_positive_int("total_observation_count", self.total_observation_count)
        if self.observation_count > self.total_observation_count:
            raise ValueError("observation_count must not exceed total_observation_count")
        if self.observation_pct is None:
            object.__setattr__(
                self,
                "observation_pct",
                _percent(self.observation_count, self.total_observation_count),
            )
        else:
            object.__setattr__(
                self,
                "observation_pct",
                _quantize_percent("observation_pct", self.observation_pct),
            )
        object.__setattr__(
            self,
            "redacted_public_identifiers",
            _normalize_redacted_identifiers(self.redacted_public_identifiers),
        )
        require_paper_only_flags("TeamResearchCoverageMapRow", self)


@dataclass(frozen=True)
class TeamResearchCoverageMapReport:
    generated_at: datetime
    config_version: str
    coverage_status: str
    observation_count: int
    domain_summaries: tuple[TeamResearchCoverageMapSummary, ...]
    source_family_summaries: tuple[TeamResearchCoverageMapSummary, ...]
    team_summaries: tuple[TeamResearchCoverageMapSummary, ...]
    evidence_status_summaries: tuple[TeamResearchCoverageMapSummary, ...]
    coverage_rows: tuple[TeamResearchCoverageMapRow, ...]
    reason_codes: tuple[str, ...]
    covered_observation_count: int | None = None
    watch_observation_count: int | None = None
    gap_observation_count: int | None = None
    blocked_observation_count: int | None = None
    covered_observation_pct: Decimal | None = None
    team_evidence_summaries: (
        tuple[TeamResearchCoverageMapTeamEvidenceSummary, ...] | None
    ) = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("coverage_status", self.coverage_status, COVERAGE_STATUSES)
        _require_nonnegative_int("observation_count", self.observation_count)
        object.__setattr__(
            self,
            "domain_summaries",
            _normalize_summaries("domain_summaries", self.domain_summaries, "research_domain"),
        )
        object.__setattr__(
            self,
            "source_family_summaries",
            _normalize_summaries(
                "source_family_summaries",
                self.source_family_summaries,
                "source_family",
            ),
        )
        object.__setattr__(
            self,
            "team_summaries",
            _normalize_summaries("team_summaries", self.team_summaries, "team_id"),
        )
        object.__setattr__(
            self,
            "evidence_status_summaries",
            _normalize_summaries(
                "evidence_status_summaries",
                self.evidence_status_summaries,
                "evidence_status",
            ),
        )
        object.__setattr__(self, "coverage_rows", _normalize_rows(self.coverage_rows))
        if self.team_evidence_summaries is None:
            object.__setattr__(
                self,
                "team_evidence_summaries",
                _team_evidence_summaries_from_rows(self.coverage_rows),
            )
        else:
            object.__setattr__(
                self,
                "team_evidence_summaries",
                _normalize_team_evidence_summaries(self.team_evidence_summaries),
            )
        status_counts = _evidence_status_counts_from_rows(self.coverage_rows)
        for field_name, evidence_status in (
            ("covered_observation_count", "covered"),
            ("watch_observation_count", "watch"),
            ("gap_observation_count", "gap"),
            ("blocked_observation_count", "blocked"),
        ):
            if getattr(self, field_name) is None:
                object.__setattr__(self, field_name, status_counts[evidence_status])
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.covered_observation_pct is None and self.observation_count:
            object.__setattr__(
                self,
                "covered_observation_pct",
                _percent(self.covered_observation_count, self.observation_count),
            )
        elif self.covered_observation_pct is not None:
            object.__setattr__(
                self,
                "covered_observation_pct",
                _quantize_percent("covered_observation_pct", self.covered_observation_pct),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report_consistency(self)
        require_paper_only_flags("TeamResearchCoverageMapReport", self)


def build_team_research_coverage_map(
    observations: object,
    *,
    config: TeamResearchCoverageMapConfig,
    generated_at: datetime,
) -> TeamResearchCoverageMapReport:
    if type(config) is not TeamResearchCoverageMapConfig:
        raise ValueError("config must be a TeamResearchCoverageMapConfig")
    require_paper_only_flags("config", config)

    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_observations(observations)
    observation_count = len(rows)
    coverage_rows = _coverage_rows(rows)
    coverage_status = _coverage_status(rows)
    status_counts = _evidence_status_counts_from_observations(rows)
    return TeamResearchCoverageMapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        coverage_status=coverage_status,
        observation_count=observation_count,
        domain_summaries=_summaries(
            "research_domain",
            (row.research_domain for row in rows),
            total=observation_count,
        ),
        source_family_summaries=_summaries(
            "source_family",
            (row.source_family for row in rows),
            total=observation_count,
        ),
        team_summaries=_summaries(
            "team_id",
            (row.team_id for row in rows),
            total=observation_count,
        ),
        evidence_status_summaries=_summaries(
            "evidence_status",
            (row.evidence_status for row in rows),
            total=observation_count,
        ),
        coverage_rows=coverage_rows,
        reason_codes=_reason_codes(rows, coverage_status),
        covered_observation_count=status_counts["covered"],
        watch_observation_count=status_counts["watch"],
        gap_observation_count=status_counts["gap"],
        blocked_observation_count=status_counts["blocked"],
        covered_observation_pct=_optional_percent(
            status_counts["covered"],
            observation_count,
        ),
        team_evidence_summaries=_team_evidence_summaries(rows),
    )


def team_research_coverage_map_payload(value: TeamResearchCoverageMapReport) -> dict[str, Any]:
    if type(value) is not TeamResearchCoverageMapReport:
        raise ValueError("value must be a TeamResearchCoverageMapReport")
    require_paper_only_flags("TeamResearchCoverageMapReport", value)
    payload = json_ready_no_floats(asdict(value))
    if type(payload) is not dict:
        raise ValueError("coverage map payload must be a JSON object")
    for row in payload.get("coverage_rows", ()):
        if type(row) is dict and "redacted_public_identifiers" in row:
            row["redacted_ids"] = row.pop("redacted_public_identifiers")
    return payload


def redact_team_research_coverage_map_identifier(value: object) -> str:
    _require_canonical_string("public_identifier", value)
    digest = sha256(value.encode("utf-8")).hexdigest()
    return f"public_id_sha256:{digest[:16]}"


def _normalize_observations(value: object) -> tuple[TeamResearchCoverageMapObservation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamResearchCoverageMapObservation:
            raise ValueError("observations must contain TeamResearchCoverageMapObservation")
        require_paper_only_flags("TeamResearchCoverageMapObservation", row)
    return rows


def _coverage_rows(
    observations: tuple[TeamResearchCoverageMapObservation, ...],
) -> tuple[TeamResearchCoverageMapRow, ...]:
    total = len(observations)
    if total == 0:
        return ()
    buckets: dict[tuple[str, str, str, str], list[str]] = {}
    for observation in observations:
        key = (
            observation.research_domain,
            observation.source_family,
            observation.team_id,
            observation.evidence_status,
        )
        buckets.setdefault(key, []).append(observation.public_identifier)
    return tuple(
        TeamResearchCoverageMapRow(
            research_domain=research_domain,
            source_family=source_family,
            team_id=team_id,
            evidence_status=evidence_status,
            observation_count=len(public_identifiers),
            total_observation_count=total,
            redacted_public_identifiers=tuple(
                redact_team_research_coverage_map_identifier(public_identifier)
                for public_identifier in sorted(set(public_identifiers))
            ),
        )
        for (
            research_domain,
            source_family,
            team_id,
            evidence_status,
        ), public_identifiers in sorted(buckets.items())
    )


def _summaries(
    dimension: str,
    values: object,
    *,
    total: int,
) -> tuple[TeamResearchCoverageMapSummary, ...]:
    if total == 0:
        return ()
    counts: dict[str, int] = {}
    for value in values:
        _require_canonical_string(dimension, value)
        counts[value] = counts.get(value, 0) + 1
    return tuple(
        TeamResearchCoverageMapSummary(
            dimension=dimension,
            value=value,
            observation_count=count,
            observation_pct=_percent(count, total),
        )
        for value, count in sorted(counts.items())
    )


def _team_evidence_summaries(
    observations: tuple[TeamResearchCoverageMapObservation, ...],
) -> tuple[TeamResearchCoverageMapTeamEvidenceSummary, ...]:
    buckets: dict[str, dict[str, int]] = {}
    for observation in observations:
        bucket = buckets.setdefault(observation.team_id, _empty_evidence_counts())
        bucket["observation_count"] += 1
        bucket[f"{observation.evidence_status}_observation_count"] += 1
    return _team_evidence_summary_rows(buckets)


def _team_evidence_summaries_from_rows(
    rows: tuple[TeamResearchCoverageMapRow, ...],
) -> tuple[TeamResearchCoverageMapTeamEvidenceSummary, ...]:
    buckets: dict[str, dict[str, int]] = {}
    for row in rows:
        bucket = buckets.setdefault(row.team_id, _empty_evidence_counts())
        bucket["observation_count"] += row.observation_count
        bucket[f"{row.evidence_status}_observation_count"] += row.observation_count
    return _team_evidence_summary_rows(buckets)


def _team_evidence_summary_rows(
    buckets: dict[str, dict[str, int]],
) -> tuple[TeamResearchCoverageMapTeamEvidenceSummary, ...]:
    return tuple(
        TeamResearchCoverageMapTeamEvidenceSummary(
            team_id=team_id,
            observation_count=bucket["observation_count"],
            covered_observation_count=bucket["covered_observation_count"],
            watch_observation_count=bucket["watch_observation_count"],
            gap_observation_count=bucket["gap_observation_count"],
            blocked_observation_count=bucket["blocked_observation_count"],
        )
        for team_id, bucket in sorted(buckets.items())
    )


def _empty_evidence_counts() -> dict[str, int]:
    return {
        "observation_count": 0,
        "covered_observation_count": 0,
        "watch_observation_count": 0,
        "gap_observation_count": 0,
        "blocked_observation_count": 0,
    }


def _evidence_status_counts_from_observations(
    observations: tuple[TeamResearchCoverageMapObservation, ...],
) -> dict[str, int]:
    counts = {status: 0 for status in EVIDENCE_STATUSES}
    for observation in observations:
        counts[observation.evidence_status] += 1
    return counts


def _evidence_status_counts_from_rows(
    rows: tuple[TeamResearchCoverageMapRow, ...],
) -> dict[str, int]:
    counts = {status: 0 for status in EVIDENCE_STATUSES}
    for row in rows:
        counts[row.evidence_status] += row.observation_count
    return counts


def _coverage_status(rows: tuple[TeamResearchCoverageMapObservation, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.evidence_status == "blocked" for row in rows):
        return "blocked"
    if any(row.evidence_status in ("gap", "watch") for row in rows):
        return "watch"
    return "safe"


def _reason_codes(
    rows: tuple[TeamResearchCoverageMapObservation, ...],
    coverage_status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("empty_coverage_map",)
    reason_codes: list[str] = []
    if any(row.evidence_status == "blocked" for row in rows):
        reason_codes.append("blocked_evidence_present")
    if any(row.evidence_status == "gap" for row in rows):
        reason_codes.append("evidence_gaps_present")
    if any(row.evidence_status == "watch" for row in rows):
        reason_codes.append("watch_evidence_present")
    if not reason_codes and coverage_status == "safe":
        reason_codes.append("coverage_map_safe")
    return tuple(reason_codes)


def _normalize_summaries(
    field_name: str,
    value: object,
    dimension: str,
) -> tuple[TeamResearchCoverageMapSummary, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    rows = tuple(value)
    previous_value: str | None = None
    for row in rows:
        if type(row) is not TeamResearchCoverageMapSummary:
            raise ValueError(f"{field_name} must contain TeamResearchCoverageMapSummary")
        require_paper_only_flags("summary", row)
        if row.dimension != dimension:
            raise ValueError(f"{field_name} must use {dimension} dimension")
        if previous_value is not None and row.value <= previous_value:
            raise ValueError(f"{field_name} must be deterministic by value")
        previous_value = row.value
    return rows


def _normalize_rows(value: object) -> tuple[TeamResearchCoverageMapRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("coverage_rows must be a list or tuple")
    rows = tuple(value)
    previous_key: tuple[str, str, str, str] | None = None
    for row in rows:
        if type(row) is not TeamResearchCoverageMapRow:
            raise ValueError("coverage_rows must contain TeamResearchCoverageMapRow")
        require_paper_only_flags("coverage row", row)
        key = (row.research_domain, row.source_family, row.team_id, row.evidence_status)
        if previous_key is not None and key <= previous_key:
            raise ValueError("coverage_rows must be deterministic by coverage key")
        previous_key = key
    return rows


def _normalize_team_evidence_summaries(
    value: object,
) -> tuple[TeamResearchCoverageMapTeamEvidenceSummary, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("team_evidence_summaries must be a list or tuple")
    rows = tuple(value)
    previous_team_id: str | None = None
    for row in rows:
        if type(row) is not TeamResearchCoverageMapTeamEvidenceSummary:
            raise ValueError(
                "team_evidence_summaries must contain "
                "TeamResearchCoverageMapTeamEvidenceSummary",
            )
        require_paper_only_flags("team evidence summary", row)
        if previous_team_id is not None and row.team_id <= previous_team_id:
            raise ValueError("team_evidence_summaries must be deterministic by team_id")
        previous_team_id = row.team_id
    return rows


def _validate_report_consistency(report: TeamResearchCoverageMapReport) -> None:
    if report.observation_count != sum(row.observation_count for row in report.domain_summaries):
        raise ValueError("domain_summaries must match observation_count")
    if report.observation_count != sum(
        row.observation_count for row in report.source_family_summaries
    ):
        raise ValueError("source_family_summaries must match observation_count")
    if report.observation_count != sum(row.observation_count for row in report.team_summaries):
        raise ValueError("team_summaries must match observation_count")
    if report.observation_count != sum(
        row.observation_count for row in report.evidence_status_summaries
    ):
        raise ValueError("evidence_status_summaries must match observation_count")
    if report.observation_count != sum(row.observation_count for row in report.coverage_rows):
        raise ValueError("coverage_rows must match observation_count")
    status_counts = _evidence_status_counts_from_rows(report.coverage_rows)
    if report.covered_observation_count != status_counts["covered"]:
        raise ValueError("covered_observation_count must match coverage rows")
    if report.watch_observation_count != status_counts["watch"]:
        raise ValueError("watch_observation_count must match coverage rows")
    if report.gap_observation_count != status_counts["gap"]:
        raise ValueError("gap_observation_count must match coverage rows")
    if report.blocked_observation_count != status_counts["blocked"]:
        raise ValueError("blocked_observation_count must match coverage rows")
    if sum(status_counts.values()) != report.observation_count:
        raise ValueError("evidence status counts must match observation_count")
    if report.covered_observation_pct != _optional_percent(
        report.covered_observation_count,
        report.observation_count,
    ):
        raise ValueError("covered_observation_pct must match coverage rows")
    if report.team_evidence_summaries != _team_evidence_summaries_from_rows(
        report.coverage_rows,
    ):
        raise ValueError("team_evidence_summaries must match coverage rows")
    expected_status = _coverage_status_from_rows(report.coverage_rows)
    if report.coverage_status != expected_status:
        raise ValueError("coverage_status must match coverage rows")
    if report.reason_codes != _reason_codes_from_rows(report.coverage_rows, expected_status):
        raise ValueError("reason_codes must match coverage rows")


def _coverage_status_from_rows(rows: tuple[TeamResearchCoverageMapRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.evidence_status == "blocked" for row in rows):
        return "blocked"
    if any(row.evidence_status in ("gap", "watch") for row in rows):
        return "watch"
    return "safe"


def _reason_codes_from_rows(
    rows: tuple[TeamResearchCoverageMapRow, ...],
    coverage_status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("empty_coverage_map",)
    statuses = tuple(row.evidence_status for row in rows)
    reason_codes: list[str] = []
    if "blocked" in statuses:
        reason_codes.append("blocked_evidence_present")
    if "gap" in statuses:
        reason_codes.append("evidence_gaps_present")
    if "watch" in statuses:
        reason_codes.append("watch_evidence_present")
    if not reason_codes and coverage_status == "safe":
        reason_codes.append("coverage_map_safe")
    return tuple(reason_codes)


def _validate_team_evidence_summary_consistency(
    row: TeamResearchCoverageMapTeamEvidenceSummary,
) -> None:
    if (
        row.covered_observation_count
        + row.watch_observation_count
        + row.gap_observation_count
        + row.blocked_observation_count
        != row.observation_count
    ):
        raise ValueError("team evidence status counts must match observation_count")
    if row.covered_observation_pct != _percent(
        row.covered_observation_count,
        row.observation_count,
    ):
        raise ValueError("covered_observation_pct must match team evidence counts")


def _normalize_redacted_identifiers(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("redacted_public_identifiers must be a tuple of canonical strings")
    try:
        identifiers = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "redacted_public_identifiers must be a tuple of canonical strings",
        ) from exc
    if not identifiers:
        raise ValueError("redacted_public_identifiers must contain at least one value")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("redacted_public_identifiers must be unique")
    for identifier in identifiers:
        _require_canonical_string("redacted_public_identifiers", identifier)
        if not identifier.startswith("public_id_sha256:"):
            raise ValueError("redacted_public_identifiers must be redacted")
    return identifiers


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _percent(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO_PERCENT
    return ((Decimal(numerator) / Decimal(denominator)) * Decimal("100")).quantize(
        PERCENT_QUANT,
    )


def _optional_percent(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return _percent(numerator, denominator)


def _quantize_percent(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal("0") or value > Decimal("100"):
        raise ValueError(f"{field_name} must be between 0 and 100")
    return value.quantize(PERCENT_QUANT)


def _normalize_string_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple of canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple of canonical strings") from exc
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must contain at least one value")
    normalized: list[str] = []
    for item in items:
        _require_canonical_string(field_name, item)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed)}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    _require_int(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


__all__ = (
    "DEFAULT_TEAM_RESEARCH_COVERAGE_MAP_CONFIG_VERSION",
    "TeamResearchCoverageMapConfig",
    "TeamResearchCoverageMapObservation",
    "TeamResearchCoverageMapReport",
    "TeamResearchCoverageMapRow",
    "TeamResearchCoverageMapSummary",
    "TeamResearchCoverageMapTeamEvidenceSummary",
    "build_team_research_coverage_map",
    "redact_team_research_coverage_map_identifier",
    "team_research_coverage_map_payload",
)
