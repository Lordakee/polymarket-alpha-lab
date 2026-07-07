"""Readonly paper report for specialist research memory decay gates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_TEAM_SPECIALIST_RESEARCH_MEMORY_DECAY_GATE_V2_CONFIG_VERSION = (
    "team-specialist-research-memory-decay-gate-v2"
)
DECIMAL_CONTEXT = Context(prec=64)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
SCORE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
ZERO_SCORE = Decimal("0").quantize(SCORE_QUANTUM)
ONE_SCORE = Decimal("1").quantize(SCORE_QUANTUM)
REPORT_STATUSES = ("pass", "watch", "blocked")
ROW_STATUSES = ("blocked", "watch", "pass")
ROW_REASON_CODES = (
    "stale_research_memory",
    "outdated_playbook",
    "recent_feedback_boost",
    "research_memory_current",
)
REPORT_REASON_CODES = (
    "no_research_memory_rows_supplied",
    "stale_research_memory_present",
    "outdated_playbook_present",
    "recent_feedback_boost_present",
    "research_memory_current",
)
UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)


@dataclass(frozen=True)
class TeamSpecialistResearchMemoryDecayGateV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_RESEARCH_MEMORY_DECAY_GATE_V2_CONFIG_VERSION
    )
    stale_research_after_seconds: Decimal = Decimal("2592000.000000")
    outdated_playbook_after_seconds: Decimal = Decimal("1209600.000000")
    recent_feedback_window_seconds: Decimal = Decimal("604800.000000")
    stale_research_penalty: Decimal = Decimal("0.300000")
    outdated_playbook_penalty: Decimal = Decimal("0.250000")
    recent_feedback_boost: Decimal = Decimal("0.100000")
    min_pass_score: Decimal = Decimal("0.700000")
    min_watch_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "stale_research_after_seconds",
            "outdated_playbook_after_seconds",
            "recent_feedback_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_research_penalty",
            "outdated_playbook_penalty",
            "recent_feedback_boost",
            "min_pass_score",
            "min_watch_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        if self.min_watch_score > self.min_pass_score:
            raise ValueError("min_watch_score must not exceed min_pass_score")
        _reject_unsafe_public_payload("research memory decay config", self)
        _require_hard_flags("TeamSpecialistResearchMemoryDecayGateV2Config", self)


@dataclass(frozen=True)
class TeamSpecialistResearchMemoryDecayGateV2Memory:
    memory_id: str
    team_id: str
    category_id: str
    specialist_id: str
    playbook_id: str
    baseline_memory_score: Decimal
    latest_research_at: datetime
    playbook_updated_at: datetime
    latest_feedback_at: datetime | None
    recent_feedback_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("memory_id", self.memory_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("category_id", self.category_id)
        _require_public_string("specialist_id", self.specialist_id)
        _require_public_string("playbook_id", self.playbook_id)
        object.__setattr__(
            self,
            "baseline_memory_score",
            _normalize_score("baseline_memory_score", self.baseline_memory_score),
        )
        object.__setattr__(
            self,
            "latest_research_at",
            _as_utc("latest_research_at", self.latest_research_at),
        )
        object.__setattr__(
            self,
            "playbook_updated_at",
            _as_utc("playbook_updated_at", self.playbook_updated_at),
        )
        object.__setattr__(
            self,
            "latest_feedback_at",
            _as_optional_utc("latest_feedback_at", self.latest_feedback_at),
        )
        object.__setattr__(
            self,
            "recent_feedback_count",
            _normalize_nonnegative_count(
                "recent_feedback_count",
                self.recent_feedback_count,
            ),
        )
        _reject_unsafe_public_payload("research memory row", self)
        _require_hard_flags("TeamSpecialistResearchMemoryDecayGateV2Memory", self)


@dataclass(frozen=True)
class TeamSpecialistResearchMemoryDecayGateV2Row:
    memory_id: str
    team_id: str
    category_id: str
    specialist_id: str
    playbook_id: str
    row_status: str
    baseline_memory_score: Decimal
    research_age_seconds: Decimal
    playbook_age_seconds: Decimal
    feedback_age_seconds: Decimal | None
    recent_feedback_count: Decimal
    stale_research_penalty: Decimal
    outdated_playbook_penalty: Decimal
    recent_feedback_boost_applied: Decimal
    adjusted_memory_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("memory_id", self.memory_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("category_id", self.category_id)
        _require_public_string("specialist_id", self.specialist_id)
        _require_public_string("playbook_id", self.playbook_id)
        _require_member("row_status", self.row_status, ROW_STATUSES)
        for field_name in (
            "baseline_memory_score",
            "stale_research_penalty",
            "outdated_playbook_penalty",
            "recent_feedback_boost_applied",
            "adjusted_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "research_age_seconds",
            _normalize_nonnegative_seconds(
                "research_age_seconds",
                self.research_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "playbook_age_seconds",
            _normalize_nonnegative_seconds(
                "playbook_age_seconds",
                self.playbook_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "feedback_age_seconds",
            _normalize_optional_nonnegative_seconds(
                "feedback_age_seconds",
                self.feedback_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "recent_feedback_count",
            _normalize_nonnegative_count(
                "recent_feedback_count",
                self.recent_feedback_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _reject_unsafe_public_payload("research memory decay row", self)
        _require_hard_flags("TeamSpecialistResearchMemoryDecayGateV2Row", self)
        _validate_row(self)


@dataclass(frozen=True)
class TeamSpecialistResearchMemoryDecayGateV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    source_memory_count: Decimal
    row_count: Decimal
    team_count: Decimal
    category_count: Decimal
    specialist_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    stale_research_count: Decimal
    outdated_playbook_count: Decimal
    recent_feedback_boost_count: Decimal
    average_adjusted_memory_score: Decimal
    rows: tuple[TeamSpecialistResearchMemoryDecayGateV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        for field_name in (
            "source_memory_count",
            "row_count",
            "team_count",
            "category_count",
            "specialist_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "stale_research_count",
            "outdated_playbook_count",
            "recent_feedback_boost_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_adjusted_memory_score",
            _normalize_score(
                "average_adjusted_memory_score",
                self.average_adjusted_memory_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _reject_unsafe_public_payload("research memory decay report", self)
        _require_hard_flags("TeamSpecialistResearchMemoryDecayGateV2Report", self)
        _validate_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest_string(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_team_specialist_research_memory_decay_gate_v2(
    rows: list[TeamSpecialistResearchMemoryDecayGateV2Memory]
    | tuple[TeamSpecialistResearchMemoryDecayGateV2Memory, ...],
    *,
    config: TeamSpecialistResearchMemoryDecayGateV2Config,
    generated_at: datetime,
) -> TeamSpecialistResearchMemoryDecayGateV2Report:
    if type(config) is not TeamSpecialistResearchMemoryDecayGateV2Config:
        raise ValueError(
            "config must be a TeamSpecialistResearchMemoryDecayGateV2Config",
        )
    _require_hard_flags("TeamSpecialistResearchMemoryDecayGateV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_source_rows(rows)
    report_rows = tuple(
        sorted(
            (_row_for_memory(row, config=config, generated_at=generated_at_utc) for row in source_rows),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(report_rows, len(source_rows))
    pass_count = _status_count(report_rows, "pass")
    watch_count = _status_count(report_rows, "watch")
    blocked_count = _status_count(report_rows, "blocked")

    return TeamSpecialistResearchMemoryDecayGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(blocked_count, watch_count),
        source_memory_count=_count(len(source_rows)),
        row_count=_count(len(report_rows)),
        team_count=_count(len({row.team_id for row in report_rows})),
        category_count=_count(len({row.category_id for row in report_rows})),
        specialist_count=_count(len({row.specialist_id for row in report_rows})),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        stale_research_count=_reason_count(report_rows, "stale_research_memory"),
        outdated_playbook_count=_reason_count(report_rows, "outdated_playbook"),
        recent_feedback_boost_count=_reason_count(report_rows, "recent_feedback_boost"),
        average_adjusted_memory_score=_average_score(
            tuple(row.adjusted_memory_score for row in report_rows),
        ),
        rows=report_rows,
        reason_codes=reason_codes,
    )


def team_specialist_research_memory_decay_gate_v2_payload(
    report: TeamSpecialistResearchMemoryDecayGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistResearchMemoryDecayGateV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("research memory decay report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("research memory decay payload", report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
    else:
        raise ValueError(
            "report must be a TeamSpecialistResearchMemoryDecayGateV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("research memory decay payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
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


def _normalize_source_rows(
    value: object,
) -> tuple[TeamSpecialistResearchMemoryDecayGateV2Memory, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not TeamSpecialistResearchMemoryDecayGateV2Memory:
            raise ValueError(
                "rows must contain TeamSpecialistResearchMemoryDecayGateV2Memory values",
            )
        _require_hard_flags("TeamSpecialistResearchMemoryDecayGateV2Memory", row)
        if row.memory_id in seen_ids:
            raise ValueError("duplicate memory_id values are not allowed")
        seen_ids.add(row.memory_id)
    return rows


def _row_for_memory(
    row: TeamSpecialistResearchMemoryDecayGateV2Memory,
    *,
    config: TeamSpecialistResearchMemoryDecayGateV2Config,
    generated_at: datetime,
) -> TeamSpecialistResearchMemoryDecayGateV2Row:
    research_age_seconds = _age_seconds(row.latest_research_at, generated_at)
    playbook_age_seconds = _age_seconds(row.playbook_updated_at, generated_at)
    feedback_age_seconds = _optional_age_seconds(row.latest_feedback_at, generated_at)
    stale_penalty = (
        config.stale_research_penalty
        if research_age_seconds > config.stale_research_after_seconds
        else ZERO_SCORE
    )
    playbook_penalty = (
        config.outdated_playbook_penalty
        if playbook_age_seconds > config.outdated_playbook_after_seconds
        else ZERO_SCORE
    )
    feedback_boost = (
        config.recent_feedback_boost
        if (
            feedback_age_seconds is not None
            and feedback_age_seconds <= config.recent_feedback_window_seconds
            and row.recent_feedback_count > ZERO_COUNT
        )
        else ZERO_SCORE
    )
    adjusted_score = _clamped_score(
        row.baseline_memory_score - stale_penalty - playbook_penalty + feedback_boost,
    )
    reason_codes = _row_reason_codes(
        stale_penalty=stale_penalty,
        playbook_penalty=playbook_penalty,
        feedback_boost=feedback_boost,
    )

    return TeamSpecialistResearchMemoryDecayGateV2Row(
        memory_id=row.memory_id,
        team_id=row.team_id,
        category_id=row.category_id,
        specialist_id=row.specialist_id,
        playbook_id=row.playbook_id,
        row_status=_row_status(adjusted_score, config),
        baseline_memory_score=row.baseline_memory_score,
        research_age_seconds=research_age_seconds,
        playbook_age_seconds=playbook_age_seconds,
        feedback_age_seconds=feedback_age_seconds,
        recent_feedback_count=row.recent_feedback_count,
        stale_research_penalty=stale_penalty,
        outdated_playbook_penalty=playbook_penalty,
        recent_feedback_boost_applied=feedback_boost,
        adjusted_memory_score=adjusted_score,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    stale_penalty: Decimal,
    playbook_penalty: Decimal,
    feedback_boost: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if stale_penalty > ZERO_SCORE:
        codes.append("stale_research_memory")
    if playbook_penalty > ZERO_SCORE:
        codes.append("outdated_playbook")
    if feedback_boost > ZERO_SCORE:
        codes.append("recent_feedback_boost")
    if stale_penalty == ZERO_SCORE and playbook_penalty == ZERO_SCORE:
        codes.append("research_memory_current")
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _row_status(
    adjusted_score: Decimal,
    config: TeamSpecialistResearchMemoryDecayGateV2Config,
) -> str:
    if adjusted_score >= config.min_pass_score:
        return "pass"
    if adjusted_score >= config.min_watch_score:
        return "watch"
    return "blocked"


def _row_sort_key(
    row: TeamSpecialistResearchMemoryDecayGateV2Row,
) -> tuple[int, Decimal, str, str, str, str]:
    return (
        ROW_STATUSES.index(row.row_status),
        row.adjusted_memory_score,
        row.team_id,
        row.category_id,
        row.specialist_id,
        row.memory_id,
    )


def _report_reason_codes(
    rows: tuple[TeamSpecialistResearchMemoryDecayGateV2Row, ...],
    source_row_count: int,
) -> tuple[str, ...]:
    if source_row_count == 0:
        return ("no_research_memory_rows_supplied",)
    codes: list[str] = []
    if any("stale_research_memory" in row.reason_codes for row in rows):
        codes.append("stale_research_memory_present")
    if any("outdated_playbook" in row.reason_codes for row in rows):
        codes.append("outdated_playbook_present")
    if any("recent_feedback_boost" in row.reason_codes for row in rows):
        codes.append("recent_feedback_boost_present")
    if all(row.row_status == "pass" for row in rows):
        codes.append("research_memory_current")
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _report_status(blocked_count: Decimal, watch_count: Decimal) -> str:
    if blocked_count > ZERO_COUNT:
        return "blocked"
    if watch_count > ZERO_COUNT:
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[TeamSpecialistResearchMemoryDecayGateV2Row, ...],
    row_status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.row_status == row_status))


def _reason_count(
    rows: tuple[TeamSpecialistResearchMemoryDecayGateV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _normalize_report_rows(
    value: object,
) -> tuple[TeamSpecialistResearchMemoryDecayGateV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not TeamSpecialistResearchMemoryDecayGateV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistResearchMemoryDecayGateV2Row values",
            )
        _require_hard_flags("TeamSpecialistResearchMemoryDecayGateV2Row", row)
        if row.memory_id in seen_ids:
            raise ValueError("duplicate memory_id values are not allowed")
        seen_ids.add(row.memory_id)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _validate_row(row: TeamSpecialistResearchMemoryDecayGateV2Row) -> None:
    if row.reason_codes == ():
        raise ValueError("reason_codes must not be empty")
    if (
        "research_memory_current" in row.reason_codes
        and "stale_research_memory" in row.reason_codes
    ):
        raise ValueError("current research memory cannot be stale")
    if (
        "research_memory_current" in row.reason_codes
        and "outdated_playbook" in row.reason_codes
    ):
        raise ValueError("current research memory cannot use outdated playbook")
    expected_score = _clamped_score(
        row.baseline_memory_score
        - row.stale_research_penalty
        - row.outdated_playbook_penalty
        + row.recent_feedback_boost_applied,
    )
    if row.adjusted_memory_score != expected_score:
        raise ValueError("adjusted_memory_score must match row penalties and boosts")


def _validate_report(report: TeamSpecialistResearchMemoryDecayGateV2Report) -> None:
    if report.source_memory_count != report.row_count:
        raise ValueError("source_memory_count must match row_count")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.team_count != _count(len({row.team_id for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.category_count != _count(len({row.category_id for row in report.rows})):
        raise ValueError("category_count must match rows")
    if report.specialist_count != _count(len({row.specialist_id for row in report.rows})):
        raise ValueError("specialist_count must match rows")
    expected_counts = {
        "pass_count": _status_count(report.rows, "pass"),
        "watch_count": _status_count(report.rows, "watch"),
        "blocked_count": _status_count(report.rows, "blocked"),
        "stale_research_count": _reason_count(report.rows, "stale_research_memory"),
        "outdated_playbook_count": _reason_count(report.rows, "outdated_playbook"),
        "recent_feedback_boost_count": _reason_count(
            report.rows,
            "recent_feedback_boost",
        ),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.average_adjusted_memory_score != _average_score(
        tuple(row.adjusted_memory_score for row in report.rows),
    ):
        raise ValueError("average_adjusted_memory_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.row_count)):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status(report.blocked_count, report.watch_count):
        raise ValueError("report_status must match rows")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be present")
    _require_digest_string("derived_validation_digest", digest)
    expected = _digest_for_json_payload(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest must match report contents")


def _report_digest(report: TeamSpecialistResearchMemoryDecayGateV2Report) -> str:
    payload = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }
    return _digest_for_json_payload(_json_ready(payload))


def _digest_for_json_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    canonical_payload = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_SCORE) / _count(len(values))).quantize(SCORE_QUANTUM)


def _optional_age_seconds(value: datetime | None, generated_at: datetime) -> Decimal | None:
    if value is None:
        return None
    return _age_seconds(value, generated_at)


def _age_seconds(value: datetime, generated_at: datetime) -> Decimal:
    if value > generated_at:
        return ZERO_SECONDS
    return _seconds_decimal((generated_at - value).total_seconds())


def _seconds_decimal(value: float) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(str(value)).quantize(SECONDS_QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _clamped_score(value: Decimal) -> Decimal:
    normalized = _require_decimal("score", value).quantize(SCORE_QUANTUM)
    if normalized < ZERO_SCORE:
        return ZERO_SCORE
    if normalized > ONE_SCORE:
        return ONE_SCORE
    return normalized


def _normalize_score(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(SCORE_QUANTUM)
    if normalized < ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE_SCORE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_seconds(field_name, value)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(SECONDS_QUANTUM)
    if normalized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_seconds(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_seconds(field_name, value)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    normalized = decimal.quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != decimal:
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_member("reason_codes", code, ROW_REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in ROW_REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    return codes


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_member("reason_codes", code, REPORT_REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REPORT_REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    return codes


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    if _has_unsafe_public_term(value):
        raise ValueError(f"unsafe public value in {field_name}")


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    _require_public_string(field_name, value)
    if value not in members:
        raise ValueError(f"{field_name} must be one of {', '.join(members)}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_public_term(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_term(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_public_term(value: str) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in UNSAFE_PUBLIC_TERMS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
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
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_RESEARCH_MEMORY_DECAY_GATE_V2_CONFIG_VERSION",
    "TeamSpecialistResearchMemoryDecayGateV2Config",
    "TeamSpecialistResearchMemoryDecayGateV2Memory",
    "TeamSpecialistResearchMemoryDecayGateV2Row",
    "TeamSpecialistResearchMemoryDecayGateV2Report",
    "build_team_specialist_research_memory_decay_gate_v2",
    "team_specialist_research_memory_decay_gate_v2_payload",
)
