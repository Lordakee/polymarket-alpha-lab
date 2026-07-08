"""Pure report-only tennis event specialist memory readiness report."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair


DEFAULT_CONFIG_VERSION = "research-tennis-event-team-memory-report-v0"

READINESS_STATUSES = ("pass", "watch", "block")
EVIDENCE_FAMILIES = ("player_form", "injury", "news")

EMPTY_REASON = "tennis_event_team_memory_empty_observations"
PASS_REASON = "tennis_event_team_memory_pass"
WATCH_REASON = "tennis_event_team_memory_watch"
BLOCK_REASON = "tennis_event_team_memory_block"
WATCH_ROWS_REASON = "tennis_event_team_memory_watch_rows"
BLOCK_ROWS_REASON = "tennis_event_team_memory_block_rows"
AGING_EVIDENCE_REASON = "tennis_event_team_memory_aging_evidence"
STALE_EVIDENCE_REASON = "tennis_event_team_memory_stale_evidence"
MISSING_EVIDENCE_REASON = "tennis_event_team_memory_missing_evidence"
PLAYER_FORM_FRESH_REASON = "tennis_event_team_memory_player_form_fresh"
INJURY_FRESH_REASON = "tennis_event_team_memory_injury_fresh"
NEWS_FRESH_REASON = "tennis_event_team_memory_news_fresh"
CALIBRATION_READY_REASON = "tennis_event_team_memory_calibration_ready"
CALIBRATION_SAMPLE_GAP_REASON = "tennis_event_team_memory_calibration_sample_gap"

REASON_CODES = (
    EMPTY_REASON,
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    WATCH_ROWS_REASON,
    BLOCK_ROWS_REASON,
    AGING_EVIDENCE_REASON,
    STALE_EVIDENCE_REASON,
    MISSING_EVIDENCE_REASON,
    PLAYER_FORM_FRESH_REASON,
    INJURY_FRESH_REASON,
    NEWS_FRESH_REASON,
    CALIBRATION_READY_REASON,
    CALIBRATION_SAMPLE_GAP_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    AGING_EVIDENCE_REASON,
    STALE_EVIDENCE_REASON,
    MISSING_EVIDENCE_REASON,
    PLAYER_FORM_FRESH_REASON,
    INJURY_FRESH_REASON,
    NEWS_FRESH_REASON,
    CALIBRATION_READY_REASON,
    CALIBRATION_SAMPLE_GAP_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    EMPTY_REASON,
    PASS_REASON,
    WATCH_ROWS_REASON,
    BLOCK_ROWS_REASON,
    AGING_EVIDENCE_REASON,
    STALE_EVIDENCE_REASON,
    MISSING_EVIDENCE_REASON,
    CALIBRATION_SAMPLE_GAP_REASON,
)
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
RAW_IDENTIFIER_FRAGMENTS = (
    "raw_match",
    "raw_player",
    "raw_source",
    "match_id",
    "match_slug",
    "player_id",
    "player_name",
    "source_id",
    "source_key",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


@dataclass(frozen=True)
class ResearchTennisEventTeamMemoryReportConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_age_threshold_seconds: Decimal = Decimal("7200.000000")
    stale_age_threshold_seconds: Decimal = Decimal("14400.000000")
    minimum_calibration_sample_count: Decimal = Decimal("9.000000")
    max_brier_like_error: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "fresh_age_threshold_seconds",
            _require_positive_decimal(
                "fresh_age_threshold_seconds",
                self.fresh_age_threshold_seconds,
            ),
        )
        object.__setattr__(
            self,
            "stale_age_threshold_seconds",
            _require_positive_decimal(
                "stale_age_threshold_seconds",
                self.stale_age_threshold_seconds,
            ),
        )
        object.__setattr__(
            self,
            "minimum_calibration_sample_count",
            _require_positive_decimal(
                "minimum_calibration_sample_count",
                self.minimum_calibration_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "max_brier_like_error",
            _require_positive_decimal("max_brier_like_error", self.max_brier_like_error),
        )
        if self.fresh_age_threshold_seconds > self.stale_age_threshold_seconds:
            raise ValueError(
                "fresh_age_threshold_seconds must not exceed stale_age_threshold_seconds",
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchTennisEventTeamMemoryObservation:
    team_id: str
    category_id: str
    event_group: str
    specialist_role: str
    evidence_family: str
    last_refreshed_at: datetime | None
    evidence_count: Decimal
    calibration_sample_count: Decimal
    brier_like_error: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        require_team_category_pair("team_id", self.team_id, "category_id", self.category_id)
        _require_public_label("event_group", self.event_group)
        _require_public_label("specialist_role", self.specialist_role)
        _require_evidence_family("evidence_family", self.evidence_family)
        object.__setattr__(
            self,
            "last_refreshed_at",
            _as_optional_utc("last_refreshed_at", self.last_refreshed_at),
        )
        object.__setattr__(
            self,
            "evidence_count",
            _require_nonnegative_decimal("evidence_count", self.evidence_count),
        )
        object.__setattr__(
            self,
            "calibration_sample_count",
            _require_nonnegative_decimal(
                "calibration_sample_count",
                self.calibration_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "brier_like_error",
            _require_ratio_decimal("brier_like_error", self.brier_like_error),
        )
        require_paper_only_flags("observation", self)


@dataclass(frozen=True)
class ResearchTennisEventTeamMemoryRow:
    team_id: str
    category_id: str
    event_group: str
    specialist_role: str
    readiness_status: str
    observation_count: Decimal
    fresh_family_count: Decimal
    aging_family_count: Decimal
    stale_family_count: Decimal
    missing_family_count: Decimal
    player_form_fresh_count: Decimal
    injury_fresh_count: Decimal
    news_fresh_count: Decimal
    max_evidence_age_seconds: Decimal
    calibration_sample_count: Decimal
    brier_like_error: Decimal
    calibration_score: Decimal
    freshness_score: Decimal
    readiness_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        require_team_category_pair("team_id", self.team_id, "category_id", self.category_id)
        _require_public_label("event_group", self.event_group)
        _require_public_label("specialist_role", self.specialist_role)
        _require_readiness_status("readiness_status", self.readiness_status)
        for field_name in (
            "observation_count",
            "fresh_family_count",
            "aging_family_count",
            "stale_family_count",
            "missing_family_count",
            "player_form_fresh_count",
            "injury_fresh_count",
            "news_fresh_count",
            "max_evidence_age_seconds",
            "calibration_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "brier_like_error",
            "calibration_score",
            "freshness_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row_consistency(self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class ResearchTennisEventTeamMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_decimal("count", self.count))
        require_paper_only_flags("reason count", self)


@dataclass(frozen=True)
class ResearchTennisEventTeamMemoryReport:
    generated_at: datetime
    config_version: str
    readiness_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    observation_count: Decimal
    fresh_family_count: Decimal
    aging_family_count: Decimal
    stale_family_count: Decimal
    missing_family_count: Decimal
    player_form_fresh_count: Decimal
    injury_fresh_count: Decimal
    news_fresh_count: Decimal
    average_readiness_score: Decimal
    average_calibration_score: Decimal
    rows: tuple[ResearchTennisEventTeamMemoryRow, ...]
    reason_code_counts: tuple[ResearchTennisEventTeamMemoryReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_readiness_status("readiness_status", self.readiness_status)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "observation_count",
            "fresh_family_count",
            "aging_family_count",
            "stale_family_count",
            "missing_family_count",
            "player_form_fresh_count",
            "injury_fresh_count",
            "news_fresh_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_readiness_score", "average_calibration_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODE_SEQUENCE),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        require_paper_only_flags("report", self)
        reject_unsafe_surface_fields("research tennis event memory report", self.payload)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        payload = json_ready_no_floats(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _reject_raw_identifier_payload("payload", payload)
        return payload


def build_research_tennis_event_team_memory_report(
    observations: Sequence[ResearchTennisEventTeamMemoryObservation],
    *,
    generated_at: datetime,
    config: ResearchTennisEventTeamMemoryReportConfig | None = None,
) -> ResearchTennisEventTeamMemoryReport:
    if config is None:
        config = ResearchTennisEventTeamMemoryReportConfig()
    if type(config) is not ResearchTennisEventTeamMemoryReportConfig:
        raise ValueError("config must be a ResearchTennisEventTeamMemoryReportConfig")
    require_paper_only_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations, generated_at=generated_at)
    rows = _build_rows(normalized, generated_at=generated_at, config=config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "readiness_status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "observation_count": _sum_decimal(rows, "observation_count"),
        "fresh_family_count": _sum_decimal(rows, "fresh_family_count"),
        "aging_family_count": _sum_decimal(rows, "aging_family_count"),
        "stale_family_count": _sum_decimal(rows, "stale_family_count"),
        "missing_family_count": _sum_decimal(rows, "missing_family_count"),
        "player_form_fresh_count": _sum_decimal(rows, "player_form_fresh_count"),
        "injury_fresh_count": _sum_decimal(rows, "injury_fresh_count"),
        "news_fresh_count": _sum_decimal(rows, "news_fresh_count"),
        "average_readiness_score": _average(tuple(row.readiness_score for row in rows)),
        "average_calibration_score": _average(tuple(row.calibration_score for row in rows)),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTennisEventTeamMemoryReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_tennis_event_team_memory_report_payload(
    report: ResearchTennisEventTeamMemoryReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTennisEventTeamMemoryReport:
        require_paper_only_flags("report", report)
        payload = report.payload
        require_paper_only_flags("payload", _DictFlags(payload))
        reject_unsafe_surface_fields("research tennis event memory report", payload)
        _reject_raw_identifier_payload("payload", payload)
        return payload
    if type(report) is dict:
        reject_unsafe_surface_fields("research tennis event memory report", report)
        _reject_raw_identifier_payload("payload", report)
        payload = json_ready_no_floats(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        require_paper_only_flags("payload", _DictFlags(payload))
        return payload
    raise ValueError("report must be a ResearchTennisEventTeamMemoryReport or payload")


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _build_rows(
    observations: tuple[ResearchTennisEventTeamMemoryObservation, ...],
    *,
    generated_at: datetime,
    config: ResearchTennisEventTeamMemoryReportConfig,
) -> tuple[ResearchTennisEventTeamMemoryRow, ...]:
    groups: dict[tuple[str, str, str, str], list[ResearchTennisEventTeamMemoryObservation]] = {}
    for observation in observations:
        key = (
            observation.team_id,
            observation.category_id,
            observation.event_group,
            observation.specialist_role,
        )
        groups.setdefault(key, []).append(observation)
    rows = tuple(
        _build_row(
            team_id=team_id,
            category_id=category_id,
            event_group=event_group,
            specialist_role=specialist_role,
            observations=tuple(group),
            generated_at=generated_at,
            config=config,
        )
        for (team_id, category_id, event_group, specialist_role), group in sorted(
            groups.items(),
        )
    )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.readiness_status],
                row.event_group,
                row.specialist_role,
            ),
        ),
    )


def _build_row(
    *,
    team_id: str,
    category_id: str,
    event_group: str,
    specialist_role: str,
    observations: tuple[ResearchTennisEventTeamMemoryObservation, ...],
    generated_at: datetime,
    config: ResearchTennisEventTeamMemoryReportConfig,
) -> ResearchTennisEventTeamMemoryRow:
    family_map = {observation.evidence_family: observation for observation in observations}
    fresh_families: set[str] = set()
    aging_count = ZERO
    stale_count = ZERO
    missing_count = ZERO
    evidence_ages: list[Decimal] = []
    for family in EVIDENCE_FAMILIES:
        observation = family_map.get(family)
        if observation is None or not _has_evidence(observation):
            missing_count += ONE
            continue
        evidence_age = _age_seconds(generated_at, observation.last_refreshed_at)
        evidence_ages.append(evidence_age)
        if evidence_age <= config.fresh_age_threshold_seconds:
            fresh_families.add(family)
            continue
        if evidence_age <= config.stale_age_threshold_seconds:
            aging_count += ONE
            continue
        stale_count += ONE
    fresh_count = _decimal_count(len(fresh_families))
    player_form_fresh_count = _family_fresh_count(fresh_families, "player_form")
    injury_fresh_count = _family_fresh_count(fresh_families, "injury")
    news_fresh_count = _family_fresh_count(fresh_families, "news")
    calibration_sample_count = _sum_observation_decimal(
        observations,
        "calibration_sample_count",
    )
    brier_like_error = _average(
        tuple(observation.brier_like_error for observation in observations),
    )
    calibration_score = _calibration_score(brier_like_error, config)
    freshness_score = _ratio(fresh_count, _decimal_count(len(EVIDENCE_FAMILIES)))
    status = _row_status(
        aging_family_count=aging_count,
        stale_family_count=stale_count,
        missing_family_count=missing_count,
        calibration_sample_count=calibration_sample_count,
        config=config,
    )
    readiness_score = _row_readiness_score(
        readiness_status=status,
        freshness_score=freshness_score,
        calibration_score=calibration_score,
    )
    reason_codes = _row_reason_codes(
        readiness_status=status,
        aging_family_count=aging_count,
        stale_family_count=stale_count,
        missing_family_count=missing_count,
        player_form_fresh_count=player_form_fresh_count,
        injury_fresh_count=injury_fresh_count,
        news_fresh_count=news_fresh_count,
        calibration_sample_count=calibration_sample_count,
        config=config,
    )
    return ResearchTennisEventTeamMemoryRow(
        team_id=team_id,
        category_id=category_id,
        event_group=event_group,
        specialist_role=specialist_role,
        readiness_status=status,
        observation_count=_decimal_count(len(observations)),
        fresh_family_count=fresh_count,
        aging_family_count=aging_count,
        stale_family_count=stale_count,
        missing_family_count=missing_count,
        player_form_fresh_count=player_form_fresh_count,
        injury_fresh_count=injury_fresh_count,
        news_fresh_count=news_fresh_count,
        max_evidence_age_seconds=max(evidence_ages, default=ZERO),
        calibration_sample_count=calibration_sample_count,
        brier_like_error=brier_like_error,
        calibration_score=calibration_score,
        freshness_score=freshness_score,
        readiness_score=readiness_score,
        reason_codes=reason_codes,
    )


def _row_status(
    *,
    aging_family_count: Decimal,
    stale_family_count: Decimal,
    missing_family_count: Decimal,
    calibration_sample_count: Decimal,
    config: ResearchTennisEventTeamMemoryReportConfig,
) -> str:
    if (
        stale_family_count > ZERO
        or missing_family_count > ZERO
        or calibration_sample_count < config.minimum_calibration_sample_count
    ):
        return "block"
    if aging_family_count > ZERO:
        return "watch"
    return "pass"


def _row_readiness_score(
    *,
    readiness_status: str,
    freshness_score: Decimal,
    calibration_score: Decimal,
) -> Decimal:
    if readiness_status == "pass":
        return ONE
    return _average((freshness_score, calibration_score))


def _row_reason_codes(
    *,
    readiness_status: str,
    aging_family_count: Decimal,
    stale_family_count: Decimal,
    missing_family_count: Decimal,
    player_form_fresh_count: Decimal,
    injury_fresh_count: Decimal,
    news_fresh_count: Decimal,
    calibration_sample_count: Decimal,
    config: ResearchTennisEventTeamMemoryReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if readiness_status == "pass":
        reasons.append(PASS_REASON)
    elif readiness_status == "watch":
        reasons.append(WATCH_REASON)
    else:
        reasons.append(BLOCK_REASON)
    if aging_family_count > ZERO:
        reasons.append(AGING_EVIDENCE_REASON)
    if stale_family_count > ZERO:
        reasons.append(STALE_EVIDENCE_REASON)
    if missing_family_count > ZERO:
        reasons.append(MISSING_EVIDENCE_REASON)
    if player_form_fresh_count > ZERO:
        reasons.append(PLAYER_FORM_FRESH_REASON)
    if injury_fresh_count > ZERO:
        reasons.append(INJURY_FRESH_REASON)
    if news_fresh_count > ZERO:
        reasons.append(NEWS_FRESH_REASON)
    if calibration_sample_count < config.minimum_calibration_sample_count:
        reasons.append(CALIBRATION_SAMPLE_GAP_REASON)
    else:
        reasons.append(CALIBRATION_READY_REASON)
    return _normalize_reason_codes(tuple(reasons), ROW_REASON_CODE_SEQUENCE)


def _report_status(rows: tuple[ResearchTennisEventTeamMemoryRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.readiness_status == "block" for row in rows):
        return "block"
    if any(row.readiness_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTennisEventTeamMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons: list[str] = []
    if any(row.readiness_status == "watch" for row in rows):
        reasons.append(WATCH_ROWS_REASON)
    if any(row.readiness_status == "block" for row in rows):
        reasons.append(BLOCK_ROWS_REASON)
    for reason in (
        AGING_EVIDENCE_REASON,
        STALE_EVIDENCE_REASON,
        MISSING_EVIDENCE_REASON,
        CALIBRATION_SAMPLE_GAP_REASON,
    ):
        if any(reason in row.reason_codes for row in rows):
            reasons.append(reason)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes(tuple(reasons), REPORT_REASON_CODE_SEQUENCE)


def _reason_code_counts(
    rows: tuple[ResearchTennisEventTeamMemoryRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTennisEventTeamMemoryReasonCodeCount, ...]:
    if reason_codes == (EMPTY_REASON,):
        return (
            ResearchTennisEventTeamMemoryReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
            ),
        )
    counts: list[ResearchTennisEventTeamMemoryReasonCodeCount] = []
    for reason_code in reason_codes:
        count = _reason_code_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                ResearchTennisEventTeamMemoryReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                ),
            )
    return tuple(counts)


def _reason_code_count(
    rows: tuple[ResearchTennisEventTeamMemoryRow, ...],
    reason_code: str,
) -> Decimal:
    if reason_code == WATCH_ROWS_REASON:
        return _status_count(rows, "watch")
    if reason_code == BLOCK_ROWS_REASON:
        return _status_count(rows, "block")
    return _decimal_count(sum(reason_code in row.reason_codes for row in rows))


def _normalize_observations(
    observations: Sequence[ResearchTennisEventTeamMemoryObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchTennisEventTeamMemoryObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized = tuple(observations)
    seen: set[tuple[str, str, str, str, str]] = set()
    for observation in normalized:
        if type(observation) is not ResearchTennisEventTeamMemoryObservation:
            raise ValueError(
                "observations must contain ResearchTennisEventTeamMemoryObservation",
            )
        require_paper_only_flags("observation", observation)
        if observation.last_refreshed_at is not None and observation.last_refreshed_at > generated_at:
            raise ValueError("last_refreshed_at must not be in the future")
        key = (
            observation.team_id,
            observation.category_id,
            observation.event_group,
            observation.specialist_role,
            observation.evidence_family,
        )
        if key in seen:
            raise ValueError("duplicate team/category/event/specialist/evidence family")
        seen.add(key)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.team_id,
                item.category_id,
                item.event_group,
                item.specialist_role,
                item.evidence_family,
            ),
        ),
    )


def _normalize_rows(value: object) -> tuple[ResearchTennisEventTeamMemoryRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchTennisEventTeamMemoryRow:
            raise ValueError("rows must contain ResearchTennisEventTeamMemoryRow")
        require_paper_only_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTennisEventTeamMemoryReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    for count in counts:
        if type(count) is not ResearchTennisEventTeamMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchTennisEventTeamMemoryReasonCodeCount",
            )
        require_paper_only_flags("reason count", count)
    return counts


def _normalize_reason_codes(
    value: object,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in sequence if reason_code in seen)


def _family_fresh_count(fresh_families: set[str], family: str) -> Decimal:
    return ONE if family in fresh_families else ZERO


def _has_evidence(observation: ResearchTennisEventTeamMemoryObservation) -> bool:
    return observation.last_refreshed_at is not None and observation.evidence_count > ZERO


def _calibration_score(
    brier_like_error: Decimal,
    config: ResearchTennisEventTeamMemoryReportConfig,
) -> Decimal:
    penalty = _ratio(brier_like_error, config.max_brier_like_error)
    return _quantize(max(ZERO, ONE - penalty))


def _sum_observation_decimal(
    observations: tuple[ResearchTennisEventTeamMemoryObservation, ...],
    field_name: str,
) -> Decimal:
    total = ZERO
    for observation in observations:
        value = getattr(observation, field_name)
        if type(value) is not Decimal:
            raise ValueError(f"{field_name} must be exactly Decimal")
        total += value
    return _quantize(total)


def _sum_decimal(rows: tuple[object, ...], field_name: str) -> Decimal:
    total = ZERO
    for row in rows:
        value = getattr(row, field_name)
        if type(value) is not Decimal:
            raise ValueError(f"{field_name} must be exactly Decimal")
        total += value
    return _quantize(total)


def _status_count(
    rows: tuple[ResearchTennisEventTeamMemoryRow, ...],
    readiness_status: str,
) -> Decimal:
    return _decimal_count(sum(row.readiness_status == readiness_status for row in rows))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("average values must be exactly Decimal")
        total += value
    return _ratio(total, _decimal_count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + microseconds)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use six decimal places or fewer") from exc


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    return value


def _require_public_label(field_name: str, value: object) -> str:
    normalized = _require_canonical_string(field_name, value)
    lowered = normalized.lower()
    for fragment in RAW_IDENTIFIER_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} has raw identifier surface")
    return normalized


def _require_evidence_family(field_name: str, value: object) -> str:
    if type(value) is not str or value not in EVIDENCE_FAMILIES:
        raise ValueError(f"{field_name} must be a tennis evidence family")
    return value


def _require_readiness_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in READINESS_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _validate_row_consistency(row: ResearchTennisEventTeamMemoryRow) -> None:
    if row.fresh_family_count > _decimal_count(len(EVIDENCE_FAMILIES)):
        raise ValueError("fresh_family_count must not exceed tennis evidence families")
    family_fresh_total = (
        row.player_form_fresh_count + row.injury_fresh_count + row.news_fresh_count
    )
    if _quantize(family_fresh_total) != row.fresh_family_count:
        raise ValueError("fresh family detail counts must match fresh_family_count")
    if row.readiness_status == "pass" and PASS_REASON not in row.reason_codes:
        raise ValueError("pass rows must include pass reason")
    if row.readiness_status == "watch" and WATCH_REASON not in row.reason_codes:
        raise ValueError("watch rows must include watch reason")
    if row.readiness_status == "block" and BLOCK_REASON not in row.reason_codes:
        raise ValueError("block rows must include block reason")


def _validate_report_consistency(report: ResearchTennisEventTeamMemoryReport) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.readiness_status != _report_status(rows):
        raise ValueError("readiness_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _report_values_without_digest(
    report: ResearchTennisEventTeamMemoryReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = json_ready_no_floats(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    reject_unsafe_surface_fields("research tennis event memory report digest", payload)
    _reject_raw_identifier_payload("digest payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _reject_raw_identifier_payload(label: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in RAW_IDENTIFIER_FRAGMENTS):
            raise ValueError(f"{label} has raw identifier surface")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in RAW_IDENTIFIER_FRAGMENTS):
                raise ValueError(f"{label} has raw identifier surface")
            _reject_raw_identifier_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_raw_identifier_payload(label, item)


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "EVIDENCE_FAMILIES",
    "READINESS_STATUSES",
    "ResearchTennisEventTeamMemoryObservation",
    "ResearchTennisEventTeamMemoryReasonCodeCount",
    "ResearchTennisEventTeamMemoryReport",
    "ResearchTennisEventTeamMemoryReportConfig",
    "ResearchTennisEventTeamMemoryRow",
    "build_research_tennis_event_team_memory_report",
    "research_tennis_event_team_memory_report_payload",
)
