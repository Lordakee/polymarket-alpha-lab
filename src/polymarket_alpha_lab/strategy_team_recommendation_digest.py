"""Paper-only strategy team recommendation report reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


_VALUE_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_FEE_DRAG = Decimal("0.020000")
_REDACTED_EVIDENCE = "<redacted-evidence-reference>"
_PAPER_REPORT_STATUSES = ("recommend", "watch", "reject")
_SIDES = ("yes", "no")
_UNSAFE_SURFACE_FIELD_FRAGMENTS = (
    "private_key",
    "exchange_mutation",
    "order_submission",
)
_UNSAFE_SURFACE_FIELD_TOKENS = (
    "action",
    "auth",
    "broker",
    "cancel",
    "execute",
    "execution",
    "live",
    "order",
    "replace",
    "sign",
    "submit",
    "trade",
    "trading",
    "wallet",
)
_SENSITIVE_REASON_TOKENS = (
    "secret",
    "token",
    "private",
    "key",
    "bearer",
    "dsn",
    "password",
    "wallet",
)
_SECRET_TEXT_MARKERS = (
    "postgres://",
    "postgresql://",
    "bearer ",
    "password=",
    "password:",
    "private_key",
    "private-key",
    "api_key",
    "api-key",
    "access_token",
    "refresh_token",
    "secret=",
    "secret:",
    "dsn=",
    "service-role",
)


@dataclass(frozen=True)
class PaperStrategyTeamRecommendationConfig:
    config_version: str
    min_net_edge: Decimal
    min_confidence: Decimal
    max_evidence_age_seconds: Decimal
    min_liquidity: Decimal
    max_spread: Decimal
    max_recommendations_per_team: Decimal
    max_recommendations_per_category: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("config_version", self.config_version)
        for name in (
            "min_net_edge",
            "min_confidence",
            "min_liquidity",
            "max_spread",
        ):
            object.__setattr__(self, name, _decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _seconds("max_evidence_age_seconds", self.max_evidence_age_seconds),
        )
        for name in ("max_recommendations_per_team", "max_recommendations_per_category"):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        _require_flags("config", self)


@dataclass(frozen=True)
class TeamResearchRecommendationSignal:
    team_id: str
    category_id: str
    market_slug: str
    question: str
    side: str
    forecast_probability: Decimal
    implied_probability: Decimal
    confidence: Decimal
    liquidity: Decimal
    spread: Decimal
    observed_at: datetime
    evidence_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for name in ("team_id", "category_id", "market_slug", "question"):
            _require_text(name, getattr(self, name))
        if self.side not in _SIDES:
            raise ValueError("side must be yes or no")
        for name in ("forecast_probability", "implied_probability", "confidence"):
            value = _decimal(name, getattr(self, name))
            if value > Decimal("1.000000"):
                raise ValueError(f"{name} must be at most 1.000000")
            object.__setattr__(self, name, value)
        for name in ("liquidity", "spread"):
            object.__setattr__(self, name, _decimal(name, getattr(self, name)))
        object.__setattr__(self, "observed_at", _utc("observed_at", self.observed_at))
        object.__setattr__(self, "evidence_reference", _REDACTED_EVIDENCE)
        object.__setattr__(self, "reason_codes", _reasons(self.reason_codes))
        _require_flags("signal", self)


@dataclass(frozen=True)
class PaperStrategyTeamRecommendationRow:
    team_id: str
    category_id: str
    market_slug: str
    question: str
    side: str
    forecast_probability: Decimal
    implied_probability: Decimal
    confidence: Decimal
    liquidity: Decimal
    spread: Decimal
    observed_at: datetime
    evidence_age_seconds: Decimal
    evidence_status: str
    evidence_reference: str
    raw_edge: Decimal
    fee_drag: Decimal
    net_edge: Decimal
    recommendation_score: Decimal
    paper_report_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if self.paper_report_status not in _PAPER_REPORT_STATUSES:
            raise ValueError("paper_report_status must be recommend, watch, or reject")
        object.__setattr__(self, "observed_at", _utc("observed_at", self.observed_at))
        for name in (
            "forecast_probability",
            "implied_probability",
            "confidence",
            "liquidity",
            "spread",
            "evidence_age_seconds",
            "raw_edge",
            "fee_drag",
            "net_edge",
            "recommendation_score",
        ):
            object.__setattr__(self, name, _decimal(name, getattr(self, name)))
        object.__setattr__(self, "reason_codes", _reasons(self.reason_codes))
        _require_flags("row", self)


@dataclass(frozen=True)
class PaperStrategyTeamRecommendationReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    recommend_count: Decimal
    watch_count: Decimal
    reject_count: Decimal
    recommendation_rows: tuple[PaperStrategyTeamRecommendationRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        object.__setattr__(
            self,
            "recommendation_rows",
            _normalize_rows(self.recommendation_rows),
        )
        for name in ("signal_count", "recommend_count", "watch_count", "reject_count"):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        if self.signal_count != self.recommend_count + self.watch_count + self.reject_count:
            raise ValueError("signal_count must reconcile with paper report status counts")
        if self.signal_count != _count("signal_count", Decimal(len(self.recommendation_rows))):
            raise ValueError("signal_count must match recommendation_rows")
        if self.recommend_count != _status_count(self.recommendation_rows, "recommend"):
            raise ValueError("recommend_count must match recommendation_rows")
        if self.watch_count != _status_count(self.recommendation_rows, "watch"):
            raise ValueError("watch_count must match recommendation_rows")
        if self.reject_count != _status_count(self.recommendation_rows, "reject"):
            raise ValueError("reject_count must match recommendation_rows")
        _require_flags("report", self)


def build_paper_strategy_team_recommendation_report(
    signals: Iterable[TeamResearchRecommendationSignal],
    *,
    config: PaperStrategyTeamRecommendationConfig,
    generated_at: datetime,
) -> PaperStrategyTeamRecommendationReport:
    if type(config) is not PaperStrategyTeamRecommendationConfig:
        raise ValueError("config must be PaperStrategyTeamRecommendationConfig")
    generated_at = _utc("generated_at", generated_at)
    _require_flags("config", config)
    rows = [_base_row(signal, config, generated_at) for signal in _normalize_signals(signals)]
    rows.sort(key=_row_sort_key)

    team_recommends: dict[str, int] = {}
    category_recommends: dict[str, int] = {}
    final_rows: list[PaperStrategyTeamRecommendationRow] = []
    for row in rows:
        paper_report_status = row.paper_report_status
        reasons = list(row.reason_codes)
        if paper_report_status != "reject":
            team_count = team_recommends.get(row.team_id, 0)
            category_count = category_recommends.get(row.category_id, 0)
            if Decimal(team_count) >= config.max_recommendations_per_team:
                paper_report_status = "watch"
                reasons.append("team_risk_cap_reached")
            else:
                reasons.append("team_risk_cap_passed")
            if Decimal(category_count) >= config.max_recommendations_per_category:
                paper_report_status = "watch"
                reasons.append("category_risk_cap_reached")
            else:
                reasons.append("category_risk_cap_passed")
            if paper_report_status == "recommend":
                team_recommends[row.team_id] = team_count + 1
                category_recommends[row.category_id] = category_count + 1
        final_rows.append(
            _copy_row_with_status(
                row,
                paper_report_status=paper_report_status,
                reason_codes=tuple(reasons),
            ),
        )

    return PaperStrategyTeamRecommendationReport(
        generated_at=generated_at,
        config_version=config.config_version,
        signal_count=_count("signal_count", Decimal(len(final_rows))),
        recommend_count=_count(
            "recommend_count",
            Decimal(sum(1 for row in final_rows if row.paper_report_status == "recommend")),
        ),
        watch_count=_count(
            "watch_count",
            Decimal(sum(1 for row in final_rows if row.paper_report_status == "watch")),
        ),
        reject_count=_count(
            "reject_count",
            Decimal(sum(1 for row in final_rows if row.paper_report_status == "reject")),
        ),
        recommendation_rows=tuple(final_rows),
    )


def strategy_team_recommendation_digest_payload(
    report: PaperStrategyTeamRecommendationReport,
) -> dict[str, object]:
    if type(report) is not PaperStrategyTeamRecommendationReport:
        raise ValueError("report must be PaperStrategyTeamRecommendationReport")
    _require_flags("report", report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "signal_count": _count_payload(report.signal_count),
        "recommend_count": _count_payload(report.recommend_count),
        "watch_count": _count_payload(report.watch_count),
        "reject_count": _count_payload(report.reject_count),
        "recommendation_rows": [_row_payload(row) for row in report.recommendation_rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: PaperStrategyTeamRecommendationRow) -> dict[str, object]:
    _require_flags("row", row)
    return {
        "team_id": row.team_id,
        "category_id": row.category_id,
        "market_slug": row.market_slug,
        "question": row.question,
        "side": row.side,
        "forecast_probability": _decimal_payload(row.forecast_probability),
        "implied_probability": _decimal_payload(row.implied_probability),
        "confidence": _decimal_payload(row.confidence),
        "liquidity": _decimal_payload(row.liquidity),
        "spread": _decimal_payload(row.spread),
        "observed_at": row.observed_at.isoformat(),
        "evidence_age_seconds": _decimal_payload(row.evidence_age_seconds),
        "evidence_status": row.evidence_status,
        "evidence_reference": row.evidence_reference,
        "raw_edge": _decimal_payload(row.raw_edge),
        "fee_drag": _decimal_payload(row.fee_drag),
        "net_edge": _decimal_payload(row.net_edge),
        "recommendation_score": _decimal_payload(row.recommendation_score),
        "paper_report_status": row.paper_report_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _base_row(
    signal: TeamResearchRecommendationSignal,
    config: PaperStrategyTeamRecommendationConfig,
    generated_at: datetime,
) -> PaperStrategyTeamRecommendationRow:
    raw_edge = _decimal("raw_edge", signal.forecast_probability - signal.implied_probability)
    net_edge = _decimal("net_edge", raw_edge - _FEE_DRAG)
    score = _decimal("recommendation_score", net_edge * signal.confidence)
    evidence_age = _seconds_between(generated_at, signal.observed_at)
    evidence_status = "stale" if evidence_age > config.max_evidence_age_seconds else "fresh"
    paper_report_status = "recommend"
    reasons = list(signal.reason_codes)
    if net_edge <= config.min_net_edge:
        paper_report_status = "reject"
        reasons.append("nonpositive_net_edge_after_fee_drag")
    else:
        reasons.append("positive_net_edge")
    if signal.confidence < config.min_confidence:
        paper_report_status = (
            "watch" if paper_report_status != "reject" else paper_report_status
        )
        reasons.append("confidence_below_threshold")
    else:
        reasons.append("confidence_passed")
    reasons.append("evidence_stale" if evidence_status == "stale" else "evidence_fresh")
    if signal.liquidity < config.min_liquidity:
        paper_report_status = (
            "watch" if paper_report_status != "reject" else paper_report_status
        )
        reasons.append("liquidity_below_threshold")
    else:
        reasons.append("liquidity_passed")
    if signal.spread > config.max_spread:
        paper_report_status = (
            "watch" if paper_report_status != "reject" else paper_report_status
        )
        reasons.append("spread_above_threshold")
    else:
        reasons.append("spread_passed")
    return PaperStrategyTeamRecommendationRow(
        team_id=signal.team_id,
        category_id=signal.category_id,
        market_slug=signal.market_slug,
        question=signal.question,
        side=signal.side,
        forecast_probability=signal.forecast_probability,
        implied_probability=signal.implied_probability,
        confidence=signal.confidence,
        liquidity=signal.liquidity,
        spread=signal.spread,
        observed_at=signal.observed_at,
        evidence_age_seconds=evidence_age,
        evidence_status=evidence_status,
        evidence_reference=_REDACTED_EVIDENCE,
        raw_edge=raw_edge,
        fee_drag=_FEE_DRAG,
        net_edge=net_edge,
        recommendation_score=score,
        paper_report_status=paper_report_status,
        reason_codes=tuple(reasons),
    )


def _copy_row_with_status(
    row: PaperStrategyTeamRecommendationRow,
    *,
    paper_report_status: str,
    reason_codes: tuple[str, ...],
) -> PaperStrategyTeamRecommendationRow:
    return PaperStrategyTeamRecommendationRow(
        team_id=row.team_id,
        category_id=row.category_id,
        market_slug=row.market_slug,
        question=row.question,
        side=row.side,
        forecast_probability=row.forecast_probability,
        implied_probability=row.implied_probability,
        confidence=row.confidence,
        liquidity=row.liquidity,
        spread=row.spread,
        observed_at=row.observed_at,
        evidence_age_seconds=row.evidence_age_seconds,
        evidence_status=row.evidence_status,
        evidence_reference=row.evidence_reference,
        raw_edge=row.raw_edge,
        fee_drag=row.fee_drag,
        net_edge=row.net_edge,
        recommendation_score=row.recommendation_score,
        paper_report_status=paper_report_status,
        reason_codes=_reasons(reason_codes),
    )


def _normalize_signals(
    signals: Iterable[TeamResearchRecommendationSignal],
) -> tuple[TeamResearchRecommendationSignal, ...]:
    if isinstance(signals, (str, bytes)) or not isinstance(signals, Iterable):
        raise ValueError("signals must be iterable")
    normalized = tuple(signals)
    for signal in normalized:
        if type(signal) is not TeamResearchRecommendationSignal:
            raise ValueError("signals must contain TeamResearchRecommendationSignal")
        _require_flags("signal", signal)
    return normalized


def _normalize_rows(
    rows: tuple[PaperStrategyTeamRecommendationRow, ...],
) -> tuple[PaperStrategyTeamRecommendationRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("recommendation_rows must be tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not PaperStrategyTeamRecommendationRow:
            raise ValueError("recommendation_rows must contain PaperStrategyTeamRecommendationRow")
        _require_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("recommendation_rows must be deterministically sorted")
    return normalized


def _row_sort_key(
    row: PaperStrategyTeamRecommendationRow,
) -> tuple[Decimal, str, str, str, str]:
    return (
        -row.recommendation_score,
        row.team_id,
        row.category_id,
        row.market_slug,
        row.side,
    )


def _status_count(
    rows: tuple[PaperStrategyTeamRecommendationRow, ...],
    paper_report_status: str,
) -> Decimal:
    return _count(
        f"{paper_report_status}_count",
        Decimal(sum(1 for row in rows if row.paper_report_status == paper_report_status)),
    )


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    return Decimal(str((later - earlier).total_seconds())).quantize(Decimal("1"))


def _utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value.quantize(_VALUE_QUANTUM)


def _count(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exact Decimal")
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be whole Decimal")
    return value.quantize(_COUNT_QUANTUM)


def _seconds(name: str, value: Decimal) -> Decimal:
    return _count(name, value)


def _require_text(name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be text")
    _reject_secret_like_text(name, value)


def _reasons(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be tuple")
    for reason_code in value:
        if type(reason_code) is not str or not reason_code:
            raise ValueError("reason_codes must contain text")
        if reason_code != reason_code.lower() or reason_code.strip() != reason_code:
            raise ValueError("reason_codes must contain canonical values")
        lowered = reason_code.lower()
        tokens = _identifier_tokens(lowered)
        if any(token in _UNSAFE_SURFACE_FIELD_TOKENS for token in tokens):
            raise ValueError(
                "reason_codes must not contain live trading or execution content",
            )
        if any(token in lowered for token in _SENSITIVE_REASON_TOKENS):
            raise ValueError("reason_codes must not contain sensitive content")
    return tuple(dict.fromkeys(value))


def _require_flags(name: str, value: Any) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{name} {flag} must be True")
    _reject_unsafe_surface_fields(name, value)


def _reject_unsafe_surface_fields(name: str, value: object) -> None:
    for field_name in _iter_field_names(value):
        normalized = field_name.lower()
        tokens = _identifier_tokens(normalized)
        if any(fragment in normalized for fragment in _UNSAFE_SURFACE_FIELD_FRAGMENTS) or any(
            token in _UNSAFE_SURFACE_FIELD_TOKENS for token in tokens
        ):
            raise ValueError(f"unsafe live surface field in {name}: {field_name}")


def _iter_field_names(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        names: list[str] = []
        for item in fields(value):
            names.append(item.name)
            names.extend(_iter_field_names(getattr(value, item.name)))
        return tuple(names)
    if isinstance(value, dict):
        names = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("field names must be strings")
            names.append(key)
            names.extend(_iter_field_names(item))
        return tuple(names)
    if isinstance(value, (list, tuple)):
        names = []
        for item in value:
            names.extend(_iter_field_names(item))
        return tuple(names)
    return ()


def _identifier_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for char in value:
        if char.isalnum():
            current.append(char)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


def _reject_secret_like_text(name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered and "@" in lowered:
        raise ValueError(f"{name} must not contain secret-like text")
    if any(marker in lowered for marker in _SECRET_TEXT_MARKERS):
        raise ValueError(f"{name} must not contain secret-like text")


def _decimal_payload(value: Decimal) -> str:
    return format(_decimal("payload decimal", value), "f")


def _count_payload(value: Decimal) -> str:
    return str(int(_count("payload count", value)))


__all__ = (
    "PaperStrategyTeamRecommendationConfig",
    "PaperStrategyTeamRecommendationReport",
    "PaperStrategyTeamRecommendationRow",
    "TeamResearchRecommendationSignal",
    "build_paper_strategy_team_recommendation_report",
    "strategy_team_recommendation_digest_payload",
)
