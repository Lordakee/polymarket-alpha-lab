from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_TEAM_POSTMORTEM_LEARNING_PRIORITY_CONFIG_VERSION = (
    "strategy-team-postmortem-learning-priority-v10"
)
LEARNING_PRIORITY_STATUSES = ("pass", "watch", "prioritize")
VALIDATION_DIGEST_PREFIX = "stplp-v10:"

_COUNT_QUANTUM = Decimal("1")
_MONEY_QUANTUM = Decimal("0.01")
_RATIO_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_MONEY = Decimal("0.00")
_ZERO_RATIO = Decimal("0.000000")
_DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
_STATUS_RANK = {"prioritize": 0, "watch": 1, "pass": 2}
_UNSAFE_TEXT_FRAGMENTS = (
    frozenset(
        fragment
        for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS
        if fragment != "".join(("si", "gn"))
    )
    | frozenset(
        "".join(parts)
        for parts in (
            ("li", "ve"),
            ("trad", "ing"),
            ("tra", "de"),
            ("bro", "ker"),
            ("cl", "ient"),
            ("exec", "ute"),
            ("conn", "ect"),
            ("requ", "est"),
            ("http",),
            ("pri", "vate", "_", "key"),
            ("api", "_", "key"),
            ("sec", "ret"),
            ("to", "ken"),
        )
    )
)


@dataclass(frozen=True)
class StrategyTeamPostmortemLearningPriorityConfig:
    config_version: str = (
        DEFAULT_STRATEGY_TEAM_POSTMORTEM_LEARNING_PRIORITY_CONFIG_VERSION
    )
    forecast_miss_threshold: Decimal = Decimal("0.150000")
    stake_notional_proxy_threshold: Decimal = Decimal("1000.00")
    source_failure_rate_threshold: Decimal = Decimal("0.200000")
    resolution_ambiguity_threshold: Decimal = Decimal("0.250000")
    lesson_reuse_potential_threshold: Decimal = Decimal("0.750000")
    stake_notional_score_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "forecast_miss_threshold",
            "source_failure_rate_threshold",
            "resolution_ambiguity_threshold",
            "lesson_reuse_potential_threshold",
            "stake_notional_score_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stake_notional_proxy_threshold",
            _normalize_positive_money(
                "stake_notional_proxy_threshold",
                self.stake_notional_proxy_threshold,
            ),
        )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class StrategyTeamPostmortemLearningPrioritySignal:
    team_id: str = field(repr=False)
    market_id: str = field(repr=False)
    postmortem_id: str = field(repr=False)
    forecast_miss: Decimal
    notional_proxy: Decimal
    source_failure_rate: Decimal
    resolution_ambiguity_score: Decimal
    lesson_reuse_potential: Decimal
    source_row_count: Decimal = _COUNT_QUANTUM
    source_missing: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("postmortem_id", self.postmortem_id)
        for field_name in (
            "forecast_miss",
            "source_failure_rate",
            "resolution_ambiguity_score",
            "lesson_reuse_potential",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "notional_proxy",
            _normalize_nonnegative_money("notional_proxy", self.notional_proxy),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_nonnegative_count("source_row_count", self.source_row_count),
        )
        if type(self.source_missing) is not bool:
            raise ValueError("source_missing must be a bool")
        require_paper_only_flags("signal", self)


@dataclass(frozen=True)
class StrategyTeamPostmortemLearningPriorityRow:
    redacted_team_ref: str
    redacted_market_ref: str
    redacted_postmortem_ref: str
    forecast_miss: Decimal
    notional_proxy: Decimal
    source_failure_rate: Decimal
    resolution_ambiguity_score: Decimal
    lesson_reuse_potential: Decimal
    source_row_count: Decimal
    source_missing: bool
    learning_priority_score: Decimal
    learning_priority_status: str
    priority_rank: Decimal
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_ref("redacted_team_ref", self.redacted_team_ref, "<redacted-team-")
        _require_redacted_ref(
            "redacted_market_ref",
            self.redacted_market_ref,
            "<redacted-market-",
        )
        _require_redacted_ref(
            "redacted_postmortem_ref",
            self.redacted_postmortem_ref,
            "<redacted-postmortem-",
        )
        for field_name in (
            "forecast_miss",
            "source_failure_rate",
            "resolution_ambiguity_score",
            "lesson_reuse_potential",
            "learning_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "notional_proxy",
            _normalize_nonnegative_money("notional_proxy", self.notional_proxy),
        )
        for field_name in ("source_row_count", "priority_rank"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if type(self.source_missing) is not bool:
            raise ValueError("source_missing must be a bool")
        _require_member(
            "learning_priority_status",
            self.learning_priority_status,
            LEARNING_PRIORITY_STATUSES,
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "validation_digest",
            _require_validation_digest("validation_digest", self.validation_digest),
        )
        _validate_row_digest(self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class StrategyTeamPostmortemLearningPriorityReport:
    generated_at: datetime
    config_version: str
    source_signal_count: Decimal
    priority_row_count: Decimal
    pass_row_count: Decimal
    watch_row_count: Decimal
    prioritize_row_count: Decimal
    source_missing_count: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    priority_rows: tuple[StrategyTeamPostmortemLearningPriorityRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_signal_count",
            "priority_row_count",
            "pass_row_count",
            "watch_row_count",
            "prioritize_row_count",
            "source_missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, LEARNING_PRIORITY_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        rows = tuple(self.priority_rows)
        for row in rows:
            if type(row) is not StrategyTeamPostmortemLearningPriorityRow:
                raise ValueError("priority_rows must contain learning priority row values")
            require_paper_only_flags("row", row)
        object.__setattr__(self, "priority_rows", rows)
        object.__setattr__(
            self,
            "validation_digest",
            _require_validation_digest("validation_digest", self.validation_digest),
        )
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        require_paper_only_flags("report", self)


def build_strategy_team_postmortem_learning_priority_report(
    signals: (
        list[StrategyTeamPostmortemLearningPrioritySignal]
        | tuple[StrategyTeamPostmortemLearningPrioritySignal, ...]
    ),
    *,
    config: StrategyTeamPostmortemLearningPriorityConfig,
    generated_at: datetime,
) -> StrategyTeamPostmortemLearningPriorityReport:
    if type(config) is not StrategyTeamPostmortemLearningPriorityConfig:
        raise ValueError("config must be a StrategyTeamPostmortemLearningPriorityConfig")
    require_paper_only_flags("config", config)
    normalized_signals = _normalize_signals(signals)
    team_refs = _redaction_map(tuple(signal.team_id for signal in normalized_signals), "team")
    market_refs = _redaction_map(
        tuple(signal.market_id for signal in normalized_signals),
        "market",
    )
    postmortem_refs = _redaction_map(
        tuple(signal.postmortem_id for signal in normalized_signals),
        "postmortem",
    )
    ranked_rows = tuple(
        sorted(
            (
                _row_from_signal(
                    signal,
                    config=config,
                    redacted_team_ref=team_refs[signal.team_id],
                    redacted_market_ref=market_refs[signal.market_id],
                    redacted_postmortem_ref=postmortem_refs[signal.postmortem_id],
                )
                for signal in normalized_signals
            ),
            key=_row_key,
        ),
    )
    rows = tuple(
        _row_with_priority(row, _count(index))
        for index, row in enumerate(ranked_rows, start=1)
    )
    pass_row_count = _count(
        sum(1 for row in rows if row.learning_priority_status == "pass"),
    )
    watch_row_count = _count(
        sum(1 for row in rows if row.learning_priority_status == "watch"),
    )
    prioritize_row_count = _count(
        sum(1 for row in rows if row.learning_priority_status == "prioritize"),
    )
    source_missing_count = _count(sum(1 for row in rows if row.source_missing))
    report_status = _report_status(rows)
    source_signal_count = _count(len(normalized_signals))
    priority_row_count = _count(len(rows))
    reason_codes = _report_reason_codes(
        report_status,
        source_missing_count=source_missing_count,
    )

    return StrategyTeamPostmortemLearningPriorityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_signal_count=source_signal_count,
        priority_row_count=priority_row_count,
        pass_row_count=pass_row_count,
        watch_row_count=watch_row_count,
        prioritize_row_count=prioritize_row_count,
        source_missing_count=source_missing_count,
        report_status=report_status,
        reason_codes=reason_codes,
        priority_rows=rows,
        validation_digest=_report_validation_digest(
            generated_at=generated_at,
            config_version=config.config_version,
            source_signal_count=source_signal_count,
            priority_row_count=priority_row_count,
            pass_row_count=pass_row_count,
            watch_row_count=watch_row_count,
            prioritize_row_count=prioritize_row_count,
            source_missing_count=source_missing_count,
            report_status=report_status,
            reason_codes=reason_codes,
            priority_rows=rows,
        ),
    )


def strategy_team_postmortem_learning_priority_payload(
    report: StrategyTeamPostmortemLearningPriorityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyTeamPostmortemLearningPriorityReport:
        require_paper_only_flags("report", report)
        _require_recursive_paper_only_flags("report", report)
        _validate_report(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_recursive_paper_only_flags("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a StrategyTeamPostmortemLearningPriorityReport")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
    _require_recursive_paper_only_flags("payload", payload)
    _reject_unsafe_public_payload("payload", payload)
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


def _normalize_signals(
    signals: (
        list[StrategyTeamPostmortemLearningPrioritySignal]
        | tuple[StrategyTeamPostmortemLearningPrioritySignal, ...]
    ),
) -> tuple[StrategyTeamPostmortemLearningPrioritySignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    seen_pairs: set[tuple[str, str]] = set()
    for signal in normalized:
        if type(signal) is not StrategyTeamPostmortemLearningPrioritySignal:
            raise ValueError("signals must contain postmortem learning priority signal values")
        require_paper_only_flags("signal", signal)
        pair = (signal.team_id, signal.postmortem_id)
        if pair in seen_pairs:
            raise ValueError("signals must not contain duplicate team postmortem pairs")
        seen_pairs.add(pair)
    return normalized


def _row_from_signal(
    signal: StrategyTeamPostmortemLearningPrioritySignal,
    *,
    config: StrategyTeamPostmortemLearningPriorityConfig,
    redacted_team_ref: str,
    redacted_market_ref: str,
    redacted_postmortem_ref: str,
) -> StrategyTeamPostmortemLearningPriorityRow:
    reason_codes = _row_reason_codes(signal, config)
    status = _row_status(signal, reason_codes)
    learning_priority_score = _learning_priority_score(signal, config)
    return StrategyTeamPostmortemLearningPriorityRow(
        redacted_team_ref=redacted_team_ref,
        redacted_market_ref=redacted_market_ref,
        redacted_postmortem_ref=redacted_postmortem_ref,
        forecast_miss=signal.forecast_miss,
        notional_proxy=signal.notional_proxy,
        source_failure_rate=signal.source_failure_rate,
        resolution_ambiguity_score=signal.resolution_ambiguity_score,
        lesson_reuse_potential=signal.lesson_reuse_potential,
        source_row_count=signal.source_row_count,
        source_missing=signal.source_missing,
        learning_priority_score=learning_priority_score,
        learning_priority_status=status,
        priority_rank=_ZERO_COUNT,
        reason_codes=reason_codes,
        validation_digest=_row_validation_digest(
            redacted_team_ref=redacted_team_ref,
            redacted_market_ref=redacted_market_ref,
            redacted_postmortem_ref=redacted_postmortem_ref,
            forecast_miss=signal.forecast_miss,
            notional_proxy=signal.notional_proxy,
            source_failure_rate=signal.source_failure_rate,
            resolution_ambiguity_score=signal.resolution_ambiguity_score,
            lesson_reuse_potential=signal.lesson_reuse_potential,
            source_row_count=signal.source_row_count,
            source_missing=signal.source_missing,
            learning_priority_score=learning_priority_score,
            learning_priority_status=status,
            priority_rank=_ZERO_COUNT,
            reason_codes=reason_codes,
        ),
    )


def _row_with_priority(
    row: StrategyTeamPostmortemLearningPriorityRow,
    priority_rank: Decimal,
) -> StrategyTeamPostmortemLearningPriorityRow:
    return StrategyTeamPostmortemLearningPriorityRow(
        redacted_team_ref=row.redacted_team_ref,
        redacted_market_ref=row.redacted_market_ref,
        redacted_postmortem_ref=row.redacted_postmortem_ref,
        forecast_miss=row.forecast_miss,
        notional_proxy=row.notional_proxy,
        source_failure_rate=row.source_failure_rate,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        lesson_reuse_potential=row.lesson_reuse_potential,
        source_row_count=row.source_row_count,
        source_missing=row.source_missing,
        learning_priority_score=row.learning_priority_score,
        learning_priority_status=row.learning_priority_status,
        priority_rank=priority_rank,
        reason_codes=row.reason_codes,
        validation_digest=_row_validation_digest(
            redacted_team_ref=row.redacted_team_ref,
            redacted_market_ref=row.redacted_market_ref,
            redacted_postmortem_ref=row.redacted_postmortem_ref,
            forecast_miss=row.forecast_miss,
            notional_proxy=row.notional_proxy,
            source_failure_rate=row.source_failure_rate,
            resolution_ambiguity_score=row.resolution_ambiguity_score,
            lesson_reuse_potential=row.lesson_reuse_potential,
            source_row_count=row.source_row_count,
            source_missing=row.source_missing,
            learning_priority_score=row.learning_priority_score,
            learning_priority_status=row.learning_priority_status,
            priority_rank=priority_rank,
            reason_codes=row.reason_codes,
        ),
    )


def _learning_priority_score(
    signal: StrategyTeamPostmortemLearningPrioritySignal,
    config: StrategyTeamPostmortemLearningPriorityConfig,
) -> Decimal:
    if signal.source_missing:
        return _ZERO_RATIO
    score = (
        signal.forecast_miss
        + signal.source_failure_rate
        + signal.resolution_ambiguity_score
        + signal.lesson_reuse_potential
    )
    if signal.notional_proxy >= config.stake_notional_proxy_threshold:
        score += _weighted_threshold_score(
            signal.notional_proxy,
            config.stake_notional_proxy_threshold,
            config.stake_notional_score_weight,
        )
    return _normalize_nonnegative_ratio("learning_priority_score", score)


def _weighted_threshold_score(value: Decimal, threshold: Decimal, weight: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return ((value / threshold) * weight).quantize(_RATIO_QUANTUM)


def _row_reason_codes(
    signal: StrategyTeamPostmortemLearningPrioritySignal,
    config: StrategyTeamPostmortemLearningPriorityConfig,
) -> tuple[str, ...]:
    if signal.source_missing:
        return ("strategy_team_postmortem_learning_priority_source_missing",)

    reason_codes: list[str] = []
    if signal.forecast_miss >= config.forecast_miss_threshold:
        reason_codes.append("forecast_miss_high")
    if signal.notional_proxy >= config.stake_notional_proxy_threshold:
        reason_codes.append("stake_notional_proxy_high")
    if signal.source_failure_rate >= config.source_failure_rate_threshold:
        reason_codes.append("source_failure_rate_high")
    if signal.resolution_ambiguity_score >= config.resolution_ambiguity_threshold:
        reason_codes.append("resolution_ambiguity_high")
    if signal.lesson_reuse_potential >= config.lesson_reuse_potential_threshold:
        reason_codes.append("lesson_reuse_potential_high")
    if not reason_codes:
        reason_codes.append("postmortem_learning_priority_clear")
    return tuple(reason_codes)


def _row_status(
    signal: StrategyTeamPostmortemLearningPrioritySignal,
    reason_codes: tuple[str, ...],
) -> str:
    if signal.source_missing:
        return "watch"
    if reason_codes == ("postmortem_learning_priority_clear",):
        return "pass"
    return "prioritize"


def _report_status(rows: tuple[StrategyTeamPostmortemLearningPriorityRow, ...]) -> str:
    if any(row.learning_priority_status == "prioritize" for row in rows):
        return "prioritize"
    if any(row.learning_priority_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    report_status: str,
    *,
    source_missing_count: Decimal,
) -> tuple[str, ...]:
    if report_status == "prioritize":
        reason_codes = ["strategy_team_postmortem_learning_priority_prioritize"]
    elif report_status == "watch":
        reason_codes = ["strategy_team_postmortem_learning_priority_watch"]
    else:
        return ("strategy_team_postmortem_learning_priority_clear",)
    if source_missing_count > _ZERO_COUNT:
        reason_codes.append("strategy_team_postmortem_learning_priority_source_missing")
    return tuple(reason_codes)


def _row_key(
    row: StrategyTeamPostmortemLearningPriorityRow,
) -> tuple[int, Decimal, str, str, str]:
    return (
        _STATUS_RANK[row.learning_priority_status],
        -row.learning_priority_score,
        row.redacted_team_ref,
        row.redacted_market_ref,
        row.redacted_postmortem_ref,
    )


def _redaction_map(values: tuple[str, ...], label: str) -> dict[str, str]:
    return {
        value: f"<redacted-{label}-{index:03d}>"
        for index, value in enumerate(sorted(set(values)), start=1)
    }


def _validate_report(report: StrategyTeamPostmortemLearningPriorityReport) -> None:
    rows = report.priority_rows
    for row in rows:
        _validate_row_digest(row)
    if report.priority_row_count != _count(len(rows)):
        raise ValueError("priority_row_count must match priority_rows")
    if report.source_signal_count != report.priority_row_count:
        raise ValueError("source_signal_count must match priority_row_count")
    if report.pass_row_count != _count(
        sum(1 for row in rows if row.learning_priority_status == "pass"),
    ):
        raise ValueError("pass_row_count must match priority_rows")
    if report.watch_row_count != _count(
        sum(1 for row in rows if row.learning_priority_status == "watch"),
    ):
        raise ValueError("watch_row_count must match priority_rows")
    if report.prioritize_row_count != _count(
        sum(1 for row in rows if row.learning_priority_status == "prioritize"),
    ):
        raise ValueError("prioritize_row_count must match priority_rows")
    if report.source_missing_count != _count(sum(1 for row in rows if row.source_missing)):
        raise ValueError("source_missing_count must match priority_rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match priority_rows")
    if report.validation_digest != _report_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_signal_count=report.source_signal_count,
        priority_row_count=report.priority_row_count,
        pass_row_count=report.pass_row_count,
        watch_row_count=report.watch_row_count,
        prioritize_row_count=report.prioritize_row_count,
        source_missing_count=report.source_missing_count,
        report_status=report.report_status,
        reason_codes=report.reason_codes,
        priority_rows=rows,
    ):
        raise ValueError("validation_digest must match report")


def _validate_row_digest(row: StrategyTeamPostmortemLearningPriorityRow) -> None:
    if row.validation_digest != _row_validation_digest(
        redacted_team_ref=row.redacted_team_ref,
        redacted_market_ref=row.redacted_market_ref,
        redacted_postmortem_ref=row.redacted_postmortem_ref,
        forecast_miss=row.forecast_miss,
        notional_proxy=row.notional_proxy,
        source_failure_rate=row.source_failure_rate,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        lesson_reuse_potential=row.lesson_reuse_potential,
        source_row_count=row.source_row_count,
        source_missing=row.source_missing,
        learning_priority_score=row.learning_priority_score,
        learning_priority_status=row.learning_priority_status,
        priority_rank=row.priority_rank,
        reason_codes=row.reason_codes,
    ):
        raise ValueError("validation_digest must match row")


def _row_validation_digest(
    *,
    redacted_team_ref: str,
    redacted_market_ref: str,
    redacted_postmortem_ref: str,
    forecast_miss: Decimal,
    notional_proxy: Decimal,
    source_failure_rate: Decimal,
    resolution_ambiguity_score: Decimal,
    lesson_reuse_potential: Decimal,
    source_row_count: Decimal,
    source_missing: bool,
    learning_priority_score: Decimal,
    learning_priority_status: str,
    priority_rank: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    return _validation_digest(
        (
            "row",
            redacted_team_ref,
            redacted_market_ref,
            redacted_postmortem_ref,
            str(forecast_miss),
            str(notional_proxy),
            str(source_failure_rate),
            str(resolution_ambiguity_score),
            str(lesson_reuse_potential),
            str(source_row_count),
            str(source_missing),
            str(learning_priority_score),
            learning_priority_status,
            str(priority_rank),
            ",".join(reason_codes),
        ),
    )


def _report_validation_digest(
    *,
    generated_at: datetime,
    config_version: str,
    source_signal_count: Decimal,
    priority_row_count: Decimal,
    pass_row_count: Decimal,
    watch_row_count: Decimal,
    prioritize_row_count: Decimal,
    source_missing_count: Decimal,
    report_status: str,
    reason_codes: tuple[str, ...],
    priority_rows: tuple[StrategyTeamPostmortemLearningPriorityRow, ...],
) -> str:
    return _validation_digest(
        (
            "report",
            _as_utc("generated_at", generated_at).isoformat(),
            config_version,
            str(source_signal_count),
            str(priority_row_count),
            str(pass_row_count),
            str(watch_row_count),
            str(prioritize_row_count),
            str(source_missing_count),
            report_status,
            ",".join(reason_codes),
            *(row.validation_digest for row in priority_rows),
        ),
    )


def _validation_digest(parts: tuple[str, ...]) -> str:
    return f"{VALIDATION_DIGEST_PREFIX}{sha256(chr(10).join(parts).encode('utf-8')).hexdigest()}"


def _json_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        if not _is_public_payload_dataclass(value):
            raise ValueError("payload dataclass values are not supported")
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("JSON datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        if type(value) is not dict:
            raise ValueError("payload must use plain dict values")
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)):
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if not _is_public_payload_dataclass(value):
            raise ValueError(f"{label} dataclass values are not supported")
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if isinstance(value, dict):
        if type(value) is not dict:
            raise ValueError(f"{label} must use plain dict values")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _require_recursive_paper_only_flags(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if not _is_public_payload_dataclass(value):
            raise ValueError(f"{label} dataclass values are not supported")
        require_paper_only_flags(label, value)
        _require_recursive_paper_only_flags(label, asdict(value))
        return
    if type(value) is dict:
        if any(key in value for key in ("paper_only", "report_only", "readonly")):
            require_paper_only_flags(label, _DictFlags(value))
        for item in value.values():
            _require_recursive_paper_only_flags(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _require_recursive_paper_only_flags(label, item)


def _is_public_payload_dataclass(value: object) -> bool:
    return type(value) in (
        StrategyTeamPostmortemLearningPriorityConfig,
        StrategyTeamPostmortemLearningPrioritySignal,
        StrategyTeamPostmortemLearningPriorityRow,
        StrategyTeamPostmortemLearningPriorityReport,
        _DictFlags,
    )


def _reject_unsafe_public_text(label: str, value: str) -> None:
    if _has_fragment(value, _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


def _has_fragment(value: str, fragments: frozenset[str]) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in fragments)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_nonnegative_money(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_MONEY_QUANTUM)
    if quantized < _ZERO_MONEY:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_positive_money(field_name: str, value: object) -> Decimal:
    quantized = _normalize_nonnegative_money(field_name, value)
    if quantized == _ZERO_MONEY:
        raise ValueError(f"{field_name} must be positive")
    return quantized


def _normalize_nonnegative_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_RATIO_QUANTUM)
    if quantized < _ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _require_reason_code(value: object) -> None:
    if type(value) is not str:
        raise ValueError("reason_codes must contain strings")
    if value.strip() != value or not value:
        raise ValueError("reason_codes must contain canonical strings")
    if value != value.lower() or value[0] == "_" or value[-1] == "_":
        raise ValueError("reason_codes must be lowercase snake_case strings")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError("reason_codes must be lowercase snake_case strings")
    _reject_unsafe_public_text("reason_codes", value)


def _require_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not value.startswith(VALIDATION_DIGEST_PREFIX):
        raise ValueError(f"{field_name} must be a validation digest")
    digest_value = value[len(VALIDATION_DIGEST_PREFIX) :]
    if (
        len(digest_value) != 64
        or digest_value != digest_value.lower()
        or any(character not in "0123456789abcdef" for character in digest_value)
    ):
        raise ValueError(f"{field_name} must be a validation digest")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_redacted_ref(field_name: str, value: object, prefix: str) -> None:
    _require_canonical_string(field_name, value)
    if not value.startswith(prefix) or not value.endswith(">"):
        raise ValueError(f"{field_name} must be redacted")
    opaque_id = value[len(prefix) : -1]
    if len(opaque_id) != 3 or not opaque_id.isdecimal():
        raise ValueError(f"{field_name} must be redacted")


__all__ = (
    "DEFAULT_STRATEGY_TEAM_POSTMORTEM_LEARNING_PRIORITY_CONFIG_VERSION",
    "LEARNING_PRIORITY_STATUSES",
    "StrategyTeamPostmortemLearningPriorityConfig",
    "StrategyTeamPostmortemLearningPrioritySignal",
    "StrategyTeamPostmortemLearningPriorityRow",
    "StrategyTeamPostmortemLearningPriorityReport",
    "build_strategy_team_postmortem_learning_priority_report",
    "strategy_team_postmortem_learning_priority_payload",
)
