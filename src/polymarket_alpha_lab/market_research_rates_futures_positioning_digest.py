"""Pure report-only reducer for rates futures positioning diagnostics."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_MARKET_RESEARCH_RATES_FUTURES_POSITIONING_DIGEST_CONFIG_VERSION = (
    "market-research-rates-futures-positioning-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
REDACTED_VALUE = "[REDACTED]"

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)

POSITION_CHANGE_REASON = "rates_futures_positioning_position_change"
PRESSURE_REASON = "rates_futures_positioning_pressure"
LOW_QUORUM_REASON = "rates_futures_positioning_low_quorum"
WATCH_SCORE_REASON = "rates_futures_positioning_watch_score"
BLOCKED_SCORE_REASON = "rates_futures_positioning_blocked_score"
STABLE_REASON = "rates_futures_positioning_stable"
DIGEST_PASSED_REASON = "rates_futures_positioning_digest_passed"
DIGEST_EMPTY_REASON = "rates_futures_positioning_digest_empty"

ROW_REASON_CODES = (
    BLOCKED_SCORE_REASON,
    LOW_QUORUM_REASON,
    POSITION_CHANGE_REASON,
    PRESSURE_REASON,
    STABLE_REASON,
    WATCH_SCORE_REASON,
)
DIGEST_REASON_CODES = (
    BLOCKED_SCORE_REASON,
    LOW_QUORUM_REASON,
    POSITION_CHANGE_REASON,
    PRESSURE_REASON,
    WATCH_SCORE_REASON,
    DIGEST_PASSED_REASON,
    DIGEST_EMPTY_REASON,
)
KNOWN_REASON_CODES = tuple(dict.fromkeys((*ROW_REASON_CODES, *DIGEST_REASON_CODES)))

NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_rates_futures_positioning_monitoring",
    WATCH_STATUS: "review_rates_futures_positioning_digest",
    BLOCKED_STATUS: "review_rates_futures_positioning_digest",
}

REDACT_REF_FRAGMENTS = (
    "bearer",
    "credential",
    "key",
    "pri" "vate",
    "se" "cret",
    "to" "ken",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_RATES_FUTURES_POSITIONING_DIGEST_CONFIG_VERSION",
    "RatesFuturesPositioningBucketRollup",
    "RatesFuturesPositioningDigestConfig",
    "RatesFuturesPositioningDigestInput",
    "RatesFuturesPositioningDigestReport",
    "RatesFuturesPositioningReasonCodeCount",
    "RatesFuturesPositioningRow",
    "build_market_research_rates_futures_positioning_digest",
    "market_research_rates_futures_positioning_digest_json_record",
)


@dataclass(frozen=True)
class RatesFuturesPositioningDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_RATES_FUTURES_POSITIONING_DIGEST_CONFIG_VERSION
    )
    watch_position_change_contracts: Decimal = Decimal("1000.000000")
    blocked_position_change_contracts: Decimal = Decimal("4000.000000")
    watch_position_pressure_share: Decimal = Decimal("0.100000")
    blocked_position_pressure_share: Decimal = Decimal("0.250000")
    source_quorum_watch_threshold: Decimal = Decimal("0.600000")
    positioning_score_watch_threshold: Decimal = Decimal("0.500000")
    positioning_score_blocked_threshold: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesFuturesPositioningDigestConfig:
            raise TypeError(
                "RatesFuturesPositioningDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not RatesFuturesPositioningDigestConfig:
            raise ValueError(
                "config must be exactly RatesFuturesPositioningDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_FUTURES_POSITIONING_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_position_change_contracts",
            "blocked_position_change_contracts",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_position_pressure_share",
            "blocked_position_pressure_share",
            "source_quorum_watch_threshold",
            "positioning_score_watch_threshold",
            "positioning_score_blocked_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_position_change_contracts <= ZERO:
            raise ValueError("watch_position_change_contracts must be positive")
        if (
            self.watch_position_change_contracts
            >= self.blocked_position_change_contracts
        ):
            raise ValueError(
                "watch_position_change_contracts must be below "
                "blocked_position_change_contracts",
            )
        if self.watch_position_pressure_share <= ZERO:
            raise ValueError("watch_position_pressure_share must be positive")
        if self.watch_position_pressure_share >= self.blocked_position_pressure_share:
            raise ValueError(
                "watch_position_pressure_share must be below "
                "blocked_position_pressure_share",
            )
        if self.positioning_score_watch_threshold <= ZERO:
            raise ValueError("positioning_score_watch_threshold must be positive")
        if (
            self.positioning_score_watch_threshold
            >= self.positioning_score_blocked_threshold
        ):
            raise ValueError(
                "positioning_score_watch_threshold must be below "
                "positioning_score_blocked_threshold",
            )
        require_paper_only_flags("RatesFuturesPositioningDigestConfig", self)


@dataclass(frozen=True)
class RatesFuturesPositioningDigestInput:
    condition_id: str
    rates_bucket: str
    observed_at: datetime
    prior_net_position_contracts: Decimal
    net_position_contracts: Decimal
    open_interest_contracts: Decimal
    source_quorum_share: Decimal
    source_config_version: str
    source_ref: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesFuturesPositioningDigestInput:
            raise TypeError(
                "RatesFuturesPositioningDigestInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not RatesFuturesPositioningDigestInput:
            raise ValueError(
                "input must be exactly RatesFuturesPositioningDigestInput",
            )
        _require_identifier("condition_id", self.condition_id)
        _require_identifier("rates_bucket", self.rates_bucket)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "prior_net_position_contracts",
            "net_position_contracts",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "open_interest_contracts",
            _normalize_nonnegative_decimal(
                "open_interest_contracts",
                self.open_interest_contracts,
            ),
        )
        object.__setattr__(
            self,
            "source_quorum_share",
            _normalize_probability("source_quorum_share", self.source_quorum_share),
        )
        _require_canonical_string("source_config_version", self.source_config_version)
        if self.source_ref is not None:
            _require_canonical_string("source_ref", self.source_ref)
        require_paper_only_flags("RatesFuturesPositioningDigestInput", self)


@dataclass(frozen=True)
class RatesFuturesPositioningReasonCodeCount:
    reason_code: str
    condition_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesFuturesPositioningReasonCodeCount:
            raise TypeError(
                "RatesFuturesPositioningReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not RatesFuturesPositioningReasonCodeCount:
            raise ValueError(
                "reason count must be exactly RatesFuturesPositioningReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "condition_count",
            _normalize_nonnegative_whole_decimal(
                "condition_count",
                self.condition_count,
            ),
        )
        require_paper_only_flags("RatesFuturesPositioningReasonCodeCount", self)


@dataclass(frozen=True)
class RatesFuturesPositioningRow:
    condition_id: str
    rates_bucket: str
    observed_at: datetime
    prior_net_position_contracts: Decimal
    net_position_contracts: Decimal
    position_change_contracts: Decimal
    open_interest_contracts: Decimal
    position_pressure_share: Decimal
    source_quorum_share: Decimal
    positioning_score: Decimal
    positioning_status: str
    source_config_version: str
    redacted_source_ref: str | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesFuturesPositioningRow:
            raise TypeError("RatesFuturesPositioningRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not RatesFuturesPositioningRow:
            raise ValueError("row must be exactly RatesFuturesPositioningRow")
        _require_identifier("condition_id", self.condition_id)
        _require_identifier("rates_bucket", self.rates_bucket)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "prior_net_position_contracts",
            "net_position_contracts",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "position_change_contracts",
            "open_interest_contracts",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "position_pressure_share",
            "source_quorum_share",
            "positioning_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("positioning_status", self.positioning_status)
        _require_canonical_string("source_config_version", self.source_config_version)
        if self.redacted_source_ref is not None:
            _require_canonical_string("redacted_source_ref", self.redacted_source_ref)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("RatesFuturesPositioningRow", self)


@dataclass(frozen=True)
class RatesFuturesPositioningBucketRollup:
    rates_bucket: str
    condition_count: Decimal
    positioning_shift_condition_count: Decimal
    blocked_condition_count: Decimal
    watch_condition_count: Decimal
    low_quorum_condition_count: Decimal
    position_change_condition_count: Decimal
    pressure_condition_count: Decimal
    max_position_change_contracts: Decimal | None
    max_position_pressure_share: Decimal | None
    max_positioning_score: Decimal | None
    bucket_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesFuturesPositioningBucketRollup:
            raise TypeError(
                "RatesFuturesPositioningBucketRollup does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not RatesFuturesPositioningBucketRollup:
            raise ValueError(
                "bucket rollup must be exactly RatesFuturesPositioningBucketRollup",
            )
        _require_identifier("rates_bucket", self.rates_bucket)
        for field_name in (
            "condition_count",
            "positioning_shift_condition_count",
            "blocked_condition_count",
            "watch_condition_count",
            "low_quorum_condition_count",
            "position_change_condition_count",
            "pressure_condition_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_position_change_contracts",
            _normalize_optional_nonnegative_decimal(
                "max_position_change_contracts",
                self.max_position_change_contracts,
            ),
        )
        object.__setattr__(
            self,
            "max_position_pressure_share",
            _normalize_optional_probability(
                "max_position_pressure_share",
                self.max_position_pressure_share,
            ),
        )
        object.__setattr__(
            self,
            "max_positioning_score",
            _normalize_optional_probability(
                "max_positioning_score",
                self.max_positioning_score,
            ),
        )
        _require_status("bucket_status", self.bucket_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_bucket_rollup(self)
        require_paper_only_flags("RatesFuturesPositioningBucketRollup", self)


@dataclass(frozen=True)
class RatesFuturesPositioningDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    condition_count: Decimal
    bucket_count: Decimal
    positioning_shift_condition_count: Decimal
    blocked_condition_count: Decimal
    watch_condition_count: Decimal
    low_quorum_condition_count: Decimal
    position_change_condition_count: Decimal
    pressure_condition_count: Decimal
    max_position_change_contracts: Decimal | None
    max_position_pressure_share: Decimal | None
    max_positioning_score: Decimal | None
    rows: tuple[RatesFuturesPositioningRow, ...]
    bucket_rollups: tuple[RatesFuturesPositioningBucketRollup, ...]
    reason_code_counts: tuple[RatesFuturesPositioningReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesFuturesPositioningDigestReport:
            raise TypeError(
                "RatesFuturesPositioningDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not RatesFuturesPositioningDigestReport:
            raise ValueError("report must be exactly RatesFuturesPositioningDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "condition_count",
            "bucket_count",
            "positioning_shift_condition_count",
            "blocked_condition_count",
            "watch_condition_count",
            "low_quorum_condition_count",
            "position_change_condition_count",
            "pressure_condition_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_position_change_contracts",
            _normalize_optional_nonnegative_decimal(
                "max_position_change_contracts",
                self.max_position_change_contracts,
            ),
        )
        object.__setattr__(
            self,
            "max_position_pressure_share",
            _normalize_optional_probability(
                "max_position_pressure_share",
                self.max_position_pressure_share,
            ),
        )
        object.__setattr__(
            self,
            "max_positioning_score",
            _normalize_optional_probability(
                "max_positioning_score",
                self.max_positioning_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "bucket_rollups",
            _normalize_bucket_rollups(self.bucket_rollups),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("RatesFuturesPositioningDigestReport", self)


def build_market_research_rates_futures_positioning_digest(
    inputs: Iterable[RatesFuturesPositioningDigestInput],
    *,
    config: RatesFuturesPositioningDigestConfig,
    generated_at: datetime,
) -> RatesFuturesPositioningDigestReport:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    if type(config) is not RatesFuturesPositioningDigestConfig:
        raise ValueError("config must be a RatesFuturesPositioningDigestConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    require_paper_only_flags("RatesFuturesPositioningDigestConfig", config)

    generated_at_utc = _as_utc("generated_at", generated_at)
    try:
        input_items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    _validate_inputs(input_items)

    rows = _build_rows(input_items, config=config, generated_at=generated_at_utc)
    bucket_rollups = _bucket_rollups_from_rows(rows)
    reason_codes = _digest_reason_codes(rows)
    digest_status = _digest_status(rows)
    return RatesFuturesPositioningDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        condition_count=Decimal(len(rows)),
        bucket_count=Decimal(len(bucket_rollups)),
        positioning_shift_condition_count=_count_by_status(
            rows,
            (WATCH_STATUS, BLOCKED_STATUS),
        ),
        blocked_condition_count=_count_by_status(rows, (BLOCKED_STATUS,)),
        watch_condition_count=_count_by_status(rows, (WATCH_STATUS,)),
        low_quorum_condition_count=_count_by_reason(rows, LOW_QUORUM_REASON),
        position_change_condition_count=_count_by_reason(rows, POSITION_CHANGE_REASON),
        pressure_condition_count=_count_by_reason(rows, PRESSURE_REASON),
        max_position_change_contracts=_max_optional_decimal(
            row.position_change_contracts for row in rows
        ),
        max_position_pressure_share=_max_optional_decimal(
            row.position_pressure_share for row in rows
        ),
        max_positioning_score=_max_optional_decimal(row.positioning_score for row in rows),
        rows=rows,
        bucket_rollups=bucket_rollups,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_rates_futures_positioning_digest_json_record(
    report: RatesFuturesPositioningDigestReport,
) -> dict[str, object]:
    if type(report) is not RatesFuturesPositioningDigestReport:
        raise ValueError("report must be a RatesFuturesPositioningDigestReport")
    require_paper_only_flags("RatesFuturesPositioningDigestReport", report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "digest_status": report.digest_status,
        "recommended_next_step": report.recommended_next_step,
        "condition_count": _count_decimal_string(report.condition_count),
        "bucket_count": _count_decimal_string(report.bucket_count),
        "positioning_shift_condition_count": _count_decimal_string(
            report.positioning_shift_condition_count,
        ),
        "blocked_condition_count": _count_decimal_string(report.blocked_condition_count),
        "watch_condition_count": _count_decimal_string(report.watch_condition_count),
        "low_quorum_condition_count": _count_decimal_string(
            report.low_quorum_condition_count,
        ),
        "position_change_condition_count": _count_decimal_string(
            report.position_change_condition_count,
        ),
        "pressure_condition_count": _count_decimal_string(
            report.pressure_condition_count,
        ),
        "max_position_change_contracts": _optional_decimal_string(
            report.max_position_change_contracts,
        ),
        "max_position_pressure_share": _optional_decimal_string(
            report.max_position_pressure_share,
        ),
        "max_positioning_score": _optional_decimal_string(report.max_positioning_score),
        "rows": [
            {
                "condition_id": row.condition_id,
                "rates_bucket": row.rates_bucket,
                "observed_at": row.observed_at.isoformat(),
                "prior_net_position_contracts": _decimal_string(
                    row.prior_net_position_contracts,
                ),
                "net_position_contracts": _decimal_string(row.net_position_contracts),
                "position_change_contracts": _decimal_string(
                    row.position_change_contracts,
                ),
                "open_interest_contracts": _decimal_string(row.open_interest_contracts),
                "position_pressure_share": _decimal_string(row.position_pressure_share),
                "source_quorum_share": _decimal_string(row.source_quorum_share),
                "positioning_score": _decimal_string(row.positioning_score),
                "positioning_status": row.positioning_status,
                "source_config_version": row.source_config_version,
                "redacted_source_ref": row.redacted_source_ref,
                "reason_codes": list(row.reason_codes),
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            }
            for row in report.rows
        ],
        "bucket_rollups": [
            {
                "rates_bucket": rollup.rates_bucket,
                "condition_count": _count_decimal_string(rollup.condition_count),
                "positioning_shift_condition_count": _count_decimal_string(
                    rollup.positioning_shift_condition_count,
                ),
                "blocked_condition_count": _count_decimal_string(
                    rollup.blocked_condition_count,
                ),
                "watch_condition_count": _count_decimal_string(
                    rollup.watch_condition_count,
                ),
                "low_quorum_condition_count": _count_decimal_string(
                    rollup.low_quorum_condition_count,
                ),
                "position_change_condition_count": _count_decimal_string(
                    rollup.position_change_condition_count,
                ),
                "pressure_condition_count": _count_decimal_string(
                    rollup.pressure_condition_count,
                ),
                "max_position_change_contracts": _optional_decimal_string(
                    rollup.max_position_change_contracts,
                ),
                "max_position_pressure_share": _optional_decimal_string(
                    rollup.max_position_pressure_share,
                ),
                "max_positioning_score": _optional_decimal_string(
                    rollup.max_positioning_score,
                ),
                "bucket_status": rollup.bucket_status,
                "reason_codes": list(rollup.reason_codes),
                "paper_only": rollup.paper_only,
                "report_only": rollup.report_only,
                "readonly": rollup.readonly,
            }
            for rollup in report.bucket_rollups
        ],
        "reason_code_counts": [
            {
                "reason_code": reason_count.reason_code,
                "condition_count": _count_decimal_string(reason_count.condition_count),
                "paper_only": reason_count.paper_only,
                "report_only": reason_count.report_only,
                "readonly": reason_count.readonly,
            }
            for reason_count in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _validate_inputs(
    inputs: tuple[RatesFuturesPositioningDigestInput, ...],
) -> None:
    seen_condition_ids: set[str] = set()
    for input_row in inputs:
        if type(input_row) is not RatesFuturesPositioningDigestInput:
            raise ValueError(
                "inputs must contain RatesFuturesPositioningDigestInput values",
            )
        require_paper_only_flags("RatesFuturesPositioningDigestInput", input_row)
        if input_row.condition_id in seen_condition_ids:
            raise ValueError("inputs must use unique condition_id values")
        seen_condition_ids.add(input_row.condition_id)


def _build_rows(
    inputs: tuple[RatesFuturesPositioningDigestInput, ...],
    *,
    config: RatesFuturesPositioningDigestConfig,
    generated_at: datetime,
) -> tuple[RatesFuturesPositioningRow, ...]:
    rows: list[RatesFuturesPositioningRow] = []
    for input_row in sorted(inputs, key=lambda row: (row.rates_bucket, row.condition_id)):
        if input_row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        position_change_contracts = _absolute_change(
            input_row.prior_net_position_contracts,
            input_row.net_position_contracts,
        )
        position_pressure_share = _bounded_ratio(
            position_change_contracts,
            input_row.open_interest_contracts,
        )
        positioning_score = _positioning_score(
            position_change_contracts=position_change_contracts,
            position_pressure_share=position_pressure_share,
            config=config,
        )
        reason_codes = _row_reason_codes(
            position_change_contracts=position_change_contracts,
            position_pressure_share=position_pressure_share,
            source_quorum_share=input_row.source_quorum_share,
            positioning_score=positioning_score,
            config=config,
        )
        rows.append(
            RatesFuturesPositioningRow(
                condition_id=input_row.condition_id,
                rates_bucket=input_row.rates_bucket,
                observed_at=input_row.observed_at,
                prior_net_position_contracts=input_row.prior_net_position_contracts,
                net_position_contracts=input_row.net_position_contracts,
                position_change_contracts=position_change_contracts,
                open_interest_contracts=input_row.open_interest_contracts,
                position_pressure_share=position_pressure_share,
                source_quorum_share=input_row.source_quorum_share,
                positioning_score=positioning_score,
                positioning_status=_status_from_reason_codes(reason_codes),
                source_config_version=input_row.source_config_version,
                redacted_source_ref=_redact_ref(input_row.source_ref),
                reason_codes=reason_codes,
            ),
        )
    return tuple(rows)


def _bucket_rollups_from_rows(
    rows: tuple[RatesFuturesPositioningRow, ...],
) -> tuple[RatesFuturesPositioningBucketRollup, ...]:
    grouped: dict[str, list[RatesFuturesPositioningRow]] = {}
    for row in rows:
        grouped.setdefault(row.rates_bucket, []).append(row)

    rollups: list[RatesFuturesPositioningBucketRollup] = []
    for rates_bucket, bucket_rows_list in sorted(grouped.items()):
        bucket_rows = tuple(bucket_rows_list)
        reason_codes = tuple(
            reason_code
            for reason_code in _unique_reason_codes(bucket_rows)
            if reason_code != STABLE_REASON
        )
        bucket_status = _digest_status(bucket_rows)
        rollups.append(
            RatesFuturesPositioningBucketRollup(
                rates_bucket=rates_bucket,
                condition_count=Decimal(len(bucket_rows)),
                positioning_shift_condition_count=_count_by_status(
                    bucket_rows,
                    (WATCH_STATUS, BLOCKED_STATUS),
                ),
                blocked_condition_count=_count_by_status(bucket_rows, (BLOCKED_STATUS,)),
                watch_condition_count=_count_by_status(bucket_rows, (WATCH_STATUS,)),
                low_quorum_condition_count=_count_by_reason(
                    bucket_rows,
                    LOW_QUORUM_REASON,
                ),
                position_change_condition_count=_count_by_reason(
                    bucket_rows,
                    POSITION_CHANGE_REASON,
                ),
                pressure_condition_count=_count_by_reason(
                    bucket_rows,
                    PRESSURE_REASON,
                ),
                max_position_change_contracts=_max_optional_decimal(
                    row.position_change_contracts for row in bucket_rows
                ),
                max_position_pressure_share=_max_optional_decimal(
                    row.position_pressure_share for row in bucket_rows
                ),
                max_positioning_score=_max_optional_decimal(
                    row.positioning_score for row in bucket_rows
                ),
                bucket_status=bucket_status,
                reason_codes=reason_codes if reason_codes else (STABLE_REASON,),
            ),
        )
    return tuple(rollups)


def _row_reason_codes(
    *,
    position_change_contracts: Decimal,
    position_pressure_share: Decimal,
    source_quorum_share: Decimal,
    positioning_score: Decimal,
    config: RatesFuturesPositioningDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if positioning_score >= config.positioning_score_blocked_threshold:
        reason_codes.append(BLOCKED_SCORE_REASON)
    elif positioning_score >= config.positioning_score_watch_threshold:
        reason_codes.append(WATCH_SCORE_REASON)
    if source_quorum_share < config.source_quorum_watch_threshold:
        reason_codes.append(LOW_QUORUM_REASON)
    if position_change_contracts >= config.watch_position_change_contracts:
        reason_codes.append(POSITION_CHANGE_REASON)
    if position_pressure_share >= config.watch_position_pressure_share:
        reason_codes.append(PRESSURE_REASON)
    if not reason_codes:
        reason_codes.append(STABLE_REASON)
    return _sort_reason_codes(tuple(dict.fromkeys(reason_codes)))


def _digest_reason_codes(rows: tuple[RatesFuturesPositioningRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (DIGEST_EMPTY_REASON,)
    reason_codes = tuple(
        reason_code
        for reason_code in _unique_reason_codes(rows)
        if reason_code != STABLE_REASON
    )
    return reason_codes if reason_codes else (DIGEST_PASSED_REASON,)


def _unique_reason_codes(rows: tuple[RatesFuturesPositioningRow, ...]) -> tuple[str, ...]:
    return _sort_reason_codes(
        tuple(
            {
                reason_code
                for row in rows
                for reason_code in row.reason_codes
            },
        ),
    )


def _digest_status(rows: tuple[RatesFuturesPositioningRow, ...]) -> str:
    if any(row.positioning_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.positioning_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if BLOCKED_SCORE_REASON in reason_codes:
        return BLOCKED_STATUS
    if reason_codes != (STABLE_REASON,):
        return WATCH_STATUS
    return PASS_STATUS


def _positioning_score(
    *,
    position_change_contracts: Decimal,
    position_pressure_share: Decimal,
    config: RatesFuturesPositioningDigestConfig,
) -> Decimal:
    change_score = _bounded_ratio(
        position_change_contracts,
        config.blocked_position_change_contracts,
    )
    pressure_score = _bounded_ratio(
        position_pressure_share,
        config.blocked_position_pressure_share,
    )
    return max(change_score, pressure_score).quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[RatesFuturesPositioningRow, ...],
) -> tuple[RatesFuturesPositioningReasonCodeCount, ...]:
    return tuple(
        RatesFuturesPositioningReasonCodeCount(
            reason_code=reason_code,
            condition_count=Decimal(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
        )
        for reason_code in reason_codes
        if reason_code not in (DIGEST_EMPTY_REASON, DIGEST_PASSED_REASON)
    )


def _count_by_status(
    rows: tuple[RatesFuturesPositioningRow, ...],
    statuses: tuple[str, ...],
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.positioning_status in statuses))


def _count_by_reason(
    rows: tuple[RatesFuturesPositioningRow, ...],
    reason_code: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _validate_row(row: RatesFuturesPositioningRow) -> None:
    expected_position_change = _absolute_change(
        row.prior_net_position_contracts,
        row.net_position_contracts,
    )
    if row.position_change_contracts != expected_position_change:
        raise ValueError(
            "position_change_contracts must equal absolute net position change",
        )
    expected_pressure_share = _bounded_ratio(
        row.position_change_contracts,
        row.open_interest_contracts,
    )
    if row.position_pressure_share != expected_pressure_share:
        raise ValueError(
            "position_pressure_share must equal position change over open interest",
        )
    if any(reason_code not in ROW_REASON_CODES for reason_code in row.reason_codes):
        raise ValueError("reason_codes must contain row reason codes")
    if row.positioning_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("positioning_status must match reason_codes")
    if row.positioning_status == PASS_STATUS and row.reason_codes != (STABLE_REASON,):
        raise ValueError("pass rows must only use the stable reason")
    if row.positioning_status != PASS_STATUS and STABLE_REASON in row.reason_codes:
        raise ValueError("shift rows must not include the stable reason")


def _validate_bucket_rollup(rollup: RatesFuturesPositioningBucketRollup) -> None:
    if rollup.positioning_shift_condition_count != (
        rollup.blocked_condition_count + rollup.watch_condition_count
    ):
        raise ValueError(
            "positioning_shift_condition_count must equal blocked plus watch counts",
        )
    if rollup.positioning_shift_condition_count > rollup.condition_count:
        raise ValueError(
            "positioning_shift_condition_count must not exceed condition_count",
        )
    for field_name in (
        "blocked_condition_count",
        "watch_condition_count",
        "low_quorum_condition_count",
        "position_change_condition_count",
        "pressure_condition_count",
    ):
        if getattr(rollup, field_name) > rollup.condition_count:
            raise ValueError(f"{field_name} must not exceed condition_count")
    max_values = (
        rollup.max_position_change_contracts,
        rollup.max_position_pressure_share,
        rollup.max_positioning_score,
    )
    if rollup.condition_count == ZERO:
        if any(value is not None for value in max_values):
            raise ValueError("empty bucket rollups must not include max values")
    elif any(value is None for value in max_values):
        raise ValueError("nonempty bucket rollups must include max values")
    if any(reason_code not in ROW_REASON_CODES for reason_code in rollup.reason_codes):
        raise ValueError("reason_codes must contain row reason codes")
    expected_status = _status_from_counts(
        blocked_count=rollup.blocked_condition_count,
        watch_count=rollup.watch_condition_count,
    )
    if rollup.bucket_status != expected_status:
        raise ValueError("bucket_status must match rollup counts")
    if rollup.bucket_status != _status_from_reason_codes(rollup.reason_codes):
        raise ValueError("bucket_status must match reason_codes")
    if rollup.bucket_status == PASS_STATUS and rollup.reason_codes != (STABLE_REASON,):
        raise ValueError("pass bucket rollups must only use the stable reason")
    if rollup.bucket_status != PASS_STATUS and STABLE_REASON in rollup.reason_codes:
        raise ValueError("shift bucket rollups must not include the stable reason")


def _validate_report(report: RatesFuturesPositioningDigestReport) -> None:
    if report.condition_count != Decimal(len(report.rows)):
        raise ValueError("condition_count must equal row count")
    if report.bucket_count != Decimal(len(report.bucket_rollups)):
        raise ValueError("bucket_count must equal bucket rollup count")
    if report.positioning_shift_condition_count != (
        report.blocked_condition_count + report.watch_condition_count
    ):
        raise ValueError(
            "positioning_shift_condition_count must equal blocked plus watch counts",
        )
    if report.positioning_shift_condition_count > report.condition_count:
        raise ValueError(
            "positioning_shift_condition_count must not exceed condition_count",
        )
    if report.blocked_condition_count != _count_by_status(report.rows, (BLOCKED_STATUS,)):
        raise ValueError("blocked_condition_count must match rows")
    if report.watch_condition_count != _count_by_status(report.rows, (WATCH_STATUS,)):
        raise ValueError("watch_condition_count must match rows")
    if report.low_quorum_condition_count != _count_by_reason(
        report.rows,
        LOW_QUORUM_REASON,
    ):
        raise ValueError("low_quorum_condition_count must match rows")
    if report.position_change_condition_count != _count_by_reason(
        report.rows,
        POSITION_CHANGE_REASON,
    ):
        raise ValueError("position_change_condition_count must match rows")
    if report.pressure_condition_count != _count_by_reason(report.rows, PRESSURE_REASON):
        raise ValueError("pressure_condition_count must match rows")
    if report.max_position_change_contracts != _max_optional_decimal(
        row.position_change_contracts for row in report.rows
    ):
        raise ValueError("max_position_change_contracts must match rows")
    if report.max_position_pressure_share != _max_optional_decimal(
        row.position_pressure_share for row in report.rows
    ):
        raise ValueError("max_position_pressure_share must match rows")
    if report.max_positioning_score != _max_optional_decimal(
        row.positioning_score for row in report.rows
    ):
        raise ValueError("max_positioning_score must match rows")
    if report.bucket_rollups != _bucket_rollups_from_rows(report.rows):
        raise ValueError("bucket_rollups must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    expected_reason_codes = _digest_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        expected_reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match reason_codes and rows")


def _normalize_rows(
    rows: tuple[RatesFuturesPositioningRow, ...],
) -> tuple[RatesFuturesPositioningRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not RatesFuturesPositioningRow:
            raise ValueError("rows must contain RatesFuturesPositioningRow values")
        require_paper_only_flags("RatesFuturesPositioningRow", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_bucket_rollups(
    rollups: tuple[RatesFuturesPositioningBucketRollup, ...],
) -> tuple[RatesFuturesPositioningBucketRollup, ...]:
    if type(rollups) is not tuple:
        raise ValueError("bucket_rollups must be a tuple")
    for rollup in rollups:
        if type(rollup) is not RatesFuturesPositioningBucketRollup:
            raise ValueError(
                "bucket_rollups must contain RatesFuturesPositioningBucketRollup "
                "values",
            )
        require_paper_only_flags("RatesFuturesPositioningBucketRollup", rollup)
    if rollups != tuple(sorted(rollups, key=lambda rollup: rollup.rates_bucket)):
        raise ValueError("bucket_rollups must be sorted deterministically")
    return rollups


def _normalize_reason_code_counts(
    counts: tuple[RatesFuturesPositioningReasonCodeCount, ...],
) -> tuple[RatesFuturesPositioningReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not RatesFuturesPositioningReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "RatesFuturesPositioningReasonCodeCount values",
            )
        require_paper_only_flags("RatesFuturesPositioningReasonCodeCount", count)
    if counts != tuple(sorted(counts, key=lambda count: _reason_rank(count.reason_code))):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
    if _sort_reason_codes(tuple(set(reason_codes))) != reason_codes:
        raise ValueError(f"{field_name} must be unique and sorted")
    return reason_codes


def _row_sort_key(row: RatesFuturesPositioningRow) -> tuple[str, str]:
    return (row.rates_bucket, row.condition_id)


def _reason_rank(reason_code: str) -> int:
    return KNOWN_REASON_CODES.index(reason_code)


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(reason_codes, key=_reason_rank))


def _status_from_counts(*, blocked_count: Decimal, watch_count: Decimal) -> str:
    if blocked_count > ZERO:
        return BLOCKED_STATUS
    if watch_count > ZERO:
        return WATCH_STATUS
    return PASS_STATUS


def _require_reason_code(field_name: str, reason_code: str) -> None:
    _require_canonical_string(field_name, reason_code)
    if reason_code not in KNOWN_REASON_CODES:
        raise ValueError(f"{field_name} contains unknown reason code")


def _require_status(field_name: str, status: str) -> None:
    _require_canonical_string(field_name, status)
    if status not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES!r}")


def _require_identifier(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have surrounding whitespace")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_optional_probability(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _absolute_change(before: Decimal, after: Decimal) -> Decimal:
    return abs(after - before).quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    value = (numerator / denominator).quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if value > ONE:
        return ONE.quantize(QUANTUM)
    return value


def _max_optional_decimal(values: Iterable[Decimal]) -> Decimal | None:
    value_items = tuple(values)
    if not value_items:
        return None
    return max(value_items)


def _redact_ref(value: str | None) -> str | None:
    if value is None:
        return None
    lowered = value.lower()
    if any(fragment in lowered for fragment in REDACT_REF_FRAGMENTS):
        return REDACTED_VALUE
    return value


def _decimal_string(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    return str(value)


def _optional_decimal_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_string(value)


def _count_decimal_string(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("count value must be a Decimal")
    if not value.is_finite():
        raise ValueError("count value must be finite")
    if value != value.to_integral_value():
        raise ValueError("count value must be whole")
    return str(value.to_integral_value())
