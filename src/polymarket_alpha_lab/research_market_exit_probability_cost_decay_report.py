"""Pure report-only exit probability cost decay reducer for manual research."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "MARKET_EXIT_PROBABILITY_COST_DECAY_STATUSES",
    "DEFAULT_RESEARCH_MARKET_EXIT_PROBABILITY_COST_DECAY_REPORT_CONFIG_VERSION",
    "ResearchMarketExitProbabilityCostDecayConfig",
    "ResearchMarketExitProbabilityCostDecayObservation",
    "ResearchMarketExitProbabilityCostDecayReasonCodeCount",
    "ResearchMarketExitProbabilityCostDecayReport",
    "ResearchMarketExitProbabilityCostDecayRow",
    "build_research_market_exit_probability_cost_decay_report",
    "research_market_exit_probability_cost_decay_report_digest",
    "research_market_exit_probability_cost_decay_report_payload",
)


DEFAULT_RESEARCH_MARKET_EXIT_PROBABILITY_COST_DECAY_REPORT_CONFIG_VERSION = (
    "research-market-exit-probability-cost-decay-report-v0"
)

MARKET_EXIT_PROBABILITY_COST_DECAY_STATUSES = ("pass", "watch", "block")
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
MISSING_INPUTS_REASON = "no_exit_probability_cost_decay_observations"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
PRIVATE_REF_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,512}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
HEX_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")

REPORT_PAYLOAD_KEYS = frozenset(
    {
        "generated_at",
        "config_version",
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_total_exit_cost_rate",
        "average_probability_decay_rate",
        "average_net_probability_after_cost_decay_rate",
        "average_exit_probability_cost_decay_score",
        "max_total_exit_cost_rate",
        "max_probability_decay_rate",
        "min_net_probability_after_cost_decay_rate",
        "max_cost_decay_to_probability_ratio",
        "status",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
        "derived_validation_digest",
    },
)

ROW_PAYLOAD_KEYS = frozenset(
    {
        "public_row_ref",
        "signal_ref_digest",
        "observed_at",
        "reference_probability",
        "current_probability",
        "probability_decay_rate",
        "exit_fee_rate",
        "exit_spread_rate",
        "exit_slippage_rate",
        "total_exit_cost_rate",
        "net_probability_after_cost_decay_rate",
        "cost_decay_to_probability_ratio",
        "exit_cost_score",
        "probability_decay_score",
        "net_buffer_score",
        "cost_decay_ratio_score",
        "exit_probability_cost_decay_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
        "row_validation_digest",
    },
)

REASON_COUNT_PAYLOAD_KEYS = frozenset(
    {
        "reason_code",
        "count",
        "row_ratio",
        "paper_only",
        "report_only",
        "readonly",
    },
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate"),
    _join_parts("can", "didate", "_", "id"),
    _join_parts("con", "dition", "_", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "-", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ma", "rket", "-", "sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "url"),
    _join_parts("sour", "ce", "_", "text"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
    "://",
    "@",
    "=",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchMarketExitProbabilityCostDecayConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_EXIT_PROBABILITY_COST_DECAY_REPORT_CONFIG_VERSION
    )
    max_pass_exit_cost_rate: Decimal = Decimal("0.030000")
    max_watch_exit_cost_rate: Decimal = Decimal("0.070000")
    max_pass_probability_decay_rate: Decimal = Decimal("0.040000")
    max_watch_probability_decay_rate: Decimal = Decimal("0.120000")
    min_pass_net_probability_after_cost_decay_rate: Decimal = Decimal("0.050000")
    min_watch_net_probability_after_cost_decay_rate: Decimal = Decimal("0.000000")
    max_pass_cost_decay_to_probability_ratio: Decimal = Decimal("0.250000")
    max_watch_cost_decay_to_probability_ratio: Decimal = Decimal("0.600000")
    pass_exit_probability_cost_decay_score: Decimal = Decimal("0.750000")
    watch_exit_probability_cost_decay_score: Decimal = Decimal("0.450000")
    exit_cost_weight: Decimal = Decimal("0.350000")
    probability_decay_weight: Decimal = Decimal("0.300000")
    net_buffer_weight: Decimal = Decimal("0.200000")
    cost_decay_ratio_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExitProbabilityCostDecayConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_EXIT_PROBABILITY_COST_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "max_pass_exit_cost_rate",
            "max_watch_exit_cost_rate",
            "max_pass_probability_decay_rate",
            "max_watch_probability_decay_rate",
            "min_pass_net_probability_after_cost_decay_rate",
            "min_watch_net_probability_after_cost_decay_rate",
            "max_pass_cost_decay_to_probability_ratio",
            "max_watch_cost_decay_to_probability_ratio",
            "pass_exit_probability_cost_decay_score",
            "watch_exit_probability_cost_decay_score",
            "exit_cost_weight",
            "probability_decay_weight",
            "net_buffer_weight",
            "cost_decay_ratio_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_watch_exit_cost_rate <= self.max_pass_exit_cost_rate:
            raise ValueError("max_watch_exit_cost_rate must exceed pass threshold")
        if self.max_watch_probability_decay_rate <= self.max_pass_probability_decay_rate:
            raise ValueError("max_watch_probability_decay_rate must exceed pass threshold")
        if (
            self.min_pass_net_probability_after_cost_decay_rate
            <= self.min_watch_net_probability_after_cost_decay_rate
        ):
            raise ValueError("pass net probability threshold must exceed watch threshold")
        if (
            self.max_watch_cost_decay_to_probability_ratio
            <= self.max_pass_cost_decay_to_probability_ratio
        ):
            raise ValueError(
                "max_watch_cost_decay_to_probability_ratio must exceed pass threshold",
            )
        if (
            self.pass_exit_probability_cost_decay_score
            <= self.watch_exit_probability_cost_decay_score
        ):
            raise ValueError("pass score must exceed watch score")
        weight_sum = _quantize(
            self.exit_cost_weight
            + self.probability_decay_weight
            + self.net_buffer_weight
            + self.cost_decay_ratio_weight,
        )
        if weight_sum != ONE:
            raise ValueError("exit probability cost decay score weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketExitProbabilityCostDecayObservation(_FinalDataclass):
    internal_signal_ref: str
    observed_at: datetime
    reference_probability: Decimal
    current_probability: Decimal
    exit_fee_rate: Decimal
    exit_spread_rate: Decimal
    exit_slippage_rate: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketExitProbabilityCostDecayObservation,
            "observation",
        )
        _require_private_reference("internal_signal_ref", self.internal_signal_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reference_probability",
            _require_positive_probability_decimal(
                "reference_probability",
                self.reference_probability,
            ),
        )
        object.__setattr__(
            self,
            "current_probability",
            _require_positive_probability_decimal(
                "current_probability",
                self.current_probability,
            ),
        )
        if self.current_probability > self.reference_probability:
            raise ValueError("current_probability must not exceed reference_probability")
        for field_name in ("exit_fee_rate", "exit_spread_rate", "exit_slippage_rate"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketExitProbabilityCostDecayRow(_FinalDataclass):
    public_row_ref: str
    signal_ref_digest: str
    observed_at: datetime
    reference_probability: Decimal
    current_probability: Decimal
    probability_decay_rate: Decimal
    exit_fee_rate: Decimal
    exit_spread_rate: Decimal
    exit_slippage_rate: Decimal
    total_exit_cost_rate: Decimal
    net_probability_after_cost_decay_rate: Decimal
    cost_decay_to_probability_ratio: Decimal
    exit_cost_score: Decimal
    probability_decay_score: Decimal
    net_buffer_score: Decimal
    cost_decay_ratio_score: Decimal
    exit_probability_cost_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    row_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExitProbabilityCostDecayRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        _require_hex_digest("signal_ref_digest", self.signal_ref_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "reference_probability",
            "current_probability",
            "probability_decay_rate",
            "exit_fee_rate",
            "exit_spread_rate",
            "exit_slippage_rate",
            "total_exit_cost_rate",
            "cost_decay_to_probability_ratio",
            "exit_cost_score",
            "probability_decay_score",
            "net_buffer_score",
            "cost_decay_ratio_score",
            "exit_probability_cost_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "net_probability_after_cost_decay_rate",
            _require_decimal(
                "net_probability_after_cost_decay_rate",
                self.net_probability_after_cost_decay_rate,
            ),
        )
        for field_name in (
            "reference_probability",
            "current_probability",
            "probability_decay_rate",
            "exit_fee_rate",
            "exit_spread_rate",
            "exit_slippage_rate",
            "total_exit_cost_rate",
            "exit_cost_score",
            "probability_decay_score",
            "net_buffer_score",
            "cost_decay_ratio_score",
            "exit_probability_cost_decay_score",
        ):
            _require_probability_decimal(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _validate_row(self)
        expected_digest = _row_validation_digest(self)
        if self.row_validation_digest:
            _require_hex_digest("row_validation_digest", self.row_validation_digest)
            if self.row_validation_digest != expected_digest:
                raise ValueError("row_validation_digest must match row fields")
        else:
            object.__setattr__(self, "row_validation_digest", expected_digest)


@dataclass(frozen=True)
class ResearchMarketExitProbabilityCostDecayReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketExitProbabilityCostDecayReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(self, "reason_code", _normalize_reason_code(self.reason_code))
        object.__setattr__(self, "count", _require_positive_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_probability_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketExitProbabilityCostDecayReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_total_exit_cost_rate: Decimal | None
    average_probability_decay_rate: Decimal | None
    average_net_probability_after_cost_decay_rate: Decimal | None
    average_exit_probability_cost_decay_score: Decimal | None
    max_total_exit_cost_rate: Decimal
    max_probability_decay_rate: Decimal
    min_net_probability_after_cost_decay_rate: Decimal
    max_cost_decay_to_probability_ratio: Decimal
    status: str
    rows: tuple[ResearchMarketExitProbabilityCostDecayRow, ...]
    reason_code_counts: tuple[ResearchMarketExitProbabilityCostDecayReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExitProbabilityCostDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_EXIT_PROBABILITY_COST_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
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
        for field_name in (
            "average_total_exit_cost_rate",
            "average_probability_decay_rate",
            "average_exit_probability_cost_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_net_probability_after_cost_decay_rate",
            _require_optional_decimal(
                "average_net_probability_after_cost_decay_rate",
                self.average_net_probability_after_cost_decay_rate,
            ),
        )
        for field_name in (
            "max_total_exit_cost_rate",
            "max_probability_decay_rate",
            "max_cost_decay_to_probability_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_net_probability_after_cost_decay_rate",
            _require_decimal(
                "min_net_probability_after_cost_decay_rate",
                self.min_net_probability_after_cost_decay_rate,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _report_validation_digest(self)
        if self.derived_validation_digest:
            _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_market_exit_probability_cost_decay_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketExitProbabilityCostDecayConfig,
    generated_at: datetime,
) -> ResearchMarketExitProbabilityCostDecayReport:
    if type(config) is not ResearchMarketExitProbabilityCostDecayConfig:
        raise ValueError("config must be a ResearchMarketExitProbabilityCostDecayConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    for item in items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows_without_refs = tuple(
        _row_from_observation(item, config=config) for item in items
    )
    sorted_rows = tuple(
        sorted(
            rows_without_refs,
            key=lambda row: (
                _status_sort_value(row.status),
                row.net_probability_after_cost_decay_rate,
                -row.cost_decay_to_probability_ratio,
                row.signal_ref_digest,
                row.observed_at.isoformat(),
            ),
        ),
    )
    rows = tuple(
        _replace_row_ref(
            row,
            public_row_ref=f"exit_probability_cost_decay_row_{index:03d}",
        )
        for index, row in enumerate(sorted_rows, start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketExitProbabilityCostDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, STATUS_PASS)),
        watch_count=_decimal_count(_status_count(rows, STATUS_WATCH)),
        block_count=_decimal_count(_status_count(rows, STATUS_BLOCK)),
        average_total_exit_cost_rate=_average_row_value(rows, "total_exit_cost_rate"),
        average_probability_decay_rate=_average_row_value(
            rows,
            "probability_decay_rate",
        ),
        average_net_probability_after_cost_decay_rate=_average_row_value(
            rows,
            "net_probability_after_cost_decay_rate",
        ),
        average_exit_probability_cost_decay_score=_average_row_value(
            rows,
            "exit_probability_cost_decay_score",
        ),
        max_total_exit_cost_rate=_maximum_row_value(rows, "total_exit_cost_rate"),
        max_probability_decay_rate=_maximum_row_value(rows, "probability_decay_rate"),
        min_net_probability_after_cost_decay_rate=_minimum_row_value(
            rows,
            "net_probability_after_cost_decay_rate",
        ),
        max_cost_decay_to_probability_ratio=_maximum_row_value(
            rows,
            "cost_decay_to_probability_ratio",
        ),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_exit_probability_cost_decay_report_payload(
    report: ResearchMarketExitProbabilityCostDecayReport | Mapping[str, object],
) -> "FrozenJsonObject":
    if type(report) is ResearchMarketExitProbabilityCostDecayReport:
        _require_hard_flags("report", report)
        expected_digest = _report_validation_digest(report)
        if report.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        payload = _report_payload(report)
        _validate_public_payload(payload)
        return _freeze_json_object(payload)
    if type(report) is dict:
        _validate_public_payload(report)
        return _freeze_json_object(dict(report))
    raise ValueError(
        "report must be a ResearchMarketExitProbabilityCostDecayReport or payload dict",
    )


def research_market_exit_probability_cost_decay_report_digest(
    report: ResearchMarketExitProbabilityCostDecayReport,
) -> str:
    if type(report) is not ResearchMarketExitProbabilityCostDecayReport:
        raise ValueError("report must be a ResearchMarketExitProbabilityCostDecayReport")
    _require_hard_flags("report", report)
    expected_digest = _report_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    return expected_digest


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def _row_from_observation(
    observation: ResearchMarketExitProbabilityCostDecayObservation,
    *,
    config: ResearchMarketExitProbabilityCostDecayConfig,
) -> ResearchMarketExitProbabilityCostDecayRow:
    total_exit_cost_rate = _quantize(
        observation.exit_fee_rate
        + observation.exit_spread_rate
        + observation.exit_slippage_rate,
    )
    probability_decay_rate = _quantize(
        observation.reference_probability - observation.current_probability,
    )
    net_probability_after_cost_decay_rate = _quantize(
        observation.current_probability - total_exit_cost_rate - probability_decay_rate,
    )
    cost_decay_to_probability_ratio = _ratio(
        _quantize(total_exit_cost_rate + probability_decay_rate),
        observation.current_probability,
    )
    exit_cost_score = _inverse_ratio_score(
        total_exit_cost_rate,
        config.max_watch_exit_cost_rate,
    )
    probability_decay_score = _inverse_ratio_score(
        probability_decay_rate,
        config.max_watch_probability_decay_rate,
    )
    net_buffer_score = _range_score(
        net_probability_after_cost_decay_rate,
        config.min_watch_net_probability_after_cost_decay_rate,
        config.min_pass_net_probability_after_cost_decay_rate,
    )
    cost_decay_ratio_score = _inverse_ratio_score(
        cost_decay_to_probability_ratio,
        config.max_watch_cost_decay_to_probability_ratio,
    )
    exit_probability_cost_decay_score = _exit_probability_cost_decay_score(
        exit_cost_score=exit_cost_score,
        probability_decay_score=probability_decay_score,
        net_buffer_score=net_buffer_score,
        cost_decay_ratio_score=cost_decay_ratio_score,
        config=config,
    )
    status = _row_status(
        total_exit_cost_rate=total_exit_cost_rate,
        probability_decay_rate=probability_decay_rate,
        net_probability_after_cost_decay_rate=net_probability_after_cost_decay_rate,
        cost_decay_to_probability_ratio=cost_decay_to_probability_ratio,
        exit_probability_cost_decay_score=exit_probability_cost_decay_score,
        config=config,
    )
    return ResearchMarketExitProbabilityCostDecayRow(
        public_row_ref="exit_probability_cost_decay_row_pending",
        signal_ref_digest=_private_reference_digest(observation.internal_signal_ref),
        observed_at=observation.observed_at,
        reference_probability=observation.reference_probability,
        current_probability=observation.current_probability,
        probability_decay_rate=probability_decay_rate,
        exit_fee_rate=observation.exit_fee_rate,
        exit_spread_rate=observation.exit_spread_rate,
        exit_slippage_rate=observation.exit_slippage_rate,
        total_exit_cost_rate=total_exit_cost_rate,
        net_probability_after_cost_decay_rate=net_probability_after_cost_decay_rate,
        cost_decay_to_probability_ratio=cost_decay_to_probability_ratio,
        exit_cost_score=exit_cost_score,
        probability_decay_score=probability_decay_score,
        net_buffer_score=net_buffer_score,
        cost_decay_ratio_score=cost_decay_ratio_score,
        exit_probability_cost_decay_score=exit_probability_cost_decay_score,
        status=status,
        reason_codes=_row_reason_codes(
            total_exit_cost_rate=total_exit_cost_rate,
            probability_decay_rate=probability_decay_rate,
            net_probability_after_cost_decay_rate=net_probability_after_cost_decay_rate,
            cost_decay_to_probability_ratio=cost_decay_to_probability_ratio,
            status=status,
            input_reason_codes=observation.reason_codes,
            config=config,
        ),
    )


def _replace_row_ref(
    row: ResearchMarketExitProbabilityCostDecayRow,
    *,
    public_row_ref: str,
) -> ResearchMarketExitProbabilityCostDecayRow:
    return ResearchMarketExitProbabilityCostDecayRow(
        public_row_ref=public_row_ref,
        signal_ref_digest=row.signal_ref_digest,
        observed_at=row.observed_at,
        reference_probability=row.reference_probability,
        current_probability=row.current_probability,
        probability_decay_rate=row.probability_decay_rate,
        exit_fee_rate=row.exit_fee_rate,
        exit_spread_rate=row.exit_spread_rate,
        exit_slippage_rate=row.exit_slippage_rate,
        total_exit_cost_rate=row.total_exit_cost_rate,
        net_probability_after_cost_decay_rate=row.net_probability_after_cost_decay_rate,
        cost_decay_to_probability_ratio=row.cost_decay_to_probability_ratio,
        exit_cost_score=row.exit_cost_score,
        probability_decay_score=row.probability_decay_score,
        net_buffer_score=row.net_buffer_score,
        cost_decay_ratio_score=row.cost_decay_ratio_score,
        exit_probability_cost_decay_score=row.exit_probability_cost_decay_score,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _exit_probability_cost_decay_score(
    *,
    exit_cost_score: Decimal,
    probability_decay_score: Decimal,
    net_buffer_score: Decimal,
    cost_decay_ratio_score: Decimal,
    config: ResearchMarketExitProbabilityCostDecayConfig,
) -> Decimal:
    return _quantize(
        exit_cost_score * config.exit_cost_weight
        + probability_decay_score * config.probability_decay_weight
        + net_buffer_score * config.net_buffer_weight
        + cost_decay_ratio_score * config.cost_decay_ratio_weight,
    )


def _row_status(
    *,
    total_exit_cost_rate: Decimal,
    probability_decay_rate: Decimal,
    net_probability_after_cost_decay_rate: Decimal,
    cost_decay_to_probability_ratio: Decimal,
    exit_probability_cost_decay_score: Decimal,
    config: ResearchMarketExitProbabilityCostDecayConfig,
) -> str:
    if (
        exit_probability_cost_decay_score < config.watch_exit_probability_cost_decay_score
        or total_exit_cost_rate >= config.max_watch_exit_cost_rate
        or probability_decay_rate >= config.max_watch_probability_decay_rate
        or (
            net_probability_after_cost_decay_rate
            < config.min_watch_net_probability_after_cost_decay_rate
        )
        or cost_decay_to_probability_ratio >= config.max_watch_cost_decay_to_probability_ratio
    ):
        return STATUS_BLOCK
    if (
        exit_probability_cost_decay_score < config.pass_exit_probability_cost_decay_score
        or total_exit_cost_rate >= config.max_pass_exit_cost_rate
        or probability_decay_rate >= config.max_pass_probability_decay_rate
        or (
            net_probability_after_cost_decay_rate
            < config.min_pass_net_probability_after_cost_decay_rate
        )
        or cost_decay_to_probability_ratio >= config.max_pass_cost_decay_to_probability_ratio
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    total_exit_cost_rate: Decimal,
    probability_decay_rate: Decimal,
    net_probability_after_cost_decay_rate: Decimal,
    cost_decay_to_probability_ratio: Decimal,
    status: str,
    input_reason_codes: tuple[str, ...],
    config: ResearchMarketExitProbabilityCostDecayConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"exit_probability_cost_decay_{status}"}
    reason_codes.add(
        _upper_threshold_reason(
            "exit_cost_pressure",
            total_exit_cost_rate,
            config.max_pass_exit_cost_rate,
            config.max_watch_exit_cost_rate,
        ),
    )
    reason_codes.add(
        _upper_threshold_reason(
            "probability_decay",
            probability_decay_rate,
            config.max_pass_probability_decay_rate,
            config.max_watch_probability_decay_rate,
        ),
    )
    reason_codes.add(
        _lower_threshold_reason(
            "net_probability_buffer",
            net_probability_after_cost_decay_rate,
            config.min_pass_net_probability_after_cost_decay_rate,
            config.min_watch_net_probability_after_cost_decay_rate,
        ),
    )
    reason_codes.add(
        _upper_threshold_reason(
            "cost_decay_ratio",
            cost_decay_to_probability_ratio,
            config.max_pass_cost_decay_to_probability_ratio,
            config.max_watch_cost_decay_to_probability_ratio,
        ),
    )
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _upper_threshold_reason(
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value >= watch_threshold:
        return f"{prefix}_block"
    if value >= pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _lower_threshold_reason(
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value < watch_threshold:
        return f"{prefix}_block"
    if value < pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketExitProbabilityCostDecayObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observation records")
    normalized: list[ResearchMarketExitProbabilityCostDecayObservation] = []
    seen_refs: set[str] = set()
    for item in observations:
        if type(item) is not ResearchMarketExitProbabilityCostDecayObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketExitProbabilityCostDecayObservation",
            )
        _require_hard_flags("observation", item)
        if item.internal_signal_ref in seen_refs:
            raise ValueError("internal_signal_ref values must be unique")
        seen_refs.add(item.internal_signal_ref)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchMarketExitProbabilityCostDecayRow, ...],
) -> tuple[ResearchMarketExitProbabilityCostDecayRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketExitProbabilityCostDecayRow:
            raise ValueError(
                "rows must contain ResearchMarketExitProbabilityCostDecayRow values",
            )
        _require_hard_flags("row", row)
    expected_refs = tuple(
        f"exit_probability_cost_decay_row_{index:03d}"
        for index in range(1, len(rows) + 1)
    )
    actual_refs = tuple(row.public_row_ref for row in rows)
    if rows and actual_refs != expected_refs:
        raise ValueError("rows must use sequential public_row_ref values")
    return rows


def _normalize_reason_code_counts(
    rows: tuple[ResearchMarketExitProbabilityCostDecayReasonCodeCount, ...],
) -> tuple[ResearchMarketExitProbabilityCostDecayReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketExitProbabilityCostDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketExitProbabilityCostDecayReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.reason_code))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return rows


def _reason_code_counts(
    rows: tuple[ResearchMarketExitProbabilityCostDecayRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketExitProbabilityCostDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketExitProbabilityCostDecayReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    total = _decimal_count(len(rows))
    return tuple(
        ResearchMarketExitProbabilityCostDecayReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(_decimal_count(count) / total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _summary_reason_codes(
    rows: tuple[ResearchMarketExitProbabilityCostDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (MISSING_INPUTS_REASON,)
    if all(row.status == STATUS_PASS for row in rows):
        return ("exit_probability_cost_decay_pass",)
    return tuple(sorted({reason for row in rows for reason in row.reason_codes}))


def _summary_status(rows: tuple[ResearchMarketExitProbabilityCostDecayRow, ...]) -> str:
    if not rows or any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchMarketExitProbabilityCostDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _status_sort_value(status: str) -> int:
    if status == STATUS_BLOCK:
        return 0
    if status == STATUS_WATCH:
        return 1
    return 2


def _maximum_row_value(
    rows: tuple[ResearchMarketExitProbabilityCostDecayRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _minimum_row_value(
    rows: tuple[ResearchMarketExitProbabilityCostDecayRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _average_row_value(
    rows: tuple[ResearchMarketExitProbabilityCostDecayRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum((getattr(row, field_name) for row in rows), ZERO) / len(rows))


def _validate_row(row: ResearchMarketExitProbabilityCostDecayRow) -> None:
    if row.current_probability > row.reference_probability:
        raise ValueError("current_probability must not exceed reference_probability")
    expected_probability_decay = _quantize(
        row.reference_probability - row.current_probability,
    )
    if row.probability_decay_rate != expected_probability_decay:
        raise ValueError("probability_decay_rate must match probability fields")
    expected_total = _quantize(
        row.exit_fee_rate + row.exit_spread_rate + row.exit_slippage_rate,
    )
    if row.total_exit_cost_rate != expected_total:
        raise ValueError("total_exit_cost_rate must match exit cost fields")
    expected_net = _quantize(
        row.current_probability - row.total_exit_cost_rate - row.probability_decay_rate,
    )
    if row.net_probability_after_cost_decay_rate != expected_net:
        raise ValueError("net_probability_after_cost_decay_rate must match row fields")
    expected_ratio = _ratio(
        _quantize(row.total_exit_cost_rate + row.probability_decay_rate),
        row.current_probability,
    )
    if row.cost_decay_to_probability_ratio != expected_ratio:
        raise ValueError("cost_decay_to_probability_ratio must match row fields")
    if f"exit_probability_cost_decay_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchMarketExitProbabilityCostDecayReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_total_exit_cost_rate != _average_row_value(
        report.rows,
        "total_exit_cost_rate",
    ):
        raise ValueError("average_total_exit_cost_rate must match rows")
    if report.average_probability_decay_rate != _average_row_value(
        report.rows,
        "probability_decay_rate",
    ):
        raise ValueError("average_probability_decay_rate must match rows")
    if report.average_net_probability_after_cost_decay_rate != _average_row_value(
        report.rows,
        "net_probability_after_cost_decay_rate",
    ):
        raise ValueError("average_net_probability_after_cost_decay_rate must match rows")
    if report.average_exit_probability_cost_decay_score != _average_row_value(
        report.rows,
        "exit_probability_cost_decay_score",
    ):
        raise ValueError("average_exit_probability_cost_decay_score must match rows")
    if report.max_total_exit_cost_rate != _maximum_row_value(
        report.rows,
        "total_exit_cost_rate",
    ):
        raise ValueError("max_total_exit_cost_rate must match rows")
    if report.max_probability_decay_rate != _maximum_row_value(
        report.rows,
        "probability_decay_rate",
    ):
        raise ValueError("max_probability_decay_rate must match rows")
    if report.min_net_probability_after_cost_decay_rate != _minimum_row_value(
        report.rows,
        "net_probability_after_cost_decay_rate",
    ):
        raise ValueError("min_net_probability_after_cost_decay_rate must match rows")
    if report.max_cost_decay_to_probability_ratio != _maximum_row_value(
        report.rows,
        "cost_decay_to_probability_ratio",
    ):
        raise ValueError("max_cost_decay_to_probability_ratio must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _row_validation_digest(row: ResearchMarketExitProbabilityCostDecayRow) -> str:
    values = _row_payload(row, include_digest=False)
    return _payload_digest(values)


def _report_validation_digest(report: ResearchMarketExitProbabilityCostDecayReport) -> str:
    values = _report_payload(report, include_digest=False)
    return _payload_digest(values)


def _private_reference_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _payload_digest(payload: Mapping[str, Any]) -> str:
    _reject_unsafe_public_payload(payload)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _report_payload(
    report: ResearchMarketExitProbabilityCostDecayReport,
    *,
    include_digest: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "observation_count": _decimal_string(report.observation_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "block_count": _decimal_string(report.block_count),
        "average_total_exit_cost_rate": _optional_decimal_string(
            report.average_total_exit_cost_rate,
        ),
        "average_probability_decay_rate": _optional_decimal_string(
            report.average_probability_decay_rate,
        ),
        "average_net_probability_after_cost_decay_rate": _optional_decimal_string(
            report.average_net_probability_after_cost_decay_rate,
        ),
        "average_exit_probability_cost_decay_score": _optional_decimal_string(
            report.average_exit_probability_cost_decay_score,
        ),
        "max_total_exit_cost_rate": _decimal_string(report.max_total_exit_cost_rate),
        "max_probability_decay_rate": _decimal_string(report.max_probability_decay_rate),
        "min_net_probability_after_cost_decay_rate": _decimal_string(
            report.min_net_probability_after_cost_decay_rate,
        ),
        "max_cost_decay_to_probability_ratio": _decimal_string(
            report.max_cost_decay_to_probability_ratio,
        ),
        "status": report.status,
        "rows": [_row_payload(row) for row in report.rows],
        "reason_code_counts": [
            _reason_code_count_payload(row) for row in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_payload(
    row: ResearchMarketExitProbabilityCostDecayRow,
    *,
    include_digest: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "public_row_ref": row.public_row_ref,
        "signal_ref_digest": row.signal_ref_digest,
        "observed_at": row.observed_at.isoformat(),
        "reference_probability": _decimal_string(row.reference_probability),
        "current_probability": _decimal_string(row.current_probability),
        "probability_decay_rate": _decimal_string(row.probability_decay_rate),
        "exit_fee_rate": _decimal_string(row.exit_fee_rate),
        "exit_spread_rate": _decimal_string(row.exit_spread_rate),
        "exit_slippage_rate": _decimal_string(row.exit_slippage_rate),
        "total_exit_cost_rate": _decimal_string(row.total_exit_cost_rate),
        "net_probability_after_cost_decay_rate": _decimal_string(
            row.net_probability_after_cost_decay_rate,
        ),
        "cost_decay_to_probability_ratio": _decimal_string(
            row.cost_decay_to_probability_ratio,
        ),
        "exit_cost_score": _decimal_string(row.exit_cost_score),
        "probability_decay_score": _decimal_string(row.probability_decay_score),
        "net_buffer_score": _decimal_string(row.net_buffer_score),
        "cost_decay_ratio_score": _decimal_string(row.cost_decay_ratio_score),
        "exit_probability_cost_decay_score": _decimal_string(
            row.exit_probability_cost_decay_score,
        ),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    if include_digest:
        payload["row_validation_digest"] = row.row_validation_digest
    return payload


def _reason_code_count_payload(
    row: ResearchMarketExitProbabilityCostDecayReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": _decimal_string(row.count),
        "row_ratio": _decimal_string(row.row_ratio),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    _reject_unknown_payload_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    _reject_unsafe_public_payload(payload)
    _require_no_public_numeric_literals(payload)
    _require_public_flags_recursive(payload)
    _validate_public_rows(payload.get("rows"))
    _validate_public_reason_code_counts(payload.get("reason_code_counts"))
    _require_status("status", payload.get("status"))
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str or not HEX_DIGEST_RE.fullmatch(digest):
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    if _payload_digest(digest_payload) != digest:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_public_rows(value: object) -> None:
    if not isinstance(value, (list, tuple)):
        raise ValueError("rows must be a list")
    for row in value:
        if not isinstance(row, Mapping):
            raise ValueError("rows must contain JSON objects")
        _reject_unknown_payload_keys("row payload", row, ROW_PAYLOAD_KEYS)
        _require_status("row status", row.get("status"))
        if not isinstance(row.get("reason_codes"), (list, tuple)):
            raise ValueError("row reason_codes must be a list")
        for reason_code in row["reason_codes"]:
            _normalize_reason_code(reason_code)
        _require_hex_digest("signal_ref_digest", row.get("signal_ref_digest"))
        _validate_public_row_digest(row)


def _validate_public_row_digest(row: Mapping[str, object]) -> None:
    digest = row.get("row_validation_digest")
    _require_hex_digest("row_validation_digest", digest)
    digest_payload = dict(row)
    digest_payload.pop("row_validation_digest")
    if _payload_digest(digest_payload) != digest:
        raise ValueError("row_validation_digest must match row fields")


def _validate_public_reason_code_counts(value: object) -> None:
    if not isinstance(value, (list, tuple)):
        raise ValueError("reason_code_counts must be a list")
    for row in value:
        if not isinstance(row, Mapping):
            raise ValueError("reason_code_counts must contain JSON objects")
        _reject_unknown_payload_keys(
            "reason_code_count payload",
            row,
            REASON_COUNT_PAYLOAD_KEYS,
        )
        _normalize_reason_code(row.get("reason_code"))


def _reject_unknown_payload_keys(
    label: str,
    value: Mapping[str, object],
    allowed_keys: frozenset[str],
) -> None:
    extra_keys = set(value) - allowed_keys
    if extra_keys:
        raise ValueError(f"{label} has unknown keys")
    missing_keys = allowed_keys - set(value)
    if missing_keys:
        raise ValueError(f"{label} is missing required keys")


def _require_no_public_numeric_literals(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public numeric values must be Decimal-derived strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _require_no_public_numeric_literals(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _require_no_public_numeric_literals(item)


def _require_public_flags_recursive(value: object) -> None:
    if isinstance(value, Mapping):
        for field_name in PHASE_FLAG_FIELDS:
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True")
        for item in value.values():
            _require_public_flags_recursive(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _require_public_flags_recursive(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_unsafe_public_text(str(key))
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, str):
        _reject_unsafe_public_text(value)


def _reject_unsafe_public_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload surface")


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    return value


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not PRIVATE_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a non-empty private reference")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        normalized = +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    return _quantize(normalized)


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


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1.000000")
    return normalized


def _require_positive_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1.000000")
    return normalized


def _require_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_decimal(field_name, value)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in MARKET_EXIT_PROBABILITY_COST_DECAY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    return tuple(sorted({_normalize_reason_code(reason_code) for reason_code in reason_codes}))


def _normalize_reason_code(value: object) -> str:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError("reason_codes must contain reason code strings")
    _reject_unsafe_public_text(value)
    return value


def _require_hex_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not HEX_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _inverse_ratio_score(value: Decimal, zero_at: Decimal) -> Decimal:
    if zero_at <= ZERO:
        raise ValueError("zero_at must be positive")
    return _quantize(max(ZERO, ONE - (value / zero_at)))


def _range_score(value: Decimal, zero_at: Decimal, full_at: Decimal) -> Decimal:
    if full_at <= zero_at:
        raise ValueError("full_at must exceed zero_at")
    return _quantize(min(ONE, max(ZERO, (value - zero_at) / (full_at - zero_at))))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_string(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _optional_decimal_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_string(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)
