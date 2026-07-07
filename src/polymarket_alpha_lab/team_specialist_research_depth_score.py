"""Pure report-only specialist research depth scoring."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_TEAM_SPECIALIST_RESEARCH_DEPTH_SCORE_CONFIG_VERSION = (
    "team-specialist-research-depth-score-v1"
)

TEAM_SPECIALIST_RESEARCH_DEPTH_SCORE_FACTORS = (
    "evidence_depth",
    "viewpoint_depth",
    "contradiction_depth",
    "synthesis_quality",
    "rank_context",
    "freshness",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUSES = frozenset(("pass", "watch", "block"))
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REASON_CODE_SEQUENCE = (
    "insufficient_evidence_depth",
    "insufficient_viewpoint_depth",
    "insufficient_contradiction_review",
    "stale_evidence_depth",
    "low_rank_context_depth",
    "research_depth_score_watch",
    "research_depth_score_block",
    "team_specialist_research_depth_pass",
)
UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "url",
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
    "DEFAULT_TEAM_SPECIALIST_RESEARCH_DEPTH_SCORE_CONFIG_VERSION",
    "TEAM_SPECIALIST_RESEARCH_DEPTH_SCORE_FACTORS",
    "TeamSpecialistResearchDepthScoreConfig",
    "TeamSpecialistResearchDepthInput",
    "TeamSpecialistResearchDepthReasonCodeCount",
    "TeamSpecialistResearchDepthRow",
    "TeamSpecialistResearchDepthReport",
    "build_team_specialist_research_depth_score_report",
    "team_specialist_research_depth_score_payload",
)


@dataclass(frozen=True)
class TeamSpecialistResearchDepthScoreConfig:
    config_version: str = DEFAULT_TEAM_SPECIALIST_RESEARCH_DEPTH_SCORE_CONFIG_VERSION
    evidence_depth_weight: Decimal = Decimal("0.300000")
    viewpoint_depth_weight: Decimal = Decimal("0.200000")
    contradiction_depth_weight: Decimal = Decimal("0.150000")
    synthesis_quality_weight: Decimal = Decimal("0.200000")
    rank_context_weight: Decimal = Decimal("0.100000")
    freshness_weight: Decimal = Decimal("0.050000")
    min_pass_depth_score: Decimal = Decimal("0.850000")
    min_watch_depth_score: Decimal = Decimal("0.650000")
    min_evidence_item_count: Decimal = Decimal("4.000000")
    min_viewpoint_count: Decimal = Decimal("2.000000")
    min_contradiction_check_count: Decimal = Decimal("1.000000")
    max_pass_stale_evidence_ratio: Decimal = Decimal("0.250000")
    max_watch_stale_evidence_ratio: Decimal = Decimal("0.500000")
    min_pass_rank_context_score: Decimal = Decimal("0.700000")
    min_watch_rank_context_score: Decimal = Decimal("0.500000")
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
            "evidence_depth_weight",
            "viewpoint_depth_weight",
            "contradiction_depth_weight",
            "synthesis_quality_weight",
            "rank_context_weight",
            "freshness_weight",
            "min_pass_depth_score",
            "min_watch_depth_score",
            "max_pass_stale_evidence_ratio",
            "max_watch_stale_evidence_ratio",
            "min_pass_rank_context_score",
            "min_watch_rank_context_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_evidence_item_count",
            "min_viewpoint_count",
            "min_contradiction_check_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamSpecialistResearchDepthInput:
    team_key: str
    specialist_key: str
    category_key: str
    evidence_item_count: Decimal
    viewpoint_count: Decimal
    contradiction_check_count: Decimal
    synthesis_quality_score: Decimal
    rank_context_score: Decimal
    stale_evidence_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_key", "specialist_key", "category_key"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_item_count",
            "viewpoint_count",
            "contradiction_check_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "synthesis_quality_score",
            "rank_context_score",
            "stale_evidence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class TeamSpecialistResearchDepthReasonCodeCount:
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
class TeamSpecialistResearchDepthRow:
    rank: Decimal
    team_key: str
    specialist_key: str
    category_key: str
    evidence_item_count: Decimal
    viewpoint_count: Decimal
    contradiction_check_count: Decimal
    evidence_depth_ratio: Decimal
    viewpoint_depth_ratio: Decimal
    contradiction_depth_ratio: Decimal
    synthesis_quality_score: Decimal
    rank_context_score: Decimal
    stale_evidence_ratio: Decimal
    freshness_score: Decimal
    research_depth_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _require_positive_count_decimal("rank", self.rank))
        for field_name in ("team_key", "specialist_key", "category_key"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_item_count",
            "viewpoint_count",
            "contradiction_check_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "evidence_depth_ratio",
            "viewpoint_depth_ratio",
            "contradiction_depth_ratio",
            "synthesis_quality_score",
            "rank_context_score",
            "stale_evidence_ratio",
            "freshness_score",
            "research_depth_score",
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
class TeamSpecialistResearchDepthReport:
    generated_at: datetime
    config_version: str
    report_status: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_research_depth_score: Decimal
    minimum_research_depth_score: Decimal
    reason_code_counts: tuple[TeamSpecialistResearchDepthReasonCodeCount, ...]
    rows: tuple[TeamSpecialistResearchDepthRow, ...]
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
        for field_name in ("average_research_depth_score", "minimum_research_depth_score"):
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
        return payload


def build_team_specialist_research_depth_score_report(
    rows: Iterable[TeamSpecialistResearchDepthInput],
    *,
    generated_at: datetime,
    config: TeamSpecialistResearchDepthScoreConfig | None = None,
) -> TeamSpecialistResearchDepthReport:
    if config is None:
        config = TeamSpecialistResearchDepthScoreConfig()
    if type(config) is not TeamSpecialistResearchDepthScoreConfig:
        raise ValueError("config must be a TeamSpecialistResearchDepthScoreConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(rows)
    scored_rows = tuple(
        _research_depth_row(index, row, config)
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
        average_research_depth_score=_average_score(scored_rows),
        minimum_research_depth_score=_minimum_score(scored_rows),
        reason_code_counts=_reason_code_counts(scored_rows),
        rows=scored_rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return TeamSpecialistResearchDepthReport(
        **values,
        derived_validation_digest=_digest_values(values),
    )


def team_specialist_research_depth_score_payload(
    value: TeamSpecialistResearchDepthReport | Mapping[str, Any],
) -> dict[str, Any]:
    if type(value) is TeamSpecialistResearchDepthReport:
        return value.payload
    if not isinstance(value, Mapping):
        raise ValueError("value must be a TeamSpecialistResearchDepthReport")
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    digest = _require_sha256_digest(
        "derived_validation_digest",
        payload.get("derived_validation_digest"),
    )
    values = dict(payload)
    values.pop("derived_validation_digest", None)
    if digest != _digest_values(values):
        raise ValueError("derived_validation_digest must match payload fields")
    return payload


def _research_depth_row(
    rank: int,
    item: TeamSpecialistResearchDepthInput,
    config: TeamSpecialistResearchDepthScoreConfig,
) -> TeamSpecialistResearchDepthRow:
    evidence_depth_ratio = _count_ratio(
        item.evidence_item_count,
        config.min_evidence_item_count,
    )
    viewpoint_depth_ratio = _count_ratio(item.viewpoint_count, config.min_viewpoint_count)
    contradiction_depth_ratio = _count_ratio(
        item.contradiction_check_count,
        config.min_contradiction_check_count,
    )
    freshness_score = _clamp_ratio(ONE - item.stale_evidence_ratio)
    research_depth_score = _research_depth_score(
        evidence_depth_ratio=evidence_depth_ratio,
        viewpoint_depth_ratio=viewpoint_depth_ratio,
        contradiction_depth_ratio=contradiction_depth_ratio,
        synthesis_quality_score=item.synthesis_quality_score,
        rank_context_score=item.rank_context_score,
        freshness_score=freshness_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        evidence_depth_ratio=evidence_depth_ratio,
        viewpoint_depth_ratio=viewpoint_depth_ratio,
        contradiction_depth_ratio=contradiction_depth_ratio,
        stale_evidence_ratio=item.stale_evidence_ratio,
        rank_context_score=item.rank_context_score,
        research_depth_score=research_depth_score,
        config=config,
    )
    return TeamSpecialistResearchDepthRow(
        rank=_decimal_count(rank),
        team_key=item.team_key,
        specialist_key=item.specialist_key,
        category_key=item.category_key,
        evidence_item_count=item.evidence_item_count,
        viewpoint_count=item.viewpoint_count,
        contradiction_check_count=item.contradiction_check_count,
        evidence_depth_ratio=evidence_depth_ratio,
        viewpoint_depth_ratio=viewpoint_depth_ratio,
        contradiction_depth_ratio=contradiction_depth_ratio,
        synthesis_quality_score=item.synthesis_quality_score,
        rank_context_score=item.rank_context_score,
        stale_evidence_ratio=item.stale_evidence_ratio,
        freshness_score=freshness_score,
        research_depth_score=research_depth_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _research_depth_score(
    *,
    evidence_depth_ratio: Decimal,
    viewpoint_depth_ratio: Decimal,
    contradiction_depth_ratio: Decimal,
    synthesis_quality_score: Decimal,
    rank_context_score: Decimal,
    freshness_score: Decimal,
    config: TeamSpecialistResearchDepthScoreConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            evidence_depth_ratio * config.evidence_depth_weight
            + viewpoint_depth_ratio * config.viewpoint_depth_weight
            + contradiction_depth_ratio * config.contradiction_depth_weight
            + synthesis_quality_score * config.synthesis_quality_weight
            + rank_context_score * config.rank_context_weight
            + freshness_score * config.freshness_weight,
        )


def _row_reason_codes(
    *,
    evidence_depth_ratio: Decimal,
    viewpoint_depth_ratio: Decimal,
    contradiction_depth_ratio: Decimal,
    stale_evidence_ratio: Decimal,
    rank_context_score: Decimal,
    research_depth_score: Decimal,
    config: TeamSpecialistResearchDepthScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if evidence_depth_ratio < ONE:
        reason_codes.append("insufficient_evidence_depth")
    if viewpoint_depth_ratio < ONE:
        reason_codes.append("insufficient_viewpoint_depth")
    if contradiction_depth_ratio < ONE:
        reason_codes.append("insufficient_contradiction_review")
    if stale_evidence_ratio > config.max_pass_stale_evidence_ratio:
        reason_codes.append("stale_evidence_depth")
    if rank_context_score < config.min_watch_rank_context_score:
        reason_codes.append("low_rank_context_depth")
    elif rank_context_score < config.min_pass_rank_context_score and not reason_codes:
        reason_codes.append("low_rank_context_depth")
    if research_depth_score < config.min_watch_depth_score:
        reason_codes.append("research_depth_score_block")
    elif research_depth_score < config.min_pass_depth_score and not reason_codes:
        reason_codes.append("research_depth_score_watch")
    if not reason_codes:
        reason_codes.append("team_specialist_research_depth_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    block_reasons = {
        "insufficient_evidence_depth",
        "insufficient_viewpoint_depth",
        "insufficient_contradiction_review",
        "research_depth_score_block",
    }
    if any(reason_code in block_reasons for reason_code in reason_codes):
        return "block"
    if reason_codes == ("team_specialist_research_depth_pass",):
        return "pass"
    return "watch"


def _report_status(rows: tuple[TeamSpecialistResearchDepthRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_inputs(
    value: Iterable[TeamSpecialistResearchDepthInput],
) -> tuple[TeamSpecialistResearchDepthInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of research depth inputs")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of research depth inputs") from exc
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamSpecialistResearchDepthInput:
            raise ValueError("rows must contain TeamSpecialistResearchDepthInput")
        _require_hard_flags("input", row)
        key = (row.team_key, row.specialist_key, row.category_key)
        if key in seen:
            raise ValueError("rows must contain unique team, specialist, and category keys")
        seen.add(key)
    return tuple(sorted(rows, key=lambda row: (row.team_key, row.specialist_key, row.category_key)))


def _normalize_rows(
    value: Iterable[TeamSpecialistResearchDepthRow],
) -> tuple[TeamSpecialistResearchDepthRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of research depth rows")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of research depth rows") from exc
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamSpecialistResearchDepthRow:
            raise ValueError("rows must contain TeamSpecialistResearchDepthRow")
        _require_hard_flags("row", row)
        key = (row.team_key, row.specialist_key, row.category_key)
        if key in seen:
            raise ValueError("rows must contain unique team, specialist, and category keys")
        seen.add(key)
    sorted_rows = tuple(sorted(rows, key=lambda row: (row.team_key, row.specialist_key, row.category_key)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[TeamSpecialistResearchDepthReasonCodeCount],
) -> tuple[TeamSpecialistResearchDepthReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not TeamSpecialistResearchDepthReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "TeamSpecialistResearchDepthReasonCodeCount",
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
    rows: tuple[TeamSpecialistResearchDepthRow, ...],
) -> tuple[TeamSpecialistResearchDepthReasonCodeCount, ...]:
    counts: list[TeamSpecialistResearchDepthReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                TeamSpecialistResearchDepthReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                ),
            )
    return tuple(counts)


def _status_count(rows: tuple[TeamSpecialistResearchDepthRow, ...], status: str) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[TeamSpecialistResearchDepthRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_score(rows: tuple[TeamSpecialistResearchDepthRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum((row.research_depth_score for row in rows), ZERO) / Decimal(len(rows)))


def _minimum_score(rows: tuple[TeamSpecialistResearchDepthRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.research_depth_score for row in rows)


def _validate_config(config: TeamSpecialistResearchDepthScoreConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weight_total = (
            config.evidence_depth_weight
            + config.viewpoint_depth_weight
            + config.contradiction_depth_weight
            + config.synthesis_quality_weight
            + config.rank_context_weight
            + config.freshness_weight
        )
    if weight_total != ONE:
        raise ValueError("research depth score weights must total 1.000000")
    if config.min_watch_depth_score > config.min_pass_depth_score:
        raise ValueError("min_watch_depth_score must not exceed min_pass_depth_score")
    if config.max_pass_stale_evidence_ratio > config.max_watch_stale_evidence_ratio:
        raise ValueError(
            "max_pass_stale_evidence_ratio must not exceed "
            "max_watch_stale_evidence_ratio",
        )
    if config.min_watch_rank_context_score > config.min_pass_rank_context_score:
        raise ValueError(
            "min_watch_rank_context_score must not exceed "
            "min_pass_rank_context_score",
        )


def _validate_row(row: TeamSpecialistResearchDepthRow) -> None:
    if row.freshness_score != _clamp_ratio(ONE - row.stale_evidence_ratio):
        raise ValueError("freshness_score must match stale_evidence_ratio")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if "team_specialist_research_depth_pass" in row.reason_codes and len(row.reason_codes) > 1:
        raise ValueError("pass reason must stand alone")


def _validate_report(report: TeamSpecialistResearchDepthReport) -> None:
    rows = report.rows
    if report.item_count != _decimal_count(len(rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_research_depth_score != _average_score(rows):
        raise ValueError("average_research_depth_score must match rows")
    if report.minimum_research_depth_score != _minimum_score(rows):
        raise ValueError("minimum_research_depth_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(payload: Mapping[str, Any]) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


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
    if "team_specialist_research_depth_pass" in normalized and len(normalized) > 1:
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


def _count_ratio(count: Decimal, threshold: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(count / threshold)


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


def _report_digest(report: TeamSpecialistResearchDepthReport) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _digest_values(values)


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
