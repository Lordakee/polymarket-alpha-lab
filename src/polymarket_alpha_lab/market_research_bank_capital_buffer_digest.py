"""Pure Phase 1 bank capital buffer digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_BANK_CAPITAL_BUFFER_DIGEST_CONFIG_VERSION = (
    "market-research-bank-capital-buffer-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_bank_capital_buffer_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
CAPITAL_BUFFER_BREACH_REASON = f"{REASON_PREFIX}capital_buffer_breach"
CAPITAL_BUFFER_THIN_REASON = f"{REASON_PREFIX}capital_buffer_thin"
STRESS_LOSS_BUFFER_GAP_REASON = f"{REASON_PREFIX}stress_loss_buffer_gap"
STALE_OBSERVATION_REASON = f"{REASON_PREFIX}stale_observation"
PROBABILITY_REPRICING_REASON = f"{REASON_PREFIX}probability_repricing"
THIN_SOURCE_REASON = f"{REASON_PREFIX}thin_source"

REASON_CODE_SEQUENCE = (
    CAPITAL_BUFFER_BREACH_REASON,
    CAPITAL_BUFFER_THIN_REASON,
    STRESS_LOSS_BUFFER_GAP_REASON,
    STALE_OBSERVATION_REASON,
    PROBABILITY_REPRICING_REASON,
    THIN_SOURCE_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    CAPITAL_BUFFER_BREACH_REASON,
    CAPITAL_BUFFER_THIN_REASON,
    STRESS_LOSS_BUFFER_GAP_REASON,
    STALE_OBSERVATION_REASON,
    PROBABILITY_REPRICING_REASON,
    THIN_SOURCE_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_bank_capital_buffer_digest",
    STATUS_WATCH: "watch_report_only_market_research_bank_capital_buffer_digest",
    STATUS_BLOCKED: "block_report_only_market_research_bank_capital_buffer_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "digest_status",
        "recommended_next_step",
        "observation_count",
        "ready_observation_count",
        "watch_observation_count",
        "blocked_observation_count",
        "capital_buffer_breach_count",
        "capital_buffer_thin_count",
        "stress_loss_buffer_gap_count",
        "stale_observation_count",
        "thin_source_count",
        "probability_repricing_count",
        "average_capital_buffer_ratio",
        "min_capital_buffer_ratio",
        "max_stress_loss_buffer_gap_ratio",
        "max_observation_age_seconds",
        "average_source_count",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "research_key",
        "condition_id",
        "bank_key",
        "capital_status",
        "observed_at",
        "observation_age_seconds",
        "source_count",
        "cet1_capital_ratio",
        "minimum_capital_ratio",
        "capital_buffer_ratio",
        "stress_loss_ratio",
        "stress_loss_buffer_gap_ratio",
        "market_probability_before",
        "market_probability_after",
        "probability_delta",
        "redacted_capital_source_reference",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_CODE_COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "observation_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ord", "er"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("ex", "change"),
        _join_parts("mut", "ation"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("api", "_key"),
        _join_parts("bear", "er"),
        _join_parts("cred", "ential"),
        _join_parts("pass", "word"),
        _join_parts("tra", "de"),
        _join_parts("dsn"),
        "://",
        "?",
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BANK_CAPITAL_BUFFER_DIGEST_CONFIG_VERSION",
    "MarketResearchBankCapitalBufferDigestConfig",
    "MarketResearchBankCapitalBufferDigestReasonCodeCount",
    "MarketResearchBankCapitalBufferDigestReport",
    "MarketResearchBankCapitalBufferDigestRow",
    "MarketResearchBankCapitalBufferDigestSignal",
    "build_market_research_bank_capital_buffer_digest",
    "market_research_bank_capital_buffer_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchBankCapitalBufferDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BANK_CAPITAL_BUFFER_DIGEST_CONFIG_VERSION
    )
    fresh_observation_max_age_seconds: Decimal = Decimal("7200.000000")
    minimum_capital_buffer_ratio: Decimal = Decimal("0.025000")
    min_source_count: Decimal = Decimal("2.000000")
    probability_repricing_threshold: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchBankCapitalBufferDigestConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBankCapitalBufferDigestConfig:
            raise TypeError(
                "config must be exactly MarketResearchBankCapitalBufferDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BANK_CAPITAL_BUFFER_DIGEST_CONFIG_VERSION
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
        object.__setattr__(
            self,
            "minimum_capital_buffer_ratio",
            _require_ratio_decimal(
                "minimum_capital_buffer_ratio",
                self.minimum_capital_buffer_ratio,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        object.__setattr__(
            self,
            "probability_repricing_threshold",
            _require_ratio_decimal(
                "probability_repricing_threshold",
                self.probability_repricing_threshold,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBankCapitalBufferDigestSignal:
    research_key: str
    condition_id: str
    bank_key: str
    capital_source_reference: str
    observed_at: datetime
    source_count: Decimal
    cet1_capital_ratio: Decimal
    minimum_capital_ratio: Decimal
    stress_loss_ratio: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchBankCapitalBufferDigestSignal does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBankCapitalBufferDigestSignal:
            raise TypeError(
                "signal must be exactly MarketResearchBankCapitalBufferDigestSignal",
            )
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_public_string("bank_key", self.bank_key)
        _require_reference("capital_source_reference", self.capital_source_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "cet1_capital_ratio",
            "minimum_capital_ratio",
            "stress_loss_ratio",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchBankCapitalBufferDigestRow:
    research_key: str
    condition_id: str
    bank_key: str
    capital_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    source_count: Decimal
    cet1_capital_ratio: Decimal
    minimum_capital_ratio: Decimal
    capital_buffer_ratio: Decimal
    stress_loss_ratio: Decimal
    stress_loss_buffer_gap_ratio: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_delta: Decimal
    redacted_capital_source_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchBankCapitalBufferDigestRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBankCapitalBufferDigestRow:
            raise TypeError("row must be exactly MarketResearchBankCapitalBufferDigestRow")
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_public_string("bank_key", self.bank_key)
        _require_digest_status("capital_status", self.capital_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "observation_age_seconds",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "cet1_capital_ratio",
            "minimum_capital_ratio",
            "stress_loss_ratio",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("capital_buffer_ratio", "stress_loss_buffer_gap_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_delta",
            _require_probability_delta("probability_delta", self.probability_delta),
        )
        object.__setattr__(
            self,
            "redacted_capital_source_reference",
            _require_redacted_reference(
                "redacted_capital_source_reference",
                self.redacted_capital_source_reference,
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
class MarketResearchBankCapitalBufferDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchBankCapitalBufferDigestReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBankCapitalBufferDigestReasonCodeCount:
            raise TypeError(
                "reason count must be exactly "
                "MarketResearchBankCapitalBufferDigestReasonCodeCount",
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
class MarketResearchBankCapitalBufferDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    capital_buffer_breach_count: Decimal
    capital_buffer_thin_count: Decimal
    stress_loss_buffer_gap_count: Decimal
    stale_observation_count: Decimal
    thin_source_count: Decimal
    probability_repricing_count: Decimal
    average_capital_buffer_ratio: Decimal
    min_capital_buffer_ratio: Decimal
    max_stress_loss_buffer_gap_ratio: Decimal
    max_observation_age_seconds: Decimal
    average_source_count: Decimal
    rows: tuple[MarketResearchBankCapitalBufferDigestRow, ...]
    reason_code_counts: tuple[MarketResearchBankCapitalBufferDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchBankCapitalBufferDigestReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBankCapitalBufferDigestReport:
            raise TypeError(
                "report must be exactly MarketResearchBankCapitalBufferDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "ready_observation_count",
            "watch_observation_count",
            "blocked_observation_count",
            "capital_buffer_breach_count",
            "capital_buffer_thin_count",
            "stress_loss_buffer_gap_count",
            "stale_observation_count",
            "thin_source_count",
            "probability_repricing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_capital_buffer_ratio",
            "min_capital_buffer_ratio",
            "max_stress_loss_buffer_gap_ratio",
            "max_observation_age_seconds",
            "average_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
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


_PUBLIC_DATACLASS_TYPES = frozenset(
    (
        MarketResearchBankCapitalBufferDigestConfig,
        MarketResearchBankCapitalBufferDigestSignal,
        MarketResearchBankCapitalBufferDigestRow,
        MarketResearchBankCapitalBufferDigestReasonCodeCount,
        MarketResearchBankCapitalBufferDigestReport,
    ),
)


def build_market_research_bank_capital_buffer_digest(
    signals: list[MarketResearchBankCapitalBufferDigestSignal]
    | tuple[MarketResearchBankCapitalBufferDigestSignal, ...],
    *,
    config: MarketResearchBankCapitalBufferDigestConfig,
    generated_at: datetime,
) -> MarketResearchBankCapitalBufferDigestReport:
    if type(config) is not MarketResearchBankCapitalBufferDigestConfig:
        raise ValueError("config must be a MarketResearchBankCapitalBufferDigestConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_signals = _normalize_signals(signals, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _build_row(signal, config=config, generated_at=generated_at_utc)
                for signal in source_signals
            ),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchBankCapitalBufferDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                observation_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    observation_count = _count(len(rows))
    ready_observation_count = _status_count(rows, STATUS_READY)
    watch_observation_count = _status_count(rows, STATUS_WATCH)
    blocked_observation_count = _status_count(rows, STATUS_BLOCKED)
    digest_status = _report_status(
        has_inputs=bool(rows),
        blocked_observation_count=blocked_observation_count,
        watch_observation_count=watch_observation_count,
    )

    return MarketResearchBankCapitalBufferDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        observation_count=observation_count,
        ready_observation_count=ready_observation_count,
        watch_observation_count=watch_observation_count,
        blocked_observation_count=blocked_observation_count,
        capital_buffer_breach_count=_reason_count(rows, CAPITAL_BUFFER_BREACH_REASON),
        capital_buffer_thin_count=_reason_count(rows, CAPITAL_BUFFER_THIN_REASON),
        stress_loss_buffer_gap_count=_reason_count(
            rows,
            STRESS_LOSS_BUFFER_GAP_REASON,
        ),
        stale_observation_count=_reason_count(rows, STALE_OBSERVATION_REASON),
        thin_source_count=_reason_count(rows, THIN_SOURCE_REASON),
        probability_repricing_count=_reason_count(rows, PROBABILITY_REPRICING_REASON),
        average_capital_buffer_ratio=_ratio(
            _sum_decimal(row.capital_buffer_ratio for row in rows),
            observation_count,
        ),
        min_capital_buffer_ratio=min(
            (row.capital_buffer_ratio for row in rows),
            default=ZERO,
        ),
        max_stress_loss_buffer_gap_ratio=max(
            (row.stress_loss_buffer_gap_ratio for row in rows),
            default=ZERO,
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in rows),
            default=ZERO,
        ),
        average_source_count=_ratio(
            _sum_decimal(row.source_count for row in rows),
            observation_count,
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_bank_capital_buffer_digest_payload(
    report: MarketResearchBankCapitalBufferDigestReport,
) -> dict[str, Any]:
    if type(report) is MarketResearchBankCapitalBufferDigestReport:
        _reject_unsafe_public_payload("report", report)
        validated = _validated_report(report)
        _require_hard_flags("report", validated)
        ready = _json_ready(validated)
    else:
        raise ValueError("report must be a MarketResearchBankCapitalBufferDigestReport")
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


def _validated_report(
    report: MarketResearchBankCapitalBufferDigestReport,
) -> MarketResearchBankCapitalBufferDigestReport:
    return MarketResearchBankCapitalBufferDigestReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        digest_status=report.digest_status,
        recommended_next_step=report.recommended_next_step,
        observation_count=report.observation_count,
        ready_observation_count=report.ready_observation_count,
        watch_observation_count=report.watch_observation_count,
        blocked_observation_count=report.blocked_observation_count,
        capital_buffer_breach_count=report.capital_buffer_breach_count,
        capital_buffer_thin_count=report.capital_buffer_thin_count,
        stress_loss_buffer_gap_count=report.stress_loss_buffer_gap_count,
        stale_observation_count=report.stale_observation_count,
        thin_source_count=report.thin_source_count,
        probability_repricing_count=report.probability_repricing_count,
        average_capital_buffer_ratio=report.average_capital_buffer_ratio,
        min_capital_buffer_ratio=report.min_capital_buffer_ratio,
        max_stress_loss_buffer_gap_ratio=report.max_stress_loss_buffer_gap_ratio,
        max_observation_age_seconds=report.max_observation_age_seconds,
        average_source_count=report.average_source_count,
        rows=_validated_rows(report.rows),
        reason_code_counts=_validated_reason_code_counts(report.reason_code_counts),
        reason_codes=report.reason_codes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _validated_rows(
    rows: object,
) -> tuple[MarketResearchBankCapitalBufferDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    return tuple(_validated_row(row) for row in rows)


def _validated_row(row: object) -> MarketResearchBankCapitalBufferDigestRow:
    if type(row) is not MarketResearchBankCapitalBufferDigestRow:
        raise ValueError("rows must contain MarketResearchBankCapitalBufferDigestRow")
    return MarketResearchBankCapitalBufferDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        bank_key=row.bank_key,
        capital_status=row.capital_status,
        observed_at=row.observed_at,
        observation_age_seconds=row.observation_age_seconds,
        source_count=row.source_count,
        cet1_capital_ratio=row.cet1_capital_ratio,
        minimum_capital_ratio=row.minimum_capital_ratio,
        capital_buffer_ratio=row.capital_buffer_ratio,
        stress_loss_ratio=row.stress_loss_ratio,
        stress_loss_buffer_gap_ratio=row.stress_loss_buffer_gap_ratio,
        market_probability_before=row.market_probability_before,
        market_probability_after=row.market_probability_after,
        probability_delta=row.probability_delta,
        redacted_capital_source_reference=row.redacted_capital_source_reference,
        reason_codes=row.reason_codes,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )


def _validated_reason_code_counts(
    counts: object,
) -> tuple[MarketResearchBankCapitalBufferDigestReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    return tuple(_validated_reason_code_count(count) for count in counts)


def _validated_reason_code_count(
    count: object,
) -> MarketResearchBankCapitalBufferDigestReasonCodeCount:
    if type(count) is not MarketResearchBankCapitalBufferDigestReasonCodeCount:
        raise ValueError("reason_code_counts must contain reason count rows")
    return MarketResearchBankCapitalBufferDigestReasonCodeCount(
        reason_code=count.reason_code,
        count=count.count,
        observation_ratio=count.observation_ratio,
        paper_only=count.paper_only,
        report_only=count.report_only,
        readonly=count.readonly,
    )


def _report_from_payload(
    payload: dict[str, Any],
) -> MarketResearchBankCapitalBufferDigestReport:
    _require_payload_fields("payload", payload, REPORT_PAYLOAD_FIELDS)
    return MarketResearchBankCapitalBufferDigestReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        digest_status=_payload_string("digest_status", payload["digest_status"]),
        recommended_next_step=_payload_string(
            "recommended_next_step",
            payload["recommended_next_step"],
        ),
        observation_count=_payload_decimal(
            "observation_count",
            payload["observation_count"],
        ),
        ready_observation_count=_payload_decimal(
            "ready_observation_count",
            payload["ready_observation_count"],
        ),
        watch_observation_count=_payload_decimal(
            "watch_observation_count",
            payload["watch_observation_count"],
        ),
        blocked_observation_count=_payload_decimal(
            "blocked_observation_count",
            payload["blocked_observation_count"],
        ),
        capital_buffer_breach_count=_payload_decimal(
            "capital_buffer_breach_count",
            payload["capital_buffer_breach_count"],
        ),
        capital_buffer_thin_count=_payload_decimal(
            "capital_buffer_thin_count",
            payload["capital_buffer_thin_count"],
        ),
        stress_loss_buffer_gap_count=_payload_decimal(
            "stress_loss_buffer_gap_count",
            payload["stress_loss_buffer_gap_count"],
        ),
        stale_observation_count=_payload_decimal(
            "stale_observation_count",
            payload["stale_observation_count"],
        ),
        thin_source_count=_payload_decimal(
            "thin_source_count",
            payload["thin_source_count"],
        ),
        probability_repricing_count=_payload_decimal(
            "probability_repricing_count",
            payload["probability_repricing_count"],
        ),
        average_capital_buffer_ratio=_payload_decimal(
            "average_capital_buffer_ratio",
            payload["average_capital_buffer_ratio"],
        ),
        min_capital_buffer_ratio=_payload_decimal(
            "min_capital_buffer_ratio",
            payload["min_capital_buffer_ratio"],
        ),
        max_stress_loss_buffer_gap_ratio=_payload_decimal(
            "max_stress_loss_buffer_gap_ratio",
            payload["max_stress_loss_buffer_gap_ratio"],
        ),
        max_observation_age_seconds=_payload_decimal(
            "max_observation_age_seconds",
            payload["max_observation_age_seconds"],
        ),
        average_source_count=_payload_decimal(
            "average_source_count",
            payload["average_source_count"],
        ),
        rows=tuple(
            _row_from_payload(item, f"rows[{index}]")
            for index, item in enumerate(_payload_sequence("rows", payload["rows"]))
        ),
        reason_code_counts=tuple(
            _reason_code_count_from_payload(item, f"reason_code_counts[{index}]")
            for index, item in enumerate(
                _payload_sequence(
                    "reason_code_counts",
                    payload["reason_code_counts"],
                ),
            )
        ),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _row_from_payload(
    value: object,
    path: str,
) -> MarketResearchBankCapitalBufferDigestRow:
    row = _payload_dict(path, value)
    _require_payload_fields(path, row, ROW_PAYLOAD_FIELDS)
    return MarketResearchBankCapitalBufferDigestRow(
        research_key=_payload_string(f"{path}.research_key", row["research_key"]),
        condition_id=_payload_string(f"{path}.condition_id", row["condition_id"]),
        bank_key=_payload_string(f"{path}.bank_key", row["bank_key"]),
        capital_status=_payload_string(f"{path}.capital_status", row["capital_status"]),
        observed_at=_payload_datetime(f"{path}.observed_at", row["observed_at"]),
        observation_age_seconds=_payload_decimal(
            f"{path}.observation_age_seconds",
            row["observation_age_seconds"],
        ),
        source_count=_payload_decimal(f"{path}.source_count", row["source_count"]),
        cet1_capital_ratio=_payload_decimal(
            f"{path}.cet1_capital_ratio",
            row["cet1_capital_ratio"],
        ),
        minimum_capital_ratio=_payload_decimal(
            f"{path}.minimum_capital_ratio",
            row["minimum_capital_ratio"],
        ),
        capital_buffer_ratio=_payload_decimal(
            f"{path}.capital_buffer_ratio",
            row["capital_buffer_ratio"],
        ),
        stress_loss_ratio=_payload_decimal(
            f"{path}.stress_loss_ratio",
            row["stress_loss_ratio"],
        ),
        stress_loss_buffer_gap_ratio=_payload_decimal(
            f"{path}.stress_loss_buffer_gap_ratio",
            row["stress_loss_buffer_gap_ratio"],
        ),
        market_probability_before=_payload_decimal(
            f"{path}.market_probability_before",
            row["market_probability_before"],
        ),
        market_probability_after=_payload_decimal(
            f"{path}.market_probability_after",
            row["market_probability_after"],
        ),
        probability_delta=_payload_decimal(
            f"{path}.probability_delta",
            row["probability_delta"],
        ),
        redacted_capital_source_reference=_payload_string(
            f"{path}.redacted_capital_source_reference",
            row["redacted_capital_source_reference"],
        ),
        reason_codes=_payload_string_tuple(
            f"{path}.reason_codes",
            row["reason_codes"],
        ),
        paper_only=_payload_bool(f"{path}.paper_only", row["paper_only"]),
        report_only=_payload_bool(f"{path}.report_only", row["report_only"]),
        readonly=_payload_bool(f"{path}.readonly", row["readonly"]),
    )


def _reason_code_count_from_payload(
    value: object,
    path: str,
) -> MarketResearchBankCapitalBufferDigestReasonCodeCount:
    count = _payload_dict(path, value)
    _require_payload_fields(path, count, REASON_CODE_COUNT_PAYLOAD_FIELDS)
    return MarketResearchBankCapitalBufferDigestReasonCodeCount(
        reason_code=_payload_string(f"{path}.reason_code", count["reason_code"]),
        count=_payload_decimal(f"{path}.count", count["count"]),
        observation_ratio=_payload_decimal(
            f"{path}.observation_ratio",
            count["observation_ratio"],
        ),
        paper_only=_payload_bool(f"{path}.paper_only", count["paper_only"]),
        report_only=_payload_bool(f"{path}.report_only", count["report_only"]),
        readonly=_payload_bool(f"{path}.readonly", count["readonly"]),
    )


def _require_payload_fields(
    label: str,
    payload: dict[str, Any],
    expected_fields: frozenset[str],
) -> None:
    actual_fields = frozenset(payload)
    if actual_fields != expected_fields:
        raise ValueError(f"{label} must contain the exact digest fields")


def _payload_dict(field_name: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    return value


def _payload_sequence(field_name: str, value: object) -> tuple[object, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    return tuple(value)


def _payload_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    return tuple(
        _payload_string(f"{field_name}[{index}]", item)
        for index, item in enumerate(_payload_sequence(field_name, value))
    )


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    return value


def _payload_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is Decimal:
        return _require_six_decimal_value(field_name, value)
    if type(value) is str:
        if not _is_six_decimal_string(value):
            raise ValueError(f"{field_name} must be a six-decimal Decimal string")
        return Decimal(value)
    raise ValueError(f"{field_name} must be a six-decimal Decimal string")


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is datetime:
        return _as_utc(field_name, value)
    if type(value) is str:
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an ISO datetime string") from exc
        normalized = _as_utc(field_name, parsed)
        if normalized.isoformat() != value:
            raise ValueError(f"{field_name} must be a UTC datetime string")
        return normalized
    raise ValueError(f"{field_name} must be a datetime string")


def _normalize_signals(
    signals: object,
    generated_at: datetime,
) -> tuple[MarketResearchBankCapitalBufferDigestSignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    seen: set[tuple[str, str, str]] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchBankCapitalBufferDigestSignal:
            raise ValueError(
                "signals must contain MarketResearchBankCapitalBufferDigestSignal",
            )
        _require_hard_flags("signal", signal)
        key = (signal.research_key, signal.condition_id, signal.bank_key)
        if key in seen:
            raise ValueError("signals must use unique research condition bank keys")
        seen.add(key)
        if signal.observed_at > generated_at:
            raise ValueError("observed_at cannot be after generated_at")
    return normalized


def _build_row(
    signal: MarketResearchBankCapitalBufferDigestSignal,
    *,
    config: MarketResearchBankCapitalBufferDigestConfig,
    generated_at: datetime,
) -> MarketResearchBankCapitalBufferDigestRow:
    observation_age_seconds = _seconds_between(signal.observed_at, generated_at)
    capital_buffer_ratio = _finite_decimal(
        signal.cet1_capital_ratio - signal.minimum_capital_ratio,
    )
    stress_loss_buffer_gap_ratio = _finite_decimal(
        max(signal.stress_loss_ratio - capital_buffer_ratio, ZERO),
    )
    probability_delta = _probability_delta(
        signal.market_probability_after - signal.market_probability_before,
    )
    reason_codes = _row_reason_codes(
        source_count=signal.source_count,
        capital_buffer_ratio=capital_buffer_ratio,
        stress_loss_buffer_gap_ratio=stress_loss_buffer_gap_ratio,
        probability_delta=probability_delta,
        observation_age_seconds=observation_age_seconds,
        config=config,
    )
    return MarketResearchBankCapitalBufferDigestRow(
        research_key=signal.research_key,
        condition_id=signal.condition_id,
        bank_key=signal.bank_key,
        capital_status=_row_status(reason_codes),
        observed_at=signal.observed_at,
        observation_age_seconds=observation_age_seconds,
        source_count=signal.source_count,
        cet1_capital_ratio=signal.cet1_capital_ratio,
        minimum_capital_ratio=signal.minimum_capital_ratio,
        capital_buffer_ratio=capital_buffer_ratio,
        stress_loss_ratio=signal.stress_loss_ratio,
        stress_loss_buffer_gap_ratio=stress_loss_buffer_gap_ratio,
        market_probability_before=signal.market_probability_before,
        market_probability_after=signal.market_probability_after,
        probability_delta=probability_delta,
        redacted_capital_source_reference=_redacted_reference(
            signal.capital_source_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_count: Decimal,
    capital_buffer_ratio: Decimal,
    stress_loss_buffer_gap_ratio: Decimal,
    probability_delta: Decimal,
    observation_age_seconds: Decimal,
    config: MarketResearchBankCapitalBufferDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if capital_buffer_ratio < ZERO:
        reasons.append(CAPITAL_BUFFER_BREACH_REASON)
    if capital_buffer_ratio < config.minimum_capital_buffer_ratio:
        reasons.append(CAPITAL_BUFFER_THIN_REASON)
    if stress_loss_buffer_gap_ratio > ZERO:
        reasons.append(STRESS_LOSS_BUFFER_GAP_REASON)
    if observation_age_seconds > config.fresh_observation_max_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if abs(probability_delta) >= config.probability_repricing_threshold:
        reasons.append(PROBABILITY_REPRICING_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCE_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_row_reason_codes(tuple(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        CAPITAL_BUFFER_BREACH_REASON in reason_codes
        or STRESS_LOSS_BUFFER_GAP_REASON in reason_codes
        or THIN_SOURCE_REASON in reason_codes
    ):
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
        return STATUS_BLOCKED
    if blocked_observation_count > ZERO:
        return STATUS_BLOCKED
    if watch_observation_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _row_sort_key(row: MarketResearchBankCapitalBufferDigestRow) -> tuple[int, Decimal, str, str, str]:
    return (
        {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[row.capital_status],
        row.capital_buffer_ratio,
        row.bank_key,
        row.condition_id,
        row.research_key,
    )


def _reason_code_counts(
    rows: tuple[MarketResearchBankCapitalBufferDigestRow, ...],
) -> tuple[MarketResearchBankCapitalBufferDigestReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts[reason_code] + 1 if reason_code in counts else 1
    observation_count = _count(len(rows))
    return tuple(
        MarketResearchBankCapitalBufferDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            observation_ratio=_ratio(_count(counts[reason_code]), observation_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchBankCapitalBufferDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    previous_key: tuple[int, Decimal, str, str, str] | None = None
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchBankCapitalBufferDigestRow:
            raise ValueError("rows must contain MarketResearchBankCapitalBufferDigestRow")
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
) -> tuple[MarketResearchBankCapitalBufferDigestReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(values)
    previous_rank = -1
    for count in counts:
        if type(count) is not MarketResearchBankCapitalBufferDigestReasonCodeCount:
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


def _validate_row(row: MarketResearchBankCapitalBufferDigestRow) -> None:
    expected_capital_buffer_ratio = _finite_decimal(
        row.cet1_capital_ratio - row.minimum_capital_ratio,
    )
    if row.capital_buffer_ratio != expected_capital_buffer_ratio:
        raise ValueError("capital_buffer_ratio must match capital fields")
    expected_stress_loss_buffer_gap_ratio = _finite_decimal(
        max(row.stress_loss_ratio - row.capital_buffer_ratio, ZERO),
    )
    if row.stress_loss_buffer_gap_ratio != expected_stress_loss_buffer_gap_ratio:
        raise ValueError("stress_loss_buffer_gap_ratio must match capital fields")
    expected_probability_delta = _probability_delta(
        row.market_probability_after - row.market_probability_before,
    )
    if row.probability_delta != expected_probability_delta:
        raise ValueError("probability_delta must match probability fields")
    if row.capital_status != _row_status(row.reason_codes):
        raise ValueError("capital_status must match reason_codes")


def _validate_report(report: MarketResearchBankCapitalBufferDigestReport) -> None:
    if report.observation_count != _count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.ready_observation_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_observation_count must match rows")
    if report.watch_observation_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_observation_count must match rows")
    if report.blocked_observation_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_observation_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_counts = (
            MarketResearchBankCapitalBufferDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                observation_ratio=ZERO,
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
        "capital_buffer_breach_count",
        CAPITAL_BUFFER_BREACH_REASON,
    )
    _validate_report_metric(report, "capital_buffer_thin_count", CAPITAL_BUFFER_THIN_REASON)
    _validate_report_metric(
        report,
        "stress_loss_buffer_gap_count",
        STRESS_LOSS_BUFFER_GAP_REASON,
    )
    _validate_report_metric(report, "stale_observation_count", STALE_OBSERVATION_REASON)
    _validate_report_metric(report, "thin_source_count", THIN_SOURCE_REASON)
    _validate_report_metric(
        report,
        "probability_repricing_count",
        PROBABILITY_REPRICING_REASON,
    )
    if report.average_capital_buffer_ratio != _ratio(
        _sum_decimal(row.capital_buffer_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_capital_buffer_ratio must match rows")
    if report.min_capital_buffer_ratio != min(
        (row.capital_buffer_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_capital_buffer_ratio must match rows")
    if report.max_stress_loss_buffer_gap_ratio != max(
        (row.stress_loss_buffer_gap_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_stress_loss_buffer_gap_ratio must match rows")
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


def _validate_report_metric(
    report: MarketResearchBankCapitalBufferDigestReport,
    field_name: str,
    reason_code: str,
) -> None:
    expected = _reason_count(report.rows, reason_code)
    if getattr(report, field_name) != expected:
        raise ValueError(f"{field_name} must match rows")


def _status_count(
    rows: tuple[MarketResearchBankCapitalBufferDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.capital_status == status))


def _reason_count(
    rows: tuple[MarketResearchBankCapitalBufferDigestRow, ...],
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


def _require_probability_delta(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _require_six_decimal_value(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be a six-decimal Decimal")
    return value


def _is_six_decimal_string(value: str) -> bool:
    if value.startswith("-"):
        value = value[1:]
    left, dot, right = value.partition(".")
    return dot == "." and bool(left) and left.isdigit() and len(right) == 6 and right.isdigit()


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
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or 'value'} must be a supported public dataclass")
        _reject_unsafe_public_payload("value", value, path)
        return {
            field.name: _json_ready(
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
            for field in fields(value)
        }
    if type(value) is Decimal:
        return format(_require_six_decimal_value(path or "value", value), "f")
    if type(value) is datetime:
        if value.tzinfo is not UTC or value.utcoffset() is None:
            raise ValueError(f"{path or 'value'} must be UTC-aware")
        return value.isoformat()
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
    if type(value) is tuple:
        return [
            _json_ready(item, f"{path}[{index}]" if path else f"value[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, (list, dict, set, frozenset)):
        raise ValueError(f"{path or 'value'} must come from public dataclass fields")
    raise ValueError(f"{path or 'value'} is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} must be a supported public dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                item_path,
            )
        return
    if isinstance(value, Decimal):
        _require_six_decimal_value(path or label, value)
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
