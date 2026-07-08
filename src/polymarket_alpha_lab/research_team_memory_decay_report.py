"""Deterministic public report for research team memory decay."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_RESEARCH_TEAM_MEMORY_DECAY_REPORT_CONFIG_VERSION = (
    "research-team-memory-decay-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
PUBLIC_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
PUBLIC_STATUS_SORT_SEQUENCE = (STATUS_BLOCK, STATUS_WATCH, STATUS_PASS)

NO_OBSERVATIONS_REASON = "research_team_memory_decay_no_observations"
MEMORY_CURRENT_REASON = "research_team_memory_decay_current"
STALE_MEMORY_REASON = "research_team_memory_decay_stale"
CONFLICT_WATCH_REASON = "research_team_memory_conflict_accumulation_watch"
CONFLICT_BLOCK_REASON = "research_team_memory_conflict_accumulation_block"
POSTMORTEM_COVERAGE_GAP_REASON = "research_team_postmortem_coverage_gap"
REVIEW_GAP_WATCH_REASON = "research_team_review_gap_watch"
REVIEW_GAP_BLOCK_REASON = "research_team_review_gap_block"
SCORE_WATCH_REASON = "research_team_memory_score_watch"
SCORE_BLOCK_REASON = "research_team_memory_score_block"

ROW_REASON_CODE_SEQUENCE = (
    STALE_MEMORY_REASON,
    CONFLICT_BLOCK_REASON,
    CONFLICT_WATCH_REASON,
    POSTMORTEM_COVERAGE_GAP_REASON,
    REVIEW_GAP_BLOCK_REASON,
    REVIEW_GAP_WATCH_REASON,
    SCORE_BLOCK_REASON,
    SCORE_WATCH_REASON,
    MEMORY_CURRENT_REASON,
)

REPORT_MEMORY_CURRENT_REASON = "research_team_memory_decay_report_current"
REPORT_STALE_MEMORY_REASON = "research_team_memory_decay_report_stale_present"
REPORT_CONFLICT_REASON = "research_team_memory_decay_report_conflict_present"
REPORT_POSTMORTEM_COVERAGE_REASON = (
    "research_team_memory_decay_report_postmortem_coverage_gap_present"
)
REPORT_REVIEW_GAP_REASON = "research_team_memory_decay_report_review_gap_present"
REPORT_SCORE_GAP_REASON = "research_team_memory_decay_report_score_gap_present"

REPORT_REASON_CODE_SEQUENCE = (
    NO_OBSERVATIONS_REASON,
    REPORT_STALE_MEMORY_REASON,
    REPORT_CONFLICT_REASON,
    REPORT_POSTMORTEM_COVERAGE_REASON,
    REPORT_REVIEW_GAP_REASON,
    REPORT_SCORE_GAP_REASON,
    REPORT_MEMORY_CURRENT_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join_parts("raw", "_", "candi", "date"),
        _join_parts("candi", "date", "_", "id"),
        _join_parts("mar", "ket", "_", "id"),
        _join_parts("mar", "ket", "_", "slug"),
        _join_parts("mar", "ket"),
        _join_parts("slug"),
        _join_parts("ques", "tion"),
        _join_parts("sour", "ce", "_", "ref"),
        _join_parts("sour", "ce", "_", "url"),
        _join_parts("sour", "ce", "_", "text"),
        _join_parts("sour", "ceref"),
        _join_parts("ur", "l"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("or", "der"),
        _join_parts("tra", "de"),
        _join_parts("tradi", "ng"),
        _join_parts("posi", "tion"),
        _join_parts("bu", "y"),
        _join_parts("se", "ll"),
        _join_parts("reco", "mmend"),
        _join_parts("ad", "vice"),
        _join_parts("secret"),
        _join_parts("private"),
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_MEMORY_DECAY_REPORT_CONFIG_VERSION",
    "ResearchTeamMemoryDecayConfig",
    "ResearchTeamMemoryDecayDigest",
    "ResearchTeamMemoryDecayObservation",
    "ResearchTeamMemoryDecayReasonCodeCount",
    "ResearchTeamMemoryDecayReport",
    "ResearchTeamMemoryDecayRow",
    "build_research_team_memory_decay_report",
    "research_team_memory_decay_digest",
    "research_team_memory_decay_digest_payload",
    "research_team_memory_decay_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamMemoryDecayConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_MEMORY_DECAY_REPORT_CONFIG_VERSION
    stale_memory_after_seconds: Decimal = Decimal("2419200.000000")
    conflict_watch_threshold: Decimal = Decimal("2.000000")
    conflict_block_threshold: Decimal = Decimal("5.000000")
    review_gap_watch_threshold: Decimal = Decimal("1.000000")
    review_gap_block_threshold: Decimal = Decimal("3.000000")
    min_postmortem_coverage_ratio: Decimal = Decimal("0.600000")
    min_pass_memory_score: Decimal = Decimal("0.700000")
    min_watch_memory_score: Decimal = Decimal("0.450000")
    stale_memory_penalty: Decimal = Decimal("0.150000")
    conflict_penalty_per_item: Decimal = Decimal("0.040000")
    review_gap_penalty_per_item: Decimal = Decimal("0.050000")
    postmortem_coverage_gap_penalty: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryDecayConfig:
            raise TypeError("ResearchTeamMemoryDecayConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryDecayConfig:
            raise ValueError("config must be exactly ResearchTeamMemoryDecayConfig")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "stale_memory_after_seconds",
            "conflict_watch_threshold",
            "conflict_block_threshold",
            "review_gap_watch_threshold",
            "review_gap_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_postmortem_coverage_ratio",
            "min_pass_memory_score",
            "min_watch_memory_score",
            "stale_memory_penalty",
            "conflict_penalty_per_item",
            "review_gap_penalty_per_item",
            "postmortem_coverage_gap_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.conflict_watch_threshold > self.conflict_block_threshold:
            raise ValueError("conflict_watch_threshold must not exceed block threshold")
        if self.review_gap_watch_threshold > self.review_gap_block_threshold:
            raise ValueError("review_gap_watch_threshold must not exceed block threshold")
        if self.min_watch_memory_score > self.min_pass_memory_score:
            raise ValueError("min_watch_memory_score must not exceed pass threshold")
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryDecayObservation:
    team_id: str
    category_id: str
    specialist_role: str
    internal_memory_key: str
    latest_memory_refresh_at: datetime
    latest_review_completed_at: datetime | None
    memory_confidence_score: Decimal
    unresolved_conflict_count: Decimal
    review_gap_count: Decimal
    postmortem_coverage_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryDecayObservation:
            raise TypeError(
                "ResearchTeamMemoryDecayObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryDecayObservation:
            raise ValueError(
                "observation must be exactly ResearchTeamMemoryDecayObservation",
            )
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("category_id", self.category_id)
        _require_public_string("specialist_role", self.specialist_role)
        _require_internal_memory_key("internal_memory_key", self.internal_memory_key)
        object.__setattr__(
            self,
            "latest_memory_refresh_at",
            _as_utc("latest_memory_refresh_at", self.latest_memory_refresh_at),
        )
        object.__setattr__(
            self,
            "latest_review_completed_at",
            _as_optional_utc(
                "latest_review_completed_at",
                self.latest_review_completed_at,
            ),
        )
        object.__setattr__(
            self,
            "memory_confidence_score",
            _require_ratio_decimal(
                "memory_confidence_score",
                self.memory_confidence_score,
            ),
        )
        for field_name in ("unresolved_conflict_count", "review_gap_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "postmortem_coverage_ratio",
            _require_ratio_decimal(
                "postmortem_coverage_ratio",
                self.postmortem_coverage_ratio,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchTeamMemoryDecayRow:
    team_id: str
    category_id: str
    specialist_role: str
    public_memory_digest: str
    public_status: str
    memory_age_seconds: Decimal
    review_age_seconds: Decimal | None
    memory_confidence_score: Decimal
    unresolved_conflict_count: Decimal
    review_gap_count: Decimal
    postmortem_coverage_ratio: Decimal
    stale_memory_penalty: Decimal
    conflict_penalty: Decimal
    review_gap_penalty: Decimal
    postmortem_coverage_gap_penalty: Decimal
    adjusted_memory_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryDecayRow:
            raise TypeError("ResearchTeamMemoryDecayRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryDecayRow:
            raise ValueError("row must be exactly ResearchTeamMemoryDecayRow")
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("category_id", self.category_id)
        _require_public_string("specialist_role", self.specialist_role)
        _require_public_digest("public_memory_digest", self.public_memory_digest)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        for field_name in (
            "memory_age_seconds",
            "unresolved_conflict_count",
            "review_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_age_seconds",
            _require_optional_nonnegative_whole_decimal(
                "review_age_seconds",
                self.review_age_seconds,
            ),
        )
        for field_name in (
            "memory_confidence_score",
            "postmortem_coverage_ratio",
            "stale_memory_penalty",
            "conflict_penalty",
            "review_gap_penalty",
            "postmortem_coverage_gap_penalty",
            "adjusted_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchTeamMemoryDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryDecayReasonCodeCount:
            raise TypeError(
                "ResearchTeamMemoryDecayReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryDecayReasonCodeCount:
            raise ValueError(
                "reason count must be exactly ResearchTeamMemoryDecayReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, ROW_REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchTeamMemoryDecayReport:
    generated_at: datetime
    config_version: str
    public_status: str
    observation_count: Decimal
    team_count: Decimal
    specialist_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_memory_count: Decimal
    conflict_accumulation_count: Decimal
    postmortem_coverage_gap_count: Decimal
    review_gap_count: Decimal
    score_gap_count: Decimal
    average_adjusted_memory_score: Decimal
    average_postmortem_coverage_ratio: Decimal
    max_memory_age_seconds: Decimal
    rows: tuple[ResearchTeamMemoryDecayRow, ...]
    reason_code_counts: tuple[ResearchTeamMemoryDecayReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    local_supabase_summary_ready: bool = True
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryDecayReport:
            raise TypeError("ResearchTeamMemoryDecayReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryDecayReport:
            raise ValueError("report must be exactly ResearchTeamMemoryDecayReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        for field_name in (
            "observation_count",
            "team_count",
            "specialist_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_memory_count",
            "conflict_accumulation_count",
            "postmortem_coverage_gap_count",
            "review_gap_count",
            "score_gap_count",
            "max_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_adjusted_memory_score",
            "average_postmortem_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _require_row_tuple("rows", self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_count_tuple("reason_code_counts", self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        if self.local_supabase_summary_ready is not True:
            raise ValueError("local_supabase_summary_ready must be True")
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_memory_decay_report_payload(self)


@dataclass(frozen=True)
class ResearchTeamMemoryDecayDigest:
    generated_at: datetime
    config_version: str
    public_status: str
    observation_count: Decimal
    team_count: Decimal
    specialist_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_memory_count: Decimal
    conflict_accumulation_count: Decimal
    postmortem_coverage_gap_count: Decimal
    review_gap_count: Decimal
    score_gap_count: Decimal
    average_adjusted_memory_score: Decimal
    average_postmortem_coverage_ratio: Decimal
    max_memory_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    report_validation_digest: str
    local_supabase_summary_ready: bool = True
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryDecayDigest:
            raise TypeError("ResearchTeamMemoryDecayDigest does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryDecayDigest:
            raise ValueError("digest must be exactly ResearchTeamMemoryDecayDigest")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        for field_name in (
            "observation_count",
            "team_count",
            "specialist_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_memory_count",
            "conflict_accumulation_count",
            "postmortem_coverage_gap_count",
            "review_gap_count",
            "score_gap_count",
            "max_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_adjusted_memory_score",
            "average_postmortem_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        _require_sha256_digest("report_validation_digest", self.report_validation_digest)
        if self.local_supabase_summary_ready is not True:
            raise ValueError("local_supabase_summary_ready must be True")
        _reject_unsafe_public_payload("digest", self)
        _require_hard_flags("digest", self)
        expected_digest = _digest_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match digest contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_memory_decay_digest_payload(self)


def build_research_team_memory_decay_report(
    rows: tuple[ResearchTeamMemoryDecayObservation, ...],
    *,
    config: ResearchTeamMemoryDecayConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamMemoryDecayReport:
    cfg = config or ResearchTeamMemoryDecayConfig()
    if type(cfg) is not ResearchTeamMemoryDecayConfig:
        raise TypeError("config must be exactly ResearchTeamMemoryDecayConfig")
    observed_at = _as_utc("generated_at", generated_at)
    input_rows = _require_observation_tuple("rows", rows)
    report_rows = tuple(
        sorted(
            (
                _build_row(row, config=cfg, generated_at=observed_at)
                for row in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(report_rows)
    public_status = _report_status(report_rows)
    reason_codes = _report_reason_codes(report_rows, len(input_rows))

    return ResearchTeamMemoryDecayReport(
        generated_at=observed_at,
        config_version=cfg.config_version,
        public_status=public_status,
        observation_count=_count_decimal(len(input_rows)),
        team_count=_count_decimal(len({row.team_id for row in report_rows})),
        specialist_count=_count_decimal(
            len({(row.team_id, row.category_id, row.specialist_role) for row in report_rows}),
        ),
        pass_count=_status_count(report_rows, STATUS_PASS),
        watch_count=_status_count(report_rows, STATUS_WATCH),
        block_count=_status_count(report_rows, STATUS_BLOCK),
        stale_memory_count=_reason_count(report_rows, STALE_MEMORY_REASON),
        conflict_accumulation_count=_reason_count_any(
            report_rows,
            (CONFLICT_BLOCK_REASON, CONFLICT_WATCH_REASON),
        ),
        postmortem_coverage_gap_count=_reason_count(
            report_rows,
            POSTMORTEM_COVERAGE_GAP_REASON,
        ),
        review_gap_count=_reason_count_any(
            report_rows,
            (REVIEW_GAP_BLOCK_REASON, REVIEW_GAP_WATCH_REASON),
        ),
        score_gap_count=_reason_count_any(
            report_rows,
            (SCORE_BLOCK_REASON, SCORE_WATCH_REASON),
        ),
        average_adjusted_memory_score=_average_decimal(
            tuple(row.adjusted_memory_score for row in report_rows),
        ),
        average_postmortem_coverage_ratio=_average_decimal(
            tuple(row.postmortem_coverage_ratio for row in report_rows),
        ),
        max_memory_age_seconds=max(
            (row.memory_age_seconds for row in report_rows),
            default=ZERO,
        ),
        rows=report_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_team_memory_decay_report_payload(
    report: ResearchTeamMemoryDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamMemoryDecayReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("report payload", report)
        _require_hard_flags("report payload", _DictFlags(report))
        payload = _json_ready(report)
    else:
        raise TypeError("report must be exactly ResearchTeamMemoryDecayReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload)
    _require_hard_flags("report payload", _DictFlags(payload))
    _validate_public_digest(payload, "derived_validation_digest")
    return payload


def research_team_memory_decay_digest(
    report: ResearchTeamMemoryDecayReport,
) -> ResearchTeamMemoryDecayDigest:
    if type(report) is not ResearchTeamMemoryDecayReport:
        raise TypeError("report must be exactly ResearchTeamMemoryDecayReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    return ResearchTeamMemoryDecayDigest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        public_status=report.public_status,
        observation_count=report.observation_count,
        team_count=report.team_count,
        specialist_count=report.specialist_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        stale_memory_count=report.stale_memory_count,
        conflict_accumulation_count=report.conflict_accumulation_count,
        postmortem_coverage_gap_count=report.postmortem_coverage_gap_count,
        review_gap_count=report.review_gap_count,
        score_gap_count=report.score_gap_count,
        average_adjusted_memory_score=report.average_adjusted_memory_score,
        average_postmortem_coverage_ratio=report.average_postmortem_coverage_ratio,
        max_memory_age_seconds=report.max_memory_age_seconds,
        reason_codes=report.reason_codes,
        report_validation_digest=report.derived_validation_digest,
    )


def research_team_memory_decay_digest_payload(
    digest: ResearchTeamMemoryDecayDigest | dict[str, Any],
) -> dict[str, Any]:
    if type(digest) is ResearchTeamMemoryDecayDigest:
        _require_hard_flags("digest", digest)
        _reject_unsafe_public_payload("digest", digest)
        payload = _json_ready(digest)
    elif type(digest) is dict:
        _reject_unsafe_public_payload("digest payload", digest)
        _require_hard_flags("digest payload", _DictFlags(digest))
        payload = _json_ready(digest)
    else:
        raise TypeError("digest must be exactly ResearchTeamMemoryDecayDigest")
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_unsafe_public_payload("digest payload", payload)
    _require_hard_flags("digest payload", _DictFlags(payload))
    _validate_public_digest(payload, "derived_validation_digest")
    _require_sha256_digest(
        "report_validation_digest",
        payload.get("report_validation_digest"),
    )
    return payload


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


def _build_row(
    row: ResearchTeamMemoryDecayObservation,
    *,
    config: ResearchTeamMemoryDecayConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryDecayRow:
    memory_age_seconds = _age_seconds(generated_at, row.latest_memory_refresh_at)
    review_age_seconds = (
        None
        if row.latest_review_completed_at is None
        else _age_seconds(generated_at, row.latest_review_completed_at)
    )
    stale_penalty = (
        config.stale_memory_penalty
        if memory_age_seconds > config.stale_memory_after_seconds
        else ZERO
    )
    conflict_penalty = _clamped_ratio(
        row.unresolved_conflict_count * config.conflict_penalty_per_item,
    )
    review_gap_penalty = _clamped_ratio(
        row.review_gap_count * config.review_gap_penalty_per_item,
    )
    coverage_gap_penalty = (
        config.postmortem_coverage_gap_penalty
        if row.postmortem_coverage_ratio < config.min_postmortem_coverage_ratio
        else ZERO
    )
    adjusted_score = _clamped_ratio(
        row.memory_confidence_score
        - stale_penalty
        - conflict_penalty
        - review_gap_penalty
        - coverage_gap_penalty,
    )
    reason_codes = _row_reason_codes(
        memory_age_seconds=memory_age_seconds,
        unresolved_conflict_count=row.unresolved_conflict_count,
        review_gap_count=row.review_gap_count,
        postmortem_coverage_ratio=row.postmortem_coverage_ratio,
        adjusted_memory_score=adjusted_score,
        config=config,
    )
    return ResearchTeamMemoryDecayRow(
        team_id=row.team_id,
        category_id=row.category_id,
        specialist_role=row.specialist_role,
        public_memory_digest=_public_memory_digest(row),
        public_status=_row_status(reason_codes),
        memory_age_seconds=memory_age_seconds,
        review_age_seconds=review_age_seconds,
        memory_confidence_score=row.memory_confidence_score,
        unresolved_conflict_count=row.unresolved_conflict_count,
        review_gap_count=row.review_gap_count,
        postmortem_coverage_ratio=row.postmortem_coverage_ratio,
        stale_memory_penalty=stale_penalty,
        conflict_penalty=conflict_penalty,
        review_gap_penalty=review_gap_penalty,
        postmortem_coverage_gap_penalty=coverage_gap_penalty,
        adjusted_memory_score=adjusted_score,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    memory_age_seconds: Decimal,
    unresolved_conflict_count: Decimal,
    review_gap_count: Decimal,
    postmortem_coverage_ratio: Decimal,
    adjusted_memory_score: Decimal,
    config: ResearchTeamMemoryDecayConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if memory_age_seconds > config.stale_memory_after_seconds:
        reasons.append(STALE_MEMORY_REASON)
    if unresolved_conflict_count >= config.conflict_block_threshold:
        reasons.append(CONFLICT_BLOCK_REASON)
    elif unresolved_conflict_count >= config.conflict_watch_threshold:
        reasons.append(CONFLICT_WATCH_REASON)
    if postmortem_coverage_ratio < config.min_postmortem_coverage_ratio:
        reasons.append(POSTMORTEM_COVERAGE_GAP_REASON)
    if review_gap_count >= config.review_gap_block_threshold:
        reasons.append(REVIEW_GAP_BLOCK_REASON)
    elif review_gap_count >= config.review_gap_watch_threshold:
        reasons.append(REVIEW_GAP_WATCH_REASON)
    if adjusted_memory_score < config.min_watch_memory_score:
        reasons.append(SCORE_BLOCK_REASON)
    elif adjusted_memory_score < config.min_pass_memory_score:
        reasons.append(SCORE_WATCH_REASON)
    if not reasons:
        reasons.append(MEMORY_CURRENT_REASON)
    return _normalize_row_reason_codes("reason_codes", tuple(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        CONFLICT_BLOCK_REASON in reason_codes
        or REVIEW_GAP_BLOCK_REASON in reason_codes
        or SCORE_BLOCK_REASON in reason_codes
    ):
        return STATUS_BLOCK
    if reason_codes == (MEMORY_CURRENT_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _row_sort_key(
    row: ResearchTeamMemoryDecayRow,
) -> tuple[int, Decimal, str, str, str, str]:
    return (
        PUBLIC_STATUS_SORT_SEQUENCE.index(row.public_status),
        row.adjusted_memory_score,
        row.team_id,
        row.category_id,
        row.specialist_role,
        row.public_memory_digest,
    )


def _report_status(rows: tuple[ResearchTeamMemoryDecayRow, ...]) -> str:
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchTeamMemoryDecayRow, ...],
    input_row_count: int,
) -> tuple[str, ...]:
    if input_row_count == 0:
        return (NO_OBSERVATIONS_REASON,)
    reasons: list[str] = []
    if any(STALE_MEMORY_REASON in row.reason_codes for row in rows):
        reasons.append(REPORT_STALE_MEMORY_REASON)
    if any(
        CONFLICT_BLOCK_REASON in row.reason_codes
        or CONFLICT_WATCH_REASON in row.reason_codes
        for row in rows
    ):
        reasons.append(REPORT_CONFLICT_REASON)
    if any(POSTMORTEM_COVERAGE_GAP_REASON in row.reason_codes for row in rows):
        reasons.append(REPORT_POSTMORTEM_COVERAGE_REASON)
    if any(
        REVIEW_GAP_BLOCK_REASON in row.reason_codes
        or REVIEW_GAP_WATCH_REASON in row.reason_codes
        for row in rows
    ):
        reasons.append(REPORT_REVIEW_GAP_REASON)
    if any(
        SCORE_BLOCK_REASON in row.reason_codes
        or SCORE_WATCH_REASON in row.reason_codes
        for row in rows
    ):
        reasons.append(REPORT_SCORE_GAP_REASON)
    if rows and all(row.public_status == STATUS_PASS for row in rows):
        reasons.append(REPORT_MEMORY_CURRENT_REASON)
    return _normalize_report_reason_codes("reason_codes", tuple(reasons))


def _reason_code_counts(
    rows: tuple[ResearchTeamMemoryDecayRow, ...],
) -> tuple[ResearchTeamMemoryDecayReasonCodeCount, ...]:
    if not rows:
        return ()
    row_count = _count_decimal(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchTeamMemoryDecayReasonCodeCount(
            reason_code=reason_code,
            count=count,
            row_ratio=_ratio(count, row_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: ROW_REASON_CODE_SEQUENCE.index(item[0]),
        )
    )


def _status_count(rows: tuple[ResearchTeamMemoryDecayRow, ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.public_status == status))


def _reason_count(
    rows: tuple[ResearchTeamMemoryDecayRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_count_any(
    rows: tuple[ResearchTeamMemoryDecayRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)),
    )


def _validate_row(row: ResearchTeamMemoryDecayRow) -> None:
    if row.reason_codes == ():
        raise ValueError("reason_codes must not be empty")
    if MEMORY_CURRENT_REASON in row.reason_codes and row.reason_codes != (
        MEMORY_CURRENT_REASON,
    ):
        raise ValueError("current memory reason must stand alone")
    if row.public_status != _row_status(row.reason_codes):
        raise ValueError("public_status must match reason_codes")
    expected_score = _clamped_ratio(
        row.memory_confidence_score
        - row.stale_memory_penalty
        - row.conflict_penalty
        - row.review_gap_penalty
        - row.postmortem_coverage_gap_penalty,
    )
    if row.adjusted_memory_score != expected_score:
        raise ValueError("adjusted_memory_score must match row penalties")


def _validate_report(report: ResearchTeamMemoryDecayReport) -> None:
    if report.observation_count != _count_decimal(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.team_count != _count_decimal(len({row.team_id for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.specialist_count != _count_decimal(
        len({(row.team_id, row.category_id, row.specialist_role) for row in report.rows}),
    ):
        raise ValueError("specialist_count must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    expected_counts = {
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
        "stale_memory_count": _reason_count(report.rows, STALE_MEMORY_REASON),
        "conflict_accumulation_count": _reason_count_any(
            report.rows,
            (CONFLICT_BLOCK_REASON, CONFLICT_WATCH_REASON),
        ),
        "postmortem_coverage_gap_count": _reason_count(
            report.rows,
            POSTMORTEM_COVERAGE_GAP_REASON,
        ),
        "review_gap_count": _reason_count_any(
            report.rows,
            (REVIEW_GAP_BLOCK_REASON, REVIEW_GAP_WATCH_REASON),
        ),
        "score_gap_count": _reason_count_any(
            report.rows,
            (SCORE_BLOCK_REASON, SCORE_WATCH_REASON),
        ),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.average_adjusted_memory_score != _average_decimal(
        tuple(row.adjusted_memory_score for row in report.rows),
    ):
        raise ValueError("average_adjusted_memory_score must match rows")
    if report.average_postmortem_coverage_ratio != _average_decimal(
        tuple(row.postmortem_coverage_ratio for row in report.rows),
    ):
        raise ValueError("average_postmortem_coverage_ratio must match rows")
    if report.max_memory_age_seconds != max(
        (row.memory_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_memory_age_seconds must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.observation_count)):
        raise ValueError("reason_codes must match rows")
    if report.public_status != _report_status(report.rows):
        raise ValueError("public_status must match rows")


def _require_observation_tuple(
    field_name: str,
    value: object,
) -> tuple[ResearchTeamMemoryDecayObservation, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    rows = tuple(value)
    seen_digests: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamMemoryDecayObservation:
            raise ValueError(
                f"{field_name} must contain ResearchTeamMemoryDecayObservation",
            )
        _require_hard_flags("observation", row)
        row_digest = _public_memory_digest(row)
        if row_digest in seen_digests:
            raise ValueError("duplicate public_memory_digest values are not allowed")
        seen_digests.add(row_digest)
    return rows


def _require_row_tuple(
    field_name: str,
    value: object,
) -> tuple[ResearchTeamMemoryDecayRow, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    rows = tuple(value)
    seen_digests: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamMemoryDecayRow:
            raise ValueError(f"{field_name} must contain ResearchTeamMemoryDecayRow")
        _require_hard_flags("row", row)
        if row.public_memory_digest in seen_digests:
            raise ValueError("duplicate public_memory_digest values are not allowed")
        seen_digests.add(row.public_memory_digest)
    return rows


def _require_reason_count_tuple(
    field_name: str,
    value: object,
) -> tuple[ResearchTeamMemoryDecayReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    items = tuple(value)
    seen_reasons: set[str] = set()
    for item in items:
        if type(item) is not ResearchTeamMemoryDecayReasonCodeCount:
            raise ValueError(
                f"{field_name} must contain ResearchTeamMemoryDecayReasonCodeCount",
            )
        if item.reason_code in seen_reasons:
            raise ValueError("reason_code_counts must be unique")
        seen_reasons.add(item.reason_code)
    if items != tuple(
        sorted(items, key=lambda item: ROW_REASON_CODE_SEQUENCE.index(item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be deterministic")
    return items


def _normalize_row_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in value:
        _require_member(field_name, reason_code, ROW_REASON_CODE_SEQUENCE)
    unique_values = frozenset(value)
    if len(unique_values) != len(value):
        raise ValueError(f"{field_name} must be unique")
    return tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in unique_values
    )


def _normalize_report_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in value:
        _require_member(field_name, reason_code, REPORT_REASON_CODE_SEQUENCE)
    unique_values = frozenset(value)
    if len(unique_values) != len(value):
        raise ValueError(f"{field_name} must be unique")
    return tuple(
        reason_code
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code in unique_values
    )


def _public_memory_digest(row: ResearchTeamMemoryDecayObservation) -> str:
    public_seed = "|".join(
        (
            row.team_id,
            row.category_id,
            row.specialist_role,
            row.internal_memory_key,
        ),
    )
    return f"sha256:{sha256(public_seed.encode('utf-8')).hexdigest()[:16]}"


def _report_digest(report: ResearchTeamMemoryDecayReport) -> str:
    payload = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }
    return _digest_for_json_object(_json_ready(payload))


def _digest_digest(digest: ResearchTeamMemoryDecayDigest) -> str:
    payload = {
        field.name: getattr(digest, field.name)
        for field in fields(digest)
        if field.name != "derived_validation_digest"
    }
    return _digest_for_json_object(_json_ready(payload))


def _validate_public_digest(payload: dict[str, Any], digest_field_name: str) -> None:
    digest_value = payload.get(digest_field_name)
    _require_sha256_digest(digest_field_name, digest_value)
    expected = _digest_for_json_object(payload)
    if digest_value != expected:
        raise ValueError(f"{digest_field_name} must match public contents")


def _digest_for_json_object(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    canonical_payload = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    value = Decimal(delta.days * 86400 + delta.seconds)
    if value < ZERO:
        raise ValueError("observed_at must be before or equal to generated_at")
    return _quantize(value)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(_sum_decimal(values), _count_decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _clamped_ratio(value: Decimal) -> Decimal:
    decimal_value = _require_decimal("ratio", value)
    if decimal_value < ZERO:
        return ZERO
    if decimal_value > ONE:
        return ONE
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return decimal_value


def _require_optional_nonnegative_whole_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_whole_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the unit interval")
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be a whole second")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be canonical")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _require_internal_memory_key(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_public_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value.startswith("sha256:") or len(value) != 23:
        raise ValueError(f"{field_name} must be a public sha256 digest")
    if any(character not in "0123456789abcdef" for character in value[7:]):
        raise ValueError(f"{field_name} must be a public sha256 digest")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> str:
    _require_public_string(field_name, value)
    if value not in members:
        raise ValueError(f"{field_name} must be a known value")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} must keep {flag_name}=True")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{path or label} contains unsafe public text")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise TypeError(f"{path or label} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise TypeError("public JSON values must not be floats")
    if type(value) is int:
        raise TypeError("public JSON values must use Decimal-derived strings")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("public JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            nested_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise TypeError("value is not public JSON serializable")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower().replace("-", "_").replace(" ", "_")
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise TypeError("public JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("public JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str or type(value) is bool:
        return value
    if isinstance(value, float):
        raise TypeError("public JSON values must not be floats")
    if type(value) is int:
        raise TypeError("public JSON values must use Decimal-derived strings")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("public JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise TypeError("value is not public JSON serializable")
