"""Pure Phase 1 bank deposit outflow digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_BANK_DEPOSIT_OUTFLOW_DIGEST_CONFIG_VERSION = (
    "market-research-bank-deposit-outflow-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_bank_deposit_outflow_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
MATERIAL_DEPOSIT_DROP_REASON = f"{REASON_PREFIX}material_deposit_drop"
STALE_OBSERVATION_REASON = f"{REASON_PREFIX}stale_observation"
PROBABILITY_REPRICING_REASON = f"{REASON_PREFIX}probability_repricing"
ELEVATED_OUTFLOW_REASON = f"{REASON_PREFIX}elevated_outflow"
THIN_SOURCE_REASON = f"{REASON_PREFIX}thin_source"

REASON_CODE_SEQUENCE = (
    MATERIAL_DEPOSIT_DROP_REASON,
    STALE_OBSERVATION_REASON,
    PROBABILITY_REPRICING_REASON,
    ELEVATED_OUTFLOW_REASON,
    THIN_SOURCE_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_DEPOSIT_DROP_REASON,
    STALE_OBSERVATION_REASON,
    PROBABILITY_REPRICING_REASON,
    ELEVATED_OUTFLOW_REASON,
    THIN_SOURCE_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_bank_deposit_outflow_digest",
    STATUS_WATCH: "watch_report_only_market_research_bank_deposit_outflow_digest",
    STATUS_BLOCKED: "block_report_only_market_research_bank_deposit_outflow_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("api", "_key"),
        _join_parts("bear", "er"),
        _join_parts("cred", "ential"),
        _join_parts("pass", "word"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BANK_DEPOSIT_OUTFLOW_DIGEST_CONFIG_VERSION",
    "MarketResearchBankDepositOutflowDigestConfig",
    "MarketResearchBankDepositOutflowDigestInputRow",
    "MarketResearchBankDepositOutflowDigestReasonCodeCount",
    "MarketResearchBankDepositOutflowDigestReport",
    "MarketResearchBankDepositOutflowDigestRow",
    "build_market_research_bank_deposit_outflow_digest",
    "market_research_bank_deposit_outflow_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchBankDepositOutflowDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BANK_DEPOSIT_OUTFLOW_DIGEST_CONFIG_VERSION
    )
    fresh_observation_max_age_seconds: Decimal = Decimal("7200.000000")
    material_deposit_drop_ratio: Decimal = Decimal("0.030000")
    elevated_outflow_ratio: Decimal = Decimal("0.050000")
    min_source_count: Decimal = Decimal("2")
    probability_repricing_threshold: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBankDepositOutflowDigestConfig:
            raise TypeError(
                "MarketResearchBankDepositOutflowDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBankDepositOutflowDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchBankDepositOutflowDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BANK_DEPOSIT_OUTFLOW_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "fresh_observation_max_age_seconds",
            _require_positive_decimal(
                "fresh_observation_max_age_seconds",
                self.fresh_observation_max_age_seconds,
            ),
        )
        for field_name in (
            "material_deposit_drop_ratio",
            "elevated_outflow_ratio",
            "probability_repricing_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBankDepositOutflowDigestInputRow:
    research_key: str
    condition_id: str
    bank_key: str
    deposit_source_reference: str
    observed_at: datetime
    source_count: Decimal
    deposit_balance: Decimal
    prior_deposit_balance: Decimal
    net_deposit_flow: Decimal
    uninsured_deposit_ratio: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBankDepositOutflowDigestInputRow:
            raise TypeError(
                "MarketResearchBankDepositOutflowDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBankDepositOutflowDigestInputRow:
            raise ValueError(
                "input row must be exactly MarketResearchBankDepositOutflowDigestInputRow",
            )
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_public_string("bank_key", self.bank_key)
        _require_reference("deposit_source_reference", self.deposit_source_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "deposit_balance",
            "prior_deposit_balance",
            "net_deposit_flow",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "uninsured_deposit_ratio",
            _require_ratio_decimal(
                "uninsured_deposit_ratio",
                self.uninsured_deposit_ratio,
            ),
        )
        for field_name in ("market_probability_before", "market_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.deposit_balance < ZERO:
            raise ValueError("deposit_balance must be nonnegative")
        if self.prior_deposit_balance < ZERO:
            raise ValueError("prior_deposit_balance must be nonnegative")
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchBankDepositOutflowDigestRow:
    research_key: str
    condition_id: str
    bank_key: str
    deposit_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    source_count: Decimal
    deposit_balance: Decimal
    prior_deposit_balance: Decimal
    deposit_delta: Decimal
    deposit_drop: Decimal
    deposit_drop_ratio: Decimal
    net_deposit_flow: Decimal
    net_deposit_flow_ratio: Decimal
    uninsured_deposit_ratio: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_delta: Decimal
    redacted_deposit_source_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBankDepositOutflowDigestRow:
            raise TypeError(
                "MarketResearchBankDepositOutflowDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBankDepositOutflowDigestRow:
            raise ValueError("row must be exactly MarketResearchBankDepositOutflowDigestRow")
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_public_string("bank_key", self.bank_key)
        _require_digest_status("deposit_status", self.deposit_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "observation_age_seconds",
            _require_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "deposit_balance",
            "prior_deposit_balance",
            "deposit_delta",
            "deposit_drop",
            "net_deposit_flow",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "deposit_drop_ratio",
            "net_deposit_flow_ratio",
            "uninsured_deposit_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_or_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("market_probability_before", "market_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_delta",
            _require_probability_delta("probability_delta", self.probability_delta),
        )
        object.__setattr__(
            self,
            "redacted_deposit_source_reference",
            _require_redacted_reference(
                "redacted_deposit_source_reference",
                self.redacted_deposit_source_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBankDepositOutflowDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBankDepositOutflowDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchBankDepositOutflowDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBankDepositOutflowDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchBankDepositOutflowDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio_decimal("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchBankDepositOutflowDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    material_deposit_drop_count: Decimal
    stale_observation_count: Decimal
    elevated_outflow_count: Decimal
    thin_source_count: Decimal
    probability_repricing_count: Decimal
    average_deposit_drop_ratio: Decimal
    max_observation_age_seconds: Decimal
    average_source_count: Decimal
    average_uninsured_deposit_ratio: Decimal
    rows: tuple[MarketResearchBankDepositOutflowDigestRow, ...]
    reason_code_counts: tuple[MarketResearchBankDepositOutflowDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBankDepositOutflowDigestReport:
            raise TypeError(
                "MarketResearchBankDepositOutflowDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBankDepositOutflowDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchBankDepositOutflowDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "ready_observation_count",
            "watch_observation_count",
            "blocked_observation_count",
            "material_deposit_drop_count",
            "stale_observation_count",
            "elevated_outflow_count",
            "thin_source_count",
            "probability_repricing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_deposit_drop_ratio",
            "max_observation_age_seconds",
            "average_source_count",
            "average_uninsured_deposit_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_bank_deposit_outflow_digest(
    input_rows: list[MarketResearchBankDepositOutflowDigestInputRow]
    | tuple[MarketResearchBankDepositOutflowDigestInputRow, ...],
    *,
    config: MarketResearchBankDepositOutflowDigestConfig,
    generated_at: datetime,
) -> MarketResearchBankDepositOutflowDigestReport:
    if type(config) is not MarketResearchBankDepositOutflowDigestConfig:
        raise ValueError("config must be a MarketResearchBankDepositOutflowDigestConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_input_rows(input_rows, generated_at_utc)
    rows = tuple(
        _build_row(row, config=config, generated_at=generated_at_utc)
        for row in source_rows
    )
    ranked_rows = tuple(sorted(rows, key=_row_sort_key))
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            MarketResearchBankDepositOutflowDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                observation_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    observation_count = _count(len(ranked_rows))
    ready_observation_count = _count(
        sum(1 for row in ranked_rows if row.deposit_status == STATUS_READY),
    )
    watch_observation_count = _count(
        sum(1 for row in ranked_rows if row.deposit_status == STATUS_WATCH),
    )
    blocked_observation_count = _count(
        sum(1 for row in ranked_rows if row.deposit_status == STATUS_BLOCKED),
    )
    digest_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_observation_count=blocked_observation_count,
        watch_observation_count=watch_observation_count,
    )

    return MarketResearchBankDepositOutflowDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        observation_count=observation_count,
        ready_observation_count=ready_observation_count,
        watch_observation_count=watch_observation_count,
        blocked_observation_count=blocked_observation_count,
        material_deposit_drop_count=_reason_count(
            ranked_rows,
            MATERIAL_DEPOSIT_DROP_REASON,
        ),
        stale_observation_count=_reason_count(ranked_rows, STALE_OBSERVATION_REASON),
        elevated_outflow_count=_reason_count(ranked_rows, ELEVATED_OUTFLOW_REASON),
        thin_source_count=_reason_count(ranked_rows, THIN_SOURCE_REASON),
        probability_repricing_count=_reason_count(
            ranked_rows,
            PROBABILITY_REPRICING_REASON,
        ),
        average_deposit_drop_ratio=_ratio(
            _sum_decimal(row.deposit_drop_ratio for row in ranked_rows),
            observation_count,
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in ranked_rows),
            default=ZERO,
        ),
        average_source_count=_ratio(
            _sum_decimal(row.source_count for row in ranked_rows),
            observation_count,
        ),
        average_uninsured_deposit_ratio=_ratio(
            _sum_decimal(row.uninsured_deposit_ratio for row in ranked_rows),
            observation_count,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_bank_deposit_outflow_digest_payload(
    report: MarketResearchBankDepositOutflowDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketResearchBankDepositOutflowDigestReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        ready = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        ready = _json_ready(report)
    else:
        raise ValueError("report must be a MarketResearchBankDepositOutflowDigestReport")
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(ready))
    _reject_unsafe_public_payload("payload", ready)
    return ready


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


def _normalize_input_rows(
    input_rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchBankDepositOutflowDigestInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(input_rows)
    seen: set[tuple[str, str, str]] = set()
    for input_row in normalized:
        if type(input_row) is not MarketResearchBankDepositOutflowDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchBankDepositOutflowDigestInputRow values",
            )
        _require_hard_flags("input row", input_row)
        key = (
            input_row.research_key,
            input_row.condition_id,
            input_row.bank_key,
        )
        if key in seen:
            raise ValueError("input rows must use unique research condition bank keys")
        seen.add(key)
        if input_row.observed_at > generated_at:
            raise ValueError("observed_at cannot be after generated_at")
    return normalized


def _build_row(
    input_row: MarketResearchBankDepositOutflowDigestInputRow,
    *,
    config: MarketResearchBankDepositOutflowDigestConfig,
    generated_at: datetime,
) -> MarketResearchBankDepositOutflowDigestRow:
    observation_age_seconds = _seconds_between(input_row.observed_at, generated_at)
    deposit_delta = _finite_decimal(
        input_row.deposit_balance - input_row.prior_deposit_balance,
    )
    deposit_drop = max(_finite_decimal(-deposit_delta), ZERO)
    deposit_drop_ratio = _ratio(deposit_drop, input_row.prior_deposit_balance)
    net_deposit_flow_ratio = _ratio(
        abs(input_row.net_deposit_flow),
        input_row.prior_deposit_balance,
    )
    probability_delta = _probability_delta(
        input_row.market_probability_after - input_row.market_probability_before,
    )
    reason_codes = _row_reason_codes(
        source_count=input_row.source_count,
        deposit_drop_ratio=deposit_drop_ratio,
        net_deposit_flow_ratio=net_deposit_flow_ratio,
        probability_delta=probability_delta,
        observation_age_seconds=observation_age_seconds,
        config=config,
    )
    return MarketResearchBankDepositOutflowDigestRow(
        research_key=input_row.research_key,
        condition_id=input_row.condition_id,
        bank_key=input_row.bank_key,
        deposit_status=_row_status(reason_codes),
        observed_at=input_row.observed_at,
        observation_age_seconds=observation_age_seconds,
        source_count=input_row.source_count,
        deposit_balance=input_row.deposit_balance,
        prior_deposit_balance=input_row.prior_deposit_balance,
        deposit_delta=deposit_delta,
        deposit_drop=deposit_drop,
        deposit_drop_ratio=deposit_drop_ratio,
        net_deposit_flow=input_row.net_deposit_flow,
        net_deposit_flow_ratio=net_deposit_flow_ratio,
        uninsured_deposit_ratio=input_row.uninsured_deposit_ratio,
        market_probability_before=input_row.market_probability_before,
        market_probability_after=input_row.market_probability_after,
        probability_delta=probability_delta,
        redacted_deposit_source_reference=_redacted_reference(
            input_row.deposit_source_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_count: Decimal,
    deposit_drop_ratio: Decimal,
    net_deposit_flow_ratio: Decimal,
    probability_delta: Decimal,
    observation_age_seconds: Decimal,
    config: MarketResearchBankDepositOutflowDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if deposit_drop_ratio >= config.material_deposit_drop_ratio:
        reasons.append(MATERIAL_DEPOSIT_DROP_REASON)
    if observation_age_seconds > config.fresh_observation_max_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if abs(probability_delta) >= config.probability_repricing_threshold:
        reasons.append(PROBABILITY_REPRICING_REASON)
    if net_deposit_flow_ratio >= config.elevated_outflow_ratio:
        reasons.append(ELEVATED_OUTFLOW_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCE_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_row_reason_codes(tuple(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if THIN_SOURCE_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_observation_count: Decimal,
    watch_observation_count: Decimal,
) -> str:
    if not has_inputs:
        return STATUS_WATCH
    if blocked_observation_count > ZERO:
        return STATUS_BLOCKED
    if watch_observation_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _row_sort_key(
    row: MarketResearchBankDepositOutflowDigestRow,
) -> tuple[int, str, str, str]:
    return (
        {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[row.deposit_status],
        row.bank_key,
        row.condition_id,
        row.research_key,
    )


def _reason_code_counts(
    rows: tuple[MarketResearchBankDepositOutflowDigestRow, ...],
) -> tuple[MarketResearchBankDepositOutflowDigestReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts[reason_code] + 1 if reason_code in counts else 1
    observation_count = _count(len(rows))
    return tuple(
        MarketResearchBankDepositOutflowDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            observation_ratio=_ratio(_count(counts[reason_code]), observation_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchBankDepositOutflowDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    previous_key: tuple[int, str, str, str] | None = None
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchBankDepositOutflowDigestRow:
            raise ValueError("rows must contain MarketResearchBankDepositOutflowDigestRow")
        _require_hard_flags("row", row)
        identity = (row.research_key, row.condition_id, row.bank_key)
        if identity in seen:
            raise ValueError("rows must use unique research condition bank keys")
        seen.add(identity)
        key = _row_sort_key(row)
        if previous_key is not None and key <= previous_key:
            raise ValueError("rows must be ranked by unique status and bank keys")
        previous_key = key
    return normalized


def _normalize_reason_code_counts(
    values: object,
) -> tuple[MarketResearchBankDepositOutflowDigestReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(values)
    previous_rank = -1
    for count in counts:
        if type(count) is not MarketResearchBankDepositOutflowDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason count", count)
        rank = _reason_code_rank(count.reason_code)
        if rank <= previous_rank:
            raise ValueError("reason_code_counts must be ranked by unique reason_code")
        previous_rank = rank
    return counts


def _normalize_row_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_rank = -1
    for reason_code in reason_codes:
        rank = _row_reason_code_rank(reason_code)
        if rank <= previous_rank:
            raise ValueError("reason_codes must be ranked by unique reason code")
        previous_rank = rank
    if READY_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes ready cannot be combined")
    if NO_INPUTS_REASON in reason_codes:
        raise ValueError("reason_codes no_inputs is report-only")
    return reason_codes


def _normalize_report_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_rank = -1
    for reason_code in reason_codes:
        rank = _reason_code_rank(reason_code)
        if rank <= previous_rank:
            raise ValueError("reason_codes must be ranked by unique reason code")
        previous_rank = rank
    if NO_INPUTS_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes no_inputs cannot be combined")
    return reason_codes


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(values)
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(reason_codes) != len(frozenset(reason_codes)):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _validate_row(row: MarketResearchBankDepositOutflowDigestRow) -> None:
    if row.deposit_balance < ZERO:
        raise ValueError("deposit_balance must be nonnegative")
    if row.prior_deposit_balance < ZERO:
        raise ValueError("prior_deposit_balance must be nonnegative")
    expected_deposit_delta = _finite_decimal(row.deposit_balance - row.prior_deposit_balance)
    if row.deposit_delta != expected_deposit_delta:
        raise ValueError("deposit_delta must match deposit fields")
    if row.deposit_drop != max(_finite_decimal(-row.deposit_delta), ZERO):
        raise ValueError("deposit_drop must match deposit_delta")
    if row.deposit_drop_ratio != _ratio(row.deposit_drop, row.prior_deposit_balance):
        raise ValueError("deposit_drop_ratio must match deposit fields")
    if row.net_deposit_flow_ratio != _ratio(
        abs(row.net_deposit_flow),
        row.prior_deposit_balance,
    ):
        raise ValueError("net_deposit_flow_ratio must match flow fields")
    expected_probability_delta = _probability_delta(
        row.market_probability_after - row.market_probability_before,
    )
    if row.probability_delta != expected_probability_delta:
        raise ValueError("probability_delta must match probability fields")
    if row.deposit_status != _row_status(row.reason_codes):
        raise ValueError("deposit_status must match reason_codes")


def _validate_report(report: MarketResearchBankDepositOutflowDigestReport) -> None:
    if report.observation_count != _count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.ready_observation_count != _count(
        sum(1 for row in report.rows if row.deposit_status == STATUS_READY),
    ):
        raise ValueError("ready_observation_count must match rows")
    if report.watch_observation_count != _count(
        sum(1 for row in report.rows if row.deposit_status == STATUS_WATCH),
    ):
        raise ValueError("watch_observation_count must match rows")
    if report.blocked_observation_count != _count(
        sum(1 for row in report.rows if row.deposit_status == STATUS_BLOCKED),
    ):
        raise ValueError("blocked_observation_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_counts = (
            MarketResearchBankDepositOutflowDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                observation_ratio=ONE,
            ),
        )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_observation_count=report.blocked_observation_count,
        watch_observation_count=report.watch_observation_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match row statuses")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    _validate_report_metric(
        report,
        "material_deposit_drop_count",
        MATERIAL_DEPOSIT_DROP_REASON,
    )
    _validate_report_metric(report, "stale_observation_count", STALE_OBSERVATION_REASON)
    _validate_report_metric(report, "elevated_outflow_count", ELEVATED_OUTFLOW_REASON)
    _validate_report_metric(report, "thin_source_count", THIN_SOURCE_REASON)
    _validate_report_metric(
        report,
        "probability_repricing_count",
        PROBABILITY_REPRICING_REASON,
    )
    if report.average_deposit_drop_ratio != _ratio(
        _sum_decimal(row.deposit_drop_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_deposit_drop_ratio must match rows")
    if report.max_observation_age_seconds != max(
        (row.observation_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observation_age_seconds must match rows")
    if report.average_source_count != _ratio(
        _sum_decimal(row.source_count for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_source_count must match rows")
    if report.average_uninsured_deposit_ratio != _ratio(
        _sum_decimal(row.uninsured_deposit_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_uninsured_deposit_ratio must match rows")


def _validate_report_metric(
    report: MarketResearchBankDepositOutflowDigestReport,
    field_name: str,
    reason_code: str,
) -> None:
    expected = _reason_count(report.rows, reason_code)
    if getattr(report, field_name) != expected:
        raise ValueError(f"{field_name} must match rows")


def _reason_count(
    rows: tuple[MarketResearchBankDepositOutflowDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _require_public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    if any(fragment in value.lower() for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    return value


def _require_redacted_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        raise ValueError(f"{field_name} must be redacted")
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain reason code strings")
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain known reason codes")
    return value


def _require_digest_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be one of {DIGEST_STATUSES}")
    return value


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _finite_decimal(value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_ratio_or_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    return normalized


def _require_probability_delta(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _finite_decimal(total_microseconds / MICROSECONDS_PER_SECOND)


def _count(value: int) -> Decimal:
    return _finite_decimal(Decimal(value))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[assignment]
        total += value
    return _finite_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _finite_decimal(numerator / denominator)


def _probability_delta(value: Decimal) -> Decimal:
    if value < -ONE or value > ONE:
        raise ValueError("probability_delta must be between -1 and 1")
    return _finite_decimal(value)


def _finite_decimal(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be finite and quantizable") from exc


def _redacted_reference(reference: str) -> str:
    if not _is_sensitive_reference(reference):
        return reference
    digest = sha256(reference.encode("utf-8")).hexdigest()[:12]
    return f"sha256:{digest}"


def _is_sensitive_reference(reference: str) -> bool:
    lowered = reference.lower()
    return (
        any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)
        or "://" in lowered
        or "?" in lowered
    )


def _reason_code_rank(reason_code: str) -> int:
    try:
        return REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("reason_code must be a known reason code") from exc


def _row_reason_code_rank(reason_code: str) -> int:
    try:
        return ROW_REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("reason_codes must contain row reason codes") from exc


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _json_ready(value: Any, path: str = "") -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value), path)
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or 'value'} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or 'value'} must be finite")
        return format(_finite_decimal(value), "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or 'value'} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or 'value'} must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError(f"{path or 'value'} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{path or 'value'} must not be a float")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            ready[key] = _json_ready(item, item_path)
        return ready
    if isinstance(value, (list, tuple)):
        return [
            _json_ready(item, f"{path}[{index}]" if path else f"value[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{path or 'value'} is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is str:
        lowered = value.lower()
        if "://" in lowered or "?" in lowered:
            raise ValueError(f"{path or label} has unsafe value")
        if _has_unsafe_public_text_fragment(lowered):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            if _has_unsafe_public_text_fragment(key.lower()):
                raise ValueError(f"{item_path} has unsafe field")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _has_unsafe_public_text_fragment(value: str) -> bool:
    return any(fragment in value for fragment in UNSAFE_TEXT_FRAGMENTS)
