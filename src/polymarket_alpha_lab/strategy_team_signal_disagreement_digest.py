"""Pure report reducer for strategy team signal disagreement."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DEFAULT_SPREAD_LIMIT = Decimal("0.250000")
_DEFAULT_STALE_SECONDS = Decimal("172800.000000")
_DEFAULT_CONFIDENCE_GAP_LIMIT = Decimal("0.250000")
_REDACTED_SOURCE_REFERENCE = "<redacted-source-reference>"
_ROW_STATUS_RANK = {"blocked": 0, "watch": 1, "clear": 2}
_REASON_RANK = {
    "high_team_forecast_disagreement": 0,
    "stale_minority_team_view": 1,
    "consensus_confidence_gap": 2,
}
_ROW_REASON_CODES = tuple(_REASON_RANK) + ("team_signal_disagreement_clear",)
_REPORT_REASON_CODES = _ROW_REASON_CODES + ("empty_team_forecast_signals",)
_PUBLIC_TEXT_BLOCKLIST = (
    "d" "b",
    "data" "base",
    "net" "work",
    "re" "quest",
    "sock" "et",
    "li" "ve",
    "trad",
    "au" "th",
    "wal" "let",
    "bro" "ker",
    "or" "der",
    "can" "cel",
    "re" "place",
    "sign" "ing",
    "acc" "ount",
    "ad" "vice",
    "sec" "ret",
    "tok" "en",
    "pass" "word",
    "cred" "ential",
    "private" "_" "key",
    "api" "_" "key",
)


@dataclass(frozen=True)
class StrategyTeamForecastSignal:
    condition_id: str
    team_id: str
    forecast_probability: Decimal
    confidence: Decimal
    signaled_at: datetime
    source_reference: str = _REDACTED_SOURCE_REFERENCE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("condition_id", self.condition_id)
        _require_public_text("team_id", self.team_id)
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_ratio("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "confidence",
            _normalize_ratio("confidence", self.confidence),
        )
        object.__setattr__(self, "signaled_at", _as_utc("signaled_at", self.signaled_at))
        _require_text("source_reference", self.source_reference)
        object.__setattr__(self, "source_reference", _REDACTED_SOURCE_REFERENCE)
        _require_flags("signal", self)


@dataclass(frozen=True)
class StrategyTeamSignalDisagreementRow:
    condition_id: str
    row_status: str
    team_count: Decimal
    minimum_forecast_probability: Decimal
    maximum_forecast_probability: Decimal
    average_forecast_probability: Decimal
    consensus_probability: Decimal
    forecast_spread: Decimal
    consensus_confidence: Decimal
    minimum_confidence: Decimal
    consensus_confidence_gap: Decimal
    high_disagreement: bool
    stale_minority_view_count: Decimal
    latest_signaled_at: datetime
    source_references: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("condition_id", self.condition_id)
        _require_row_status("row_status", self.row_status)
        object.__setattr__(self, "team_count", _normalize_count("team_count", self.team_count))
        for name in (
            "minimum_forecast_probability",
            "maximum_forecast_probability",
            "average_forecast_probability",
            "consensus_probability",
            "forecast_spread",
            "consensus_confidence",
            "minimum_confidence",
            "consensus_confidence_gap",
        ):
            object.__setattr__(self, name, _normalize_ratio(name, getattr(self, name)))
        _require_bool("high_disagreement", self.high_disagreement)
        object.__setattr__(
            self,
            "stale_minority_view_count",
            _normalize_count("stale_minority_view_count", self.stale_minority_view_count),
        )
        object.__setattr__(
            self,
            "latest_signaled_at",
            _as_utc("latest_signaled_at", self.latest_signaled_at),
        )
        object.__setattr__(
            self,
            "source_references",
            _normalize_source_references(self.source_references),
        )
        object.__setattr__(self, "reason_codes", _normalize_row_reasons(self.reason_codes))
        _check_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class StrategyTeamSignalDisagreementReasonRollup:
    reason_code: str
    condition_count: Decimal
    condition_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code, tuple(_REASON_RANK))
        object.__setattr__(
            self,
            "condition_count",
            _normalize_count("condition_count", self.condition_count),
        )
        object.__setattr__(
            self,
            "condition_ratio",
            _normalize_ratio("condition_ratio", self.condition_ratio),
        )
        _require_flags("reason rollup", self)


@dataclass(frozen=True)
class StrategyTeamSignalDisagreementDigestReport:
    generated_at: datetime
    config_version: str
    condition_count: Decimal
    signal_count: Decimal
    clear_condition_count: Decimal
    watch_condition_count: Decimal
    blocked_condition_count: Decimal
    disagreement_condition_count: Decimal
    disagreement_condition_ratio: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyTeamSignalDisagreementRow, ...]
    reason_rollups: tuple[StrategyTeamSignalDisagreementReasonRollup, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for name in (
            "condition_count",
            "signal_count",
            "clear_condition_count",
            "watch_condition_count",
            "blocked_condition_count",
            "disagreement_condition_count",
        ):
            object.__setattr__(self, name, _normalize_count(name, getattr(self, name)))
        if self.disagreement_condition_ratio is not None:
            object.__setattr__(
                self,
                "disagreement_condition_ratio",
                _normalize_ratio(
                    "disagreement_condition_ratio",
                    self.disagreement_condition_ratio,
                ),
            )
        _require_row_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_report_reasons(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_rollups", _normalize_rollups(self.reason_rollups))
        _check_report(self)
        _require_flags("report", self)


def build_strategy_team_signal_disagreement_digest(
    *,
    generated_at: datetime,
    config_version: str,
    signals: object,
    disagreement_spread_limit: Decimal = _DEFAULT_SPREAD_LIMIT,
    stale_signal_seconds: Decimal = _DEFAULT_STALE_SECONDS,
    confidence_gap_limit: Decimal = _DEFAULT_CONFIDENCE_GAP_LIMIT,
) -> StrategyTeamSignalDisagreementDigestReport:
    generated_at = _as_utc("generated_at", generated_at)
    _require_public_text("config_version", config_version)
    disagreement_spread_limit = _normalize_ratio(
        "disagreement_spread_limit",
        disagreement_spread_limit,
    )
    stale_signal_seconds = _normalize_decimal("stale_signal_seconds", stale_signal_seconds)
    confidence_gap_limit = _normalize_ratio("confidence_gap_limit", confidence_gap_limit)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (
                _condition_row(
                    condition_id,
                    condition_signals,
                    generated_at=generated_at,
                    disagreement_spread_limit=disagreement_spread_limit,
                    stale_signal_seconds=stale_signal_seconds,
                    confidence_gap_limit=confidence_gap_limit,
                )
                for condition_id, condition_signals in _group_signals(normalized_signals)
            ),
            key=_row_key,
        ),
    )
    condition_count = _count(len(rows))
    disagreement_condition_count = _count(
        sum(1 for row in rows if row.reason_codes != ("team_signal_disagreement_clear",)),
    )

    return StrategyTeamSignalDisagreementDigestReport(
        generated_at=generated_at,
        config_version=config_version,
        condition_count=condition_count,
        signal_count=_count(len(normalized_signals)),
        clear_condition_count=_row_count(rows, "clear"),
        watch_condition_count=_row_count(rows, "watch"),
        blocked_condition_count=_row_count(rows, "blocked"),
        disagreement_condition_count=disagreement_condition_count,
        disagreement_condition_ratio=(
            None
            if condition_count == _ZERO
            else _ratio(disagreement_condition_count, condition_count)
        ),
        status=_report_status(rows),
        reason_codes=_report_reasons(rows),
        rows=rows,
        reason_rollups=_reason_rollups(rows, condition_count),
    )


def strategy_team_signal_disagreement_digest_payload(
    report: StrategyTeamSignalDisagreementDigestReport,
) -> dict[str, Any]:
    if type(report) is not StrategyTeamSignalDisagreementDigestReport:
        raise ValueError("report must be a StrategyTeamSignalDisagreementDigestReport")
    _require_flags("report", report)
    payload = _json_ready(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def _condition_row(
    condition_id: str,
    signals: tuple[StrategyTeamForecastSignal, ...],
    *,
    generated_at: datetime,
    disagreement_spread_limit: Decimal,
    stale_signal_seconds: Decimal,
    confidence_gap_limit: Decimal,
) -> StrategyTeamSignalDisagreementRow:
    probabilities = tuple(signal.forecast_probability for signal in signals)
    confidences = tuple(signal.confidence for signal in signals)
    minimum_probability = min(probabilities)
    maximum_probability = max(probabilities)
    forecast_spread = _quantize(maximum_probability - minimum_probability)
    confidence_sum = sum(confidences)
    consensus_probability = (
        _ratio(sum(probabilities), _count(len(probabilities)))
        if confidence_sum == _ZERO
        else _ratio(
            sum(signal.forecast_probability * signal.confidence for signal in signals),
            confidence_sum,
        )
    )
    consensus_confidence = _ratio(sum(confidences), _count(len(confidences)))
    minimum_confidence = min(confidences)
    consensus_confidence_gap = _quantize(consensus_confidence - minimum_confidence)
    high_disagreement = forecast_spread > disagreement_spread_limit
    stale_minority_count = _stale_minority_count(
        signals,
        generated_at=generated_at,
        consensus_probability=consensus_probability,
        stale_signal_seconds=stale_signal_seconds,
    )
    reasons = _row_reasons(
        high_disagreement=high_disagreement,
        stale_minority_count=stale_minority_count,
        consensus_confidence_gap=consensus_confidence_gap,
        confidence_gap_limit=confidence_gap_limit,
    )

    return StrategyTeamSignalDisagreementRow(
        condition_id=condition_id,
        row_status=_row_status(reasons),
        team_count=_count(len(signals)),
        minimum_forecast_probability=minimum_probability,
        maximum_forecast_probability=maximum_probability,
        average_forecast_probability=_ratio(sum(probabilities), _count(len(probabilities))),
        consensus_probability=consensus_probability,
        forecast_spread=forecast_spread,
        consensus_confidence=consensus_confidence,
        minimum_confidence=minimum_confidence,
        consensus_confidence_gap=consensus_confidence_gap,
        high_disagreement=high_disagreement,
        stale_minority_view_count=_count(stale_minority_count),
        latest_signaled_at=max(signal.signaled_at for signal in signals),
        source_references=tuple(sorted({signal.source_reference for signal in signals})),
        reason_codes=reasons,
    )


def _normalize_signals(signals: object) -> tuple[StrategyTeamForecastSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        items = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not StrategyTeamForecastSignal:
            raise ValueError("signals must contain StrategyTeamForecastSignal")
        _require_flags("signal", item)
        key = (item.condition_id, item.team_id)
        if key in seen:
            raise ValueError("signals must contain unique condition and team values")
        seen.add(key)
    return items


def _group_signals(
    signals: tuple[StrategyTeamForecastSignal, ...],
) -> tuple[tuple[str, tuple[StrategyTeamForecastSignal, ...]], ...]:
    condition_ids = tuple(sorted({signal.condition_id for signal in signals}))
    return tuple(
        (
            condition_id,
            tuple(
                sorted(
                    (
                        signal
                        for signal in signals
                        if signal.condition_id == condition_id
                    ),
                    key=lambda signal: signal.team_id,
                ),
            ),
        )
        for condition_id in condition_ids
    )


def _stale_minority_count(
    signals: tuple[StrategyTeamForecastSignal, ...],
    *,
    generated_at: datetime,
    consensus_probability: Decimal,
    stale_signal_seconds: Decimal,
) -> int:
    count = 0
    for signal in signals:
        if signal.signaled_at > generated_at:
            raise ValueError("signaled_at must not be after generated_at")
        if _age_seconds(generated_at, signal.signaled_at) <= stale_signal_seconds:
            continue
        if _quantize(abs(signal.forecast_probability - consensus_probability)) > _ZERO:
            count += 1
    return count


def _row_reasons(
    *,
    high_disagreement: bool,
    stale_minority_count: int,
    consensus_confidence_gap: Decimal,
    confidence_gap_limit: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if high_disagreement:
        reasons.append("high_team_forecast_disagreement")
    if stale_minority_count > 0:
        reasons.append("stale_minority_team_view")
    if consensus_confidence_gap > confidence_gap_limit:
        reasons.append("consensus_confidence_gap")
    if not reasons:
        return ("team_signal_disagreement_clear",)
    return tuple(sorted(reasons, key=_reason_key))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "stale_minority_team_view" in reason_codes and "consensus_confidence_gap" in reason_codes:
        return "blocked"
    if reason_codes != ("team_signal_disagreement_clear",):
        return "watch"
    return "clear"


def _report_status(rows: tuple[StrategyTeamSignalDisagreementRow, ...]) -> str:
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reasons(rows: tuple[StrategyTeamSignalDisagreementRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("empty_team_forecast_signals",)
    reasons = tuple(
        sorted(
            {
                reason
                for row in rows
                for reason in row.reason_codes
                if reason != "team_signal_disagreement_clear"
            },
            key=_reason_key,
        ),
    )
    if reasons:
        return reasons
    return ("team_signal_disagreement_clear",)


def _reason_rollups(
    rows: tuple[StrategyTeamSignalDisagreementRow, ...],
    condition_count: Decimal,
) -> tuple[StrategyTeamSignalDisagreementReasonRollup, ...]:
    if condition_count == _ZERO:
        return ()
    reason_codes = tuple(
        sorted(
            {
                reason
                for row in rows
                for reason in row.reason_codes
                if reason != "team_signal_disagreement_clear"
            },
            key=_reason_key,
        ),
    )
    return tuple(
        StrategyTeamSignalDisagreementReasonRollup(
            reason_code=reason_code,
            condition_count=_count(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
            condition_ratio=_ratio(
                _count(sum(1 for row in rows if reason_code in row.reason_codes)),
                condition_count,
            ),
        )
        for reason_code in reason_codes
    )


def _row_count(rows: tuple[StrategyTeamSignalDisagreementRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.row_status == status))


def _normalize_rows(rows: object) -> tuple[StrategyTeamSignalDisagreementRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyTeamSignalDisagreementRow:
            raise ValueError("rows must contain StrategyTeamSignalDisagreementRow")
    if normalized != tuple(sorted(normalized, key=_row_key)):
        raise ValueError("rows must use deterministic sequence")
    return normalized


def _normalize_rollups(
    rollups: object,
) -> tuple[StrategyTeamSignalDisagreementReasonRollup, ...]:
    if isinstance(rollups, (str, bytes)):
        raise ValueError("reason_rollups must be an iterable")
    try:
        normalized = tuple(rollups)
    except TypeError as exc:
        raise ValueError("reason_rollups must be an iterable") from exc
    for rollup in normalized:
        if type(rollup) is not StrategyTeamSignalDisagreementReasonRollup:
            raise ValueError("reason_rollups must contain StrategyTeamSignalDisagreementReasonRollup")
    if normalized != tuple(sorted(normalized, key=lambda rollup: _reason_key(rollup.reason_code))):
        raise ValueError("reason_rollups must use deterministic sequence")
    return normalized


def _normalize_source_references(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("source_references must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError("source_references must be an iterable") from exc
    if not items:
        raise ValueError("source_references must not be empty")
    for item in items:
        _require_text("source_reference", item)
    return tuple(dict.fromkeys(_REDACTED_SOURCE_REFERENCE for _ in items))


def _normalize_row_reasons(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reasons = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reasons:
        raise ValueError("reason_codes must include at least one code")
    for reason in reasons:
        _require_reason_code("reason_code", reason, _ROW_REASON_CODES)
    if "team_signal_disagreement_clear" in reasons and reasons != (
        "team_signal_disagreement_clear",
    ):
        raise ValueError("reason_codes clear code must stand alone")
    if tuple(sorted(dict.fromkeys(reasons), key=_reason_key)) != reasons:
        raise ValueError("reason_codes must use deterministic sequence")
    return reasons


def _normalize_report_reasons(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reasons = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reasons:
        raise ValueError("reason_codes must include at least one code")
    for reason in reasons:
        _require_reason_code("reason_code", reason, _REPORT_REASON_CODES)
    summary_codes = {
        "empty_team_forecast_signals",
        "team_signal_disagreement_clear",
    }
    if any(reason in summary_codes for reason in reasons) and len(reasons) != 1:
        raise ValueError("reason_codes summary code must stand alone")
    if tuple(sorted(dict.fromkeys(reasons), key=_reason_key)) != reasons:
        raise ValueError("reason_codes must use deterministic sequence")
    return reasons


def _check_row(row: StrategyTeamSignalDisagreementRow) -> None:
    if row.minimum_forecast_probability > row.maximum_forecast_probability:
        raise ValueError("minimum_forecast_probability must not exceed maximum")
    if row.forecast_spread != _quantize(
        row.maximum_forecast_probability - row.minimum_forecast_probability,
    ):
        raise ValueError("forecast_spread must match min and max probabilities")
    if row.consensus_confidence_gap != _quantize(
        row.consensus_confidence - row.minimum_confidence,
    ):
        raise ValueError("consensus_confidence_gap must match confidence fields")
    if row.high_disagreement != ("high_team_forecast_disagreement" in row.reason_codes):
        raise ValueError("high_disagreement must match reason_codes")
    if row.stale_minority_view_count > row.team_count:
        raise ValueError("stale_minority_view_count must not exceed team_count")
    if (row.stale_minority_view_count > _ZERO) != (
        "stale_minority_team_view" in row.reason_codes
    ):
        raise ValueError("stale_minority_view_count must match reason_codes")
    expected_status = _row_status(row.reason_codes)
    if row.row_status != expected_status:
        raise ValueError("row_status must match reason_codes")


def _check_report(report: StrategyTeamSignalDisagreementDigestReport) -> None:
    if report.condition_count != _count(len(report.rows)):
        raise ValueError("condition_count must match rows")
    if report.signal_count != sum((row.team_count for row in report.rows), _ZERO):
        raise ValueError("signal_count must match rows")
    if report.clear_condition_count != _row_count(report.rows, "clear"):
        raise ValueError("clear_condition_count must match rows")
    if report.watch_condition_count != _row_count(report.rows, "watch"):
        raise ValueError("watch_condition_count must match rows")
    if report.blocked_condition_count != _row_count(report.rows, "blocked"):
        raise ValueError("blocked_condition_count must match rows")
    expected_disagreement_count = _count(
        sum(
            1
            for row in report.rows
            if row.reason_codes != ("team_signal_disagreement_clear",)
        ),
    )
    if report.disagreement_condition_count != expected_disagreement_count:
        raise ValueError("disagreement_condition_count must match rows")
    if report.condition_count == _ZERO:
        if report.disagreement_condition_ratio is not None:
            raise ValueError("empty reports must not set disagreement_condition_ratio")
    elif report.disagreement_condition_ratio != _ratio(
        report.disagreement_condition_count,
        report.condition_count,
    ):
        raise ValueError("disagreement_condition_ratio must match rows")
    if report.clear_condition_count + report.watch_condition_count + report.blocked_condition_count != report.condition_count:
        raise ValueError("condition status counts must match rows")
    if any(row.latest_signaled_at > report.generated_at for row in report.rows):
        raise ValueError("latest_signaled_at must not be after generated_at")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reasons(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_rollups != _reason_rollups(report.rows, report.condition_count):
        raise ValueError("reason_rollups must match rows")


def _row_key(row: StrategyTeamSignalDisagreementRow) -> tuple[int, str]:
    return (_ROW_STATUS_RANK[row.row_status], row.condition_id)


def _reason_key(reason_code: str) -> tuple[int, str]:
    return (_REASON_RANK.get(reason_code, len(_REASON_RANK)), reason_code)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value)


def _normalize_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return normalized


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _age_seconds(generated_at: datetime, signaled_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - signaled_at).total_seconds()))
    if seconds < _ZERO:
        raise ValueError("signaled_at must not be after generated_at")
    return _quantize(seconds)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in _PUBLIC_TEXT_BLOCKLIST):
        raise ValueError(f"{name} contains unsafe public text")


def _require_reason_code(name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_public_text(name, value)
    if value not in allowed:
        raise ValueError(f"{name} must be a known code")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_row_status(name: str, value: object) -> None:
    _require_text(name, value)
    if value not in _ROW_STATUS_RANK:
        raise ValueError(f"{name} must be clear, watch, or blocked")


def _require_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if dataclass_isinstance(value):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        _require_public_text("JSON value", value)
        return value
    if type(value) is bool:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_text("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def dataclass_isinstance(value: object) -> bool:
    return hasattr(value, "__dataclass_fields__") and not isinstance(value, type)


__all__ = (
    "StrategyTeamForecastSignal",
    "StrategyTeamSignalDisagreementDigestReport",
    "StrategyTeamSignalDisagreementReasonRollup",
    "StrategyTeamSignalDisagreementRow",
    "build_strategy_team_signal_disagreement_digest",
    "strategy_team_signal_disagreement_digest_payload",
)
