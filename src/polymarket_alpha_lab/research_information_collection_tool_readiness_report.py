"""Pure report-only readiness view for research information collection tools."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_INFORMATION_COLLECTION_TOOL_READINESS_CONFIG_VERSION = (
    "research-information-collection-tool-readiness-report-v0"
)

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

PASS_REASON = "research_information_collection_tool_readiness_pass"
WATCH_REASON = "research_information_collection_tool_readiness_watch"
BLOCK_REASON = "research_information_collection_tool_readiness_block"
WATCH_GAP_REASON = "research_information_collection_tool_readiness_watch_gap"
WATCH_SCORE_REASON = "research_information_collection_tool_readiness_watch_score"
BLOCK_HARD_GAP_REASON = (
    "research_information_collection_tool_readiness_block_hard_gap"
)
BLOCK_SCORE_REASON = "research_information_collection_tool_readiness_block_score"

REASON_CODES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    WATCH_GAP_REASON,
    WATCH_SCORE_REASON,
    BLOCK_HARD_GAP_REASON,
    BLOCK_SCORE_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RATIO_QUANTUM = Decimal("0.000001")
SCORE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE = Decimal("1")
SCORE_FIELD_NAMES = (
    "coverage_score",
    "extraction_score",
    "verification_score",
    "stability_score",
)
SOFT_GAP_SCORE_PENALTY = Decimal("0.035000")
HARD_GAP_SCORE_PENALTY = Decimal("0.030000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join_parts("raw", "candidate", "id"),
        _join_parts("candidate", "id"),
        _join_parts("market", "id"),
        _join_parts("market", "slug"),
        "question",
        _join_parts("source", "ref"),
        _join_parts("source", "url"),
        _join_parts("source", "text"),
        "dsn",
        "table",
        "token",
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
        _join_parts("au", "th"),
        _join_parts("private", "key"),
        _join_parts("acc", "ount"),
        "balance",
        _join_parts("li", "ve"),
        "submit",
        "cancel",
        "signing",
    ),
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
class ResearchInformationCollectionToolReadinessConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_INFORMATION_COLLECTION_TOOL_READINESS_CONFIG_VERSION
    )
    pass_score_floor: Decimal = Decimal("0.850000")
    block_score_floor: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    external_collection_allowed: bool = False
    network_write_allowed: bool = False

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchInformationCollectionToolReadinessConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        for field_name in ("pass_score_floor", "block_score_floor"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_score_floor > self.pass_score_floor:
            raise ValueError("block_score_floor must be <= pass_score_floor")
        _require_hard_flags("config", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchInformationCollectionToolReadinessInput(_FinalPublicDataclass):
    tool_name: str
    task_family: str
    coverage_score: Decimal
    extraction_score: Decimal
    verification_score: Decimal
    stability_score: Decimal
    gap_count: Decimal = ZERO
    hard_gap_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    external_collection_allowed: bool = False
    network_write_allowed: bool = False

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchInformationCollectionToolReadinessInput,
            "input",
        )
        _require_public_string("tool_name", self.tool_name)
        _require_public_string("task_family", self.task_family)
        for field_name in SCORE_FIELD_NAMES:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("gap_count", "hard_gap_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_surface("input", self)


@dataclass(frozen=True)
class ResearchInformationCollectionToolReadinessRow(_FinalPublicDataclass):
    tool_name: str
    task_family: str
    status: str
    coverage_score: Decimal
    extraction_score: Decimal
    verification_score: Decimal
    stability_score: Decimal
    readiness_score: Decimal
    gap_count: Decimal
    hard_gap_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    external_collection_allowed: bool = False
    network_write_allowed: bool = False

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchInformationCollectionToolReadinessRow, "row")
        _require_public_string("tool_name", self.tool_name)
        _require_public_string("task_family", self.task_family)
        _require_status("status", self.status)
        for field_name in (*SCORE_FIELD_NAMES, "readiness_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("gap_count", "hard_gap_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchInformationCollectionToolReadinessDigest(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    tool_task_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    pass_ratio: Decimal
    watch_ratio: Decimal
    block_ratio: Decimal
    mean_readiness_score: Decimal
    min_readiness_score: Decimal
    max_readiness_score: Decimal
    public_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    external_collection_allowed: bool = False
    network_write_allowed: bool = False

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchInformationCollectionToolReadinessDigest,
            "digest",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        for field_name in (
            "tool_task_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_ratio",
            "watch_ratio",
            "block_ratio",
            "mean_readiness_score",
            "min_readiness_score",
            "max_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_digest("public_digest", self.public_digest)
        _require_hard_flags("digest", self)
        _reject_unsafe_public_surface("digest", self)


@dataclass(frozen=True)
class ResearchInformationCollectionToolReadinessReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    tool_task_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    pass_ratio: Decimal
    watch_ratio: Decimal
    block_ratio: Decimal
    mean_readiness_score: Decimal
    min_readiness_score: Decimal
    max_readiness_score: Decimal
    rows: tuple[ResearchInformationCollectionToolReadinessRow, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    external_collection_allowed: bool = False
    network_write_allowed: bool = False

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchInformationCollectionToolReadinessReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        for field_name in (
            "tool_task_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_ratio",
            "watch_ratio",
            "block_ratio",
            "mean_readiness_score",
            "min_readiness_score",
            "max_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _require_or_set_public_digest(self)
        _reject_unsafe_public_surface("report", self)


def build_research_information_collection_tool_readiness_report(
    inputs: list[ResearchInformationCollectionToolReadinessInput]
    | tuple[ResearchInformationCollectionToolReadinessInput, ...],
    *,
    config: ResearchInformationCollectionToolReadinessConfig,
    generated_at: datetime,
) -> ResearchInformationCollectionToolReadinessReport:
    if type(config) is not ResearchInformationCollectionToolReadinessConfig:
        raise ValueError(
            "config must be a ResearchInformationCollectionToolReadinessConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_input(input_row, config=config)
                for input_row in _normalize_inputs(inputs)
            ),
            key=_row_sort_key,
        ),
    )
    tool_task_count = _count(len(rows))
    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    block_count = _status_count(rows, "block")
    scores = tuple(row.readiness_score for row in rows)
    return ResearchInformationCollectionToolReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        tool_task_count=tool_task_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        pass_ratio=_ratio(pass_count, tool_task_count),
        watch_ratio=_ratio(watch_count, tool_task_count),
        block_ratio=_ratio(block_count, tool_task_count),
        mean_readiness_score=_mean_decimal(scores),
        min_readiness_score=_min_decimal(scores),
        max_readiness_score=_max_decimal(scores),
        rows=rows,
    )


def research_information_collection_tool_readiness_report_to_payload(
    report: ResearchInformationCollectionToolReadinessReport,
) -> dict[str, Any]:
    if type(report) is not ResearchInformationCollectionToolReadinessReport:
        raise ValueError(
            "report must be a ResearchInformationCollectionToolReadinessReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_surface("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_surface("payload", payload)
    return payload


def research_information_collection_tool_readiness_digest(
    report: ResearchInformationCollectionToolReadinessReport,
) -> ResearchInformationCollectionToolReadinessDigest:
    if type(report) is not ResearchInformationCollectionToolReadinessReport:
        raise ValueError(
            "report must be a ResearchInformationCollectionToolReadinessReport",
        )
    _require_hard_flags("report", report)
    return ResearchInformationCollectionToolReadinessDigest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        reason_codes=report.reason_codes,
        tool_task_count=report.tool_task_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        pass_ratio=report.pass_ratio,
        watch_ratio=report.watch_ratio,
        block_ratio=report.block_ratio,
        mean_readiness_score=report.mean_readiness_score,
        min_readiness_score=report.min_readiness_score,
        max_readiness_score=report.max_readiness_score,
        public_digest=report.public_digest,
    )


def research_information_collection_tool_readiness_digest_to_payload(
    digest: ResearchInformationCollectionToolReadinessDigest,
) -> dict[str, Any]:
    if type(digest) is not ResearchInformationCollectionToolReadinessDigest:
        raise ValueError(
            "digest must be a ResearchInformationCollectionToolReadinessDigest",
        )
    _require_hard_flags("digest", digest)
    _reject_unsafe_public_surface("digest", digest)
    payload = json_ready_no_floats(digest)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_surface("digest payload", payload)
    return payload


def _normalize_inputs(
    value: object,
) -> tuple[ResearchInformationCollectionToolReadinessInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    inputs = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for input_row in inputs:
        if type(input_row) is not ResearchInformationCollectionToolReadinessInput:
            raise ValueError(
                "inputs must contain ResearchInformationCollectionToolReadinessInput values",
            )
        _require_hard_flags("input", input_row)
        key = (input_row.tool_name, input_row.task_family)
        if key in seen_keys:
            raise ValueError("duplicate tool/task readiness inputs")
        seen_keys.add(key)
    return inputs


def _row_from_input(
    input_row: ResearchInformationCollectionToolReadinessInput,
    *,
    config: ResearchInformationCollectionToolReadinessConfig,
) -> ResearchInformationCollectionToolReadinessRow:
    readiness_score = _readiness_score(input_row)
    status = _row_status(input_row, readiness_score=readiness_score, config=config)
    return ResearchInformationCollectionToolReadinessRow(
        tool_name=input_row.tool_name,
        task_family=input_row.task_family,
        status=status,
        coverage_score=input_row.coverage_score,
        extraction_score=input_row.extraction_score,
        verification_score=input_row.verification_score,
        stability_score=input_row.stability_score,
        readiness_score=readiness_score,
        gap_count=input_row.gap_count,
        hard_gap_count=input_row.hard_gap_count,
        reason_codes=_row_reason_codes(
            input_row,
            status=status,
            readiness_score=readiness_score,
            config=config,
        ),
    )


def _row_status(
    input_row: ResearchInformationCollectionToolReadinessInput,
    *,
    readiness_score: Decimal,
    config: ResearchInformationCollectionToolReadinessConfig,
) -> str:
    if (
        input_row.hard_gap_count > ZERO
        or readiness_score < config.block_score_floor
        or _min_score(input_row) < config.block_score_floor
    ):
        return "block"
    if (
        input_row.gap_count > ZERO
        or readiness_score < config.pass_score_floor
        or _min_score(input_row) < config.pass_score_floor
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    input_row: ResearchInformationCollectionToolReadinessInput,
    *,
    status: str,
    readiness_score: Decimal,
    config: ResearchInformationCollectionToolReadinessConfig,
) -> tuple[str, ...]:
    if status == "pass":
        return (PASS_REASON,)
    codes: list[str] = []
    if status == "block":
        if input_row.hard_gap_count > ZERO:
            codes.append(BLOCK_HARD_GAP_REASON)
        if (
            readiness_score < config.block_score_floor
            or _min_score(input_row) < config.block_score_floor
        ):
            codes.append(BLOCK_SCORE_REASON)
        return tuple(codes) or (BLOCK_REASON,)
    if input_row.gap_count > ZERO:
        codes.append(WATCH_GAP_REASON)
    if (
        readiness_score < config.pass_score_floor
        or _min_score(input_row) < config.pass_score_floor
    ):
        codes.append(WATCH_SCORE_REASON)
    return tuple(codes) or (WATCH_REASON,)


def _report_status(
    rows: tuple[ResearchInformationCollectionToolReadinessRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchInformationCollectionToolReadinessRow, ...],
) -> tuple[str, ...]:
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append(BLOCK_REASON)
    if any(row.status == "watch" for row in rows):
        codes.append(WATCH_REASON)
    if not rows or any(row.status == "pass" for row in rows):
        codes.append(PASS_REASON)
    return tuple(codes)


def _readiness_score(
    input_row: ResearchInformationCollectionToolReadinessInput,
) -> Decimal:
    values = tuple(getattr(input_row, field_name) for field_name in SCORE_FIELD_NAMES)
    with localcontext(DECIMAL_CONTEXT):
        raw_score = sum(values, ZERO) / _count(len(values))
        penalty = (
            input_row.gap_count * SOFT_GAP_SCORE_PENALTY
            + input_row.hard_gap_count * HARD_GAP_SCORE_PENALTY
        )
        score = max(ZERO, raw_score - penalty)
        return score.quantize(SCORE_QUANTUM)


def _min_score(input_row: ResearchInformationCollectionToolReadinessInput) -> Decimal:
    return min(getattr(input_row, field_name) for field_name in SCORE_FIELD_NAMES)


def _normalize_rows(
    value: object,
) -> tuple[ResearchInformationCollectionToolReadinessRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchInformationCollectionToolReadinessRow:
            raise ValueError(
                "rows must contain ResearchInformationCollectionToolReadinessRow values",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(row: ResearchInformationCollectionToolReadinessRow) -> tuple[int, str, str]:
    return (STATUS_RANK[row.status], row.tool_name, row.task_family)


def _validate_row(row: ResearchInformationCollectionToolReadinessRow) -> None:
    if row.readiness_score != _readiness_score_from_scores(
        row.coverage_score,
        row.extraction_score,
        row.verification_score,
        row.stability_score,
        row.gap_count,
        row.hard_gap_count,
    ):
        raise ValueError("readiness_score must match component scores")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use the pass reason code")
    if row.status == "watch" and not any(
        reason_code in row.reason_codes
        for reason_code in (WATCH_REASON, WATCH_GAP_REASON, WATCH_SCORE_REASON)
    ):
        raise ValueError("watch rows require a watch reason code")
    if row.status == "block" and not any(
        reason_code in row.reason_codes
        for reason_code in (BLOCK_REASON, BLOCK_HARD_GAP_REASON, BLOCK_SCORE_REASON)
    ):
        raise ValueError("block rows require a block reason code")


def _validate_report(report: ResearchInformationCollectionToolReadinessReport) -> None:
    rows = tuple(sorted(report.rows, key=_row_sort_key))
    if report.rows != rows:
        raise ValueError("rows must be sorted deterministically")
    if report.tool_task_count != _count(len(rows)):
        raise ValueError("tool_task_count must match rows")
    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    block_count = _status_count(rows, "block")
    if report.pass_count != pass_count:
        raise ValueError("pass_count must match rows")
    if report.watch_count != watch_count:
        raise ValueError("watch_count must match rows")
    if report.block_count != block_count:
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.pass_ratio != _ratio(pass_count, report.tool_task_count):
        raise ValueError("pass_ratio must match rows")
    if report.watch_ratio != _ratio(watch_count, report.tool_task_count):
        raise ValueError("watch_ratio must match rows")
    if report.block_ratio != _ratio(block_count, report.tool_task_count):
        raise ValueError("block_ratio must match rows")
    scores = tuple(row.readiness_score for row in rows)
    if report.mean_readiness_score != _mean_decimal(scores):
        raise ValueError("mean_readiness_score must match rows")
    if report.min_readiness_score != _min_decimal(scores):
        raise ValueError("min_readiness_score must match rows")
    if report.max_readiness_score != _max_decimal(scores):
        raise ValueError("max_readiness_score must match rows")


def _readiness_score_from_scores(
    coverage_score: Decimal,
    extraction_score: Decimal,
    verification_score: Decimal,
    stability_score: Decimal,
    gap_count: Decimal,
    hard_gap_count: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        raw_score = (
            (
                coverage_score
                + extraction_score
                + verification_score
                + stability_score
            )
            / Decimal("4")
        )
        penalty = (
            gap_count * SOFT_GAP_SCORE_PENALTY
            + hard_gap_count * HARD_GAP_SCORE_PENALTY
        )
        return max(ZERO, raw_score - penalty).quantize(SCORE_QUANTUM)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative integer")
    return Decimal(value)


def _status_count(
    rows: tuple[ResearchInformationCollectionToolReadinessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _mean_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / _count(len(values))).quantize(SCORE_QUANTUM)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return min(values).quantize(SCORE_QUANTUM)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return max(values).quantize(SCORE_QUANTUM)


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_decimal(field_name, decimal_value, RATIO_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value.quantize(Decimal("1"))


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_decimal(field_name: str, value: Decimal, quantum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(quantum)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be quantizable") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    seen_codes: set[str] = set()
    for code in codes:
        _require_public_string(field_name, code)
        if code not in REASON_CODES:
            raise ValueError(f"{field_name} contains an unknown reason code")
        if code in seen_codes:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen_codes.add(code)
    return codes


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_public_digest(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)
    if getattr(value, "external_collection_allowed") is not False:
        raise ValueError(f"external_collection_allowed must be False for {label}")
    if getattr(value, "network_write_allowed") is not False:
        raise ValueError(f"network_write_allowed must be False for {label}")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload field must be a string")
            if _contains_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if _contains_unsafe_public_fragment(field.name):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_surface(label, getattr(value, field.name))
        return
    if type(value) is str and _contains_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public value in {label}")


def _contains_unsafe_public_fragment(value: str) -> bool:
    normalized = "".join(character for character in value.lower() if character.isalnum())
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _require_or_set_public_digest(
    report: ResearchInformationCollectionToolReadinessReport,
) -> None:
    derived_digest = _derived_public_digest(report)
    if report.public_digest:
        _require_public_digest("public_digest", report.public_digest)
        if report.public_digest != derived_digest:
            raise ValueError("public_digest does not match report payload")
        return
    object.__setattr__(report, "public_digest", derived_digest)


def _derived_public_digest(value: object) -> str:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest source must be a dataclass instance")
    ready = json_ready_no_floats(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest payload must be a dict")
    ready.pop("public_digest", None)
    _reject_unsafe_public_surface("digest payload", ready)
    canonical_payload = json.dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


__all__ = (
    "DEFAULT_RESEARCH_INFORMATION_COLLECTION_TOOL_READINESS_CONFIG_VERSION",
    "ResearchInformationCollectionToolReadinessConfig",
    "ResearchInformationCollectionToolReadinessDigest",
    "ResearchInformationCollectionToolReadinessInput",
    "ResearchInformationCollectionToolReadinessReport",
    "ResearchInformationCollectionToolReadinessRow",
    "build_research_information_collection_tool_readiness_report",
    "research_information_collection_tool_readiness_digest",
    "research_information_collection_tool_readiness_digest_to_payload",
    "research_information_collection_tool_readiness_report_to_payload",
)
