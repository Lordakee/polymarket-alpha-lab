"""Pure report-only claim cost memory guard reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_CLAIM_COST_MEMORY_GUARD_REPORT_CONFIG_VERSION = (
    "research-market-claim-cost-memory-guard-report-v1"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
CLAIM_COST_MEMORY_GUARD_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)
STATUS_RANK = {
    BLOCK_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
NO_INPUTS_REASON = "claim_cost_memory_guard_no_inputs"


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("r", "aw"),
    _join_parts("can", "didate"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "ur", "l"),
    _join_parts("sour", "ce", "_", "tex", "t"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("li", "ve"),
    _join_parts("tra", "ding"),
    _join_parts("siz", "ing"),
    _join_parts("reco", "mmend", "ation"),
    _join_parts("net", "work"),
    _join_parts("data", "base"),
    _join_parts("d", "b"),
    "://",
    "?",
    "@",
    "=",
)

__all__ = (
    "CLAIM_COST_MEMORY_GUARD_STATUSES",
    "DEFAULT_RESEARCH_MARKET_CLAIM_COST_MEMORY_GUARD_REPORT_CONFIG_VERSION",
    "ResearchMarketClaimCostMemoryGuardConfig",
    "ResearchMarketClaimCostMemoryGuardInput",
    "ResearchMarketClaimCostMemoryGuardReasonCodeCount",
    "ResearchMarketClaimCostMemoryGuardReport",
    "ResearchMarketClaimCostMemoryGuardRow",
    "build_research_market_claim_cost_memory_guard_report",
    "research_market_claim_cost_memory_guard_report_digest",
    "research_market_claim_cost_memory_guard_report_payload",
    "validate_research_market_claim_cost_memory_guard_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketClaimCostMemoryGuardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_CLAIM_COST_MEMORY_GUARD_REPORT_CONFIG_VERSION
    )
    maximum_pass_claim_cost_rate: Decimal = Decimal("0.020000")
    maximum_watch_claim_cost_rate: Decimal = Decimal("0.050000")
    minimum_pass_memory_hit_count: Decimal = Decimal("3.000000")
    minimum_watch_memory_hit_count: Decimal = Decimal("1.000000")
    maximum_pass_memory_loss_rate: Decimal = Decimal("0.100000")
    maximum_watch_memory_loss_rate: Decimal = Decimal("0.250000")
    minimum_pass_memory_confidence_score: Decimal = Decimal("0.750000")
    minimum_watch_memory_confidence_score: Decimal = Decimal("0.500000")
    claim_cost_weight: Decimal = Decimal("0.350000")
    memory_depth_weight: Decimal = Decimal("0.200000")
    memory_loss_weight: Decimal = Decimal("0.250000")
    memory_confidence_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketClaimCostMemoryGuardConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_CLAIM_COST_MEMORY_GUARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "maximum_pass_claim_cost_rate",
            "maximum_watch_claim_cost_rate",
            "maximum_pass_memory_loss_rate",
            "maximum_watch_memory_loss_rate",
            "minimum_pass_memory_confidence_score",
            "minimum_watch_memory_confidence_score",
            "claim_cost_weight",
            "memory_depth_weight",
            "memory_loss_weight",
            "memory_confidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_pass_memory_hit_count",
            "minimum_watch_memory_hit_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.maximum_pass_claim_cost_rate > self.maximum_watch_claim_cost_rate:
            raise ValueError("maximum_pass_claim_cost_rate must not exceed watch")
        if self.minimum_pass_memory_hit_count < self.minimum_watch_memory_hit_count:
            raise ValueError("minimum_pass_memory_hit_count must be at least watch")
        if self.maximum_pass_memory_loss_rate > self.maximum_watch_memory_loss_rate:
            raise ValueError("maximum_pass_memory_loss_rate must not exceed watch")
        if (
            self.minimum_pass_memory_confidence_score
            < self.minimum_watch_memory_confidence_score
        ):
            raise ValueError(
                "minimum_pass_memory_confidence_score must be at least watch",
            )
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketClaimCostMemoryGuardInput:
    private_claim_ref: str
    observed_at: datetime
    claim_cost_rate: Decimal
    memory_hit_count: Decimal
    memory_loss_rate: Decimal
    memory_confidence_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketClaimCostMemoryGuardInput, "input")
        _require_private_ref("private_claim_ref", self.private_claim_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("claim_cost_rate", "memory_loss_rate", "memory_confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_hit_count",
            _require_nonnegative_decimal("memory_hit_count", self.memory_hit_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketClaimCostMemoryGuardRow:
    public_row_ref: str
    claim_ref_digest: str
    observed_at: datetime
    claim_cost_rate: Decimal
    claim_cost_score: Decimal
    memory_hit_count: Decimal
    memory_depth_score: Decimal
    memory_loss_rate: Decimal
    memory_loss_score: Decimal
    memory_confidence_score: Decimal
    memory_confidence_component_score: Decimal
    guard_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketClaimCostMemoryGuardRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        _require_sha256_digest("claim_ref_digest", self.claim_ref_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "memory_hit_count",
            _require_nonnegative_decimal("memory_hit_count", self.memory_hit_count),
        )
        for field_name in (
            "claim_cost_rate",
            "claim_cost_score",
            "memory_depth_score",
            "memory_loss_rate",
            "memory_loss_score",
            "memory_confidence_score",
            "memory_confidence_component_score",
            "guard_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketClaimCostMemoryGuardReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketClaimCostMemoryGuardReasonCodeCount,
            "reason_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_count", self)


@dataclass(frozen=True)
class ResearchMarketClaimCostMemoryGuardReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    high_claim_cost_count: Decimal
    low_memory_depth_count: Decimal
    high_memory_loss_count: Decimal
    low_memory_confidence_count: Decimal
    average_guard_score: Decimal
    max_claim_cost_rate: Decimal
    min_memory_hit_count: Decimal
    max_memory_loss_rate: Decimal
    min_memory_confidence_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketClaimCostMemoryGuardReasonCodeCount, ...]
    rows: tuple[ResearchMarketClaimCostMemoryGuardRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketClaimCostMemoryGuardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "high_claim_cost_count",
            "low_memory_depth_count",
            "high_memory_loss_count",
            "low_memory_confidence_count",
            "max_claim_cost_rate",
            "min_memory_hit_count",
            "max_memory_loss_rate",
            "min_memory_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_guard_score",
            _require_ratio_decimal("average_guard_score", self.average_guard_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError(
                    "derived_validation_digest does not match public payload",
                )

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_market_claim_cost_memory_guard_report_payload(self)


def build_research_market_claim_cost_memory_guard_report(
    inputs: Iterable[ResearchMarketClaimCostMemoryGuardInput],
    *,
    config: ResearchMarketClaimCostMemoryGuardConfig,
    generated_at: datetime,
) -> ResearchMarketClaimCostMemoryGuardReport:
    if type(config) is not ResearchMarketClaimCostMemoryGuardConfig:
        raise ValueError("config must be a ResearchMarketClaimCostMemoryGuardConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    keyed_inputs = tuple(
        sorted(
            ((_private_digest(value.private_claim_ref), value) for value in normalized),
            key=lambda item: item[0],
        ),
    )
    if len({key for key, _ in keyed_inputs}) != len(keyed_inputs):
        raise ValueError("private_claim_ref values must be unique")
    row_values = tuple(
        sorted(
            (_row_values_from_input(value, config=config, claim_ref_digest=key) for key, value in keyed_inputs),
            key=_row_values_sort_key,
        ),
    )
    rows = tuple(
        ResearchMarketClaimCostMemoryGuardRow(
            public_row_ref=_public_row_ref(index),
            **values,
        )
        for index, values in enumerate(row_values, start=1)
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketClaimCostMemoryGuardReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_decimal_count(len(normalized)),
        row_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, PASS_STATUS)),
        watch_count=_decimal_count(_status_count(rows, WATCH_STATUS)),
        block_count=_decimal_count(_status_count(rows, BLOCK_STATUS)),
        high_claim_cost_count=_decimal_count(
            sum(row.claim_cost_rate > config.maximum_pass_claim_cost_rate for row in rows),
        ),
        low_memory_depth_count=_decimal_count(
            sum(row.memory_hit_count < config.minimum_pass_memory_hit_count for row in rows),
        ),
        high_memory_loss_count=_decimal_count(
            sum(row.memory_loss_rate > config.maximum_pass_memory_loss_rate for row in rows),
        ),
        low_memory_confidence_count=_decimal_count(
            sum(
                row.memory_confidence_score
                < config.minimum_pass_memory_confidence_score
                for row in rows
            ),
        ),
        average_guard_score=_average(tuple(row.guard_score for row in rows)),
        max_claim_cost_rate=max((row.claim_cost_rate for row in rows), default=ZERO),
        min_memory_hit_count=min((row.memory_hit_count for row in rows), default=ZERO),
        max_memory_loss_rate=max((row.memory_loss_rate for row in rows), default=ZERO),
        min_memory_confidence_score=min(
            (row.memory_confidence_score for row in rows),
            default=ZERO,
        ),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes),
        rows=rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_market_claim_cost_memory_guard_report_payload(
    report: ResearchMarketClaimCostMemoryGuardReport | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(report, Mapping):
        return validate_research_market_claim_cost_memory_guard_report_payload(report)
    if type(report) is not ResearchMarketClaimCostMemoryGuardReport:
        raise ValueError("report must be a ResearchMarketClaimCostMemoryGuardReport")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_numeric_literals(payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def validate_research_market_claim_cost_memory_guard_report_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    normalized = dict(payload)
    _reject_numeric_literals(normalized)
    _reject_unsafe_public_payload("payload", normalized)
    provided_digest = normalized.get("derived_validation_digest")
    if type(provided_digest) is not str:
        raise ValueError("derived_validation_digest must be present")
    _require_sha256_digest("derived_validation_digest", provided_digest)
    digest_payload = dict(normalized)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    if sha256(encoded.encode("utf-8")).hexdigest() != provided_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    return normalized


def research_market_claim_cost_memory_guard_report_digest(
    report: ResearchMarketClaimCostMemoryGuardReport,
) -> str:
    return research_market_claim_cost_memory_guard_report_payload(report)[
        "derived_validation_digest"
    ]


def _row_values_from_input(
    value: ResearchMarketClaimCostMemoryGuardInput,
    *,
    config: ResearchMarketClaimCostMemoryGuardConfig,
    claim_ref_digest: str,
) -> dict[str, Any]:
    claim_cost_score, claim_cost_reason = _low_is_good_score(
        value.claim_cost_rate,
        pass_value=config.maximum_pass_claim_cost_rate,
        watch_value=config.maximum_watch_claim_cost_rate,
        label="claim_cost_rate",
    )
    memory_depth_score, memory_depth_reason = _high_is_good_score(
        value.memory_hit_count,
        pass_value=config.minimum_pass_memory_hit_count,
        watch_value=config.minimum_watch_memory_hit_count,
        label="claim_memory_depth",
    )
    memory_loss_score, memory_loss_reason = _low_is_good_score(
        value.memory_loss_rate,
        pass_value=config.maximum_pass_memory_loss_rate,
        watch_value=config.maximum_watch_memory_loss_rate,
        label="claim_memory_loss",
    )
    memory_confidence_score, memory_confidence_reason = _high_is_good_score(
        value.memory_confidence_score,
        pass_value=config.minimum_pass_memory_confidence_score,
        watch_value=config.minimum_watch_memory_confidence_score,
        label="claim_memory_confidence",
    )
    guard_score = _quantize(
        (
            claim_cost_score * config.claim_cost_weight
            + memory_depth_score * config.memory_depth_weight
            + memory_loss_score * config.memory_loss_weight
            + memory_confidence_score * config.memory_confidence_weight
        ),
    )
    status = _status_from_score(guard_score)
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        (
            f"claim_cost_memory_guard_status_{status}",
            claim_cost_reason,
            memory_confidence_reason,
            memory_depth_reason,
            memory_loss_reason,
            *tuple(f"input_{reason_code}" for reason_code in value.reason_codes),
        ),
    )
    return {
        "claim_ref_digest": claim_ref_digest,
        "observed_at": value.observed_at,
        "claim_cost_rate": value.claim_cost_rate,
        "claim_cost_score": claim_cost_score,
        "memory_hit_count": value.memory_hit_count,
        "memory_depth_score": memory_depth_score,
        "memory_loss_rate": value.memory_loss_rate,
        "memory_loss_score": memory_loss_score,
        "memory_confidence_score": value.memory_confidence_score,
        "memory_confidence_component_score": memory_confidence_score,
        "guard_score": guard_score,
        "status": status,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _low_is_good_score(
    value: Decimal,
    *,
    pass_value: Decimal,
    watch_value: Decimal,
    label: str,
) -> tuple[Decimal, str]:
    if value <= pass_value:
        return ONE, f"{label}_pass"
    if value <= watch_value:
        return _quantize((watch_value - value) / (watch_value - pass_value)), f"{label}_watch"
    return ZERO, f"{label}_block"


def _high_is_good_score(
    value: Decimal,
    *,
    pass_value: Decimal,
    watch_value: Decimal,
    label: str,
) -> tuple[Decimal, str]:
    if value >= pass_value:
        return ONE, f"{label}_pass"
    if value >= watch_value:
        return _quantize((value - watch_value) / (pass_value - watch_value)), f"{label}_watch"
    return ZERO, f"{label}_block"


def _status_from_score(value: Decimal) -> str:
    if value >= Decimal("0.750000"):
        return PASS_STATUS
    if value >= Decimal("0.500000"):
        return WATCH_STATUS
    return BLOCK_STATUS


def _report_status(rows: tuple[ResearchMarketClaimCostMemoryGuardRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    return min((row.status for row in rows), key=lambda status: STATUS_RANK[status])


def _report_reason_codes(rows: tuple[ResearchMarketClaimCostMemoryGuardRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
    )


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketClaimCostMemoryGuardReasonCodeCount, ...]:
    counts = Counter(reason_codes)
    return tuple(
        ResearchMarketClaimCostMemoryGuardReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _status_count(
    rows: tuple[ResearchMarketClaimCostMemoryGuardRow, ...],
    status: str,
) -> int:
    return sum(row.status == status for row in rows)


def _row_values_sort_key(values: dict[str, Any]) -> tuple[Decimal, Decimal, str]:
    guard_score = values["guard_score"]
    status = values["status"]
    claim_ref_digest = values["claim_ref_digest"]
    if type(guard_score) is not Decimal or type(status) is not str or type(claim_ref_digest) is not str:
        raise ValueError("row values are invalid")
    return (STATUS_RANK[status], guard_score, claim_ref_digest)


def _public_row_ref(index: int) -> str:
    return f"claim_cost_memory_guard_row_{index:03d}"


def _private_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _report_derived_validation_digest(
    report: ResearchMarketClaimCostMemoryGuardReport,
) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_row_consistency(row: ResearchMarketClaimCostMemoryGuardRow) -> None:
    expected_status = _status_from_score(row.guard_score)
    if row.status != expected_status:
        raise ValueError("status must match guard_score")
    status_reason = f"claim_cost_memory_guard_status_{row.status}"
    if status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include status reason")


def _validate_report_consistency(report: ResearchMarketClaimCostMemoryGuardReport) -> None:
    row_count = _decimal_count(len(report.rows))
    if report.row_count != row_count:
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.pass_count != _decimal_count(_status_count(report.rows, PASS_STATUS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, WATCH_STATUS)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, BLOCK_STATUS)):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.average_guard_score != _average(tuple(row.guard_score for row in report.rows)):
        raise ValueError("average_guard_score must match rows")


def _normalize_inputs(
    values: Iterable[ResearchMarketClaimCostMemoryGuardInput],
) -> tuple[ResearchMarketClaimCostMemoryGuardInput, ...]:
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not ResearchMarketClaimCostMemoryGuardInput:
            raise ValueError("inputs must be ResearchMarketClaimCostMemoryGuardInput")
        _require_hard_flags("input", value)
    return normalized


def _normalize_rows(
    values: tuple[ResearchMarketClaimCostMemoryGuardRow, ...],
) -> tuple[ResearchMarketClaimCostMemoryGuardRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple")
    for value in values:
        if type(value) is not ResearchMarketClaimCostMemoryGuardRow:
            raise ValueError("rows must contain ResearchMarketClaimCostMemoryGuardRow")
    return values


def _normalize_reason_code_counts(
    values: tuple[ResearchMarketClaimCostMemoryGuardReasonCodeCount, ...],
) -> tuple[ResearchMarketClaimCostMemoryGuardReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchMarketClaimCostMemoryGuardReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketClaimCostMemoryGuardReasonCodeCount",
            )
    if values != tuple(sorted(values, key=lambda item: item.reason_code)):
        raise ValueError("reason_code_counts must be sorted")
    return values


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: str) -> None:
    _require_public_label(field_name, value)
    _reject_unsafe_text(field_name, value)


def _require_public_label(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if len(value) > 160:
        raise ValueError(f"{field_name} is too long")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a public label")


def _require_private_ref(field_name: str, value: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_exact_type(value: object, expected: type[object], label: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{label} must be exactly {expected.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_status(field_name: str, value: str) -> None:
    if value not in CLAIM_COST_MEMORY_GUARD_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_sha256_digest(field_name: str, value: str) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return value


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _decimal_count(len(values)))


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _weight_sum(config: ResearchMarketClaimCostMemoryGuardConfig) -> Decimal:
    return _quantize(
        config.claim_cost_weight
        + config.memory_depth_weight
        + config.memory_loss_weight
        + config.memory_confidence_weight,
    )


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        return format(value, ".6f")
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _reject_numeric_literals(value: object) -> None:
    if isinstance(value, bool):
        return
    if type(value) in (float, int, Decimal):
        raise ValueError("public payload numerics must be Decimal-derived string values")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_numeric_literals(key)
            _reject_numeric_literals(item)
    elif isinstance(value, list):
        for item in value:
            _reject_numeric_literals(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value):
        for field in fields(value):
            _reject_unsafe_text(label, field.name)
            _reject_unsafe_public_payload(label, getattr(value, field.name))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload")
            _reject_unsafe_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str):
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
