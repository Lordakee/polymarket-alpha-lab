"""Pure report-only policy for caller-supplied model signal weights.

The module is deterministic and side-effect free. Callers provide typed signal
rows; the policy returns public weight explanations, statuses, and reason codes.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchModelSignalWeightingConfig",
    "ResearchModelSignalWeightingInputRow",
    "ResearchModelSignalWeightingReasonCodeCount",
    "ResearchModelSignalWeightingReport",
    "ResearchModelSignalWeightingRow",
    "build_research_model_signal_weighting_policy_report",
    "research_model_signal_weighting_policy_payload",
)


DEFAULT_CONFIG_VERSION = "research-model-signal-weighting-policy-v0"
SIGNAL_NAMES = ("naive", "book_imbalance", "llm", "manual-research", "team-memory")
HUMAN_RESEARCH_SIGNALS = ("manual-research", "team-memory")
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
UNSAFE_PUBLIC_KEYS = (
    "raw_signal_id",
    "raw_source",
    "raw_market_id",
    "source_id",
    "source_ids",
    "market_id",
    "market_ids",
    "identifier",
    "identifiers",
)
UNSAFE_REASON_FRAGMENTS = ("source", "market", "identifier")


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchModelSignalWeightingConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_min_active_signal_count: Decimal = Decimal("3")
    watch_min_active_signal_count: Decimal = Decimal("2")
    max_single_signal_weight_pass: Decimal = Decimal("0.600000")
    max_single_signal_weight_watch: Decimal = Decimal("0.800000")
    min_human_research_weight_pass: Decimal = Decimal("0.150000")
    min_human_research_weight_watch: Decimal = Decimal("0.050000")
    min_component_watch_score: Decimal = Decimal("0.250000")
    conflict_watch_threshold: Decimal = Decimal("0.400000")
    conflict_block_threshold: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchModelSignalWeightingConfig:
            raise TypeError(
                "ResearchModelSignalWeightingConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchModelSignalWeightingConfig:
            raise ValueError(
                "config must be exactly ResearchModelSignalWeightingConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_min_active_signal_count",
            "watch_min_active_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_active_signal_count < self.watch_min_active_signal_count:
            raise ValueError(
                "pass_min_active_signal_count must be at least "
                "watch_min_active_signal_count",
            )
        for field_name in (
            "max_single_signal_weight_pass",
            "max_single_signal_weight_watch",
            "min_human_research_weight_pass",
            "min_human_research_weight_watch",
            "min_component_watch_score",
            "conflict_watch_threshold",
            "conflict_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_single_signal_weight_pass > self.max_single_signal_weight_watch:
            raise ValueError(
                "max_single_signal_weight_watch must be at least "
                "max_single_signal_weight_pass",
            )
        if self.min_human_research_weight_pass < self.min_human_research_weight_watch:
            raise ValueError(
                "min_human_research_weight_pass must be at least "
                "min_human_research_weight_watch",
            )
        if self.conflict_watch_threshold > self.conflict_block_threshold:
            raise ValueError(
                "conflict_block_threshold must be at least conflict_watch_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchModelSignalWeightingInputRow:
    signal_name: str
    raw_signal_id: str | None
    raw_source: str | None
    raw_market_id: str | None
    raw_weight: Decimal
    quality_score: Decimal
    confidence_score: Decimal
    freshness_score: Decimal
    conflict_score: Decimal
    enabled: bool = True
    hard_block: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchModelSignalWeightingInputRow:
            raise TypeError(
                "ResearchModelSignalWeightingInputRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchModelSignalWeightingInputRow:
            raise ValueError(
                "input row must be exactly ResearchModelSignalWeightingInputRow",
            )
        _require_signal_name("signal_name", self.signal_name)
        for field_name in ("raw_signal_id", "raw_source", "raw_market_id"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_public_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "raw_weight",
            "quality_score",
            "confidence_score",
            "freshness_score",
            "conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "enabled", _require_bool("enabled", self.enabled))
        object.__setattr__(
            self,
            "hard_block",
            _require_bool("hard_block", self.hard_block),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchModelSignalWeightingRow:
    signal_name: str
    raw_weight: Decimal
    quality_multiplier: Decimal
    confidence_multiplier: Decimal
    freshness_multiplier: Decimal
    conflict_penalty_multiplier: Decimal
    adjusted_weight: Decimal
    normalized_weight: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchModelSignalWeightingRow:
            raise TypeError(
                "ResearchModelSignalWeightingRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchModelSignalWeightingRow:
            raise ValueError("row must be exactly ResearchModelSignalWeightingRow")
        _require_signal_name("signal_name", self.signal_name)
        for field_name in (
            "raw_weight",
            "quality_multiplier",
            "confidence_multiplier",
            "freshness_multiplier",
            "conflict_penalty_multiplier",
            "adjusted_weight",
            "normalized_weight",
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


@dataclass(frozen=True)
class ResearchModelSignalWeightingReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchModelSignalWeightingReasonCodeCount:
            raise TypeError(
                "ResearchModelSignalWeightingReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchModelSignalWeightingReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchModelSignalWeightingReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchModelSignalWeightingReport:
    generated_at: datetime
    config_version: str
    status: str
    signal_count: Decimal
    active_signal_count: Decimal
    watch_signal_count: Decimal
    block_signal_count: Decimal
    zero_weight_signal_count: Decimal
    total_raw_weight: Decimal
    total_adjusted_weight: Decimal
    max_normalized_weight: Decimal
    human_research_normalized_weight: Decimal
    rows: tuple[ResearchModelSignalWeightingRow, ...]
    reason_code_counts: tuple[ResearchModelSignalWeightingReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchModelSignalWeightingReport:
            raise TypeError(
                "ResearchModelSignalWeightingReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchModelSignalWeightingReport:
            raise ValueError("report must be exactly ResearchModelSignalWeightingReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "signal_count",
            "active_signal_count",
            "watch_signal_count",
            "block_signal_count",
            "zero_weight_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("total_raw_weight", "total_adjusted_weight"):
            object.__setattr__(
                self,
                field_name,
                _quantize(_require_nonnegative_decimal(field_name, getattr(self, field_name))),
            )
        for field_name in ("max_normalized_weight", "human_research_normalized_weight"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_model_signal_weighting_policy_report(
    input_rows: Iterable[object],
    *,
    config: ResearchModelSignalWeightingConfig | None = None,
    generated_at: datetime,
) -> ResearchModelSignalWeightingReport:
    cfg = config or ResearchModelSignalWeightingConfig()
    if type(cfg) is not ResearchModelSignalWeightingConfig:
        raise ValueError("config must be a ResearchModelSignalWeightingConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows)
    _reject_duplicate_signal_names(rows)

    interim_rows = tuple(
        _build_interim_row(row, config=cfg)
        for row in sorted(rows, key=lambda row: _signal_sort_key(row.signal_name))
    )
    total_adjusted_weight = _sum_decimal(item["adjusted_weight"] for item in interim_rows)
    built_rows = tuple(
        _build_output_row(
            item,
            total_adjusted_weight=total_adjusted_weight,
            config=cfg,
        )
        for item in interim_rows
    )
    active_signal_count = _decimal_count(
        sum(1 for row in built_rows if row.adjusted_weight > ZERO),
    )
    max_normalized_weight = max(
        (row.normalized_weight for row in built_rows),
        default=ZERO,
    )
    human_research_normalized_weight = _sum_decimal(
        row.normalized_weight
        for row in built_rows
        if row.signal_name in HUMAN_RESEARCH_SIGNALS
    )
    reason_codes = _report_reason_codes(
        rows=built_rows,
        active_signal_count=active_signal_count,
        total_adjusted_weight=total_adjusted_weight,
        max_normalized_weight=max_normalized_weight,
        human_research_normalized_weight=human_research_normalized_weight,
        config=cfg,
    )
    status = _summary_status(reason_codes)

    return ResearchModelSignalWeightingReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        status=status,
        signal_count=_decimal_count(len(built_rows)),
        active_signal_count=active_signal_count,
        watch_signal_count=_decimal_count(_status_count(built_rows, "watch")),
        block_signal_count=_decimal_count(_status_count(built_rows, "block")),
        zero_weight_signal_count=_decimal_count(
            sum(1 for row in built_rows if row.adjusted_weight == ZERO),
        ),
        total_raw_weight=_sum_decimal(row.raw_weight for row in built_rows),
        total_adjusted_weight=total_adjusted_weight,
        max_normalized_weight=max_normalized_weight,
        human_research_normalized_weight=human_research_normalized_weight,
        rows=built_rows,
        reason_code_counts=_reason_code_counts(built_rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_model_signal_weighting_policy_payload(
    report: ResearchModelSignalWeightingReport,
) -> dict[str, Any]:
    if type(report) is not ResearchModelSignalWeightingReport:
        raise ValueError("report must be a ResearchModelSignalWeightingReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _rename_public_weight_keys(payload)
    _reject_unsafe_public_payload(payload)
    return payload


def _build_interim_row(
    row: ResearchModelSignalWeightingInputRow,
    *,
    config: ResearchModelSignalWeightingConfig,
) -> dict[str, object]:
    conflict_penalty_multiplier = _quantize(ONE - row.conflict_score)
    adjusted_weight = ZERO
    if row.enabled and not row.hard_block:
        adjusted_weight = _quantize(
            row.raw_weight
            * row.quality_score
            * row.confidence_score
            * row.freshness_score
            * conflict_penalty_multiplier,
        )
    status = "pass"
    reason_codes: set[str] = set()
    if not row.enabled:
        status = "block"
        reason_codes.add("disabled_signal")
    if row.hard_block:
        status = "block"
        reason_codes.add("hard_block_signal")
    if row.raw_weight == ZERO:
        status = _worse_status(status, "block")
        reason_codes.add("zero_input_weight")
    if adjusted_weight == ZERO:
        status = _worse_status(status, "block")
        reason_codes.add("zero_adjusted_weight")
    if row.quality_score < config.min_component_watch_score:
        status = _worse_status(status, "watch")
        reason_codes.add("low_quality_score")
    if row.confidence_score < config.min_component_watch_score:
        status = _worse_status(status, "watch")
        reason_codes.add("low_confidence_score")
    if row.freshness_score < config.min_component_watch_score:
        status = _worse_status(status, "watch")
        reason_codes.add("stale_signal_score")
    if row.conflict_score >= config.conflict_block_threshold:
        status = _worse_status(status, "block")
        reason_codes.add("conflict_block")
    elif row.conflict_score >= config.conflict_watch_threshold:
        status = _worse_status(status, "watch")
        reason_codes.add("conflict_watch")
    for reason_code in row.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    reason_codes.add(f"signal_weight_{status}")
    return {
        "signal_name": row.signal_name,
        "raw_weight": row.raw_weight,
        "quality_multiplier": row.quality_score,
        "confidence_multiplier": row.confidence_score,
        "freshness_multiplier": row.freshness_score,
        "conflict_penalty_multiplier": conflict_penalty_multiplier,
        "adjusted_weight": adjusted_weight,
        "status": status,
        "reason_codes": tuple(sorted(reason_codes)),
    }


def _build_output_row(
    item: dict[str, object],
    *,
    total_adjusted_weight: Decimal,
    config: ResearchModelSignalWeightingConfig,
) -> ResearchModelSignalWeightingRow:
    adjusted_weight = _require_probability_decimal(
        "adjusted_weight",
        item["adjusted_weight"],
    )
    normalized_weight = _ratio(adjusted_weight, total_adjusted_weight)
    status = _require_status_value("status", item["status"])
    reason_codes = set(
        _normalize_reason_codes(
            "reason_codes",
            item["reason_codes"],
            allow_empty=False,
        ),
    )
    reason_codes = {
        reason_code
        for reason_code in reason_codes
        if not reason_code.startswith("signal_weight_")
    }
    if normalized_weight > config.max_single_signal_weight_watch:
        status = _worse_status(status, "block")
        reason_codes.add("single_signal_weight_block")
    elif normalized_weight > config.max_single_signal_weight_pass:
        status = _worse_status(status, "watch")
        reason_codes.add("single_signal_weight_watch")
    reason_codes.add(f"signal_weight_{status}")

    return ResearchModelSignalWeightingRow(
        signal_name=_require_signal_name_value("signal_name", item["signal_name"]),
        raw_weight=_require_probability_decimal("raw_weight", item["raw_weight"]),
        quality_multiplier=_require_probability_decimal(
            "quality_multiplier",
            item["quality_multiplier"],
        ),
        confidence_multiplier=_require_probability_decimal(
            "confidence_multiplier",
            item["confidence_multiplier"],
        ),
        freshness_multiplier=_require_probability_decimal(
            "freshness_multiplier",
            item["freshness_multiplier"],
        ),
        conflict_penalty_multiplier=_require_probability_decimal(
            "conflict_penalty_multiplier",
            item["conflict_penalty_multiplier"],
        ),
        adjusted_weight=adjusted_weight,
        normalized_weight=normalized_weight,
        status=status,
        reason_codes=tuple(sorted(reason_codes)),
    )


def _normalize_input_rows(
    input_rows: Iterable[object],
) -> tuple[ResearchModelSignalWeightingInputRow, ...]:
    if isinstance(input_rows, (str, bytes)):
        raise ValueError("input_rows must be an iterable")
    try:
        values = tuple(input_rows)
    except TypeError as exc:
        raise ValueError("input_rows must be an iterable") from exc
    return tuple(_coerce_input_row(value) for value in values)


def _coerce_input_row(value: object) -> ResearchModelSignalWeightingInputRow:
    if type(value) is ResearchModelSignalWeightingInputRow:
        _require_hard_flags("input row", value)
        return value
    _require_hard_flags("input row", value)
    return ResearchModelSignalWeightingInputRow(
        signal_name=_field_value(value, "signal_name"),
        raw_signal_id=_field_value(value, "raw_signal_id"),
        raw_source=_field_value(value, "raw_source"),
        raw_market_id=_field_value(value, "raw_market_id"),
        raw_weight=_field_value(value, "raw_weight"),
        quality_score=_field_value(value, "quality_score"),
        confidence_score=_field_value(value, "confidence_score"),
        freshness_score=_field_value(value, "freshness_score"),
        conflict_score=_field_value(value, "conflict_score"),
        enabled=_field_value(value, "enabled", default=True),
        hard_block=_field_value(value, "hard_block", default=False),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _reject_duplicate_signal_names(
    rows: tuple[ResearchModelSignalWeightingInputRow, ...],
) -> None:
    seen: set[str] = set()
    for row in rows:
        if row.signal_name in seen:
            raise ValueError("signal_name values must be unique")
        seen.add(row.signal_name)


def _report_reason_codes(
    *,
    rows: tuple[ResearchModelSignalWeightingRow, ...],
    active_signal_count: Decimal,
    total_adjusted_weight: Decimal,
    max_normalized_weight: Decimal,
    human_research_normalized_weight: Decimal,
    config: ResearchModelSignalWeightingConfig,
) -> tuple[str, ...]:
    status = _report_status(
        rows=rows,
        active_signal_count=active_signal_count,
        total_adjusted_weight=total_adjusted_weight,
        max_normalized_weight=max_normalized_weight,
        human_research_normalized_weight=human_research_normalized_weight,
        config=config,
    )
    reason_codes: set[str] = {f"signal_weight_policy_{status}"}
    if not rows:
        reason_codes.add("no_signal_weights")
    if rows and total_adjusted_weight == ZERO:
        reason_codes.add("no_adjusted_signal_weight")
    if active_signal_count < config.watch_min_active_signal_count:
        reason_codes.add("too_few_active_signals_block")
    elif active_signal_count < config.pass_min_active_signal_count:
        reason_codes.add("too_few_active_signals_watch")
    if max_normalized_weight > config.max_single_signal_weight_watch:
        reason_codes.add("single_signal_concentration_block")
    elif max_normalized_weight > config.max_single_signal_weight_pass:
        reason_codes.add("single_signal_concentration_watch")
    if human_research_normalized_weight < config.min_human_research_weight_watch:
        reason_codes.add("human_research_weight_block")
    elif human_research_normalized_weight < config.min_human_research_weight_pass:
        reason_codes.add("human_research_weight_watch")
    if _has_hard_blocked_signal(rows):
        reason_codes.add("hard_block_signal_present")
    elif any(row.status == "block" for row in rows):
        reason_codes.add("block_signal_present")
    elif any(row.status == "watch" for row in rows):
        reason_codes.add("watch_signal_present")
    if status == "pass":
        reason_codes.add("balanced_signal_weights")
    return tuple(sorted(reason_codes))


def _report_status(
    *,
    rows: tuple[ResearchModelSignalWeightingRow, ...],
    active_signal_count: Decimal,
    total_adjusted_weight: Decimal,
    max_normalized_weight: Decimal,
    human_research_normalized_weight: Decimal,
    config: ResearchModelSignalWeightingConfig,
) -> str:
    if not rows or total_adjusted_weight == ZERO:
        return "block"
    if _has_hard_blocked_signal(rows):
        return "block"
    if active_signal_count < config.watch_min_active_signal_count:
        return "block"
    if max_normalized_weight > config.max_single_signal_weight_watch:
        return "block"
    if human_research_normalized_weight < config.min_human_research_weight_watch:
        return "block"
    if active_signal_count < config.pass_min_active_signal_count:
        return "watch"
    if max_normalized_weight > config.max_single_signal_weight_pass:
        return "watch"
    if human_research_normalized_weight < config.min_human_research_weight_pass:
        return "watch"
    if any(row.status != "pass" for row in rows):
        return "watch"
    return "pass"


def _has_hard_blocked_signal(
    rows: tuple[ResearchModelSignalWeightingRow, ...],
) -> bool:
    hard_codes = {"hard_block_signal", "conflict_block"}
    return any(bool(hard_codes.intersection(row.reason_codes)) for row in rows)


def _reason_code_counts(
    rows: tuple[ResearchModelSignalWeightingRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchModelSignalWeightingReasonCodeCount, ...]:
    counts: Counter[str] = Counter(report_reason_codes)
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchModelSignalWeightingReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _normalize_rows(
    rows: tuple[ResearchModelSignalWeightingRow, ...],
) -> tuple[ResearchModelSignalWeightingRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchModelSignalWeightingRow:
            raise ValueError(
                "rows must contain ResearchModelSignalWeightingRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: _signal_sort_key(row.signal_name)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by signal_name policy sequence")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchModelSignalWeightingReasonCodeCount, ...],
) -> tuple[ResearchModelSignalWeightingReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchModelSignalWeightingReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchModelSignalWeightingReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchModelSignalWeightingRow) -> None:
    if row.adjusted_weight > row.raw_weight:
        raise ValueError("adjusted_weight must not exceed raw_weight")
    if row.normalized_weight > ZERO and row.adjusted_weight == ZERO:
        raise ValueError("normalized_weight requires adjusted_weight")
    if row.adjusted_weight == ZERO and row.status != "block":
        raise ValueError("zero adjusted_weight must block the row")
    if f"signal_weight_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if any(
        reason_code.startswith("signal_weight_")
        and reason_code != f"signal_weight_{row.status}"
        for reason_code in row.reason_codes
    ):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and any(
        reason_code.endswith("_watch") or reason_code.endswith("_block")
        for reason_code in row.reason_codes
    ):
        raise ValueError("pass row must not include watch or block reason codes")


def _validate_report_consistency(report: ResearchModelSignalWeightingReport) -> None:
    rows = report.rows
    if report.signal_count != _decimal_count(len(rows)):
        raise ValueError("signal_count must match rows")
    if report.active_signal_count != _decimal_count(
        sum(1 for row in rows if row.adjusted_weight > ZERO),
    ):
        raise ValueError("active_signal_count must match rows")
    if report.watch_signal_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_signal_count must match rows")
    if report.block_signal_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_signal_count must match rows")
    if report.zero_weight_signal_count != _decimal_count(
        sum(1 for row in rows if row.adjusted_weight == ZERO),
    ):
        raise ValueError("zero_weight_signal_count must match rows")
    if report.total_raw_weight != _sum_decimal(row.raw_weight for row in rows):
        raise ValueError("total_raw_weight must match rows")
    if report.total_adjusted_weight != _sum_decimal(
        row.adjusted_weight for row in rows
    ):
        raise ValueError("total_adjusted_weight must match rows")
    if report.max_normalized_weight != max(
        (row.normalized_weight for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_normalized_weight must match rows")
    if report.human_research_normalized_weight != _sum_decimal(
        row.normalized_weight
        for row in rows
        if row.signal_name in HUMAN_RESEARCH_SIGNALS
    ):
        raise ValueError("human_research_normalized_weight must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if "signal_weight_policy_block" in reason_codes:
        return "block"
    if "signal_weight_policy_watch" in reason_codes:
        return "watch"
    if "signal_weight_policy_pass" in reason_codes:
        return "pass"
    raise ValueError("reason_codes must include a policy status")


def _status_count(
    rows: tuple[ResearchModelSignalWeightingRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    return _quantize(sum(values, ZERO))


def _worse_status(left: str, right: str) -> str:
    _require_status("left", left)
    _require_status("right", right)
    if STATUSES.index(left) >= STATUSES.index(right):
        return left
    return right


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _rename_public_weight_keys(payload: dict[str, object]) -> None:
    if "total_raw_weight" in payload:
        payload["total_input_weight"] = payload.pop("total_raw_weight")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("payload rows must be a list")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("payload rows must contain objects")
        if "raw_weight" in row:
            row["input_weight"] = row.pop("raw_weight")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if lowered in UNSAFE_PUBLIC_KEYS:
                raise ValueError("public payload contains an unsafe identifier key")
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be from 0 to 1")
    return _quantize(normalized)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")


def _require_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_public_string(field_name, value)
    return value


def _require_signal_name(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIGNAL_NAMES:
        raise ValueError(f"{field_name} must be a known signal name")


def _require_signal_name_value(field_name: str, value: object) -> str:
    _require_signal_name(field_name, value)
    return value


def _signal_sort_key(signal_name: str) -> int:
    _require_signal_name("signal_name", signal_name)
    return SIGNAL_NAMES.index(signal_name)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_status_value(field_name: str, value: object) -> str:
    _require_status(field_name, value)
    return value


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
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")
    if any(fragment in value for fragment in UNSAFE_REASON_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain unsafe identifier text")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")
