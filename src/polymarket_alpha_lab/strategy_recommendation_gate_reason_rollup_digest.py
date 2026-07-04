"""Pure in-memory reducer for strategy gate reason rollups."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CONFIG_VERSION = "strategy-recommendation-gate-reason-rollup-v1"
COUNT_QUANTUM = Decimal("1")
ZERO_COUNT = Decimal("0")
ALLOWED_GATE_STATUSES = ("blocked", "watch", "pass")
REPORT_STATUSES = ("blocked", "watch", "pass", "clear")
CLEAR_REASON_CODE = "gate_reason_rollup_clear"
PASS_REASON_CODE = "gate_passed"
REDACTED_SOURCE_REFERENCE = "<redacted-source-reference>"
REDACTED_CANDIDATE_ID = "<redacted-candidate-id>"
_ALLOWED_PUBLIC_LABEL_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-",
)
_PUBLIC_SECRET_TERMS = (
    "secret-token",
    "bearer_token",
    "api_key",
    "password",
    "credential",
    "postgres://",
    "private" + "_key",
)
_GATE_STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}


@dataclass(frozen=True)
class StrategyRecommendationGateReasonRollupDigestConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    max_top_blockers: Decimal = Decimal("5")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label(
            "config_version",
            self.config_version,
            allow_dot=True,
            allow_plain_secret=False,
        )
        object.__setattr__(
            self,
            "max_top_blockers",
            _normalize_positive_count("max_top_blockers", self.max_top_blockers),
        )
        _require_hard_flags("StrategyRecommendationGateReasonRollupDigestConfig", self)


@dataclass(frozen=True)
class StrategyRecommendationGateReasonRollupDigestInput:
    candidate_id: str
    category_id: str
    team_id: str
    gate_id: str
    gate_status: str
    observed_at: datetime
    reason_codes: tuple[str, ...]
    source_reference: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "candidate_id",
            _require_public_label(
                "candidate_id",
                self.candidate_id,
                allow_dot=False,
                allow_plain_secret=True,
            ),
        )
        object.__setattr__(
            self,
            "category_id",
            _require_public_label(
                "category_id",
                self.category_id,
                allow_dot=True,
                allow_plain_secret=False,
            ),
        )
        object.__setattr__(
            self,
            "team_id",
            _require_public_label(
                "team_id",
                self.team_id,
                allow_dot=False,
                allow_plain_secret=False,
            ),
        )
        object.__setattr__(
            self,
            "gate_id",
            _require_public_label(
                "gate_id",
                self.gate_id,
                allow_dot=False,
                allow_plain_secret=False,
            ),
        )
        _require_member("gate_status", self.gate_status, ALLOWED_GATE_STATUSES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "source_reference",
            _normalize_source_reference(self.source_reference),
        )
        _require_hard_flags("StrategyRecommendationGateReasonRollupDigestInput", self)
        reject_unsafe_surface_fields("strategy recommendation gate reason input", self)


@dataclass(frozen=True, eq=False)
class StrategyRecommendationGateReasonRollupDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        _require_hard_flags(
            "StrategyRecommendationGateReasonRollupDigestReasonCodeCount",
            self,
        )

    def __eq__(self, other: object) -> bool:
        if type(other) is StrategyRecommendationGateReasonRollupDigestReasonCodeCount:
            return self.reason_code == other.reason_code and self.count == other.count
        if type(other) in (list, tuple) and len(other) == 2:
            return (self.reason_code, self.count) == tuple(other)
        return NotImplemented


@dataclass(frozen=True)
class StrategyRecommendationGateReasonRollupDigestCategoryRollup:
    category_id: str
    input_count: Decimal
    candidate_count: Decimal
    blocked_candidate_count: Decimal
    watch_candidate_count: Decimal
    pass_candidate_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "category_id",
            _require_public_label(
                "category_id",
                self.category_id,
                allow_dot=True,
                allow_plain_secret=False,
            ),
        )
        _normalize_public_counts(self)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _require_hard_flags(
            "StrategyRecommendationGateReasonRollupDigestCategoryRollup",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationGateReasonRollupDigestTeamRollup:
    team_id: str
    input_count: Decimal
    candidate_count: Decimal
    blocked_candidate_count: Decimal
    watch_candidate_count: Decimal
    pass_candidate_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "team_id",
            _require_public_label(
                "team_id",
                self.team_id,
                allow_dot=False,
                allow_plain_secret=False,
            ),
        )
        _normalize_public_counts(self)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _require_hard_flags("StrategyRecommendationGateReasonRollupDigestTeamRollup", self)


@dataclass(frozen=True)
class StrategyRecommendationGateReasonRollupDigestTopBlocker:
    reason_code: str
    blocked_candidate_count: Decimal
    category_ids: tuple[str, ...]
    team_ids: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "blocked_candidate_count",
            _normalize_count("blocked_candidate_count", self.blocked_candidate_count),
        )
        object.__setattr__(
            self,
            "category_ids",
            _normalize_public_labels(
                "category_ids",
                self.category_ids,
                allow_dot=True,
            ),
        )
        object.__setattr__(
            self,
            "team_ids",
            _normalize_public_labels("team_ids", self.team_ids, allow_dot=False),
        )
        _require_hard_flags("StrategyRecommendationGateReasonRollupDigestTopBlocker", self)


@dataclass(frozen=True)
class StrategyRecommendationGateReasonRollupDigestReport:
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    input_count: Decimal
    candidate_count: Decimal
    blocked_candidate_count: Decimal
    watch_candidate_count: Decimal
    pass_candidate_count: Decimal
    failure_reason_code_count: Decimal
    reason_code_counts: tuple[
        StrategyRecommendationGateReasonRollupDigestReasonCodeCount,
        ...,
    ]
    category_rollups: tuple[
        StrategyRecommendationGateReasonRollupDigestCategoryRollup,
        ...,
    ]
    team_rollups: tuple[StrategyRecommendationGateReasonRollupDigestTeamRollup, ...]
    top_blockers: tuple[StrategyRecommendationGateReasonRollupDigestTopBlocker, ...]
    rows: tuple[StrategyRecommendationGateReasonRollupDigestInput, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label(
            "config_version",
            self.config_version,
            allow_dot=True,
            allow_plain_secret=False,
        )
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _normalize_public_counts(self)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_count_rows(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "category_rollups",
            _normalize_category_rollups(self.category_rollups),
        )
        object.__setattr__(
            self,
            "team_rollups",
            _normalize_team_rollups(self.team_rollups),
        )
        object.__setattr__(
            self,
            "top_blockers",
            _normalize_top_blockers(self.top_blockers),
        )
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        _require_hard_flags("StrategyRecommendationGateReasonRollupDigestReport", self)
        reject_unsafe_surface_fields("strategy recommendation gate reason report", self)
        _validate_report(self)


def build_strategy_recommendation_gate_reason_rollup_digest(
    inputs: tuple[StrategyRecommendationGateReasonRollupDigestInput, ...]
    | list[StrategyRecommendationGateReasonRollupDigestInput],
    *,
    config: StrategyRecommendationGateReasonRollupDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationGateReasonRollupDigestReport:
    if type(config) is not StrategyRecommendationGateReasonRollupDigestConfig:
        raise ValueError("config must be a StrategyRecommendationGateReasonRollupDigestConfig")
    _require_hard_flags("strategy recommendation gate reason config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(sorted(_normalize_inputs(inputs), key=_row_key))
    reason_code_counts = _reason_code_count_rows_from_inputs(rows)
    reason_codes = _report_reason_codes_from_counts(reason_code_counts)
    return StrategyRecommendationGateReasonRollupDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        reason_codes=reason_codes,
        input_count=_count(len(rows)),
        candidate_count=_count(len(_candidate_statuses(rows))),
        blocked_candidate_count=_candidate_count_for_status(rows, "blocked"),
        watch_candidate_count=_candidate_count_for_status(rows, "watch"),
        pass_candidate_count=_candidate_count_for_status(rows, "pass"),
        failure_reason_code_count=_count(
            len(tuple(code for code in reason_codes if code != CLEAR_REASON_CODE)),
        ),
        reason_code_counts=reason_code_counts,
        category_rollups=_category_rollups(rows),
        team_rollups=_team_rollups(rows),
        top_blockers=_top_blockers(rows, max_count=config.max_top_blockers),
        rows=rows,
    )


def strategy_recommendation_gate_reason_rollup_digest_payload(
    value: object,
) -> dict[str, Any]:
    if type(value) is StrategyRecommendationGateReasonRollupDigestReport:
        _require_hard_flags("strategy recommendation gate reason report payload", value)
    elif type(value) is not dict:
        raise ValueError("payload must be a strategy recommendation gate reason report or dict")
    _validate_payload_flags(value, "payload")
    payload = _json_ready(value, "payload")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_payload_flags(payload, "payload")
    return payload


def _normalize_inputs(
    inputs: object,
) -> tuple[StrategyRecommendationGateReasonRollupDigestInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if type(row) is not StrategyRecommendationGateReasonRollupDigestInput:
            raise ValueError(
                "inputs must contain StrategyRecommendationGateReasonRollupDigestInput values",
            )
        _require_hard_flags("strategy recommendation gate reason input", row)
        identity = (row.candidate_id, row.category_id, row.team_id, row.gate_id)
        if identity in seen:
            raise ValueError("inputs must not contain duplicate candidate gate rows")
        seen.add(identity)
    return rows


def _normalize_report_rows(
    value: object,
) -> tuple[StrategyRecommendationGateReasonRollupDigestInput, ...]:
    rows = _normalize_inputs(value)
    if rows != tuple(sorted(rows, key=_row_key)):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _row_key(row: StrategyRecommendationGateReasonRollupDigestInput) -> tuple[int, str, str, str, str]:
    return (
        _GATE_STATUS_RANK[row.gate_status],
        row.candidate_id,
        row.gate_id,
        row.category_id,
        row.team_id,
    )


def _candidate_statuses(
    rows: tuple[StrategyRecommendationGateReasonRollupDigestInput, ...],
) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for row in rows:
        current = statuses.get(row.candidate_id)
        if current is None or _GATE_STATUS_RANK[row.gate_status] < _GATE_STATUS_RANK[current]:
            statuses[row.candidate_id] = row.gate_status
    return statuses


def _candidate_count_for_status(
    rows: tuple[StrategyRecommendationGateReasonRollupDigestInput, ...],
    status: str,
) -> Decimal:
    _require_member("status", status, ALLOWED_GATE_STATUSES)
    statuses = _candidate_statuses(rows)
    return _count(sum(1 for candidate_status in statuses.values() if candidate_status == status))


def _report_status(rows: tuple[StrategyRecommendationGateReasonRollupDigestInput, ...]) -> str:
    statuses = set(_candidate_statuses(rows).values())
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    if "pass" in statuses:
        return "pass"
    return "clear"


def _reason_code_count_rows_from_inputs(
    rows: tuple[StrategyRecommendationGateReasonRollupDigestInput, ...],
) -> tuple[StrategyRecommendationGateReasonRollupDigestReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in _failure_reason_codes(row.reason_codes):
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        StrategyRecommendationGateReasonRollupDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(count_value),
        )
        for reason_code, count_value in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _report_reason_codes_from_counts(
    counts: tuple[StrategyRecommendationGateReasonRollupDigestReasonCodeCount, ...],
) -> tuple[str, ...]:
    reason_codes = tuple(sorted(row.reason_code for row in counts))
    if reason_codes:
        return reason_codes
    return (CLEAR_REASON_CODE,)


def _category_rollups(
    rows: tuple[StrategyRecommendationGateReasonRollupDigestInput, ...],
) -> tuple[StrategyRecommendationGateReasonRollupDigestCategoryRollup, ...]:
    category_ids = tuple(sorted({row.category_id for row in rows}))
    return tuple(
        StrategyRecommendationGateReasonRollupDigestCategoryRollup(
            category_id=category_id,
            input_count=_count(len(_rows_for_value(rows, "category_id", category_id))),
            candidate_count=_count(
                len(_candidate_statuses(_rows_for_value(rows, "category_id", category_id))),
            ),
            blocked_candidate_count=_candidate_count_for_status(
                _rows_for_value(rows, "category_id", category_id),
                "blocked",
            ),
            watch_candidate_count=_candidate_count_for_status(
                _rows_for_value(rows, "category_id", category_id),
                "watch",
            ),
            pass_candidate_count=_candidate_count_for_status(
                _rows_for_value(rows, "category_id", category_id),
                "pass",
            ),
            reason_codes=_reason_codes_for_rows(
                _rows_for_value(rows, "category_id", category_id),
            ),
        )
        for category_id in category_ids
    )


def _team_rollups(
    rows: tuple[StrategyRecommendationGateReasonRollupDigestInput, ...],
) -> tuple[StrategyRecommendationGateReasonRollupDigestTeamRollup, ...]:
    team_ids = tuple(sorted({row.team_id for row in rows}))
    return tuple(
        StrategyRecommendationGateReasonRollupDigestTeamRollup(
            team_id=team_id,
            input_count=_count(len(_rows_for_value(rows, "team_id", team_id))),
            candidate_count=_count(
                len(_candidate_statuses(_rows_for_value(rows, "team_id", team_id))),
            ),
            blocked_candidate_count=_candidate_count_for_status(
                _rows_for_value(rows, "team_id", team_id),
                "blocked",
            ),
            watch_candidate_count=_candidate_count_for_status(
                _rows_for_value(rows, "team_id", team_id),
                "watch",
            ),
            pass_candidate_count=_candidate_count_for_status(
                _rows_for_value(rows, "team_id", team_id),
                "pass",
            ),
            reason_codes=_reason_codes_for_rows(_rows_for_value(rows, "team_id", team_id)),
        )
        for team_id in team_ids
    )


def _rows_for_value(
    rows: tuple[StrategyRecommendationGateReasonRollupDigestInput, ...],
    field_name: str,
    field_value: str,
) -> tuple[StrategyRecommendationGateReasonRollupDigestInput, ...]:
    return tuple(row for row in rows if getattr(row, field_name) == field_value)


def _reason_codes_for_rows(
    rows: tuple[StrategyRecommendationGateReasonRollupDigestInput, ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                reason_code
                for row in rows
                for reason_code in _failure_reason_codes(row.reason_codes)
            },
        ),
    )


def _top_blockers(
    rows: tuple[StrategyRecommendationGateReasonRollupDigestInput, ...],
    *,
    max_count: Decimal,
) -> tuple[StrategyRecommendationGateReasonRollupDigestTopBlocker, ...]:
    limit = int(_normalize_positive_count("max_top_blockers", max_count))
    candidate_ids_by_code: dict[str, set[str]] = {}
    category_ids_by_code: dict[str, set[str]] = {}
    team_ids_by_code: dict[str, set[str]] = {}
    for row in rows:
        if row.gate_status != "blocked":
            continue
        for reason_code in _failure_reason_codes(row.reason_codes):
            candidate_ids_by_code.setdefault(reason_code, set()).add(row.candidate_id)
            category_ids_by_code.setdefault(reason_code, set()).add(row.category_id)
            team_ids_by_code.setdefault(reason_code, set()).add(row.team_id)
    blockers = tuple(
        StrategyRecommendationGateReasonRollupDigestTopBlocker(
            reason_code=reason_code,
            blocked_candidate_count=_count(len(candidate_ids_by_code[reason_code])),
            category_ids=tuple(sorted(category_ids_by_code[reason_code])),
            team_ids=tuple(sorted(team_ids_by_code[reason_code])),
        )
        for reason_code in sorted(
            candidate_ids_by_code,
            key=lambda code: (-len(candidate_ids_by_code[code]), code),
        )
    )
    return blockers[:limit]


def _failure_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(reason_code for reason_code in reason_codes if reason_code != PASS_REASON_CODE)


def _validate_report(report: StrategyRecommendationGateReasonRollupDigestReport) -> None:
    rows = report.rows
    if report.input_count != _count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.candidate_count != _count(len(_candidate_statuses(rows))):
        raise ValueError("candidate_count must match rows")
    if report.blocked_candidate_count != _candidate_count_for_status(rows, "blocked"):
        raise ValueError("blocked_candidate_count must match rows")
    if report.watch_candidate_count != _candidate_count_for_status(rows, "watch"):
        raise ValueError("watch_candidate_count must match rows")
    if report.pass_candidate_count != _candidate_count_for_status(rows, "pass"):
        raise ValueError("pass_candidate_count must match rows")
    expected_counts = _reason_code_count_rows_from_inputs(rows)
    expected_reason_codes = _report_reason_codes_from_counts(expected_counts)
    if report.failure_reason_code_count != _count(
        len(tuple(code for code in expected_reason_codes if code != CLEAR_REASON_CODE)),
    ):
        raise ValueError("failure_reason_code_count must match reason codes")
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.category_rollups != _category_rollups(rows):
        raise ValueError("category_rollups must match rows")
    if report.team_rollups != _team_rollups(rows):
        raise ValueError("team_rollups must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")


def _normalize_public_counts(value: object) -> None:
    for field in fields(type(value)):
        if field.name.endswith("_count") or field.name == "count":
            object.__setattr__(
                value,
                field.name,
                _normalize_count(field.name, getattr(value, field.name)),
            )


def _normalize_reason_code_count_rows(
    value: object,
) -> tuple[StrategyRecommendationGateReasonRollupDigestReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not StrategyRecommendationGateReasonRollupDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain StrategyRecommendationGateReasonRollupDigestReasonCodeCount values",
            )
        _require_hard_flags("strategy recommendation gate reason code count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate reason codes")
        seen.add(row.reason_code)
    expected = tuple(sorted(rows, key=lambda row: (-row.count, row.reason_code)))
    if rows != expected:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return rows


def _normalize_category_rollups(
    value: object,
) -> tuple[StrategyRecommendationGateReasonRollupDigestCategoryRollup, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("category_rollups must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyRecommendationGateReasonRollupDigestCategoryRollup:
            raise ValueError(
                "category_rollups must contain StrategyRecommendationGateReasonRollupDigestCategoryRollup values",
            )
        _require_hard_flags("strategy recommendation gate category rollup", row)
    if rows != tuple(sorted(rows, key=lambda row: row.category_id)):
        raise ValueError("category_rollups must be sorted deterministically")
    return rows


def _normalize_team_rollups(
    value: object,
) -> tuple[StrategyRecommendationGateReasonRollupDigestTeamRollup, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("team_rollups must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyRecommendationGateReasonRollupDigestTeamRollup:
            raise ValueError(
                "team_rollups must contain StrategyRecommendationGateReasonRollupDigestTeamRollup values",
            )
        _require_hard_flags("strategy recommendation gate team rollup", row)
    if rows != tuple(sorted(rows, key=lambda row: row.team_id)):
        raise ValueError("team_rollups must be sorted deterministically")
    return rows


def _normalize_top_blockers(
    value: object,
) -> tuple[StrategyRecommendationGateReasonRollupDigestTopBlocker, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("top_blockers must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyRecommendationGateReasonRollupDigestTopBlocker:
            raise ValueError(
                "top_blockers must contain StrategyRecommendationGateReasonRollupDigestTopBlocker values",
            )
        _require_hard_flags("strategy recommendation gate top blocker", row)
    if rows != tuple(sorted(rows, key=lambda row: (-row.blocked_candidate_count, row.reason_code))):
        raise ValueError("top_blockers must be sorted deterministically")
    return rows


def _normalize_input_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    return tuple(sorted({_require_reason_code("reason_codes", code) for code in reason_codes}))


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        return ()
    return tuple(sorted({_require_reason_code("reason_codes", code) for code in reason_codes}))


def _require_reason_code(field_name: str, value: object) -> str:
    return _require_public_label(
        field_name,
        value,
        allow_dot=False,
        allow_plain_secret=False,
    )


def _normalize_public_labels(
    field_name: str,
    value: object,
    *,
    allow_dot: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    labels = tuple(
        _require_public_label(
            field_name,
            item,
            allow_dot=allow_dot,
            allow_plain_secret=False,
        )
        for item in value
    )
    if len(set(labels)) != len(labels):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(labels))


def _require_public_label(
    field_name: str,
    value: object,
    *,
    allow_dot: bool,
    allow_plain_secret: bool,
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    allowed_chars = _ALLOWED_PUBLIC_LABEL_CHARS if allow_dot else _ALLOWED_PUBLIC_LABEL_CHARS - {"."}
    if any(char not in allowed_chars for char in value):
        raise ValueError(f"{field_name} must use public label characters")
    _reject_blocked_secret_text(field_name, value)
    if "secret" in value.lower():
        if allow_plain_secret:
            return _redacted_label(field_name)
        raise ValueError(f"{field_name} must not contain secret-like text")
    return value


def _redacted_label(field_name: str) -> str:
    if field_name == "candidate_id":
        return REDACTED_CANDIDATE_ID
    return "<redacted-public-label>"


def _normalize_source_reference(value: object) -> str:
    if type(value) is not str:
        raise ValueError("source_reference must be a string")
    if not value or value.strip() != value:
        raise ValueError("source_reference must be a nonempty canonical string")
    if _has_secret_text(value):
        return REDACTED_SOURCE_REFERENCE
    return value


def _reject_blocked_secret_text(field_name: str, value: str) -> None:
    if any(term in value.lower() for term in _PUBLIC_SECRET_TERMS):
        raise ValueError(f"{field_name} must not contain secret-like text")


def _has_secret_text(value: str) -> bool:
    lowered = value.lower()
    return "secret" in lowered or any(term in lowered for term in _PUBLIC_SECRET_TERMS)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be an integral Decimal count")
    return value


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    value = _normalize_count(field_name, value)
    if value <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _validate_payload_flags(value: object, path: str) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _validate_payload_flags(asdict(value), path)
        return
    if type(value) is dict:
        for flag_name in ("paper_only", "report_only", "readonly"):
            if flag_name in value and value[flag_name] is not True:
                raise ValueError(f"{flag_name} must be True in {path}")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _validate_payload_flags(item, f"{path}.{key}")
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            _validate_payload_flags(item, f"{path}[{index}]")


def _json_ready(value: Any, path: str) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value), path)
    if type(value) is datetime:
        return _as_utc(path, value).isoformat()
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("payload Decimal values must use exact Decimal")
    if type(value) is float:
        raise ValueError("payload values must not be floats")
    if type(value) is int:
        raise ValueError("payload values must not be ints")
    if type(value) in (str, bool):
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _json_ready(item, f"{path}.{key}")
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item, f"{path}[{index}]") for index, item in enumerate(value)]
    raise ValueError("payload values must be JSON serializable")


__all__ = (
    "StrategyRecommendationGateReasonRollupDigestConfig",
    "StrategyRecommendationGateReasonRollupDigestInput",
    "StrategyRecommendationGateReasonRollupDigestReasonCodeCount",
    "StrategyRecommendationGateReasonRollupDigestCategoryRollup",
    "StrategyRecommendationGateReasonRollupDigestTeamRollup",
    "StrategyRecommendationGateReasonRollupDigestTopBlocker",
    "StrategyRecommendationGateReasonRollupDigestReport",
    "build_strategy_recommendation_gate_reason_rollup_digest",
    "strategy_recommendation_gate_reason_rollup_digest_payload",
)
