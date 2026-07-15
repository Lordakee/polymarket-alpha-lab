"""Pure report-only source memory decay scoring for strategy research."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, final


__all__ = (
    "ResearchStrategySpecialistSourceMemoryDecayConfig",
    "ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount",
    "ResearchStrategySpecialistSourceMemoryDecayReport",
    "ResearchStrategySpecialistSourceMemoryDecayRow",
    "ResearchStrategySpecialistSourceMemoryObservation",
    "build_research_strategy_specialist_source_memory_decay_report",
    "research_strategy_specialist_source_memory_decay_report_digest",
    "research_strategy_specialist_source_memory_decay_report_payload",
    "validate_research_strategy_specialist_source_memory_decay_report_digest",
    "validate_research_strategy_specialist_source_memory_decay_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-strategy-specialist-source-memory-decay-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
RATIO_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_CANONICAL_RE = re.compile(r"[a-z0-9][a-z0-9_.:-]*")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class _Missing:
    pass


_MISSING = _Missing()


class _FinalPublicDataclass:
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(base, _FinalPublicDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySpecialistSourceMemoryDecayConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_memory_age_seconds: Decimal = Decimal("3600")
    stale_memory_age_seconds: Decimal = Decimal("86400")
    watch_decay_score: Decimal = Decimal("0.300000")
    block_decay_score: Decimal = Decimal("0.650000")
    recency_weight: Decimal = Decimal("0.650000")
    recall_weight: Decimal = Decimal("0.350000")
    contradiction_penalty: Decimal = Decimal("0.200000")
    min_recall_reliability_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategySpecialistSourceMemoryDecayConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySpecialistSourceMemoryDecayConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fresh_memory_age_seconds", "stale_memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_memory_age_seconds <= self.fresh_memory_age_seconds:
            raise ValueError(
                "stale_memory_age_seconds must exceed fresh_memory_age_seconds",
            )
        for field_name in (
            "watch_decay_score",
            "block_decay_score",
            "recency_weight",
            "recall_weight",
            "contradiction_penalty",
            "min_recall_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_decay_score >= self.block_decay_score:
            raise ValueError("watch_decay_score must be less than block_decay_score")
        with localcontext(DECIMAL_CONTEXT):
            weight_sum = _quantize(self.recency_weight + self.recall_weight)
        if weight_sum != ONE:
            raise ValueError("recency_weight and recall_weight must sum to 1")
        _require_hard_flags("config", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySpecialistSourceMemoryObservation(_FinalPublicDataclass):
    source_memory_id: str
    candidate_id: str
    market_id: str | None = None
    market_slug: str | None = None
    market_question: str | None = None
    source_url: str | None = None
    source_text: str | None = None
    memory_observed_at: datetime = datetime(1970, 1, 1, tzinfo=UTC)
    last_recalled_at: datetime | None = None
    successful_recall_count: Decimal = ZERO
    failed_recall_count: Decimal = ZERO
    contradiction_count: Decimal = ZERO
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategySpecialistSourceMemoryObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySpecialistSourceMemoryObservation,
            "observation",
        )
        _require_canonical_string("source_memory_id", self.source_memory_id)
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in (
            "market_id",
            "market_slug",
            "market_question",
            "source_url",
            "source_text",
        ):
            _require_optional_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "memory_observed_at",
            _as_utc("memory_observed_at", self.memory_observed_at),
        )
        object.__setattr__(
            self,
            "last_recalled_at",
            _optional_as_utc("last_recalled_at", self.last_recalled_at),
        )
        for field_name in (
            "successful_recall_count",
            "failed_recall_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySpecialistSourceMemoryDecayRow(_FinalPublicDataclass):
    memory_alias: str
    last_memory_touch_at: datetime
    memory_age_seconds: Decimal
    successful_recall_count: Decimal
    failed_recall_count: Decimal
    contradiction_count: Decimal
    recall_observation_count: Decimal
    recency_retention_score: Decimal
    recall_reliability_score: Decimal
    contradiction_penalty_score: Decimal
    memory_retention_score: Decimal
    decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategySpecialistSourceMemoryDecayRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySpecialistSourceMemoryDecayRow,
            "row",
        )
        _require_canonical_string("memory_alias", self.memory_alias)
        object.__setattr__(
            self,
            "last_memory_touch_at",
            _as_utc("last_memory_touch_at", self.last_memory_touch_at),
        )
        for field_name in (
            "memory_age_seconds",
            "successful_recall_count",
            "failed_recall_count",
            "contradiction_count",
            "recall_observation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recency_retention_score",
            "recall_reliability_score",
            "contradiction_penalty_score",
            "memory_retention_score",
            "decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySpecialistSourceMemoryDecayReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    config: ResearchStrategySpecialistSourceMemoryDecayConfig
    memory_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_decay_score: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount, ...]
    rows: tuple[ResearchStrategySpecialistSourceMemoryDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategySpecialistSourceMemoryDecayReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySpecialistSourceMemoryDecayReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_exact_type(
            self.config,
            ResearchStrategySpecialistSourceMemoryDecayConfig,
            "config",
        )
        _require_hard_flags("config", self.config)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in ("memory_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_decay_score",
            _require_optional_probability_decimal(
                "average_decay_score",
                self.average_decay_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _payload_digest(_report_payload(self, include_digest=False))
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_strategy_specialist_source_memory_decay_report(
    observations: Iterable[object],
    *,
    config: ResearchStrategySpecialistSourceMemoryDecayConfig,
    generated_at: datetime,
) -> ResearchStrategySpecialistSourceMemoryDecayReport:
    config = _revalidate_config(config)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        _reject_future_times(item, generated_at_utc)
    rows = tuple(
        _row_from_observation(
            item,
            alias=f"memory-{index:03d}",
            config=config,
            generated_at=generated_at_utc,
        )
        for index, item in enumerate(
            sorted(normalized, key=lambda value: (value.source_memory_id, value.candidate_id)),
            start=1,
        )
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchStrategySpecialistSourceMemoryDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        config=config,
        memory_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_decay_score=_average_decay_score(rows),
        status=_summary_status(reason_codes),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        rows=rows,
    )


def research_strategy_specialist_source_memory_decay_report_payload(
    report: ResearchStrategySpecialistSourceMemoryDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategySpecialistSourceMemoryDecayReport:
        _revalidate_report(report)
        payload = _report_payload(report, include_digest=True)
    elif type(report) is dict:
        validate_research_strategy_specialist_source_memory_decay_report_payload(report)
        payload = report
    else:
        raise ValueError(
            "report must be a ResearchStrategySpecialistSourceMemoryDecayReport",
        )
    validate_research_strategy_specialist_source_memory_decay_report_payload(payload)
    return payload


def research_strategy_specialist_source_memory_decay_report_digest(
    report: ResearchStrategySpecialistSourceMemoryDecayReport,
) -> str:
    if type(report) is not ResearchStrategySpecialistSourceMemoryDecayReport:
        raise ValueError(
            "report must be a ResearchStrategySpecialistSourceMemoryDecayReport",
        )
    _revalidate_report(report)
    return report.derived_validation_digest


def validate_research_strategy_specialist_source_memory_decay_report_digest(
    report: ResearchStrategySpecialistSourceMemoryDecayReport,
    expected_digest: str,
) -> str:
    if type(expected_digest) is not str or _SHA256_RE.fullmatch(expected_digest) is None:
        raise ValueError("expected_digest must be a sha256 hex digest")
    actual_digest = research_strategy_specialist_source_memory_decay_report_digest(report)
    if actual_digest != expected_digest:
        raise ValueError("digest validation failed")
    return actual_digest


def validate_research_strategy_specialist_source_memory_decay_report_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _validate_public_payload_schema(payload)
    report = _report_from_public_payload(payload)
    canonical_payload = _report_payload(report, include_digest=True)
    if payload != canonical_payload:
        raise ValueError("public payload must use canonical schema values")


def _row_from_observation(
    observation: ResearchStrategySpecialistSourceMemoryObservation,
    *,
    alias: str,
    config: ResearchStrategySpecialistSourceMemoryDecayConfig,
    generated_at: datetime,
) -> ResearchStrategySpecialistSourceMemoryDecayRow:
    last_touch = _last_memory_touch_at(observation)
    age_seconds = _age_seconds(generated_at, last_touch)
    with localcontext(DECIMAL_CONTEXT):
        recall_observation_count = (
            observation.successful_recall_count + observation.failed_recall_count
        )
    recency_retention_score = _recency_retention_score(age_seconds, config=config)
    recall_reliability_score = _recall_reliability_score(
        observation.successful_recall_count,
        recall_observation_count,
    )
    with localcontext(DECIMAL_CONTEXT):
        contradiction_penalty_score = _quantize(
            min(ONE, observation.contradiction_count * config.contradiction_penalty),
        )
    memory_retention_score = _memory_retention_score(
        recency_retention_score=recency_retention_score,
        recall_reliability_score=recall_reliability_score,
        contradiction_penalty_score=contradiction_penalty_score,
        config=config,
    )
    with localcontext(DECIMAL_CONTEXT):
        decay_score = _quantize(ONE - memory_retention_score)
    status = _row_status(
        decay_score=decay_score,
        recall_reliability_score=recall_reliability_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        age_seconds=age_seconds,
        recall_reliability_score=recall_reliability_score,
        contradiction_count=observation.contradiction_count,
        input_reason_codes=observation.reason_codes,
        config=config,
    )
    return ResearchStrategySpecialistSourceMemoryDecayRow(
        memory_alias=alias,
        last_memory_touch_at=last_touch,
        memory_age_seconds=age_seconds,
        successful_recall_count=observation.successful_recall_count,
        failed_recall_count=observation.failed_recall_count,
        contradiction_count=observation.contradiction_count,
        recall_observation_count=recall_observation_count,
        recency_retention_score=recency_retention_score,
        recall_reliability_score=recall_reliability_score,
        contradiction_penalty_score=contradiction_penalty_score,
        memory_retention_score=memory_retention_score,
        decay_score=decay_score,
        status=status,
        reason_codes=reason_codes,
    )


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchStrategySpecialistSourceMemoryObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized = tuple(_coerce_observation(value) for value in values)
    seen: set[tuple[str, str]] = set()
    for value in normalized:
        key = (value.source_memory_id, value.candidate_id)
        if key in seen:
            raise ValueError("observations must not contain duplicate memory keys")
        seen.add(key)
    return normalized


def _coerce_observation(
    value: object,
) -> ResearchStrategySpecialistSourceMemoryObservation:
    if type(value) is ResearchStrategySpecialistSourceMemoryObservation:
        _require_hard_flags("observation", value)
        return _revalidate_observation(value)
    raise ValueError(
        "observations must contain ResearchStrategySpecialistSourceMemoryObservation values",
    )


def _revalidate_config(
    config: ResearchStrategySpecialistSourceMemoryDecayConfig,
) -> ResearchStrategySpecialistSourceMemoryDecayConfig:
    if type(config) is not ResearchStrategySpecialistSourceMemoryDecayConfig:
        raise ValueError(
            "config must be a ResearchStrategySpecialistSourceMemoryDecayConfig",
        )
    values = {field.name: getattr(config, field.name) for field in fields(config)}
    return ResearchStrategySpecialistSourceMemoryDecayConfig(**values)


def _revalidate_observation(
    observation: ResearchStrategySpecialistSourceMemoryObservation,
) -> ResearchStrategySpecialistSourceMemoryObservation:
    values = {field.name: getattr(observation, field.name) for field in fields(observation)}
    return ResearchStrategySpecialistSourceMemoryObservation(**values)


def _last_memory_touch_at(
    observation: ResearchStrategySpecialistSourceMemoryObservation,
) -> datetime:
    if observation.last_recalled_at is None:
        return observation.memory_observed_at
    return max(observation.memory_observed_at, observation.last_recalled_at)


def _recency_retention_score(
    age_seconds: Decimal,
    *,
    config: ResearchStrategySpecialistSourceMemoryDecayConfig,
) -> Decimal:
    if age_seconds <= config.fresh_memory_age_seconds:
        return _quantize(ONE)
    if age_seconds >= config.stale_memory_age_seconds:
        return _quantize(ZERO)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(ONE - (age_seconds / config.stale_memory_age_seconds))


def _recall_reliability_score(
    successful_recall_count: Decimal,
    recall_observation_count: Decimal,
) -> Decimal:
    if recall_observation_count == ZERO:
        return _quantize(ZERO)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(successful_recall_count / recall_observation_count)


def _memory_retention_score(
    *,
    recency_retention_score: Decimal,
    recall_reliability_score: Decimal,
    contradiction_penalty_score: Decimal,
    config: ResearchStrategySpecialistSourceMemoryDecayConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        raw_score = (
            (recency_retention_score * config.recency_weight)
            + (recall_reliability_score * config.recall_weight)
            - contradiction_penalty_score
        )
        return _quantize(max(ZERO, min(ONE, raw_score)))


def _row_status(
    *,
    decay_score: Decimal,
    recall_reliability_score: Decimal,
    config: ResearchStrategySpecialistSourceMemoryDecayConfig,
) -> str:
    if decay_score >= config.block_decay_score:
        return "block"
    if decay_score >= config.watch_decay_score:
        return "watch"
    if recall_reliability_score < config.min_recall_reliability_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    age_seconds: Decimal,
    recall_reliability_score: Decimal,
    contradiction_count: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchStrategySpecialistSourceMemoryDecayConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"source_memory_decay_{status}"}
    if age_seconds <= config.fresh_memory_age_seconds:
        reason_codes.add("fresh_source_memory")
    elif age_seconds >= config.stale_memory_age_seconds:
        reason_codes.add("stale_source_memory")
    else:
        reason_codes.add("aging_source_memory")
    if recall_reliability_score >= config.min_recall_reliability_score:
        reason_codes.add("recall_reliability_pass")
    else:
        reason_codes.add("recall_reliability_weak")
    if contradiction_count > ZERO:
        reason_codes.add("contradictions_present")
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _summary_reason_codes(
    rows: tuple[ResearchStrategySpecialistSourceMemoryDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_source_memory_observations",)
    if all(row.status == "pass" for row in rows):
        return ("source_memory_decay_pass",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_source_memory_observations",):
        return "block"
    if "source_memory_decay_block" in reason_codes:
        return "block"
    if "source_memory_decay_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchStrategySpecialistSourceMemoryDecayRow, ...],
) -> tuple[ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_decay_score(
    rows: tuple[ResearchStrategySpecialistSourceMemoryDecayRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum((row.decay_score for row in rows), ZERO) / Decimal(len(rows)))


def _status_count(
    rows: tuple[ResearchStrategySpecialistSourceMemoryDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchStrategySpecialistSourceMemoryDecayRow, ...],
) -> tuple[ResearchStrategySpecialistSourceMemoryDecayRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategySpecialistSourceMemoryDecayRow:
            raise ValueError(
                "rows must contain ResearchStrategySpecialistSourceMemoryDecayRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.memory_alias))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by memory_alias")
    if len({row.memory_alias for row in rows}) != len(rows):
        raise ValueError("rows must not contain duplicate memory_alias values")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount, ...],
) -> tuple[ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    if len({count.reason_code for count in counts}) != len(counts):
        raise ValueError("reason_code_counts must not contain duplicates")
    return counts


def _validate_row_consistency(
    row: ResearchStrategySpecialistSourceMemoryDecayRow,
    config: ResearchStrategySpecialistSourceMemoryDecayConfig | None = None,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        expected_recall_observation_count = (
            row.successful_recall_count + row.failed_recall_count
        )
    if row.recall_observation_count != expected_recall_observation_count:
        raise ValueError("recall_observation_count must match recall counts")
    with localcontext(DECIMAL_CONTEXT):
        expected_decay_score = _quantize(ONE - row.memory_retention_score)
    if row.decay_score != expected_decay_score:
        raise ValueError("decay_score must match memory_retention_score")
    if config is not None:
        expected_status = _row_status(
            decay_score=row.decay_score,
            recall_reliability_score=row.recall_reliability_score,
            config=config,
        )
        if row.status != expected_status:
            raise ValueError("status must match derived scores and config")
        input_reason_codes = tuple(
            reason_code.removeprefix("input_")
            for reason_code in row.reason_codes
            if reason_code.startswith("input_")
        )
        expected_reason_codes = _row_reason_codes(
            status=expected_status,
            age_seconds=row.memory_age_seconds,
            recall_reliability_score=row.recall_reliability_score,
            contradiction_count=row.contradiction_count,
            input_reason_codes=input_reason_codes,
            config=config,
        )
        if row.reason_codes != expected_reason_codes:
            raise ValueError("reason_codes must match derived row values")


def _validate_report_consistency(
    report: ResearchStrategySpecialistSourceMemoryDecayReport,
) -> None:
    config = report.config
    _require_exact_type(config, ResearchStrategySpecialistSourceMemoryDecayConfig, "config")
    _require_hard_flags("config", config)
    if report.config_version != config.config_version:
        raise ValueError("config_version must match config")
    if report.memory_count != _decimal_count(len(report.rows)):
        raise ValueError("memory_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_decay_score != _average_decay_score(report.rows):
        raise ValueError("average_decay_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    for row in report.rows:
        if row.last_memory_touch_at > report.generated_at:
            raise ValueError("last_memory_touch_at must not be after generated_at")
        expected_age = _age_seconds(report.generated_at, row.last_memory_touch_at)
        if row.memory_age_seconds != expected_age:
            raise ValueError("memory_age_seconds must match generated_at")
        expected_recency = _recency_retention_score(row.memory_age_seconds, config=config)
        if row.recency_retention_score != expected_recency:
            raise ValueError("recency_retention_score must match config")
        expected_reliability = _recall_reliability_score(
            row.successful_recall_count,
            row.recall_observation_count,
        )
        if row.recall_reliability_score != expected_reliability:
            raise ValueError("recall_reliability_score must match recall counts")
        with localcontext(DECIMAL_CONTEXT):
            expected_contradiction = _quantize(
                min(ONE, row.contradiction_count * config.contradiction_penalty),
            )
        if row.contradiction_penalty_score != expected_contradiction:
            raise ValueError("contradiction_penalty_score must match config")
        expected_retention = _memory_retention_score(
            recency_retention_score=expected_recency,
            recall_reliability_score=expected_reliability,
            contradiction_penalty_score=expected_contradiction,
            config=config,
        )
        if row.memory_retention_score != expected_retention:
            raise ValueError("memory_retention_score must match config")
        _validate_row_consistency(row, config)


def _reject_future_times(
    item: ResearchStrategySpecialistSourceMemoryObservation,
    generated_at: datetime,
) -> None:
    if item.memory_observed_at > generated_at:
        raise ValueError("memory_observed_at must not be after generated_at")
    if item.last_recalled_at is not None and item.last_recalled_at > generated_at:
        raise ValueError("last_recalled_at must not be after generated_at")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _revalidate_report(
    report: ResearchStrategySpecialistSourceMemoryDecayReport,
) -> None:
    if type(report) is not ResearchStrategySpecialistSourceMemoryDecayReport:
        raise ValueError(
            "report must be a ResearchStrategySpecialistSourceMemoryDecayReport",
        )
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    ResearchStrategySpecialistSourceMemoryDecayReport(**values)


def _report_payload(
    report: ResearchStrategySpecialistSourceMemoryDecayReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in fields(report):
        if field.name == "derived_validation_digest" and not include_digest:
            continue
        payload[field.name] = _payload_value(getattr(report, field.name))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    return payload


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        if not value.is_finite() or (value.is_zero() and value.is_signed()):
            raise ValueError("payload Decimal values must be finite and not signed zero")
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise ValueError("payload object keys must be strings")
        return {key: _payload_value(value[key]) for key in value}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload values must use JSON-safe exact types")


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_exact_fields(
        "payload",
        payload,
        tuple(field.name for field in fields(ResearchStrategySpecialistSourceMemoryDecayReport)),
    )
    _require_hard_flags("payload", _PayloadFlags(payload))
    _payload_string("payload.config_version", payload["config_version"])
    config_payload = _require_payload_object("payload.config", payload["config"])
    _require_exact_fields(
        "payload.config",
        config_payload,
        tuple(field.name for field in fields(ResearchStrategySpecialistSourceMemoryDecayConfig)),
    )
    _require_hard_flags("payload.config", _PayloadFlags(config_payload))
    rows = _require_payload_list("payload.rows", payload["rows"])
    reason_counts = _require_payload_list(
        "payload.reason_code_counts",
        payload["reason_code_counts"],
    )
    for index, row in enumerate(rows):
        row_object = _require_payload_object(f"payload.rows[{index}]", row)
        _require_exact_fields(
            f"payload.rows[{index}]",
            row_object,
            tuple(field.name for field in fields(ResearchStrategySpecialistSourceMemoryDecayRow)),
        )
        _require_hard_flags(f"payload.rows[{index}]", _PayloadFlags(row_object))
    for index, reason_count in enumerate(reason_counts):
        count_object = _require_payload_object(
            f"payload.reason_code_counts[{index}]",
            reason_count,
        )
        _require_exact_fields(
            f"payload.reason_code_counts[{index}]",
            count_object,
            tuple(
                field.name
                for field in fields(ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount)
            ),
        )
        _require_hard_flags(
            f"payload.reason_code_counts[{index}]",
            _PayloadFlags(count_object),
        )
    _reject_unsafe_public_payload(payload)


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategySpecialistSourceMemoryDecayReport:
    config_payload = payload["config"]
    if type(config_payload) is not dict:
        raise ValueError("payload.config must be a JSON object")
    config = ResearchStrategySpecialistSourceMemoryDecayConfig(
        **{
            field.name: _payload_config_value(field.name, config_payload[field.name])
            for field in fields(ResearchStrategySpecialistSourceMemoryDecayConfig)
        },
    )
    rows = tuple(
        _row_from_public_payload(item, index=index)
        for index, item in enumerate(payload["rows"])
    )
    reason_counts = tuple(
        _reason_count_from_public_payload(item, index=index)
        for index, item in enumerate(payload["reason_code_counts"])
    )
    return ResearchStrategySpecialistSourceMemoryDecayReport(
        generated_at=_payload_datetime("payload.generated_at", payload["generated_at"]),
        config_version=_payload_string("payload.config_version", payload["config_version"]),
        config=config,
        memory_count=_payload_decimal("payload.memory_count", payload["memory_count"]),
        pass_count=_payload_decimal("payload.pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("payload.watch_count", payload["watch_count"]),
        block_count=_payload_decimal("payload.block_count", payload["block_count"]),
        average_decay_score=_payload_optional_decimal(
            "payload.average_decay_score",
            payload["average_decay_score"],
        ),
        status=_payload_string("payload.status", payload["status"]),
        reason_codes=_payload_reason_codes("payload.reason_codes", payload["reason_codes"]),
        reason_code_counts=reason_counts,
        rows=rows,
        derived_validation_digest=_payload_string(
            "payload.derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(value: object, *, index: int) -> ResearchStrategySpecialistSourceMemoryDecayRow:
    row = _require_payload_object(f"payload.rows[{index}]", value)
    return ResearchStrategySpecialistSourceMemoryDecayRow(
        memory_alias=_payload_string(f"payload.rows[{index}].memory_alias", row["memory_alias"]),
        last_memory_touch_at=_payload_datetime(
            f"payload.rows[{index}].last_memory_touch_at",
            row["last_memory_touch_at"],
        ),
        memory_age_seconds=_payload_decimal(
            f"payload.rows[{index}].memory_age_seconds",
            row["memory_age_seconds"],
        ),
        successful_recall_count=_payload_decimal(
            f"payload.rows[{index}].successful_recall_count",
            row["successful_recall_count"],
        ),
        failed_recall_count=_payload_decimal(
            f"payload.rows[{index}].failed_recall_count",
            row["failed_recall_count"],
        ),
        contradiction_count=_payload_decimal(
            f"payload.rows[{index}].contradiction_count",
            row["contradiction_count"],
        ),
        recall_observation_count=_payload_decimal(
            f"payload.rows[{index}].recall_observation_count",
            row["recall_observation_count"],
        ),
        recency_retention_score=_payload_decimal(
            f"payload.rows[{index}].recency_retention_score",
            row["recency_retention_score"],
        ),
        recall_reliability_score=_payload_decimal(
            f"payload.rows[{index}].recall_reliability_score",
            row["recall_reliability_score"],
        ),
        contradiction_penalty_score=_payload_decimal(
            f"payload.rows[{index}].contradiction_penalty_score",
            row["contradiction_penalty_score"],
        ),
        memory_retention_score=_payload_decimal(
            f"payload.rows[{index}].memory_retention_score",
            row["memory_retention_score"],
        ),
        decay_score=_payload_decimal(
            f"payload.rows[{index}].decay_score",
            row["decay_score"],
        ),
        status=_payload_string(f"payload.rows[{index}].status", row["status"]),
        reason_codes=_payload_reason_codes(
            f"payload.rows[{index}].reason_codes",
            row["reason_codes"],
        ),
        paper_only=row["paper_only"],
        report_only=row["report_only"],
        readonly=row["readonly"],
    )


def _reason_count_from_public_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount:
    item = _require_payload_object(f"payload.reason_code_counts[{index}]", value)
    return ResearchStrategySpecialistSourceMemoryDecayReasonCodeCount(
        reason_code=_payload_string(
            f"payload.reason_code_counts[{index}].reason_code",
            item["reason_code"],
        ),
        count=_payload_decimal(
            f"payload.reason_code_counts[{index}].count",
            item["count"],
        ),
        paper_only=item["paper_only"],
        report_only=item["report_only"],
        readonly=item["readonly"],
    )


def _payload_config_value(field_name: str, value: object) -> object:
    if field_name == "config_version":
        return _payload_string(f"payload.config.{field_name}", value)
    if field_name in ("paper_only", "report_only", "readonly"):
        if type(value) is not bool:
            raise ValueError(f"payload.config.{field_name} must be a bool")
        return value
    return _payload_decimal(f"payload.config.{field_name}", value)


def _payload_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(_payload_string(field_name, item) for item in value)


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = _quantize(decimal_value)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must use canonical Decimal precision")
    return normalized


def _payload_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _payload_decimal(field_name, value)


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_payload_object(field_name: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    return value


def _require_payload_list(field_name: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    return value


def _require_exact_fields(
    field_name: str,
    value: dict[str, Any],
    expected: tuple[str, ...],
) -> None:
    if tuple(value) != expected:
        raise ValueError(f"{field_name} must use exact public fields")


class _PayloadFlags:
    __slots__ = ("value",)

    def __init__(self, value: dict[str, Any]) -> None:
        self.value = value

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(str(key))
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str):
        _reject_unsafe_public_text(value)


def _reject_unsafe_public_text(value: str) -> None:
    lowered = value.lower()
    for fragment in _unsafe_public_fragments():
        if fragment in lowered:
            raise ValueError("public payload contains unsafe surface")


def _unsafe_public_fragments() -> tuple[str, ...]:
    return (
        "candidate",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wal" + "let",
        "or" + "der",
        "tra" + "de",
        "position_" + "size",
        "live_" + "trading",
        "rec" + "ommendation",
        "au" + "th",
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_as_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            Decimal(delta.days * 86_400)
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / Decimal("1000000")),
        )


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(normalized)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        is_whole = normalized == normalized.to_integral_value()
    if not is_whole:
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        is_whole = normalized == normalized.to_integral_value()
    if not is_whole:
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("Decimal must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError("Decimal must not use signed zero")
    with localcontext(DECIMAL_CONTEXT):
        try:
            normalized = value.quantize(RATIO_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError("Decimal must fit canonical precision") from exc
    if normalized.is_zero() and normalized.is_signed():
        raise ValueError("Decimal must not quantize to signed zero")
    return ZERO if normalized.is_zero() else normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or _CANONICAL_RE.fullmatch(value) is None
    ):
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_optional_string(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not str or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    for fragment in _unsafe_public_fragments():
        if fragment in lowered:
            raise ValueError(f"{field_name} must not include unsafe surface terms")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(
    value: object,
    expected_type: type[object],
    field_name: str,
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")
