"""Pure Phase 1 PMI surprise research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_PMI_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-pmi-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_pmi_surprise_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
STALE_SIGNAL_REASON = f"{REASON_PREFIX}stale_signal"
MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}material_surprise"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
HIGH_REVISION_REASON = f"{REASON_PREFIX}high_revision"
CONFIRMATION_GAP_REASON = f"{REASON_PREFIX}confirmation_gap"

ROW_REASON_CODE_SEQUENCE = (
    CONFIRMATION_GAP_REASON,
    HIGH_REVISION_REASON,
    MATERIAL_SURPRISE_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    MATERIAL_SURPRISE_REASON,
    CONFIRMATION_GAP_REASON,
    HIGH_REVISION_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_pmi_surprise_digest",
    STATUS_WATCH: "watch_report_only_market_research_pmi_surprise_digest",
    STATUS_BLOCKED: "block_report_only_market_research_pmi_surprise_digest",
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_PMI_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchPmiSurpriseDigestConfig",
    "MarketResearchPmiSurpriseDigestReasonCodeCount",
    "MarketResearchPmiSurpriseDigestReport",
    "MarketResearchPmiSurpriseDigestRow",
    "MarketResearchPmiSurpriseDigestSignal",
    "build_market_research_pmi_surprise_digest",
    "market_research_pmi_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPmiSurpriseDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_PMI_SURPRISE_DIGEST_CONFIG_VERSION
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    material_surprise_threshold: Decimal = Decimal("0.200000")
    max_revision_ratio: Decimal = Decimal("0.250000")
    min_confirmation_ratio: Decimal = Decimal("0.650000")
    stale_confidence_decay: Decimal = Decimal("0.200000")
    thin_source_confidence_decay: Decimal = Decimal("0.150000")
    revision_confidence_decay: Decimal = Decimal("0.100000")
    confirmation_confidence_decay: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPmiSurpriseDigestConfig:
            raise TypeError("MarketResearchPmiSurpriseDigestConfig does not support subclassing")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_MARKET_RESEARCH_PMI_SURPRISE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_signal_age_seconds",
            _require_positive_decimal("max_signal_age_seconds", self.max_signal_age_seconds),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        object.__setattr__(
            self,
            "material_surprise_threshold",
            _require_positive_decimal(
                "material_surprise_threshold",
                self.material_surprise_threshold,
            ),
        )
        for field_name in ("max_revision_ratio", "min_confirmation_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_confidence_decay",
            "thin_source_confidence_decay",
            "revision_confidence_decay",
            "confirmation_confidence_decay",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPmiSurpriseDigestSignal:
    condition_id: str
    research_key: str
    release_key: str
    pmi_family: str
    public_signal_reference: str
    observed_at: datetime
    expected_pmi: Decimal
    actual_pmi: Decimal
    surprise_score: Decimal
    source_count: Decimal
    revision_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPmiSurpriseDigestSignal:
            raise TypeError("MarketResearchPmiSurpriseDigestSignal does not support subclassing")
        for field_name in (
            "condition_id",
            "research_key",
            "release_key",
            "pmi_family",
            "public_signal_reference",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("expected_pmi", "actual_pmi"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "surprise_score",
            _require_nonnegative_decimal("surprise_score", self.surprise_score),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in ("revision_ratio", "confirmation_ratio", "base_confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchPmiSurpriseDigestRow:
    condition_id: str
    research_key: str
    release_key: str
    pmi_family: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    expected_pmi: Decimal
    actual_pmi: Decimal
    surprise_delta: Decimal
    surprise_score: Decimal
    source_count: Decimal
    revision_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    confidence_decay_factor: Decimal
    final_confidence: Decimal
    redacted_public_signal_reference: str
    signal_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPmiSurpriseDigestRow:
            raise TypeError("MarketResearchPmiSurpriseDigestRow does not support subclassing")
        for field_name in (
            "condition_id",
            "research_key",
            "release_key",
            "pmi_family",
            "redacted_public_signal_reference",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_digest_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("expected_pmi", "actual_pmi", "surprise_delta"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("signal_age_seconds", "surprise_score", "confidence_decay_factor"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "revision_ratio",
            "confirmation_ratio",
            "base_confidence",
            "final_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        if self.signal_age_seconds < ZERO:
            raise ValueError("signal_age_seconds must be nonnegative")
        if self.surprise_delta != _six(self.actual_pmi - self.expected_pmi):
            raise ValueError("surprise_delta must match PMI values")
        if self.final_confidence != _final_confidence(
            self.base_confidence,
            self.confidence_decay_factor,
        ):
            raise ValueError("final_confidence must match confidence decay")
        if self.digest_status != _row_status(self.reason_codes):
            raise ValueError("digest_status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPmiSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPmiSurpriseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPmiSurpriseDigestReasonCodeCount does not support subclassing",
            )
        _require_digest_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchPmiSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_signal_count: Decimal
    material_surprise_count: Decimal
    thin_source_count: Decimal
    high_revision_count: Decimal
    confirmation_gap_count: Decimal
    average_surprise_score: Decimal
    average_final_confidence: Decimal
    max_signal_age_seconds: Decimal
    min_source_count: Decimal
    material_surprise_threshold: Decimal
    max_revision_ratio: Decimal
    min_confirmation_ratio: Decimal
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchPmiSurpriseDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchPmiSurpriseDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPmiSurpriseDigestReport:
            raise TypeError("MarketResearchPmiSurpriseDigestReport does not support subclassing")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "signal_count",
            "ready_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "stale_signal_count",
            "material_surprise_count",
            "thin_source_count",
            "high_revision_count",
            "confirmation_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_surprise_score",
            "max_observed_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_final_confidence",
            _require_ratio_decimal("average_final_confidence", self.average_final_confidence),
        )
        object.__setattr__(
            self,
            "max_signal_age_seconds",
            _require_positive_decimal("max_signal_age_seconds", self.max_signal_age_seconds),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        object.__setattr__(
            self,
            "material_surprise_threshold",
            _require_positive_decimal(
                "material_surprise_threshold",
                self.material_surprise_threshold,
            ),
        )
        for field_name in ("max_revision_ratio", "min_confirmation_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "signal_config_versions",
            _normalize_signal_config_versions(self.signal_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODE_SEQUENCE),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_market_research_pmi_surprise_digest(
    signals: list[MarketResearchPmiSurpriseDigestSignal]
    | tuple[MarketResearchPmiSurpriseDigestSignal, ...],
    *,
    config: MarketResearchPmiSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchPmiSurpriseDigestReport:
    if type(config) is not MarketResearchPmiSurpriseDigestConfig:
        raise ValueError("config must be a MarketResearchPmiSurpriseDigestConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = _build_rows(normalized_signals, config=config, generated_at=generated_at_utc)
    signal_count = _decimal_count(len(rows))
    ready_signal_count = _status_count(rows, STATUS_READY)
    watch_signal_count = _status_count(rows, STATUS_WATCH)
    blocked_signal_count = _status_count(rows, STATUS_BLOCKED)
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchPmiSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    digest_status = _report_status(
        event_count=signal_count,
        watch_count=watch_signal_count,
        blocked_count=blocked_signal_count,
    )
    return MarketResearchPmiSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        signal_count=signal_count,
        ready_signal_count=ready_signal_count,
        watch_signal_count=watch_signal_count,
        blocked_signal_count=blocked_signal_count,
        stale_signal_count=_reason_signal_count(rows, STALE_SIGNAL_REASON),
        material_surprise_count=_reason_signal_count(rows, MATERIAL_SURPRISE_REASON),
        thin_source_count=_reason_signal_count(rows, THIN_SOURCES_REASON),
        high_revision_count=_reason_signal_count(rows, HIGH_REVISION_REASON),
        confirmation_gap_count=_reason_signal_count(rows, CONFIRMATION_GAP_REASON),
        average_surprise_score=_ratio(
            _sum_decimal(row.surprise_score for row in rows),
            signal_count,
        ),
        average_final_confidence=_ratio(
            _sum_decimal(row.final_confidence for row in rows),
            signal_count,
        ),
        max_signal_age_seconds=_six(config.max_signal_age_seconds),
        min_source_count=_six(config.min_source_count),
        material_surprise_threshold=_six(config.material_surprise_threshold),
        max_revision_ratio=_six(config.max_revision_ratio),
        min_confirmation_ratio=_six(config.min_confirmation_ratio),
        max_observed_signal_age_seconds=_max_decimal(row.signal_age_seconds for row in rows),
        rows=rows,
        signal_config_versions=_signal_config_versions(normalized_signals),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_pmi_surprise_digest_payload(
    report: MarketResearchPmiSurpriseDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketResearchPmiSurpriseDigestReport:
        raise ValueError("report must be a MarketResearchPmiSurpriseDigestReport")
    _require_hard_flags("report", report)
    return _payload_value(asdict(report))


def _normalize_signals(
    signals: list[MarketResearchPmiSurpriseDigestSignal]
    | tuple[MarketResearchPmiSurpriseDigestSignal, ...],
) -> tuple[MarketResearchPmiSurpriseDigestSignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    seen_release_keys: set[str] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchPmiSurpriseDigestSignal:
            raise ValueError("signals must contain MarketResearchPmiSurpriseDigestSignal")
        _require_hard_flags("signal", signal)
        if signal.release_key in seen_release_keys:
            raise ValueError("release_key values must be unique")
        seen_release_keys.add(signal.release_key)
    return normalized


def _build_rows(
    signals: tuple[MarketResearchPmiSurpriseDigestSignal, ...],
    *,
    config: MarketResearchPmiSurpriseDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchPmiSurpriseDigestRow, ...]:
    rows = []
    for signal in signals:
        signal_age = _age_seconds(generated_at, signal.observed_at)
        reason_codes = _row_reason_codes(signal, config=config, signal_age_seconds=signal_age)
        confidence_decay = _confidence_decay_factor(reason_codes, config)
        rows.append(
            MarketResearchPmiSurpriseDigestRow(
                condition_id=signal.condition_id,
                research_key=signal.research_key,
                release_key=signal.release_key,
                pmi_family=signal.pmi_family,
                digest_status=_row_status(reason_codes),
                observed_at=signal.observed_at,
                signal_age_seconds=signal_age,
                expected_pmi=_six(signal.expected_pmi),
                actual_pmi=_six(signal.actual_pmi),
                surprise_delta=_six(signal.actual_pmi - signal.expected_pmi),
                surprise_score=_six(signal.surprise_score),
                source_count=_six(signal.source_count),
                revision_ratio=_six(signal.revision_ratio),
                confirmation_ratio=_six(signal.confirmation_ratio),
                base_confidence=_six(signal.base_confidence),
                confidence_decay_factor=confidence_decay,
                final_confidence=_final_confidence(signal.base_confidence, confidence_decay),
                redacted_public_signal_reference=_redacted_public_reference(
                    signal.public_signal_reference,
                ),
                signal_config_version=signal.signal_config_version,
                reason_codes=reason_codes,
            ),
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (_status_rank(row.digest_status), row.release_key, row.condition_id),
        ),
    )


def _row_reason_codes(
    signal: MarketResearchPmiSurpriseDigestSignal,
    *,
    config: MarketResearchPmiSurpriseDigestConfig,
    signal_age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes = []
    if signal.confirmation_ratio < config.min_confirmation_ratio:
        reason_codes.append(CONFIRMATION_GAP_REASON)
    if signal.revision_ratio > config.max_revision_ratio:
        reason_codes.append(HIGH_REVISION_REASON)
    if signal.surprise_score >= config.material_surprise_threshold:
        reason_codes.append(MATERIAL_SURPRISE_REASON)
    if signal_age_seconds > config.max_signal_age_seconds:
        reason_codes.append(STALE_SIGNAL_REASON)
    if signal.source_count < config.min_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if not reason_codes:
        return (READY_REASON,)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if (
        STALE_SIGNAL_REASON in reason_codes
        or THIN_SOURCES_REASON in reason_codes
        or CONFIRMATION_GAP_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(*, event_count: Decimal, watch_count: Decimal, blocked_count: Decimal) -> str:
    if event_count == ZERO:
        return STATUS_BLOCKED
    if blocked_count > ZERO:
        return STATUS_BLOCKED
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _status_count(rows: tuple[MarketResearchPmiSurpriseDigestRow, ...], status: str) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_signal_count(
    rows: tuple[MarketResearchPmiSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchPmiSurpriseDigestRow, ...],
) -> tuple[MarketResearchPmiSurpriseDigestReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchPmiSurpriseDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            signal_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if (count := counts.get(reason_code, 0)) > 0
    )


def _signal_config_versions(
    signals: tuple[MarketResearchPmiSurpriseDigestSignal, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted((signal.release_key, signal.signal_config_version) for signal in signals),
    )


def _confidence_decay_factor(
    reason_codes: tuple[str, ...],
    config: MarketResearchPmiSurpriseDigestConfig,
) -> Decimal:
    decay = ZERO
    if STALE_SIGNAL_REASON in reason_codes:
        decay += config.stale_confidence_decay
    if THIN_SOURCES_REASON in reason_codes:
        decay += config.thin_source_confidence_decay
    if HIGH_REVISION_REASON in reason_codes:
        decay += config.revision_confidence_decay
    if CONFIRMATION_GAP_REASON in reason_codes:
        decay += config.confirmation_confidence_decay
    return _six(decay)


def _final_confidence(base_confidence: Decimal, confidence_decay: Decimal) -> Decimal:
    value = base_confidence - confidence_decay
    if value < ZERO:
        return ZERO
    return _six(value)


def _redacted_public_reference(value: str) -> str:
    if _must_redact(value):
        return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]
    return value


def _must_redact(value: str) -> bool:
    lowered = value.lower()
    hidden_fragments = (
        "://",
        "?",
        "=",
        *(
            "".join(chr(code) for code in codes)
            for codes in (
                (116, 111, 107, 101, 110),
                (115, 101, 99, 114, 101, 116),
                (97, 117, 116, 104),
            )
        ),
    )
    return any(fragment in lowered for fragment in hidden_fragments)


def _normalize_rows(
    rows: tuple[MarketResearchPmiSurpriseDigestRow, ...],
) -> tuple[MarketResearchPmiSurpriseDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_release_keys: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchPmiSurpriseDigestRow:
            raise ValueError("rows must contain MarketResearchPmiSurpriseDigestRow")
        _require_hard_flags("row", row)
        if row.release_key in seen_release_keys:
            raise ValueError("row release_key values must be unique")
        seen_release_keys.add(row.release_key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (_status_rank(row.digest_status), row.release_key, row.condition_id),
        ),
    )


def _normalize_signal_config_versions(
    versions: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(versions) is not tuple:
        raise ValueError("signal_config_versions must be a tuple")
    normalized = []
    seen_release_keys: set[str] = set()
    for item in versions:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("signal_config_versions must contain pairs")
        release_key, config_version = item
        _require_canonical_string("signal_config_versions release key", release_key)
        _require_canonical_string("signal_config_versions config version", config_version)
        if release_key in seen_release_keys:
            raise ValueError("signal_config_versions must contain unique release keys")
        seen_release_keys.add(release_key)
        normalized.append((release_key, config_version))
    return tuple(sorted(normalized))


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchPmiSurpriseDigestReasonCodeCount, ...],
) -> tuple[MarketResearchPmiSurpriseDigestReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_reason_codes: set[str] = set()
    for count in counts:
        if type(count) is not MarketResearchPmiSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MarketResearchPmiSurpriseDigestReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen_reason_codes.add(count.reason_code)
    return tuple(
        sorted(
            counts,
            key=lambda count: REPORT_REASON_CODE_SEQUENCE.index(count.reason_code),
        ),
    )


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    reason_code_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen_reason_codes: set[str] = set()
    normalized = []
    for reason_code in reason_codes:
        _require_digest_reason_code("reason_code", reason_code)
        if reason_code not in reason_code_sequence:
            raise ValueError("reason_code is not valid for this scope")
        if reason_code in seen_reason_codes:
            raise ValueError("reason_codes must be unique")
        seen_reason_codes.add(reason_code)
        normalized.append(reason_code)
    if (
        reason_code_sequence == ROW_REASON_CODE_SEQUENCE
        and READY_REASON in seen_reason_codes
        and len(seen_reason_codes) != 1
    ):
        raise ValueError("ready reason_code must be exclusive")
    if NO_INPUTS_REASON in seen_reason_codes and len(seen_reason_codes) != 1:
        raise ValueError("no_inputs reason_code must be exclusive")
    deterministic = tuple(
        reason_code
        for reason_code in reason_code_sequence
        if reason_code in seen_reason_codes
    )
    if tuple(normalized) != deterministic:
        raise ValueError("reason_codes must be deterministic")
    return tuple(normalized)


def _validate_report_consistency(report: MarketResearchPmiSurpriseDigestReport) -> None:
    signal_count = _decimal_count(len(report.rows))
    if report.signal_count != signal_count:
        raise ValueError("signal_count must match rows")
    expected_ready = _status_count(report.rows, STATUS_READY)
    expected_watch = _status_count(report.rows, STATUS_WATCH)
    expected_blocked = _status_count(report.rows, STATUS_BLOCKED)
    expected_counts = (
        ("ready_signal_count", expected_ready),
        ("watch_signal_count", expected_watch),
        ("blocked_signal_count", expected_blocked),
        ("stale_signal_count", _reason_signal_count(report.rows, STALE_SIGNAL_REASON)),
        (
            "material_surprise_count",
            _reason_signal_count(report.rows, MATERIAL_SURPRISE_REASON),
        ),
        ("thin_source_count", _reason_signal_count(report.rows, THIN_SOURCES_REASON)),
        ("high_revision_count", _reason_signal_count(report.rows, HIGH_REVISION_REASON)),
        (
            "confirmation_gap_count",
            _reason_signal_count(report.rows, CONFIRMATION_GAP_REASON),
        ),
    )
    for field_name, expected in expected_counts:
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.average_surprise_score != _ratio(
        _sum_decimal(row.surprise_score for row in report.rows),
        signal_count,
    ):
        raise ValueError("average_surprise_score must match rows")
    if report.average_final_confidence != _ratio(
        _sum_decimal(row.final_confidence for row in report.rows),
        signal_count,
    ):
        raise ValueError("average_final_confidence must match rows")
    if report.max_observed_signal_age_seconds != _max_decimal(
        (row.signal_age_seconds for row in report.rows),
    ):
        raise ValueError("max_observed_signal_age_seconds must match rows")
    if report.signal_config_versions != tuple(
        sorted((row.release_key, row.signal_config_version) for row in report.rows),
    ):
        raise ValueError("signal_config_versions must match rows")
    if report.reason_code_counts != _expected_reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.digest_status != _report_status(
        event_count=signal_count,
        watch_count=expected_watch,
        blocked_count=expected_blocked,
    ):
        raise ValueError("digest_status must match row statuses")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _expected_reason_code_counts(
    rows: tuple[MarketResearchPmiSurpriseDigestRow, ...],
) -> tuple[MarketResearchPmiSurpriseDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchPmiSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    return _reason_code_counts(rows)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be an aware datetime")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.total_seconds() < 0:
        raise ValueError("observed_at must not be in the future")
    return _six(Decimal(str(delta.total_seconds())))


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be non-empty canonical string")


def _require_digest_status(field_name: str, value: str) -> None:
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be one of {DIGEST_STATUSES}")


def _require_digest_reason_code(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in REPORT_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _six(value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value == ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value == ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_hard_flags(context: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{context} {field_name} must be True")


def _status_rank(status: str) -> int:
    return {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[status]


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _six(Decimal(value))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _six(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _six(numerator / denominator)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    return max(tuple(values), default=ZERO)


def _six(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _payload_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    return value
