"""Read-only market momentum reversal watchlist report for Phase 1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_MOMENTUM_REVERSAL_WATCHLIST_CONFIG_VERSION = (
    "market-momentum-reversal-watchlist-report-v0"
)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
PROBABILITY_QUANTUM = Decimal("0.000001")
AGE_SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ZERO_PROBABILITY = Decimal("0.000000")
ZERO_AGE_SECONDS = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

REVERSAL_DIRECTIONS = ("up_to_down", "down_to_up")
WATCHLIST_STATUSES = ("empty", "pass", "watch", "blocked")
ROW_REASON_CODES = (
    "market_momentum_reversal_clear",
    "sharp_probability_reversal",
    "stale_market_context",
    "thin_market_depth",
    "missing_research_acknowledgement",
)
REPORT_REASON_CODES = (
    "market_momentum_reversal_watchlist_empty",
    "market_momentum_reversal_watchlist_clear",
    "sharp_probability_reversal_present",
    "stale_market_context_present",
    "thin_market_depth_present",
    "missing_research_acknowledgement_present",
)
STATUS_WEIGHT = {
    "blocked": Decimal("2"),
    "watch": Decimal("1"),
    "pass": Decimal("0"),
}
UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
)
REPORT_DECIMAL_PAYLOAD_FIELDS = (
    "source_market_count",
    "watchlist_market_count",
    "sharp_reversal_count",
    "stale_context_count",
    "thin_depth_count",
    "missing_research_acknowledgement_count",
    "watchlist_ratio",
    "max_reversal_delta",
    "max_context_age_seconds",
    "min_available_depth",
)
ROW_DECIMAL_PAYLOAD_FIELDS = (
    "prior_probability",
    "extreme_probability",
    "latest_probability",
    "probability_delta",
    "reversal_delta",
    "probability_observation_age_seconds",
    "context_age_seconds",
    "available_depth",
    "flag_count",
)
ROW_BOOL_PAYLOAD_FIELDS = (
    "sharp_reversal",
    "stale_context",
    "thin_depth",
    "missing_research_acknowledgement",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    *REPORT_DECIMAL_PAYLOAD_FIELDS,
    "status",
    "reason_codes",
    "watchlist_rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "market_key",
    "status",
    "reversal_direction",
    *ROW_DECIMAL_PAYLOAD_FIELDS,
    *ROW_BOOL_PAYLOAD_FIELDS,
    "reason_codes",
)


@dataclass(frozen=True)
class MarketMomentumReversalWatchlistConfig:
    config_version: str = DEFAULT_MARKET_MOMENTUM_REVERSAL_WATCHLIST_CONFIG_VERSION
    sharp_reversal_delta_threshold: Decimal = Decimal("0.050000")
    stale_context_age_seconds_threshold: Decimal = Decimal("7200")
    thin_depth_available_threshold: Decimal = Decimal("500")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketMomentumReversalWatchlistConfig:
            raise ValueError("config must be exact")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_MARKET_MOMENTUM_REVERSAL_WATCHLIST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "sharp_reversal_delta_threshold",
            _normalize_probability_delta(
                "sharp_reversal_delta_threshold",
                self.sharp_reversal_delta_threshold,
            ),
        )
        object.__setattr__(
            self,
            "stale_context_age_seconds_threshold",
            _normalize_nonnegative_age_seconds(
                "stale_context_age_seconds_threshold",
                self.stale_context_age_seconds_threshold,
            ),
        )
        object.__setattr__(
            self,
            "thin_depth_available_threshold",
            _normalize_nonnegative_count(
                "thin_depth_available_threshold",
                self.thin_depth_available_threshold,
            ),
        )
        require_paper_only_flags("market momentum reversal watchlist config", self)


@dataclass(frozen=True)
class MarketMomentumReversalWatchlistInput:
    market_key: str
    prior_probability: Decimal
    extreme_probability: Decimal
    latest_probability: Decimal
    reversal_direction: str
    probability_observed_at: datetime
    context_updated_at: datetime
    available_depth: Decimal
    research_acknowledged: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketMomentumReversalWatchlistInput:
            raise ValueError("input must be exact")
        _require_canonical_string("market_key", self.market_key)
        for field_name in (
            "prior_probability",
            "extreme_probability",
            "latest_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("reversal_direction", self.reversal_direction, REVERSAL_DIRECTIONS)
        object.__setattr__(
            self,
            "probability_observed_at",
            _as_utc("probability_observed_at", self.probability_observed_at),
        )
        object.__setattr__(
            self,
            "context_updated_at",
            _as_utc("context_updated_at", self.context_updated_at),
        )
        object.__setattr__(
            self,
            "available_depth",
            _normalize_nonnegative_count("available_depth", self.available_depth),
        )
        if type(self.research_acknowledged) is not bool:
            raise ValueError("research_acknowledged must be a bool")
        require_paper_only_flags("market momentum reversal watchlist input", self)
        _validate_input(self)


@dataclass(frozen=True)
class MarketMomentumReversalWatchlistRow:
    market_key: str
    status: str
    reversal_direction: str
    prior_probability: Decimal
    extreme_probability: Decimal
    latest_probability: Decimal
    probability_delta: Decimal
    reversal_delta: Decimal
    probability_observation_age_seconds: Decimal
    context_age_seconds: Decimal
    available_depth: Decimal
    flag_count: Decimal
    sharp_reversal: bool
    stale_context: bool
    thin_depth: bool
    missing_research_acknowledgement: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketMomentumReversalWatchlistRow:
            raise ValueError("row must be exact")
        _require_canonical_string("market_key", self.market_key)
        _require_member("status", self.status, WATCHLIST_STATUSES)
        if self.status == "empty":
            raise ValueError("row status must not be empty")
        _require_member("reversal_direction", self.reversal_direction, REVERSAL_DIRECTIONS)
        for field_name in (
            "prior_probability",
            "extreme_probability",
            "latest_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("probability_delta",):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_probability_delta(field_name, getattr(self, field_name)),
            )
        for field_name in ("reversal_delta",):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_delta(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "probability_observation_age_seconds",
            "context_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_age_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in ("available_depth", "flag_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "sharp_reversal",
            "stale_context",
            "thin_depth",
            "missing_research_acknowledgement",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        require_paper_only_flags("market momentum reversal watchlist row", self)
        _validate_row(self)


@dataclass(frozen=True)
class MarketMomentumReversalWatchlistReport:
    generated_at: datetime
    config_version: str
    source_market_count: Decimal
    watchlist_market_count: Decimal
    sharp_reversal_count: Decimal
    stale_context_count: Decimal
    thin_depth_count: Decimal
    missing_research_acknowledgement_count: Decimal
    watchlist_ratio: Decimal
    max_reversal_delta: Decimal
    max_context_age_seconds: Decimal
    min_available_depth: Decimal
    status: str
    reason_codes: tuple[str, ...]
    watchlist_rows: tuple[MarketMomentumReversalWatchlistRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketMomentumReversalWatchlistReport:
            raise ValueError("report must be exact")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_market_count",
            "watchlist_market_count",
            "sharp_reversal_count",
            "stale_context_count",
            "thin_depth_count",
            "missing_research_acknowledgement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "watchlist_ratio",
            _normalize_ratio("watchlist_ratio", self.watchlist_ratio),
        )
        object.__setattr__(
            self,
            "max_reversal_delta",
            _normalize_probability_delta("max_reversal_delta", self.max_reversal_delta),
        )
        object.__setattr__(
            self,
            "max_context_age_seconds",
            _normalize_nonnegative_age_seconds(
                "max_context_age_seconds",
                self.max_context_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_available_depth",
            _normalize_nonnegative_count("min_available_depth", self.min_available_depth),
        )
        _require_member("status", self.status, WATCHLIST_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "watchlist_rows",
            _normalize_rows(self.watchlist_rows),
        )
        require_paper_only_flags("market momentum reversal watchlist report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("market momentum reversal watchlist report", self)
        _validate_derived_validation_digest(self)


def build_market_momentum_reversal_watchlist_report(
    inputs: list[MarketMomentumReversalWatchlistInput]
    | tuple[MarketMomentumReversalWatchlistInput, ...],
    *,
    config: MarketMomentumReversalWatchlistConfig,
    generated_at: datetime,
) -> MarketMomentumReversalWatchlistReport:
    if type(config) is not MarketMomentumReversalWatchlistConfig:
        raise ValueError("config must be a MarketMomentumReversalWatchlistConfig")
    require_paper_only_flags("market momentum reversal watchlist config", config)
    generated_at = _as_utc("generated_at", generated_at)
    rows = _normalize_inputs(inputs, generated_at)
    watchlist_rows = tuple(
        sorted(
            (
                row
                for row in (
                    _watchlist_row(source, config=config, generated_at=generated_at)
                    for source in rows
                )
                if row.flag_count > ZERO_COUNT
            ),
            key=_row_sort_key,
        ),
    )
    return MarketMomentumReversalWatchlistReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_market_count=_count(len(rows)),
        watchlist_market_count=_count(len(watchlist_rows)),
        sharp_reversal_count=_flag_total(watchlist_rows, "sharp_reversal"),
        stale_context_count=_flag_total(watchlist_rows, "stale_context"),
        thin_depth_count=_flag_total(watchlist_rows, "thin_depth"),
        missing_research_acknowledgement_count=_flag_total(
            watchlist_rows,
            "missing_research_acknowledgement",
        ),
        watchlist_ratio=_ratio(_count(len(watchlist_rows)), _count(len(rows))),
        max_reversal_delta=_max_probability_delta(row.reversal_delta for row in watchlist_rows),
        max_context_age_seconds=_max_age_seconds(
            row.context_age_seconds for row in watchlist_rows
        ),
        min_available_depth=_min_count(row.available_depth for row in watchlist_rows),
        status=_report_status(watchlist_rows, len(rows)),
        reason_codes=_report_reason_codes(watchlist_rows, len(rows)),
        watchlist_rows=watchlist_rows,
        derived_validation_digest=_derived_validation_digest(
            generated_at=generated_at,
            config_version=config.config_version,
            source_market_count=_count(len(rows)),
            watchlist_market_count=_count(len(watchlist_rows)),
            sharp_reversal_count=_flag_total(watchlist_rows, "sharp_reversal"),
            stale_context_count=_flag_total(watchlist_rows, "stale_context"),
            thin_depth_count=_flag_total(watchlist_rows, "thin_depth"),
            missing_research_acknowledgement_count=_flag_total(
                watchlist_rows,
                "missing_research_acknowledgement",
            ),
            watchlist_ratio=_ratio(_count(len(watchlist_rows)), _count(len(rows))),
            max_reversal_delta=_max_probability_delta(
                row.reversal_delta for row in watchlist_rows
            ),
            max_context_age_seconds=_max_age_seconds(
                row.context_age_seconds for row in watchlist_rows
            ),
            min_available_depth=_min_count(row.available_depth for row in watchlist_rows),
            status=_report_status(watchlist_rows, len(rows)),
            reason_codes=_report_reason_codes(watchlist_rows, len(rows)),
            watchlist_rows=watchlist_rows,
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
    )


def market_momentum_reversal_watchlist_payload(
    report: MarketMomentumReversalWatchlistReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketMomentumReversalWatchlistReport:
        require_paper_only_flags("market momentum reversal watchlist report", report)
        reject_unsafe_surface_fields("market momentum reversal watchlist report", report)
        _reject_unsafe_public_payload("market momentum reversal watchlist report", report)
        payload = json_ready_no_floats(report)
    elif type(report) is dict:
        reject_unsafe_surface_fields("market momentum reversal watchlist payload", report)
        _reject_unsafe_public_payload("market momentum reversal watchlist payload", report)
        payload = json_ready_no_floats(report)
    else:
        raise ValueError("report must be a MarketMomentumReversalWatchlistReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    require_paper_only_flags("market momentum reversal watchlist payload", _DictFlags(payload))
    return payload


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


def _normalize_inputs(
    values: list[MarketMomentumReversalWatchlistInput]
    | tuple[MarketMomentumReversalWatchlistInput, ...],
    generated_at: datetime,
) -> tuple[MarketMomentumReversalWatchlistInput, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(values)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketMomentumReversalWatchlistInput:
            raise ValueError("inputs must contain MarketMomentumReversalWatchlistInput values")
        require_paper_only_flags("market momentum reversal watchlist input", row)
        if row.market_key in seen:
            raise ValueError("duplicate market_key values are not allowed")
        if row.probability_observed_at > generated_at:
            raise ValueError("probability_observed_at must not be after generated_at")
        if row.context_updated_at > generated_at:
            raise ValueError("context_updated_at must not be after generated_at")
        seen.add(row.market_key)
    return rows


def _watchlist_row(
    source: MarketMomentumReversalWatchlistInput,
    *,
    config: MarketMomentumReversalWatchlistConfig,
    generated_at: datetime,
) -> MarketMomentumReversalWatchlistRow:
    probability_delta = _normalize_signed_probability_delta(
        "probability_delta",
        source.latest_probability - source.prior_probability,
    )
    reversal_delta = _normalize_probability_delta(
        "reversal_delta",
        abs(source.latest_probability - source.extreme_probability),
    )
    probability_age = _age_seconds(generated_at, source.probability_observed_at)
    context_age = _age_seconds(generated_at, source.context_updated_at)
    sharp_reversal = reversal_delta >= config.sharp_reversal_delta_threshold
    stale_context = context_age >= config.stale_context_age_seconds_threshold
    thin_depth = source.available_depth < config.thin_depth_available_threshold
    missing_ack = not source.research_acknowledged
    flags = (sharp_reversal, stale_context, thin_depth, missing_ack)
    flag_count = _count(sum(1 for flag in flags if flag))
    return MarketMomentumReversalWatchlistRow(
        market_key=source.market_key,
        status=_row_status(
            sharp_reversal=sharp_reversal,
            stale_context=stale_context,
            thin_depth=thin_depth,
            missing_research_acknowledgement=missing_ack,
        ),
        reversal_direction=source.reversal_direction,
        prior_probability=source.prior_probability,
        extreme_probability=source.extreme_probability,
        latest_probability=source.latest_probability,
        probability_delta=probability_delta,
        reversal_delta=reversal_delta,
        probability_observation_age_seconds=probability_age,
        context_age_seconds=context_age,
        available_depth=source.available_depth,
        flag_count=flag_count,
        sharp_reversal=sharp_reversal,
        stale_context=stale_context,
        thin_depth=thin_depth,
        missing_research_acknowledgement=missing_ack,
        reason_codes=_row_reason_codes(
            sharp_reversal=sharp_reversal,
            stale_context=stale_context,
            thin_depth=thin_depth,
            missing_research_acknowledgement=missing_ack,
        ),
    )


def _row_status(
    *,
    sharp_reversal: bool,
    stale_context: bool,
    thin_depth: bool,
    missing_research_acknowledgement: bool,
) -> str:
    flag_count = sum(
        1
        for flag in (
            sharp_reversal,
            stale_context,
            thin_depth,
            missing_research_acknowledgement,
        )
        if flag
    )
    if flag_count == 0:
        return "pass"
    if flag_count >= 3 or (sharp_reversal and missing_research_acknowledgement):
        return "blocked"
    return "watch"


def _row_reason_codes(
    *,
    sharp_reversal: bool,
    stale_context: bool,
    thin_depth: bool,
    missing_research_acknowledgement: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    if sharp_reversal:
        codes.append("sharp_probability_reversal")
    if stale_context:
        codes.append("stale_market_context")
    if thin_depth:
        codes.append("thin_market_depth")
    if missing_research_acknowledgement:
        codes.append("missing_research_acknowledgement")
    return tuple(codes) if codes else ("market_momentum_reversal_clear",)


def _report_status(
    rows: tuple[MarketMomentumReversalWatchlistRow, ...],
    source_count: int,
) -> str:
    if source_count == 0:
        return "empty"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[MarketMomentumReversalWatchlistRow, ...],
    source_count: int,
) -> tuple[str, ...]:
    if source_count == 0:
        return ("market_momentum_reversal_watchlist_empty",)
    if not rows:
        return ("market_momentum_reversal_watchlist_clear",)
    codes: list[str] = []
    if any(row.sharp_reversal for row in rows):
        codes.append("sharp_probability_reversal_present")
    if any(row.stale_context for row in rows):
        codes.append("stale_market_context_present")
    if any(row.thin_depth for row in rows):
        codes.append("thin_market_depth_present")
    if any(row.missing_research_acknowledgement for row in rows):
        codes.append("missing_research_acknowledgement_present")
    return tuple(codes)


def _row_sort_key(
    row: MarketMomentumReversalWatchlistRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.flag_count,
        -row.reversal_delta,
        -row.context_age_seconds,
        row.available_depth,
        row.market_key,
    )


def _validate_input(row: MarketMomentumReversalWatchlistInput) -> None:
    if row.reversal_direction == "up_to_down":
        if row.extreme_probability < row.prior_probability:
            raise ValueError("up_to_down extreme_probability must not be below prior")
        if row.latest_probability > row.extreme_probability:
            raise ValueError("up_to_down latest_probability must not exceed extreme")
    if row.reversal_direction == "down_to_up":
        if row.extreme_probability > row.prior_probability:
            raise ValueError("down_to_up extreme_probability must not be above prior")
        if row.latest_probability < row.extreme_probability:
            raise ValueError("down_to_up latest_probability must not be below extreme")


def _validate_row(row: MarketMomentumReversalWatchlistRow) -> None:
    expected_probability_delta = _normalize_signed_probability_delta(
        "probability_delta",
        row.latest_probability - row.prior_probability,
    )
    if row.probability_delta != expected_probability_delta:
        raise ValueError("probability_delta must match probabilities")
    expected_reversal_delta = _normalize_probability_delta(
        "reversal_delta",
        abs(row.latest_probability - row.extreme_probability),
    )
    if row.reversal_delta != expected_reversal_delta:
        raise ValueError("reversal_delta must match probabilities")
    expected_flag_count = _count(
        sum(
            1
            for flag in (
                row.sharp_reversal,
                row.stale_context,
                row.thin_depth,
                row.missing_research_acknowledgement,
            )
            if flag
        ),
    )
    if row.flag_count != expected_flag_count:
        raise ValueError("flag_count must match row flags")
    expected_status = _row_status(
        sharp_reversal=row.sharp_reversal,
        stale_context=row.stale_context,
        thin_depth=row.thin_depth,
        missing_research_acknowledgement=row.missing_research_acknowledgement,
    )
    if row.status != expected_status:
        raise ValueError("status must match row flags")
    expected_reason_codes = _row_reason_codes(
        sharp_reversal=row.sharp_reversal,
        stale_context=row.stale_context,
        thin_depth=row.thin_depth,
        missing_research_acknowledgement=row.missing_research_acknowledgement,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row flags")


def _validate_report(report: MarketMomentumReversalWatchlistReport) -> None:
    if report.source_market_count < report.watchlist_market_count:
        raise ValueError("watchlist_market_count must not exceed source_market_count")
    if report.watchlist_market_count != _count(len(report.watchlist_rows)):
        raise ValueError("watchlist_market_count must match watchlist_rows")
    for field_name, flag_name in (
        ("sharp_reversal_count", "sharp_reversal"),
        ("stale_context_count", "stale_context"),
        ("thin_depth_count", "thin_depth"),
        (
            "missing_research_acknowledgement_count",
            "missing_research_acknowledgement",
        ),
    ):
        if getattr(report, field_name) != _flag_total(report.watchlist_rows, flag_name):
            raise ValueError(f"{field_name} must match watchlist_rows")
    if report.watchlist_ratio != _ratio(
        report.watchlist_market_count,
        report.source_market_count,
    ):
        raise ValueError("watchlist_ratio must match counts")
    if report.max_reversal_delta != _max_probability_delta(
        row.reversal_delta for row in report.watchlist_rows
    ):
        raise ValueError("max_reversal_delta must match watchlist_rows")
    if report.max_context_age_seconds != _max_age_seconds(
        row.context_age_seconds for row in report.watchlist_rows
    ):
        raise ValueError("max_context_age_seconds must match watchlist_rows")
    if report.min_available_depth != _min_count(
        row.available_depth for row in report.watchlist_rows
    ):
        raise ValueError("min_available_depth must match watchlist_rows")
    if report.status != _report_status(
        report.watchlist_rows,
        int(report.source_market_count),
    ):
        raise ValueError("status must match watchlist_rows")
    if report.reason_codes != _report_reason_codes(
        report.watchlist_rows,
        int(report.source_market_count),
    ):
        raise ValueError("reason_codes must match watchlist_rows")
    if report.watchlist_rows != tuple(sorted(report.watchlist_rows, key=_row_sort_key)):
        raise ValueError("watchlist_rows must use deterministic sequence")
    for row in report.watchlist_rows:
        if row.flag_count == ZERO_COUNT:
            raise ValueError("watchlist_rows must contain flagged rows")


def _validate_derived_validation_digest(
    report: MarketMomentumReversalWatchlistReport,
) -> None:
    _require_digest_string(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match derived report values")


def _normalize_rows(value: object) -> tuple[MarketMomentumReversalWatchlistRow, ...]:
    if type(value) is not tuple:
        raise ValueError("watchlist_rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketMomentumReversalWatchlistRow:
            raise ValueError("watchlist_rows must contain watchlist row values")
        require_paper_only_flags("market momentum reversal watchlist row", row)
    return rows


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(values)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known values")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unknown_payload_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    _require_canonical_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    if payload["config_version"] != DEFAULT_MARKET_MOMENTUM_REVERSAL_WATCHLIST_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    for field_name in REPORT_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    _require_member("status", payload["status"], WATCHLIST_STATUSES)
    _normalize_reason_codes(
        "reason_codes",
        payload["reason_codes"],
        REPORT_REASON_CODES,
    )
    if type(payload["watchlist_rows"]) is not list:
        raise ValueError("watchlist_rows must be a list")
    for row in payload["watchlist_rows"]:
        _validate_public_row_payload(row)
    _require_digest_string(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    if payload["derived_validation_digest"] != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload values")


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("watchlist_rows must contain JSON objects")
    _reject_unknown_payload_keys("watchlist row payload", value, ROW_PAYLOAD_KEYS)
    _require_canonical_string("market_key", value["market_key"])
    _require_member("status", value["status"], WATCHLIST_STATUSES)
    if value["status"] == "empty":
        raise ValueError("row status must not be empty")
    _require_member("reversal_direction", value["reversal_direction"], REVERSAL_DIRECTIONS)
    for field_name in ROW_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, value[field_name])
    for field_name in ROW_BOOL_PAYLOAD_FIELDS:
        if type(value[field_name]) is not bool:
            raise ValueError(f"{field_name} must be a bool")
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _normalize_reason_codes(
        "reason_codes",
        value["reason_codes"],
        ROW_REASON_CODES,
    )


def _reject_unknown_payload_keys(
    label: str,
    payload: dict[str, Any],
    allowed_keys: tuple[str, ...],
) -> None:
    if tuple(payload.keys()) != allowed_keys:
        if set(payload.keys()) != set(allowed_keys):
            raise ValueError(f"{label} must use the public readonly schema")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_fragment(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_fragment(label, value)


def _reject_unsafe_fragment(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _report_derived_validation_digest(
    report: MarketMomentumReversalWatchlistReport,
) -> str:
    return _derived_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_market_count=report.source_market_count,
        watchlist_market_count=report.watchlist_market_count,
        sharp_reversal_count=report.sharp_reversal_count,
        stale_context_count=report.stale_context_count,
        thin_depth_count=report.thin_depth_count,
        missing_research_acknowledgement_count=(
            report.missing_research_acknowledgement_count
        ),
        watchlist_ratio=report.watchlist_ratio,
        max_reversal_delta=report.max_reversal_delta,
        max_context_age_seconds=report.max_context_age_seconds,
        min_available_depth=report.min_available_depth,
        status=report.status,
        reason_codes=report.reason_codes,
        watchlist_rows=report.watchlist_rows,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    return _hash_digest_parts(
        (
            str(payload["generated_at"]),
            str(payload["config_version"]),
            *(str(payload[field_name]) for field_name in REPORT_DECIMAL_PAYLOAD_FIELDS),
            str(payload["status"]),
            *tuple(str(reason_code) for reason_code in payload["reason_codes"]),
            *tuple(
                component
                for row in payload["watchlist_rows"]
                for component in _payload_row_digest_parts(row)
            ),
            str(payload["paper_only"]),
            str(payload["report_only"]),
            str(payload["readonly"]),
        ),
    )


def _derived_validation_digest(
    *,
    generated_at: datetime,
    config_version: str,
    source_market_count: Decimal,
    watchlist_market_count: Decimal,
    sharp_reversal_count: Decimal,
    stale_context_count: Decimal,
    thin_depth_count: Decimal,
    missing_research_acknowledgement_count: Decimal,
    watchlist_ratio: Decimal,
    max_reversal_delta: Decimal,
    max_context_age_seconds: Decimal,
    min_available_depth: Decimal,
    status: str,
    reason_codes: tuple[str, ...],
    watchlist_rows: tuple[MarketMomentumReversalWatchlistRow, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> str:
    return _hash_digest_parts(
        (
            generated_at.isoformat(),
            config_version,
            str(source_market_count),
            str(watchlist_market_count),
            str(sharp_reversal_count),
            str(stale_context_count),
            str(thin_depth_count),
            str(missing_research_acknowledgement_count),
            str(watchlist_ratio),
            str(max_reversal_delta),
            str(max_context_age_seconds),
            str(min_available_depth),
            status,
            *reason_codes,
            *tuple(
                component
                for row in watchlist_rows
                for component in _row_digest_parts(row)
            ),
            str(paper_only),
            str(report_only),
            str(readonly),
        ),
    )


def _row_digest_parts(row: MarketMomentumReversalWatchlistRow) -> tuple[str, ...]:
    return (
        row.market_key,
        row.status,
        row.reversal_direction,
        str(row.prior_probability),
        str(row.extreme_probability),
        str(row.latest_probability),
        str(row.probability_delta),
        str(row.reversal_delta),
        str(row.probability_observation_age_seconds),
        str(row.context_age_seconds),
        str(row.available_depth),
        str(row.flag_count),
        str(row.sharp_reversal),
        str(row.stale_context),
        str(row.thin_depth),
        str(row.missing_research_acknowledgement),
        *row.reason_codes,
        str(row.paper_only),
        str(row.report_only),
        str(row.readonly),
    )


def _payload_row_digest_parts(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(row["market_key"]),
        str(row["status"]),
        str(row["reversal_direction"]),
        *(str(row[field_name]) for field_name in ROW_DECIMAL_PAYLOAD_FIELDS),
        str(row["sharp_reversal"]),
        str(row["stale_context"]),
        str(row["thin_depth"]),
        str(row["missing_research_acknowledgement"]),
        *tuple(str(reason_code) for reason_code in row["reason_codes"]),
        str(row["paper_only"]),
        str(row["report_only"]),
        str(row["readonly"]),
    )


def _hash_digest_parts(parts: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        encoded = part.encode("utf-8")
        digest.update(str(len(encoded)).encode("ascii"))
        digest.update(b":")
        digest.update(encoded)
        digest.update(b"|")
    return digest.hexdigest()


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _flag_total(
    rows: tuple[MarketMomentumReversalWatchlistRow, ...],
    field_name: str,
) -> Decimal:
    return _count(sum(1 for row in rows if getattr(row, field_name)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    _normalize_nonnegative_count("numerator", numerator)
    _normalize_nonnegative_count("denominator", denominator)
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _max_probability_delta(values: object) -> Decimal:
    maximum = ZERO_PROBABILITY
    for value in values:
        candidate = _normalize_probability_delta("value", value)
        if candidate > maximum:
            maximum = candidate
    return maximum


def _max_age_seconds(values: object) -> Decimal:
    maximum = ZERO_AGE_SECONDS
    for value in values:
        candidate = _normalize_nonnegative_age_seconds("value", value)
        if candidate > maximum:
            maximum = candidate
    return maximum


def _min_count(values: object) -> Decimal:
    minimum: Decimal | None = None
    for value in values:
        candidate = _normalize_nonnegative_count("value", value)
        if minimum is None or candidate < minimum:
            minimum = candidate
    return ZERO_COUNT if minimum is None else minimum


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    delta = generated_at - observed_at
    whole_seconds = delta.days * 86_400 + delta.seconds
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(whole_seconds) + Decimal(delta.microseconds) / Decimal(1_000_000)).quantize(
            AGE_SECONDS_QUANTUM,
        )


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = decimal_value.quantize(COUNT_QUANTUM)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return decimal_value.quantize(RATIO_QUANTUM)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_PROBABILITY or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value.quantize(PROBABILITY_QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_probability_delta(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_PROBABILITY or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value.quantize(PROBABILITY_QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_signed_probability_delta(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return decimal_value.quantize(PROBABILITY_QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_nonnegative_age_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_AGE_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return decimal_value.quantize(AGE_SECONDS_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a UTC offset")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


__all__ = (
    "DEFAULT_MARKET_MOMENTUM_REVERSAL_WATCHLIST_CONFIG_VERSION",
    "MarketMomentumReversalWatchlistConfig",
    "MarketMomentumReversalWatchlistInput",
    "MarketMomentumReversalWatchlistReport",
    "MarketMomentumReversalWatchlistRow",
    "build_market_momentum_reversal_watchlist_report",
    "market_momentum_reversal_watchlist_payload",
)
