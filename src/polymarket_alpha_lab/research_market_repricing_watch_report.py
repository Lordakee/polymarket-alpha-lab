"""Pure public repricing watch report for manual review."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_MARKET_REPRICING_WATCH_CONFIG_VERSION = (
    "research-market-repricing-watch-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_PREFIX = "repricing_watch_"
NO_OBSERVATIONS_REASON = f"{REASON_PREFIX}no_observations"
CLEAR_REASON = f"{REASON_PREFIX}clear"
PROBABILITY_MOVE_BLOCK_REASON = f"{REASON_PREFIX}probability_move_block"
PROBABILITY_MOVE_WATCH_REASON = f"{REASON_PREFIX}probability_move_watch"
PROBABILITY_MOVE_FRESHNESS_BLOCK_REASON = (
    f"{REASON_PREFIX}probability_move_freshness_block"
)
PROBABILITY_MOVE_FRESHNESS_WATCH_REASON = (
    f"{REASON_PREFIX}probability_move_freshness_watch"
)
SPREAD_COST_PRESSURE_BLOCK_REASON = f"{REASON_PREFIX}spread_cost_pressure_block"
SPREAD_COST_PRESSURE_WATCH_REASON = f"{REASON_PREFIX}spread_cost_pressure_watch"
EVIDENCE_LAG_BLOCK_REASON = f"{REASON_PREFIX}evidence_lag_block"
EVIDENCE_LAG_WATCH_REASON = f"{REASON_PREFIX}evidence_lag_watch"
MANUAL_RECHECK_BLOCK_REASON = f"{REASON_PREFIX}manual_recheck_block"
MANUAL_RECHECK_WATCH_REASON = f"{REASON_PREFIX}manual_recheck_watch"
RECHECK_URGENCY_BLOCK_REASON = f"{REASON_PREFIX}recheck_urgency_block"
RECHECK_URGENCY_WATCH_REASON = f"{REASON_PREFIX}recheck_urgency_watch"

REPORT_CLEAR_REASON = f"{REASON_PREFIX}report_clear"
REPORT_PROBABILITY_MOVE_REASON = f"{REASON_PREFIX}probability_move_detected"
REPORT_PROBABILITY_MOVE_FRESHNESS_REASON = (
    f"{REASON_PREFIX}probability_move_freshness_detected"
)
REPORT_SPREAD_COST_REASON = f"{REASON_PREFIX}spread_cost_pressure_detected"
REPORT_EVIDENCE_LAG_REASON = f"{REASON_PREFIX}evidence_lag_detected"
REPORT_MANUAL_RECHECK_REASON = f"{REASON_PREFIX}manual_recheck_required"
REPORT_RECHECK_URGENCY_REASON = f"{REASON_PREFIX}recheck_urgency_detected"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

PUBLIC_DENY_FRAGMENTS = (
    "market_id",
    "market_slug",
    "condition_id",
    "source_id",
    "source_url",
    "raw",
    "://",
    "?",
    "api_key",
    "secret",
    "credential",
    "session",
    "cookie",
    "bearer",
    "private" + "_key",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "bu" + "y",
    "se" + "ll",
    "recom" + "mend",
    "siz" + "ing",
)


__all__ = (
    "DEFAULT_RESEARCH_MARKET_REPRICING_WATCH_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketRepricingWatchConfig",
    "ResearchMarketRepricingWatchObservation",
    "ResearchMarketRepricingWatchReasonCodeCount",
    "ResearchMarketRepricingWatchReport",
    "ResearchMarketRepricingWatchRow",
    "build_research_market_repricing_watch_report",
    "research_market_repricing_watch_report_digest",
    "research_market_repricing_watch_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketRepricingWatchConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_REPRICING_WATCH_CONFIG_VERSION
    watch_probability_move_age_seconds: Decimal = Decimal("900.000000")
    block_probability_move_age_seconds: Decimal = Decimal("3600.000000")
    watch_probability_move_ratio: Decimal = Decimal("0.050000")
    block_probability_move_ratio: Decimal = Decimal("0.150000")
    watch_spread_cost_pressure: Decimal = Decimal("0.300000")
    block_spread_cost_pressure: Decimal = Decimal("0.700000")
    watch_evidence_lag_seconds: Decimal = Decimal("1800.000000")
    block_evidence_lag_seconds: Decimal = Decimal("7200.000000")
    watch_manual_recheck_score: Decimal = Decimal("0.300000")
    block_manual_recheck_score: Decimal = Decimal("0.700000")
    watch_recheck_urgency_score: Decimal = Decimal("0.300000")
    block_recheck_urgency_score: Decimal = Decimal("0.700000")
    probability_move_weight: Decimal = Decimal("0.250000")
    probability_move_freshness_weight: Decimal = Decimal("0.250000")
    spread_cost_weight: Decimal = Decimal("0.200000")
    evidence_lag_weight: Decimal = Decimal("0.200000")
    manual_recheck_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketRepricingWatchConfig:
            raise TypeError("ResearchMarketRepricingWatchConfig does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketRepricingWatchConfig, "config")
        _require_public_label("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MARKET_REPRICING_WATCH_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_probability_move_age_seconds",
            "block_probability_move_age_seconds",
            "watch_evidence_lag_seconds",
            "block_evidence_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_probability_move_ratio",
            "block_probability_move_ratio",
            "watch_spread_cost_pressure",
            "block_spread_cost_pressure",
            "watch_manual_recheck_score",
            "block_manual_recheck_score",
            "watch_recheck_urgency_score",
            "block_recheck_urgency_score",
            "probability_move_weight",
            "probability_move_freshness_weight",
            "spread_cost_weight",
            "evidence_lag_weight",
            "manual_recheck_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_increasing_threshold(
            "watch_probability_move_age_seconds",
            self.watch_probability_move_age_seconds,
            "block_probability_move_age_seconds",
            self.block_probability_move_age_seconds,
        )
        _require_increasing_threshold(
            "watch_probability_move_ratio",
            self.watch_probability_move_ratio,
            "block_probability_move_ratio",
            self.block_probability_move_ratio,
        )
        _require_increasing_threshold(
            "watch_spread_cost_pressure",
            self.watch_spread_cost_pressure,
            "block_spread_cost_pressure",
            self.block_spread_cost_pressure,
        )
        _require_increasing_threshold(
            "watch_evidence_lag_seconds",
            self.watch_evidence_lag_seconds,
            "block_evidence_lag_seconds",
            self.block_evidence_lag_seconds,
        )
        _require_increasing_threshold(
            "watch_manual_recheck_score",
            self.watch_manual_recheck_score,
            "block_manual_recheck_score",
            self.block_manual_recheck_score,
        )
        _require_increasing_threshold(
            "watch_recheck_urgency_score",
            self.watch_recheck_urgency_score,
            "block_recheck_urgency_score",
            self.block_recheck_urgency_score,
        )
        weight_sum = _quantize(
            self.probability_move_weight
            + self.probability_move_freshness_weight
            + self.spread_cost_weight
            + self.evidence_lag_weight
            + self.manual_recheck_weight,
        )
        if weight_sum != ONE:
            raise ValueError("repricing watch weights must sum to 1.000000")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketRepricingWatchObservation:
    public_bucket: str
    observed_at: datetime
    evidence_observed_at: datetime
    sample_count: Decimal
    probability_move_ratio: Decimal
    spread_cost_pressure_score: Decimal
    manual_recheck_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketRepricingWatchObservation:
            raise TypeError(
                "ResearchMarketRepricingWatchObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketRepricingWatchObservation, "observation")
        object.__setattr__(
            self,
            "public_bucket",
            _require_public_label("public_bucket", self.public_bucket),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        if self.evidence_observed_at > self.observed_at:
            raise ValueError("evidence_observed_at must be on or before observed_at")
        object.__setattr__(
            self,
            "sample_count",
            _require_positive_whole_decimal("sample_count", self.sample_count),
        )
        for field_name in (
            "probability_move_ratio",
            "spread_cost_pressure_score",
            "manual_recheck_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketRepricingWatchRow:
    public_bucket: str
    observed_at: datetime
    evidence_observed_at: datetime
    probability_move_age_seconds: Decimal
    evidence_lag_seconds: Decimal
    sample_count: Decimal
    probability_move_ratio: Decimal
    spread_cost_pressure_score: Decimal
    manual_recheck_score: Decimal
    probability_move_pressure: Decimal
    probability_move_freshness_pressure: Decimal
    spread_cost_pressure: Decimal
    evidence_lag_pressure: Decimal
    manual_recheck_pressure: Decimal
    recheck_urgency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketRepricingWatchRow:
            raise TypeError("ResearchMarketRepricingWatchRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketRepricingWatchRow, "row")
        object.__setattr__(
            self,
            "public_bucket",
            _require_public_label("public_bucket", self.public_bucket),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        for field_name in ("probability_move_age_seconds", "evidence_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sample_count",
            _require_positive_whole_decimal("sample_count", self.sample_count),
        )
        for field_name in (
            "probability_move_ratio",
            "spread_cost_pressure_score",
            "manual_recheck_score",
            "probability_move_pressure",
            "probability_move_freshness_pressure",
            "spread_cost_pressure",
            "evidence_lag_pressure",
            "manual_recheck_pressure",
            "recheck_urgency_score",
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
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketRepricingWatchReasonCodeCount:
    reason_code: str
    count: Decimal
    sample_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketRepricingWatchReasonCodeCount:
            raise TypeError(
                "ResearchMarketRepricingWatchReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketRepricingWatchReasonCodeCount, "count")
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "sample_ratio",
            _require_ratio_decimal("sample_ratio", self.sample_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketRepricingWatchReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    sample_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    probability_move_freshness_count: Decimal
    spread_cost_pressure_count: Decimal
    evidence_lag_count: Decimal
    manual_recheck_count: Decimal
    mean_probability_move_age_seconds: Decimal
    mean_evidence_lag_seconds: Decimal
    mean_probability_move_ratio: Decimal
    mean_spread_cost_pressure_score: Decimal
    mean_manual_recheck_score: Decimal
    mean_recheck_urgency_score: Decimal
    max_recheck_urgency_score: Decimal
    manual_recheck_required: bool
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketRepricingWatchReasonCodeCount, ...]
    rows: tuple[ResearchMarketRepricingWatchRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketRepricingWatchReport:
            raise TypeError("ResearchMarketRepricingWatchReport does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketRepricingWatchReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "sample_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "probability_move_freshness_count",
            "spread_cost_pressure_count",
            "evidence_lag_count",
            "manual_recheck_count",
            "mean_probability_move_age_seconds",
            "mean_evidence_lag_seconds",
            "mean_probability_move_ratio",
            "mean_spread_cost_pressure_score",
            "mean_manual_recheck_score",
            "mean_recheck_urgency_score",
            "max_recheck_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("manual_recheck_required", self.manual_recheck_required)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for reason_count in self.reason_code_counts:
            if type(reason_count) is not ResearchMarketRepricingWatchReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchMarketRepricingWatchReasonCodeCount",
                )
            _require_hard_flags("reason code count", reason_count)
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchMarketRepricingWatchRow:
                raise ValueError("rows must contain ResearchMarketRepricingWatchRow")
            _require_hard_flags("row", row)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_research_market_repricing_watch_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketRepricingWatchConfig,
    generated_at: datetime,
) -> ResearchMarketRepricingWatchReport:
    if type(config) is not ResearchMarketRepricingWatchConfig:
        raise ValueError("config must be a ResearchMarketRepricingWatchConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    row,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for row in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketRepricingWatchReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_count(len(input_rows)),
        sample_count=sum((row.sample_count for row in rows), ZERO),
        row_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, STATUS_PASS)),
        watch_count=_count(_status_count(rows, STATUS_WATCH)),
        block_count=_count(_status_count(rows, STATUS_BLOCK)),
        probability_move_freshness_count=_count(
            _reason_count(rows, PROBABILITY_MOVE_FRESHNESS_WATCH_REASON)
            + _reason_count(rows, PROBABILITY_MOVE_FRESHNESS_BLOCK_REASON),
        ),
        spread_cost_pressure_count=_count(
            _reason_count(rows, SPREAD_COST_PRESSURE_WATCH_REASON)
            + _reason_count(rows, SPREAD_COST_PRESSURE_BLOCK_REASON),
        ),
        evidence_lag_count=_count(
            _reason_count(rows, EVIDENCE_LAG_WATCH_REASON)
            + _reason_count(rows, EVIDENCE_LAG_BLOCK_REASON),
        ),
        manual_recheck_count=_count(
            _reason_count(rows, MANUAL_RECHECK_WATCH_REASON)
            + _reason_count(rows, MANUAL_RECHECK_BLOCK_REASON),
        ),
        mean_probability_move_age_seconds=_mean(
            tuple(row.probability_move_age_seconds for row in rows),
        ),
        mean_evidence_lag_seconds=_mean(tuple(row.evidence_lag_seconds for row in rows)),
        mean_probability_move_ratio=_mean(tuple(row.probability_move_ratio for row in rows)),
        mean_spread_cost_pressure_score=_mean(
            tuple(row.spread_cost_pressure_score for row in rows),
        ),
        mean_manual_recheck_score=_mean(tuple(row.manual_recheck_score for row in rows)),
        mean_recheck_urgency_score=_mean(tuple(row.recheck_urgency_score for row in rows)),
        max_recheck_urgency_score=max(
            (row.recheck_urgency_score for row in rows),
            default=ZERO,
        ),
        manual_recheck_required=_manual_recheck_required(rows),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def research_market_repricing_watch_report_payload(
    report: ResearchMarketRepricingWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketRepricingWatchReport:
        _require_hard_flags("report", report)
        _validate_report_consistency(report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchMarketRepricingWatchReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_payload("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


def research_market_repricing_watch_report_digest(
    report: ResearchMarketRepricingWatchReport | dict[str, Any],
) -> str:
    payload = research_market_repricing_watch_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


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


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketRepricingWatchObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    rows = tuple(observations)
    for row in rows:
        if type(row) is not ResearchMarketRepricingWatchObservation:
            raise ValueError(
                "observations must contain ResearchMarketRepricingWatchObservation",
            )
        _require_hard_flags("observation", row)
    return rows


def _row_from_observation(
    row: ResearchMarketRepricingWatchObservation,
    *,
    config: ResearchMarketRepricingWatchConfig,
    generated_at: datetime,
) -> ResearchMarketRepricingWatchRow:
    probability_move_age_seconds = _age_seconds(row.observed_at, generated_at)
    evidence_lag_seconds = _age_seconds(row.evidence_observed_at, row.observed_at)
    probability_move_pressure = _threshold_pressure(
        row.probability_move_ratio,
        watch_value=config.watch_probability_move_ratio,
        block_value=config.block_probability_move_ratio,
    )
    probability_move_freshness_pressure = _threshold_pressure(
        probability_move_age_seconds,
        watch_value=config.watch_probability_move_age_seconds,
        block_value=config.block_probability_move_age_seconds,
    )
    spread_cost_pressure = _threshold_pressure(
        row.spread_cost_pressure_score,
        watch_value=config.watch_spread_cost_pressure,
        block_value=config.block_spread_cost_pressure,
    )
    evidence_lag_pressure = _threshold_pressure(
        evidence_lag_seconds,
        watch_value=config.watch_evidence_lag_seconds,
        block_value=config.block_evidence_lag_seconds,
    )
    manual_recheck_pressure = _threshold_pressure(
        row.manual_recheck_score,
        watch_value=config.watch_manual_recheck_score,
        block_value=config.block_manual_recheck_score,
    )
    recheck_urgency_score = _recheck_urgency_score(
        probability_move_pressure=probability_move_pressure,
        probability_move_freshness_pressure=probability_move_freshness_pressure,
        spread_cost_pressure=spread_cost_pressure,
        evidence_lag_pressure=evidence_lag_pressure,
        manual_recheck_pressure=manual_recheck_pressure,
        config=config,
    )
    status = _row_status(
        row,
        probability_move_age_seconds=probability_move_age_seconds,
        evidence_lag_seconds=evidence_lag_seconds,
        recheck_urgency_score=recheck_urgency_score,
        config=config,
    )
    return ResearchMarketRepricingWatchRow(
        public_bucket=row.public_bucket,
        observed_at=row.observed_at,
        evidence_observed_at=row.evidence_observed_at,
        probability_move_age_seconds=probability_move_age_seconds,
        evidence_lag_seconds=evidence_lag_seconds,
        sample_count=row.sample_count,
        probability_move_ratio=row.probability_move_ratio,
        spread_cost_pressure_score=row.spread_cost_pressure_score,
        manual_recheck_score=row.manual_recheck_score,
        probability_move_pressure=probability_move_pressure,
        probability_move_freshness_pressure=probability_move_freshness_pressure,
        spread_cost_pressure=spread_cost_pressure,
        evidence_lag_pressure=evidence_lag_pressure,
        manual_recheck_pressure=manual_recheck_pressure,
        recheck_urgency_score=recheck_urgency_score,
        status=status,
        reason_codes=_row_reason_codes(
            row,
            probability_move_age_seconds=probability_move_age_seconds,
            evidence_lag_seconds=evidence_lag_seconds,
            recheck_urgency_score=recheck_urgency_score,
            status=status,
            config=config,
        ),
    )


def _row_status(
    row: ResearchMarketRepricingWatchObservation,
    *,
    probability_move_age_seconds: Decimal,
    evidence_lag_seconds: Decimal,
    recheck_urgency_score: Decimal,
    config: ResearchMarketRepricingWatchConfig,
) -> str:
    if (
        row.probability_move_ratio >= config.block_probability_move_ratio
        or probability_move_age_seconds >= config.block_probability_move_age_seconds
        or row.spread_cost_pressure_score >= config.block_spread_cost_pressure
        or evidence_lag_seconds >= config.block_evidence_lag_seconds
        or row.manual_recheck_score >= config.block_manual_recheck_score
        or recheck_urgency_score >= config.block_recheck_urgency_score
    ):
        return STATUS_BLOCK
    if (
        row.reason_codes
        or row.probability_move_ratio >= config.watch_probability_move_ratio
        or probability_move_age_seconds >= config.watch_probability_move_age_seconds
        or row.spread_cost_pressure_score >= config.watch_spread_cost_pressure
        or evidence_lag_seconds >= config.watch_evidence_lag_seconds
        or row.manual_recheck_score >= config.watch_manual_recheck_score
        or recheck_urgency_score >= config.watch_recheck_urgency_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    row: ResearchMarketRepricingWatchObservation,
    *,
    probability_move_age_seconds: Decimal,
    evidence_lag_seconds: Decimal,
    recheck_urgency_score: Decimal,
    status: str,
    config: ResearchMarketRepricingWatchConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = list(row.reason_codes)
    if row.probability_move_ratio >= config.block_probability_move_ratio:
        reason_codes.append(PROBABILITY_MOVE_BLOCK_REASON)
    elif row.probability_move_ratio >= config.watch_probability_move_ratio:
        reason_codes.append(PROBABILITY_MOVE_WATCH_REASON)
    if probability_move_age_seconds >= config.block_probability_move_age_seconds:
        reason_codes.append(PROBABILITY_MOVE_FRESHNESS_BLOCK_REASON)
    elif probability_move_age_seconds >= config.watch_probability_move_age_seconds:
        reason_codes.append(PROBABILITY_MOVE_FRESHNESS_WATCH_REASON)
    if row.spread_cost_pressure_score >= config.block_spread_cost_pressure:
        reason_codes.append(SPREAD_COST_PRESSURE_BLOCK_REASON)
    elif row.spread_cost_pressure_score >= config.watch_spread_cost_pressure:
        reason_codes.append(SPREAD_COST_PRESSURE_WATCH_REASON)
    if evidence_lag_seconds >= config.block_evidence_lag_seconds:
        reason_codes.append(EVIDENCE_LAG_BLOCK_REASON)
    elif evidence_lag_seconds >= config.watch_evidence_lag_seconds:
        reason_codes.append(EVIDENCE_LAG_WATCH_REASON)
    if row.manual_recheck_score >= config.block_manual_recheck_score:
        reason_codes.append(MANUAL_RECHECK_BLOCK_REASON)
    elif row.manual_recheck_score >= config.watch_manual_recheck_score:
        reason_codes.append(MANUAL_RECHECK_WATCH_REASON)
    if recheck_urgency_score >= config.block_recheck_urgency_score:
        reason_codes.append(RECHECK_URGENCY_BLOCK_REASON)
    elif recheck_urgency_score >= config.watch_recheck_urgency_score:
        reason_codes.append(RECHECK_URGENCY_WATCH_REASON)
    if status == STATUS_PASS and not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _report_reason_codes(
    rows: tuple[ResearchMarketRepricingWatchRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_OBSERVATIONS_REASON,)
    reason_codes: list[str] = []
    if any(
        PROBABILITY_MOVE_WATCH_REASON in row.reason_codes
        or PROBABILITY_MOVE_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_PROBABILITY_MOVE_REASON)
    if any(
        PROBABILITY_MOVE_FRESHNESS_WATCH_REASON in row.reason_codes
        or PROBABILITY_MOVE_FRESHNESS_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_PROBABILITY_MOVE_FRESHNESS_REASON)
    if any(
        SPREAD_COST_PRESSURE_WATCH_REASON in row.reason_codes
        or SPREAD_COST_PRESSURE_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_SPREAD_COST_REASON)
    if any(
        EVIDENCE_LAG_WATCH_REASON in row.reason_codes
        or EVIDENCE_LAG_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_EVIDENCE_LAG_REASON)
    if any(
        MANUAL_RECHECK_WATCH_REASON in row.reason_codes
        or MANUAL_RECHECK_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_MANUAL_RECHECK_REASON)
    if any(
        RECHECK_URGENCY_WATCH_REASON in row.reason_codes
        or RECHECK_URGENCY_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_RECHECK_URGENCY_REASON)
    if any(row.status != STATUS_PASS or row.reason_codes[0].startswith("input_") for row in rows):
        if REPORT_MANUAL_RECHECK_REASON not in reason_codes:
            reason_codes.append(REPORT_MANUAL_RECHECK_REASON)
    if not reason_codes:
        reason_codes.append(REPORT_CLEAR_REASON)
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _reason_code_counts(
    rows: tuple[ResearchMarketRepricingWatchRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketRepricingWatchReasonCodeCount, ...]:
    if not rows:
        return tuple(
            ResearchMarketRepricingWatchReasonCodeCount(
                reason_code=reason_code,
                count=ONE,
                sample_ratio=ZERO,
            )
            for reason_code in report_reason_codes
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = _count(len(rows))
    return tuple(
        ResearchMarketRepricingWatchReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            sample_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items())
    )


def _validate_row_consistency(row: ResearchMarketRepricingWatchRow) -> None:
    if row.status == STATUS_PASS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must contain only the clear reason")
    if RECHECK_URGENCY_BLOCK_REASON in row.reason_codes and row.status != STATUS_BLOCK:
        raise ValueError("recheck urgency block reason requires block status")


def _validate_report_consistency(report: ResearchMarketRepricingWatchReport) -> None:
    rows = report.rows
    for row in rows:
        _require_hard_flags("row", row)
    for reason_count in report.reason_code_counts:
        _require_hard_flags("reason code count", reason_count)
    if report.observation_count != _count(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.row_count != _count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.sample_count != sum((row.sample_count for row in rows), ZERO):
        raise ValueError("sample_count must match rows")
    if report.pass_count != _count(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.mean_recheck_urgency_score != _mean(
        tuple(row.recheck_urgency_score for row in rows),
    ):
        raise ValueError("mean_recheck_urgency_score must match rows")
    if report.max_recheck_urgency_score != max(
        (row.recheck_urgency_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_recheck_urgency_score must match rows")
    if report.manual_recheck_required is not _manual_recheck_required(rows):
        raise ValueError("manual_recheck_required must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _manual_recheck_required(rows: tuple[ResearchMarketRepricingWatchRow, ...]) -> bool:
    if not rows:
        return True
    return any(row.status != STATUS_PASS for row in rows)


def _report_status(rows: tuple[ResearchMarketRepricingWatchRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(rows: tuple[ResearchMarketRepricingWatchRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(rows: tuple[ResearchMarketRepricingWatchRow, ...], reason_code: str) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _row_sort_key(row: ResearchMarketRepricingWatchRow) -> tuple[int, str, datetime]:
    return (STATUS_RANK[row.status], row.public_bucket, row.observed_at)


def _recheck_urgency_score(
    *,
    probability_move_pressure: Decimal,
    probability_move_freshness_pressure: Decimal,
    spread_cost_pressure: Decimal,
    evidence_lag_pressure: Decimal,
    manual_recheck_pressure: Decimal,
    config: ResearchMarketRepricingWatchConfig,
) -> Decimal:
    weighted = _clamp_ratio(
        probability_move_pressure * config.probability_move_weight
        + probability_move_freshness_pressure * config.probability_move_freshness_weight
        + spread_cost_pressure * config.spread_cost_weight
        + evidence_lag_pressure * config.evidence_lag_weight
        + manual_recheck_pressure * config.manual_recheck_weight,
    )
    if weighted < config.block_recheck_urgency_score:
        return weighted
    direct_peak = max(
        probability_move_pressure,
        spread_cost_pressure,
        manual_recheck_pressure,
    )
    return max(weighted, direct_peak)


def _threshold_pressure(
    value: Decimal,
    *,
    watch_value: Decimal,
    block_value: Decimal,
) -> Decimal:
    if value <= watch_value:
        return ZERO
    if value >= block_value:
        return ONE
    return _clamp_ratio((value - watch_value) / (block_value - watch_value))


def _age_seconds(older_at: datetime, newer_at: datetime) -> Decimal:
    if older_at > newer_at:
        raise ValueError("older timestamp must be on or before newer timestamp")
    delta = newer_at - older_at
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    )
    return _quantize(seconds)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty")
    if not re.fullmatch(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,191}$", value):
        raise ValueError(f"{field_name} must be public")
    _reject_unsafe_public_text(field_name, value)
    return value


def _normalize_input_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    normalized: list[str] = []
    for reason_code in _normalize_reason_codes(reason_codes, allow_empty=allow_empty):
        if reason_code.startswith("input_"):
            prefixed = reason_code
        else:
            prefixed = f"input_{reason_code}"
        if prefixed not in normalized:
            normalized.append(prefixed)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        public_reason = _require_reason_code("reason_code", reason_code)
        if public_reason not in normalized:
            normalized.append(public_reason)
    return tuple(normalized)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in PUBLIC_DENY_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
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
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_increasing_threshold(
    watch_field_name: str,
    watch_value: Decimal,
    block_field_name: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_field_name} must exceed {watch_field_name}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) in (str, int, bool):
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


def _reject_unsafe_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)
