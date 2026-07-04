"""Pure Phase 1 crypto oracle outage-latency digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_CRYPTO_ORACLE_OUTAGE_LATENCY_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-oracle-outage-latency-digest-v0"
)

LATENCY_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "crypto_oracle_outage_latency_high_latency",
    "crypto_oracle_outage_latency_missed_heartbeat",
    "crypto_oracle_outage_latency_stale_price",
    "crypto_oracle_outage_latency_quorum_gap",
    "crypto_oracle_outage_latency_confidence_pressure",
    "crypto_oracle_outage_latency_inline",
    "crypto_oracle_outage_latency_watch_latency",
    "crypto_oracle_outage_latency_watch_missed_heartbeat",
    "crypto_oracle_outage_latency_watch_stale_price",
    "crypto_oracle_outage_latency_watch_quorum_gap",
    "crypto_oracle_outage_latency_watch_confidence_pressure",
)
REPORT_REASON_CODES = (
    "crypto_oracle_outage_latency_high_latency_present",
    "crypto_oracle_outage_latency_missed_heartbeat_present",
    "crypto_oracle_outage_latency_stale_price_present",
    "crypto_oracle_outage_latency_quorum_gap_present",
    "crypto_oracle_outage_latency_confidence_pressure_present",
    "crypto_oracle_outage_latency_digest_clear",
    "crypto_oracle_outage_latency_digest_empty",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_OUTAGE_RISK_SCORE = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_CRYPTO_ORACLE_OUTAGE_LATENCY_DIGEST_CONFIG_VERSION",
    "CryptoOracleOutageLatencyDigestConfig",
    "CryptoOracleOutageLatencyObservation",
    "CryptoOracleOutageLatencyDigestRow",
    "CryptoOracleOutageLatencyReasonCodeCount",
    "CryptoOracleOutageLatencyDigestReport",
    "build_market_research_crypto_oracle_outage_latency_digest",
    "market_research_crypto_oracle_outage_latency_digest_payload",
)


@dataclass(frozen=True)
class CryptoOracleOutageLatencyDigestConfig:
    config_version: str = DEFAULT_CRYPTO_ORACLE_OUTAGE_LATENCY_DIGEST_CONFIG_VERSION
    watch_update_latency_seconds: Decimal = Decimal("90.000000")
    blocked_update_latency_seconds: Decimal = Decimal("300.000000")
    watch_stale_price_age_seconds: Decimal = Decimal("180.000000")
    blocked_stale_price_age_seconds: Decimal = Decimal("600.000000")
    watch_missed_heartbeat_count: Decimal = Decimal("2.000000")
    blocked_missed_heartbeat_count: Decimal = Decimal("5.000000")
    watch_source_quorum_gap: Decimal = Decimal("1.000000")
    blocked_source_quorum_gap: Decimal = Decimal("2.000000")
    watch_confidence_score: Decimal = Decimal("0.750000")
    blocked_confidence_score: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoOracleOutageLatencyDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CRYPTO_ORACLE_OUTAGE_LATENCY_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_update_latency_seconds",
            "blocked_update_latency_seconds",
            "watch_stale_price_age_seconds",
            "blocked_stale_price_age_seconds",
            "watch_missed_heartbeat_count",
            "blocked_missed_heartbeat_count",
            "watch_source_quorum_gap",
            "blocked_source_quorum_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_confidence_score", "blocked_confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_update_latency_seconds > self.blocked_update_latency_seconds:
            raise ValueError(
                "watch_update_latency_seconds must not exceed "
                "blocked_update_latency_seconds",
            )
        if self.watch_stale_price_age_seconds > self.blocked_stale_price_age_seconds:
            raise ValueError(
                "watch_stale_price_age_seconds must not exceed "
                "blocked_stale_price_age_seconds",
            )
        if self.watch_missed_heartbeat_count > self.blocked_missed_heartbeat_count:
            raise ValueError(
                "watch_missed_heartbeat_count must not exceed "
                "blocked_missed_heartbeat_count",
            )
        if self.watch_source_quorum_gap > self.blocked_source_quorum_gap:
            raise ValueError(
                "watch_source_quorum_gap must not exceed blocked_source_quorum_gap",
            )
        if self.blocked_confidence_score > self.watch_confidence_score:
            raise ValueError(
                "blocked_confidence_score must not exceed watch_confidence_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class CryptoOracleOutageLatencyObservation:
    source_id: str
    oracle_name: str
    asset_symbol: str
    market_slug: str
    update_latency_seconds: Decimal
    missed_heartbeat_count: Decimal
    stale_price_age_seconds: Decimal
    expected_source_count: Decimal
    observed_source_count: Decimal
    confidence_score: Decimal
    data_timestamp: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoOracleOutageLatencyObservation, "observation")
        for field_name in ("source_id", "oracle_name", "asset_symbol", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "update_latency_seconds",
            "missed_heartbeat_count",
            "stale_price_age_seconds",
            "expected_source_count",
            "observed_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio("confidence_score", self.confidence_score),
        )
        _validate_source_counts(self.expected_source_count, self.observed_source_count)
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class CryptoOracleOutageLatencyDigestRow:
    source_id: str
    oracle_name: str
    asset_symbol: str
    market_slug: str
    update_latency_seconds: Decimal
    missed_heartbeat_count: Decimal
    stale_price_age_seconds: Decimal
    expected_source_count: Decimal
    observed_source_count: Decimal
    source_quorum_gap: Decimal
    confidence_score: Decimal
    confidence_pressure: Decimal
    data_timestamp: datetime
    latency_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoOracleOutageLatencyDigestRow, "row")
        for field_name in ("source_id", "oracle_name", "asset_symbol", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "update_latency_seconds",
            "missed_heartbeat_count",
            "stale_price_age_seconds",
            "expected_source_count",
            "observed_source_count",
            "source_quorum_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("confidence_score", "confidence_pressure"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _validate_source_counts(self.expected_source_count, self.observed_source_count)
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        _require_member("latency_status", self.latency_status, LATENCY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class CryptoOracleOutageLatencyReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            CryptoOracleOutageLatencyReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class CryptoOracleOutageLatencyDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    high_latency_count: Decimal
    missed_heartbeat_row_count: Decimal
    stale_price_count: Decimal
    quorum_gap_count: Decimal
    confidence_pressure_count: Decimal
    max_update_latency_seconds: Decimal
    average_update_latency_seconds: Decimal
    max_stale_price_age_seconds: Decimal
    max_source_quorum_gap: Decimal
    max_confidence_pressure: Decimal
    outage_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[CryptoOracleOutageLatencyDigestRow, ...]
    reason_code_counts: tuple[CryptoOracleOutageLatencyReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoOracleOutageLatencyDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CRYPTO_ORACLE_OUTAGE_LATENCY_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "high_latency_count",
            "missed_heartbeat_row_count",
            "stale_price_count",
            "quorum_gap_count",
            "confidence_pressure_count",
            "max_update_latency_seconds",
            "average_update_latency_seconds",
            "max_stale_price_age_seconds",
            "max_source_quorum_gap",
            "max_confidence_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "outage_risk_score",
            _require_ratio("outage_risk_score", self.outage_risk_score),
        )
        _require_member("digest_status", self.digest_status, LATENCY_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_crypto_oracle_outage_latency_digest(
    observations: Iterable[CryptoOracleOutageLatencyObservation],
    *,
    config: CryptoOracleOutageLatencyDigestConfig,
    generated_at: datetime,
) -> CryptoOracleOutageLatencyDigestReport:
    if type(config) is not CryptoOracleOutageLatencyDigestConfig:
        raise ValueError("config must be exactly CryptoOracleOutageLatencyDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (_row_from_observation(observation, config=config) for observation in normalized),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)

    return CryptoOracleOutageLatencyDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        high_latency_count=_reason_count(
            rows,
            "crypto_oracle_outage_latency_high_latency",
        ),
        missed_heartbeat_row_count=_reason_count(
            rows,
            "crypto_oracle_outage_latency_missed_heartbeat",
        ),
        stale_price_count=_reason_count(
            rows,
            "crypto_oracle_outage_latency_stale_price",
        ),
        quorum_gap_count=_reason_count(rows, "crypto_oracle_outage_latency_quorum_gap"),
        confidence_pressure_count=_reason_count(
            rows,
            "crypto_oracle_outage_latency_confidence_pressure",
        ),
        max_update_latency_seconds=_max_row_decimal(rows, "update_latency_seconds"),
        average_update_latency_seconds=_ratio(
            _sum_decimal(row.update_latency_seconds for row in rows),
            row_count,
        ),
        max_stale_price_age_seconds=_max_row_decimal(rows, "stale_price_age_seconds"),
        max_source_quorum_gap=_max_row_decimal(rows, "source_quorum_gap"),
        max_confidence_pressure=_max_row_decimal(rows, "confidence_pressure"),
        outage_risk_score=_outage_risk_score(rows),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_crypto_oracle_outage_latency_digest_payload(
    report: CryptoOracleOutageLatencyDigestReport,
) -> dict[str, Any]:
    if type(report) is not CryptoOracleOutageLatencyDigestReport:
        raise ValueError("report must be exactly CryptoOracleOutageLatencyDigestReport")
    return _payload_value(report)


def _row_from_observation(
    observation: CryptoOracleOutageLatencyObservation,
    *,
    config: CryptoOracleOutageLatencyDigestConfig,
) -> CryptoOracleOutageLatencyDigestRow:
    source_quorum_gap = _quantize_decimal(
        observation.expected_source_count - observation.observed_source_count,
    )
    confidence_pressure = _quantize_decimal(ONE - observation.confidence_score)
    latency_status = _latency_status(
        observation,
        source_quorum_gap=source_quorum_gap,
        config=config,
    )
    return CryptoOracleOutageLatencyDigestRow(
        source_id=observation.source_id,
        oracle_name=observation.oracle_name,
        asset_symbol=observation.asset_symbol,
        market_slug=observation.market_slug,
        update_latency_seconds=observation.update_latency_seconds,
        missed_heartbeat_count=observation.missed_heartbeat_count,
        stale_price_age_seconds=observation.stale_price_age_seconds,
        expected_source_count=observation.expected_source_count,
        observed_source_count=observation.observed_source_count,
        source_quorum_gap=source_quorum_gap,
        confidence_score=observation.confidence_score,
        confidence_pressure=confidence_pressure,
        data_timestamp=observation.data_timestamp,
        latency_status=latency_status,
        reason_codes=_row_reason_codes(
            observation,
            source_quorum_gap=source_quorum_gap,
            latency_status=latency_status,
            config=config,
        ),
    )


def _latency_status(
    observation: CryptoOracleOutageLatencyObservation,
    *,
    source_quorum_gap: Decimal,
    config: CryptoOracleOutageLatencyDigestConfig,
) -> str:
    if (
        observation.update_latency_seconds >= config.blocked_update_latency_seconds
        or observation.missed_heartbeat_count >= config.blocked_missed_heartbeat_count
        or observation.stale_price_age_seconds >= config.blocked_stale_price_age_seconds
        or source_quorum_gap >= config.blocked_source_quorum_gap
        or observation.confidence_score <= config.blocked_confidence_score
    ):
        return "blocked"
    if (
        observation.update_latency_seconds >= config.watch_update_latency_seconds
        or observation.missed_heartbeat_count >= config.watch_missed_heartbeat_count
        or observation.stale_price_age_seconds >= config.watch_stale_price_age_seconds
        or source_quorum_gap >= config.watch_source_quorum_gap
        or observation.confidence_score <= config.watch_confidence_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: CryptoOracleOutageLatencyObservation,
    *,
    source_quorum_gap: Decimal,
    latency_status: str,
    config: CryptoOracleOutageLatencyDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.update_latency_seconds >= config.blocked_update_latency_seconds:
        reason_codes.append("crypto_oracle_outage_latency_high_latency")
    elif observation.update_latency_seconds >= config.watch_update_latency_seconds:
        reason_codes.append("crypto_oracle_outage_latency_watch_latency")

    if observation.missed_heartbeat_count >= config.blocked_missed_heartbeat_count:
        reason_codes.append("crypto_oracle_outage_latency_missed_heartbeat")
    elif observation.missed_heartbeat_count >= config.watch_missed_heartbeat_count:
        reason_codes.append("crypto_oracle_outage_latency_watch_missed_heartbeat")

    if observation.stale_price_age_seconds >= config.blocked_stale_price_age_seconds:
        reason_codes.append("crypto_oracle_outage_latency_stale_price")
    elif observation.stale_price_age_seconds >= config.watch_stale_price_age_seconds:
        reason_codes.append("crypto_oracle_outage_latency_watch_stale_price")

    if source_quorum_gap >= config.blocked_source_quorum_gap:
        reason_codes.append("crypto_oracle_outage_latency_quorum_gap")
    elif source_quorum_gap >= config.watch_source_quorum_gap:
        reason_codes.append("crypto_oracle_outage_latency_watch_quorum_gap")

    if observation.confidence_score <= config.blocked_confidence_score:
        reason_codes.append("crypto_oracle_outage_latency_confidence_pressure")
    elif observation.confidence_score <= config.watch_confidence_score:
        reason_codes.append("crypto_oracle_outage_latency_watch_confidence_pressure")

    if latency_status == "pass" and not reason_codes:
        reason_codes.append("crypto_oracle_outage_latency_inline")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[CryptoOracleOutageLatencyDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("crypto_oracle_outage_latency_digest_empty",)
    reason_codes: list[str] = []
    if _reason_count(rows, "crypto_oracle_outage_latency_high_latency") > ZERO:
        reason_codes.append("crypto_oracle_outage_latency_high_latency_present")
    if _reason_count(rows, "crypto_oracle_outage_latency_missed_heartbeat") > ZERO:
        reason_codes.append("crypto_oracle_outage_latency_missed_heartbeat_present")
    if _reason_count(rows, "crypto_oracle_outage_latency_stale_price") > ZERO:
        reason_codes.append("crypto_oracle_outage_latency_stale_price_present")
    if _reason_count(rows, "crypto_oracle_outage_latency_quorum_gap") > ZERO:
        reason_codes.append("crypto_oracle_outage_latency_quorum_gap_present")
    if _reason_count(rows, "crypto_oracle_outage_latency_confidence_pressure") > ZERO:
        reason_codes.append("crypto_oracle_outage_latency_confidence_pressure_present")
    if not reason_codes:
        reason_codes.append("crypto_oracle_outage_latency_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[CryptoOracleOutageLatencyDigestRow, ...],
) -> tuple[CryptoOracleOutageLatencyReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("crypto_oracle_outage_latency_digest_empty",):
        return (
            CryptoOracleOutageLatencyReasonCodeCount(
                reason_code="crypto_oracle_outage_latency_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        CryptoOracleOutageLatencyReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[CryptoOracleOutageLatencyDigestRow, ...],
) -> Decimal:
    row_reason_code = {
        "crypto_oracle_outage_latency_high_latency_present": (
            "crypto_oracle_outage_latency_high_latency"
        ),
        "crypto_oracle_outage_latency_missed_heartbeat_present": (
            "crypto_oracle_outage_latency_missed_heartbeat"
        ),
        "crypto_oracle_outage_latency_stale_price_present": (
            "crypto_oracle_outage_latency_stale_price"
        ),
        "crypto_oracle_outage_latency_quorum_gap_present": (
            "crypto_oracle_outage_latency_quorum_gap"
        ),
        "crypto_oracle_outage_latency_confidence_pressure_present": (
            "crypto_oracle_outage_latency_confidence_pressure"
        ),
        "crypto_oracle_outage_latency_digest_clear": (
            "crypto_oracle_outage_latency_inline"
        ),
    }[reason_code]
    return _reason_count(rows, row_reason_code)


def _digest_status(rows: tuple[CryptoOracleOutageLatencyDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.latency_status == "blocked" for row in rows):
        return "blocked"
    if any(row.latency_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_crypto_oracle_outage_latency_screening"
    if status == "watch":
        return "monitor_report_only_crypto_oracle_outage_latency_screening"
    return "block_report_only_crypto_oracle_outage_latency_screening"


def _outage_risk_score(rows: tuple[CryptoOracleOutageLatencyDigestRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    digest_status = _digest_status(rows)
    if digest_status == "blocked":
        return ONE
    if digest_status == "watch":
        return WATCH_OUTAGE_RISK_SCORE
    return ZERO


def _validate_row(row: CryptoOracleOutageLatencyDigestRow) -> None:
    if row.source_quorum_gap != _quantize_decimal(
        row.expected_source_count - row.observed_source_count,
    ):
        raise ValueError("source_quorum_gap must match source counts")
    if row.confidence_pressure != _quantize_decimal(ONE - row.confidence_score):
        raise ValueError("confidence_pressure must match confidence_score")
    blocked_reasons = (
        "crypto_oracle_outage_latency_high_latency",
        "crypto_oracle_outage_latency_missed_heartbeat",
        "crypto_oracle_outage_latency_stale_price",
        "crypto_oracle_outage_latency_quorum_gap",
        "crypto_oracle_outage_latency_confidence_pressure",
    )
    watch_reasons = (
        "crypto_oracle_outage_latency_watch_latency",
        "crypto_oracle_outage_latency_watch_missed_heartbeat",
        "crypto_oracle_outage_latency_watch_stale_price",
        "crypto_oracle_outage_latency_watch_quorum_gap",
        "crypto_oracle_outage_latency_watch_confidence_pressure",
    )
    if row.latency_status == "pass":
        if row.reason_codes != ("crypto_oracle_outage_latency_inline",):
            raise ValueError("reason_codes must match latency_status")
        return
    if row.latency_status == "watch":
        if not any(reason in row.reason_codes for reason in watch_reasons):
            raise ValueError("reason_codes must match latency_status")
        if any(reason in row.reason_codes for reason in blocked_reasons):
            raise ValueError("reason_codes must match latency_status")
        return
    if not any(reason in row.reason_codes for reason in blocked_reasons):
        raise ValueError("reason_codes must match latency_status")


def _validate_report(report: CryptoOracleOutageLatencyDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.high_latency_count != _reason_count(
        report.rows,
        "crypto_oracle_outage_latency_high_latency",
    ):
        raise ValueError("high_latency_count must match rows")
    if report.missed_heartbeat_row_count != _reason_count(
        report.rows,
        "crypto_oracle_outage_latency_missed_heartbeat",
    ):
        raise ValueError("missed_heartbeat_row_count must match rows")
    if report.stale_price_count != _reason_count(
        report.rows,
        "crypto_oracle_outage_latency_stale_price",
    ):
        raise ValueError("stale_price_count must match rows")
    if report.quorum_gap_count != _reason_count(
        report.rows,
        "crypto_oracle_outage_latency_quorum_gap",
    ):
        raise ValueError("quorum_gap_count must match rows")
    if report.confidence_pressure_count != _reason_count(
        report.rows,
        "crypto_oracle_outage_latency_confidence_pressure",
    ):
        raise ValueError("confidence_pressure_count must match rows")
    if report.max_update_latency_seconds != _max_row_decimal(
        report.rows,
        "update_latency_seconds",
    ):
        raise ValueError("max_update_latency_seconds must match rows")
    if report.average_update_latency_seconds != _ratio(
        _sum_decimal(row.update_latency_seconds for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_update_latency_seconds must match rows")
    if report.max_stale_price_age_seconds != _max_row_decimal(
        report.rows,
        "stale_price_age_seconds",
    ):
        raise ValueError("max_stale_price_age_seconds must match rows")
    if report.max_source_quorum_gap != _max_row_decimal(report.rows, "source_quorum_gap"):
        raise ValueError("max_source_quorum_gap must match rows")
    if report.max_confidence_pressure != _max_row_decimal(
        report.rows,
        "confidence_pressure",
    ):
        raise ValueError("max_confidence_pressure must match rows")
    if report.outage_risk_score != _outage_risk_score(report.rows):
        raise ValueError("outage_risk_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[CryptoOracleOutageLatencyObservation],
) -> tuple[CryptoOracleOutageLatencyObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must contain CryptoOracleOutageLatencyObservation")
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not CryptoOracleOutageLatencyObservation:
            raise ValueError(
                "observations must contain CryptoOracleOutageLatencyObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[CryptoOracleOutageLatencyDigestRow],
) -> tuple[CryptoOracleOutageLatencyDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain CryptoOracleOutageLatencyDigestRow")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not CryptoOracleOutageLatencyDigestRow:
            raise ValueError("rows must contain CryptoOracleOutageLatencyDigestRow")
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[CryptoOracleOutageLatencyReasonCodeCount],
) -> tuple[CryptoOracleOutageLatencyReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not CryptoOracleOutageLatencyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain CryptoOracleOutageLatencyReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
    return tuple(
        sorted(normalized, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)),
    )


def _normalize_open_reason_codes(
    field_name: str,
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string("reason_code", value)
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(values)
    for value in normalized:
        _require_member("reason_code", value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized, key=lambda value: allowed.index(value)))


def _row_sort_key(
    row: CryptoOracleOutageLatencyDigestRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.latency_status],
        -row.update_latency_seconds,
        -row.stale_price_age_seconds,
        -row.source_quorum_gap,
        row.asset_symbol,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[CryptoOracleOutageLatencyDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.latency_status == status))


def _reason_count(
    rows: tuple[CryptoOracleOutageLatencyDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[CryptoOracleOutageLatencyDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _validate_source_counts(expected_source_count: Decimal, observed_source_count: Decimal) -> None:
    if observed_source_count > expected_source_count:
        raise ValueError("observed_source_count must not exceed expected_source_count")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
