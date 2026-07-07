"""Pure report-only specialist evidence and review coverage scoring."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_TEAM_SPECIALIST_EVIDENCE_REVIEW_COVERAGE_SCORE_CONFIG_VERSION = (
    "team-specialist-evidence-review-coverage-score-v1"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUSES = frozenset(("pass", "watch", "block"))
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REASON_CODE_SEQUENCE = (
    "evidence_type_coverage_block",
    "review_step_coverage_block",
    "evidence_independence_block",
    "cross_review_block",
    "unresolved_gap_block",
    "evidence_review_coverage_score_block",
    "evidence_type_coverage_watch",
    "review_step_coverage_watch",
    "evidence_independence_watch",
    "cross_review_watch",
    "unresolved_gap_watch",
    "evidence_review_coverage_score_watch",
    "team_specialist_evidence_review_coverage_pass",
)
UNSAFE_PUBLIC_TERMS = (
    "market",
    "candidate",
    "slug",
    "question",
    "source",
    "source_ref",
    "source ref",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "secret",
    "auth",
    "wallet",
    "order",
    "trade",
    "buy",
    "sell",
    "recommendation",
    "position",
)
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_:-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_EVIDENCE_REVIEW_COVERAGE_SCORE_CONFIG_VERSION",
    "TeamSpecialistEvidenceReviewCoverageScoreConfig",
    "TeamSpecialistEvidenceReviewCoverageScoreInput",
    "TeamSpecialistEvidenceReviewCoverageScoreReasonCodeCount",
    "TeamSpecialistEvidenceReviewCoverageScoreRow",
    "TeamSpecialistEvidenceReviewCoverageScoreReport",
    "build_team_specialist_evidence_review_coverage_score_report",
    "team_specialist_evidence_review_coverage_score_payload",
)


@dataclass(frozen=True)
class TeamSpecialistEvidenceReviewCoverageScoreConfig:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_EVIDENCE_REVIEW_COVERAGE_SCORE_CONFIG_VERSION
    )
    evidence_type_weight: Decimal = Decimal("0.300000")
    review_step_weight: Decimal = Decimal("0.300000")
    evidence_independence_weight: Decimal = Decimal("0.200000")
    cross_review_weight: Decimal = Decimal("0.200000")
    unresolved_gap_penalty_weight: Decimal = Decimal("0.200000")
    min_evidence_type_pass_ratio: Decimal = Decimal("0.800000")
    min_evidence_type_watch_ratio: Decimal = Decimal("0.500000")
    min_review_step_pass_ratio: Decimal = Decimal("0.800000")
    min_review_step_watch_ratio: Decimal = Decimal("0.500000")
    min_evidence_independence_pass_ratio: Decimal = Decimal("0.700000")
    min_evidence_independence_watch_ratio: Decimal = Decimal("0.400000")
    min_cross_review_pass_ratio: Decimal = Decimal("0.600000")
    min_cross_review_watch_ratio: Decimal = Decimal("0.300000")
    max_unresolved_gap_pass_ratio: Decimal = Decimal("0.200000")
    max_unresolved_gap_watch_ratio: Decimal = Decimal("0.400000")
    pass_score_floor: Decimal = Decimal("0.800000")
    watch_score_floor: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "evidence_type_weight",
            "review_step_weight",
            "evidence_independence_weight",
            "cross_review_weight",
            "unresolved_gap_penalty_weight",
            "min_evidence_type_pass_ratio",
            "min_evidence_type_watch_ratio",
            "min_review_step_pass_ratio",
            "min_review_step_watch_ratio",
            "min_evidence_independence_pass_ratio",
            "min_evidence_independence_watch_ratio",
            "min_cross_review_pass_ratio",
            "min_cross_review_watch_ratio",
            "max_unresolved_gap_pass_ratio",
            "max_unresolved_gap_watch_ratio",
            "pass_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamSpecialistEvidenceReviewCoverageScoreInput:
    team_id: str
    specialist_id: str
    category_id: str
    required_evidence_type_count: Decimal
    covered_evidence_type_count: Decimal
    required_review_step_count: Decimal
    completed_review_step_count: Decimal
    independent_evidence_ratio: Decimal
    cross_review_ratio: Decimal
    unresolved_gap_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "specialist_id", "category_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "required_evidence_type_count",
            "required_review_step_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "covered_evidence_type_count",
            "completed_review_step_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "independent_evidence_ratio",
            "cross_review_ratio",
            "unresolved_gap_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class TeamSpecialistEvidenceReviewCoverageScoreReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class TeamSpecialistEvidenceReviewCoverageScoreRow:
    rank: Decimal
    team_id: str
    specialist_id: str
    category_id: str
    required_evidence_type_count: Decimal
    covered_evidence_type_count: Decimal
    evidence_type_coverage_ratio: Decimal
    required_review_step_count: Decimal
    completed_review_step_count: Decimal
    review_step_completion_ratio: Decimal
    independent_evidence_ratio: Decimal
    cross_review_ratio: Decimal
    unresolved_gap_ratio: Decimal
    resolved_gap_ratio: Decimal
    review_coverage_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _require_positive_count_decimal("rank", self.rank))
        for field_name in ("team_id", "specialist_id", "category_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "required_evidence_type_count",
            "required_review_step_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "covered_evidence_type_count",
            "completed_review_step_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_type_coverage_ratio",
            "review_step_completion_ratio",
            "independent_evidence_ratio",
            "cross_review_ratio",
            "unresolved_gap_ratio",
            "resolved_gap_ratio",
            "review_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class TeamSpecialistEvidenceReviewCoverageScoreReport:
    generated_at: datetime
    config_version: str
    report_status: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_review_coverage_score: Decimal
    minimum_review_coverage_score: Decimal
    reason_code_counts: tuple[
        TeamSpecialistEvidenceReviewCoverageScoreReasonCodeCount,
        ...,
    ]
    rows: tuple[TeamSpecialistEvidenceReviewCoverageScoreRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "report_status",
            _require_status("report_status", self.report_status),
        )
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_review_coverage_score",
            "minimum_review_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "derived_validation_digest",
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        if self.derived_validation_digest != _report_digest(self):
            raise ValueError("derived_validation_digest must match report fields")
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(self)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
        _require_payload_hard_flags("payload", payload)
        _validate_payload_digest(payload)
        return payload


def build_team_specialist_evidence_review_coverage_score_report(
    rows: Iterable[TeamSpecialistEvidenceReviewCoverageScoreInput],
    *,
    generated_at: datetime,
    config: TeamSpecialistEvidenceReviewCoverageScoreConfig | None = None,
) -> TeamSpecialistEvidenceReviewCoverageScoreReport:
    if config is None:
        config = TeamSpecialistEvidenceReviewCoverageScoreConfig()
    if type(config) is not TeamSpecialistEvidenceReviewCoverageScoreConfig:
        raise ValueError(
            "config must be a TeamSpecialistEvidenceReviewCoverageScoreConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(rows)
    scored_rows = tuple(
        _coverage_row(index, row, config)
        for index, row in enumerate(input_rows, start=1)
    )
    values = dict(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(scored_rows),
        item_count=_decimal_count(len(scored_rows)),
        pass_count=_status_count(scored_rows, "pass"),
        watch_count=_status_count(scored_rows, "watch"),
        block_count=_status_count(scored_rows, "block"),
        average_review_coverage_score=_average_score(scored_rows),
        minimum_review_coverage_score=_minimum_score(scored_rows),
        reason_code_counts=_reason_code_counts(scored_rows),
        rows=scored_rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return TeamSpecialistEvidenceReviewCoverageScoreReport(
        **values,
        derived_validation_digest=_digest_values(values),
    )


def team_specialist_evidence_review_coverage_score_payload(
    report: TeamSpecialistEvidenceReviewCoverageScoreReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistEvidenceReviewCoverageScoreReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = report.payload
    elif type(report) is dict:
        _reject_unsafe_public_payload(
            "payload",
            report,
            allow_json_containers=True,
        )
        _require_payload_hard_flags("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_payload_hard_flags("payload", payload)
        _validate_payload_digest(payload)
    else:
        raise ValueError(
            "report must be a TeamSpecialistEvidenceReviewCoverageScoreReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _require_payload_hard_flags("payload", payload)
    _validate_payload_digest(payload)
    return payload


def _coverage_row(
    rank: int,
    item: TeamSpecialistEvidenceReviewCoverageScoreInput,
    config: TeamSpecialistEvidenceReviewCoverageScoreConfig,
) -> TeamSpecialistEvidenceReviewCoverageScoreRow:
    evidence_type_coverage_ratio = _coverage_ratio(
        item.covered_evidence_type_count,
        item.required_evidence_type_count,
    )
    review_step_completion_ratio = _coverage_ratio(
        item.completed_review_step_count,
        item.required_review_step_count,
    )
    resolved_gap_ratio = _clamp_ratio(ONE - item.unresolved_gap_ratio)
    review_coverage_score = _review_coverage_score(
        evidence_type_coverage_ratio=evidence_type_coverage_ratio,
        review_step_completion_ratio=review_step_completion_ratio,
        independent_evidence_ratio=item.independent_evidence_ratio,
        cross_review_ratio=item.cross_review_ratio,
        unresolved_gap_ratio=item.unresolved_gap_ratio,
        config=config,
    )
    reason_codes = _row_reason_codes(
        evidence_type_coverage_ratio=evidence_type_coverage_ratio,
        review_step_completion_ratio=review_step_completion_ratio,
        independent_evidence_ratio=item.independent_evidence_ratio,
        cross_review_ratio=item.cross_review_ratio,
        unresolved_gap_ratio=item.unresolved_gap_ratio,
        review_coverage_score=review_coverage_score,
        config=config,
    )
    return TeamSpecialistEvidenceReviewCoverageScoreRow(
        rank=_decimal_count(rank),
        team_id=item.team_id,
        specialist_id=item.specialist_id,
        category_id=item.category_id,
        required_evidence_type_count=item.required_evidence_type_count,
        covered_evidence_type_count=item.covered_evidence_type_count,
        evidence_type_coverage_ratio=evidence_type_coverage_ratio,
        required_review_step_count=item.required_review_step_count,
        completed_review_step_count=item.completed_review_step_count,
        review_step_completion_ratio=review_step_completion_ratio,
        independent_evidence_ratio=item.independent_evidence_ratio,
        cross_review_ratio=item.cross_review_ratio,
        unresolved_gap_ratio=item.unresolved_gap_ratio,
        resolved_gap_ratio=resolved_gap_ratio,
        review_coverage_score=review_coverage_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _review_coverage_score(
    *,
    evidence_type_coverage_ratio: Decimal,
    review_step_completion_ratio: Decimal,
    independent_evidence_ratio: Decimal,
    cross_review_ratio: Decimal,
    unresolved_gap_ratio: Decimal,
    config: TeamSpecialistEvidenceReviewCoverageScoreConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            evidence_type_coverage_ratio * config.evidence_type_weight
            + review_step_completion_ratio * config.review_step_weight
            + independent_evidence_ratio * config.evidence_independence_weight
            + cross_review_ratio * config.cross_review_weight
            - unresolved_gap_ratio * config.unresolved_gap_penalty_weight,
        )


def _coverage_ratio(covered_count: Decimal, required_count: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(covered_count / required_count)


def _row_reason_codes(
    *,
    evidence_type_coverage_ratio: Decimal,
    review_step_completion_ratio: Decimal,
    independent_evidence_ratio: Decimal,
    cross_review_ratio: Decimal,
    unresolved_gap_ratio: Decimal,
    review_coverage_score: Decimal,
    config: TeamSpecialistEvidenceReviewCoverageScoreConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    if evidence_type_coverage_ratio < config.min_evidence_type_watch_ratio:
        block_reasons.append("evidence_type_coverage_block")
    if review_step_completion_ratio < config.min_review_step_watch_ratio:
        block_reasons.append("review_step_coverage_block")
    if independent_evidence_ratio < config.min_evidence_independence_watch_ratio:
        block_reasons.append("evidence_independence_block")
    if cross_review_ratio < config.min_cross_review_watch_ratio:
        block_reasons.append("cross_review_block")
    if unresolved_gap_ratio > config.max_unresolved_gap_watch_ratio:
        block_reasons.append("unresolved_gap_block")
    if review_coverage_score < config.watch_score_floor:
        block_reasons.append("evidence_review_coverage_score_block")
    if block_reasons:
        return _normalize_reason_codes(tuple(block_reasons))

    watch_reasons: list[str] = []
    if evidence_type_coverage_ratio < config.min_evidence_type_pass_ratio:
        watch_reasons.append("evidence_type_coverage_watch")
    if review_step_completion_ratio < config.min_review_step_pass_ratio:
        watch_reasons.append("review_step_coverage_watch")
    if independent_evidence_ratio < config.min_evidence_independence_pass_ratio:
        watch_reasons.append("evidence_independence_watch")
    if cross_review_ratio < config.min_cross_review_pass_ratio:
        watch_reasons.append("cross_review_watch")
    if unresolved_gap_ratio > config.max_unresolved_gap_pass_ratio:
        watch_reasons.append("unresolved_gap_watch")
    if review_coverage_score < config.pass_score_floor:
        watch_reasons.append("evidence_review_coverage_score_watch")
    if watch_reasons:
        return _normalize_reason_codes(tuple(watch_reasons))
    return ("team_specialist_evidence_review_coverage_pass",)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes == ("team_specialist_evidence_review_coverage_pass",):
        return "pass"
    return "watch"


def _report_status(rows: tuple[TeamSpecialistEvidenceReviewCoverageScoreRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_inputs(
    value: Iterable[TeamSpecialistEvidenceReviewCoverageScoreInput],
) -> tuple[TeamSpecialistEvidenceReviewCoverageScoreInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of evidence review coverage inputs")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of evidence review coverage inputs") from exc
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamSpecialistEvidenceReviewCoverageScoreInput:
            raise ValueError(
                "rows must contain TeamSpecialistEvidenceReviewCoverageScoreInput",
            )
        _require_hard_flags("input", row)
        key = (row.team_id, row.specialist_id, row.category_id)
        if key in seen:
            raise ValueError("rows must contain unique team, specialist, and category ids")
        seen.add(key)
    return tuple(sorted(rows, key=lambda row: (row.team_id, row.specialist_id, row.category_id)))


def _normalize_rows(
    value: Iterable[TeamSpecialistEvidenceReviewCoverageScoreRow],
) -> tuple[TeamSpecialistEvidenceReviewCoverageScoreRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of evidence review coverage rows")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of evidence review coverage rows") from exc
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamSpecialistEvidenceReviewCoverageScoreRow:
            raise ValueError(
                "rows must contain TeamSpecialistEvidenceReviewCoverageScoreRow",
            )
        _require_hard_flags("row", row)
        key = (row.team_id, row.specialist_id, row.category_id)
        if key in seen:
            raise ValueError("rows must contain unique team, specialist, and category ids")
        seen.add(key)
    sorted_rows = tuple(sorted(rows, key=lambda row: (row.team_id, row.specialist_id, row.category_id)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[TeamSpecialistEvidenceReviewCoverageScoreReasonCodeCount],
) -> tuple[TeamSpecialistEvidenceReviewCoverageScoreReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not TeamSpecialistEvidenceReviewCoverageScoreReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "TeamSpecialistEvidenceReviewCoverageScoreReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen.add(row.reason_code)
    sorted_rows = tuple(sorted(rows, key=lambda row: REASON_CODE_SEQUENCE.index(row.reason_code)))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return rows


def _reason_code_counts(
    rows: tuple[TeamSpecialistEvidenceReviewCoverageScoreRow, ...],
) -> tuple[TeamSpecialistEvidenceReviewCoverageScoreReasonCodeCount, ...]:
    counts: list[TeamSpecialistEvidenceReviewCoverageScoreReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                TeamSpecialistEvidenceReviewCoverageScoreReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                ),
            )
    return tuple(counts)


def _status_count(
    rows: tuple[TeamSpecialistEvidenceReviewCoverageScoreRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[TeamSpecialistEvidenceReviewCoverageScoreRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_score(
    rows: tuple[TeamSpecialistEvidenceReviewCoverageScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            sum((row.review_coverage_score for row in rows), ZERO)
            / Decimal(len(rows)),
        )


def _minimum_score(
    rows: tuple[TeamSpecialistEvidenceReviewCoverageScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.review_coverage_score for row in rows)


def _validate_config(
    config: TeamSpecialistEvidenceReviewCoverageScoreConfig,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        base_weight_total = (
            config.evidence_type_weight
            + config.review_step_weight
            + config.evidence_independence_weight
            + config.cross_review_weight
        )
    if base_weight_total != ONE:
        raise ValueError("base score weights must total 1.000000")
    if config.min_evidence_type_watch_ratio > config.min_evidence_type_pass_ratio:
        raise ValueError(
            "min_evidence_type_watch_ratio must be less than or equal to pass ratio",
        )
    if config.min_review_step_watch_ratio > config.min_review_step_pass_ratio:
        raise ValueError(
            "min_review_step_watch_ratio must be less than or equal to pass ratio",
        )
    if (
        config.min_evidence_independence_watch_ratio
        > config.min_evidence_independence_pass_ratio
    ):
        raise ValueError(
            "min_evidence_independence_watch_ratio must be less than or equal to pass ratio",
        )
    if config.min_cross_review_watch_ratio > config.min_cross_review_pass_ratio:
        raise ValueError(
            "min_cross_review_watch_ratio must be less than or equal to pass ratio",
        )
    if config.max_unresolved_gap_pass_ratio > config.max_unresolved_gap_watch_ratio:
        raise ValueError(
            "max_unresolved_gap_pass_ratio must be less than or equal to watch ratio",
        )
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must be less than or equal to pass_score_floor")


def _validate_row(row: TeamSpecialistEvidenceReviewCoverageScoreRow) -> None:
    if row.evidence_type_coverage_ratio != _coverage_ratio(
        row.covered_evidence_type_count,
        row.required_evidence_type_count,
    ):
        raise ValueError("evidence_type_coverage_ratio must match evidence counts")
    if row.review_step_completion_ratio != _coverage_ratio(
        row.completed_review_step_count,
        row.required_review_step_count,
    ):
        raise ValueError("review_step_completion_ratio must match review counts")
    if row.resolved_gap_ratio != _clamp_ratio(ONE - row.unresolved_gap_ratio):
        raise ValueError("resolved_gap_ratio must match unresolved_gap_ratio")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if (
        "team_specialist_evidence_review_coverage_pass" in row.reason_codes
        and len(row.reason_codes) > 1
    ):
        raise ValueError("pass reason must stand alone")


def _validate_report(report: TeamSpecialistEvidenceReviewCoverageScoreReport) -> None:
    rows = report.rows
    if report.item_count != _decimal_count(len(rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_review_coverage_score != _average_score(rows):
        raise ValueError("average_review_coverage_score must match rows")
    if report.minimum_review_coverage_score != _minimum_score(rows):
        raise ValueError("minimum_review_coverage_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _require_payload_hard_flags(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        _require_hard_flags(label, _DictFlags(value))
        for key, item in value.items():
            _require_payload_hard_flags(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _require_payload_hard_flags(f"{label}[{index}]", item)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_string(field_name, normalized)
    return normalized


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    _reject_unsafe_public_string(field_name, normalized)
    if not PUBLIC_IDENTIFIER_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a public identifier")
    return normalized


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of reason codes")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of reason codes") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if (
        "team_specialist_evidence_review_coverage_pass" in normalized
        and len(normalized) > 1
    ):
        raise ValueError("pass reason must stand alone")
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in normalized)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_exact(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value().quantize(QUANT):
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    quantized = _quantize(value)
    if quantized < ZERO:
        return ZERO
    if quantized > ONE:
        return ONE
    return quantized


def _quantize_exact(field_name: str, value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _report_digest(report: TeamSpecialistEvidenceReviewCoverageScoreReport) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _digest_values(values)


def _validate_payload_digest(payload: Mapping[str, object]) -> None:
    digest = _require_sha256_digest(
        "derived_validation_digest",
        payload.get("derived_validation_digest"),
    )
    values = dict(payload)
    values.pop("derived_validation_digest", None)
    if digest != _digest_values(values):
        raise ValueError("derived_validation_digest must match payload fields")


def _digest_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest payload", payload, allow_json_containers=True)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")
