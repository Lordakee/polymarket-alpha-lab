"""Pure crypto validator exit digest."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_VALIDATOR_EXIT_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-validator-exit-digest-v0"
)

CLEAR_REASON = "market_research_crypto_validator_exit_clear"
EMPTY_REASON = "market_research_crypto_validator_exit_empty"
CONFIRMED_REASON = "market_research_crypto_validator_exit_confirmed"
STATUS_CONFLICT_REASON = "market_research_crypto_validator_exit_status_conflict"
PENDING_STALE_REASON = "market_research_crypto_validator_exit_pending_stale"
SOURCE_GAP_REASON = "market_research_crypto_validator_exit_source_gap"
UNKNOWN_STATUS_REASON = "market_research_crypto_validator_exit_unknown_status"

REASON_CODES = (
    CLEAR_REASON,
    EMPTY_REASON,
    CONFIRMED_REASON,
    STATUS_CONFLICT_REASON,
    PENDING_STALE_REASON,
    SOURCE_GAP_REASON,
    UNKNOWN_STATUS_REASON,
)
SUMMARY_STATUSES = ("clear", "watch", "blocked")
EXIT_STATUSES = ("confirmed", "pending", "not_seen", "unknown")
NEXT_STEPS = {
    "clear": "allow_report_only_market_research_crypto_validator_exit",
    "watch": "refresh_report_only_market_research_crypto_validator_exit",
    "blocked": "block_report_only_market_research_crypto_validator_exit",
}

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUS_RANK = {"blocked": 0, "watch": 1, "clear": 2}
REASON_RANK = {
    CONFIRMED_REASON: 0,
    STATUS_CONFLICT_REASON: 1,
    PENDING_STALE_REASON: 2,
    SOURCE_GAP_REASON: 3,
    UNKNOWN_STATUS_REASON: 4,
    CLEAR_REASON: 5,
    EMPTY_REASON: 6,
}

__all__ = (
    "MarketResearchCryptoValidatorExitDigestConfig",
    "MarketResearchCryptoValidatorExitDigestReport",
    "MarketResearchCryptoValidatorExitDigestReasonCodeCount",
    "MarketResearchCryptoValidatorExitDigestRow",
    "MarketResearchCryptoValidatorExitDigestSource",
    "build_market_research_crypto_validator_exit_digest",
    "market_research_crypto_validator_exit_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoValidatorExitDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_CRYPTO_VALIDATOR_EXIT_DIGEST_CONFIG_VERSION
    min_validator_source_count: Decimal = Decimal("2.000000")
    min_confirmed_exit_ratio: Decimal = Decimal("0.600000")
    max_unconfirmed_exit_age_seconds: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoValidatorExitDigestConfig:
            raise TypeError(
                "MarketResearchCryptoValidatorExitDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchCryptoValidatorExitDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_validator_source_count",
            _require_positive_decimal(
                "min_validator_source_count",
                self.min_validator_source_count,
            ),
        )
        object.__setattr__(
            self,
            "min_confirmed_exit_ratio",
            _require_decimal_ratio("min_confirmed_exit_ratio", self.min_confirmed_exit_ratio),
        )
        object.__setattr__(
            self,
            "max_unconfirmed_exit_age_seconds",
            _require_positive_decimal(
                "max_unconfirmed_exit_age_seconds",
                self.max_unconfirmed_exit_age_seconds,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoValidatorExitDigestSource:
    market_id: str
    chain_id: str
    validator_id: str
    source_ref: str
    observed_at: datetime
    exit_status: str
    source_confidence: Decimal
    source_config_version: str = DEFAULT_MARKET_RESEARCH_CRYPTO_VALIDATOR_EXIT_DIGEST_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoValidatorExitDigestSource:
            raise TypeError(
                "MarketResearchCryptoValidatorExitDigestSource does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchCryptoValidatorExitDigestSource,
            "source",
        )
        for field_name in ("market_id", "chain_id", "validator_id", "source_ref"):
            value = getattr(self, field_name)
            _require_canonical_string(field_name, value)
            _require_redacted_reference(field_name, value)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("exit_status", self.exit_status, EXIT_STATUSES)
        object.__setattr__(
            self,
            "source_confidence",
            _require_decimal_ratio("source_confidence", self.source_confidence),
        )
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_redacted_reference("source_config_version", self.source_config_version)
        _require_hard_flags("source", self)


@dataclass(frozen=True)
class MarketResearchCryptoValidatorExitDigestRow:
    market_id: str
    chain_id: str
    validator_id: str
    row_status: str
    source_count: Decimal
    confirming_source_count: Decimal
    pending_source_count: Decimal
    not_seen_source_count: Decimal
    unknown_source_count: Decimal
    confirmed_exit_ratio: Decimal
    latest_observed_at: datetime
    max_source_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoValidatorExitDigestRow:
            raise TypeError(
                "MarketResearchCryptoValidatorExitDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchCryptoValidatorExitDigestRow,
            "row",
        )
        for field_name in ("market_id", "chain_id", "validator_id"):
            value = getattr(self, field_name)
            _require_canonical_string(field_name, value)
            _require_redacted_reference(field_name, value)
        _require_member("row_status", self.row_status, SUMMARY_STATUSES)
        for field_name in (
            "source_count",
            "confirming_source_count",
            "pending_source_count",
            "not_seen_source_count",
            "unknown_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confirmed_exit_ratio",
            _require_decimal_ratio("confirmed_exit_ratio", self.confirmed_exit_ratio),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCryptoValidatorExitDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    validator_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoValidatorExitDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoValidatorExitDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchCryptoValidatorExitDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_decimal("count", self.count))
        object.__setattr__(
            self,
            "validator_ratio",
            _require_decimal_ratio("validator_ratio", self.validator_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchCryptoValidatorExitDigestReport:
    generated_at: datetime
    config_version: str
    summary_status: str
    recommended_next_step: str
    validator_count: Decimal
    clear_validator_count: Decimal
    watch_validator_count: Decimal
    blocked_validator_count: Decimal
    source_count: Decimal
    min_validator_source_count: Decimal
    min_confirmed_exit_ratio: Decimal
    max_unconfirmed_exit_age_seconds: Decimal
    confirmed_validator_count: Decimal
    confirmed_validator_ratio: Decimal | None
    max_observed_source_age_seconds: Decimal | None
    rows: tuple[MarketResearchCryptoValidatorExitDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchCryptoValidatorExitDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoValidatorExitDigestReport:
            raise TypeError(
                "MarketResearchCryptoValidatorExitDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchCryptoValidatorExitDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("summary_status", self.summary_status, SUMMARY_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "validator_count",
            "clear_validator_count",
            "watch_validator_count",
            "blocked_validator_count",
            "source_count",
            "min_validator_source_count",
            "confirmed_validator_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_validator_source_count <= ZERO:
            raise ValueError("min_validator_source_count must be positive")
        object.__setattr__(
            self,
            "min_confirmed_exit_ratio",
            _require_decimal_ratio("min_confirmed_exit_ratio", self.min_confirmed_exit_ratio),
        )
        object.__setattr__(
            self,
            "max_unconfirmed_exit_age_seconds",
            _require_positive_decimal(
                "max_unconfirmed_exit_age_seconds",
                self.max_unconfirmed_exit_age_seconds,
            ),
        )
        if self.confirmed_validator_ratio is not None:
            object.__setattr__(
                self,
                "confirmed_validator_ratio",
                _require_decimal_ratio(
                    "confirmed_validator_ratio",
                    self.confirmed_validator_ratio,
                ),
            )
        if self.max_observed_source_age_seconds is not None:
            object.__setattr__(
                self,
                "max_observed_source_age_seconds",
                _require_nonnegative_decimal(
                    "max_observed_source_age_seconds",
                    self.max_observed_source_age_seconds,
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
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchCryptoValidatorExitDigestConfig,
    MarketResearchCryptoValidatorExitDigestReasonCodeCount,
    MarketResearchCryptoValidatorExitDigestReport,
    MarketResearchCryptoValidatorExitDigestRow,
    MarketResearchCryptoValidatorExitDigestSource,
)


def build_market_research_crypto_validator_exit_digest(
    sources: object,
    *,
    config: MarketResearchCryptoValidatorExitDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoValidatorExitDigestReport:
    if type(config) is not MarketResearchCryptoValidatorExitDigestConfig:
        raise ValueError("config must be a MarketResearchCryptoValidatorExitDigestConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_sources = _normalize_sources(sources)
    for source in normalized_sources:
        if source.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
    rows = _build_rows(normalized_sources, config=config, generated_at=generated_at)
    reason_codes = _report_reason_codes(rows)
    summary_status = _summary_status(rows)
    validator_count = _decimal_count(len(rows))
    confirmed_validator_count = _decimal_count(
        sum(1 for row in rows if CONFIRMED_REASON in row.reason_codes),
    )
    return MarketResearchCryptoValidatorExitDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        summary_status=summary_status,
        recommended_next_step=NEXT_STEPS[summary_status],
        validator_count=validator_count,
        clear_validator_count=_decimal_count(_row_status_count(rows, "clear")),
        watch_validator_count=_decimal_count(_row_status_count(rows, "watch")),
        blocked_validator_count=_decimal_count(_row_status_count(rows, "blocked")),
        source_count=_decimal_count(len(normalized_sources)),
        min_validator_source_count=config.min_validator_source_count,
        min_confirmed_exit_ratio=config.min_confirmed_exit_ratio,
        max_unconfirmed_exit_age_seconds=config.max_unconfirmed_exit_age_seconds,
        confirmed_validator_count=confirmed_validator_count,
        confirmed_validator_ratio=(
            None if validator_count == ZERO else _ratio(confirmed_validator_count, validator_count)
        ),
        max_observed_source_age_seconds=_max_observed_source_age_seconds(rows),
        rows=rows,
        source_config_versions=_source_config_versions(normalized_sources),
        reason_code_counts=_reason_code_counts(rows, validator_count),
        reason_codes=reason_codes,
    )


def market_research_crypto_validator_exit_digest_payload(
    report: MarketResearchCryptoValidatorExitDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchCryptoValidatorExitDigestReport:
        raise ValueError("report must be a MarketResearchCryptoValidatorExitDigestReport")
    _require_payload_safe_value("report", report)
    _require_hard_flags("report", report)
    payload = _to_payload(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _build_rows(
    sources: tuple[MarketResearchCryptoValidatorExitDigestSource, ...],
    *,
    config: MarketResearchCryptoValidatorExitDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchCryptoValidatorExitDigestRow, ...]:
    grouped: dict[tuple[str, str, str], list[MarketResearchCryptoValidatorExitDigestSource]] = {}
    for source in sources:
        grouped.setdefault((source.market_id, source.chain_id, source.validator_id), []).append(
            source,
        )
    return tuple(
        sorted(
            (
                _build_row(
                    market_id=market_id,
                    chain_id=chain_id,
                    validator_id=validator_id,
                    sources=tuple(group_sources),
                    config=config,
                    generated_at=generated_at,
                )
                for (market_id, chain_id, validator_id), group_sources in grouped.items()
            ),
            key=_row_sort_key,
        ),
    )


def _build_row(
    *,
    market_id: str,
    chain_id: str,
    validator_id: str,
    sources: tuple[MarketResearchCryptoValidatorExitDigestSource, ...],
    config: MarketResearchCryptoValidatorExitDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoValidatorExitDigestRow:
    source_count = len(sources)
    confirming_count = sum(1 for source in sources if source.exit_status == "confirmed")
    pending_count = sum(1 for source in sources if source.exit_status == "pending")
    not_seen_count = sum(1 for source in sources if source.exit_status == "not_seen")
    unknown_count = sum(1 for source in sources if source.exit_status == "unknown")
    confirmed_ratio = _ratio(_decimal_count(confirming_count), _decimal_count(source_count))
    max_source_age_seconds = _decimal_count(
        max(int((generated_at - source.observed_at).total_seconds()) for source in sources),
    )
    reason_codes = _row_reason_codes(
        source_count=source_count,
        confirming_count=confirming_count,
        pending_count=pending_count,
        not_seen_count=not_seen_count,
        unknown_count=unknown_count,
        confirmed_ratio=confirmed_ratio,
        max_source_age_seconds=max_source_age_seconds,
        config=config,
    )
    return MarketResearchCryptoValidatorExitDigestRow(
        market_id=market_id,
        chain_id=chain_id,
        validator_id=validator_id,
        row_status=_row_status(reason_codes),
        source_count=_decimal_count(source_count),
        confirming_source_count=_decimal_count(confirming_count),
        pending_source_count=_decimal_count(pending_count),
        not_seen_source_count=_decimal_count(not_seen_count),
        unknown_source_count=_decimal_count(unknown_count),
        confirmed_exit_ratio=confirmed_ratio,
        latest_observed_at=max(source.observed_at for source in sources),
        max_source_age_seconds=max_source_age_seconds,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_count: int,
    confirming_count: int,
    pending_count: int,
    not_seen_count: int,
    unknown_count: int,
    confirmed_ratio: Decimal,
    max_source_age_seconds: Decimal,
    config: MarketResearchCryptoValidatorExitDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if confirming_count and confirmed_ratio >= config.min_confirmed_exit_ratio:
        reasons.append(CONFIRMED_REASON)
    if confirming_count and source_count > confirming_count:
        reasons.append(STATUS_CONFLICT_REASON)
    if pending_count and max_source_age_seconds > config.max_unconfirmed_exit_age_seconds:
        reasons.append(PENDING_STALE_REASON)
    if Decimal(source_count) < config.min_validator_source_count:
        reasons.append(SOURCE_GAP_REASON)
    if unknown_count:
        reasons.append(UNKNOWN_STATUS_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    if not_seen_count < 0:
        raise ValueError("not_seen_count must be nonnegative")
    return tuple(sorted(reasons, key=_reason_sort_key))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if CONFIRMED_REASON in reason_codes:
        return "blocked"
    if reason_codes == (CLEAR_REASON,):
        return "clear"
    return "watch"


def _summary_status(rows: tuple[MarketResearchCryptoValidatorExitDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[MarketResearchCryptoValidatorExitDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = sorted(
        {reason for row in rows for reason in row.reason_codes},
        key=_reason_sort_key,
    )
    if reasons == [CLEAR_REASON]:
        return (CLEAR_REASON,)
    return tuple(reason for reason in reasons if reason != CLEAR_REASON)


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoValidatorExitDigestRow, ...],
    validator_count: Decimal,
) -> tuple[MarketResearchCryptoValidatorExitDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchCryptoValidatorExitDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                validator_ratio=ZERO,
            ),
        )
    if validator_count == ZERO:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoValidatorExitDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            validator_ratio=_ratio(_decimal_count(count), validator_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], _reason_sort_key(item[0])),
        )
    )


def _source_config_versions(
    sources: tuple[MarketResearchCryptoValidatorExitDigestSource, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted({(source.source_ref, source.source_config_version) for source in sources}),
    )


def _max_observed_source_age_seconds(
    rows: tuple[MarketResearchCryptoValidatorExitDigestRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return max(row.max_source_age_seconds for row in rows)


def _normalize_sources(
    value: object,
) -> tuple[MarketResearchCryptoValidatorExitDigestSource, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("sources must be an iterable")
    try:
        sources = tuple(value)
    except TypeError as exc:
        raise ValueError("sources must be an iterable") from exc
    seen: set[tuple[str, str, str, str]] = set()
    for source in sources:
        if type(source) is not MarketResearchCryptoValidatorExitDigestSource:
            raise ValueError(
                "sources must contain MarketResearchCryptoValidatorExitDigestSource",
            )
        _require_hard_flags("source", source)
        key = (source.market_id, source.chain_id, source.validator_id, source.source_ref)
        if key in seen:
            raise ValueError(
                "sources must be unique by market_id, chain_id, validator_id, and source_ref",
            )
        seen.add(key)
    return sources


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchCryptoValidatorExitDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not MarketResearchCryptoValidatorExitDigestRow:
            raise ValueError("rows must contain MarketResearchCryptoValidatorExitDigestRow")
    expected = tuple(sorted(rows, key=_row_sort_key))
    if rows != expected:
        raise ValueError("rows must use deterministic sort")
    return rows


def _normalize_source_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("source_config_versions must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("source_config_versions must be an iterable") from exc
    normalized: list[tuple[str, str]] = []
    for item in items:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions entries must be pairs")
        source_ref, source_config_version = item
        _require_canonical_string("source_ref", source_ref)
        _require_redacted_reference("source_ref", source_ref)
        _require_canonical_string("source_config_version", source_config_version)
        _require_redacted_reference("source_config_version", source_config_version)
        normalized.append((source_ref, source_config_version))
    expected = tuple(sorted(set(normalized)))
    if tuple(normalized) != expected:
        raise ValueError("source_config_versions must be unique and deterministic")
    return tuple(normalized)


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchCryptoValidatorExitDigestReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in counts:
        if type(count) is not MarketResearchCryptoValidatorExitDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchCryptoValidatorExitDigestReasonCodeCount",
            )
    expected = tuple(
        sorted(counts, key=lambda item: (-item.count, _reason_sort_key(item.reason_code))),
    )
    if counts != expected:
        raise ValueError("reason_code_counts must use deterministic sort")
    return counts


def _validate_row_consistency(row: MarketResearchCryptoValidatorExitDigestRow) -> None:
    if row.row_status != _row_status(row.reason_codes):
        raise ValueError("row_status must match reason_codes")
    if (
        row.confirming_source_count
        + row.pending_source_count
        + row.not_seen_source_count
        + row.unknown_source_count
        != row.source_count
    ):
        raise ValueError("source status counts must match source_count")
    expected_ratio = _ratio(row.confirming_source_count, row.source_count)
    if row.confirmed_exit_ratio != expected_ratio:
        raise ValueError("confirmed_exit_ratio must match counts")


def _validate_report_consistency(
    report: MarketResearchCryptoValidatorExitDigestReport,
) -> None:
    if report.validator_count != _decimal_count(len(report.rows)):
        raise ValueError("validator_count must match rows")
    if (
        report.clear_validator_count
        + report.watch_validator_count
        + report.blocked_validator_count
        != report.validator_count
    ):
        raise ValueError("status counts must match validator_count")
    for status, count in (
        ("clear", report.clear_validator_count),
        ("watch", report.watch_validator_count),
        ("blocked", report.blocked_validator_count),
    ):
        if count != _decimal_count(_row_status_count(report.rows, status)):
            raise ValueError(f"{status}_validator_count must match rows")
    if report.source_count != sum((row.source_count for row in report.rows), ZERO):
        raise ValueError("source_count must match rows")
    expected_confirmed_count = _decimal_count(
        sum(1 for row in report.rows if CONFIRMED_REASON in row.reason_codes),
    )
    if report.confirmed_validator_count != expected_confirmed_count:
        raise ValueError("confirmed_validator_count must match rows")
    expected_ratio = (
        None
        if report.validator_count == ZERO
        else _ratio(report.confirmed_validator_count, report.validator_count)
    )
    if report.confirmed_validator_ratio != expected_ratio:
        raise ValueError("confirmed_validator_ratio must match counts")
    if report.max_observed_source_age_seconds != _max_observed_source_age_seconds(report.rows):
        raise ValueError("max_observed_source_age_seconds must match rows")
    if report.summary_status != _summary_status(report.rows):
        raise ValueError("summary_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.summary_status]:
        raise ValueError("recommended_next_step must match summary_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.validator_count):
        raise ValueError("reason_code_counts must match rows")


def _row_status_count(
    rows: tuple[MarketResearchCryptoValidatorExitDigestRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.row_status == status)


def _row_sort_key(row: MarketResearchCryptoValidatorExitDigestRow) -> tuple[int, str, str, str]:
    return (STATUS_RANK[row.row_status], row.market_id, row.chain_id, row.validator_id)


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    return (REASON_RANK.get(reason_code, len(REASON_RANK)), reason_code)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reasons = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for reason in reasons:
        _require_reason_code(field_name, reason)
    expected = tuple(sorted(set(reasons), key=_reason_sort_key))
    if reasons != expected:
        raise ValueError(f"{field_name} must be unique and deterministic")
    return reasons


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} is unknown")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} is invalid")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty trimmed string")


def _require_redacted_reference(field_name: str, value: str) -> None:
    lowered = value.lower()
    fragments = (
        "wal" + "let",
        "acc" + "ount",
        "tok" + "en",
        "sec" + "ret",
        "private" + "_" + "key",
        "0x",
    )
    if any(fragment in lowered for fragment in fragments):
        raise ValueError(f"{field_name} must be redacted")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone aware")
    return value.astimezone(UTC)


def _require_exact_type(
    value: object,
    expected_type: type[object],
    field_name: str,
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return value.quantize(QUANT, rounding=ROUND_HALF_UP)


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


def _require_decimal_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag) is not True:
            raise ValueError(f"{label} {flag} must be True")


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT, rounding=ROUND_HALF_UP)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(QUANT, rounding=ROUND_HALF_UP)


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if type(value) is Decimal:
        decimal_value = _require_decimal(field_name, value)
        if decimal_value != value or not value.same_quantum(QUANT):
            raise ValueError(f"{field_name} must be quantized to six decimals")
        return
    if type(value) is datetime:
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a supported public dataclass")
        _require_hard_flags(field_name, value)
        for field in fields(value):
            _require_payload_safe_value(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
            )
        _rebuild_public_dataclass(field_name, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) in (str, bool) or value is None:
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")
    raise ValueError(f"{field_name} must be safe for payload serialization")


def _rebuild_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid") from exc


def _to_payload(value: object) -> object:
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("value must be a supported public dataclass")
        return {field.name: _to_payload(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return tuple(_to_payload(item) for item in value)
    return value
