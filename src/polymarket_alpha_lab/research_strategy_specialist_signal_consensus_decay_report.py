"""Pure report-only reducer for specialist signal consensus decay."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, final


DEFAULT_RESEARCH_STRATEGY_SPECIALIST_SIGNAL_CONSENSUS_DECAY_CONFIG_VERSION = (
    "research-strategy-specialist-signal-consensus-decay-report-v0"
)
RESEARCH_STRATEGY_SPECIALIST_SIGNAL_CONSENSUS_DECAY_STATUSES = (
    "pass",
    "watch",
    "block",
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_CONSENSUS_STRENGTH_WEIGHT = Decimal("0.450000")
_CONFIDENCE_WEIGHT = Decimal("0.300000")
_FRESHNESS_WEIGHT = Decimal("0.250000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_REPORT_REASON_PRIORITY = (
    "specialist_signal_consensus_decay_report_block",
    "specialist_signal_consensus_decay_report_watch",
    "specialist_signal_consensus_decay_report_pass",
    "specialist_signal_consensus_decay_report_clear",
    "consensus_decay_review",
    "specialist_freshness_review",
    "specialist_dispersion_review",
    "specialist_quorum_review",
)
_ROW_REASON_PRIORITY = (
    "specialist_quorum_block",
    "consensus_decay_block",
    "specialist_freshness_block",
    "specialist_dispersion_block",
    "consensus_decay_watch",
    "specialist_freshness_watch",
    "specialist_dispersion_watch",
    "specialist_signal_consensus_decay_pass",
)
_REASON_PRIORITY = {
    reason_code: index
    for index, reason_code in enumerate((*_REPORT_REASON_PRIORITY, *_ROW_REASON_PRIORITY))
}
_REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "config",
    "input_signal_count",
    "consensus_row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "mean_consensus_decay_score",
    "max_probability_dispersion",
    "min_freshness_score",
    "status",
    "reason_codes",
    "rows",
    "reason_code_counts",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_CONFIG_PAYLOAD_FIELDS = (
    "config_version",
    "consensus_pass_floor",
    "consensus_watch_floor",
    "freshness_watch_floor",
    "freshness_block_floor",
    "dispersion_watch_ceiling",
    "dispersion_block_ceiling",
    "stale_signal_block_seconds",
    "minimum_specialist_count",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_FIELDS = (
    "signal_ref",
    "observed_at",
    "specialist_count",
    "consensus_probability",
    "probability_dispersion",
    "mean_confidence_score",
    "mean_freshness_score",
    "consensus_decay_score",
    "status",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_REASON_CODE_COUNT_PAYLOAD_FIELDS = (
    "reason_code",
    "count",
    "input_ratio",
    "paper_only",
    "report_only",
    "readonly",
)


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    _surface_term("candi", "date"),
    "market",
    "slug",
    _surface_term("ques", "tion"),
    _surface_term("source", "_", "url"),
    _surface_term("source", "_", "text"),
    "://",
    _surface_term("d", "sn"),
    _surface_term("ta", "ble"),
    _surface_term("tok", "en"),
    _surface_term("wal", "let"),
    _surface_term("or", "der"),
    _surface_term("tra", "de"),
    _surface_term("siz", "ing"),
    _surface_term("reco", "mmendation"),
    _surface_term("li", "ve"),
    _surface_term("au", "th"),
    _surface_term("api", "_", "key"),
    "credential",
    "secret",
    _surface_term("private", "_", "key"),
    "password",
    "bearer",
)


class _FinalPublicDataclass:
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySpecialistSignalConsensusDecayConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_SPECIALIST_SIGNAL_CONSENSUS_DECAY_CONFIG_VERSION
    )
    consensus_pass_floor: Decimal = Decimal("0.750000")
    consensus_watch_floor: Decimal = Decimal("0.550000")
    freshness_watch_floor: Decimal = Decimal("0.500000")
    freshness_block_floor: Decimal = Decimal("0.250000")
    dispersion_watch_ceiling: Decimal = Decimal("0.200000")
    dispersion_block_ceiling: Decimal = Decimal("0.350000")
    stale_signal_block_seconds: Decimal = Decimal("7200.000000")
    minimum_specialist_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySpecialistSignalConsensusDecayConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchStrategySpecialistSignalConsensusDecayConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "consensus_pass_floor",
            "consensus_watch_floor",
            "freshness_watch_floor",
            "freshness_block_floor",
            "dispersion_watch_ceiling",
            "dispersion_block_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_signal_block_seconds",
            _normalize_positive_decimal(
                "stale_signal_block_seconds",
                self.stale_signal_block_seconds,
            ),
        )
        object.__setattr__(
            self,
            "minimum_specialist_count",
            _normalize_positive_whole_decimal(
                "minimum_specialist_count",
                self.minimum_specialist_count,
            ),
        )
        if self.consensus_pass_floor <= self.consensus_watch_floor:
            raise ValueError("consensus_pass_floor must exceed consensus_watch_floor")
        if self.freshness_watch_floor <= self.freshness_block_floor:
            raise ValueError("freshness_watch_floor must exceed freshness_block_floor")
        if self.dispersion_block_ceiling <= self.dispersion_watch_ceiling:
            raise ValueError(
                "dispersion_block_ceiling must exceed dispersion_watch_ceiling",
            )
        _require_hard_flags("config", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySpecialistSignalConsensusDecayInput(_FinalPublicDataclass):
    signal_ref: str
    specialist_ref: str
    observed_at: datetime
    probability_estimate: Decimal
    confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySpecialistSignalConsensusDecayInput:
            raise ValueError(
                "input must be exactly "
                "ResearchStrategySpecialistSignalConsensusDecayInput",
            )
        for field_name in ("signal_ref", "specialist_ref"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("probability_estimate", "confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount",
            )
        _require_row_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_probability_decimal("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySpecialistSignalConsensusDecayRow(_FinalPublicDataclass):
    signal_ref: str
    observed_at: datetime
    specialist_count: Decimal
    consensus_probability: Decimal
    probability_dispersion: Decimal
    mean_confidence_score: Decimal
    mean_freshness_score: Decimal
    consensus_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySpecialistSignalConsensusDecayRow:
            raise ValueError(
                "row must be exactly ResearchStrategySpecialistSignalConsensusDecayRow",
            )
        _require_public_identifier("signal_ref", self.signal_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "specialist_count",
            _normalize_positive_whole_decimal("specialist_count", self.specialist_count),
        )
        for field_name in (
            "consensus_probability",
            "probability_dispersion",
            "mean_confidence_score",
            "mean_freshness_score",
            "consensus_decay_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        for reason_code in self.reason_codes:
            _require_row_reason_code("reason_codes", reason_code)
        _require_hard_flags("row", self)
        _validate_row_reason_codes(self)
        _validate_row_derived_score(self)
        if type(self.derived_validation_digest) is not str:
            _require_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySpecialistSignalConsensusDecayReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    config: ResearchStrategySpecialistSignalConsensusDecayConfig
    input_signal_count: Decimal
    consensus_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_consensus_decay_score: Decimal
    max_probability_dispersion: Decimal
    min_freshness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategySpecialistSignalConsensusDecayRow, ...]
    reason_code_counts: tuple[
        ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount,
        ...
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySpecialistSignalConsensusDecayReport:
            raise ValueError(
                "report must be exactly "
                "ResearchStrategySpecialistSignalConsensusDecayReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        if type(self.config) is not ResearchStrategySpecialistSignalConsensusDecayConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchStrategySpecialistSignalConsensusDecayConfig",
            )
        object.__setattr__(self, "config", _revalidate_config(self.config))
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in (
            "input_signal_count",
            "consensus_row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "mean_consensus_decay_score",
            "max_probability_dispersion",
            "min_freshness_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        if type(self.derived_validation_digest) is not str:
            _require_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_strategy_specialist_signal_consensus_decay_report(
    inputs: object,
    *,
    config: ResearchStrategySpecialistSignalConsensusDecayConfig,
    generated_at: datetime,
) -> ResearchStrategySpecialistSignalConsensusDecayReport:
    if type(config) is not ResearchStrategySpecialistSignalConsensusDecayConfig:
        raise ValueError(
            "config must be a ResearchStrategySpecialistSignalConsensusDecayConfig",
        )
    config = _revalidate_config(config)
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at:
            raise ValueError("generated_at must not precede observed_at")
    rows = tuple(
        sorted(
            (
                _row_from_inputs(signal_ref, signal_inputs, config, generated_at)
                for signal_ref, signal_inputs in _group_inputs(normalized_inputs)
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchStrategySpecialistSignalConsensusDecayReport(
        generated_at=generated_at,
        config_version=config.config_version,
        config=config,
        input_signal_count=_count(len(normalized_inputs)),
        consensus_row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_consensus_decay_score=_mean_row_decimal(
            rows,
            "consensus_decay_score",
        ),
        max_probability_dispersion=_max_row_decimal(rows, "probability_dispersion"),
        min_freshness_score=_min_row_decimal(rows, "mean_freshness_score"),
        status=_report_status(rows),
        reason_codes=reason_codes,
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
    )


def research_strategy_specialist_signal_consensus_decay_report_payload(
    report: ResearchStrategySpecialistSignalConsensusDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategySpecialistSignalConsensusDecayReport:
        validated_report = _revalidate_report(report)
        _reject_unsafe_public("report", validated_report)
        payload = _json_ready(validated_report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _verify_payload_digest(payload)
        _validate_payload_semantics(payload)
        return payload
    if type(report) is dict:
        _require_exact_wire_payload(report)
        _reject_unsafe_public("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _reject_flag_downgrades("payload", payload)
        _verify_payload_digest(payload)
        _validate_payload_semantics(payload)
        _reject_unsafe_public("payload", payload)
        return payload
    raise ValueError(
        "report must be a ResearchStrategySpecialistSignalConsensusDecayReport",
    )


@dataclass(frozen=True, slots=True)
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


def _row_from_inputs(
    signal_ref: str,
    signal_inputs: tuple[ResearchStrategySpecialistSignalConsensusDecayInput, ...],
    config: ResearchStrategySpecialistSignalConsensusDecayConfig,
    generated_at: datetime,
) -> ResearchStrategySpecialistSignalConsensusDecayRow:
    with localcontext(_DECIMAL_CONTEXT):
        probabilities = tuple(item.probability_estimate for item in signal_inputs)
        freshness_scores = tuple(
            _freshness_score(
                item.observed_at,
                generated_at,
                config.stale_signal_block_seconds,
            )
            for item in signal_inputs
        )
        confidence_scores = tuple(item.confidence_score for item in signal_inputs)
        mean_confidence_score = _average(confidence_scores)
        mean_freshness_score = _average(freshness_scores)
        probability_dispersion = _quantize(max(probabilities) - min(probabilities))
        consensus_probability = _weighted_probability(signal_inputs, freshness_scores)
        consensus_decay_score = _consensus_decay_score(
            probability_dispersion=probability_dispersion,
            mean_confidence_score=mean_confidence_score,
            mean_freshness_score=mean_freshness_score,
        )
        specialist_count = _count(len(signal_inputs))
        reason_codes = _row_reason_codes(
            specialist_count=specialist_count,
            probability_dispersion=probability_dispersion,
            mean_freshness_score=mean_freshness_score,
            consensus_decay_score=consensus_decay_score,
            config=config,
        )
    return ResearchStrategySpecialistSignalConsensusDecayRow(
        signal_ref=signal_ref,
        observed_at=max(item.observed_at for item in signal_inputs),
        specialist_count=specialist_count,
        consensus_probability=consensus_probability,
        probability_dispersion=probability_dispersion,
        mean_confidence_score=mean_confidence_score,
        mean_freshness_score=mean_freshness_score,
        consensus_decay_score=consensus_decay_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _normalize_inputs(
    inputs: object,
) -> tuple[ResearchStrategySpecialistSignalConsensusDecayInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    normalized: list[ResearchStrategySpecialistSignalConsensusDecayInput] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not ResearchStrategySpecialistSignalConsensusDecayInput:
            raise ValueError(
                "inputs must contain "
                "ResearchStrategySpecialistSignalConsensusDecayInput",
            )
        validated = _revalidate_input(item)
        key = (validated.signal_ref, validated.specialist_ref)
        if key in seen:
            raise ValueError("inputs must contain unique signal_ref and specialist_ref pairs")
        seen.add(key)
        normalized.append(validated)
    return tuple(normalized)


def _revalidate_config(
    config: ResearchStrategySpecialistSignalConsensusDecayConfig,
) -> ResearchStrategySpecialistSignalConsensusDecayConfig:
    if type(config) is not ResearchStrategySpecialistSignalConsensusDecayConfig:
        raise ValueError(
            "config must be a ResearchStrategySpecialistSignalConsensusDecayConfig",
        )
    _require_canonical_decimal_storage(config)
    return ResearchStrategySpecialistSignalConsensusDecayConfig(
        **{field.name: getattr(config, field.name) for field in fields(config)},
    )


def _revalidate_input(
    item: ResearchStrategySpecialistSignalConsensusDecayInput,
) -> ResearchStrategySpecialistSignalConsensusDecayInput:
    _require_canonical_utc_storage("observed_at", item.observed_at)
    _require_canonical_decimal_storage(item)
    return ResearchStrategySpecialistSignalConsensusDecayInput(
        **{field.name: getattr(item, field.name) for field in fields(item)},
    )


def _revalidate_row(
    row: ResearchStrategySpecialistSignalConsensusDecayRow,
) -> ResearchStrategySpecialistSignalConsensusDecayRow:
    if type(row) is not ResearchStrategySpecialistSignalConsensusDecayRow:
        raise ValueError(
            "row must be a ResearchStrategySpecialistSignalConsensusDecayRow",
        )
    _require_canonical_utc_storage("observed_at", row.observed_at)
    _require_digest("derived_validation_digest", row.derived_validation_digest)
    _require_canonical_decimal_storage(row)
    return ResearchStrategySpecialistSignalConsensusDecayRow(
        **{field.name: getattr(row, field.name) for field in fields(row)},
    )


def _revalidate_reason_code_count(
    value: ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount,
) -> ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount:
    if type(value) is not ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount:
        raise ValueError(
            "reason_code_count must be a "
            "ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount",
        )
    _require_canonical_decimal_storage(value)
    return ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidate_report(
    report: ResearchStrategySpecialistSignalConsensusDecayReport,
) -> ResearchStrategySpecialistSignalConsensusDecayReport:
    if type(report) is not ResearchStrategySpecialistSignalConsensusDecayReport:
        raise ValueError(
            "report must be a ResearchStrategySpecialistSignalConsensusDecayReport",
        )
    _require_canonical_utc_storage("generated_at", report.generated_at)
    _require_digest("derived_validation_digest", report.derived_validation_digest)
    _require_canonical_decimal_storage(report)
    return ResearchStrategySpecialistSignalConsensusDecayReport(
        **{field.name: getattr(report, field.name) for field in fields(report)},
    )


def _require_canonical_decimal_storage(value: object) -> None:
    for field in fields(value):
        field_value = getattr(value, field.name)
        if isinstance(field_value, Decimal):
            raw_value = _require_raw_decimal(field.name, field_value)
            normalized = _quantize(raw_value)
            if raw_value.as_tuple() != normalized.as_tuple():
                raise ValueError(
                    f"{field.name} must be stored canonically at six decimals",
                )


def _group_inputs(
    inputs: tuple[ResearchStrategySpecialistSignalConsensusDecayInput, ...],
) -> tuple[
    tuple[str, tuple[ResearchStrategySpecialistSignalConsensusDecayInput, ...]],
    ...,
]:
    signal_refs = tuple(sorted({item.signal_ref for item in inputs}))
    return tuple(
        (
            signal_ref,
            tuple(
                sorted(
                    (item for item in inputs if item.signal_ref == signal_ref),
                    key=lambda item: item.specialist_ref,
                ),
            ),
        )
        for signal_ref in signal_refs
    )


def _freshness_score(
    observed_at: datetime,
    generated_at: datetime,
    stale_signal_block_seconds: Decimal,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        age = generated_at - observed_at
        age_seconds = _quantize(
            Decimal(age.days * 86400 + age.seconds)
            + (Decimal(age.microseconds) / Decimal("1000000")),
        )
        if age_seconds <= _ZERO:
            return _ONE
        if age_seconds >= stale_signal_block_seconds:
            return _ZERO
        return _clamp_probability(
            _ONE - _ratio(age_seconds, stale_signal_block_seconds),
        )


def _weighted_probability(
    signal_inputs: tuple[ResearchStrategySpecialistSignalConsensusDecayInput, ...],
    freshness_scores: tuple[Decimal, ...],
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        weights = tuple(
            _quantize(item.confidence_score * freshness_score)
            for item, freshness_score in zip(
                signal_inputs,
                freshness_scores,
                strict=True,
            )
        )
        weight_sum = sum(weights, _ZERO)
        if weight_sum == _ZERO:
            return _average(tuple(item.probability_estimate for item in signal_inputs))
        return _ratio(
            sum(
                item.probability_estimate * weight
                for item, weight in zip(signal_inputs, weights, strict=True)
            ),
            weight_sum,
        )


def _consensus_decay_score(
    *,
    probability_dispersion: Decimal,
    mean_confidence_score: Decimal,
    mean_freshness_score: Decimal,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        consensus_strength = _clamp_probability(_ONE - probability_dispersion)
        return _clamp_probability(
            consensus_strength * _CONSENSUS_STRENGTH_WEIGHT
            + mean_confidence_score * _CONFIDENCE_WEIGHT
            + mean_freshness_score * _FRESHNESS_WEIGHT,
        )


def _row_reason_codes(
    *,
    specialist_count: Decimal,
    probability_dispersion: Decimal,
    mean_freshness_score: Decimal,
    consensus_decay_score: Decimal,
    config: ResearchStrategySpecialistSignalConsensusDecayConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if specialist_count < config.minimum_specialist_count:
        reason_codes.append("specialist_quorum_block")
    if consensus_decay_score < config.consensus_watch_floor:
        reason_codes.append("consensus_decay_block")
    elif consensus_decay_score < config.consensus_pass_floor:
        reason_codes.append("consensus_decay_watch")
    if mean_freshness_score <= config.freshness_block_floor:
        reason_codes.append("specialist_freshness_block")
    elif mean_freshness_score < config.freshness_watch_floor:
        reason_codes.append("specialist_freshness_watch")
    if probability_dispersion > config.dispersion_block_ceiling:
        reason_codes.append("specialist_dispersion_block")
    elif probability_dispersion > config.dispersion_watch_ceiling:
        reason_codes.append("specialist_dispersion_watch")
    if not reason_codes:
        reason_codes.append("specialist_signal_consensus_decay_pass")
    return _sort_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategySpecialistSignalConsensusDecayRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategySpecialistSignalConsensusDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("specialist_signal_consensus_decay_report_clear",)
    status = _report_status(rows)
    reason_codes = [f"specialist_signal_consensus_decay_report_{status}"]
    row_reasons = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    if any(reason_code.startswith("consensus_decay_") for reason_code in row_reasons):
        reason_codes.append("consensus_decay_review")
    if any(reason_code.startswith("specialist_freshness_") for reason_code in row_reasons):
        reason_codes.append("specialist_freshness_review")
    if any(reason_code.startswith("specialist_dispersion_") for reason_code in row_reasons):
        reason_codes.append("specialist_dispersion_review")
    if any(reason_code.startswith("specialist_quorum_") for reason_code in row_reasons):
        reason_codes.append("specialist_quorum_review")
    return _sort_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchStrategySpecialistSignalConsensusDecayRow, ...],
) -> tuple[ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            input_ratio=_ratio(_count(count), denominator),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], _reason_sort_key(item[0])),
        )
    )


def _status_count(
    rows: tuple[ResearchStrategySpecialistSignalConsensusDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _mean_row_decimal(
    rows: tuple[ResearchStrategySpecialistSignalConsensusDecayRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _ZERO
    return _average(tuple(getattr(row, field_name) for row in rows))


def _max_row_decimal(
    rows: tuple[ResearchStrategySpecialistSignalConsensusDecayRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[ResearchStrategySpecialistSignalConsensusDecayRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _ZERO
    return min(getattr(row, field_name) for row in rows)


def _validate_row_reason_codes(
    row: ResearchStrategySpecialistSignalConsensusDecayRow,
) -> None:
    if row.reason_codes != _sort_reason_codes(row.reason_codes):
        raise ValueError("reason_codes must be sorted")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    pass_reason = "specialist_signal_consensus_decay_pass"
    if row.status == "pass" and row.reason_codes != (pass_reason,):
        raise ValueError("pass rows must use the pass reason")
    if row.status != "pass" and pass_reason in row.reason_codes:
        raise ValueError("non-pass rows must not use the pass reason")


def _validate_row_derived_score(
    row: ResearchStrategySpecialistSignalConsensusDecayRow,
) -> None:
    if row.specialist_count == _ONE and row.probability_dispersion != _ZERO:
        raise ValueError(
            "probability_dispersion must be zero for a single specialist",
        )
    expected_score = _consensus_decay_score(
        probability_dispersion=row.probability_dispersion,
        mean_confidence_score=row.mean_confidence_score,
        mean_freshness_score=row.mean_freshness_score,
    )
    if row.consensus_decay_score != expected_score:
        raise ValueError("consensus_decay_score must match row components")


def _validate_report(
    report: ResearchStrategySpecialistSignalConsensusDecayReport,
) -> None:
    rows = report.rows
    for row in rows:
        if row.observed_at > report.generated_at:
            raise ValueError("observed_at must not be after generated_at")
        latest_freshness_score = _freshness_score(
            row.observed_at,
            report.generated_at,
            report.config.stale_signal_block_seconds,
        )
        if row.specialist_count == _ONE:
            if row.mean_freshness_score != latest_freshness_score:
                raise ValueError(
                    "mean_freshness_score must match observed_at "
                    "for a single specialist",
                )
        elif row.mean_freshness_score > latest_freshness_score:
            raise ValueError(
                "mean_freshness_score must not exceed observed_at freshness",
            )
        expected_reason_codes = _row_reason_codes(
            specialist_count=row.specialist_count,
            probability_dispersion=row.probability_dispersion,
            mean_freshness_score=row.mean_freshness_score,
            consensus_decay_score=row.consensus_decay_score,
            config=report.config,
        )
        expected_status = _row_status(expected_reason_codes)
        if row.status != expected_status:
            raise ValueError("status must match config")
        if row.reason_codes != expected_reason_codes:
            raise ValueError("reason_codes must match config")
    with localcontext(_DECIMAL_CONTEXT):
        if report.input_signal_count != sum(
            (row.specialist_count for row in rows),
            _ZERO,
        ):
            raise ValueError("input_signal_count must match rows")
    if report.consensus_row_count != _count(len(rows)):
        raise ValueError("consensus_row_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_consensus_decay_score != _mean_row_decimal(
        rows,
        "consensus_decay_score",
    ):
        raise ValueError("mean_consensus_decay_score must match rows")
    if report.max_probability_dispersion != _max_row_decimal(
        rows,
        "probability_dispersion",
    ):
        raise ValueError("max_probability_dispersion must match rows")
    if report.min_freshness_score != _min_row_decimal(rows, "mean_freshness_score"):
        raise ValueError("min_freshness_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _row_sort_key(row: ResearchStrategySpecialistSignalConsensusDecayRow) -> tuple[int, str]:
    return (_STATUS_RANK[row.status], row.signal_ref)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategySpecialistSignalConsensusDecayRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchStrategySpecialistSignalConsensusDecayRow] = []
    for item in rows:
        if type(item) is not ResearchStrategySpecialistSignalConsensusDecayRow:
            raise ValueError(
                "rows must contain ResearchStrategySpecialistSignalConsensusDecayRow",
            )
        normalized.append(_revalidate_row(item))
    items = tuple(normalized)
    if items != tuple(sorted(items, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if len({item.signal_ref for item in items}) != len(items):
        raise ValueError("rows must not contain duplicate signal_ref values")
    return items


def _normalize_reason_code_counts(
    reason_code_counts: object,
) -> tuple[ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[
        ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount
    ] = []
    for item in reason_code_counts:
        if type(item) is not ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount",
            )
        normalized.append(_revalidate_reason_code_count(item))
    return tuple(normalized)


def _normalize_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    items = values
    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        _require_reason_code(name, item)
        if item in seen:
            raise ValueError(f"{name} must not contain duplicates")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(reason_codes, key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    return (_REASON_PRIORITY.get(reason_code, len(_REASON_PRIORITY)), reason_code)


def _row_digest(row: ResearchStrategySpecialistSignalConsensusDecayRow) -> str:
    value = asdict(row)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _report_digest(report: ResearchStrategySpecialistSignalConsensusDecayReport) -> str:
    value = asdict(report)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str or not digest:
        raise ValueError("derived_validation_digest is required")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _canonical_digest(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _validate_payload_semantics(payload: dict[str, Any]) -> None:
    _require_exact_payload_fields(
        "report",
        payload,
        _REPORT_PAYLOAD_FIELDS,
    )
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a JSON array")
    rows = tuple(_row_from_payload(item) for item in rows_value)
    reason_code_counts_value = payload["reason_code_counts"]
    if type(reason_code_counts_value) is not list:
        raise ValueError("reason_code_counts must be a JSON array")
    reason_code_counts = tuple(
        _reason_code_count_from_payload(item)
        for item in reason_code_counts_value
    )
    config = _config_from_payload(payload["config"])
    ResearchStrategySpecialistSignalConsensusDecayReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        config=config,
        input_signal_count=_payload_decimal(
            "input_signal_count",
            payload["input_signal_count"],
        ),
        consensus_row_count=_payload_decimal(
            "consensus_row_count",
            payload["consensus_row_count"],
        ),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        mean_consensus_decay_score=_payload_decimal(
            "mean_consensus_decay_score",
            payload["mean_consensus_decay_score"],
        ),
        max_probability_dispersion=_payload_decimal(
            "max_probability_dispersion",
            payload["max_probability_dispersion"],
        ),
        min_freshness_score=_payload_decimal(
            "min_freshness_score",
            payload["min_freshness_score"],
        ),
        status=payload["status"],
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        rows=rows,
        reason_code_counts=reason_code_counts,
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _config_from_payload(
    value: object,
) -> ResearchStrategySpecialistSignalConsensusDecayConfig:
    if type(value) is not dict:
        raise ValueError("config payload must be a JSON object")
    _require_exact_payload_fields("config", value, _CONFIG_PAYLOAD_FIELDS)
    return ResearchStrategySpecialistSignalConsensusDecayConfig(
        config_version=value["config_version"],
        consensus_pass_floor=_payload_decimal(
            "consensus_pass_floor",
            value["consensus_pass_floor"],
        ),
        consensus_watch_floor=_payload_decimal(
            "consensus_watch_floor",
            value["consensus_watch_floor"],
        ),
        freshness_watch_floor=_payload_decimal(
            "freshness_watch_floor",
            value["freshness_watch_floor"],
        ),
        freshness_block_floor=_payload_decimal(
            "freshness_block_floor",
            value["freshness_block_floor"],
        ),
        dispersion_watch_ceiling=_payload_decimal(
            "dispersion_watch_ceiling",
            value["dispersion_watch_ceiling"],
        ),
        dispersion_block_ceiling=_payload_decimal(
            "dispersion_block_ceiling",
            value["dispersion_block_ceiling"],
        ),
        stale_signal_block_seconds=_payload_decimal(
            "stale_signal_block_seconds",
            value["stale_signal_block_seconds"],
        ),
        minimum_specialist_count=_payload_decimal(
            "minimum_specialist_count",
            value["minimum_specialist_count"],
        ),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _row_from_payload(
    value: object,
) -> ResearchStrategySpecialistSignalConsensusDecayRow:
    if type(value) is not dict:
        raise ValueError("row payload must be a JSON object")
    _require_exact_payload_fields("row", value, _ROW_PAYLOAD_FIELDS)
    return ResearchStrategySpecialistSignalConsensusDecayRow(
        signal_ref=value["signal_ref"],
        observed_at=_payload_datetime("observed_at", value["observed_at"]),
        specialist_count=_payload_decimal(
            "specialist_count",
            value["specialist_count"],
        ),
        consensus_probability=_payload_decimal(
            "consensus_probability",
            value["consensus_probability"],
        ),
        probability_dispersion=_payload_decimal(
            "probability_dispersion",
            value["probability_dispersion"],
        ),
        mean_confidence_score=_payload_decimal(
            "mean_confidence_score",
            value["mean_confidence_score"],
        ),
        mean_freshness_score=_payload_decimal(
            "mean_freshness_score",
            value["mean_freshness_score"],
        ),
        consensus_decay_score=_payload_decimal(
            "consensus_decay_score",
            value["consensus_decay_score"],
        ),
        status=value["status"],
        reason_codes=_payload_string_tuple("reason_codes", value["reason_codes"]),
        derived_validation_digest=value["derived_validation_digest"],
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _reason_code_count_from_payload(
    value: object,
) -> ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount:
    if type(value) is not dict:
        raise ValueError("reason code count payload must be a JSON object")
    _require_exact_payload_fields(
        "reason code count",
        value,
        _REASON_CODE_COUNT_PAYLOAD_FIELDS,
    )
    return ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount(
        reason_code=value["reason_code"],
        count=_payload_decimal("count", value["count"]),
        input_ratio=_payload_decimal("input_ratio", value["input_ratio"]),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _require_exact_payload_fields(
    label: str,
    payload: dict[str, Any],
    expected_fields: tuple[str, ...],
) -> None:
    if tuple(payload) != expected_fields:
        raise ValueError(f"{label} payload fields must match exact schema")


def _require_exact_wire_payload(payload: dict[str, Any]) -> None:
    _require_wire_object("report", payload, _REPORT_PAYLOAD_FIELDS)
    for field_name in (
        "generated_at",
        "config_version",
        "status",
        "derived_validation_digest",
    ):
        _require_wire_string(payload[field_name])
    for field_name in (
        "input_signal_count",
        "consensus_row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_consensus_decay_score",
        "max_probability_dispersion",
        "min_freshness_score",
    ):
        _require_wire_string(payload[field_name])
    _require_wire_string_array(payload["reason_codes"])
    _require_wire_flags(payload)

    config = _require_wire_object(
        "config",
        payload["config"],
        _CONFIG_PAYLOAD_FIELDS,
    )
    _require_wire_string(config["config_version"])
    for field_name in (
        "consensus_pass_floor",
        "consensus_watch_floor",
        "freshness_watch_floor",
        "freshness_block_floor",
        "dispersion_watch_ceiling",
        "dispersion_block_ceiling",
        "stale_signal_block_seconds",
        "minimum_specialist_count",
    ):
        _require_wire_string(config[field_name])
    _require_wire_flags(config)

    rows = _require_wire_array(payload["rows"])
    for row_value in rows:
        row = _require_wire_object("row", row_value, _ROW_PAYLOAD_FIELDS)
        for field_name in (
            "signal_ref",
            "observed_at",
            "status",
            "derived_validation_digest",
        ):
            _require_wire_string(row[field_name])
        for field_name in (
            "specialist_count",
            "consensus_probability",
            "probability_dispersion",
            "mean_confidence_score",
            "mean_freshness_score",
            "consensus_decay_score",
        ):
            _require_wire_string(row[field_name])
        _require_wire_string_array(row["reason_codes"])
        _require_wire_flags(row)

    reason_code_counts = _require_wire_array(payload["reason_code_counts"])
    for count_value in reason_code_counts:
        count = _require_wire_object(
            "reason code count",
            count_value,
            _REASON_CODE_COUNT_PAYLOAD_FIELDS,
        )
        for field_name in ("reason_code", "count", "input_ratio"):
            _require_wire_string(count[field_name])
        _require_wire_flags(count)


def _require_wire_object(
    label: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError("payload must use exact JSON types")
    if any(type(key) is not str for key in value):
        raise ValueError("payload must use exact JSON types")
    _require_exact_payload_fields(label, value, expected_fields)
    return value


def _require_wire_array(value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError("payload must use exact JSON types")
    return value


def _require_wire_string(value: object) -> None:
    if type(value) is not str:
        raise ValueError("payload must use exact JSON types")


def _require_wire_string_array(value: object) -> None:
    for item in _require_wire_array(value):
        _require_wire_string(item)


def _require_wire_flags(value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if type(value[field_name]) is not bool:
            raise ValueError("payload must use exact JSON types")


def _payload_decimal(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{name} must be finite")
    if parsed.is_zero() and parsed.is_signed():
        raise ValueError(f"{name} must not use signed zero")
    normalized = _quantize(parsed)
    if format(normalized, "f") != value:
        raise ValueError(f"{name} must be a canonical Decimal string")
    return normalized


def _payload_datetime(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string") from exc
    normalized = _as_utc(name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{name} must be a canonical UTC datetime string")
    return normalized


def _payload_string_tuple(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a JSON array")
    return tuple(value)


def _canonical_digest(payload: object) -> str:
    encoded = json.dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}")
            _reject_unsafe_public(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public(label, item)


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_flag_downgrades(label, item)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must not be empty")
    with localcontext(_DECIMAL_CONTEXT):
        return _ratio(sum(values, _ZERO), _count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        raise ValueError("ratio denominator must be non-zero")
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _clamp_probability(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return min(_ONE, max(_ZERO, _quantize(value)))


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be non-negative")
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    try:
        with localcontext(_DECIMAL_CONTEXT):
            normalized = value.quantize(_QUANT, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError("value must be representable at six decimals") from exc
    if normalized.is_zero():
        return _ZERO
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    return _quantize(_require_raw_decimal(name, value))


def _require_raw_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{name} must not use signed zero")
    return value


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value <= _ZERO:
        raise ValueError(f"{name} must be positive")
    normalized = _quantize(raw_value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value < _ZERO:
        raise ValueError(f"{name} must be non-negative")
    return _quantize(raw_value)


def _normalize_probability_decimal(name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value < _ZERO or raw_value > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(raw_value)


def _normalize_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value < _ZERO:
        raise ValueError(f"{name} must be non-negative")
    if raw_value != raw_value.to_integral_value():
        raise ValueError(f"{name} must be a whole number")
    return _quantize(raw_value)


def _normalize_positive_whole_decimal(name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value <= _ZERO:
        raise ValueError(f"{name} must be positive")
    if raw_value != raw_value.to_integral_value():
        raise ValueError(f"{name} must be a whole number")
    return _quantize(raw_value)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    try:
        offset = value.utcoffset()
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must have a valid timezone offset") from exc
    if offset is None:
        raise ValueError(f"{name} must be timezone-aware")
    try:
        return value.astimezone(UTC)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must have a valid timezone offset") from exc


def _require_canonical_utc_storage(name: str, value: object) -> None:
    if type(value) is not datetime or value.tzinfo is not UTC:
        raise ValueError(f"{name} must be canonical UTC datetime")


def _require_public_identifier(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a canonical public identifier")
    if _has_unsafe_fragment(value):
        raise ValueError(f"unsafe value in {name}")


def _require_reason_code(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in _REASON_PRIORITY:
        raise ValueError(f"{name} must be a supported reason code")


def _require_row_reason_code(name: str, value: object) -> None:
    _require_reason_code(name, value)
    if value not in _ROW_REASON_PRIORITY:
        raise ValueError(f"{name} must be a supported row reason code")


def _require_status(name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_SPECIALIST_SIGNAL_CONSENSUS_DECAY_STATUSES
    ):
        raise ValueError(f"{name} must be a supported status")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a sha256 hex digest")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SPECIALIST_SIGNAL_CONSENSUS_DECAY_CONFIG_VERSION",
    "RESEARCH_STRATEGY_SPECIALIST_SIGNAL_CONSENSUS_DECAY_STATUSES",
    "ResearchStrategySpecialistSignalConsensusDecayConfig",
    "ResearchStrategySpecialistSignalConsensusDecayInput",
    "ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount",
    "ResearchStrategySpecialistSignalConsensusDecayReport",
    "ResearchStrategySpecialistSignalConsensusDecayRow",
    "build_research_strategy_specialist_signal_consensus_decay_report",
    "research_strategy_specialist_signal_consensus_decay_report_payload",
)
