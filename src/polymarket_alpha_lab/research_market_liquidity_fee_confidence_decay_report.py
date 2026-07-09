from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_FEE_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION",
    "ResearchMarketLiquidityFeeConfidenceDecayConfig",
    "ResearchMarketLiquidityFeeConfidenceDecayObservation",
    "ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount",
    "ResearchMarketLiquidityFeeConfidenceDecayReport",
    "ResearchMarketLiquidityFeeConfidenceDecayRow",
    "build_research_market_liquidity_fee_confidence_decay_report",
    "research_market_liquidity_fee_confidence_decay_report_payload",
)


DEFAULT_RESEARCH_MARKET_LIQUIDITY_FEE_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION = (
    "research-market-liquidity-fee-confidence-decay-report-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
NO_INPUTS_REASON = "research_market_liquidity_fee_confidence_decay_no_inputs"
ROW_REASON_CODE_SEQUENCE = (
    "confidence_decay_block",
    "confidence_decay_watch",
    "depth_score_block",
    "depth_score_watch",
    "fee_cost_block",
    "fee_cost_watch",
    "spread_cost_block",
    "spread_cost_watch",
    "total_cost_block",
    "total_cost_watch",
    "liquidity_fee_confidence_decay_clear",
)
ROW_REASON_CODES = frozenset(ROW_REASON_CODE_SEQUENCE)
REASON_CODE_COUNT_CODES = ROW_REASON_CODES | frozenset((NO_INPUTS_REASON,))
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "d" + "b",
    "net" + "work",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "li" + "ve",
    "trad" + "ing",
    "siz" + "ing",
    "reco" + "mmendation",
    "cand" + "idate",
    "sour" + "ce",
    "u" + "rl",
    "te" + "xt",
    "d" + "sn",
    "ta" + "ble",
    "tok" + "en",
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
class ResearchMarketLiquidityFeeConfidenceDecayConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_FEE_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION
    )
    spread_watch_bps: Decimal = Decimal("20.000000")
    spread_block_bps: Decimal = Decimal("50.000000")
    fee_watch_bps: Decimal = Decimal("8.000000")
    fee_block_bps: Decimal = Decimal("18.000000")
    total_cost_watch_bps: Decimal = Decimal("30.000000")
    total_cost_block_bps: Decimal = Decimal("60.000000")
    depth_pass_floor: Decimal = Decimal("0.650000")
    depth_watch_floor: Decimal = Decimal("0.350000")
    confidence_pass_floor: Decimal = Decimal("0.700000")
    confidence_watch_floor: Decimal = Decimal("0.400000")
    confidence_decay_window_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityFeeConfidenceDecayConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_FEE_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "spread_watch_bps",
            "spread_block_bps",
            "fee_watch_bps",
            "fee_block_bps",
            "total_cost_watch_bps",
            "total_cost_block_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_pass_floor",
            "depth_watch_floor",
            "confidence_pass_floor",
            "confidence_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_decay_window_seconds",
            _normalize_positive_decimal(
                "confidence_decay_window_seconds",
                self.confidence_decay_window_seconds,
            ),
        )
        _require_at_most("spread_watch_bps", self.spread_watch_bps, self.spread_block_bps)
        _require_at_most("fee_watch_bps", self.fee_watch_bps, self.fee_block_bps)
        _require_at_most(
            "total_cost_watch_bps",
            self.total_cost_watch_bps,
            self.total_cost_block_bps,
        )
        _require_at_most("depth_watch_floor", self.depth_watch_floor, self.depth_pass_floor)
        _require_at_most(
            "confidence_watch_floor",
            self.confidence_watch_floor,
            self.confidence_pass_floor,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityFeeConfidenceDecayObservation(_FinalPublicDataclass):
    observation_id: str
    spread_bps: Decimal
    fee_bps: Decimal
    depth_score: Decimal
    confidence_score: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityFeeConfidenceDecayObservation,
            "observation",
        )
        _require_public_identifier("observation_id", self.observation_id)
        for field_name in ("spread_bps", "fee_bps"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("depth_score", "confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityFeeConfidenceDecayRow(_FinalPublicDataclass):
    observation_digest: str
    observed_at: datetime
    age_seconds: Decimal
    spread_bps: Decimal
    fee_bps: Decimal
    total_cost_bps: Decimal
    depth_score: Decimal
    confidence_score: Decimal
    confidence_decay_multiplier: Decimal
    adjusted_confidence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityFeeConfidenceDecayRow, "row")
        _require_sha256_digest("observation_digest", self.observation_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "age_seconds",
            "spread_bps",
            "fee_bps",
            "total_cost_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_score",
            "confidence_score",
            "confidence_decay_multiplier",
            "adjusted_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount,
            "reason_code_count",
        )
        _require_public_identifier("reason_code", self.reason_code)
        if self.reason_code not in REASON_CODE_COUNT_CODES:
            raise ValueError("reason_code must use supported report vocabulary")
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityFeeConfidenceDecayReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_total_cost_bps: Decimal
    max_total_cost_bps: Decimal
    mean_adjusted_confidence_score: Decimal
    min_adjusted_confidence_score: Decimal
    rows: tuple[ResearchMarketLiquidityFeeConfidenceDecayRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityFeeConfidenceDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_FEE_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "mean_total_cost_bps",
            "max_total_cost_bps",
            "mean_adjusted_confidence_score",
            "min_adjusted_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        return research_market_liquidity_fee_confidence_decay_report_payload(self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchMarketLiquidityFeeConfidenceDecayConfig,
    ResearchMarketLiquidityFeeConfidenceDecayObservation,
    ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount,
    ResearchMarketLiquidityFeeConfidenceDecayReport,
    ResearchMarketLiquidityFeeConfidenceDecayRow,
)
_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_total_cost_bps",
        "max_total_cost_bps",
        "mean_adjusted_confidence_score",
        "min_adjusted_confidence_score",
        "rows",
        "reason_codes",
        "reason_code_counts",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_KEYS = frozenset(
    (
        "observation_digest",
        "observed_at",
        "age_seconds",
        "spread_bps",
        "fee_bps",
        "total_cost_bps",
        "depth_score",
        "confidence_score",
        "confidence_decay_multiplier",
        "adjusted_confidence_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REASON_CODE_COUNT_PAYLOAD_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


def build_research_market_liquidity_fee_confidence_decay_report(
    observations: Iterable[ResearchMarketLiquidityFeeConfidenceDecayObservation],
    *,
    config: ResearchMarketLiquidityFeeConfidenceDecayConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityFeeConfidenceDecayReport:
    if type(config) is not ResearchMarketLiquidityFeeConfidenceDecayConfig:
        raise ValueError(
            "config must be a ResearchMarketLiquidityFeeConfidenceDecayConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_for_observation(
                    observation=row,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for row in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _rollup_status(tuple(row.status for row in rows)),
        "observation_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "mean_total_cost_bps": _mean(tuple(row.total_cost_bps for row in rows)),
        "max_total_cost_bps": _max_decimal(tuple(row.total_cost_bps for row in rows)),
        "mean_adjusted_confidence_score": _mean(
            tuple(row.adjusted_confidence_score for row in rows),
        ),
        "min_adjusted_confidence_score": _min_decimal(
            tuple(row.adjusted_confidence_score for row in rows),
        ),
        "rows": rows,
        "reason_codes": _rollup_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketLiquidityFeeConfidenceDecayReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_market_liquidity_fee_confidence_decay_report_payload(
    value: ResearchMarketLiquidityFeeConfidenceDecayReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchMarketLiquidityFeeConfidenceDecayReport:
        _require_payload_safe_value("report", value)
        _reject_unsafe_public_payload("report", value)
        payload = _json_ready(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchMarketLiquidityFeeConfidenceDecayReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _validate_public_payload_digest(payload)
    _validate_public_payload_schema(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_for_observation(
    *,
    observation: ResearchMarketLiquidityFeeConfidenceDecayObservation,
    config: ResearchMarketLiquidityFeeConfidenceDecayConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityFeeConfidenceDecayRow:
    age_seconds = _age_seconds(generated_at, observation.observed_at)
    decay_multiplier = _decay_multiplier(age_seconds, config.confidence_decay_window_seconds)
    adjusted_confidence_score = _quantize(
        observation.confidence_score * decay_multiplier,
    )
    total_cost_bps = _quantize(observation.spread_bps + observation.fee_bps)
    reason_codes = _row_reason_codes(
        spread_bps=observation.spread_bps,
        fee_bps=observation.fee_bps,
        total_cost_bps=total_cost_bps,
        depth_score=observation.depth_score,
        adjusted_confidence_score=adjusted_confidence_score,
        config=config,
    )
    return ResearchMarketLiquidityFeeConfidenceDecayRow(
        observation_digest=_sha256_text(observation.observation_id),
        observed_at=observation.observed_at,
        age_seconds=age_seconds,
        spread_bps=observation.spread_bps,
        fee_bps=observation.fee_bps,
        total_cost_bps=total_cost_bps,
        depth_score=observation.depth_score,
        confidence_score=observation.confidence_score,
        confidence_decay_multiplier=decay_multiplier,
        adjusted_confidence_score=adjusted_confidence_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    spread_bps: Decimal,
    fee_bps: Decimal,
    total_cost_bps: Decimal,
    depth_score: Decimal,
    adjusted_confidence_score: Decimal,
    config: ResearchMarketLiquidityFeeConfidenceDecayConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if adjusted_confidence_score < config.confidence_watch_floor:
        reason_codes.append("confidence_decay_block")
    elif adjusted_confidence_score < config.confidence_pass_floor:
        reason_codes.append("confidence_decay_watch")
    if depth_score < config.depth_watch_floor:
        reason_codes.append("depth_score_block")
    elif depth_score < config.depth_pass_floor:
        reason_codes.append("depth_score_watch")
    if fee_bps >= config.fee_block_bps:
        reason_codes.append("fee_cost_block")
    elif fee_bps >= config.fee_watch_bps:
        reason_codes.append("fee_cost_watch")
    if spread_bps >= config.spread_block_bps:
        reason_codes.append("spread_cost_block")
    elif spread_bps >= config.spread_watch_bps:
        reason_codes.append("spread_cost_watch")
    if total_cost_bps >= config.total_cost_block_bps:
        reason_codes.append("total_cost_block")
    elif total_cost_bps >= config.total_cost_watch_bps:
        reason_codes.append("total_cost_watch")
    if not reason_codes:
        reason_codes.append("liquidity_fee_confidence_decay_clear")
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
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


def _rollup_reason_codes(
    rows: tuple[ResearchMarketLiquidityFeeConfidenceDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = [
        f"research_market_liquidity_fee_confidence_decay_{status}",
    ]
    row_reason_codes = frozenset(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    for reason_code in (
        "confidence_decay_block",
        "confidence_decay_watch",
        "depth_score_block",
        "depth_score_watch",
        "fee_cost_block",
        "fee_cost_watch",
        "spread_cost_block",
        "spread_cost_watch",
        "total_cost_block",
        "total_cost_watch",
    ):
        if reason_code in row_reason_codes:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchMarketLiquidityFeeConfidenceDecayRow, ...],
) -> tuple[ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_observations(
    observations: Iterable[ResearchMarketLiquidityFeeConfidenceDecayObservation],
) -> tuple[ResearchMarketLiquidityFeeConfidenceDecayObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        rows = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketLiquidityFeeConfidenceDecayObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketLiquidityFeeConfidenceDecayObservation values",
            )
        _require_hard_flags("observation", row)
        if row.observation_id in seen_ids:
            raise ValueError("observations must not contain duplicate observation_id values")
        seen_ids.add(row.observation_id)
    return rows


def _normalize_rows(
    rows: Iterable[ResearchMarketLiquidityFeeConfidenceDecayRow],
) -> tuple[ResearchMarketLiquidityFeeConfidenceDecayRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_digests: set[str] = set()
    for row in values:
        if type(row) is not ResearchMarketLiquidityFeeConfidenceDecayRow:
            raise ValueError(
                "rows must contain ResearchMarketLiquidityFeeConfidenceDecayRow values",
            )
        _require_hard_flags("row", row)
        if row.observation_digest in seen_digests:
            raise ValueError("rows must not contain duplicate observation_digest values")
        seen_digests.add(row.observation_digest)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount],
) -> tuple[ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    if values != tuple(sorted(values, key=lambda item: (-item.count, item.reason_code))):
        raise ValueError("reason_code_counts must be sorted by count then reason_code")
    return values


def _row_sort_key(
    row: ResearchMarketLiquidityFeeConfidenceDecayRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.total_cost_bps,
        row.adjusted_confidence_score,
        row.observation_digest,
    )


def _status_count(
    rows: tuple[ResearchMarketLiquidityFeeConfidenceDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _validate_row_consistency(
    row: ResearchMarketLiquidityFeeConfidenceDecayRow,
) -> None:
    if row.total_cost_bps != _quantize(row.spread_bps + row.fee_bps):
        raise ValueError("total_cost_bps must match spread_bps and fee_bps")
    if row.adjusted_confidence_score != _quantize(
        row.confidence_score * row.confidence_decay_multiplier,
    ):
        raise ValueError(
            "adjusted_confidence_score must match confidence_score and "
            "confidence_decay_multiplier",
        )
    _validate_row_reason_codes(row.reason_codes)
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_row_reason_codes(reason_codes: tuple[str, ...]) -> None:
    if any(reason_code not in ROW_REASON_CODES for reason_code in reason_codes):
        raise ValueError("reason_codes must use supported row vocabulary")
    canonical_reason_codes = tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )
    if reason_codes != canonical_reason_codes:
        raise ValueError("reason_codes must use canonical row sequence")
    if (
        "liquidity_fee_confidence_decay_clear" in reason_codes
        and len(reason_codes) != 1
    ):
        raise ValueError("reason_codes must not mix clear with watch or block reasons")


def _validate_report_consistency(
    report: ResearchMarketLiquidityFeeConfidenceDecayReport,
) -> None:
    rows = report.rows
    for row in rows:
        if row.age_seconds != _age_seconds(report.generated_at, row.observed_at):
            raise ValueError("age_seconds must match generated_at and observed_at")
    if report.observation_count != _count(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_total_cost_bps != _mean(tuple(row.total_cost_bps for row in rows)):
        raise ValueError("mean_total_cost_bps must match rows")
    if report.max_total_cost_bps != _max_decimal(tuple(row.total_cost_bps for row in rows)):
        raise ValueError("max_total_cost_bps must match rows")
    if report.mean_adjusted_confidence_score != _mean(
        tuple(row.adjusted_confidence_score for row in rows),
    ):
        raise ValueError("mean_adjusted_confidence_score must match rows")
    if report.min_adjusted_confidence_score != _min_decimal(
        tuple(row.adjusted_confidence_score for row in rows),
    ):
        raise ValueError("min_adjusted_confidence_score must match rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * Decimal("86400")
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / Decimal("1000000"))
        )
    age_seconds = _quantize(seconds)
    if age_seconds < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return age_seconds


def _decay_multiplier(age_seconds: Decimal, decay_window_seconds: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(ONE / (ONE + (age_seconds / decay_window_seconds)))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _clamp_probability(value: Decimal) -> Decimal:
    decimal_value = _quantize(value)
    if decimal_value < ZERO:
        return ZERO
    if decimal_value > ONE:
        return ONE
    return decimal_value


def _require_at_most(field_name: str, value: Decimal, ceiling: Decimal) -> None:
    if value > ceiling:
        raise ValueError(f"{field_name} must not exceed ceiling")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    lowered = value.lower()
    if _has_unsafe_public_fragment(lowered):
        raise ValueError(f"{field_name} contains unsafe public fragment")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be public-safe")
    return value


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen_codes: set[str] = set()
    for reason_code in values:
        _require_public_identifier("reason_code", reason_code)
        if reason_code in seen_codes:
            raise ValueError("reason_codes must not contain duplicates")
        seen_codes.add(reason_code)
    return values


def _require_sha256_digest(field_name: str, value: object) -> None:
    if not _is_sha256_digest(value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchMarketLiquidityFeeConfidenceDecayReport,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "status": report.status,
        "observation_count": report.observation_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "mean_total_cost_bps": report.mean_total_cost_bps,
        "max_total_cost_bps": report.max_total_cost_bps,
        "mean_adjusted_confidence_score": report.mean_adjusted_confidence_score,
        "min_adjusted_confidence_score": report.min_adjusted_confidence_score,
        "rows": report.rows,
        "reason_codes": report.reason_codes,
        "reason_code_counts": report.reason_code_counts,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("derived_validation_digest payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_public_payload_digest(payload: Mapping[str, object]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    expected_digest = _report_digest_from_values(payload_without_digest)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match payload")


def _validate_public_payload_schema(payload: Mapping[str, object]) -> None:
    _require_payload_keys("payload", payload, _REPORT_PAYLOAD_KEYS)
    report = ResearchMarketLiquidityFeeConfidenceDecayReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        status=_payload_string("status", payload["status"]),
        observation_count=_payload_decimal(
            "observation_count",
            payload["observation_count"],
        ),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        mean_total_cost_bps=_payload_decimal(
            "mean_total_cost_bps",
            payload["mean_total_cost_bps"],
        ),
        max_total_cost_bps=_payload_decimal(
            "max_total_cost_bps",
            payload["max_total_cost_bps"],
        ),
        mean_adjusted_confidence_score=_payload_decimal(
            "mean_adjusted_confidence_score",
            payload["mean_adjusted_confidence_score"],
        ),
        min_adjusted_confidence_score=_payload_decimal(
            "min_adjusted_confidence_score",
            payload["min_adjusted_confidence_score"],
        ),
        rows=_payload_rows(payload["rows"]),
        reason_codes=_payload_strings("reason_codes", payload["reason_codes"]),
        reason_code_counts=_payload_reason_code_counts(
            payload["reason_code_counts"],
        ),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    if _json_ready(report) != payload:
        raise ValueError("payload must match public schema")


def _payload_rows(value: object) -> tuple[ResearchMarketLiquidityFeeConfidenceDecayRow, ...]:
    return tuple(
        _payload_row(f"rows[{index}]", item)
        for index, item in enumerate(_payload_sequence("rows", value))
    )


def _payload_row(
    label: str,
    value: object,
) -> ResearchMarketLiquidityFeeConfidenceDecayRow:
    row = _payload_mapping(label, value)
    _require_payload_keys(label, row, _ROW_PAYLOAD_KEYS)
    return ResearchMarketLiquidityFeeConfidenceDecayRow(
        observation_digest=_payload_string(
            f"{label}.observation_digest",
            row["observation_digest"],
        ),
        observed_at=_payload_datetime(f"{label}.observed_at", row["observed_at"]),
        age_seconds=_payload_decimal(f"{label}.age_seconds", row["age_seconds"]),
        spread_bps=_payload_decimal(f"{label}.spread_bps", row["spread_bps"]),
        fee_bps=_payload_decimal(f"{label}.fee_bps", row["fee_bps"]),
        total_cost_bps=_payload_decimal(
            f"{label}.total_cost_bps",
            row["total_cost_bps"],
        ),
        depth_score=_payload_decimal(f"{label}.depth_score", row["depth_score"]),
        confidence_score=_payload_decimal(
            f"{label}.confidence_score",
            row["confidence_score"],
        ),
        confidence_decay_multiplier=_payload_decimal(
            f"{label}.confidence_decay_multiplier",
            row["confidence_decay_multiplier"],
        ),
        adjusted_confidence_score=_payload_decimal(
            f"{label}.adjusted_confidence_score",
            row["adjusted_confidence_score"],
        ),
        status=_payload_string(f"{label}.status", row["status"]),
        reason_codes=_payload_strings(f"{label}.reason_codes", row["reason_codes"]),
        paper_only=row["paper_only"],
        report_only=row["report_only"],
        readonly=row["readonly"],
    )


def _payload_reason_code_counts(
    value: object,
) -> tuple[ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount, ...]:
    return tuple(
        _payload_reason_code_count(f"reason_code_counts[{index}]", item)
        for index, item in enumerate(_payload_sequence("reason_code_counts", value))
    )


def _payload_reason_code_count(
    label: str,
    value: object,
) -> ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount:
    row = _payload_mapping(label, value)
    _require_payload_keys(label, row, _REASON_CODE_COUNT_PAYLOAD_KEYS)
    return ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount(
        reason_code=_payload_string(f"{label}.reason_code", row["reason_code"]),
        count=_payload_decimal(f"{label}.count", row["count"]),
        paper_only=row["paper_only"],
        report_only=row["report_only"],
        readonly=row["readonly"],
    )


def _payload_mapping(label: str, value: object) -> Mapping[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{label} must match public schema")
    return value


def _payload_sequence(label: str, value: object) -> tuple[object, ...]:
    if type(value) is not list:
        raise ValueError(f"{label} must match public schema")
    return tuple(value)


def _payload_strings(label: str, value: object) -> tuple[str, ...]:
    return tuple(
        _payload_string(f"{label}[{index}]", item)
        for index, item in enumerate(_payload_sequence(label, value))
    )


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a six decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a six decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    _require_six_decimal_decimal(field_name, decimal_value)
    if format(decimal_value, "f") != value:
        raise ValueError(f"{field_name} must be a canonical decimal string")
    return decimal_value


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    parsed_utc = _as_utc(field_name, parsed)
    if parsed_utc.isoformat() != value:
        raise ValueError(f"{field_name} must be canonical UTC")
    return parsed_utc


def _require_payload_keys(
    label: str,
    value: Mapping[str, object],
    expected_keys: frozenset[str],
) -> None:
    if frozenset(value) != expected_keys:
        raise ValueError(f"{label} must match public schema")


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
        for field in fields(value):
            _require_payload_safe_value(f"{label}.{field.name}", getattr(value, field.name))
        if type(value) is ResearchMarketLiquidityFeeConfidenceDecayReport:
            _validate_report_consistency(value)
        if type(value) is ResearchMarketLiquidityFeeConfidenceDecayRow:
            _validate_row_consistency(value)
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(label, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{label}[{index}]", item)
        return
    if value is None or type(value) in (bool, str):
        return
    raise ValueError(f"{label} contains unsupported value")


def _require_six_decimal_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be six decimal")
    if value != _quantize(value):
        raise ValueError(f"{field_name} must be six decimal")


def _require_utc_datetime(field_name: str, value: object) -> None:
    if type(value) is not datetime or value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if value is None or type(value) in (bool, str):
        return value
    raise ValueError("value is not public-payload safe")


def _copy_json_object(value: Mapping[str, object]) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError("payload must be a dict")
    return {
        key: _copy_public_json_value(f"payload.{key}", item)
        for key, item in value.items()
        if _require_json_key("payload", key)
    }


def _copy_public_json_value(label: str, value: object) -> object:
    if type(value) is dict:
        return {
            key: _copy_public_json_value(f"{label}.{key}", item)
            for key, item in value.items()
            if _require_json_key(label, key)
        }
    if type(value) is list:
        return [
            _copy_public_json_value(f"{label}[{index}]", item)
            for index, item in enumerate(value)
        ]
    if value is None or type(value) in (bool, str):
        return value
    if type(value) in (Decimal, int):
        raise ValueError(f"{label} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{label} must not be a float")
    if isinstance(value, datetime):
        raise ValueError(f"{label} must use datetime string values")
    raise ValueError(f"{label} contains unsupported public JSON value")


def _require_json_key(label: str, key: object) -> bool:
    if type(key) is not str:
        raise ValueError(f"{label} keys must be strings")
    return True


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name.lower()):
                raise ValueError(f"{label}.{field.name} contains unsafe public fragment")
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            if _has_unsafe_public_fragment(key.lower()):
                raise ValueError(f"{label}.{key} contains unsafe public fragment")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if _is_sha256_digest(value):
        return
    if type(value) is str and _has_unsafe_public_fragment(value.lower()):
        raise ValueError(f"{label} contains unsafe public fragment")


def _has_unsafe_public_fragment(value: str) -> bool:
    return any(fragment in value for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _is_sha256_digest(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
