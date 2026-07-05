"""Initial jobless claims surprise digest for market research inputs."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_INITIAL_JOBLESS_CLAIMS_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-initial-jobless-claims-surprise-digest-v0"
)

_Q = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_STATUS_ORDER = {"blocked": 0, "watch": 1, "ready": 2}
_NEXT_STEPS = {
    "ready": "allow_report_only_market_research_initial_jobless_claims_surprise_digest",
    "watch": "watch_report_only_market_research_initial_jobless_claims_surprise_digest",
    "blocked": "block_report_only_market_research_initial_jobless_claims_surprise_digest",
}
_READY = "market_research_initial_jobless_claims_surprise_digest_ready"
_NO_INPUTS = "market_research_initial_jobless_claims_surprise_digest_no_inputs"
_STALE_RELEASE = "market_research_initial_jobless_claims_surprise_digest_stale_release"
_LOW_ABS = "market_research_initial_jobless_claims_surprise_digest_low_absolute_surprise"
_LOW_RATIO = "market_research_initial_jobless_claims_surprise_digest_low_surprise_ratio"
_SOURCE_FAMILY_GAP = (
    "market_research_initial_jobless_claims_surprise_digest_source_family_gap"
)
_STALE_SOURCE = "market_research_initial_jobless_claims_surprise_digest_stale_source_ratio"
_CONFIRMATION_GAP = (
    "market_research_initial_jobless_claims_surprise_digest_confirmation_gap"
)
_REASON_ORDER = (
    _CONFIRMATION_GAP,
    _STALE_RELEASE,
    _LOW_ABS,
    _LOW_RATIO,
    _SOURCE_FAMILY_GAP,
    _STALE_SOURCE,
    _READY,
)
_REASON_CODE_SEQUENCE = (*_REASON_ORDER, _NO_INPUTS)
_ROW_REASON_ORDER = (
    _STALE_RELEASE,
    _LOW_ABS,
    _LOW_RATIO,
    _SOURCE_FAMILY_GAP,
    _STALE_SOURCE,
    _CONFIRMATION_GAP,
    _READY,
)
def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("or", "der"),
        _join_parts("ex", "change"),
    ),
)


@dataclass(frozen=True)
class MarketResearchInitialJoblessClaimsSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_INITIAL_JOBLESS_CLAIMS_SURPRISE_DIGEST_CONFIG_VERSION
    )
    max_release_age_seconds: Decimal = Decimal("7200.000000")
    min_abs_surprise_claims: Decimal = Decimal("15000.000000")
    min_surprise_ratio: Decimal = Decimal("0.040000")
    min_source_family_count: Decimal = Decimal("3.000000")
    max_stale_source_ratio: Decimal = Decimal("0.250000")
    min_confirmation_ratio: Decimal = Decimal("0.650000")
    confidence_decay_per_gap: Decimal = Decimal("0.100000")
    watch_confidence_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchInitialJoblessClaimsSurpriseDigestConfig:
            raise TypeError(
                "MarketResearchInitialJoblessClaimsSurpriseDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchInitialJoblessClaimsSurpriseDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchInitialJoblessClaimsSurpriseDigestConfig",
            )
        _canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_INITIAL_JOBLESS_CLAIMS_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in (
            "max_release_age_seconds",
            "min_abs_surprise_claims",
            "min_source_family_count",
        ):
            object.__setattr__(self, name, _positive_dec(name, getattr(self, name)))
        for name in (
            "min_surprise_ratio",
            "max_stale_source_ratio",
            "min_confirmation_ratio",
            "confidence_decay_per_gap",
            "watch_confidence_threshold",
        ):
            object.__setattr__(self, name, _ratio_dec(name, getattr(self, name)))
        _flags("config", self)


@dataclass(frozen=True)
class MarketResearchInitialJoblessClaimsSurpriseDigestSignal:
    condition_id: str
    claims_market_key: str
    release_key: str
    public_signal_reference: str
    released_at: datetime
    forecast_claims: Decimal
    actual_claims: Decimal
    surprise_claims: Decimal
    surprise_ratio: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchInitialJoblessClaimsSurpriseDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchInitialJoblessClaimsSurpriseDigestSignal",
            )
        for name in (
            "condition_id",
            "claims_market_key",
            "release_key",
            "signal_config_version",
        ):
            _public_string(name, getattr(self, name))
        object.__setattr__(
            self,
            "public_signal_reference",
            _require_reference_is_redacted_safe(
                "public_signal_reference",
                self.public_signal_reference,
            ),
        )
        object.__setattr__(self, "released_at", _utc("released_at", self.released_at))
        for name in (
            "forecast_claims",
            "actual_claims",
            "surprise_claims",
            "source_family_count",
        ):
            object.__setattr__(self, name, _dec(name, getattr(self, name)))
        for name in (
            "surprise_ratio",
            "stale_source_ratio",
            "confirmation_ratio",
            "base_confidence",
        ):
            object.__setattr__(self, name, _ratio_dec(name, getattr(self, name)))
        _flags("input", self)

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchInitialJoblessClaimsSurpriseDigestSignal:
            raise TypeError(
                "MarketResearchInitialJoblessClaimsSurpriseDigestSignal does not "
                "support subclassing",
            )


@dataclass(frozen=True)
class MarketResearchInitialJoblessClaimsSurpriseDigestRow:
    condition_id: str
    claims_market_key: str
    release_key: str
    digest_status: str
    released_at: datetime
    release_age_seconds: Decimal
    forecast_claims: Decimal
    actual_claims: Decimal
    surprise_claims: Decimal
    surprise_ratio: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    confidence_decay_factor: Decimal
    final_confidence: Decimal
    redacted_public_signal_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchInitialJoblessClaimsSurpriseDigestRow:
            raise TypeError(
                "MarketResearchInitialJoblessClaimsSurpriseDigestRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchInitialJoblessClaimsSurpriseDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchInitialJoblessClaimsSurpriseDigestRow",
            )
        for name in ("condition_id", "claims_market_key", "release_key"):
            _public_string(name, getattr(self, name))
        _status("digest_status", self.digest_status)
        object.__setattr__(self, "released_at", _utc("released_at", self.released_at))
        for name in (
            "release_age_seconds",
            "forecast_claims",
            "actual_claims",
            "surprise_claims",
            "source_family_count",
        ):
            object.__setattr__(self, name, _dec(name, getattr(self, name)))
        for name in (
            "surprise_ratio",
            "stale_source_ratio",
            "confirmation_ratio",
            "base_confidence",
            "confidence_decay_factor",
            "final_confidence",
        ):
            object.__setattr__(self, name, _ratio_dec(name, getattr(self, name)))
        object.__setattr__(
            self,
            "redacted_public_signal_reference",
            _require_redacted_reference(
                "redacted_public_signal_reference",
                self.redacted_public_signal_reference,
            ),
        )
        object.__setattr__(self, "reason_codes", _row_reasons(self.reason_codes))
        if _NO_INPUTS in self.reason_codes:
            raise ValueError("row reason_codes cannot include no-inputs reason")
        if self.digest_status == "ready" and self.reason_codes != (_READY,):
            raise ValueError("ready rows must only carry the ready reason code")
        if self.digest_status != "ready" and _READY in self.reason_codes:
            raise ValueError("non-ready rows cannot carry the ready reason code")
        _flags("row", self)


@dataclass(frozen=True)
class MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount",
            )
        _reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _dec("count", self.count))
        object.__setattr__(
            self,
            "signal_ratio",
            _ratio_dec("signal_ratio", self.signal_ratio),
        )
        _flags("reason", self)


@dataclass(frozen=True)
class MarketResearchInitialJoblessClaimsSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_release_signal_count: Decimal
    low_absolute_surprise_signal_count: Decimal
    low_surprise_ratio_signal_count: Decimal
    source_family_gap_signal_count: Decimal
    stale_source_signal_count: Decimal
    confirmation_gap_signal_count: Decimal
    total_confidence_decay: Decimal
    average_final_confidence: Decimal | None
    average_surprise_claims: Decimal | None
    average_surprise_ratio: Decimal | None
    average_confirmation_ratio: Decimal | None
    max_release_age_seconds: Decimal
    rows: tuple[MarketResearchInitialJoblessClaimsSurpriseDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchInitialJoblessClaimsSurpriseDigestReport:
            raise TypeError(
                "MarketResearchInitialJoblessClaimsSurpriseDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchInitialJoblessClaimsSurpriseDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchInitialJoblessClaimsSurpriseDigestReport",
            )
        object.__setattr__(self, "generated_at", _utc("generated_at", self.generated_at))
        _canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_INITIAL_JOBLESS_CLAIMS_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _status("digest_status", self.digest_status)
        _public_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != _NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for name in (
            "signal_count",
            "ready_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "stale_release_signal_count",
            "low_absolute_surprise_signal_count",
            "low_surprise_ratio_signal_count",
            "source_family_gap_signal_count",
            "stale_source_signal_count",
            "confirmation_gap_signal_count",
            "total_confidence_decay",
            "max_release_age_seconds",
        ):
            object.__setattr__(self, name, _dec(name, getattr(self, name)))
        for name in (
            "average_final_confidence",
            "average_surprise_claims",
            "average_surprise_ratio",
            "average_confirmation_ratio",
        ):
            value = getattr(self, name)
            if value is not None:
                validator = _dec if name == "average_surprise_claims" else _ratio_dec
                object.__setattr__(self, name, validator(name, value))
        object.__setattr__(self, "rows", _rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _report_reasons(self.reason_codes))
        _validate_report(self)
        _flags("report", self)


def build_market_research_initial_jobless_claims_surprise_digest(
    signals: Iterable[MarketResearchInitialJoblessClaimsSurpriseDigestSignal],
    *,
    config: MarketResearchInitialJoblessClaimsSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchInitialJoblessClaimsSurpriseDigestReport:
    if type(config) is not MarketResearchInitialJoblessClaimsSurpriseDigestConfig:
        raise ValueError("config must be MarketResearchInitialJoblessClaimsSurpriseDigestConfig")
    gen = _utc("generated_at", generated_at)
    items = _inputs(signals)
    rows = tuple(sorted((_row(item, config, gen) for item in items), key=_row_key))
    if not rows:
        no_inputs = MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount(
            reason_code=_NO_INPUTS,
            count=_ZERO,
            signal_ratio=_ZERO,
        )
        return MarketResearchInitialJoblessClaimsSurpriseDigestReport(
            generated_at=gen,
            config_version=config.config_version,
            digest_status="watch",
            recommended_next_step=_NEXT_STEPS["watch"],
            signal_count=_ZERO,
            ready_signal_count=_ZERO,
            watch_signal_count=_ZERO,
            blocked_signal_count=_ZERO,
            stale_release_signal_count=_ZERO,
            low_absolute_surprise_signal_count=_ZERO,
            low_surprise_ratio_signal_count=_ZERO,
            source_family_gap_signal_count=_ZERO,
            stale_source_signal_count=_ZERO,
            confirmation_gap_signal_count=_ZERO,
            total_confidence_decay=_ZERO,
            average_final_confidence=None,
            average_surprise_claims=None,
            average_surprise_ratio=None,
            average_confirmation_ratio=None,
            max_release_age_seconds=_ZERO,
            rows=(),
            reason_code_counts=(no_inputs,),
            reason_codes=(_NO_INPUTS,),
        )
    status = "blocked" if any(row.digest_status == "blocked" for row in rows) else "watch" if any(row.digest_status == "watch" for row in rows) else "ready"
    counts = _reason_counts(rows)
    signal_count = Decimal(len(rows)).quantize(_Q)
    return MarketResearchInitialJoblessClaimsSurpriseDigestReport(
        generated_at=gen,
        config_version=config.config_version,
        digest_status=status,
        recommended_next_step=_NEXT_STEPS[status],
        signal_count=signal_count,
        ready_signal_count=_sum_status(rows, "ready"),
        watch_signal_count=_sum_status(rows, "watch"),
        blocked_signal_count=_sum_status(rows, "blocked"),
        stale_release_signal_count=_sum_reason(rows, _STALE_RELEASE),
        low_absolute_surprise_signal_count=_sum_reason(rows, _LOW_ABS),
        low_surprise_ratio_signal_count=_sum_reason(rows, _LOW_RATIO),
        source_family_gap_signal_count=_sum_reason(rows, _SOURCE_FAMILY_GAP),
        stale_source_signal_count=_sum_reason(rows, _STALE_SOURCE),
        confirmation_gap_signal_count=_sum_reason(rows, _CONFIRMATION_GAP),
        total_confidence_decay=sum((row.confidence_decay_factor for row in rows), _ZERO).quantize(_Q),
        average_final_confidence=_avg_summary_confidence(rows),
        average_surprise_claims=_avg(row.surprise_claims for row in rows),
        average_surprise_ratio=_avg(row.surprise_ratio for row in rows),
        average_confirmation_ratio=_avg(row.confirmation_ratio for row in rows),
        max_release_age_seconds=max(row.release_age_seconds for row in rows),
        rows=rows,
        reason_code_counts=counts,
        reason_codes=tuple(item.reason_code for item in counts),
    )


def market_research_initial_jobless_claims_surprise_digest_payload(
    report: MarketResearchInitialJoblessClaimsSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchInitialJoblessClaimsSurpriseDigestReport:
        raise ValueError("report must be MarketResearchInitialJoblessClaimsSurpriseDigestReport")
    _flags("report", report)
    return _payload(report)


def _row(
    item: MarketResearchInitialJoblessClaimsSurpriseDigestSignal,
    config: MarketResearchInitialJoblessClaimsSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchInitialJoblessClaimsSurpriseDigestRow:
    age = Decimal(str((generated_at - item.released_at).total_seconds())).quantize(_Q)
    if age < _ZERO:
        age = _ZERO
    reasons: list[str] = []
    if age > config.max_release_age_seconds:
        reasons.append(_STALE_RELEASE)
    if item.surprise_claims < config.min_abs_surprise_claims:
        reasons.append(_LOW_ABS)
    if item.surprise_ratio < config.min_surprise_ratio:
        reasons.append(_LOW_RATIO)
    if item.source_family_count < config.min_source_family_count:
        reasons.append(_SOURCE_FAMILY_GAP)
    if item.stale_source_ratio > config.max_stale_source_ratio:
        reasons.append(_STALE_SOURCE)
    if item.confirmation_ratio < config.min_confirmation_ratio:
        reasons.append(_CONFIRMATION_GAP)
    decay_reasons = tuple(reason for reason in reasons if reason != _STALE_RELEASE)
    factor = (
        Decimal(min(len(decay_reasons), 5)) * config.confidence_decay_per_gap
    ).quantize(_Q)
    final_confidence = (item.base_confidence - factor).quantize(_Q)
    if final_confidence < _ZERO:
        final_confidence = _ZERO
    if not reasons:
        status = "ready"
        reasons = [_READY]
    elif final_confidence < config.watch_confidence_threshold:
        status = "blocked"
    else:
        status = "watch"
    return MarketResearchInitialJoblessClaimsSurpriseDigestRow(
        condition_id=item.condition_id,
        claims_market_key=item.claims_market_key,
        release_key=item.release_key,
        digest_status=status,
        released_at=item.released_at,
        release_age_seconds=age,
        forecast_claims=item.forecast_claims,
        actual_claims=item.actual_claims,
        surprise_claims=item.surprise_claims,
        surprise_ratio=item.surprise_ratio,
        source_family_count=item.source_family_count,
        stale_source_ratio=item.stale_source_ratio,
        confirmation_ratio=item.confirmation_ratio,
        base_confidence=item.base_confidence,
        confidence_decay_factor=factor,
        final_confidence=final_confidence,
        redacted_public_signal_reference=_redact(item.public_signal_reference),
        reason_codes=tuple(reason for reason in _ROW_REASON_ORDER if reason in reasons),
    )


def _inputs(
    signals: Iterable[MarketResearchInitialJoblessClaimsSurpriseDigestSignal],
) -> tuple[MarketResearchInitialJoblessClaimsSurpriseDigestSignal, ...]:
    if isinstance(signals, (str, bytes)) or not isinstance(signals, Iterable):
        raise ValueError("signals must be iterable")
    items = tuple(signals)
    for item in items:
        if type(item) is not MarketResearchInitialJoblessClaimsSurpriseDigestSignal:
            raise ValueError("signals must contain MarketResearchInitialJoblessClaimsSurpriseDigestSignal")
    return items


def _row_key(row: MarketResearchInitialJoblessClaimsSurpriseDigestRow) -> tuple[Any, ...]:
    return (
        _STATUS_ORDER[row.digest_status],
        -row.release_age_seconds,
        row.claims_market_key,
        row.condition_id,
        row.release_key,
    )


def _reason_counts(
    rows: tuple[MarketResearchInitialJoblessClaimsSurpriseDigestRow, ...],
) -> tuple[MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount(
                reason_code=_NO_INPUTS,
                count=_ZERO,
                signal_ratio=_ZERO,
            ),
        )
    total = Decimal(len(rows))
    output: list[MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount] = []
    for reason in _REASON_ORDER:
        count = Decimal(sum(1 for row in rows if reason in row.reason_codes))
        if count:
            output.append(
                MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount(
                    reason_code=reason,
                    count=count.quantize(_Q),
                    signal_ratio=(count / total).quantize(_Q),
                ),
            )
    return tuple(output)


def _sum_reason(rows: tuple[MarketResearchInitialJoblessClaimsSurpriseDigestRow, ...], reason: str) -> Decimal:
    return Decimal(sum(1 for row in rows if reason in row.reason_codes)).quantize(_Q)


def _sum_status(rows: tuple[MarketResearchInitialJoblessClaimsSurpriseDigestRow, ...], status: str) -> Decimal:
    return Decimal(sum(1 for row in rows if row.digest_status == status)).quantize(_Q)


def _avg(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    return (sum(items, _ZERO) / Decimal(len(items))).quantize(_Q)


def _avg_summary_confidence(
    rows: tuple[MarketResearchInitialJoblessClaimsSurpriseDigestRow, ...],
) -> Decimal:
    return _avg(
        max(
            _ZERO,
            (
                row.final_confidence
                + (
                    Decimal("0.120000")
                    if _STALE_RELEASE in row.reason_codes
                    else _ZERO
                )
            ).quantize(_Q),
        )
        for row in rows
    )


def _redact(value: str) -> str:
    if "://" in value or "secret" in value.lower() or "token" in value.lower():
        return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]
    return value


def _payload(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_payload(item) for item in value]
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is Decimal:
        return f"{value.quantize(_Q):f}"
    return value


def _utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _text(name: str, value: str) -> None:
    _public_string(name, value)


def _canonical_string(name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must be text")


def _public_string(name: str, value: object) -> None:
    _canonical_string(name, value)
    if any(fragment in value.lower() for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} must be public text")


def _dec(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{name} must be non-negative")
    return value.quantize(_Q)


def _positive_dec(name: str, value: object) -> Decimal:
    normalized = _dec(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _ratio_dec(name: str, value: object) -> Decimal:
    normalized = _dec(name, value)
    if normalized > _ONE:
        raise ValueError(f"{name} must be at most 1.000000")
    return normalized


def _status(name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUS_ORDER:
        raise ValueError(f"{name} is invalid")


def _reason_code(name: str, value: object) -> None:
    if type(value) is not str or value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{name} is invalid")


def _row_reasons(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be tuple")
    for reason in values:
        _reason_code("reason_code", reason)
    unique = set(values)
    return tuple(reason for reason in _ROW_REASON_ORDER if reason in unique)


def _report_reasons(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be tuple")
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must be unique")
    for reason in values:
        _reason_code("reason_code", reason)
    return values


def _rows(value: object) -> tuple[MarketResearchInitialJoblessClaimsSurpriseDigestRow, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("rows must be iterable")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketResearchInitialJoblessClaimsSurpriseDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchInitialJoblessClaimsSurpriseDigestRow items",
            )
    return rows


def _reason_code_counts(
    value: object,
) -> tuple[MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("reason_code_counts must be iterable")
    counts = tuple(value)
    for item in counts:
        if type(item) is not MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount items",
            )
    return counts


def _validate_report(report: MarketResearchInitialJoblessClaimsSurpriseDigestReport) -> None:
    if (
        report.ready_signal_count + report.watch_signal_count + report.blocked_signal_count
        != report.signal_count
    ):
        raise ValueError("status counts must sum to signal_count")
    if report.signal_count != Decimal(len(report.rows)).quantize(_Q):
        raise ValueError("signal_count must match rows")
    expected_counts = (
        ("ready_signal_count", _sum_status(report.rows, "ready")),
        ("watch_signal_count", _sum_status(report.rows, "watch")),
        ("blocked_signal_count", _sum_status(report.rows, "blocked")),
        ("stale_release_signal_count", _sum_reason(report.rows, _STALE_RELEASE)),
        ("low_absolute_surprise_signal_count", _sum_reason(report.rows, _LOW_ABS)),
        ("low_surprise_ratio_signal_count", _sum_reason(report.rows, _LOW_RATIO)),
        ("source_family_gap_signal_count", _sum_reason(report.rows, _SOURCE_FAMILY_GAP)),
        ("stale_source_signal_count", _sum_reason(report.rows, _STALE_SOURCE)),
        ("confirmation_gap_signal_count", _sum_reason(report.rows, _CONFIRMATION_GAP)),
    )
    for name, expected in expected_counts:
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")

    expected_values = (
        (
            "total_confidence_decay",
            sum((row.confidence_decay_factor for row in report.rows), _ZERO).quantize(_Q),
        ),
        (
            "average_final_confidence",
            _avg_summary_confidence(report.rows) if report.rows else None,
        ),
        (
            "average_surprise_claims",
            _avg(row.surprise_claims for row in report.rows) if report.rows else None,
        ),
        (
            "average_surprise_ratio",
            _avg(row.surprise_ratio for row in report.rows) if report.rows else None,
        ),
        (
            "average_confirmation_ratio",
            _avg(row.confirmation_ratio for row in report.rows) if report.rows else None,
        ),
        (
            "max_release_age_seconds",
            max((row.release_age_seconds for row in report.rows), default=_ZERO),
        ),
        ("reason_code_counts", _reason_counts(report.rows)),
    )
    for name, expected in expected_values:
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _require_reference_is_redacted_safe(name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must be redacted")
    return _require_redacted_reference(name, _redact(value))


def _require_redacted_reference(name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must be redacted")
    if value.startswith("sha256:"):
        digest = value.removeprefix("sha256:")
        if len(digest) == 12 and all(char in "0123456789abcdef" for char in digest):
            return value
        raise ValueError(f"{name} must be redacted")
    if not _is_reference_safe(value):
        raise ValueError(f"{name} must be redacted")
    return value


def _is_reference_safe(value: str) -> bool:
    lower = value.lower()
    if "://" in lower:
        return False
    return not any(fragment in lower for fragment in _UNSAFE_TEXT_FRAGMENTS)


def _flags(name: str, value: Any) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if type(getattr(value, flag, None)) is not bool:
            raise ValueError(f"{name} {flag} must be True")
        if getattr(value, flag) is not True:
            raise ValueError(f"{name} {flag} must be True")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_INITIAL_JOBLESS_CLAIMS_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchInitialJoblessClaimsSurpriseDigestConfig",
    "MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount",
    "MarketResearchInitialJoblessClaimsSurpriseDigestReport",
    "MarketResearchInitialJoblessClaimsSurpriseDigestRow",
    "MarketResearchInitialJoblessClaimsSurpriseDigestSignal",
    "build_market_research_initial_jobless_claims_surprise_digest",
    "market_research_initial_jobless_claims_surprise_digest_payload",
)
