"""Pure research decomposition for probability-event differences.

The module is deterministic and side-effect free. Callers provide redacted,
typed probability inputs; the report returns explanation-only decomposition
rows, statuses, and public payloads.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
from typing import Any


DEFAULT_RESEARCH_PROBABILITY_EDGE_DECOMPOSITION_CONFIG_VERSION = (
    "research-probability-edge-decomposition-v0"
)

_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_REFERENCE_RE = re.compile(r"^event_ref_[a-z0-9_]{3,48}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_-]{2,63}$")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_STATUSES = frozenset(("pass", "watch", "block"))
_REASON_CODE_SEQUENCE = (
    "no_probability_events",
    "evidence_adjustment_positive",
    "evidence_adjustment_negative",
    "evidence_adjustment_neutral",
    "material_probability_difference",
    "modest_probability_difference",
    "cost_friction_present",
    "high_cost_friction",
    "conflict_discount_present",
    "high_conflict_discount",
    "insufficient_evidence_items",
    "research_probability_edge_pass",
    "research_probability_edge_watch",
    "research_probability_edge_block",
)
_UNSAFE_PUBLIC_TERMS = (
    "candidate" + "_id",
    "market" + "_id",
    "sl" + "ug",
    "ques" + "tion",
    "src" + "_url",
    "source" + "_url",
    "src" + "_text",
    "source" + "_text",
    "dsn",
    "ta" + "ble",
    "tok" + "en",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "sub" + "mit",
    "can" + "cel",
    "rep" + "lace",
    "pos" + "ition_sizing",
    "b" + "uy",
    "s" + "ell",
    "rec" + "ommend",
    "li" + "ve",
    "tr" + "ade",
)


@dataclass(frozen=True)
class ResearchProbabilityEdgeDecompositionConfig:
    config_version: str = DEFAULT_RESEARCH_PROBABILITY_EDGE_DECOMPOSITION_CONFIG_VERSION
    pass_net_delta_threshold: Decimal = Decimal("0.050000")
    watch_net_delta_threshold: Decimal = Decimal("0.020000")
    max_pass_cost_friction: Decimal = Decimal("0.010000")
    max_pass_conflict_discount: Decimal = Decimal("0.020000")
    block_conflict_discount: Decimal = Decimal("0.100000")
    min_evidence_item_count: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchProbabilityEdgeDecompositionConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchProbabilityEdgeDecompositionConfig:
            raise ValueError(
                "config must be exactly ResearchProbabilityEdgeDecompositionConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PROBABILITY_EDGE_DECOMPOSITION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_net_delta_threshold",
            "watch_net_delta_threshold",
            "max_pass_cost_friction",
            "max_pass_conflict_discount",
            "block_conflict_discount",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_evidence_item_count",
            _require_positive_count_decimal(
                "min_evidence_item_count",
                self.min_evidence_item_count,
            ),
        )
        if self.pass_net_delta_threshold <= self.watch_net_delta_threshold:
            raise ValueError(
                "pass_net_delta_threshold must exceed watch_net_delta_threshold",
            )
        if self.block_conflict_discount <= self.max_pass_conflict_discount:
            raise ValueError(
                "block_conflict_discount must exceed max_pass_conflict_discount",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchProbabilityEdgeInput:
    event_reference: str
    baseline_probability: Decimal
    evidence_adjustment: Decimal
    cost_friction: Decimal = _ZERO
    conflict_discount: Decimal = _ZERO
    evidence_item_count: Decimal = Decimal("1.000000")
    conflict_item_count: Decimal = _ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchProbabilityEdgeInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchProbabilityEdgeInput:
            raise ValueError("input must be exactly ResearchProbabilityEdgeInput")
        object.__setattr__(
            self,
            "event_reference",
            _require_public_reference("event_reference", self.event_reference),
        )
        object.__setattr__(
            self,
            "baseline_probability",
            _require_probability_decimal(
                "baseline_probability",
                self.baseline_probability,
            ),
        )
        object.__setattr__(
            self,
            "evidence_adjustment",
            _require_signed_probability_decimal(
                "evidence_adjustment",
                self.evidence_adjustment,
            ),
        )
        for field_name in ("cost_friction", "conflict_discount"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_item_count", "conflict_item_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchProbabilityEdgeDecompositionRow:
    event_reference: str
    baseline_probability: Decimal
    evidence_adjustment: Decimal
    evidence_adjusted_probability: Decimal
    cost_friction: Decimal
    conflict_discount: Decimal
    decomposed_probability: Decimal
    net_probability_delta: Decimal
    absolute_net_probability_delta: Decimal
    evidence_item_count: Decimal
    conflict_item_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchProbabilityEdgeDecompositionRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchProbabilityEdgeDecompositionRow:
            raise ValueError(
                "row must be exactly ResearchProbabilityEdgeDecompositionRow",
            )
        object.__setattr__(
            self,
            "event_reference",
            _require_public_reference("event_reference", self.event_reference),
        )
        object.__setattr__(
            self,
            "baseline_probability",
            _require_probability_decimal(
                "baseline_probability",
                self.baseline_probability,
            ),
        )
        object.__setattr__(
            self,
            "evidence_adjustment",
            _require_signed_probability_decimal(
                "evidence_adjustment",
                self.evidence_adjustment,
            ),
        )
        for field_name in (
            "evidence_adjusted_probability",
            "cost_friction",
            "conflict_discount",
            "decomposed_probability",
            "absolute_net_probability_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "net_probability_delta",
            _require_signed_probability_decimal(
                "net_probability_delta",
                self.net_probability_delta,
            ),
        )
        for field_name in ("evidence_item_count", "conflict_item_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchProbabilityEdgeDecompositionReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchProbabilityEdgeDecompositionReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchProbabilityEdgeDecompositionReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchProbabilityEdgeDecompositionReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchProbabilityEdgeDecompositionReport:
    generated_at: datetime
    config_version: str
    report_status: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_absolute_net_probability_delta: Decimal
    max_cost_friction: Decimal
    max_conflict_discount: Decimal
    rows: tuple[ResearchProbabilityEdgeDecompositionRow, ...]
    reason_code_counts: tuple[
        ResearchProbabilityEdgeDecompositionReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchProbabilityEdgeDecompositionReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchProbabilityEdgeDecompositionReport:
            raise ValueError(
                "report must be exactly ResearchProbabilityEdgeDecompositionReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PROBABILITY_EDGE_DECOMPOSITION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("report_status", self.report_status)
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_absolute_net_probability_delta",
            "max_cost_friction",
            "max_conflict_discount",
        ):
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
            _normalize_reason_codes(self.reason_codes),
        )
        if self.derived_validation_digest != "":
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchProbabilityEdgeDecompositionReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_probability_edge_decomposition_report(
    events: Iterable[ResearchProbabilityEdgeInput],
    *,
    generated_at: datetime,
    config: ResearchProbabilityEdgeDecompositionConfig | None = None,
) -> ResearchProbabilityEdgeDecompositionReport:
    cfg = config or ResearchProbabilityEdgeDecompositionConfig()
    if type(cfg) is not ResearchProbabilityEdgeDecompositionConfig:
        raise ValueError(
            "config must be a ResearchProbabilityEdgeDecompositionConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(events)
    rows = tuple(_row_from_input(item, config=cfg) for item in inputs)
    reason_codes = _report_reason_codes(rows)
    return ResearchProbabilityEdgeDecompositionReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        report_status=_report_status(rows),
        event_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_absolute_net_probability_delta=_average(
            tuple(row.absolute_net_probability_delta for row in rows),
        ),
        max_cost_friction=max((row.cost_friction for row in rows), default=_ZERO),
        max_conflict_discount=max(
            (row.conflict_discount for row in rows),
            default=_ZERO,
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=reason_codes,
    )


def research_probability_edge_decomposition_payload(
    report: ResearchProbabilityEdgeDecompositionReport,
) -> dict[str, object]:
    if type(report) is not ResearchProbabilityEdgeDecompositionReport:
        raise ValueError(
            "report must be a ResearchProbabilityEdgeDecompositionReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    return report.payload


def _row_from_input(
    item: ResearchProbabilityEdgeInput,
    *,
    config: ResearchProbabilityEdgeDecompositionConfig,
) -> ResearchProbabilityEdgeDecompositionRow:
    evidence_adjusted_probability = _evidence_adjusted_probability(item)
    decomposed_probability = _decomposed_probability(item)
    net_probability_delta = _quantize(decomposed_probability - item.baseline_probability)
    absolute_net_probability_delta = _quantize(abs(net_probability_delta))
    status = _row_status(
        item,
        absolute_net_probability_delta=absolute_net_probability_delta,
        config=config,
    )
    return ResearchProbabilityEdgeDecompositionRow(
        event_reference=item.event_reference,
        baseline_probability=item.baseline_probability,
        evidence_adjustment=item.evidence_adjustment,
        evidence_adjusted_probability=evidence_adjusted_probability,
        cost_friction=item.cost_friction,
        conflict_discount=item.conflict_discount,
        decomposed_probability=decomposed_probability,
        net_probability_delta=net_probability_delta,
        absolute_net_probability_delta=absolute_net_probability_delta,
        evidence_item_count=item.evidence_item_count,
        conflict_item_count=item.conflict_item_count,
        status=status,
        reason_codes=_row_reason_codes(
            item,
            status=status,
            absolute_net_probability_delta=absolute_net_probability_delta,
            config=config,
        ),
    )


def _row_status(
    item: ResearchProbabilityEdgeInput | ResearchProbabilityEdgeDecompositionRow,
    *,
    absolute_net_probability_delta: Decimal,
    config: ResearchProbabilityEdgeDecompositionConfig,
) -> str:
    if (
        item.conflict_discount >= config.block_conflict_discount
        or item.evidence_item_count < config.min_evidence_item_count
    ):
        return "block"
    if (
        absolute_net_probability_delta >= config.pass_net_delta_threshold
        and item.cost_friction <= config.max_pass_cost_friction
        and item.conflict_discount <= config.max_pass_conflict_discount
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    item: ResearchProbabilityEdgeInput | ResearchProbabilityEdgeDecompositionRow,
    *,
    status: str,
    absolute_net_probability_delta: Decimal,
    config: ResearchProbabilityEdgeDecompositionConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.evidence_adjustment > _ZERO:
        reason_codes.append("evidence_adjustment_positive")
    elif item.evidence_adjustment < _ZERO:
        reason_codes.append("evidence_adjustment_negative")
    else:
        reason_codes.append("evidence_adjustment_neutral")
    if absolute_net_probability_delta >= config.pass_net_delta_threshold:
        reason_codes.append("material_probability_difference")
    elif absolute_net_probability_delta >= config.watch_net_delta_threshold:
        reason_codes.append("modest_probability_difference")
    if item.cost_friction > _ZERO:
        reason_codes.append("cost_friction_present")
    if item.cost_friction > config.max_pass_cost_friction:
        reason_codes.append("high_cost_friction")
    if item.conflict_discount > _ZERO or item.conflict_item_count > _ZERO:
        reason_codes.append("conflict_discount_present")
    if item.conflict_discount >= config.block_conflict_discount:
        reason_codes.append("high_conflict_discount")
    if item.evidence_item_count < config.min_evidence_item_count:
        reason_codes.append("insufficient_evidence_items")
    reason_codes.append(f"research_probability_edge_{status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[ResearchProbabilityEdgeDecompositionRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchProbabilityEdgeDecompositionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_probability_events", "research_probability_edge_block")
    return _normalize_reason_codes(
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
    )


def _validate_row_consistency(row: ResearchProbabilityEdgeDecompositionRow) -> None:
    if row.evidence_adjusted_probability != _clamp_probability(
        row.baseline_probability + row.evidence_adjustment,
    ):
        raise ValueError("evidence_adjusted_probability must match decomposition")
    expected_decomposed = _clamp_probability(
        row.evidence_adjusted_probability - row.cost_friction - row.conflict_discount,
    )
    if row.decomposed_probability != expected_decomposed:
        raise ValueError("decomposed_probability must match decomposition")
    expected_delta = _quantize(row.decomposed_probability - row.baseline_probability)
    if row.net_probability_delta != expected_delta:
        raise ValueError("net_probability_delta must match decomposition")
    if row.absolute_net_probability_delta != _quantize(abs(expected_delta)):
        raise ValueError("absolute_net_probability_delta must match decomposition")


def _validate_report_consistency(
    report: ResearchProbabilityEdgeDecompositionReport,
) -> None:
    rows = report.rows
    if report.event_count != _decimal_count(len(rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_absolute_net_probability_delta != _average(
        tuple(row.absolute_net_probability_delta for row in rows),
    ):
        raise ValueError("average_absolute_net_probability_delta must match rows")
    if report.max_cost_friction != max(
        (row.cost_friction for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_cost_friction must match rows")
    if report.max_conflict_discount != max(
        (row.conflict_discount for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_conflict_discount must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    value: Iterable[ResearchProbabilityEdgeInput],
) -> tuple[ResearchProbabilityEdgeInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("events must be an iterable of probability inputs")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("events must be an iterable of probability inputs") from exc
    seen_references: set[str] = set()
    for row in rows:
        if type(row) is not ResearchProbabilityEdgeInput:
            raise ValueError("events must contain ResearchProbabilityEdgeInput")
        _require_hard_flags("input", row)
        if row.event_reference in seen_references:
            raise ValueError("event_reference values must be unique")
        seen_references.add(row.event_reference)
    return tuple(sorted(rows, key=lambda row: row.event_reference))


def _normalize_rows(
    value: Iterable[ResearchProbabilityEdgeDecompositionRow],
) -> tuple[ResearchProbabilityEdgeDecompositionRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of decomposition rows")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of decomposition rows") from exc
    sorted_rows = tuple(sorted(rows, key=lambda row: row.event_reference))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    seen_references: set[str] = set()
    for row in rows:
        if type(row) is not ResearchProbabilityEdgeDecompositionRow:
            raise ValueError("rows must contain ResearchProbabilityEdgeDecompositionRow")
        _require_hard_flags("row", row)
        if row.event_reference in seen_references:
            raise ValueError("rows event_reference values must be unique")
        seen_references.add(row.event_reference)
    return rows


def _normalize_reason_code_counts(
    value: Iterable[ResearchProbabilityEdgeDecompositionReasonCodeCount],
) -> tuple[ResearchProbabilityEdgeDecompositionReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    sorted_rows = tuple(sorted(rows, key=lambda row: _REASON_CODE_SEQUENCE.index(row.reason_code)))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted deterministically")
    seen_codes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchProbabilityEdgeDecompositionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchProbabilityEdgeDecompositionReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts values must be unique")
        seen_codes.add(row.reason_code)
    return rows


def _reason_code_counts(
    rows: tuple[ResearchProbabilityEdgeDecompositionRow, ...],
) -> tuple[ResearchProbabilityEdgeDecompositionReasonCodeCount, ...]:
    counts: list[ResearchProbabilityEdgeDecompositionReasonCodeCount] = []
    for reason_code in _REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if not rows and reason_code == "no_probability_events":
            count = Decimal("1.000000")
        if count > _ZERO:
            counts.append(
                ResearchProbabilityEdgeDecompositionReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                ),
            )
    return tuple(counts)


def _status_count(
    rows: tuple[ResearchProbabilityEdgeDecompositionRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchProbabilityEdgeDecompositionRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _evidence_adjusted_probability(value: ResearchProbabilityEdgeInput) -> Decimal:
    return _clamp_probability(value.baseline_probability + value.evidence_adjustment)


def _decomposed_probability(value: ResearchProbabilityEdgeInput) -> Decimal:
    return _clamp_probability(
        _evidence_adjusted_probability(value)
        - value.cost_friction
        - value.conflict_discount,
    )


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext() as context:
        context.prec = 64
        return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_REFERENCE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a redacted event reference")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if value != normalized:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_signed_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < -_ONE or normalized > _ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


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
    return tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _clamp_probability(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _report_values_without_digest(
    report: ResearchProbabilityEdgeDecompositionReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
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
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_PROBABILITY_EDGE_DECOMPOSITION_CONFIG_VERSION",
    "ResearchProbabilityEdgeDecompositionConfig",
    "ResearchProbabilityEdgeDecompositionReasonCodeCount",
    "ResearchProbabilityEdgeDecompositionReport",
    "ResearchProbabilityEdgeDecompositionRow",
    "ResearchProbabilityEdgeInput",
    "build_research_probability_edge_decomposition_report",
    "research_probability_edge_decomposition_payload",
)
