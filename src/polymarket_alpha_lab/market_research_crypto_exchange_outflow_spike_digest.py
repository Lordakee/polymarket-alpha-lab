"""Pure Phase 1 crypto exchange outflow spike digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_CRYPTO_EXCHANGE_OUTFLOW_SPIKE_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-exchange-outflow-spike-digest-v0"
)

INPUT_REASON_CODES = (
    "crypto_exchange_outflow_spike_observed_stable",
    "crypto_exchange_outflow_spike_pressure",
    "crypto_exchange_outflow_balance_drawdown_pressure",
)
ROW_REASON_CODES = (
    "crypto_exchange_outflow_spike_blocked",
    "crypto_exchange_balance_drawdown_blocked",
    "crypto_exchange_outflow_spike_watch",
    "crypto_exchange_balance_drawdown_watch",
    "crypto_exchange_outflow_spike_observed_stable",
)
REPORT_REASON_CODES = (
    "crypto_exchange_outflow_spike_blocked_present",
    "crypto_exchange_outflow_spike_watch_present",
    "crypto_exchange_outflow_spike_digest_clear",
    "crypto_exchange_outflow_spike_digest_empty",
)
SCREENING_STATUSES = ("pass", "watch", "blocked")

VALUE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_SPIKE_MULTIPLE = Decimal("2.000000")
BLOCKED_SPIKE_MULTIPLE = Decimal("4.000000")
WATCH_BALANCE_DRAWDOWN_RATIO = Decimal("0.050000")
BLOCKED_BALANCE_DRAWDOWN_RATIO = Decimal("0.100000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_CRYPTO_EXCHANGE_OUTFLOW_SPIKE_DIGEST_CONFIG_VERSION",
    "CryptoExchangeOutflowSpikeDigestConfig",
    "CryptoExchangeOutflowSpikeObservation",
    "CryptoExchangeOutflowSpikeDigestRow",
    "CryptoExchangeOutflowSpikeReasonCodeCount",
    "CryptoExchangeOutflowSpikeDigestReport",
    "build_market_research_crypto_exchange_outflow_spike_digest",
    "market_research_crypto_exchange_outflow_spike_digest_payload",
)


@dataclass(frozen=True)
class CryptoExchangeOutflowSpikeDigestConfig:
    config_version: str = DEFAULT_CRYPTO_EXCHANGE_OUTFLOW_SPIKE_DIGEST_CONFIG_VERSION
    watch_spike_multiple: Decimal = WATCH_SPIKE_MULTIPLE
    blocked_spike_multiple: Decimal = BLOCKED_SPIKE_MULTIPLE
    watch_balance_drawdown_ratio: Decimal = WATCH_BALANCE_DRAWDOWN_RATIO
    blocked_balance_drawdown_ratio: Decimal = BLOCKED_BALANCE_DRAWDOWN_RATIO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoExchangeOutflowSpikeDigestConfig:
            raise TypeError("CryptoExchangeOutflowSpikeDigestConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not CryptoExchangeOutflowSpikeDigestConfig:
            raise ValueError("config must be exactly CryptoExchangeOutflowSpikeDigestConfig")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CRYPTO_EXCHANGE_OUTFLOW_SPIKE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_spike_multiple", "blocked_spike_multiple"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_balance_drawdown_ratio",
            "blocked_balance_drawdown_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_ratio(field_name, getattr(self, field_name)),
            )
        if self.blocked_spike_multiple < self.watch_spike_multiple:
            raise ValueError("blocked_spike_multiple must be at least watch threshold")
        if self.blocked_balance_drawdown_ratio < self.watch_balance_drawdown_ratio:
            raise ValueError(
                "blocked_balance_drawdown_ratio must be at least watch threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class CryptoExchangeOutflowSpikeObservation:
    source_id: str
    exchange_id: str
    asset_symbol: str
    market_slug: str
    exchange_balance_usd: Decimal
    net_outflow_usd: Decimal
    baseline_outflow_usd: Decimal
    source_row_count: Decimal
    observation_timestamp: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoExchangeOutflowSpikeObservation:
            raise TypeError("CryptoExchangeOutflowSpikeObservation does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not CryptoExchangeOutflowSpikeObservation:
            raise ValueError("observation must be exactly CryptoExchangeOutflowSpikeObservation")
        for field_name in ("source_id", "exchange_id", "asset_symbol", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("exchange_balance_usd", "net_outflow_usd"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "baseline_outflow_usd",
            _require_positive_decimal("baseline_outflow_usd", self.baseline_outflow_usd),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _require_whole_nonnegative_decimal("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "observation_timestamp",
            _as_utc("observation_timestamp", self.observation_timestamp),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, INPUT_REASON_CODES),
        )
        _validate_observation(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class CryptoExchangeOutflowSpikeDigestRow:
    source_id: str
    exchange_id: str
    asset_symbol: str
    market_slug: str
    exchange_balance_usd: Decimal
    net_outflow_usd: Decimal
    baseline_outflow_usd: Decimal
    spike_multiple: Decimal
    balance_drawdown_ratio: Decimal
    source_row_count: Decimal
    observation_timestamp: datetime
    screening_score: Decimal
    screening_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoExchangeOutflowSpikeDigestRow:
            raise TypeError("CryptoExchangeOutflowSpikeDigestRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not CryptoExchangeOutflowSpikeDigestRow:
            raise ValueError("row must be exactly CryptoExchangeOutflowSpikeDigestRow")
        for field_name in ("source_id", "exchange_id", "asset_symbol", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "exchange_balance_usd",
            "net_outflow_usd",
            "spike_multiple",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "baseline_outflow_usd",
            _require_positive_decimal("baseline_outflow_usd", self.baseline_outflow_usd),
        )
        object.__setattr__(
            self,
            "balance_drawdown_ratio",
            _require_nonnegative_decimal("balance_drawdown_ratio", self.balance_drawdown_ratio),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _require_whole_nonnegative_decimal("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "observation_timestamp",
            _as_utc("observation_timestamp", self.observation_timestamp),
        )
        object.__setattr__(
            self,
            "screening_score",
            _require_ratio("screening_score", self.screening_score),
        )
        _require_member("screening_status", self.screening_status, SCREENING_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class CryptoExchangeOutflowSpikeReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoExchangeOutflowSpikeReasonCodeCount:
            raise TypeError(
                "CryptoExchangeOutflowSpikeReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CryptoExchangeOutflowSpikeReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly CryptoExchangeOutflowSpikeReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES + REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class CryptoExchangeOutflowSpikeDigestReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    observation_count: Decimal
    blocked_exchange_count: Decimal
    watch_exchange_count: Decimal
    pass_exchange_count: Decimal
    total_net_outflow_usd: Decimal
    max_spike_multiple: Decimal
    max_balance_drawdown_ratio: Decimal
    max_screening_score: Decimal
    average_screening_score: Decimal
    blocked_observation_ratio: Decimal
    digest_status: str
    recommended_next_step: str
    exchange_rows: tuple[CryptoExchangeOutflowSpikeDigestRow, ...]
    reason_code_counts: tuple[CryptoExchangeOutflowSpikeReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoExchangeOutflowSpikeDigestReport:
            raise TypeError("CryptoExchangeOutflowSpikeDigestReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not CryptoExchangeOutflowSpikeDigestReport:
            raise ValueError("report must be exactly CryptoExchangeOutflowSpikeDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CRYPTO_EXCHANGE_OUTFLOW_SPIKE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_row_count",
            "observation_count",
            "blocked_exchange_count",
            "watch_exchange_count",
            "pass_exchange_count",
            "total_net_outflow_usd",
            "max_spike_multiple",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_balance_drawdown_ratio",
            "max_screening_score",
            "average_screening_score",
            "blocked_observation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, SCREENING_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "exchange_rows", _normalize_rows(self.exchange_rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_crypto_exchange_outflow_spike_digest(
    inputs: Iterable[CryptoExchangeOutflowSpikeObservation],
    *,
    config: CryptoExchangeOutflowSpikeDigestConfig,
    generated_at: datetime,
) -> CryptoExchangeOutflowSpikeDigestReport:
    if type(config) is not CryptoExchangeOutflowSpikeDigestConfig:
        raise ValueError("config must be exactly CryptoExchangeOutflowSpikeDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    observations = _normalize_inputs(inputs)
    rows = tuple(_row_for_observation(item, config=config) for item in observations)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    observation_count = _count_decimal(len(sorted_rows))
    blocked_count = _count_decimal(
        sum(1 for row in sorted_rows if row.screening_status == "blocked"),
    )
    row_reason_codes = tuple(
        reason_code for row in sorted_rows for reason_code in row.reason_codes
    )
    digest_status = _digest_status(sorted_rows)

    return CryptoExchangeOutflowSpikeDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_sum_decimal(row.source_row_count for row in sorted_rows),
        observation_count=observation_count,
        blocked_exchange_count=blocked_count,
        watch_exchange_count=_count_decimal(
            sum(1 for row in sorted_rows if row.screening_status == "watch"),
        ),
        pass_exchange_count=_count_decimal(
            sum(1 for row in sorted_rows if row.screening_status == "pass"),
        ),
        total_net_outflow_usd=_sum_decimal(row.net_outflow_usd for row in sorted_rows),
        max_spike_multiple=max((row.spike_multiple for row in sorted_rows), default=ZERO),
        max_balance_drawdown_ratio=max(
            (row.balance_drawdown_ratio for row in sorted_rows),
            default=ZERO,
        ),
        max_screening_score=max((row.screening_score for row in sorted_rows), default=ZERO),
        average_screening_score=_ratio(
            _sum_decimal(row.screening_score for row in sorted_rows),
            observation_count,
        ),
        blocked_observation_ratio=_ratio(blocked_count, observation_count),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        exchange_rows=sorted_rows,
        reason_code_counts=_reason_code_counts(row_reason_codes, observation_count),
        reason_codes=_report_reason_codes(sorted_rows),
    )


def market_research_crypto_exchange_outflow_spike_digest_payload(
    report: CryptoExchangeOutflowSpikeDigestReport,
) -> dict[str, Any]:
    if type(report) is not CryptoExchangeOutflowSpikeDigestReport:
        raise ValueError("report must be exactly CryptoExchangeOutflowSpikeDigestReport")
    return _json_ready(asdict(report))


def _row_for_observation(
    observation: CryptoExchangeOutflowSpikeObservation,
    *,
    config: CryptoExchangeOutflowSpikeDigestConfig,
) -> CryptoExchangeOutflowSpikeDigestRow:
    spike_multiple = _spike_multiple(observation)
    balance_drawdown_ratio = _balance_drawdown_ratio(observation)
    status = _screening_status(
        spike_multiple=spike_multiple,
        balance_drawdown_ratio=balance_drawdown_ratio,
        config=config,
    )
    return CryptoExchangeOutflowSpikeDigestRow(
        source_id=observation.source_id,
        exchange_id=observation.exchange_id,
        asset_symbol=observation.asset_symbol,
        market_slug=observation.market_slug,
        exchange_balance_usd=observation.exchange_balance_usd,
        net_outflow_usd=observation.net_outflow_usd,
        baseline_outflow_usd=observation.baseline_outflow_usd,
        spike_multiple=spike_multiple,
        balance_drawdown_ratio=balance_drawdown_ratio,
        source_row_count=observation.source_row_count,
        observation_timestamp=observation.observation_timestamp,
        screening_score=_screening_score(
            spike_multiple=spike_multiple,
            balance_drawdown_ratio=balance_drawdown_ratio,
            config=config,
        ),
        screening_status=status,
        reason_codes=_row_reason_codes(
            spike_multiple=spike_multiple,
            balance_drawdown_ratio=balance_drawdown_ratio,
            config=config,
            status=status,
        ),
    )


def _spike_multiple(observation: CryptoExchangeOutflowSpikeObservation) -> Decimal:
    return _ratio(observation.net_outflow_usd, observation.baseline_outflow_usd)


def _balance_drawdown_ratio(observation: CryptoExchangeOutflowSpikeObservation) -> Decimal:
    return _ratio(observation.net_outflow_usd, observation.exchange_balance_usd)


def _screening_score(
    *,
    spike_multiple: Decimal,
    balance_drawdown_ratio: Decimal,
    config: CryptoExchangeOutflowSpikeDigestConfig,
) -> Decimal:
    spike_score = _ratio(spike_multiple, config.blocked_spike_multiple)
    drawdown_score = _ratio(balance_drawdown_ratio, config.blocked_balance_drawdown_ratio)
    score = max(spike_score, drawdown_score)
    if score > ONE:
        return ONE
    return score


def _screening_status(
    *,
    spike_multiple: Decimal,
    balance_drawdown_ratio: Decimal,
    config: CryptoExchangeOutflowSpikeDigestConfig,
) -> str:
    if (
        spike_multiple >= config.blocked_spike_multiple
        or balance_drawdown_ratio >= config.blocked_balance_drawdown_ratio
    ):
        return "blocked"
    if (
        spike_multiple >= config.watch_spike_multiple
        or balance_drawdown_ratio >= config.watch_balance_drawdown_ratio
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    spike_multiple: Decimal,
    balance_drawdown_ratio: Decimal,
    config: CryptoExchangeOutflowSpikeDigestConfig,
    status: str,
) -> tuple[str, ...]:
    if status == "pass":
        return ("crypto_exchange_outflow_spike_observed_stable",)

    reason_codes: list[str] = []
    if spike_multiple >= config.blocked_spike_multiple:
        reason_codes.append("crypto_exchange_outflow_spike_blocked")
    elif spike_multiple >= config.watch_spike_multiple:
        reason_codes.append("crypto_exchange_outflow_spike_watch")
    if balance_drawdown_ratio >= config.blocked_balance_drawdown_ratio:
        reason_codes.append("crypto_exchange_balance_drawdown_blocked")
    elif balance_drawdown_ratio >= config.watch_balance_drawdown_ratio:
        reason_codes.append("crypto_exchange_balance_drawdown_watch")
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in reason_codes)


def _report_reason_codes(
    rows: tuple[CryptoExchangeOutflowSpikeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("crypto_exchange_outflow_spike_digest_empty",)
    has_blocked = any(row.screening_status == "blocked" for row in rows)
    has_watch = any(row.screening_status == "watch" for row in rows)
    if has_blocked and has_watch:
        return (
            "crypto_exchange_outflow_spike_blocked_present",
            "crypto_exchange_outflow_spike_watch_present",
        )
    if has_blocked:
        return ("crypto_exchange_outflow_spike_blocked_present",)
    if has_watch:
        return ("crypto_exchange_outflow_spike_watch_present",)
    return ("crypto_exchange_outflow_spike_digest_clear",)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    observation_count: Decimal,
) -> tuple[CryptoExchangeOutflowSpikeReasonCodeCount, ...]:
    if not reason_codes:
        return (
            CryptoExchangeOutflowSpikeReasonCodeCount(
                reason_code="crypto_exchange_outflow_spike_digest_empty",
                count=ONE,
                observation_ratio=ZERO,
            ),
        )
    return tuple(
        CryptoExchangeOutflowSpikeReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(sum(1 for item in reason_codes if item == reason_code)),
            observation_ratio=_ratio(
                _count_decimal(sum(1 for item in reason_codes if item == reason_code)),
                observation_count,
            ),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in reason_codes
    )


def _digest_status(rows: tuple[CryptoExchangeOutflowSpikeDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.screening_status == "blocked" for row in rows):
        return "blocked"
    if any(row.screening_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_market_research_crypto_exchange_outflow_spike_digest"
    if status == "watch":
        return "monitor_report_only_market_research_crypto_exchange_outflow_spike_digest"
    return "block_report_only_market_research_crypto_exchange_outflow_spike_digest"


def _validate_observation(observation: CryptoExchangeOutflowSpikeObservation) -> None:
    if observation.reason_codes != _input_reason_codes(observation):
        raise ValueError("reason_codes must match exchange outflow metrics")


def _input_reason_codes(
    observation: CryptoExchangeOutflowSpikeObservation,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if _spike_multiple(observation) >= WATCH_SPIKE_MULTIPLE:
        reason_codes.append("crypto_exchange_outflow_spike_pressure")
    if _balance_drawdown_ratio(observation) >= WATCH_BALANCE_DRAWDOWN_RATIO:
        reason_codes.append("crypto_exchange_outflow_balance_drawdown_pressure")
    if not reason_codes:
        reason_codes.append("crypto_exchange_outflow_spike_observed_stable")
    return tuple(reason_code for reason_code in INPUT_REASON_CODES if reason_code in reason_codes)


def _validate_row(row: CryptoExchangeOutflowSpikeDigestRow) -> None:
    if row.spike_multiple != _ratio(row.net_outflow_usd, row.baseline_outflow_usd):
        raise ValueError("spike_multiple must match outflow metrics")
    if row.balance_drawdown_ratio != _ratio(row.net_outflow_usd, row.exchange_balance_usd):
        raise ValueError("balance_drawdown_ratio must match outflow metrics")
    if row.screening_status == "pass":
        if row.reason_codes != ("crypto_exchange_outflow_spike_observed_stable",):
            raise ValueError("reason_codes must match screening_status")
        return
    if row.screening_status == "watch" and not any(
        reason_code.endswith("_watch") for reason_code in row.reason_codes
    ):
        raise ValueError("reason_codes must match screening_status")
    if row.screening_status == "blocked" and not any(
        reason_code.endswith("_blocked") for reason_code in row.reason_codes
    ):
        raise ValueError("reason_codes must match screening_status")


def _validate_report(report: CryptoExchangeOutflowSpikeDigestReport) -> None:
    if report.source_row_count != _sum_decimal(row.source_row_count for row in report.exchange_rows):
        raise ValueError("source_row_count must match rows")
    if report.observation_count != _count_decimal(len(report.exchange_rows)):
        raise ValueError("observation_count must match rows")
    if report.blocked_exchange_count != _count_decimal(
        sum(1 for row in report.exchange_rows if row.screening_status == "blocked"),
    ):
        raise ValueError("blocked_exchange_count must match rows")
    if report.watch_exchange_count != _count_decimal(
        sum(1 for row in report.exchange_rows if row.screening_status == "watch"),
    ):
        raise ValueError("watch_exchange_count must match rows")
    if report.pass_exchange_count != _count_decimal(
        sum(1 for row in report.exchange_rows if row.screening_status == "pass"),
    ):
        raise ValueError("pass_exchange_count must match rows")
    if report.total_net_outflow_usd != _sum_decimal(
        row.net_outflow_usd for row in report.exchange_rows
    ):
        raise ValueError("total_net_outflow_usd must match rows")
    if report.max_spike_multiple != max(
        (row.spike_multiple for row in report.exchange_rows),
        default=ZERO,
    ):
        raise ValueError("max_spike_multiple must match rows")
    if report.max_balance_drawdown_ratio != max(
        (row.balance_drawdown_ratio for row in report.exchange_rows),
        default=ZERO,
    ):
        raise ValueError("max_balance_drawdown_ratio must match rows")
    if report.max_screening_score != max(
        (row.screening_score for row in report.exchange_rows),
        default=ZERO,
    ):
        raise ValueError("max_screening_score must match rows")
    if report.average_screening_score != _ratio(
        _sum_decimal(row.screening_score for row in report.exchange_rows),
        report.observation_count,
    ):
        raise ValueError("average_screening_score must match rows")
    if report.blocked_observation_ratio != _ratio(
        report.blocked_exchange_count,
        report.observation_count,
    ):
        raise ValueError("blocked_observation_ratio must match rows")
    if report.digest_status != _digest_status(report.exchange_rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.exchange_rows):
        raise ValueError("reason_codes must match rows")
    row_reason_codes = tuple(
        reason_code for row in report.exchange_rows for reason_code in row.reason_codes
    )
    if report.reason_code_counts != _reason_code_counts(
        row_reason_codes,
        report.observation_count,
    ):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    inputs: Iterable[CryptoExchangeOutflowSpikeObservation],
) -> tuple[CryptoExchangeOutflowSpikeObservation, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must contain crypto exchange outflow spike observations")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must contain crypto exchange outflow spike observations") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not CryptoExchangeOutflowSpikeObservation:
            raise ValueError("inputs must contain CryptoExchangeOutflowSpikeObservation")
        if item.source_id in seen:
            raise ValueError("inputs must not contain duplicate source_id values")
        seen.add(item.source_id)
    return normalized


def _normalize_rows(
    value: object,
) -> tuple[CryptoExchangeOutflowSpikeDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("exchange_rows must contain crypto exchange outflow spike digest rows")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "exchange_rows must contain crypto exchange outflow spike digest rows",
        ) from exc
    for row in rows:
        if type(row) is not CryptoExchangeOutflowSpikeDigestRow:
            raise ValueError("exchange_rows must contain CryptoExchangeOutflowSpikeDigestRow")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("exchange_rows must be sorted deterministically")
    if len({row.source_id for row in rows}) != len(rows):
        raise ValueError("exchange_rows must not contain duplicate source_id values")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[CryptoExchangeOutflowSpikeReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        counts = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    for item in counts:
        if type(item) is not CryptoExchangeOutflowSpikeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain CryptoExchangeOutflowSpikeReasonCodeCount",
            )
    allowed = ROW_REASON_CODES + REPORT_REASON_CODES
    if counts != tuple(sorted(counts, key=lambda item: allowed.index(item.reason_code))):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason code strings") from exc
    for reason_code in normalized:
        _require_member("reason_code", reason_code, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if normalized != tuple(
        sorted(normalized, key=lambda reason_code: allowed.index(reason_code))
    ):
        raise ValueError(f"{field_name} must be sorted deterministically")
    return normalized


def _row_sort_key(
    row: CryptoExchangeOutflowSpikeDigestRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        -STATUS_WEIGHT[row.screening_status],
        -row.screening_score,
        row.exchange_id,
        row.asset_symbol,
        row.source_id,
    )


def _json_ready(value: object) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        if not value.is_finite():
            raise ValueError("values must be finite")
        total += value
    return _quantize(total)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_ratio(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
