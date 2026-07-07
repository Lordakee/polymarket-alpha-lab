"""Pure report-only scorer for specialist topic novelty coverage."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_TEAM_SPECIALIST_TOPIC_NOVELTY_SCORE_CONFIG_VERSION = (
    "team-specialist-topic-novelty-score-v1"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUSES = frozenset(("pass", "watch", "block"))
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REASON_CODE_SEQUENCE = (
    "topic_novelty_unseen_event_type",
    "topic_novelty_low_topic_overlap",
    "topic_novelty_low_event_type_overlap",
    "topic_novelty_low_prior_case_count",
    "topic_novelty_score_block",
    "topic_novelty_score_watch",
    "team_specialist_topic_novelty_pass",
)
UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "ref",
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
    "position",
    "sizing",
    "buy",
    "sell",
    "recommendation",
)
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_:-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_TOPIC_NOVELTY_SCORE_CONFIG_VERSION",
    "TeamSpecialistTopicNoveltyScoreConfig",
    "TeamSpecialistTopicNoveltyScoreInput",
    "TeamSpecialistTopicNoveltyScoreReasonCodeCount",
    "TeamSpecialistTopicNoveltyScoreRow",
    "TeamSpecialistTopicNoveltyScoreReport",
    "build_team_specialist_topic_novelty_score_report",
    "team_specialist_topic_novelty_score_payload",
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
class TeamSpecialistTopicNoveltyScoreConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_TEAM_SPECIALIST_TOPIC_NOVELTY_SCORE_CONFIG_VERSION
    topic_overlap_weight: Decimal = Decimal("0.450000")
    event_type_overlap_weight: Decimal = Decimal("0.350000")
    prior_case_depth_weight: Decimal = Decimal("0.200000")
    min_topic_overlap_ratio: Decimal = Decimal("0.500000")
    min_event_type_overlap_ratio: Decimal = Decimal("0.500000")
    min_prior_case_count: Decimal = Decimal("5.000000")
    full_prior_case_count: Decimal = Decimal("20.000000")
    pass_score_floor: Decimal = Decimal("0.750000")
    watch_score_floor: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistTopicNoveltyScoreConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "topic_overlap_weight",
            "event_type_overlap_weight",
            "prior_case_depth_weight",
            "min_topic_overlap_ratio",
            "min_event_type_overlap_ratio",
            "pass_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_prior_case_count", "full_prior_case_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamSpecialistTopicNoveltyScoreInput(_FinalPublicDataclass):
    team_id: str
    specialist_id: str
    topic_family_id: str
    event_type_family_id: str
    topic_overlap_ratio: Decimal
    event_type_overlap_ratio: Decimal
    prior_case_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistTopicNoveltyScoreInput, "input")
        for field_name in (
            "team_id",
            "specialist_id",
            "topic_family_id",
            "event_type_family_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in ("topic_overlap_ratio", "event_type_overlap_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "prior_case_count",
            _require_nonnegative_count_decimal("prior_case_count", self.prior_case_count),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class TeamSpecialistTopicNoveltyScoreReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamSpecialistTopicNoveltyScoreReasonCodeCount,
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
class TeamSpecialistTopicNoveltyScoreRow(_FinalPublicDataclass):
    rank: Decimal
    team_id: str
    specialist_id: str
    topic_family_id: str
    event_type_family_id: str
    topic_overlap_ratio: Decimal
    event_type_overlap_ratio: Decimal
    prior_case_count: Decimal
    prior_case_depth_score: Decimal
    novelty_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistTopicNoveltyScoreRow, "row")
        object.__setattr__(self, "rank", _require_positive_count_decimal("rank", self.rank))
        for field_name in (
            "team_id",
            "specialist_id",
            "topic_family_id",
            "event_type_family_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in ("topic_overlap_ratio", "event_type_overlap_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "prior_case_count",
            _require_nonnegative_count_decimal("prior_case_count", self.prior_case_count),
        )
        for field_name in ("prior_case_depth_score", "novelty_score"):
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
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class TeamSpecialistTopicNoveltyScoreReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_status: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_novelty_score: Decimal
    minimum_novelty_score: Decimal
    reason_code_counts: tuple[TeamSpecialistTopicNoveltyScoreReasonCodeCount, ...]
    rows: tuple[TeamSpecialistTopicNoveltyScoreRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistTopicNoveltyScoreReport, "report")
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
        for field_name in ("average_novelty_score", "minimum_novelty_score"):
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


def build_team_specialist_topic_novelty_score_report(
    rows: Iterable[TeamSpecialistTopicNoveltyScoreInput],
    *,
    generated_at: datetime,
    config: TeamSpecialistTopicNoveltyScoreConfig | None = None,
) -> TeamSpecialistTopicNoveltyScoreReport:
    if config is None:
        config = TeamSpecialistTopicNoveltyScoreConfig()
    if type(config) is not TeamSpecialistTopicNoveltyScoreConfig:
        raise ValueError("config must be a TeamSpecialistTopicNoveltyScoreConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(rows)
    scored_rows = tuple(
        _novelty_row(index, row, config)
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
        average_novelty_score=_average_score(scored_rows),
        minimum_novelty_score=_minimum_score(scored_rows),
        reason_code_counts=_reason_code_counts(scored_rows),
        rows=scored_rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return TeamSpecialistTopicNoveltyScoreReport(
        **values,
        derived_validation_digest=_digest_values(values),
    )


def team_specialist_topic_novelty_score_payload(
    report: TeamSpecialistTopicNoveltyScoreReport,
) -> dict[str, Any]:
    if type(report) is not TeamSpecialistTopicNoveltyScoreReport:
        raise ValueError("report must be a TeamSpecialistTopicNoveltyScoreReport")
    return report.payload


def _novelty_row(
    rank: int,
    item: TeamSpecialistTopicNoveltyScoreInput,
    config: TeamSpecialistTopicNoveltyScoreConfig,
) -> TeamSpecialistTopicNoveltyScoreRow:
    prior_case_depth_score = _prior_case_depth_score(
        item.prior_case_count,
        config.full_prior_case_count,
    )
    novelty_score = _novelty_score(
        topic_overlap_ratio=item.topic_overlap_ratio,
        event_type_overlap_ratio=item.event_type_overlap_ratio,
        prior_case_depth_score=prior_case_depth_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        topic_overlap_ratio=item.topic_overlap_ratio,
        event_type_overlap_ratio=item.event_type_overlap_ratio,
        prior_case_count=item.prior_case_count,
        novelty_score=novelty_score,
        config=config,
    )
    return TeamSpecialistTopicNoveltyScoreRow(
        rank=_decimal_count(rank),
        team_id=item.team_id,
        specialist_id=item.specialist_id,
        topic_family_id=item.topic_family_id,
        event_type_family_id=item.event_type_family_id,
        topic_overlap_ratio=item.topic_overlap_ratio,
        event_type_overlap_ratio=item.event_type_overlap_ratio,
        prior_case_count=item.prior_case_count,
        prior_case_depth_score=prior_case_depth_score,
        novelty_score=novelty_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _novelty_score(
    *,
    topic_overlap_ratio: Decimal,
    event_type_overlap_ratio: Decimal,
    prior_case_depth_score: Decimal,
    config: TeamSpecialistTopicNoveltyScoreConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            topic_overlap_ratio * config.topic_overlap_weight
            + event_type_overlap_ratio * config.event_type_overlap_weight
            + prior_case_depth_score * config.prior_case_depth_weight,
        )


def _prior_case_depth_score(
    prior_case_count: Decimal,
    full_prior_case_count: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(prior_case_count / full_prior_case_count)


def _row_reason_codes(
    *,
    topic_overlap_ratio: Decimal,
    event_type_overlap_ratio: Decimal,
    prior_case_count: Decimal,
    novelty_score: Decimal,
    config: TeamSpecialistTopicNoveltyScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if event_type_overlap_ratio == ZERO:
        reason_codes.append("topic_novelty_unseen_event_type")
    if topic_overlap_ratio < config.min_topic_overlap_ratio:
        reason_codes.append("topic_novelty_low_topic_overlap")
    if event_type_overlap_ratio < config.min_event_type_overlap_ratio:
        reason_codes.append("topic_novelty_low_event_type_overlap")
    if prior_case_count < config.min_prior_case_count:
        reason_codes.append("topic_novelty_low_prior_case_count")
    if novelty_score < config.watch_score_floor:
        reason_codes.append("topic_novelty_score_block")
    elif novelty_score < config.pass_score_floor and not reason_codes:
        reason_codes.append("topic_novelty_score_watch")
    if not reason_codes:
        reason_codes.append("team_specialist_topic_novelty_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "topic_novelty_unseen_event_type" in reason_codes
        or "topic_novelty_score_block" in reason_codes
    ):
        return "block"
    if reason_codes == ("team_specialist_topic_novelty_pass",):
        return "pass"
    return "watch"


def _report_status(rows: tuple[TeamSpecialistTopicNoveltyScoreRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_inputs(
    value: Iterable[TeamSpecialistTopicNoveltyScoreInput],
) -> tuple[TeamSpecialistTopicNoveltyScoreInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of topic novelty inputs")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of topic novelty inputs") from exc
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamSpecialistTopicNoveltyScoreInput:
            raise ValueError("rows must contain TeamSpecialistTopicNoveltyScoreInput")
        _require_hard_flags("input", row)
        key = (
            row.team_id,
            row.specialist_id,
            row.topic_family_id,
            row.event_type_family_id,
        )
        if key in seen:
            raise ValueError(
                "rows must contain unique team, specialist, topic, and event type ids",
            )
        seen.add(key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.team_id,
                row.specialist_id,
                row.topic_family_id,
                row.event_type_family_id,
            ),
        ),
    )


def _normalize_rows(
    value: Iterable[TeamSpecialistTopicNoveltyScoreRow],
) -> tuple[TeamSpecialistTopicNoveltyScoreRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of topic novelty rows")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of topic novelty rows") from exc
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamSpecialistTopicNoveltyScoreRow:
            raise ValueError("rows must contain TeamSpecialistTopicNoveltyScoreRow")
        _require_hard_flags("row", row)
        key = (
            row.team_id,
            row.specialist_id,
            row.topic_family_id,
            row.event_type_family_id,
        )
        if key in seen:
            raise ValueError(
                "rows must contain unique team, specialist, topic, and event type ids",
            )
        seen.add(key)
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                row.team_id,
                row.specialist_id,
                row.topic_family_id,
                row.event_type_family_id,
            ),
        ),
    )
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[TeamSpecialistTopicNoveltyScoreReasonCodeCount],
) -> tuple[TeamSpecialistTopicNoveltyScoreReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not TeamSpecialistTopicNoveltyScoreReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "TeamSpecialistTopicNoveltyScoreReasonCodeCount",
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
    rows: tuple[TeamSpecialistTopicNoveltyScoreRow, ...],
) -> tuple[TeamSpecialistTopicNoveltyScoreReasonCodeCount, ...]:
    counts: list[TeamSpecialistTopicNoveltyScoreReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                TeamSpecialistTopicNoveltyScoreReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                ),
            )
    return tuple(counts)


def _status_count(
    rows: tuple[TeamSpecialistTopicNoveltyScoreRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[TeamSpecialistTopicNoveltyScoreRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_score(rows: tuple[TeamSpecialistTopicNoveltyScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum((row.novelty_score for row in rows), ZERO) / Decimal(len(rows)))


def _minimum_score(rows: tuple[TeamSpecialistTopicNoveltyScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.novelty_score for row in rows)


def _validate_config(config: TeamSpecialistTopicNoveltyScoreConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weight_total = (
            config.topic_overlap_weight
            + config.event_type_overlap_weight
            + config.prior_case_depth_weight
        )
    if weight_total != ONE:
        raise ValueError("topic novelty weights must total 1.000000")
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must be less than or equal to pass_score_floor")
    if config.min_prior_case_count > config.full_prior_case_count:
        raise ValueError("min_prior_case_count must not exceed full_prior_case_count")


def _validate_row(row: TeamSpecialistTopicNoveltyScoreRow) -> None:
    expected_depth_score = _prior_case_depth_score(
        row.prior_case_count,
        TeamSpecialistTopicNoveltyScoreConfig().full_prior_case_count,
    )
    if row.prior_case_depth_score != expected_depth_score:
        raise ValueError("prior_case_depth_score must match prior case count")
    expected_score = _novelty_score(
        topic_overlap_ratio=row.topic_overlap_ratio,
        event_type_overlap_ratio=row.event_type_overlap_ratio,
        prior_case_depth_score=row.prior_case_depth_score,
        config=TeamSpecialistTopicNoveltyScoreConfig(),
    )
    if row.novelty_score != expected_score:
        raise ValueError("novelty_score must match scoring fields")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if "team_specialist_topic_novelty_pass" in row.reason_codes and len(row.reason_codes) > 1:
        raise ValueError("pass reason must stand alone")


def _validate_report(report: TeamSpecialistTopicNoveltyScoreReport) -> None:
    rows = report.rows
    if report.item_count != _decimal_count(len(rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_novelty_score != _average_score(rows):
        raise ValueError("average_novelty_score must match rows")
    if report.minimum_novelty_score != _minimum_score(rows):
        raise ValueError("minimum_novelty_score must match rows")
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
    if "team_specialist_topic_novelty_pass" in normalized and len(normalized) > 1:
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


def _report_digest(report: TeamSpecialistTopicNoveltyScoreReport) -> str:
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
    return sha256(canonical.encode("utf-8")).hexdigest()


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
    raise ValueError(f"unsupported public payload value in {current_path}")


def _reject_unsafe_public_key(value: str, path: str) -> None:
    _reject_unsafe_public_string(path, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    normalized = value.casefold()
    if any(term in normalized for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public payload in {field_name}")
