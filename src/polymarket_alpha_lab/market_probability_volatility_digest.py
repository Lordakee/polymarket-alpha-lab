"""Pure report-only reducer for market probability volatility."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_MARKET_PROBABILITY_VOLATILITY_DIGEST_CONFIG_VERSION = (
    "market-probability-volatility-digest-v0"
)
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
UNSAFE_PUBLIC_SURFACE_TERMS = (
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
DIGEST_STATUSES = (PASS_STATUS, WATCH_STATUS)
ROW_STATUSES = (PASS_STATUS, WATCH_STATUS)

RECENT_PROBABILITY_CHANGE_REASON = (
    "probability_volatility_recent_probability_change_high"
)
BID_ASK_MOVE_REASON = "probability_volatility_bid_ask_move_high"
FORECAST_REVISION_REASON = "probability_volatility_forecast_revision_high"
CONFIDENCE_INSTABILITY_REASON = (
    "probability_volatility_confidence_instability_high"
)
STALE_EVIDENCE_REASON = "probability_volatility_stale_evidence_present"
MARKET_STABLE_REASON = "probability_volatility_market_stable"
DIGEST_PASSED_REASON = "probability_volatility_digest_passed"
DIGEST_EMPTY_REASON = "probability_volatility_digest_empty"

ROW_REASON_CODES = (
    BID_ASK_MOVE_REASON,
    CONFIDENCE_INSTABILITY_REASON,
    FORECAST_REVISION_REASON,
    RECENT_PROBABILITY_CHANGE_REASON,
    STALE_EVIDENCE_REASON,
    MARKET_STABLE_REASON,
)
DIGEST_REASON_CODES = (
    BID_ASK_MOVE_REASON,
    CONFIDENCE_INSTABILITY_REASON,
    FORECAST_REVISION_REASON,
    RECENT_PROBABILITY_CHANGE_REASON,
    STALE_EVIDENCE_REASON,
    DIGEST_PASSED_REASON,
    DIGEST_EMPTY_REASON,
)
KNOWN_REASON_CODES = tuple(
    dict.fromkeys((*ROW_REASON_CODES, *DIGEST_REASON_CODES)),
)

NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_probability_volatility_monitoring",
    WATCH_STATUS: "review_probability_volatility_before_use",
}

__all__ = (
    "DEFAULT_MARKET_PROBABILITY_VOLATILITY_DIGEST_CONFIG_VERSION",
    "MarketProbabilityVolatilityDigestConfig",
    "MarketProbabilityVolatilityInput",
    "MarketProbabilityVolatilityReasonCodeCount",
    "MarketProbabilityVolatilityRow",
    "MarketProbabilityVolatilityDigestReport",
    "build_market_probability_volatility_digest",
    "market_probability_volatility_digest_json_payload",
    "validate_market_probability_volatility_digest_public_payload",
)


@dataclass(frozen=True)
class MarketProbabilityVolatilityDigestConfig:
    config_version: str = DEFAULT_MARKET_PROBABILITY_VOLATILITY_DIGEST_CONFIG_VERSION
    recent_probability_move_threshold: Decimal = Decimal("0.050000")
    bid_ask_move_threshold: Decimal = Decimal("0.080000")
    forecast_revision_threshold: Decimal = Decimal("0.100000")
    confidence_move_threshold: Decimal = Decimal("0.150000")
    stale_evidence_seconds_threshold: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityVolatilityDigestConfig:
            raise TypeError(
                "MarketProbabilityVolatilityDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityVolatilityDigestConfig:
            raise ValueError(
                "config must be exactly MarketProbabilityVolatilityDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "recent_probability_move_threshold",
            "bid_ask_move_threshold",
            "forecast_revision_threshold",
            "confidence_move_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_evidence_seconds_threshold",
            _normalize_nonnegative_decimal(
                "stale_evidence_seconds_threshold",
                self.stale_evidence_seconds_threshold,
            ),
        )
        require_paper_only_flags("MarketProbabilityVolatilityDigestConfig", self)


@dataclass(frozen=True)
class MarketProbabilityVolatilityInput:
    market_id: str
    probability_before: Decimal
    probability_after: Decimal
    bid_before: Decimal | None
    bid_after: Decimal | None
    ask_before: Decimal | None
    ask_after: Decimal | None
    forecast_probability_before: Decimal | None
    forecast_probability_after: Decimal | None
    confidence_before: Decimal | None
    confidence_after: Decimal | None
    evidence_observed_at: datetime
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityVolatilityInput:
            raise TypeError(
                "MarketProbabilityVolatilityInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityVolatilityInput:
            raise ValueError(
                "input must be exactly MarketProbabilityVolatilityInput",
            )
        _require_market_id("market_id", self.market_id)
        for field_name in ("probability_before", "probability_after"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "bid_before",
            "bid_after",
            "ask_before",
            "ask_after",
            "forecast_probability_before",
            "forecast_probability_after",
            "confidence_before",
            "confidence_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        _require_canonical_string("source_config_version", self.source_config_version)
        _reject_sensitive_value("market_id", self.market_id)
        _reject_sensitive_value("source_config_version", self.source_config_version)
        require_paper_only_flags("MarketProbabilityVolatilityInput", self)


@dataclass(frozen=True)
class MarketProbabilityVolatilityReasonCodeCount:
    reason_code: str
    market_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityVolatilityReasonCodeCount:
            raise TypeError(
                "MarketProbabilityVolatilityReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityVolatilityReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketProbabilityVolatilityReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "market_count",
            _normalize_nonnegative_whole_decimal("market_count", self.market_count),
        )
        require_paper_only_flags("MarketProbabilityVolatilityReasonCodeCount", self)


@dataclass(frozen=True)
class MarketProbabilityVolatilityRow:
    market_id: str
    probability_before: Decimal
    probability_after: Decimal
    probability_change: Decimal
    bid_ask_move: Decimal | None
    forecast_revision: Decimal | None
    confidence_change: Decimal | None
    evidence_observed_at: datetime
    evidence_age_seconds: Decimal
    source_config_version: str
    volatility_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityVolatilityRow:
            raise TypeError(
                "MarketProbabilityVolatilityRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityVolatilityRow:
            raise ValueError("row must be exactly MarketProbabilityVolatilityRow")
        _require_market_id("market_id", self.market_id)
        for field_name in (
            "probability_before",
            "probability_after",
            "probability_change",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "bid_ask_move",
            "forecast_revision",
            "confidence_change",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        _require_canonical_string("source_config_version", self.source_config_version)
        _reject_sensitive_value("source_config_version", self.source_config_version)
        _require_row_status("volatility_status", self.volatility_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("MarketProbabilityVolatilityRow", self)


@dataclass(frozen=True)
class MarketProbabilityVolatilityDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    market_count: Decimal
    volatile_market_count: Decimal
    stale_evidence_market_count: Decimal
    max_probability_change: Decimal | None
    max_bid_ask_move: Decimal | None
    max_forecast_revision: Decimal | None
    max_confidence_change: Decimal | None
    max_evidence_age_seconds: Decimal | None
    rows: tuple[MarketProbabilityVolatilityRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketProbabilityVolatilityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityVolatilityDigestReport:
            raise TypeError(
                "MarketProbabilityVolatilityDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityVolatilityDigestReport:
            raise ValueError(
                "report must be exactly MarketProbabilityVolatilityDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "market_count",
            "volatile_market_count",
            "stale_evidence_market_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "max_probability_change",
            "max_bid_ask_move",
            "max_forecast_revision",
            "max_confidence_change",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
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
        require_paper_only_flags("MarketProbabilityVolatilityDigestReport", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_market_probability_volatility_digest(
    inputs: Iterable[MarketProbabilityVolatilityInput],
    *,
    config: MarketProbabilityVolatilityDigestConfig,
    generated_at: datetime,
) -> MarketProbabilityVolatilityDigestReport:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    if type(config) is not MarketProbabilityVolatilityDigestConfig:
        raise ValueError("config must be a MarketProbabilityVolatilityDigestConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    require_paper_only_flags("MarketProbabilityVolatilityDigestConfig", config)

    generated_at_utc = _as_utc("generated_at", generated_at)
    try:
        input_items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    _validate_inputs(input_items)
    rows = _build_rows(input_items, config=config, generated_at=generated_at_utc)
    reason_codes = _digest_reason_codes(rows)
    digest_status = WATCH_STATUS if _volatile_market_count(rows) > ZERO else PASS_STATUS
    return MarketProbabilityVolatilityDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        market_count=Decimal(len(rows)),
        volatile_market_count=_volatile_market_count(rows),
        stale_evidence_market_count=_stale_evidence_market_count(rows),
        max_probability_change=_max_optional_decimal(
            row.probability_change for row in rows
        ),
        max_bid_ask_move=_max_optional_decimal(row.bid_ask_move for row in rows),
        max_forecast_revision=_max_optional_decimal(
            row.forecast_revision for row in rows
        ),
        max_confidence_change=_max_optional_decimal(
            row.confidence_change for row in rows
        ),
        max_evidence_age_seconds=_max_optional_decimal(
            row.evidence_age_seconds for row in rows
        ),
        rows=rows,
        source_config_versions=tuple(
            (row.market_id, row.source_config_version) for row in rows
        ),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        reason_codes=reason_codes,
    )


def market_probability_volatility_digest_json_payload(
    report: MarketProbabilityVolatilityDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketProbabilityVolatilityDigestReport:
        raise ValueError("report must be a MarketProbabilityVolatilityDigestReport")
    require_paper_only_flags("MarketProbabilityVolatilityDigestReport", report)
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_market_probability_volatility_digest_public_payload(payload)
    return payload


def validate_market_probability_volatility_digest_public_payload(
    payload: dict[str, object],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("market probability volatility payload", payload)
    _require_public_payload_flags(payload)
    _require_public_payload_decimal_strings(payload)
    actual_digest = _payload_required_string(payload, "derived_validation_digest")
    if actual_digest != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _report_public_payload_for_digest(
    report: MarketProbabilityVolatilityDigestReport,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "digest_status": report.digest_status,
        "recommended_next_step": report.recommended_next_step,
        "market_count": _count_decimal_string(report.market_count),
        "volatile_market_count": _count_decimal_string(report.volatile_market_count),
        "stale_evidence_market_count": _count_decimal_string(
            report.stale_evidence_market_count,
        ),
        "max_probability_change": _optional_decimal_string(
            report.max_probability_change,
        ),
        "max_bid_ask_move": _optional_decimal_string(report.max_bid_ask_move),
        "max_forecast_revision": _optional_decimal_string(
            report.max_forecast_revision,
        ),
        "max_confidence_change": _optional_decimal_string(
            report.max_confidence_change,
        ),
        "max_evidence_age_seconds": _optional_decimal_string(
            report.max_evidence_age_seconds,
        ),
        "rows": [
            {
                "market_id": row.market_id,
                "probability_before": _decimal_string(row.probability_before),
                "probability_after": _decimal_string(row.probability_after),
                "probability_change": _decimal_string(row.probability_change),
                "bid_ask_move": _optional_decimal_string(row.bid_ask_move),
                "forecast_revision": _optional_decimal_string(row.forecast_revision),
                "confidence_change": _optional_decimal_string(row.confidence_change),
                "evidence_observed_at": row.evidence_observed_at.isoformat(),
                "evidence_age_seconds": _decimal_string(row.evidence_age_seconds),
                "source_config_version": row.source_config_version,
                "volatility_status": row.volatility_status,
                "reason_codes": list(row.reason_codes),
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            }
            for row in report.rows
        ],
        "source_config_versions": [
            [market_id, config_version]
            for market_id, config_version in report.source_config_versions
        ],
        "reason_code_counts": [
            {
                "reason_code": reason_count.reason_code,
                "market_count": _count_decimal_string(reason_count.market_count),
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
    inputs: tuple[MarketProbabilityVolatilityInput, ...],
) -> None:
    seen_market_ids: set[str] = set()
    for input_row in inputs:
        if type(input_row) is not MarketProbabilityVolatilityInput:
            raise ValueError(
                "inputs must contain MarketProbabilityVolatilityInput values",
            )
        require_paper_only_flags("MarketProbabilityVolatilityInput", input_row)
        if input_row.market_id in seen_market_ids:
            raise ValueError("inputs must use unique market_id values")
        seen_market_ids.add(input_row.market_id)


def _build_rows(
    inputs: tuple[MarketProbabilityVolatilityInput, ...],
    *,
    config: MarketProbabilityVolatilityDigestConfig,
    generated_at: datetime,
) -> tuple[MarketProbabilityVolatilityRow, ...]:
    rows: list[MarketProbabilityVolatilityRow] = []
    for input_row in sorted(inputs, key=lambda row: row.market_id):
        if input_row.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must not be after generated_at")
        probability_change = _absolute_change(
            input_row.probability_before,
            input_row.probability_after,
        )
        bid_ask_move = _max_optional_decimal(
            (
                _optional_absolute_change(input_row.bid_before, input_row.bid_after),
                _optional_absolute_change(input_row.ask_before, input_row.ask_after),
            ),
        )
        forecast_revision = _optional_absolute_change(
            input_row.forecast_probability_before,
            input_row.forecast_probability_after,
        )
        confidence_change = _optional_absolute_change(
            input_row.confidence_before,
            input_row.confidence_after,
        )
        evidence_age_seconds = _normalize_nonnegative_decimal(
            "evidence_age_seconds",
            Decimal(str((generated_at - input_row.evidence_observed_at).total_seconds())),
        )
        reason_codes = _row_reason_codes(
            probability_change=probability_change,
            bid_ask_move=bid_ask_move,
            forecast_revision=forecast_revision,
            confidence_change=confidence_change,
            evidence_age_seconds=evidence_age_seconds,
            config=config,
        )
        rows.append(
            MarketProbabilityVolatilityRow(
                market_id=input_row.market_id,
                probability_before=input_row.probability_before,
                probability_after=input_row.probability_after,
                probability_change=probability_change,
                bid_ask_move=bid_ask_move,
                forecast_revision=forecast_revision,
                confidence_change=confidence_change,
                evidence_observed_at=input_row.evidence_observed_at,
                evidence_age_seconds=evidence_age_seconds,
                source_config_version=input_row.source_config_version,
                volatility_status=(
                    PASS_STATUS
                    if reason_codes == (MARKET_STABLE_REASON,)
                    else WATCH_STATUS
                ),
                reason_codes=reason_codes,
            ),
        )
    return tuple(rows)


def _row_reason_codes(
    *,
    probability_change: Decimal,
    bid_ask_move: Decimal | None,
    forecast_revision: Decimal | None,
    confidence_change: Decimal | None,
    evidence_age_seconds: Decimal,
    config: MarketProbabilityVolatilityDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if bid_ask_move is not None and bid_ask_move >= config.bid_ask_move_threshold:
        reason_codes.append(BID_ASK_MOVE_REASON)
    if (
        confidence_change is not None
        and confidence_change >= config.confidence_move_threshold
    ):
        reason_codes.append(CONFIDENCE_INSTABILITY_REASON)
    if (
        forecast_revision is not None
        and forecast_revision >= config.forecast_revision_threshold
    ):
        reason_codes.append(FORECAST_REVISION_REASON)
    if probability_change >= config.recent_probability_move_threshold:
        reason_codes.append(RECENT_PROBABILITY_CHANGE_REASON)
    if evidence_age_seconds >= config.stale_evidence_seconds_threshold:
        reason_codes.append(STALE_EVIDENCE_REASON)
    if not reason_codes:
        return (MARKET_STABLE_REASON,)
    return tuple(reason_codes)


def _digest_reason_codes(
    rows: tuple[MarketProbabilityVolatilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (DIGEST_EMPTY_REASON,)
    reason_codes = tuple(
        reason_code
        for reason_code in DIGEST_REASON_CODES
        if reason_code
        in {
            row_reason_code
            for row in rows
            for row_reason_code in row.reason_codes
            if row_reason_code != MARKET_STABLE_REASON
        }
    )
    if not reason_codes:
        return (DIGEST_PASSED_REASON,)
    return reason_codes


def _reason_code_counts_from_rows(
    rows: tuple[MarketProbabilityVolatilityRow, ...],
) -> tuple[MarketProbabilityVolatilityReasonCodeCount, ...]:
    return _reason_code_counts(_digest_reason_codes(rows), rows)


def _reason_code_counts_from_report(
    report: MarketProbabilityVolatilityDigestReport,
) -> tuple[MarketProbabilityVolatilityReasonCodeCount, ...]:
    return _reason_code_counts(report.reason_codes, report.rows)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketProbabilityVolatilityRow, ...],
) -> tuple[MarketProbabilityVolatilityReasonCodeCount, ...]:
    counts: list[MarketProbabilityVolatilityReasonCodeCount] = []
    for reason_code in reason_codes:
        if reason_code == DIGEST_EMPTY_REASON:
            market_count = ZERO
        elif reason_code == DIGEST_PASSED_REASON:
            market_count = Decimal(len(rows))
        else:
            market_count = Decimal(
                sum(1 for row in rows if reason_code in row.reason_codes),
            )
        counts.append(
            MarketProbabilityVolatilityReasonCodeCount(
                reason_code=reason_code,
                market_count=market_count,
            ),
        )
    return tuple(counts)


def _validate_row(row: MarketProbabilityVolatilityRow) -> None:
    expected_probability_change = _absolute_change(
        row.probability_before,
        row.probability_after,
    )
    if row.probability_change != expected_probability_change:
        raise ValueError("probability_change must match probability inputs")
    if row.volatility_status == PASS_STATUS:
        if row.reason_codes != (MARKET_STABLE_REASON,):
            raise ValueError("pass rows must use the stable reason code")
    elif row.reason_codes == (MARKET_STABLE_REASON,):
        raise ValueError("watch rows must not use only the stable reason code")


def _validate_report(report: MarketProbabilityVolatilityDigestReport) -> None:
    if report.market_count != Decimal(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.volatile_market_count != _volatile_market_count(report.rows):
        raise ValueError("volatile_market_count must match rows")
    if report.stale_evidence_market_count != _stale_evidence_market_count(report.rows):
        raise ValueError("stale_evidence_market_count must match rows")
    if report.max_probability_change != _max_optional_decimal(
        row.probability_change for row in report.rows
    ):
        raise ValueError("max_probability_change must match rows")
    if report.max_bid_ask_move != _max_optional_decimal(
        row.bid_ask_move for row in report.rows
    ):
        raise ValueError("max_bid_ask_move must match rows")
    if report.max_forecast_revision != _max_optional_decimal(
        row.forecast_revision for row in report.rows
    ):
        raise ValueError("max_forecast_revision must match rows")
    if report.max_confidence_change != _max_optional_decimal(
        row.confidence_change for row in report.rows
    ):
        raise ValueError("max_confidence_change must match rows")
    if report.max_evidence_age_seconds != _max_optional_decimal(
        row.evidence_age_seconds for row in report.rows
    ):
        raise ValueError("max_evidence_age_seconds must match rows")
    expected_status = (
        WATCH_STATUS if _volatile_market_count(report.rows) > ZERO else PASS_STATUS
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    expected_versions = tuple(
        (row.market_id, row.source_config_version) for row in report.rows
    )
    if report.source_config_versions != expected_versions:
        raise ValueError("source_config_versions must match rows")
    expected_reason_codes = _digest_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_reason_code_counts = _reason_code_counts_from_report(report)
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _normalize_rows(value: object) -> tuple[MarketProbabilityVolatilityRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not MarketProbabilityVolatilityRow:
            raise ValueError("rows must contain MarketProbabilityVolatilityRow values")
        require_paper_only_flags("MarketProbabilityVolatilityRow", row)
    if tuple(sorted(rows, key=lambda row: row.market_id)) != rows:
        raise ValueError("rows must be sorted by market_id")
    return rows


def _normalize_source_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("source_config_versions must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("source_config_versions must be an iterable") from exc
    normalized: list[tuple[str, str]] = []
    for row in rows:
        if type(row) not in (tuple, list) or len(row) != 2:
            raise ValueError("source_config_versions must contain pairs")
        market_id, config_version = row
        if type(market_id) is not str or type(config_version) is not str:
            raise ValueError("source_config_versions must contain string pairs")
        _require_market_id("market_id", market_id)
        _require_canonical_string("config_version", config_version)
        _reject_sensitive_value("config_version", config_version)
        normalized.append((market_id, config_version))
    return tuple(normalized)


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketProbabilityVolatilityReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not MarketProbabilityVolatilityReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason counts")
        require_paper_only_flags("MarketProbabilityVolatilityReasonCodeCount", row)
    if tuple(sorted(rows, key=lambda row: row.reason_code)) != rows:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return rows


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
    if tuple(sorted(reason_codes)) != reason_codes:
        raise ValueError(f"{field_name} must be sorted")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return reason_codes


def _volatile_market_count(rows: tuple[MarketProbabilityVolatilityRow, ...]) -> Decimal:
    return Decimal(sum(1 for row in rows if row.volatility_status == WATCH_STATUS))


def _stale_evidence_market_count(
    rows: tuple[MarketProbabilityVolatilityRow, ...],
) -> Decimal:
    return Decimal(
        sum(1 for row in rows if STALE_EVIDENCE_REASON in row.reason_codes),
    )


def _max_optional_decimal(values: object) -> Decimal | None:
    decimal_values = tuple(value for value in values if value is not None)
    if not decimal_values:
        return None
    return _quantize_decimal(max(decimal_values))


def _optional_absolute_change(
    before: Decimal | None,
    after: Decimal | None,
) -> Decimal | None:
    if before is None or after is None:
        return None
    return _absolute_change(before, after)


def _absolute_change(before: Decimal, after: Decimal) -> Decimal:
    return _quantize_decimal(abs(after - before))


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_market_id(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if not all(char.islower() or char.isdigit() or char == "_" for char in value):
        raise ValueError(f"{field_name} must be lowercase snake case")
    _reject_sensitive_value(field_name, value)


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_reason_code(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in KNOWN_REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_row_status(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be a known row status")


def _require_digest_status(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a known digest status")


def _report_derived_validation_digest(
    report: MarketProbabilityVolatilityDigestReport,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _public_payload_derived_validation_digest(payload: dict[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded_payload = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for key_or_value in _public_payload_strings(value):
        lowered = key_or_value.lower()
        if any(term in lowered for term in UNSAFE_PUBLIC_SURFACE_TERMS):
            raise ValueError(f"unsafe surface value in {label}")


def _public_payload_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            strings.append(key)
            strings.extend(_public_payload_strings(item))
        return tuple(strings)
    if isinstance(value, list):
        strings = []
        for item in value:
            strings.extend(_public_payload_strings(item))
        return tuple(strings)
    if type(value) is str:
        return (value,)
    return ()


def _require_public_payload_flags(payload: dict[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True in public payload")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("public payload rows must be a list")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("public payload rows must contain dict rows")
        for field_name in ("paper_only", "report_only", "readonly"):
            if row.get(field_name) is not True:
                raise ValueError(f"{field_name} must be True in public payload row")
    reason_counts = payload.get("reason_code_counts")
    if not isinstance(reason_counts, list):
        raise ValueError("public payload reason_code_counts must be a list")
    for reason_count in reason_counts:
        if not isinstance(reason_count, dict):
            raise ValueError("public payload reason_code_counts must contain dict rows")
        for field_name in ("paper_only", "report_only", "readonly"):
            if reason_count.get(field_name) is not True:
                raise ValueError(
                    f"{field_name} must be True in public payload reason count",
                )


def _require_public_payload_decimal_strings(payload: dict[str, object]) -> None:
    _reject_public_payload_numbers(payload)
    for field_name in (
        "market_count",
        "volatile_market_count",
        "stale_evidence_market_count",
        "max_probability_change",
        "max_bid_ask_move",
        "max_forecast_revision",
        "max_confidence_change",
        "max_evidence_age_seconds",
    ):
        _require_optional_decimal_string(field_name, payload.get(field_name))
    rows = payload["rows"]
    if not isinstance(rows, list):
        raise ValueError("public payload rows must be a list")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("public payload rows must contain dict rows")
        for field_name in (
            "probability_before",
            "probability_after",
            "probability_change",
            "bid_ask_move",
            "forecast_revision",
            "confidence_change",
            "evidence_age_seconds",
        ):
            _require_optional_decimal_string(field_name, row.get(field_name))
    reason_counts = payload["reason_code_counts"]
    if not isinstance(reason_counts, list):
        raise ValueError("public payload reason_code_counts must be a list")
    for reason_count in reason_counts:
        if not isinstance(reason_count, dict):
            raise ValueError("public payload reason_code_counts must contain dict rows")
        _require_optional_decimal_string("market_count", reason_count.get("market_count"))


def _reject_public_payload_numbers(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_payload_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload_numbers(item)
        return
    if type(value) is bool:
        return
    if isinstance(value, (Decimal, float)) or type(value) is int:
        raise ValueError("public payload numeric values must be Decimal strings")


def _require_optional_decimal_string(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc


def _payload_required_string(payload: dict[str, object], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be present as a string")
    return value


def _reject_sensitive_value(field_name: str, value: str) -> None:
    lowered = value.lower()
    for forbidden in UNSAFE_PUBLIC_SURFACE_TERMS:
        if forbidden in lowered:
            raise ValueError(f"{field_name} contains a disallowed value")


def _decimal_string(value: Decimal) -> str:
    return format(value, "f")


def _count_decimal_string(value: Decimal) -> str:
    if value == value.to_integral_value():
        return format(value, ".0f")
    return _decimal_string(value)


def _optional_decimal_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_string(value)
