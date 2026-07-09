"""Pure public settlement fee uncertainty ladder report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_SETTLEMENT_FEE_UNCERTAINTY_LADDER_CONFIG_VERSION",
    "ResearchMarketSettlementFeeUncertaintyLadderConfig",
    "ResearchMarketSettlementFeeUncertaintyLadderObservation",
    "ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount",
    "ResearchMarketSettlementFeeUncertaintyLadderReport",
    "ResearchMarketSettlementFeeUncertaintyLadderRow",
    "build_research_market_settlement_fee_uncertainty_ladder_report",
    "research_market_settlement_fee_uncertainty_ladder_digest",
    "research_market_settlement_fee_uncertainty_ladder_report_payload",
)


DEFAULT_RESEARCH_MARKET_SETTLEMENT_FEE_UNCERTAINTY_LADDER_CONFIG_VERSION = (
    "research-market-settlement-fee-uncertainty-ladder-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "execute",
    "recommend",
    "position",
    "sizing",
)
_REASON_CODE_SEQUENCE = (
    "empty_observations",
    "fee_assumption_component",
    "spread_component",
    "slippage_buffer_component",
    "settlement_friction_component",
    "liquidity_depth_component",
    "confidence_haircut_component",
    "settlement_fee_uncertainty_pass",
    "settlement_fee_uncertainty_watch",
    "settlement_fee_uncertainty_block",
)
_REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "sample_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_settlement_fee_uncertainty_score",
        "max_settlement_fee_uncertainty_score",
        "status",
        "reason_code_counts",
        "reason_codes",
        "rows",
        "public_report_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_FIELDS = frozenset(
    (
        "ladder_rank",
        "observed_at",
        "fee_assumption_cost",
        "spread_cost",
        "slippage_buffer_cost",
        "settlement_friction_cost",
        "liquidity_depth_score",
        "liquidity_depth_cost",
        "confidence_haircut_cost",
        "settlement_fee_uncertainty_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REASON_CODE_COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
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
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchMarketSettlementFeeUncertaintyLadderConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_SETTLEMENT_FEE_UNCERTAINTY_LADDER_CONFIG_VERSION
    )
    liquidity_depth_penalty_rate: Decimal = Decimal("0.050000")
    pass_threshold: Decimal = Decimal("0.020000")
    block_threshold: Decimal = Decimal("0.070000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementFeeUncertaintyLadderConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_SETTLEMENT_FEE_UNCERTAINTY_LADDER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "liquidity_depth_penalty_rate",
            "pass_threshold",
            "block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_threshold <= self.pass_threshold:
            raise ValueError("block_threshold must exceed pass_threshold")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketSettlementFeeUncertaintyLadderObservation(_FinalPublicDataclass):
    raw_candidate_id: str
    observed_at: datetime
    fee_assumption: Decimal
    quoted_spread: Decimal
    slippage_buffer: Decimal
    settlement_friction: Decimal
    liquidity_depth: Decimal
    confidence_haircut: Decimal
    sensitive_context: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementFeeUncertaintyLadderObservation,
            "observation",
        )
        _require_nonblank_string("raw_candidate_id", self.raw_candidate_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "fee_assumption",
            "quoted_spread",
            "slippage_buffer",
            "settlement_friction",
            "liquidity_depth",
            "confidence_haircut",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sensitive_context",
            _normalize_optional_string("sensitive_context", self.sensitive_context),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketSettlementFeeUncertaintyLadderRow(_FinalPublicDataclass):
    ladder_rank: Decimal
    observed_at: datetime
    fee_assumption_cost: Decimal
    spread_cost: Decimal
    slippage_buffer_cost: Decimal
    settlement_friction_cost: Decimal
    liquidity_depth_score: Decimal
    liquidity_depth_cost: Decimal
    confidence_haircut_cost: Decimal
    settlement_fee_uncertainty_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementFeeUncertaintyLadderRow,
            "row",
        )
        object.__setattr__(
            self,
            "ladder_rank",
            _require_positive_count_decimal("ladder_rank", self.ladder_rank),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "fee_assumption_cost",
            "spread_cost",
            "slippage_buffer_cost",
            "settlement_friction_cost",
            "liquidity_depth_cost",
            "confidence_haircut_cost",
            "settlement_fee_uncertainty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_depth_score",
            _require_ratio_decimal("liquidity_depth_score", self.liquidity_depth_score),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount,
            "reason_code_count",
        )
        _require_public_identifier("reason_code", self.reason_code)
        if self.reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketSettlementFeeUncertaintyLadderReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    sample_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_settlement_fee_uncertainty_score: Decimal
    max_settlement_fee_uncertainty_score: Decimal
    status: str
    reason_code_counts: tuple[
        ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketSettlementFeeUncertaintyLadderRow, ...]
    public_report_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementFeeUncertaintyLadderReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_SETTLEMENT_FEE_UNCERTAINTY_LADDER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "sample_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_settlement_fee_uncertainty_score",
            "max_settlement_fee_uncertainty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
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
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("public_report_digest", self.public_report_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.public_report_digest != _expected_public_report_digest(self):
            raise ValueError("public_report_digest must match public report payload")

    @property
    def payload(self) -> dict[str, object]:
        return research_market_settlement_fee_uncertainty_ladder_report_payload(self)


@dataclass(frozen=True)
class _RowDraft:
    observed_at: datetime
    fee_assumption_cost: Decimal
    spread_cost: Decimal
    slippage_buffer_cost: Decimal
    settlement_friction_cost: Decimal
    liquidity_depth_score: Decimal
    liquidity_depth_cost: Decimal
    confidence_haircut_cost: Decimal
    settlement_fee_uncertainty_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def build_research_market_settlement_fee_uncertainty_ladder_report(
    observations: Iterable[ResearchMarketSettlementFeeUncertaintyLadderObservation],
    *,
    generated_at: datetime,
    config: ResearchMarketSettlementFeeUncertaintyLadderConfig | None = None,
) -> ResearchMarketSettlementFeeUncertaintyLadderReport:
    """Build a local report-only settlement fee uncertainty ladder."""

    if config is None:
        config = ResearchMarketSettlementFeeUncertaintyLadderConfig()
    if type(config) is not ResearchMarketSettlementFeeUncertaintyLadderConfig:
        raise ValueError(
            "config must be a ResearchMarketSettlementFeeUncertaintyLadderConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must be less than or equal to generated_at")

    drafts = tuple(
        _row_draft_for_observation(observation, config)
        for observation in normalized_observations
    )
    rows = tuple(
        _row_from_draft(ladder_rank=_decimal_count(index), draft=draft)
        for index, draft in enumerate(sorted(drafts, key=_draft_sort_key), start=1)
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "sample_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_settlement_fee_uncertainty_score": _average(
            tuple(row.settlement_fee_uncertainty_score for row in rows),
        ),
        "max_settlement_fee_uncertainty_score": max(
            (row.settlement_fee_uncertainty_score for row in rows),
            default=_ZERO,
        ),
        "status": _report_status(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketSettlementFeeUncertaintyLadderReport(
        **values,
        public_report_digest=_public_digest(values),
    )


def research_market_settlement_fee_uncertainty_ladder_report_payload(
    report: ResearchMarketSettlementFeeUncertaintyLadderReport,
) -> dict[str, object]:
    validated_report = _validated_report_copy(report)
    payload = asdict(validated_report)
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload_schema(ready)
    _reject_unsafe_public_payload(
        "research_market_settlement_fee_uncertainty_ladder_report_payload",
        ready,
        allow_json_containers=True,
    )
    return ready


def research_market_settlement_fee_uncertainty_ladder_digest(
    report: ResearchMarketSettlementFeeUncertaintyLadderReport,
) -> str:
    payload = research_market_settlement_fee_uncertainty_ladder_report_payload(report)
    digest = payload.get("public_report_digest")
    if type(digest) is not str:
        raise ValueError("public_report_digest must be a string")
    return digest


def _row_draft_for_observation(
    observation: ResearchMarketSettlementFeeUncertaintyLadderObservation,
    config: ResearchMarketSettlementFeeUncertaintyLadderConfig,
) -> _RowDraft:
    fee_assumption_cost = observation.fee_assumption
    spread_cost = _quantize(observation.quoted_spread / _TWO)
    slippage_buffer_cost = observation.slippage_buffer
    settlement_friction_cost = observation.settlement_friction
    liquidity_depth_score = observation.liquidity_depth
    liquidity_depth_cost = _quantize(
        (_ONE - observation.liquidity_depth) * config.liquidity_depth_penalty_rate,
    )
    confidence_haircut_cost = observation.confidence_haircut
    settlement_fee_uncertainty_score = _quantize(
        fee_assumption_cost
        + spread_cost
        + slippage_buffer_cost
        + settlement_friction_cost
        + liquidity_depth_cost
        + confidence_haircut_cost,
    )
    status = _row_status(
        settlement_fee_uncertainty_score=settlement_fee_uncertainty_score,
        config=config,
    )
    return _RowDraft(
        observed_at=observation.observed_at,
        fee_assumption_cost=fee_assumption_cost,
        spread_cost=spread_cost,
        slippage_buffer_cost=slippage_buffer_cost,
        settlement_friction_cost=settlement_friction_cost,
        liquidity_depth_score=liquidity_depth_score,
        liquidity_depth_cost=liquidity_depth_cost,
        confidence_haircut_cost=confidence_haircut_cost,
        settlement_fee_uncertainty_score=settlement_fee_uncertainty_score,
        status=status,
        reason_codes=_row_reason_codes(
            fee_assumption_cost=fee_assumption_cost,
            spread_cost=spread_cost,
            slippage_buffer_cost=slippage_buffer_cost,
            settlement_friction_cost=settlement_friction_cost,
            liquidity_depth_cost=liquidity_depth_cost,
            confidence_haircut_cost=confidence_haircut_cost,
            status=status,
        ),
    )


def _row_from_draft(
    *,
    ladder_rank: Decimal,
    draft: _RowDraft,
) -> ResearchMarketSettlementFeeUncertaintyLadderRow:
    return ResearchMarketSettlementFeeUncertaintyLadderRow(
        ladder_rank=ladder_rank,
        observed_at=draft.observed_at,
        fee_assumption_cost=draft.fee_assumption_cost,
        spread_cost=draft.spread_cost,
        slippage_buffer_cost=draft.slippage_buffer_cost,
        settlement_friction_cost=draft.settlement_friction_cost,
        liquidity_depth_score=draft.liquidity_depth_score,
        liquidity_depth_cost=draft.liquidity_depth_cost,
        confidence_haircut_cost=draft.confidence_haircut_cost,
        settlement_fee_uncertainty_score=draft.settlement_fee_uncertainty_score,
        status=draft.status,
        reason_codes=draft.reason_codes,
    )


def _row_status(
    *,
    settlement_fee_uncertainty_score: Decimal,
    config: ResearchMarketSettlementFeeUncertaintyLadderConfig,
) -> str:
    if settlement_fee_uncertainty_score >= config.block_threshold:
        return "block"
    if settlement_fee_uncertainty_score <= config.pass_threshold:
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    fee_assumption_cost: Decimal,
    spread_cost: Decimal,
    slippage_buffer_cost: Decimal,
    settlement_friction_cost: Decimal,
    liquidity_depth_cost: Decimal,
    confidence_haircut_cost: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if fee_assumption_cost > _ZERO:
        reason_codes.append("fee_assumption_component")
    if spread_cost > _ZERO:
        reason_codes.append("spread_component")
    if slippage_buffer_cost > _ZERO:
        reason_codes.append("slippage_buffer_component")
    if settlement_friction_cost > _ZERO:
        reason_codes.append("settlement_friction_component")
    if liquidity_depth_cost > _ZERO:
        reason_codes.append("liquidity_depth_component")
    if confidence_haircut_cost > _ZERO:
        reason_codes.append("confidence_haircut_component")
    reason_codes.append(f"settlement_fee_uncertainty_{status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[ResearchMarketSettlementFeeUncertaintyLadderRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketSettlementFeeUncertaintyLadderRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_observations",)
    reason_codes: set[str] = set()
    for row in rows:
        reason_codes.update(row.reason_codes)
    return _normalize_reason_codes(
        tuple(
            reason_code
            for reason_code in _REASON_CODE_SEQUENCE
            if reason_code in reason_codes
        ),
    )


def _reason_code_counts(
    rows: tuple[ResearchMarketSettlementFeeUncertaintyLadderRow, ...],
) -> tuple[ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    if not rows:
        counter["empty_observations"] = 1
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if counter[reason_code] > 0
    )


def _status_count(
    rows: tuple[ResearchMarketSettlementFeeUncertaintyLadderRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_row_consistency(
    row: ResearchMarketSettlementFeeUncertaintyLadderRow,
) -> None:
    expected_score = _quantize(
        row.fee_assumption_cost
        + row.spread_cost
        + row.slippage_buffer_cost
        + row.settlement_friction_cost
        + row.liquidity_depth_cost
        + row.confidence_haircut_cost,
    )
    if row.settlement_fee_uncertainty_score != expected_score:
        raise ValueError(
            "settlement_fee_uncertainty_score must match cost components",
        )
    expected_reason_codes = _row_reason_codes(
        fee_assumption_cost=row.fee_assumption_cost,
        spread_cost=row.spread_cost,
        slippage_buffer_cost=row.slippage_buffer_cost,
        settlement_friction_cost=row.settlement_friction_cost,
        liquidity_depth_cost=row.liquidity_depth_cost,
        confidence_haircut_cost=row.confidence_haircut_cost,
        status=row.status,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match cost components and status")


def _validate_report_consistency(
    report: ResearchMarketSettlementFeeUncertaintyLadderReport,
) -> None:
    if any(row.observed_at > report.generated_at for row in report.rows):
        raise ValueError("row observed_at must not exceed generated_at")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must follow canonical ladder order")
    if report.sample_count != _decimal_count(len(report.rows)):
        raise ValueError("sample_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_settlement_fee_uncertainty_score != _average(
        tuple(row.settlement_fee_uncertainty_score for row in report.rows),
    ):
        raise ValueError("average_settlement_fee_uncertainty_score must match rows")
    expected_max = max(
        (row.settlement_fee_uncertainty_score for row in report.rows),
        default=_ZERO,
    )
    if report.max_settlement_fee_uncertainty_score != expected_max:
        raise ValueError("max_settlement_fee_uncertainty_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_observations(
    observations: Iterable[ResearchMarketSettlementFeeUncertaintyLadderObservation],
) -> tuple[ResearchMarketSettlementFeeUncertaintyLadderObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    normalized: list[ResearchMarketSettlementFeeUncertaintyLadderObservation] = []
    try:
        iterator = iter(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    raw_candidate_ids: set[str] = set()
    for observation in iterator:
        if type(observation) is not ResearchMarketSettlementFeeUncertaintyLadderObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketSettlementFeeUncertaintyLadderObservation",
            )
        if observation.raw_candidate_id in raw_candidate_ids:
            raise ValueError("raw_candidate_id values must be unique")
        raw_candidate_ids.add(observation.raw_candidate_id)
        normalized.append(observation)
    return tuple(
        sorted(
            normalized,
            key=lambda observation: (
                observation.fee_assumption,
                observation.quoted_spread,
                observation.slippage_buffer,
                observation.settlement_friction,
                observation.liquidity_depth,
                observation.confidence_haircut,
                observation.observed_at,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchMarketSettlementFeeUncertaintyLadderRow],
) -> tuple[ResearchMarketSettlementFeeUncertaintyLadderRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchMarketSettlementFeeUncertaintyLadderRow] = []
    for row in rows:
        if type(row) is not ResearchMarketSettlementFeeUncertaintyLadderRow:
            raise ValueError(
                "rows must contain ResearchMarketSettlementFeeUncertaintyLadderRow",
            )
        normalized.append(_validated_row_copy(row))
    ordered = tuple(sorted(normalized, key=lambda row: row.ladder_rank))
    for expected_rank, row in enumerate(ordered, start=1):
        if row.ladder_rank != _decimal_count(expected_rank):
            raise ValueError("ladder_rank must be sequential")
    return ordered


def _normalize_reason_code_counts(
    rows: Sequence[ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount],
) -> tuple[ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount] = []
    reason_codes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount",
            )
        if row.reason_code in reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        reason_codes.add(row.reason_code)
        normalized.append(_validated_reason_code_count_copy(row))
    return tuple(
        sorted(
            normalized,
            key=lambda row: _REASON_CODE_SEQUENCE.index(row.reason_code),
        ),
    )


def _draft_sort_key(
    draft: _RowDraft,
) -> tuple[
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    datetime,
]:
    return (
        -draft.settlement_fee_uncertainty_score,
        -draft.fee_assumption_cost,
        -draft.spread_cost,
        -draft.slippage_buffer_cost,
        -draft.settlement_friction_cost,
        -draft.liquidity_depth_cost,
        -draft.confidence_haircut_cost,
        draft.liquidity_depth_score,
        draft.observed_at,
    )


def _row_sort_key(
    row: ResearchMarketSettlementFeeUncertaintyLadderRow,
) -> tuple[
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    datetime,
]:
    return (
        -row.settlement_fee_uncertainty_score,
        -row.fee_assumption_cost,
        -row.spread_cost,
        -row.slippage_buffer_cost,
        -row.settlement_friction_cost,
        -row.liquidity_depth_cost,
        -row.confidence_haircut_cost,
        row.liquidity_depth_score,
        row.observed_at,
    )


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_nonblank_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must be nonblank")
    return value


def _normalize_optional_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_nonblank_string(field_name, value)


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
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
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code in normalized:
            raise ValueError("reason_codes must be unique")
        normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _expected_public_report_digest(
    report: ResearchMarketSettlementFeeUncertaintyLadderReport,
) -> str:
    values = asdict(report)
    values.pop("public_report_digest", None)
    return _public_digest(values)


def _validated_report_copy(
    report: ResearchMarketSettlementFeeUncertaintyLadderReport,
) -> ResearchMarketSettlementFeeUncertaintyLadderReport:
    if type(report) is not ResearchMarketSettlementFeeUncertaintyLadderReport:
        raise ValueError(
            "report must be a ResearchMarketSettlementFeeUncertaintyLadderReport",
        )
    return ResearchMarketSettlementFeeUncertaintyLadderReport(
        **_public_dataclass_values(
            report,
            ResearchMarketSettlementFeeUncertaintyLadderReport,
        ),
    )


def _validated_row_copy(
    row: ResearchMarketSettlementFeeUncertaintyLadderRow,
) -> ResearchMarketSettlementFeeUncertaintyLadderRow:
    return ResearchMarketSettlementFeeUncertaintyLadderRow(
        **_public_dataclass_values(
            row,
            ResearchMarketSettlementFeeUncertaintyLadderRow,
        ),
    )


def _validated_reason_code_count_copy(
    row: ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount,
) -> ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount:
    return ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount(
        **_public_dataclass_values(
            row,
            ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount,
        ),
    )


def _public_dataclass_values(
    value: object,
    expected_type: type[object],
) -> dict[str, object]:
    return {
        field.name: getattr(value, field.name)
        for field in fields(expected_type)
    }


def _validate_public_payload_schema(payload: Mapping[str, object]) -> None:
    _require_exact_payload_fields("report payload", payload, _REPORT_PAYLOAD_FIELDS)
    _require_payload_hard_flags("report payload", payload)

    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("report payload reason_code_counts schema is invalid")
    for index, row in enumerate(reason_code_counts):
        if type(row) is not dict:
            raise ValueError("report payload reason_code_counts schema is invalid")
        label = f"report payload reason_code_counts[{index}]"
        _require_exact_payload_fields(
            label,
            row,
            _REASON_CODE_COUNT_PAYLOAD_FIELDS,
        )
        _require_payload_hard_flags(label, row)

    reason_codes = payload["reason_codes"]
    if type(reason_codes) is not list or any(
        type(reason_code) is not str for reason_code in reason_codes
    ):
        raise ValueError("report payload reason_codes schema is invalid")

    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("report payload rows schema is invalid")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("report payload rows schema is invalid")
        label = f"report payload rows[{index}]"
        _require_exact_payload_fields(label, row, _ROW_PAYLOAD_FIELDS)
        _require_payload_hard_flags(label, row)
        row_reason_codes = row["reason_codes"]
        if type(row_reason_codes) is not list or any(
            type(reason_code) is not str for reason_code in row_reason_codes
        ):
            raise ValueError(f"{label} reason_codes schema is invalid")


def _require_exact_payload_fields(
    label: str,
    value: Mapping[str, object],
    expected_fields: frozenset[str],
) -> None:
    if frozenset(value) != expected_fields:
        raise ValueError(f"{label} schema must match expected fields")


def _require_payload_hard_flags(
    label: str,
    value: Mapping[str, object],
) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _public_digest(values: Mapping[str, object]) -> str:
    ready = _json_ready(values)
    if type(ready) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload(
        "public_digest",
        ready,
        allow_json_containers=True,
    )
    encoded = json.dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric values must be Decimal-derived strings")
    if type(value) is str or type(value) is bool:
        return value
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=True,
        )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_string(f"{label}.{key}", key)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers:
            raise ValueError(f"{label} public payload containers are not allowed")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                f"{label}[{index}]",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if isinstance(value, float):
        raise ValueError(f"{label} public payload must not contain floats")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(term in normalized for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} contains an unsafe public surface")
