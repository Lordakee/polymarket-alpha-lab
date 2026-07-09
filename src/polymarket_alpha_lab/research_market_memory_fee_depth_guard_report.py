"""Deterministic report-only memory fee depth guard."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any


__all__ = (
    "ResearchMarketMemoryFeeDepthGuardConfig",
    "ResearchMarketMemoryFeeDepthGuardObservation",
    "ResearchMarketMemoryFeeDepthGuardReport",
    "ResearchMarketMemoryFeeDepthGuardRow",
    "build_research_market_memory_fee_depth_guard_report",
    "research_market_memory_fee_depth_guard_public_payload",
    "validate_research_market_memory_fee_depth_guard_public_payload",
)


DEFAULT_CONFIG_VERSION = "memory-fee-depth-guard-v0"
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_RANK = {STATUS_BLOCK: Decimal("0"), STATUS_WATCH: Decimal("1"), STATUS_PASS: Decimal("2")}
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "source",
    "url",
    "dsn",
    "table",
    "token",
    "text",
)


@dataclass(frozen=True)
class ResearchMarketMemoryFeeDepthGuardConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    max_fee_rate: Decimal = Decimal("0.020000")
    max_spread_cost: Decimal = Decimal("0.100000")
    min_depth_value: Decimal = Decimal("100.000000")
    min_memory_observations: Decimal = Decimal("2")
    pass_score: Decimal = Decimal("0.750000")
    watch_score: Decimal = Decimal("0.450000")
    cost_weight: Decimal = Decimal("0.333333")
    depth_weight: Decimal = Decimal("0.333333")
    memory_weight: Decimal = Decimal("0.333334")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMemoryFeeDepthGuardConfig:
            raise TypeError(
                "ResearchMarketMemoryFeeDepthGuardConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketMemoryFeeDepthGuardConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "max_fee_rate",
            "max_spread_cost",
            "min_depth_value",
            "min_memory_observations",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_score",
            "watch_score",
            "cost_weight",
            "depth_weight",
            "memory_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_score <= self.watch_score:
            raise ValueError("pass_score must be greater than watch_score")
        if self.min_memory_observations != self.min_memory_observations.to_integral_value():
            raise ValueError("min_memory_observations must be a whole count")
        weight_sum = _quantize(
            self.cost_weight + self.depth_weight + self.memory_weight,
        )
        if weight_sum != ONE:
            raise ValueError("cost_weight, depth_weight, and memory_weight must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketMemoryFeeDepthGuardObservation:
    case_id: str
    sample_id: str
    observed_at: datetime
    fee_rate: Decimal
    spread_cost: Decimal
    depth_value: Decimal
    private_refs: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMemoryFeeDepthGuardObservation:
            raise TypeError(
                "ResearchMarketMemoryFeeDepthGuardObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketMemoryFeeDepthGuardObservation, "observation")
        _require_canonical_string("case_id", self.case_id)
        _require_canonical_string("sample_id", self.sample_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("fee_rate", "spread_cost", "depth_value"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "private_refs",
            _normalize_private_refs("private_refs", self.private_refs),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketMemoryFeeDepthGuardRow:
    case_digest: str
    observation_count: Decimal
    latest_observed_at: datetime
    average_fee_rate: Decimal
    average_spread_cost: Decimal
    average_depth_value: Decimal
    cost_score: Decimal
    depth_score: Decimal
    memory_score: Decimal
    cost_weight: Decimal
    depth_weight: Decimal
    memory_weight: Decimal
    pass_score: Decimal
    watch_score: Decimal
    guard_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMemoryFeeDepthGuardRow:
            raise TypeError("ResearchMarketMemoryFeeDepthGuardRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketMemoryFeeDepthGuardRow, "row")
        object.__setattr__(self, "case_digest", _require_sha256("case_digest", self.case_digest))
        object.__setattr__(
            self,
            "observation_count",
            _require_positive_whole_decimal("observation_count", self.observation_count),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in ("average_fee_rate", "average_spread_cost", "average_depth_value"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "cost_score",
            "depth_score",
            "memory_score",
            "cost_weight",
            "depth_weight",
            "memory_weight",
            "pass_score",
            "watch_score",
            "guard_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_score <= self.watch_score:
            raise ValueError("pass_score must be greater than watch_score")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchMarketMemoryFeeDepthGuardReport:
    generated_at: datetime
    config_version: str
    item_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_guard_score: Decimal | None
    status: str
    rows: tuple[ResearchMarketMemoryFeeDepthGuardRow, ...]
    reason_codes: tuple[str, ...]
    public_payload_sha256: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketMemoryFeeDepthGuardReport:
            raise TypeError(
                "ResearchMarketMemoryFeeDepthGuardReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketMemoryFeeDepthGuardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "item_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_guard_score",
            _require_optional_probability_decimal(
                "average_guard_score",
                self.average_guard_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "public_payload_sha256",
            _require_sha256("public_payload_sha256", self.public_payload_sha256),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _payload_sha256(_public_payload_without_digest(self))
        if self.public_payload_sha256 != expected_digest:
            raise ValueError("public_payload_sha256 does not match public payload")


def build_research_market_memory_fee_depth_guard_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketMemoryFeeDepthGuardConfig,
    generated_at: datetime,
) -> ResearchMarketMemoryFeeDepthGuardReport:
    if type(config) is not ResearchMarketMemoryFeeDepthGuardConfig:
        raise ValueError("config must be a ResearchMarketMemoryFeeDepthGuardConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    for item in items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[str, list[ResearchMarketMemoryFeeDepthGuardObservation]] = {}
    for item in items:
        grouped.setdefault(item.case_id, []).append(item)

    built_rows = tuple(
        _build_row(case_id=case_id, observations=tuple(grouped[case_id]), config=config)
        for case_id in sorted(grouped)
    )
    rows = tuple(
        sorted(
            built_rows,
            key=lambda row: (STATUS_RANK[row.status], row.case_digest),
        ),
    )
    reason_codes = _report_reason_codes(rows)
    item_count = _decimal_count(len(rows))
    observation_count = _quantize(sum((row.observation_count for row in rows), ZERO))
    pass_count = _decimal_count(_status_count(rows, STATUS_PASS))
    watch_count = _decimal_count(_status_count(rows, STATUS_WATCH))
    block_count = _decimal_count(_status_count(rows, STATUS_BLOCK))
    average_guard_score = _average_decimal_or_none(tuple(row.guard_score for row in rows))
    status = _report_status(reason_codes)
    public_payload_sha256 = _payload_sha256(
        _public_payload_without_digest_from_parts(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            item_count=item_count,
            observation_count=observation_count,
            pass_count=pass_count,
            watch_count=watch_count,
            block_count=block_count,
            average_guard_score=average_guard_score,
            status=status,
            rows=rows,
            reason_codes=reason_codes,
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
    )

    return ResearchMarketMemoryFeeDepthGuardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        item_count=item_count,
        observation_count=observation_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_guard_score=average_guard_score,
        status=status,
        rows=rows,
        reason_codes=reason_codes,
        public_payload_sha256=public_payload_sha256,
    )


def research_market_memory_fee_depth_guard_public_payload(
    report: ResearchMarketMemoryFeeDepthGuardReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketMemoryFeeDepthGuardReport:
        raise ValueError("report must be a ResearchMarketMemoryFeeDepthGuardReport")
    _require_hard_flags("report", report)
    payload = _public_payload_without_digest(report)
    payload["sha256_digest"] = report.public_payload_sha256
    if not validate_research_market_memory_fee_depth_guard_public_payload(payload):
        raise ValueError("public_payload_sha256 does not match public payload")
    return payload


def validate_research_market_memory_fee_depth_guard_public_payload(payload: object) -> bool:
    try:
        if type(payload) is not dict:
            return False
        _reject_unsafe_public_payload("public payload", payload)
        _reject_public_numerics(payload)
        _require_hard_flags("public payload", _PayloadFlags(payload))
        digest = payload.get("sha256_digest")
        if type(digest) is not str or not _is_sha256(digest):
            return False
        unsigned_payload = {
            key: value for key, value in payload.items() if key != "sha256_digest"
        }
        return _payload_sha256(unsigned_payload) == digest
    except ValueError:
        return False


def _build_row(
    *,
    case_id: str,
    observations: tuple[ResearchMarketMemoryFeeDepthGuardObservation, ...],
    config: ResearchMarketMemoryFeeDepthGuardConfig,
) -> ResearchMarketMemoryFeeDepthGuardRow:
    if not observations:
        raise ValueError("observations must be nonempty")
    sample_ids = tuple(item.sample_id for item in observations)
    if len(set(sample_ids)) != len(sample_ids):
        raise ValueError("sample_id values must be unique within a case_id")
    sorted_items = tuple(sorted(observations, key=lambda item: item.sample_id))
    observation_count = _decimal_count(len(sorted_items))
    average_fee_rate = _average_decimal(tuple(item.fee_rate for item in sorted_items))
    average_spread_cost = _average_decimal(tuple(item.spread_cost for item in sorted_items))
    average_depth_value = _average_decimal(tuple(item.depth_value for item in sorted_items))
    cost_score = _average_decimal(
        (
            _one_minus_bounded_ratio(average_fee_rate, config.max_fee_rate),
            _one_minus_bounded_ratio(average_spread_cost, config.max_spread_cost),
        ),
    )
    depth_score = _bounded_ratio(average_depth_value, config.min_depth_value)
    memory_score = _bounded_ratio(observation_count, config.min_memory_observations)
    guard_score = _weighted_score(
        cost_score=cost_score,
        depth_score=depth_score,
        memory_score=memory_score,
        cost_weight=config.cost_weight,
        depth_weight=config.depth_weight,
        memory_weight=config.memory_weight,
    )
    status = _score_status(
        guard_score,
        pass_score=config.pass_score,
        watch_score=config.watch_score,
    )
    return ResearchMarketMemoryFeeDepthGuardRow(
        case_digest=_sha256_text(case_id),
        observation_count=observation_count,
        latest_observed_at=max(item.observed_at for item in sorted_items),
        average_fee_rate=average_fee_rate,
        average_spread_cost=average_spread_cost,
        average_depth_value=average_depth_value,
        cost_score=cost_score,
        depth_score=depth_score,
        memory_score=memory_score,
        cost_weight=config.cost_weight,
        depth_weight=config.depth_weight,
        memory_weight=config.memory_weight,
        pass_score=config.pass_score,
        watch_score=config.watch_score,
        guard_score=guard_score,
        status=status,
        reason_codes=_row_reason_codes(
            cost_score=cost_score,
            depth_score=depth_score,
            memory_score=memory_score,
            guard_score=guard_score,
            config=config,
        ),
    )


def _row_reason_codes(
    *,
    cost_score: Decimal,
    depth_score: Decimal,
    memory_score: Decimal,
    guard_score: Decimal,
    config: ResearchMarketMemoryFeeDepthGuardConfig,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                _component_reason_code("cost", cost_score, config),
                _component_reason_code("depth", depth_score, config),
                _component_reason_code("memory", memory_score, config),
                f"guard_{_score_status(guard_score, pass_score=config.pass_score, watch_score=config.watch_score)}",
            },
        ),
    )


def _component_reason_code(
    prefix: str,
    score: Decimal,
    config: ResearchMarketMemoryFeeDepthGuardConfig,
) -> str:
    return (
        f"{prefix}_"
        f"{_score_status(score, pass_score=config.pass_score, watch_score=config.watch_score)}"
    )


def _report_reason_codes(rows: tuple[ResearchMarketMemoryFeeDepthGuardRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("no_observations",)
    codes: set[str] = set()
    if any(row.status == STATUS_BLOCK for row in rows):
        codes.add("guard_block")
    if any(row.status == STATUS_WATCH for row in rows):
        codes.add("guard_watch")
    if all(row.status == STATUS_PASS for row in rows):
        codes.add("all_guards_pass")
    counter = Counter(code for row in rows for code in row.reason_codes)
    codes.update(code for code, count in counter.items() if count > 1)
    return tuple(sorted(codes))


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if "no_observations" in reason_codes or "guard_block" in reason_codes:
        return STATUS_BLOCK
    if "guard_watch" in reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _score_status(score: Decimal, *, pass_score: Decimal, watch_score: Decimal) -> str:
    if score >= pass_score:
        return STATUS_PASS
    if score >= watch_score:
        return STATUS_WATCH
    return STATUS_BLOCK


def _validate_row_consistency(row: ResearchMarketMemoryFeeDepthGuardRow) -> None:
    expected_guard_score = _weighted_score(
        cost_score=row.cost_score,
        depth_score=row.depth_score,
        memory_score=row.memory_score,
        cost_weight=row.cost_weight,
        depth_weight=row.depth_weight,
        memory_weight=row.memory_weight,
    )
    if row.guard_score != expected_guard_score:
        raise ValueError("guard_score does not match component scores")
    expected_status = _score_status(
        row.guard_score,
        pass_score=row.pass_score,
        watch_score=row.watch_score,
    )
    if row.status != expected_status:
        raise ValueError("status does not match guard_score")
    required_code = f"guard_{row.status}"
    if required_code not in row.reason_codes:
        raise ValueError("reason_codes must include guard status")


def _validate_report_consistency(report: ResearchMarketMemoryFeeDepthGuardReport) -> None:
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count does not match rows")
    expected_observation_count = sum((row.observation_count for row in report.rows), ZERO)
    if report.observation_count != expected_observation_count:
        raise ValueError("observation_count does not match rows")
    expected_pass_count = _decimal_count(_status_count(report.rows, STATUS_PASS))
    expected_watch_count = _decimal_count(_status_count(report.rows, STATUS_WATCH))
    expected_block_count = _decimal_count(_status_count(report.rows, STATUS_BLOCK))
    if report.pass_count != expected_pass_count:
        raise ValueError("pass_count does not match rows")
    if report.watch_count != expected_watch_count:
        raise ValueError("watch_count does not match rows")
    if report.block_count != expected_block_count:
        raise ValueError("block_count does not match rows")
    expected_average_guard_score = _average_decimal_or_none(
        tuple(row.guard_score for row in report.rows),
    )
    if report.average_guard_score != expected_average_guard_score:
        raise ValueError("average_guard_score does not match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes do not match rows")
    expected_status = _report_status(report.reason_codes)
    if report.status != expected_status:
        raise ValueError("status does not match rows")


def _public_payload_without_digest(report: ResearchMarketMemoryFeeDepthGuardReport) -> dict[str, Any]:
    return _public_payload_without_digest_from_parts(
        generated_at=report.generated_at,
        config_version=report.config_version,
        item_count=report.item_count,
        observation_count=report.observation_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_guard_score=report.average_guard_score,
        status=report.status,
        rows=report.rows,
        reason_codes=report.reason_codes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _public_payload_without_digest_from_parts(
    *,
    generated_at: datetime,
    config_version: str,
    item_count: Decimal,
    observation_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    average_guard_score: Decimal | None,
    status: str,
    rows: tuple[ResearchMarketMemoryFeeDepthGuardRow, ...],
    reason_codes: tuple[str, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, Any]:
    payload = {
        "generated_at": generated_at,
        "config_version": config_version,
        "item_count": item_count,
        "observation_count": observation_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "average_guard_score": average_guard_score,
        "status": status,
        "rows": tuple(_public_row_payload(row) for row in rows),
        "reason_codes": reason_codes,
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", ready)
    _reject_public_numerics(ready)
    return ready


def _public_row_payload(row: ResearchMarketMemoryFeeDepthGuardRow) -> Mapping[str, object]:
    return {
        "case_digest": row.case_digest,
        "observation_count": row.observation_count,
        "latest_observed_at": row.latest_observed_at,
        "average_fee_rate": row.average_fee_rate,
        "average_spread_cost": row.average_spread_cost,
        "average_depth_value": row.average_depth_value,
        "cost_score": row.cost_score,
        "depth_score": row.depth_score,
        "memory_score": row.memory_score,
        "guard_score": row.guard_score,
        "status": row.status,
        "reason_codes": row.reason_codes,
    }


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketMemoryFeeDepthGuardObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observations")
    normalized: list[ResearchMarketMemoryFeeDepthGuardObservation] = []
    for item in observations:
        if type(item) is not ResearchMarketMemoryFeeDepthGuardObservation:
            raise ValueError(
                "observations must contain ResearchMarketMemoryFeeDepthGuardObservation",
            )
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: Iterable[ResearchMarketMemoryFeeDepthGuardRow],
) -> tuple[ResearchMarketMemoryFeeDepthGuardRow, ...]:
    normalized = tuple(rows)
    if any(type(row) is not ResearchMarketMemoryFeeDepthGuardRow for row in normalized):
        raise ValueError("rows must contain ResearchMarketMemoryFeeDepthGuardRow")
    if tuple(sorted(normalized, key=lambda row: (STATUS_RANK[row.status], row.case_digest))) != (
        normalized
    ):
        raise ValueError("rows must be canonical")
    digests = tuple(row.case_digest for row in normalized)
    if len(set(digests)) != len(digests):
        raise ValueError("case_digest values must be unique")
    return normalized


def _normalize_private_refs(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple of strings")
    normalized: list[str] = []
    for index, item in enumerate(value):
        if type(item) is not str:
            raise ValueError(f"{field_name}[{index}] must be a string")
        normalized.append(item)
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple of reason codes")
    normalized = tuple(_require_canonical_string(f"{field_name}[]", item) for item in value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    if tuple(sorted(set(normalized))) != normalized:
        raise ValueError(f"{field_name} must be canonical sorted unique reason codes")
    return normalized


def _status_count(rows: tuple[ResearchMarketMemoryFeeDepthGuardRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / _decimal_count(len(values)))


def _average_decimal_or_none(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _average_decimal(values)


def _weighted_score(
    *,
    cost_score: Decimal,
    depth_score: Decimal,
    memory_score: Decimal,
    cost_weight: Decimal,
    depth_weight: Decimal,
    memory_weight: Decimal,
) -> Decimal:
    return _quantize(
        (cost_score * cost_weight)
        + (depth_score * depth_weight)
        + (memory_score * memory_weight),
    )


def _bounded_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return min(ONE, _quantize(value / denominator))


def _one_minus_bounded_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    return _quantize(ONE - _bounded_ratio(value, denominator))


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return value.quantize(RATIO_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


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
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or not _is_sha256(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(RATIO_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _payload_sha256(payload: Mapping[str, Any]) -> str:
    _reject_unsafe_public_payload("digest payload", payload)
    _reject_public_numerics(payload)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("JSON datetime value", value).isoformat()
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) in (str, bool):
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


@dataclass(frozen=True)
class _PayloadFlags:
    value: Mapping[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")
