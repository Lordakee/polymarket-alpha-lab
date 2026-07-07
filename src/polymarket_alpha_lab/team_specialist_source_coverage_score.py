"""Pure report-only specialist public source coverage scoring."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_TEAM_SPECIALIST_SOURCE_COVERAGE_SCORE_CONFIG_VERSION = (
    "team-specialist-source-coverage-score-v1"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUSES = frozenset(("pass", "watch", "block"))
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REASON_CODE_SEQUENCE = (
    "insufficient_public_source_coverage",
    "low_public_source_independence",
    "stale_public_source_coverage",
    "low_public_source_quality",
    "source_coverage_score_watch",
    "source_coverage_score_block",
    "team_specialist_source_coverage_pass",
)
UNSAFE_PUBLIC_TERMS = (
    "market",
    "candidate",
    "slug",
    "question",
    "url",
    "source_ref",
    "source refs",
    "source reference",
    "source references",
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
    "sizing",
)
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_:-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_SOURCE_COVERAGE_SCORE_CONFIG_VERSION",
    "TeamSpecialistSourceCoverageScoreConfig",
    "TeamSpecialistSourceCoverageScoreInput",
    "TeamSpecialistSourceCoverageScoreReasonCodeCount",
    "TeamSpecialistSourceCoverageScoreRow",
    "TeamSpecialistSourceCoverageScoreReport",
    "build_team_specialist_source_coverage_score_report",
)


@dataclass(frozen=True)
class TeamSpecialistSourceCoverageScoreConfig:
    config_version: str = DEFAULT_TEAM_SPECIALIST_SOURCE_COVERAGE_SCORE_CONFIG_VERSION
    coverage_weight: Decimal = Decimal("0.400000")
    independence_weight: Decimal = Decimal("0.300000")
    freshness_weight: Decimal = Decimal("0.100000")
    quality_weight: Decimal = Decimal("0.200000")
    stale_penalty_weight: Decimal = Decimal("0.300000")
    min_coverage_ratio: Decimal = Decimal("1.000000")
    min_independent_source_ratio: Decimal = Decimal("0.600000")
    max_stale_source_ratio: Decimal = Decimal("0.250000")
    min_source_quality_score: Decimal = Decimal("0.700000")
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
            "coverage_weight",
            "independence_weight",
            "freshness_weight",
            "quality_weight",
            "stale_penalty_weight",
            "min_coverage_ratio",
            "min_independent_source_ratio",
            "max_stale_source_ratio",
            "min_source_quality_score",
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
class TeamSpecialistSourceCoverageScoreInput:
    team_id: str
    specialist_id: str
    category_id: str
    required_source_count: Decimal
    covered_source_count: Decimal
    independent_source_ratio: Decimal
    stale_source_ratio: Decimal
    source_quality_score: Decimal
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
        object.__setattr__(
            self,
            "required_source_count",
            _require_positive_count_decimal(
                "required_source_count",
                self.required_source_count,
            ),
        )
        object.__setattr__(
            self,
            "covered_source_count",
            _require_nonnegative_count_decimal(
                "covered_source_count",
                self.covered_source_count,
            ),
        )
        for field_name in (
            "independent_source_ratio",
            "stale_source_ratio",
            "source_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class TeamSpecialistSourceCoverageScoreReasonCodeCount:
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
class TeamSpecialistSourceCoverageScoreRow:
    rank: Decimal
    team_id: str
    specialist_id: str
    category_id: str
    required_source_count: Decimal
    covered_source_count: Decimal
    coverage_ratio: Decimal
    independent_source_ratio: Decimal
    stale_source_ratio: Decimal
    fresh_source_ratio: Decimal
    source_quality_score: Decimal
    coverage_score: Decimal
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
        for field_name in ("required_source_count", "covered_source_count"):
            normalizer = (
                _require_positive_count_decimal
                if field_name == "required_source_count"
                else _require_nonnegative_count_decimal
            )
            object.__setattr__(
                self,
                field_name,
                normalizer(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "coverage_ratio",
            "independent_source_ratio",
            "stale_source_ratio",
            "fresh_source_ratio",
            "source_quality_score",
            "coverage_score",
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
class TeamSpecialistSourceCoverageScoreReport:
    generated_at: datetime
    config_version: str
    report_status: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_coverage_score: Decimal
    minimum_coverage_score: Decimal
    reason_code_counts: tuple[TeamSpecialistSourceCoverageScoreReasonCodeCount, ...]
    rows: tuple[TeamSpecialistSourceCoverageScoreRow, ...]
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
        for field_name in ("average_coverage_score", "minimum_coverage_score"):
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


def build_team_specialist_source_coverage_score_report(
    rows: Iterable[TeamSpecialistSourceCoverageScoreInput],
    *,
    generated_at: datetime,
    config: TeamSpecialistSourceCoverageScoreConfig | None = None,
) -> TeamSpecialistSourceCoverageScoreReport:
    if config is None:
        config = TeamSpecialistSourceCoverageScoreConfig()
    if type(config) is not TeamSpecialistSourceCoverageScoreConfig:
        raise ValueError("config must be a TeamSpecialistSourceCoverageScoreConfig")
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
        average_coverage_score=_average_score(scored_rows),
        minimum_coverage_score=_minimum_score(scored_rows),
        reason_code_counts=_reason_code_counts(scored_rows),
        rows=scored_rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return TeamSpecialistSourceCoverageScoreReport(
        **values,
        derived_validation_digest=_digest_values(values),
    )


def _coverage_row(
    rank: int,
    item: TeamSpecialistSourceCoverageScoreInput,
    config: TeamSpecialistSourceCoverageScoreConfig,
) -> TeamSpecialistSourceCoverageScoreRow:
    coverage_ratio = _coverage_ratio(item.covered_source_count, item.required_source_count)
    fresh_source_ratio = _clamp_ratio(ONE - item.stale_source_ratio)
    coverage_score = _coverage_score(
        coverage_ratio=coverage_ratio,
        independent_source_ratio=item.independent_source_ratio,
        fresh_source_ratio=fresh_source_ratio,
        stale_source_ratio=item.stale_source_ratio,
        source_quality_score=item.source_quality_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        coverage_ratio=coverage_ratio,
        independent_source_ratio=item.independent_source_ratio,
        stale_source_ratio=item.stale_source_ratio,
        source_quality_score=item.source_quality_score,
        coverage_score=coverage_score,
        config=config,
    )
    return TeamSpecialistSourceCoverageScoreRow(
        rank=_decimal_count(rank),
        team_id=item.team_id,
        specialist_id=item.specialist_id,
        category_id=item.category_id,
        required_source_count=item.required_source_count,
        covered_source_count=item.covered_source_count,
        coverage_ratio=coverage_ratio,
        independent_source_ratio=item.independent_source_ratio,
        stale_source_ratio=item.stale_source_ratio,
        fresh_source_ratio=fresh_source_ratio,
        source_quality_score=item.source_quality_score,
        coverage_score=coverage_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _coverage_score(
    *,
    coverage_ratio: Decimal,
    independent_source_ratio: Decimal,
    fresh_source_ratio: Decimal,
    stale_source_ratio: Decimal,
    source_quality_score: Decimal,
    config: TeamSpecialistSourceCoverageScoreConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            coverage_ratio * config.coverage_weight
            + independent_source_ratio * config.independence_weight
            + fresh_source_ratio * config.freshness_weight
            + source_quality_score * config.quality_weight
            - stale_source_ratio * config.stale_penalty_weight,
        )


def _coverage_ratio(covered_source_count: Decimal, required_source_count: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(covered_source_count / required_source_count)


def _row_reason_codes(
    *,
    coverage_ratio: Decimal,
    independent_source_ratio: Decimal,
    stale_source_ratio: Decimal,
    source_quality_score: Decimal,
    coverage_score: Decimal,
    config: TeamSpecialistSourceCoverageScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if coverage_ratio < config.min_coverage_ratio:
        reason_codes.append("insufficient_public_source_coverage")
    if independent_source_ratio < config.min_independent_source_ratio:
        reason_codes.append("low_public_source_independence")
    if not reason_codes:
        if stale_source_ratio > config.max_stale_source_ratio:
            reason_codes.append("stale_public_source_coverage")
        if source_quality_score < config.min_source_quality_score:
            reason_codes.append("low_public_source_quality")
    if coverage_score < config.watch_score_floor:
        reason_codes.append("source_coverage_score_block")
    elif coverage_score < config.pass_score_floor and not reason_codes:
        reason_codes.append("source_coverage_score_watch")
    if not reason_codes:
        reason_codes.append("team_specialist_source_coverage_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "insufficient_public_source_coverage" in reason_codes
        or "low_public_source_independence" in reason_codes
        or "source_coverage_score_block" in reason_codes
    ):
        return "block"
    if reason_codes == ("team_specialist_source_coverage_pass",):
        return "pass"
    return "watch"


def _report_status(rows: tuple[TeamSpecialistSourceCoverageScoreRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_inputs(
    value: Iterable[TeamSpecialistSourceCoverageScoreInput],
) -> tuple[TeamSpecialistSourceCoverageScoreInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of coverage inputs")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of coverage inputs") from exc
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamSpecialistSourceCoverageScoreInput:
            raise ValueError("rows must contain TeamSpecialistSourceCoverageScoreInput")
        _require_hard_flags("input", row)
        key = (row.team_id, row.specialist_id, row.category_id)
        if key in seen:
            raise ValueError("rows must contain unique team, specialist, and category ids")
        seen.add(key)
    return tuple(sorted(rows, key=lambda row: (row.team_id, row.specialist_id, row.category_id)))


def _normalize_rows(
    value: Iterable[TeamSpecialistSourceCoverageScoreRow],
) -> tuple[TeamSpecialistSourceCoverageScoreRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of coverage rows")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of coverage rows") from exc
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamSpecialistSourceCoverageScoreRow:
            raise ValueError("rows must contain TeamSpecialistSourceCoverageScoreRow")
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
    value: Iterable[TeamSpecialistSourceCoverageScoreReasonCodeCount],
) -> tuple[TeamSpecialistSourceCoverageScoreReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not TeamSpecialistSourceCoverageScoreReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "TeamSpecialistSourceCoverageScoreReasonCodeCount",
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
    rows: tuple[TeamSpecialistSourceCoverageScoreRow, ...],
) -> tuple[TeamSpecialistSourceCoverageScoreReasonCodeCount, ...]:
    counts: list[TeamSpecialistSourceCoverageScoreReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                TeamSpecialistSourceCoverageScoreReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                ),
            )
    return tuple(counts)


def _status_count(rows: tuple[TeamSpecialistSourceCoverageScoreRow, ...], status: str) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[TeamSpecialistSourceCoverageScoreRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_score(rows: tuple[TeamSpecialistSourceCoverageScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum((row.coverage_score for row in rows), ZERO) / Decimal(len(rows)))


def _minimum_score(rows: tuple[TeamSpecialistSourceCoverageScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.coverage_score for row in rows)


def _validate_config(config: TeamSpecialistSourceCoverageScoreConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        base_weight_total = (
            config.coverage_weight
            + config.independence_weight
            + config.freshness_weight
            + config.quality_weight
        )
    if base_weight_total != ONE:
        raise ValueError("base score weights must total 1.000000")
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must be less than or equal to pass_score_floor")


def _validate_row(row: TeamSpecialistSourceCoverageScoreRow) -> None:
    if row.fresh_source_ratio != _clamp_ratio(ONE - row.stale_source_ratio):
        raise ValueError("fresh_source_ratio must match stale_source_ratio")
    if row.coverage_ratio != _coverage_ratio(row.covered_source_count, row.required_source_count):
        raise ValueError("coverage_ratio must match coverage counts")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.reason_codes == ("team_specialist_source_coverage_pass",) and row.status != "pass":
        raise ValueError("pass reason must match pass status")
    if "team_specialist_source_coverage_pass" in row.reason_codes and len(row.reason_codes) > 1:
        raise ValueError("pass reason must stand alone")


def _validate_report(report: TeamSpecialistSourceCoverageScoreReport) -> None:
    rows = report.rows
    if report.item_count != _decimal_count(len(rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_coverage_score != _average_score(rows):
        raise ValueError("average_coverage_score must match rows")
    if report.minimum_coverage_score != _minimum_score(rows):
        raise ValueError("minimum_coverage_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


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
    if "team_specialist_source_coverage_pass" in normalized and len(normalized) > 1:
        raise ValueError("pass reason must stand alone")
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in normalized)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
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


def _report_digest(report: TeamSpecialistSourceCoverageScoreReport) -> str:
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
