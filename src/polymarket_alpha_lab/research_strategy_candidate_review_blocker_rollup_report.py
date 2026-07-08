"""Pure candidate review blocker rollup report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_CANDIDATE_REVIEW_BLOCKER_ROLLUP_REPORT_CONFIG_VERSION = (
    "research-strategy-candidate-review-blocker-rollup-report-v0"
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_REVIEW_BLOCKER_ROLLUP_REPORT_CONFIG_VERSION",
    "ResearchStrategyCandidateReviewBlockerInput",
    "ResearchStrategyCandidateReviewBlockerReasonCodeCount",
    "ResearchStrategyCandidateReviewBlockerRollupConfig",
    "ResearchStrategyCandidateReviewBlockerRollupReport",
    "ResearchStrategyCandidateReviewBlockerRow",
    "build_research_strategy_candidate_review_blocker_rollup_report",
    "research_strategy_candidate_review_blocker_rollup_report_digest",
    "research_strategy_candidate_review_blocker_rollup_report_payload",
)


STATUSES = ("pass", "watch", "block")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_WEIGHT = Decimal("0.500000")
BLOCK_WEIGHT = Decimal("1.000000")
DIMENSION_COUNT = Decimal("6.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": ZERO,
}
NO_INPUTS_REASON = "review_blocker_rollup_no_inputs"
PASS_REASON = "review_blocker_rollup_pass"
DIMENSIONS = (
    ("evidence", "evidence_status"),
    ("source_coverage", "source_coverage_status"),
    ("cost_freshness", "cost_freshness_status"),
    ("settlement_clarity", "settlement_clarity_status"),
    ("domain_memory", "domain_memory_status"),
    ("forecast_rationale", "forecast_rationale_status"),
)
REPORT_REASON_PRIORITY = (
    "evidence_block",
    "evidence_watch",
    "source_coverage_block",
    "source_coverage_watch",
    "cost_freshness_block",
    "cost_freshness_watch",
    "settlement_clarity_block",
    "settlement_clarity_watch",
    "domain_memory_block",
    "domain_memory_watch",
    "forecast_rationale_block",
    "forecast_rationale_watch",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_TEXT_PARTS = (
    _join_parts("raw", "_candidate", "_id"),
    _join_parts("candidate", "_id"),
    _join_parts("mar", "ket", "_id"),
    _join_parts("mar", "ket", "_sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sou", "rce", "_u", "rl"),
    _join_parts("sou", "rce", "_te", "xt"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble", "_na", "me"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("tra", "ding"),
    _join_parts("b", "uy"),
    _join_parts("se", "ll"),
    _join_parts("rec", "ommend"),
    _join_parts("siz", "ing"),
    _join_parts("au", "th"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("req", "uest"),
    _join_parts("li", "ve"),
    "://",
    "?",
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
class ResearchStrategyCandidateReviewBlockerRollupConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CANDIDATE_REVIEW_BLOCKER_ROLLUP_REPORT_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCandidateReviewBlockerRollupConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CANDIDATE_REVIEW_BLOCKER_ROLLUP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateReviewBlockerInput(_FinalPublicDataclass):
    review_key: str
    evidence_status: str
    source_coverage_status: str
    cost_freshness_status: str
    settlement_clarity_status: str
    domain_memory_status: str
    forecast_rationale_status: str
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCandidateReviewBlockerInput,
            "input",
        )
        _require_canonical_string("review_key", self.review_key)
        for _, field_name in DIMENSIONS:
            _require_status(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateReviewBlockerRow(_FinalPublicDataclass):
    row_number: Decimal
    review_hash: str
    status: str
    evidence_status: str
    source_coverage_status: str
    cost_freshness_status: str
    settlement_clarity_status: str
    domain_memory_status: str
    forecast_rationale_status: str
    blocker_dimension_count: Decimal
    watch_dimension_count: Decimal
    blocker_pressure_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCandidateReviewBlockerRow, "row")
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        _require_public_digest("review_hash", self.review_hash)
        _require_status("status", self.status)
        statuses = _dimension_statuses(self)
        for field_name, value in zip((item[1] for item in DIMENSIONS), statuses):
            _require_status(field_name, value)
        object.__setattr__(
            self,
            "blocker_dimension_count",
            _normalize_nonnegative_decimal(
                "blocker_dimension_count",
                self.blocker_dimension_count,
            ),
        )
        object.__setattr__(
            self,
            "watch_dimension_count",
            _normalize_nonnegative_decimal(
                "watch_dimension_count",
                self.watch_dimension_count,
            ),
        )
        object.__setattr__(
            self,
            "blocker_pressure_score",
            _normalize_probability_decimal(
                "blocker_pressure_score",
                self.blocker_pressure_score,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _status_from_dimension_statuses(statuses):
            raise ValueError("status must match blocker statuses")
        if self.blocker_dimension_count != _dimension_status_count(statuses, "block"):
            raise ValueError("blocker_dimension_count must match blocker statuses")
        if self.watch_dimension_count != _dimension_status_count(statuses, "watch"):
            raise ValueError("watch_dimension_count must match blocker statuses")
        if self.blocker_pressure_score != _pressure_score(statuses):
            raise ValueError("blocker_pressure_score must match blocker statuses")
        if self.reason_codes != _reason_codes_from_dimension_statuses(statuses):
            raise ValueError("reason_codes must match blocker statuses")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateReviewBlockerReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCandidateReviewBlockerReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateReviewBlockerRollupReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    review_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    blocker_dimension_count: Decimal
    watch_dimension_count: Decimal
    attention_dimension_count: Decimal
    evidence_block_count: Decimal
    evidence_watch_count: Decimal
    source_coverage_block_count: Decimal
    source_coverage_watch_count: Decimal
    cost_freshness_block_count: Decimal
    cost_freshness_watch_count: Decimal
    settlement_clarity_block_count: Decimal
    settlement_clarity_watch_count: Decimal
    domain_memory_block_count: Decimal
    domain_memory_watch_count: Decimal
    forecast_rationale_block_count: Decimal
    forecast_rationale_watch_count: Decimal
    mean_blocker_pressure_score: Decimal
    max_blocker_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyCandidateReviewBlockerReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyCandidateReviewBlockerRow, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCandidateReviewBlockerRollupReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "review_count",
            "pass_count",
            "watch_count",
            "block_count",
            "blocker_dimension_count",
            "watch_dimension_count",
            "attention_dimension_count",
            "evidence_block_count",
            "evidence_watch_count",
            "source_coverage_block_count",
            "source_coverage_watch_count",
            "cost_freshness_block_count",
            "cost_freshness_watch_count",
            "settlement_clarity_block_count",
            "settlement_clarity_watch_count",
            "domain_memory_block_count",
            "domain_memory_watch_count",
            "forecast_rationale_block_count",
            "forecast_rationale_watch_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_blocker_pressure_score",
            "max_blocker_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest_or_empty("public_digest", self.public_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _computed_report_digest(self)
        if self.public_digest:
            if self.public_digest != expected_digest:
                raise ValueError("public_digest must match report payload")
        else:
            object.__setattr__(self, "public_digest", expected_digest)
        _reject_unsafe_public_payload("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchStrategyCandidateReviewBlockerInput,
    ResearchStrategyCandidateReviewBlockerReasonCodeCount,
    ResearchStrategyCandidateReviewBlockerRollupConfig,
    ResearchStrategyCandidateReviewBlockerRollupReport,
    ResearchStrategyCandidateReviewBlockerRow,
)


def build_research_strategy_candidate_review_blocker_rollup_report(
    inputs: Iterable[ResearchStrategyCandidateReviewBlockerInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyCandidateReviewBlockerRollupConfig | None = None,
) -> ResearchStrategyCandidateReviewBlockerRollupReport:
    if config is None:
        config = ResearchStrategyCandidateReviewBlockerRollupConfig()
    if type(config) is not ResearchStrategyCandidateReviewBlockerRollupConfig:
        raise ValueError(
            "config must be ResearchStrategyCandidateReviewBlockerRollupConfig",
        )
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_inputs(inputs)
    row_values = sorted(
        (_row_values_from_input(item) for item in items),
        key=_row_values_sort_key,
    )
    rows = tuple(
        _row_from_values(_count(index), values)
        for index, values in enumerate(row_values, start=1)
    )
    values = _report_values(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
    )
    return ResearchStrategyCandidateReviewBlockerRollupReport(
        **values,
        public_digest=_digest_from_mapping(values),
    )


def research_strategy_candidate_review_blocker_rollup_report_digest(
    report: ResearchStrategyCandidateReviewBlockerRollupReport,
) -> str:
    if type(report) is not ResearchStrategyCandidateReviewBlockerRollupReport:
        raise ValueError(
            "report must be ResearchStrategyCandidateReviewBlockerRollupReport",
        )
    _reject_unsafe_public_payload("report", report)
    _revalidate_report_for_payload(report)
    return _computed_report_digest(report)


def research_strategy_candidate_review_blocker_rollup_report_payload(
    report: ResearchStrategyCandidateReviewBlockerRollupReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyCandidateReviewBlockerRollupReport:
        raise ValueError(
            "report must be ResearchStrategyCandidateReviewBlockerRollupReport",
        )
    _reject_unsafe_public_payload("report", report)
    _revalidate_report_for_payload(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
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


@dataclass(frozen=True)
class _RowValues:
    review_hash: str
    status: str
    evidence_status: str
    source_coverage_status: str
    cost_freshness_status: str
    settlement_clarity_status: str
    domain_memory_status: str
    forecast_rationale_status: str
    blocker_dimension_count: Decimal
    watch_dimension_count: Decimal
    blocker_pressure_score: Decimal
    reason_codes: tuple[str, ...]


def _row_values_from_input(
    item: ResearchStrategyCandidateReviewBlockerInput,
) -> _RowValues:
    statuses = (
        item.evidence_status,
        item.source_coverage_status,
        item.cost_freshness_status,
        item.settlement_clarity_status,
        item.domain_memory_status,
        item.forecast_rationale_status,
    )
    return _RowValues(
        review_hash=_public_hash(item.review_key),
        status=_status_from_dimension_statuses(statuses),
        evidence_status=item.evidence_status,
        source_coverage_status=item.source_coverage_status,
        cost_freshness_status=item.cost_freshness_status,
        settlement_clarity_status=item.settlement_clarity_status,
        domain_memory_status=item.domain_memory_status,
        forecast_rationale_status=item.forecast_rationale_status,
        blocker_dimension_count=_dimension_status_count(statuses, "block"),
        watch_dimension_count=_dimension_status_count(statuses, "watch"),
        blocker_pressure_score=_pressure_score(statuses),
        reason_codes=_reason_codes_from_dimension_statuses(statuses),
    )


def _row_from_values(
    row_number: Decimal,
    values: _RowValues,
) -> ResearchStrategyCandidateReviewBlockerRow:
    return ResearchStrategyCandidateReviewBlockerRow(
        row_number=row_number,
        review_hash=values.review_hash,
        status=values.status,
        evidence_status=values.evidence_status,
        source_coverage_status=values.source_coverage_status,
        cost_freshness_status=values.cost_freshness_status,
        settlement_clarity_status=values.settlement_clarity_status,
        domain_memory_status=values.domain_memory_status,
        forecast_rationale_status=values.forecast_rationale_status,
        blocker_dimension_count=values.blocker_dimension_count,
        watch_dimension_count=values.watch_dimension_count,
        blocker_pressure_score=values.blocker_pressure_score,
        reason_codes=values.reason_codes,
    )


def _report_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchStrategyCandidateReviewBlockerRow, ...],
) -> dict[str, Any]:
    blocker_dimension_count = _sum_decimal(
        tuple(row.blocker_dimension_count for row in rows),
    )
    watch_dimension_count = _sum_decimal(
        tuple(row.watch_dimension_count for row in rows),
    )
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "review_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "blocker_dimension_count": blocker_dimension_count,
        "watch_dimension_count": watch_dimension_count,
        "attention_dimension_count": _quantize(
            blocker_dimension_count + watch_dimension_count,
        ),
        "evidence_block_count": _dimension_count(rows, "evidence_status", "block"),
        "evidence_watch_count": _dimension_count(rows, "evidence_status", "watch"),
        "source_coverage_block_count": _dimension_count(
            rows,
            "source_coverage_status",
            "block",
        ),
        "source_coverage_watch_count": _dimension_count(
            rows,
            "source_coverage_status",
            "watch",
        ),
        "cost_freshness_block_count": _dimension_count(
            rows,
            "cost_freshness_status",
            "block",
        ),
        "cost_freshness_watch_count": _dimension_count(
            rows,
            "cost_freshness_status",
            "watch",
        ),
        "settlement_clarity_block_count": _dimension_count(
            rows,
            "settlement_clarity_status",
            "block",
        ),
        "settlement_clarity_watch_count": _dimension_count(
            rows,
            "settlement_clarity_status",
            "watch",
        ),
        "domain_memory_block_count": _dimension_count(
            rows,
            "domain_memory_status",
            "block",
        ),
        "domain_memory_watch_count": _dimension_count(
            rows,
            "domain_memory_status",
            "watch",
        ),
        "forecast_rationale_block_count": _dimension_count(
            rows,
            "forecast_rationale_status",
            "block",
        ),
        "forecast_rationale_watch_count": _dimension_count(
            rows,
            "forecast_rationale_status",
            "watch",
        ),
        "mean_blocker_pressure_score": _mean(
            tuple(row.blocker_pressure_score for row in rows),
        ),
        "max_blocker_pressure_score": _max_decimal(
            tuple(row.blocker_pressure_score for row in rows),
        ),
        "status": _rollup_status(tuple(row.status for row in rows)),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_inputs(
    value: Iterable[ResearchStrategyCandidateReviewBlockerInput],
) -> tuple[ResearchStrategyCandidateReviewBlockerInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyCandidateReviewBlockerInput:
            raise ValueError(
                "inputs must contain ResearchStrategyCandidateReviewBlockerInput values",
            )
        _require_hard_flags("input", row)
        _reject_unsafe_public_payload("input", row)
        if row.review_key in seen_keys:
            raise ValueError("inputs must not contain duplicate review_key values")
        seen_keys.add(row.review_key)
    return rows


def _normalize_rows(
    value: Iterable[ResearchStrategyCandidateReviewBlockerRow],
) -> tuple[ResearchStrategyCandidateReviewBlockerRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_hashes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyCandidateReviewBlockerRow:
            raise ValueError(
                "rows must contain ResearchStrategyCandidateReviewBlockerRow values",
            )
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
        if row.review_hash in seen_hashes:
            raise ValueError("rows must not contain duplicate review_hash values")
        seen_hashes.add(row.review_hash)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[ResearchStrategyCandidateReviewBlockerReasonCodeCount],
) -> tuple[ResearchStrategyCandidateReviewBlockerReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyCandidateReviewBlockerReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyCandidateReviewBlockerReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code")
        seen_codes.add(row.reason_code)
    expected = tuple(sorted(rows, key=lambda item: (-item.count, item.reason_code)))
    if rows != expected:
        raise ValueError("reason_code_counts must use canonical sequence")
    return rows


def _row_values_sort_key(values: _RowValues) -> tuple[Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[values.status],
        -values.blocker_pressure_score,
        values.review_hash,
    )


def _row_sort_key(
    row: ResearchStrategyCandidateReviewBlockerRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.blocker_pressure_score,
        row.review_hash,
    )


def _status_count(
    rows: tuple[ResearchStrategyCandidateReviewBlockerRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _dimension_count(
    rows: tuple[ResearchStrategyCandidateReviewBlockerRow, ...],
    field_name: str,
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if getattr(row, field_name) == status))


def _dimension_status_count(statuses: tuple[str, ...], status: str) -> Decimal:
    return _count(sum(1 for value in statuses if value == status))


def _dimension_statuses(value: object) -> tuple[str, ...]:
    return tuple(str(getattr(value, field_name)) for _, field_name in DIMENSIONS)


def _status_from_dimension_statuses(statuses: tuple[str, ...]) -> str:
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _pressure_score(statuses: tuple[str, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = sum(
            (
                BLOCK_WEIGHT
                if status == "block"
                else WATCH_WEIGHT
                if status == "watch"
                else ZERO
            )
            for status in statuses
        )
        return _quantize(score / DIMENSION_COUNT)


def _reason_codes_from_dimension_statuses(statuses: tuple[str, ...]) -> tuple[str, ...]:
    reason_codes = [
        f"{prefix}_{status}"
        for (prefix, _), status in zip(DIMENSIONS, statuses)
        if status in ("watch", "block")
    ]
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(sorted(reason_codes)))


def _report_reason_codes(
    rows: tuple[ResearchStrategyCandidateReviewBlockerRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.status for row in rows))
    row_codes = frozenset(code for row in rows for code in row.reason_codes)
    return (
        f"review_blocker_rollup_{status}",
        *tuple(code for code in REPORT_REASON_PRIORITY if code in row_codes),
    )


def _reason_code_counts(
    rows: tuple[ResearchStrategyCandidateReviewBlockerRow, ...],
) -> tuple[ResearchStrategyCandidateReviewBlockerReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyCandidateReviewBlockerReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyCandidateReviewBlockerReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _validate_report(report: ResearchStrategyCandidateReviewBlockerRollupReport) -> None:
    rows = report.rows
    expected_values = _report_values(
        generated_at=report.generated_at,
        config_version=report.config_version,
        rows=rows,
    )
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    for index, row in enumerate(rows, start=1):
        if row.row_number != _count(index):
            raise ValueError("row_number must match rows")


def _revalidate_report_for_payload(
    report: ResearchStrategyCandidateReviewBlockerRollupReport,
) -> None:
    _require_exact_type(
        report,
        ResearchStrategyCandidateReviewBlockerRollupReport,
        "report",
    )
    _require_utc_datetime("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    for field_name in (
        "review_count",
        "pass_count",
        "watch_count",
        "block_count",
        "blocker_dimension_count",
        "watch_dimension_count",
        "attention_dimension_count",
        "evidence_block_count",
        "evidence_watch_count",
        "source_coverage_block_count",
        "source_coverage_watch_count",
        "cost_freshness_block_count",
        "cost_freshness_watch_count",
        "settlement_clarity_block_count",
        "settlement_clarity_watch_count",
        "domain_memory_block_count",
        "domain_memory_watch_count",
        "forecast_rationale_block_count",
        "forecast_rationale_watch_count",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(report, field_name))
    for field_name in (
        "mean_blocker_pressure_score",
        "max_blocker_pressure_score",
    ):
        _require_probability_six_decimal_decimal(field_name, getattr(report, field_name))
    _require_status("status", report.status)
    _normalize_report_reason_codes(report.reason_codes)
    if type(report.reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in report.reason_code_counts:
        _revalidate_reason_code_count_for_payload(row)
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in report.rows:
        _revalidate_row_for_payload(row)
    _require_public_digest("public_digest", report.public_digest)
    _require_hard_flags("report", report)
    _validate_report(report)
    if report.public_digest != _computed_report_digest(report):
        raise ValueError("public_digest must match report payload")


def _revalidate_row_for_payload(row: object) -> None:
    if type(row) is not ResearchStrategyCandidateReviewBlockerRow:
        raise ValueError("rows must contain ResearchStrategyCandidateReviewBlockerRow")
    _require_positive_six_decimal_decimal("row_number", row.row_number)
    _require_public_digest("review_hash", row.review_hash)
    _require_status("status", row.status)
    statuses = _dimension_statuses(row)
    for field_name, status in zip((item[1] for item in DIMENSIONS), statuses):
        _require_status(field_name, status)
    _require_nonnegative_six_decimal_decimal(
        "blocker_dimension_count",
        row.blocker_dimension_count,
    )
    _require_nonnegative_six_decimal_decimal(
        "watch_dimension_count",
        row.watch_dimension_count,
    )
    _require_probability_six_decimal_decimal(
        "blocker_pressure_score",
        row.blocker_pressure_score,
    )
    _normalize_reason_codes("reason_codes", row.reason_codes)
    if row.status != _status_from_dimension_statuses(statuses):
        raise ValueError("status must match blocker statuses")
    if row.blocker_dimension_count != _dimension_status_count(statuses, "block"):
        raise ValueError("blocker_dimension_count must match blocker statuses")
    if row.watch_dimension_count != _dimension_status_count(statuses, "watch"):
        raise ValueError("watch_dimension_count must match blocker statuses")
    if row.blocker_pressure_score != _pressure_score(statuses):
        raise ValueError("blocker_pressure_score must match blocker statuses")
    if row.reason_codes != _reason_codes_from_dimension_statuses(statuses):
        raise ValueError("reason_codes must match blocker statuses")
    _require_hard_flags("row", row)


def _revalidate_reason_code_count_for_payload(row: object) -> None:
    if type(row) is not ResearchStrategyCandidateReviewBlockerReasonCodeCount:
        raise ValueError(
            "reason_code_counts must contain ResearchStrategyCandidateReviewBlockerReasonCodeCount",
        )
    _require_canonical_string("reason_code", row.reason_code)
    _require_positive_six_decimal_decimal("count", row.count)
    _require_hard_flags("reason_code_count", row)


def _computed_report_digest(
    report: ResearchStrategyCandidateReviewBlockerRollupReport,
) -> str:
    values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "public_digest"
    }
    return _digest_from_mapping(values)


def _digest_from_mapping(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    return sha256(
        json.dumps(
            ready,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8"),
    ).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("payload contains unknown dataclass")
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return str(value)
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if value is None or type(value) in (bool, str):
        if type(value) is str:
            _require_canonical_string("JSON string value", value)
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_canonical_string("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (int, float) or isinstance(value, (list, set)):
        raise ValueError("value must use public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unknown dataclass")
        for field in fields(value):
            _reject_unsafe_text(field.name, field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)
        return
    if type(value) in (Decimal, datetime) or value is None or type(value) is bool:
        return
    if type(value) in (tuple, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_text(key, key)
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if type(value) in (int, float) or isinstance(value, set):
        raise ValueError(f"{label} must use public dataclass fields")
    raise ValueError(f"{label} has unknown value")


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(part in lowered for part in _UNSAFE_TEXT_PARTS):
        raise ValueError(f"{label} contains unsafe public value")


def _normalize_reason_codes(
    label: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    _require_reason_codes_tuple(label, values)
    if not allow_empty and not values:
        raise ValueError(f"{label} must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_canonical_string(label, value)
        if value in seen:
            raise ValueError(f"{label} must not contain duplicates")
        seen.add(value)
    normalized = tuple(sorted(values))
    if values != normalized:
        raise ValueError(f"{label} must use canonical sequence")
    return normalized


def _normalize_report_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    _require_reason_codes_tuple("reason_codes", values)
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_canonical_string("reason_codes", value)
        if value in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(value)
    return values


def _require_reason_codes_tuple(label: str, values: object) -> None:
    if type(values) is not tuple:
        raise ValueError(f"{label} must be a tuple")
    for value in values:
        if type(value) is not str:
            raise ValueError(f"{label} must contain strings")


def _require_canonical_string(label: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{label} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{label} must be canonical")
    _reject_unsafe_text(label, value)


def _require_status(label: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{label} must be pass, watch, or block")


def _require_public_digest(label: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{label} must be a lowercase hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be a lowercase hex digest")


def _require_digest_or_empty(label: str, value: object) -> None:
    if value == "":
        return
    _require_public_digest(label, value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _as_utc(label: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(label: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be exactly datetime")
    if value.tzinfo is not UTC or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{label} must be UTC")


def _normalize_decimal(label: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(label: str, value: object) -> Decimal:
    normalized = _normalize_decimal(label, value)
    if normalized < ZERO:
        raise ValueError(f"{label} must be nonnegative")
    return normalized


def _normalize_positive_count(label: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(label, value)
    if normalized <= ZERO:
        raise ValueError(f"{label} must be positive")
    return normalized


def _normalize_probability_decimal(label: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(label, value)
    if normalized > ONE:
        raise ValueError(f"{label} must be between 0 and 1")
    return normalized


def _require_six_decimal_decimal(label: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    if value != _quantize(value):
        raise ValueError(f"{label} must use six decimal places")


def _require_nonnegative_six_decimal_decimal(label: str, value: object) -> None:
    _require_six_decimal_decimal(label, value)
    if value < ZERO:
        raise ValueError(f"{label} must be nonnegative")


def _require_positive_six_decimal_decimal(label: str, value: object) -> None:
    _require_nonnegative_six_decimal_decimal(label, value)
    if value <= ZERO:
        raise ValueError(f"{label} must be positive")


def _require_probability_six_decimal_decimal(label: str, value: object) -> None:
    _require_nonnegative_six_decimal_decimal(label, value)
    if value > ONE:
        raise ValueError(f"{label} must be between 0 and 1")


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _public_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()
