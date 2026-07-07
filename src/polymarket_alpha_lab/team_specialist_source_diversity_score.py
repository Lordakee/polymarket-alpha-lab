"""Pure report-only specialist source-type diversity scoring."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_TEAM_SPECIALIST_SOURCE_DIVERSITY_SCORE_CONFIG_VERSION = (
    "team-specialist-source-diversity-score-v1"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUSES = frozenset(("pass", "watch", "block"))
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REASON_CODE_SEQUENCE = (
    "single_source_type_block",
    "insufficient_source_type_coverage",
    "high_primary_source_type_concentration",
    "low_source_type_independence",
    "source_diversity_score_block",
    "source_diversity_score_watch",
    "team_specialist_source_diversity_pass",
)
UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "url",
    "dsn",
    "table",
    "token",
    "secret",
    "auth",
    "wal" + "let",
    "order",
    "trade",
    "position",
    "sizing",
    "buy",
    "sell",
    "recommendation",
)
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_:-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_SOURCE_DIVERSITY_SCORE_CONFIG_VERSION",
    "TeamSpecialistSourceDiversityScoreConfig",
    "TeamSpecialistSourceDiversityScoreInput",
    "TeamSpecialistSourceDiversityScoreReasonCodeCount",
    "TeamSpecialistSourceDiversityScoreRow",
    "TeamSpecialistSourceDiversityScoreReport",
    "build_team_specialist_source_diversity_score_report",
    "team_specialist_source_diversity_score_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class TeamSpecialistSourceDiversityScoreConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_TEAM_SPECIALIST_SOURCE_DIVERSITY_SCORE_CONFIG_VERSION
    coverage_weight: Decimal = Decimal("0.500000")
    concentration_spread_weight: Decimal = Decimal("0.300000")
    independence_weight: Decimal = Decimal("0.200000")
    min_source_type_coverage_ratio: Decimal = Decimal("1.000000")
    max_primary_source_type_share: Decimal = Decimal("0.600000")
    min_independent_source_type_ratio: Decimal = Decimal("0.500000")
    pass_score_floor: Decimal = Decimal("0.800000")
    watch_score_floor: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistSourceDiversityScoreConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "coverage_weight",
            "concentration_spread_weight",
            "independence_weight",
            "min_source_type_coverage_ratio",
            "max_primary_source_type_share",
            "min_independent_source_type_ratio",
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
class TeamSpecialistSourceDiversityScoreInput(_FinalPublicDataclass):
    team_id: str
    specialist_id: str
    topic_id: str
    required_source_type_count: Decimal
    observed_source_type_count: Decimal
    primary_source_type_share: Decimal
    independent_source_type_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistSourceDiversityScoreInput, "input")
        for field_name in ("team_id", "specialist_id", "topic_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_source_type_count",
            _require_positive_count_decimal(
                "required_source_type_count",
                self.required_source_type_count,
            ),
        )
        object.__setattr__(
            self,
            "observed_source_type_count",
            _require_nonnegative_count_decimal(
                "observed_source_type_count",
                self.observed_source_type_count,
            ),
        )
        for field_name in (
            "primary_source_type_share",
            "independent_source_type_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class TeamSpecialistSourceDiversityScoreReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamSpecialistSourceDiversityScoreReasonCodeCount,
            "reason_code_count",
        )
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
class TeamSpecialistSourceDiversityScoreRow(_FinalPublicDataclass):
    rank: Decimal
    team_id: str
    specialist_id: str
    topic_id: str
    required_source_type_count: Decimal
    observed_source_type_count: Decimal
    source_type_coverage_ratio: Decimal
    primary_source_type_share: Decimal
    concentration_spread_score: Decimal
    independent_source_type_ratio: Decimal
    diversity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistSourceDiversityScoreRow, "row")
        object.__setattr__(self, "rank", _require_positive_count_decimal("rank", self.rank))
        for field_name in ("team_id", "specialist_id", "topic_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_source_type_count",
            _require_positive_count_decimal(
                "required_source_type_count",
                self.required_source_type_count,
            ),
        )
        object.__setattr__(
            self,
            "observed_source_type_count",
            _require_nonnegative_count_decimal(
                "observed_source_type_count",
                self.observed_source_type_count,
            ),
        )
        for field_name in (
            "source_type_coverage_ratio",
            "primary_source_type_share",
            "concentration_spread_score",
            "independent_source_type_ratio",
            "diversity_score",
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
class TeamSpecialistSourceDiversityScoreReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_status: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_diversity_score: Decimal
    minimum_diversity_score: Decimal
    reason_code_counts: tuple[TeamSpecialistSourceDiversityScoreReasonCodeCount, ...]
    rows: tuple[TeamSpecialistSourceDiversityScoreRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistSourceDiversityScoreReport, "report")
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
        for field_name in ("average_diversity_score", "minimum_diversity_score"):
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


def build_team_specialist_source_diversity_score_report(
    rows: Iterable[TeamSpecialistSourceDiversityScoreInput],
    *,
    generated_at: datetime,
    config: TeamSpecialistSourceDiversityScoreConfig | None = None,
) -> TeamSpecialistSourceDiversityScoreReport:
    if config is None:
        config = TeamSpecialistSourceDiversityScoreConfig()
    if type(config) is not TeamSpecialistSourceDiversityScoreConfig:
        raise ValueError("config must be a TeamSpecialistSourceDiversityScoreConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(rows)
    scored_rows = tuple(
        _diversity_row(index, row, config)
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
        average_diversity_score=_average_score(scored_rows),
        minimum_diversity_score=_minimum_score(scored_rows),
        reason_code_counts=_reason_code_counts(scored_rows),
        rows=scored_rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return TeamSpecialistSourceDiversityScoreReport(
        **values,
        derived_validation_digest=_digest_values(values),
    )


def team_specialist_source_diversity_score_payload(
    report: TeamSpecialistSourceDiversityScoreReport,
) -> dict[str, Any]:
    if type(report) is not TeamSpecialistSourceDiversityScoreReport:
        raise ValueError("report must be a TeamSpecialistSourceDiversityScoreReport")
    return report.payload


def _diversity_row(
    rank: int,
    item: TeamSpecialistSourceDiversityScoreInput,
    config: TeamSpecialistSourceDiversityScoreConfig,
) -> TeamSpecialistSourceDiversityScoreRow:
    source_type_coverage_ratio = _coverage_ratio(
        item.observed_source_type_count,
        item.required_source_type_count,
    )
    concentration_spread_score = _clamp_ratio(ONE - item.primary_source_type_share)
    diversity_score = _diversity_score(
        source_type_coverage_ratio=source_type_coverage_ratio,
        concentration_spread_score=concentration_spread_score,
        independent_source_type_ratio=item.independent_source_type_ratio,
        config=config,
    )
    reason_codes = _row_reason_codes(
        observed_source_type_count=item.observed_source_type_count,
        source_type_coverage_ratio=source_type_coverage_ratio,
        primary_source_type_share=item.primary_source_type_share,
        independent_source_type_ratio=item.independent_source_type_ratio,
        diversity_score=diversity_score,
        config=config,
    )
    return TeamSpecialistSourceDiversityScoreRow(
        rank=_decimal_count(rank),
        team_id=item.team_id,
        specialist_id=item.specialist_id,
        topic_id=item.topic_id,
        required_source_type_count=item.required_source_type_count,
        observed_source_type_count=item.observed_source_type_count,
        source_type_coverage_ratio=source_type_coverage_ratio,
        primary_source_type_share=item.primary_source_type_share,
        concentration_spread_score=concentration_spread_score,
        independent_source_type_ratio=item.independent_source_type_ratio,
        diversity_score=diversity_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _diversity_score(
    *,
    source_type_coverage_ratio: Decimal,
    concentration_spread_score: Decimal,
    independent_source_type_ratio: Decimal,
    config: TeamSpecialistSourceDiversityScoreConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            source_type_coverage_ratio * config.coverage_weight
            + concentration_spread_score * config.concentration_spread_weight
            + independent_source_type_ratio * config.independence_weight,
        )


def _coverage_ratio(
    observed_source_type_count: Decimal,
    required_source_type_count: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(observed_source_type_count / required_source_type_count)


def _row_reason_codes(
    *,
    observed_source_type_count: Decimal,
    source_type_coverage_ratio: Decimal,
    primary_source_type_share: Decimal,
    independent_source_type_ratio: Decimal,
    diversity_score: Decimal,
    config: TeamSpecialistSourceDiversityScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observed_source_type_count <= ONE:
        reason_codes.append("single_source_type_block")
    if source_type_coverage_ratio < config.min_source_type_coverage_ratio:
        reason_codes.append("insufficient_source_type_coverage")
    if primary_source_type_share > config.max_primary_source_type_share:
        reason_codes.append("high_primary_source_type_concentration")
    if independent_source_type_ratio < config.min_independent_source_type_ratio:
        reason_codes.append("low_source_type_independence")
    if diversity_score < config.watch_score_floor:
        reason_codes.append("source_diversity_score_block")
    elif diversity_score < config.pass_score_floor and not reason_codes:
        reason_codes.append("source_diversity_score_watch")
    if not reason_codes:
        reason_codes.append("team_specialist_source_diversity_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "single_source_type_block" in reason_codes
        or "low_source_type_independence" in reason_codes
        or "source_diversity_score_block" in reason_codes
    ):
        return "block"
    if reason_codes == ("team_specialist_source_diversity_pass",):
        return "pass"
    return "watch"


def _report_status(rows: tuple[TeamSpecialistSourceDiversityScoreRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_inputs(
    value: Iterable[TeamSpecialistSourceDiversityScoreInput],
) -> tuple[TeamSpecialistSourceDiversityScoreInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of diversity inputs")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of diversity inputs") from exc
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamSpecialistSourceDiversityScoreInput:
            raise ValueError("rows must contain TeamSpecialistSourceDiversityScoreInput")
        _require_hard_flags("input", row)
        key = (row.team_id, row.specialist_id, row.topic_id)
        if key in seen:
            raise ValueError("rows must contain unique team, specialist, and topic ids")
        seen.add(key)
    return tuple(sorted(rows, key=lambda row: (row.team_id, row.specialist_id, row.topic_id)))


def _normalize_rows(
    value: Iterable[TeamSpecialistSourceDiversityScoreRow],
) -> tuple[TeamSpecialistSourceDiversityScoreRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of diversity rows")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of diversity rows") from exc
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamSpecialistSourceDiversityScoreRow:
            raise ValueError("rows must contain TeamSpecialistSourceDiversityScoreRow")
        _require_hard_flags("row", row)
        key = (row.team_id, row.specialist_id, row.topic_id)
        if key in seen:
            raise ValueError("rows must contain unique team, specialist, and topic ids")
        seen.add(key)
    sorted_rows = tuple(sorted(rows, key=lambda row: (row.team_id, row.specialist_id, row.topic_id)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[TeamSpecialistSourceDiversityScoreReasonCodeCount],
) -> tuple[TeamSpecialistSourceDiversityScoreReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not TeamSpecialistSourceDiversityScoreReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "TeamSpecialistSourceDiversityScoreReasonCodeCount",
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
    rows: tuple[TeamSpecialistSourceDiversityScoreRow, ...],
) -> tuple[TeamSpecialistSourceDiversityScoreReasonCodeCount, ...]:
    counts: list[TeamSpecialistSourceDiversityScoreReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                TeamSpecialistSourceDiversityScoreReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                ),
            )
    return tuple(counts)


def _status_count(
    rows: tuple[TeamSpecialistSourceDiversityScoreRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[TeamSpecialistSourceDiversityScoreRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_score(rows: tuple[TeamSpecialistSourceDiversityScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum((row.diversity_score for row in rows), ZERO) / Decimal(len(rows)))


def _minimum_score(rows: tuple[TeamSpecialistSourceDiversityScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.diversity_score for row in rows)


def _validate_config(config: TeamSpecialistSourceDiversityScoreConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weight_total = (
            config.coverage_weight
            + config.concentration_spread_weight
            + config.independence_weight
        )
    if weight_total != ONE:
        raise ValueError("source diversity weights must total 1.000000")
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must be less than or equal to pass_score_floor")


def _validate_row(row: TeamSpecialistSourceDiversityScoreRow) -> None:
    if row.source_type_coverage_ratio != _coverage_ratio(
        row.observed_source_type_count,
        row.required_source_type_count,
    ):
        raise ValueError("source_type_coverage_ratio must match source type counts")
    if row.concentration_spread_score != _clamp_ratio(ONE - row.primary_source_type_share):
        raise ValueError("concentration_spread_score must match primary share")
    expected_score = _diversity_score(
        source_type_coverage_ratio=row.source_type_coverage_ratio,
        concentration_spread_score=row.concentration_spread_score,
        independent_source_type_ratio=row.independent_source_type_ratio,
        config=TeamSpecialistSourceDiversityScoreConfig(),
    )
    if row.diversity_score != expected_score:
        raise ValueError("diversity_score must match scoring fields")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if "team_specialist_source_diversity_pass" in row.reason_codes and len(row.reason_codes) > 1:
        raise ValueError("pass reason must stand alone")


def _validate_report(report: TeamSpecialistSourceDiversityScoreReport) -> None:
    rows = report.rows
    if report.item_count != _decimal_count(len(rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_diversity_score != _average_score(rows):
        raise ValueError("average_diversity_score must match rows")
    if report.minimum_diversity_score != _minimum_score(rows):
        raise ValueError("minimum_diversity_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


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
    if "team_specialist_source_diversity_pass" in normalized and len(normalized) > 1:
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


def _report_digest(report: TeamSpecialistSourceDiversityScoreReport) -> str:
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
