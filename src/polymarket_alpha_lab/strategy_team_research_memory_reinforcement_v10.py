from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_TEAM_RESEARCH_MEMORY_REINFORCEMENT_CONFIG_VERSION = (
    "strategy-team-research-memory-reinforcement-v10"
)
REINFORCEMENT_STATUSES = ("pass", "watch", "reinforce")

_COUNT_QUANTUM = Decimal("1")
_RATIO_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ONE_COUNT = Decimal("1")
_ZERO_RATIO = Decimal("0.000000")
_DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
_STATUS_RANK = {"reinforce": 0, "watch": 1, "pass": 2}
_VALIDATION_DIGEST_PREFIX = "tmrmr-v10:"
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
class StrategyTeamResearchMemoryReinforcementConfig:
    config_version: str = (
        DEFAULT_STRATEGY_TEAM_RESEARCH_MEMORY_REINFORCEMENT_CONFIG_VERSION
    )
    high_outcome_error_threshold: Decimal = Decimal("0.150000")
    repeated_source_failure_threshold: Decimal = Decimal("3")
    stale_playbook_days_threshold: Decimal = Decimal("30")
    domain_drift_threshold: Decimal = Decimal("0.200000")
    review_backlog_threshold: Decimal = Decimal("5")
    source_failure_score_weight: Decimal = Decimal("0.306667")
    stale_playbook_score_weight: Decimal = Decimal("0.350000")
    review_backlog_score_weight: Decimal = Decimal("0.236508")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyTeamResearchMemoryReinforcementConfig:
            raise ValueError("config must be a StrategyTeamResearchMemoryReinforcementConfig")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "high_outcome_error_threshold",
            "domain_drift_threshold",
            "source_failure_score_weight",
            "stale_playbook_score_weight",
            "review_backlog_score_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "repeated_source_failure_threshold",
            "stale_playbook_days_threshold",
            "review_backlog_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class StrategyTeamResearchMemoryReinforcementSignal:
    team_id: str = field(repr=False)
    lesson_id: str = field(repr=False)
    domain_id: str = field(repr=False)
    recent_outcome_error: Decimal
    source_failure_count: Decimal
    days_since_playbook_review: Decimal
    domain_drift_score: Decimal
    review_backlog_count: Decimal
    source_row_count: Decimal = _ONE_COUNT
    source_missing: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyTeamResearchMemoryReinforcementSignal:
            raise ValueError("signal must be a StrategyTeamResearchMemoryReinforcementSignal")
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("lesson_id", self.lesson_id)
        _require_canonical_string("domain_id", self.domain_id)
        for field_name in ("recent_outcome_error", "domain_drift_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_failure_count",
            "days_since_playbook_review",
            "review_backlog_count",
            "source_row_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if type(self.source_missing) is not bool:
            raise ValueError("source_missing must be a bool")
        require_paper_only_flags("signal", self)


@dataclass(frozen=True)
class StrategyTeamResearchMemoryReinforcementRow:
    redacted_team_ref: str
    redacted_lesson_ref: str
    redacted_domain_ref: str
    recent_outcome_error: Decimal
    source_failure_count: Decimal
    days_since_playbook_review: Decimal
    domain_drift_score: Decimal
    review_backlog_count: Decimal
    source_row_count: Decimal
    source_missing: bool
    memory_reinforcement_score: Decimal
    reinforcement_status: str
    priority_rank: Decimal
    reason_codes: tuple[str, ...]
    validation_digest: str = field(default="", init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyTeamResearchMemoryReinforcementRow:
            raise ValueError("row must be a StrategyTeamResearchMemoryReinforcementRow")
        _require_redacted_ref("redacted_team_ref", self.redacted_team_ref, "<redacted-team-")
        _require_redacted_ref(
            "redacted_lesson_ref",
            self.redacted_lesson_ref,
            "<redacted-lesson-",
        )
        _require_redacted_ref(
            "redacted_domain_ref",
            self.redacted_domain_ref,
            "<redacted-domain-",
        )
        for field_name in (
            "recent_outcome_error",
            "domain_drift_score",
            "memory_reinforcement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_failure_count",
            "days_since_playbook_review",
            "review_backlog_count",
            "source_row_count",
            "priority_rank",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if type(self.source_missing) is not bool:
            raise ValueError("source_missing must be a bool")
        _require_member("reinforcement_status", self.reinforcement_status, REINFORCEMENT_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "validation_digest", _row_validation_digest(self))
        _require_row_validation_digest(self)
        require_paper_only_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class StrategyTeamResearchMemoryReinforcementReport:
    generated_at: datetime
    config_version: str
    source_signal_count: Decimal
    reinforcement_row_count: Decimal
    pass_row_count: Decimal
    watch_row_count: Decimal
    reinforce_row_count: Decimal
    source_missing_count: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reinforcement_rows: tuple[StrategyTeamResearchMemoryReinforcementRow, ...]
    validation_digest: str = field(default="", init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyTeamResearchMemoryReinforcementReport:
            raise ValueError("report must be a StrategyTeamResearchMemoryReinforcementReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_signal_count",
            "reinforcement_row_count",
            "pass_row_count",
            "watch_row_count",
            "reinforce_row_count",
            "source_missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, REINFORCEMENT_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        rows = tuple(self.reinforcement_rows)
        for row in rows:
            if type(row) is not StrategyTeamResearchMemoryReinforcementRow:
                raise ValueError("reinforcement_rows must contain reinforcement row values")
            _require_row_validation_digest(row)
            require_paper_only_flags("row", row)
        object.__setattr__(self, "reinforcement_rows", rows)
        _validate_report(self)
        object.__setattr__(self, "validation_digest", _report_validation_digest(self))
        _require_report_validation_digest(self)
        _reject_unsafe_public_payload("report", self)
        require_paper_only_flags("report", self)


def build_strategy_team_research_memory_reinforcement_report(
    signals: (
        list[StrategyTeamResearchMemoryReinforcementSignal]
        | tuple[StrategyTeamResearchMemoryReinforcementSignal, ...]
    ),
    *,
    config: StrategyTeamResearchMemoryReinforcementConfig,
    generated_at: datetime,
) -> StrategyTeamResearchMemoryReinforcementReport:
    if type(config) is not StrategyTeamResearchMemoryReinforcementConfig:
        raise ValueError("config must be a StrategyTeamResearchMemoryReinforcementConfig")
    require_paper_only_flags("config", config)
    normalized_signals = _normalize_signals(signals)
    team_refs = _redaction_map(tuple(signal.team_id for signal in normalized_signals), "team")
    lesson_refs = _redaction_map(
        tuple(signal.lesson_id for signal in normalized_signals),
        "lesson",
    )
    domain_refs = _redaction_map(
        tuple(signal.domain_id for signal in normalized_signals),
        "domain",
    )
    ranked_rows = tuple(
        sorted(
            (
                _row_from_signal(
                    signal,
                    config=config,
                    redacted_team_ref=team_refs[signal.team_id],
                    redacted_lesson_ref=lesson_refs[signal.lesson_id],
                    redacted_domain_ref=domain_refs[signal.domain_id],
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
    pass_row_count = _count(sum(1 for row in rows if row.reinforcement_status == "pass"))
    watch_row_count = _count(sum(1 for row in rows if row.reinforcement_status == "watch"))
    reinforce_row_count = _count(
        sum(1 for row in rows if row.reinforcement_status == "reinforce"),
    )
    source_missing_count = _count(sum(1 for row in rows if row.source_missing))
    report_status = _report_status(rows)

    return StrategyTeamResearchMemoryReinforcementReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_signal_count=_count(len(normalized_signals)),
        reinforcement_row_count=_count(len(rows)),
        pass_row_count=pass_row_count,
        watch_row_count=watch_row_count,
        reinforce_row_count=reinforce_row_count,
        source_missing_count=source_missing_count,
        report_status=report_status,
        reason_codes=_report_reason_codes(
            report_status,
            source_missing_count=source_missing_count,
        ),
        reinforcement_rows=rows,
    )


def strategy_team_research_memory_reinforcement_payload(
    report: StrategyTeamResearchMemoryReinforcementReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyTeamResearchMemoryReinforcementReport:
        require_paper_only_flags("report", report)
        _validate_report(report)
        _require_report_validation_digest(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a StrategyTeamResearchMemoryReinforcementReport")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
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
        list[StrategyTeamResearchMemoryReinforcementSignal]
        | tuple[StrategyTeamResearchMemoryReinforcementSignal, ...]
    ),
) -> tuple[StrategyTeamResearchMemoryReinforcementSignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    seen_pairs: set[tuple[str, str]] = set()
    for signal in normalized:
        if type(signal) is not StrategyTeamResearchMemoryReinforcementSignal:
            raise ValueError("signals must contain team memory reinforcement signal values")
        require_paper_only_flags("signal", signal)
        pair = (signal.team_id, signal.lesson_id)
        if pair in seen_pairs:
            raise ValueError("signals must not contain duplicate team lesson pairs")
        seen_pairs.add(pair)
    return normalized


def _row_from_signal(
    signal: StrategyTeamResearchMemoryReinforcementSignal,
    *,
    config: StrategyTeamResearchMemoryReinforcementConfig,
    redacted_team_ref: str,
    redacted_lesson_ref: str,
    redacted_domain_ref: str,
) -> StrategyTeamResearchMemoryReinforcementRow:
    reason_codes = _row_reason_codes(signal, config)
    status = _row_status(signal, reason_codes)
    return StrategyTeamResearchMemoryReinforcementRow(
        redacted_team_ref=redacted_team_ref,
        redacted_lesson_ref=redacted_lesson_ref,
        redacted_domain_ref=redacted_domain_ref,
        recent_outcome_error=signal.recent_outcome_error,
        source_failure_count=signal.source_failure_count,
        days_since_playbook_review=signal.days_since_playbook_review,
        domain_drift_score=signal.domain_drift_score,
        review_backlog_count=signal.review_backlog_count,
        source_row_count=signal.source_row_count,
        source_missing=signal.source_missing,
        memory_reinforcement_score=_reinforcement_score(signal, config),
        reinforcement_status=status,
        priority_rank=_ZERO_COUNT,
        reason_codes=reason_codes,
    )


def _row_with_priority(
    row: StrategyTeamResearchMemoryReinforcementRow,
    priority_rank: Decimal,
) -> StrategyTeamResearchMemoryReinforcementRow:
    return StrategyTeamResearchMemoryReinforcementRow(
        redacted_team_ref=row.redacted_team_ref,
        redacted_lesson_ref=row.redacted_lesson_ref,
        redacted_domain_ref=row.redacted_domain_ref,
        recent_outcome_error=row.recent_outcome_error,
        source_failure_count=row.source_failure_count,
        days_since_playbook_review=row.days_since_playbook_review,
        domain_drift_score=row.domain_drift_score,
        review_backlog_count=row.review_backlog_count,
        source_row_count=row.source_row_count,
        source_missing=row.source_missing,
        memory_reinforcement_score=row.memory_reinforcement_score,
        reinforcement_status=row.reinforcement_status,
        priority_rank=priority_rank,
        reason_codes=row.reason_codes,
    )


def _reinforcement_score(
    signal: StrategyTeamResearchMemoryReinforcementSignal,
    config: StrategyTeamResearchMemoryReinforcementConfig,
) -> Decimal:
    if signal.source_missing:
        return _ZERO_RATIO
    score = signal.recent_outcome_error + signal.domain_drift_score
    if signal.source_failure_count >= config.repeated_source_failure_threshold:
        score += _weighted_threshold_score(
            signal.source_failure_count,
            config.repeated_source_failure_threshold,
            config.source_failure_score_weight,
        )
    if signal.days_since_playbook_review >= config.stale_playbook_days_threshold:
        score += config.stale_playbook_score_weight
    if signal.review_backlog_count >= config.review_backlog_threshold:
        score += _weighted_threshold_score(
            signal.review_backlog_count,
            config.review_backlog_threshold,
            config.review_backlog_score_weight,
        )
    return _normalize_nonnegative_ratio("memory_reinforcement_score", score)


def _weighted_threshold_score(value: Decimal, threshold: Decimal, weight: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return ((value / threshold) * weight).quantize(_RATIO_QUANTUM)


def _row_reason_codes(
    signal: StrategyTeamResearchMemoryReinforcementSignal,
    config: StrategyTeamResearchMemoryReinforcementConfig,
) -> tuple[str, ...]:
    if signal.source_missing:
        return ("strategy_team_research_memory_reinforcement_source_missing",)

    reason_codes: list[str] = []
    if signal.recent_outcome_error >= config.high_outcome_error_threshold:
        reason_codes.append("outcome_error_reinforce")
    if signal.source_failure_count >= config.repeated_source_failure_threshold:
        reason_codes.append("repeated_source_failures")
    if signal.days_since_playbook_review >= config.stale_playbook_days_threshold:
        reason_codes.append("playbook_stale")
    if signal.domain_drift_score >= config.domain_drift_threshold:
        reason_codes.append("domain_drift_reinforce")
    if signal.review_backlog_count >= config.review_backlog_threshold:
        reason_codes.append("review_backlog_reinforce")
    if not reason_codes:
        reason_codes.append("team_memory_reinforcement_clear")
    return tuple(reason_codes)


def _row_status(
    signal: StrategyTeamResearchMemoryReinforcementSignal,
    reason_codes: tuple[str, ...],
) -> str:
    if signal.source_missing:
        return "watch"
    if reason_codes == ("team_memory_reinforcement_clear",):
        return "pass"
    return "reinforce"


def _report_status(rows: tuple[StrategyTeamResearchMemoryReinforcementRow, ...]) -> str:
    if any(row.reinforcement_status == "reinforce" for row in rows):
        return "reinforce"
    if any(row.reinforcement_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    report_status: str,
    *,
    source_missing_count: Decimal,
) -> tuple[str, ...]:
    if report_status == "reinforce":
        reason_codes = ["strategy_team_research_memory_reinforcement_reinforce"]
    elif report_status == "watch":
        reason_codes = ["strategy_team_research_memory_reinforcement_watch"]
    else:
        return ("strategy_team_research_memory_reinforcement_clear",)
    if source_missing_count > _ZERO_COUNT:
        reason_codes.append("strategy_team_research_memory_reinforcement_source_missing")
    return tuple(reason_codes)


def _row_key(row: StrategyTeamResearchMemoryReinforcementRow) -> tuple[int, Decimal, str, str, str]:
    return (
        _STATUS_RANK[row.reinforcement_status],
        -row.memory_reinforcement_score,
        row.redacted_team_ref,
        row.redacted_lesson_ref,
        row.redacted_domain_ref,
    )


def _redaction_map(values: tuple[str, ...], label: str) -> dict[str, str]:
    return {
        value: f"<redacted-{label}-{index:03d}>"
        for index, value in enumerate(sorted(set(values)), start=1)
    }


def _validate_report(report: StrategyTeamResearchMemoryReinforcementReport) -> None:
    rows = report.reinforcement_rows
    for row in rows:
        if type(row) is not StrategyTeamResearchMemoryReinforcementRow:
            raise ValueError("reinforcement_rows must contain reinforcement row values")
        _require_row_validation_digest(row)
        require_paper_only_flags("row", row)
    if report.reinforcement_row_count != _count(len(rows)):
        raise ValueError("reinforcement_row_count must match reinforcement_rows")
    if report.source_signal_count != report.reinforcement_row_count:
        raise ValueError("source_signal_count must match reinforcement_row_count")
    if report.pass_row_count != _count(
        sum(1 for row in rows if row.reinforcement_status == "pass"),
    ):
        raise ValueError("pass_row_count must match reinforcement_rows")
    if report.watch_row_count != _count(
        sum(1 for row in rows if row.reinforcement_status == "watch"),
    ):
        raise ValueError("watch_row_count must match reinforcement_rows")
    if report.reinforce_row_count != _count(
        sum(1 for row in rows if row.reinforcement_status == "reinforce"),
    ):
        raise ValueError("reinforce_row_count must match reinforcement_rows")
    if report.source_missing_count != _count(sum(1 for row in rows if row.source_missing)):
        raise ValueError("source_missing_count must match reinforcement_rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match reinforcement_rows")


def _row_validation_digest(row: StrategyTeamResearchMemoryReinforcementRow) -> str:
    return _validation_digest(
        (
            row.redacted_team_ref,
            row.redacted_lesson_ref,
            row.redacted_domain_ref,
            row.recent_outcome_error,
            row.source_failure_count,
            row.days_since_playbook_review,
            row.domain_drift_score,
            row.review_backlog_count,
            row.source_row_count,
            row.source_missing,
            row.memory_reinforcement_score,
            row.reinforcement_status,
            row.priority_rank,
            row.reason_codes,
            row.paper_only,
            row.report_only,
            row.readonly,
        ),
    )


def _report_validation_digest(report: StrategyTeamResearchMemoryReinforcementReport) -> str:
    return _validation_digest(
        (
            report.generated_at,
            report.config_version,
            report.source_signal_count,
            report.reinforcement_row_count,
            report.pass_row_count,
            report.watch_row_count,
            report.reinforce_row_count,
            report.source_missing_count,
            report.report_status,
            report.reason_codes,
            tuple(row.validation_digest for row in report.reinforcement_rows),
            report.paper_only,
            report.report_only,
            report.readonly,
        ),
    )


def _require_row_validation_digest(row: StrategyTeamResearchMemoryReinforcementRow) -> None:
    if row.validation_digest != _row_validation_digest(row):
        raise ValueError("validation_digest mismatch: row may be tampered")


def _require_report_validation_digest(
    report: StrategyTeamResearchMemoryReinforcementReport,
) -> None:
    if report.validation_digest != _report_validation_digest(report):
        raise ValueError("validation_digest mismatch: report may be tampered")


def _validation_digest(parts: tuple[object, ...]) -> str:
    material = "\n".join(_digest_part(part) for part in parts)
    return _VALIDATION_DIGEST_PREFIX + hashlib.sha256(material.encode("utf-8")).hexdigest()


def _digest_part(value: object) -> str:
    if value is None:
        return "none:"
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("validation_digest values must be finite")
        return f"decimal:{value}"
    if type(value) is datetime:
        return f"datetime:{_as_utc('validation_digest datetime', value).isoformat()}"
    if type(value) is str:
        return f"str:{len(value)}:{value}"
    if type(value) is bool:
        if value:
            return "bool:true"
        return "bool:false"
    if type(value) is tuple:
        return "tuple:[" + ",".join(_digest_part(item) for item in value) + "]"
    raise ValueError("validation_digest values must be canonical")


def _json_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        if not _is_allowed_public_dataclass(value):
            raise ValueError("unsafe payload object must use plain values")
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
            raise ValueError("unsafe payload object must use plain dict values")
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        if type(value) not in (list, tuple):
            raise ValueError("unsafe payload object must use plain sequence values")
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)):
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if not _is_allowed_public_dataclass(value):
            raise ValueError("unsafe payload object must use plain values")
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if isinstance(value, dict):
        if type(value) is not dict:
            raise ValueError("unsafe payload object must use plain dict values")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        if type(value) not in (list, tuple):
            raise ValueError("unsafe payload object must use plain sequence values")
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _is_allowed_public_dataclass(value: object) -> bool:
    return type(value) in (
        StrategyTeamResearchMemoryReinforcementConfig,
        StrategyTeamResearchMemoryReinforcementSignal,
        StrategyTeamResearchMemoryReinforcementRow,
        StrategyTeamResearchMemoryReinforcementReport,
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


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    quantized = _normalize_nonnegative_count(field_name, value)
    if quantized == _ZERO_COUNT:
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
    "DEFAULT_STRATEGY_TEAM_RESEARCH_MEMORY_REINFORCEMENT_CONFIG_VERSION",
    "REINFORCEMENT_STATUSES",
    "StrategyTeamResearchMemoryReinforcementConfig",
    "StrategyTeamResearchMemoryReinforcementSignal",
    "StrategyTeamResearchMemoryReinforcementRow",
    "StrategyTeamResearchMemoryReinforcementReport",
    "build_strategy_team_research_memory_reinforcement_report",
    "strategy_team_research_memory_reinforcement_payload",
)
