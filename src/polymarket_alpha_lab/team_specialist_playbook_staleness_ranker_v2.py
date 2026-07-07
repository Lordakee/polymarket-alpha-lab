"""Phase 1 paper-only ranker for stale specialist playbooks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_TEAM_SPECIALIST_PLAYBOOK_STALENESS_RANKER_V2_CONFIG_VERSION = (
    "team-specialist-playbook-staleness-ranker-v2-phase1"
)

STATUS_VALUES = ("stale", "watch", "fresh")
ROW_REASON_CODES = (
    "team_specialist_playbook_staleness_last_used_age",
    "team_specialist_playbook_staleness_recent_misses",
    "team_specialist_playbook_staleness_source_family_drift",
    "team_specialist_playbook_staleness_resolution_rule_drift",
    "team_specialist_playbook_staleness_category_coverage_gap",
    "team_specialist_playbook_staleness_sample_size_thin",
    "team_specialist_playbook_staleness_stale",
    "team_specialist_playbook_staleness_watch",
    "team_specialist_playbook_staleness_fresh",
)
REPORT_REASON_CODES = (
    "team_specialist_playbook_staleness_rank_stale_rows",
    "team_specialist_playbook_staleness_rank_watch_rows",
    "team_specialist_playbook_staleness_rank_fresh_rows",
    "team_specialist_playbook_staleness_rank_empty",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
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

DECIMAL_CONTEXT = Context(prec=64)
ZERO = Decimal("0")
ONE = Decimal("1")
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400")


@dataclass(frozen=True)
class TeamSpecialistPlaybookStalenessRankerV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_PLAYBOOK_STALENESS_RANKER_V2_CONFIG_VERSION
    )
    last_used_age_weight: Decimal = Decimal("0.250000")
    recent_miss_weight: Decimal = Decimal("0.200000")
    source_family_drift_weight: Decimal = Decimal("0.150000")
    resolution_rule_drift_weight: Decimal = Decimal("0.150000")
    category_coverage_gap_weight: Decimal = Decimal("0.150000")
    sample_size_weight: Decimal = Decimal("0.100000")
    max_last_used_age_days: Decimal = Decimal("90.000000")
    max_recent_miss_count: Decimal = Decimal("5")
    min_sample_size: Decimal = Decimal("20")
    stale_score_floor: Decimal = Decimal("0.700000")
    watch_score_floor: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_PLAYBOOK_STALENESS_RANKER_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "last_used_age_weight",
            "recent_miss_weight",
            "source_family_drift_weight",
            "resolution_rule_drift_weight",
            "category_coverage_gap_weight",
            "sample_size_weight",
            "stale_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_last_used_age_days",
            _normalize_positive_decimal(
                "max_last_used_age_days",
                self.max_last_used_age_days,
            ),
        )
        for field_name in ("max_recent_miss_count", "min_sample_size"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        _require_ratio_total(
            self.last_used_age_weight,
            self.recent_miss_weight,
            self.source_family_drift_weight,
            self.resolution_rule_drift_weight,
            self.category_coverage_gap_weight,
            self.sample_size_weight,
        )
        if self.watch_score_floor > self.stale_score_floor:
            raise ValueError("watch_score_floor must not exceed stale_score_floor")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", asdict(self))


@dataclass(frozen=True)
class TeamSpecialistPlaybookStalenessRankerV2Context:
    review_id: str
    required_category_ids: tuple[str, ...]
    required_source_family_ids: tuple[str, ...]
    required_resolution_rule_ids: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("review_id", self.review_id)
        object.__setattr__(
            self,
            "required_category_ids",
            _normalize_public_refs(
                "required_category_ids",
                self.required_category_ids,
            ),
        )
        object.__setattr__(
            self,
            "required_source_family_ids",
            _normalize_public_refs(
                "required_source_family_ids",
                self.required_source_family_ids,
            ),
        )
        object.__setattr__(
            self,
            "required_resolution_rule_ids",
            _normalize_public_refs(
                "required_resolution_rule_ids",
                self.required_resolution_rule_ids,
            ),
        )
        _require_hard_flags("review_context", self)
        _reject_unsafe_public_payload("review_context", asdict(self))


@dataclass(frozen=True)
class TeamSpecialistPlaybookStalenessRankerV2Playbook:
    team_id: str
    specialist_id: str
    playbook_id: str
    category_ids: tuple[str, ...]
    source_family_ids: tuple[str, ...]
    resolution_rule_ids: tuple[str, ...]
    last_used_at: datetime
    recent_miss_count: Decimal
    sample_size: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "specialist_id", "playbook_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "category_ids",
            _normalize_optional_public_refs("category_ids", self.category_ids),
        )
        object.__setattr__(
            self,
            "source_family_ids",
            _normalize_optional_public_refs("source_family_ids", self.source_family_ids),
        )
        object.__setattr__(
            self,
            "resolution_rule_ids",
            _normalize_optional_public_refs(
                "resolution_rule_ids",
                self.resolution_rule_ids,
            ),
        )
        object.__setattr__(self, "last_used_at", _as_utc("last_used_at", self.last_used_at))
        for field_name in ("recent_miss_count", "sample_size"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("playbook", self)
        _reject_unsafe_public_payload("playbook", asdict(self))


@dataclass(frozen=True)
class TeamSpecialistPlaybookStalenessRankerV2Row:
    rank: Decimal
    review_id: str
    team_id: str
    specialist_id: str
    playbook_id: str
    last_used_at: datetime
    last_used_age_days: Decimal
    last_used_age_score: Decimal
    recent_miss_count: Decimal
    recent_miss_score: Decimal
    required_source_family_count: Decimal
    matched_source_family_count: Decimal
    missing_source_family_count: Decimal
    matched_source_family_ids: tuple[str, ...]
    source_family_drift_score: Decimal
    required_resolution_rule_count: Decimal
    matched_resolution_rule_count: Decimal
    missing_resolution_rule_count: Decimal
    matched_resolution_rule_ids: tuple[str, ...]
    resolution_rule_drift_score: Decimal
    required_category_count: Decimal
    matched_category_count: Decimal
    missing_category_count: Decimal
    matched_category_ids: tuple[str, ...]
    category_coverage_gap_score: Decimal
    sample_size: Decimal
    sample_size_gap_score: Decimal
    staleness_score: Decimal
    staleness_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_count("rank", self.rank))
        for field_name in ("review_id", "team_id", "specialist_id", "playbook_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "last_used_at",
            _as_utc("last_used_at", self.last_used_at),
        )
        for field_name in (
            "last_used_age_days",
            "last_used_age_score",
            "recent_miss_score",
            "source_family_drift_score",
            "resolution_rule_drift_score",
            "category_coverage_gap_score",
            "sample_size_gap_score",
            "staleness_score",
        ):
            normalizer = (
                _normalize_nonnegative_decimal
                if field_name == "last_used_age_days"
                else _normalize_ratio
            )
            object.__setattr__(
                self,
                field_name,
                normalizer(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recent_miss_count",
            "required_source_family_count",
            "matched_source_family_count",
            "missing_source_family_count",
            "required_resolution_rule_count",
            "matched_resolution_rule_count",
            "missing_resolution_rule_count",
            "required_category_count",
            "matched_category_count",
            "missing_category_count",
            "sample_size",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "matched_source_family_ids",
            _normalize_optional_public_refs(
                "matched_source_family_ids",
                self.matched_source_family_ids,
            ),
        )
        object.__setattr__(
            self,
            "matched_resolution_rule_ids",
            _normalize_optional_public_refs(
                "matched_resolution_rule_ids",
                self.matched_resolution_rule_ids,
            ),
        )
        object.__setattr__(
            self,
            "matched_category_ids",
            _normalize_optional_public_refs(
                "matched_category_ids",
                self.matched_category_ids,
            ),
        )
        _require_status("staleness_status", self.staleness_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row_counts(self)
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _row_digest(self):
            raise ValueError("derived_validation_digest must match row fields")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class TeamSpecialistPlaybookStalenessRankerV2Report:
    generated_at: datetime
    config_version: str
    review_id: str
    playbook_count: Decimal
    stale_count: Decimal
    watch_count: Decimal
    fresh_count: Decimal
    average_staleness_score: Decimal
    top_staleness_score: Decimal
    rank_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[TeamSpecialistPlaybookStalenessRankerV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_PLAYBOOK_STALENESS_RANKER_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_public_string("review_id", self.review_id)
        for field_name in ("playbook_count", "stale_count", "watch_count", "fresh_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_staleness_score", "top_staleness_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("rank_status", self.rank_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_counts_status_and_reasons(self)
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _report_digest(self):
            raise ValueError("derived_validation_digest must match report fields")
        _validate_report_scores(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self.payload)

    @property
    def payload(self) -> dict[str, Any]:
        return team_specialist_playbook_staleness_ranker_v2_payload(self)


def build_team_specialist_playbook_staleness_ranker_v2_report(
    *,
    review_context: TeamSpecialistPlaybookStalenessRankerV2Context,
    playbooks: object,
    generated_at: datetime,
    config: TeamSpecialistPlaybookStalenessRankerV2Config | None = None,
) -> TeamSpecialistPlaybookStalenessRankerV2Report:
    if type(review_context) is not TeamSpecialistPlaybookStalenessRankerV2Context:
        raise ValueError(
            "review_context must be TeamSpecialistPlaybookStalenessRankerV2Context",
        )
    _require_hard_flags("review_context", review_context)
    if config is None:
        config = TeamSpecialistPlaybookStalenessRankerV2Config()
    if type(config) is not TeamSpecialistPlaybookStalenessRankerV2Config:
        raise ValueError(
            "config must be a TeamSpecialistPlaybookStalenessRankerV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_playbooks = _normalize_playbooks(playbooks)
    for playbook in normalized_playbooks:
        if playbook.last_used_at > generated_at_utc:
            raise ValueError("last_used_at must be on or before generated_at")

    rows_without_rank = tuple(
        _row_parts(review_context, playbook, generated_at_utc, config)
        for playbook in normalized_playbooks
    )
    ranked_rows = tuple(
        TeamSpecialistPlaybookStalenessRankerV2Row(
            **parts,
            rank=_count(index),
            derived_validation_digest=_digest_public({**parts, "rank": _count(index)}),
        )
        for index, parts in enumerate(
            sorted(rows_without_rank, key=_row_parts_sort_key),
            start=1,
        )
    )
    report_parts = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "review_id": review_context.review_id,
        "playbook_count": _count(len(ranked_rows)),
        "stale_count": _count(
            sum(1 for row in ranked_rows if row.staleness_status == "stale"),
        ),
        "watch_count": _count(
            sum(1 for row in ranked_rows if row.staleness_status == "watch"),
        ),
        "fresh_count": _count(
            sum(1 for row in ranked_rows if row.staleness_status == "fresh"),
        ),
        "average_staleness_score": _average_staleness_score(ranked_rows),
        "top_staleness_score": _top_staleness_score(ranked_rows),
        "rank_status": _report_status(ranked_rows),
        "reason_codes": _report_reason_codes(ranked_rows),
        "rows": ranked_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return TeamSpecialistPlaybookStalenessRankerV2Report(
        **report_parts,
        derived_validation_digest=_digest_public(report_parts),
    )


def team_specialist_playbook_staleness_ranker_v2_payload(
    report: TeamSpecialistPlaybookStalenessRankerV2Report,
) -> dict[str, Any]:
    if type(report) is not TeamSpecialistPlaybookStalenessRankerV2Report:
        raise ValueError(
            "report must be a TeamSpecialistPlaybookStalenessRankerV2Report",
        )
    _require_hard_flags("report", report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = _json_ready(report)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _row_parts(
    review_context: TeamSpecialistPlaybookStalenessRankerV2Context,
    playbook: TeamSpecialistPlaybookStalenessRankerV2Playbook,
    generated_at: datetime,
    config: TeamSpecialistPlaybookStalenessRankerV2Config,
) -> dict[str, object]:
    matched_source_family_ids = tuple(
        source_family_id
        for source_family_id in review_context.required_source_family_ids
        if source_family_id in playbook.source_family_ids
    )
    matched_resolution_rule_ids = tuple(
        resolution_rule_id
        for resolution_rule_id in review_context.required_resolution_rule_ids
        if resolution_rule_id in playbook.resolution_rule_ids
    )
    matched_category_ids = tuple(
        category_id
        for category_id in review_context.required_category_ids
        if category_id in playbook.category_ids
    )
    required_source_family_count = _count(
        len(review_context.required_source_family_ids),
    )
    matched_source_family_count = _count(len(matched_source_family_ids))
    missing_source_family_count = (
        required_source_family_count - matched_source_family_count
    ).quantize(COUNT_QUANTUM)
    required_resolution_rule_count = _count(
        len(review_context.required_resolution_rule_ids),
    )
    matched_resolution_rule_count = _count(len(matched_resolution_rule_ids))
    missing_resolution_rule_count = (
        required_resolution_rule_count - matched_resolution_rule_count
    ).quantize(COUNT_QUANTUM)
    required_category_count = _count(len(review_context.required_category_ids))
    matched_category_count = _count(len(matched_category_ids))
    missing_category_count = (
        required_category_count - matched_category_count
    ).quantize(COUNT_QUANTUM)

    last_used_age_days = _age_days(generated_at, playbook.last_used_at)
    last_used_age_score = _count_ratio(
        last_used_age_days,
        config.max_last_used_age_days,
    )
    recent_miss_score = _count_ratio(
        playbook.recent_miss_count,
        config.max_recent_miss_count,
    )
    source_family_drift_score = _count_ratio(
        missing_source_family_count,
        required_source_family_count,
    )
    resolution_rule_drift_score = _count_ratio(
        missing_resolution_rule_count,
        required_resolution_rule_count,
    )
    category_coverage_gap_score = _count_ratio(
        missing_category_count,
        required_category_count,
    )
    sample_size_gap_score = _sample_size_gap_score(playbook.sample_size, config)
    staleness_score = _staleness_score(
        last_used_age_score=last_used_age_score,
        recent_miss_score=recent_miss_score,
        source_family_drift_score=source_family_drift_score,
        resolution_rule_drift_score=resolution_rule_drift_score,
        category_coverage_gap_score=category_coverage_gap_score,
        sample_size_gap_score=sample_size_gap_score,
        config=config,
    )
    staleness_status = _row_status(staleness_score, config)

    return {
        "review_id": review_context.review_id,
        "team_id": playbook.team_id,
        "specialist_id": playbook.specialist_id,
        "playbook_id": playbook.playbook_id,
        "last_used_at": playbook.last_used_at,
        "last_used_age_days": last_used_age_days,
        "last_used_age_score": last_used_age_score,
        "recent_miss_count": playbook.recent_miss_count,
        "recent_miss_score": recent_miss_score,
        "required_source_family_count": required_source_family_count,
        "matched_source_family_count": matched_source_family_count,
        "missing_source_family_count": missing_source_family_count,
        "matched_source_family_ids": matched_source_family_ids,
        "source_family_drift_score": source_family_drift_score,
        "required_resolution_rule_count": required_resolution_rule_count,
        "matched_resolution_rule_count": matched_resolution_rule_count,
        "missing_resolution_rule_count": missing_resolution_rule_count,
        "matched_resolution_rule_ids": matched_resolution_rule_ids,
        "resolution_rule_drift_score": resolution_rule_drift_score,
        "required_category_count": required_category_count,
        "matched_category_count": matched_category_count,
        "missing_category_count": missing_category_count,
        "matched_category_ids": matched_category_ids,
        "category_coverage_gap_score": category_coverage_gap_score,
        "sample_size": playbook.sample_size,
        "sample_size_gap_score": sample_size_gap_score,
        "staleness_score": staleness_score,
        "staleness_status": staleness_status,
        "reason_codes": _row_reason_codes(
            staleness_status=staleness_status,
            last_used_age_score=last_used_age_score,
            recent_miss_score=recent_miss_score,
            source_family_drift_score=source_family_drift_score,
            resolution_rule_drift_score=resolution_rule_drift_score,
            category_coverage_gap_score=category_coverage_gap_score,
            sample_size_gap_score=sample_size_gap_score,
            config=config,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_parts_sort_key(parts: dict[str, object]) -> tuple[Decimal, str, str, str]:
    score = parts["staleness_score"]
    if type(score) is not Decimal:
        raise ValueError("staleness_score must be a Decimal")
    return (
        -score,
        str(parts["team_id"]),
        str(parts["specialist_id"]),
        str(parts["playbook_id"]),
    )


def _row_sort_key(
    row: TeamSpecialistPlaybookStalenessRankerV2Row,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        -row.staleness_score,
        row.rank,
        row.team_id,
        row.specialist_id,
        row.playbook_id,
    )


def _staleness_score(
    *,
    last_used_age_score: Decimal,
    recent_miss_score: Decimal,
    source_family_drift_score: Decimal,
    resolution_rule_drift_score: Decimal,
    category_coverage_gap_score: Decimal,
    sample_size_gap_score: Decimal,
    config: TeamSpecialistPlaybookStalenessRankerV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            last_used_age_score * config.last_used_age_weight
            + recent_miss_score * config.recent_miss_weight
            + source_family_drift_score * config.source_family_drift_weight
            + resolution_rule_drift_score * config.resolution_rule_drift_weight
            + category_coverage_gap_score * config.category_coverage_gap_weight
            + sample_size_gap_score * config.sample_size_weight,
        )


def _sample_size_gap_score(
    sample_size: Decimal,
    config: TeamSpecialistPlaybookStalenessRankerV2Config,
) -> Decimal:
    return _clamp_ratio(ONE - _count_ratio(sample_size, config.min_sample_size))


def _row_reason_codes(
    *,
    staleness_status: str,
    last_used_age_score: Decimal,
    recent_miss_score: Decimal,
    source_family_drift_score: Decimal,
    resolution_rule_drift_score: Decimal,
    category_coverage_gap_score: Decimal,
    sample_size_gap_score: Decimal,
    config: TeamSpecialistPlaybookStalenessRankerV2Config,
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    if last_used_age_score >= config.watch_score_floor:
        reason_codes.add("team_specialist_playbook_staleness_last_used_age")
    if recent_miss_score > ZERO:
        reason_codes.add("team_specialist_playbook_staleness_recent_misses")
    if source_family_drift_score > ZERO:
        reason_codes.add("team_specialist_playbook_staleness_source_family_drift")
    if resolution_rule_drift_score > ZERO:
        reason_codes.add("team_specialist_playbook_staleness_resolution_rule_drift")
    if category_coverage_gap_score > ZERO:
        reason_codes.add("team_specialist_playbook_staleness_category_coverage_gap")
    if sample_size_gap_score > ZERO:
        reason_codes.add("team_specialist_playbook_staleness_sample_size_thin")
    reason_codes.add(f"team_specialist_playbook_staleness_{staleness_status}")
    return tuple(reason for reason in ROW_REASON_CODES if reason in reason_codes)


def _report_reason_codes(
    rows: tuple[TeamSpecialistPlaybookStalenessRankerV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("team_specialist_playbook_staleness_rank_empty",)
    reason_codes: list[str] = []
    if any(row.staleness_status == "stale" for row in rows):
        reason_codes.append("team_specialist_playbook_staleness_rank_stale_rows")
    if any(row.staleness_status == "watch" for row in rows):
        reason_codes.append("team_specialist_playbook_staleness_rank_watch_rows")
    if any(row.staleness_status == "fresh" for row in rows):
        reason_codes.append("team_specialist_playbook_staleness_rank_fresh_rows")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _row_status(
    staleness_score: Decimal,
    config: TeamSpecialistPlaybookStalenessRankerV2Config,
) -> str:
    if staleness_score >= config.stale_score_floor:
        return "stale"
    if staleness_score >= config.watch_score_floor:
        return "watch"
    return "fresh"


def _report_status(
    rows: tuple[TeamSpecialistPlaybookStalenessRankerV2Row, ...],
) -> str:
    if any(row.staleness_status == "stale" for row in rows):
        return "stale"
    if any(row.staleness_status == "watch" for row in rows):
        return "watch"
    return "fresh"


def _average_staleness_score(
    rows: tuple[TeamSpecialistPlaybookStalenessRankerV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.staleness_score for row in rows), ZERO) / Decimal(len(rows)),
        )


def _top_staleness_score(
    rows: tuple[TeamSpecialistPlaybookStalenessRankerV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANTUM)
    return max(row.staleness_score for row in rows).quantize(RATIO_QUANTUM)


def _normalize_playbooks(
    playbooks: object,
) -> tuple[TeamSpecialistPlaybookStalenessRankerV2Playbook, ...]:
    if type(playbooks) not in (list, tuple):
        raise ValueError("playbooks must be a list or tuple")
    normalized = tuple(playbooks)
    seen_keys: set[tuple[str, str, str]] = set()
    for playbook in normalized:
        if type(playbook) is not TeamSpecialistPlaybookStalenessRankerV2Playbook:
            raise ValueError(
                "playbooks must contain TeamSpecialistPlaybookStalenessRankerV2Playbook",
            )
        _require_hard_flags("playbook", playbook)
        key = (playbook.team_id, playbook.specialist_id, playbook.playbook_id)
        if key in seen_keys:
            raise ValueError("playbooks must have unique public keys")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[TeamSpecialistPlaybookStalenessRankerV2Row, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not TeamSpecialistPlaybookStalenessRankerV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistPlaybookStalenessRankerV2Row values",
            )
        _require_hard_flags("row", row)
        key = (row.team_id, row.specialist_id, row.playbook_id)
        if key in seen_keys:
            raise ValueError("rows must have unique public keys")
        seen_keys.add(key)
    return normalized


def _validate_row_counts(row: TeamSpecialistPlaybookStalenessRankerV2Row) -> None:
    if row.required_source_family_count <= ZERO:
        raise ValueError("required_source_family_count must be positive")
    if row.required_resolution_rule_count <= ZERO:
        raise ValueError("required_resolution_rule_count must be positive")
    if row.required_category_count <= ZERO:
        raise ValueError("required_category_count must be positive")
    if row.matched_source_family_count > row.required_source_family_count:
        raise ValueError("matched_source_family_count must not exceed required")
    if row.matched_resolution_rule_count > row.required_resolution_rule_count:
        raise ValueError("matched_resolution_rule_count must not exceed required")
    if row.matched_category_count > row.required_category_count:
        raise ValueError("matched_category_count must not exceed required")
    if (
        row.matched_source_family_count
        != _count(len(row.matched_source_family_ids))
        or row.matched_resolution_rule_count
        != _count(len(row.matched_resolution_rule_ids))
        or row.matched_category_count
        != _count(len(row.matched_category_ids))
    ):
        raise ValueError("matched counts must match matched identifiers")
    if (
        row.missing_source_family_count
        != row.required_source_family_count - row.matched_source_family_count
        or row.missing_resolution_rule_count
        != row.required_resolution_rule_count - row.matched_resolution_rule_count
        or row.missing_category_count
        != row.required_category_count - row.matched_category_count
    ):
        raise ValueError("missing counts must match required and matched counts")
    status_reason = f"team_specialist_playbook_staleness_{row.staleness_status}"
    if status_reason not in row.reason_codes:
        raise ValueError("staleness_status reason must be present")


def _validate_report_counts_status_and_reasons(
    report: TeamSpecialistPlaybookStalenessRankerV2Report,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by staleness score and rank")
    if tuple(row.rank for row in report.rows) != tuple(
        _count(index) for index in range(1, len(report.rows) + 1)
    ):
        raise ValueError("rows must be sorted by staleness score and rank")
    if report.playbook_count != _count(len(report.rows)):
        raise ValueError("playbook_count must match rows")
    if (
        report.stale_count
        != _count(sum(1 for row in report.rows if row.staleness_status == "stale"))
        or report.watch_count
        != _count(sum(1 for row in report.rows if row.staleness_status == "watch"))
        or report.fresh_count
        != _count(sum(1 for row in report.rows if row.staleness_status == "fresh"))
    ):
        raise ValueError("status counts must match rows")
    if report.rank_status != _report_status(report.rows):
        raise ValueError("rank_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rank_status")


def _validate_report_scores(report: TeamSpecialistPlaybookStalenessRankerV2Report) -> None:
    if report.average_staleness_score != _average_staleness_score(report.rows):
        raise ValueError("average_staleness_score must match rows")
    if report.top_staleness_score != _top_staleness_score(report.rows):
        raise ValueError("top_staleness_score must match rows")


def _row_digest(row: TeamSpecialistPlaybookStalenessRankerV2Row) -> str:
    return _digest_public(asdict(row))


def _report_digest(report: TeamSpecialistPlaybookStalenessRankerV2Report) -> str:
    return _digest_public(asdict(report))


def _digest_public(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(value)
        for key, value in values.items()
        if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {
            key: _payload_value(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    return value


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _json_ready(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("payload numeric values must be Decimal-derived strings")
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if is_dataclass(payload) and not isinstance(payload, type):
        for field in fields(payload):
            _reject_unsafe_text(field.name)
            _reject_unsafe_public_payload(label, getattr(payload, field.name))
        return
    if type(payload) is dict:
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_text(key)
            _reject_unsafe_public_payload(label, value)
        return
    if type(payload) in (list, tuple):
        for value in payload:
            _reject_unsafe_public_payload(label, value)
        return
    if type(payload) is Decimal:
        if not payload.is_finite():
            raise ValueError(f"unsafe public payload in {label}")
        return
    if type(payload) is datetime:
        _as_utc("payload datetime", payload)
        return
    if payload is None or type(payload) is bool:
        return
    if type(payload) is float or type(payload) is int:
        raise ValueError(f"unsafe public payload in {label}")
    if type(payload) is str:
        _reject_unsafe_text(payload)
        return
    raise ValueError(f"unsafe public payload in {label}")


def _reject_unsafe_text(value: str) -> None:
    normalized = value.lower()
    if value.strip() != value or "://" in normalized or "?" in normalized:
        raise ValueError("unsafe public payload")
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError("unsafe public payload")


def _normalize_public_refs(field_name: str, value: object) -> tuple[str, ...]:
    normalized = _normalize_optional_public_refs(field_name, value)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _normalize_optional_public_refs(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(value)
    for item in normalized:
        _require_public_string(field_name, item)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(value)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in normalized:
        _require_public_string(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason for reason in allowed if reason in normalized) != normalized:
        raise ValueError(f"{field_name} must be deterministic")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(value)


def _require_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in STATUS_VALUES:
        raise ValueError(f"{field_name} must be stale, watch, or fresh")


def _require_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_ratio_total(*values: Decimal) -> None:
    total = sum(values, ZERO).quantize(RATIO_QUANTUM)
    if total != ONE.quantize(RATIO_QUANTUM):
        raise ValueError("staleness weights must sum to 1.000000")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value.quantize(RATIO_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value.quantize(RATIO_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _count_ratio(value: Decimal, limit: Decimal) -> Decimal:
    if limit <= ZERO:
        raise ValueError("ratio limit must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(value / limit)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = value.quantize(RATIO_QUANTUM)
    if normalized < ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    if normalized > ONE:
        return ONE.quantize(RATIO_QUANTUM)
    return normalized


def _age_days(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("last_used_age_days must be >= 0.000000")
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    with localcontext(DECIMAL_CONTEXT):
        return ((seconds + microseconds) / SECONDS_PER_DAY).quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_PLAYBOOK_STALENESS_RANKER_V2_CONFIG_VERSION",
    "TeamSpecialistPlaybookStalenessRankerV2Config",
    "TeamSpecialistPlaybookStalenessRankerV2Context",
    "TeamSpecialistPlaybookStalenessRankerV2Playbook",
    "TeamSpecialistPlaybookStalenessRankerV2Report",
    "TeamSpecialistPlaybookStalenessRankerV2Row",
    "build_team_specialist_playbook_staleness_ranker_v2_report",
    "team_specialist_playbook_staleness_ranker_v2_payload",
)
