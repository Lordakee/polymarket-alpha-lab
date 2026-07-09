"""Pure scorecard drift report for research strategy teams."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_STRATEGY_TEAM_SCORECARD_DRIFT_CONFIG_VERSION = (
    "research-strategy-team-scorecard-drift-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
STATUS_RANK = {"pass": 0, "watch": 1, "block": 2}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"


def _term(*parts: str) -> str:
    return "".join(parts)


_EXTRA_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _term("candidate", "_id"),
        _term("mar", "ket_id"),
        _term("mar", "ket_slug"),
        _term("slug"),
        _term("que", "stion"),
        _term("source", "_url"),
        _term("source", "_text"),
        _term("http"),
        _term("u", "rl"),
        _term("d", "sn"),
        _term("table", "_name"),
        _term("private", "_to", "ken"),
        _term("to", "ken"),
        _term("sec", "ret"),
        _term("sub", "ject_ref"),
    ),
)
UNSAFE_PUBLIC_FRAGMENTS = (
    UNSAFE_SURFACE_FIELD_FRAGMENTS | _EXTRA_UNSAFE_PUBLIC_FRAGMENTS
)
ROW_GUARD_REASONS = (
    "score_drop_block",
    "status_regression_block",
    "score_drop_watch",
    "snapshot_stale_watch",
    "status_regression_watch",
)
REPORT_REASON_RANK = {
    "scorecard_drift_block": 0,
    "scorecard_drift_watch": 1,
    "scorecard_drift_clear": 2,
    "score_drop_block": 3,
    "score_drop_watch": 4,
    "snapshot_stale_watch": 5,
    "status_regression_block": 6,
    "status_regression_watch": 7,
}


@dataclass(frozen=True)
class ResearchStrategyTeamScorecardDriftConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_TEAM_SCORECARD_DRIFT_CONFIG_VERSION
    watch_score_drop: Decimal = Decimal("0.100000")
    block_score_drop: Decimal = Decimal("0.250000")
    max_snapshot_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_score_drop",
            "block_score_drop",
            "max_snapshot_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_score_drop > self.block_score_drop:
            raise ValueError("watch_score_drop must not exceed block_score_drop")
        require_paper_only_flags("ResearchStrategyTeamScorecardDriftConfig", self)
        _reject_unsafe_public_payload("ResearchStrategyTeamScorecardDriftConfig", self)


@dataclass(frozen=True)
class ResearchStrategyTeamScorecardDriftInput:
    subject_ref: str
    baseline_score: Decimal
    current_score: Decimal
    baseline_status: str
    current_status: str
    baseline_observed_at: datetime
    current_observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_private_ref("subject_ref", self.subject_ref)
        object.__setattr__(
            self,
            "baseline_score",
            _normalize_ratio("baseline_score", self.baseline_score),
        )
        object.__setattr__(
            self,
            "current_score",
            _normalize_ratio("current_score", self.current_score),
        )
        _require_status("baseline_status", self.baseline_status)
        _require_status("current_status", self.current_status)
        object.__setattr__(
            self,
            "baseline_observed_at",
            _as_utc("baseline_observed_at", self.baseline_observed_at),
        )
        object.__setattr__(
            self,
            "current_observed_at",
            _as_utc("current_observed_at", self.current_observed_at),
        )
        if self.current_observed_at < self.baseline_observed_at:
            raise ValueError("current_observed_at must not precede baseline_observed_at")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("ResearchStrategyTeamScorecardDriftInput", self)


@dataclass(frozen=True)
class ResearchStrategyTeamScorecardDriftRow:
    subject_key: str
    drift_status: str
    baseline_score: Decimal
    current_score: Decimal
    score_delta: Decimal
    score_drop: Decimal
    baseline_status: str
    current_status: str
    status_drift: Decimal
    baseline_observed_at: datetime
    current_observed_at: datetime
    snapshot_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_subject_key("subject_key", self.subject_key)
        _require_status("drift_status", self.drift_status)
        for field_name in ("baseline_score", "current_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("score_delta", "score_drop", "status_drift"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        if self.score_drop < ZERO:
            raise ValueError("score_drop must be nonnegative")
        if self.status_drift < ZERO:
            raise ValueError("status_drift must be nonnegative")
        _require_status("baseline_status", self.baseline_status)
        _require_status("current_status", self.current_status)
        object.__setattr__(
            self,
            "baseline_observed_at",
            _as_utc("baseline_observed_at", self.baseline_observed_at),
        )
        object.__setattr__(
            self,
            "current_observed_at",
            _as_utc("current_observed_at", self.current_observed_at),
        )
        object.__setattr__(
            self,
            "snapshot_age_seconds",
            _normalize_nonnegative_decimal(
                "snapshot_age_seconds",
                self.snapshot_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("ResearchStrategyTeamScorecardDriftRow", self)
        _reject_unsafe_public_payload("ResearchStrategyTeamScorecardDriftRow", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchStrategyTeamScorecardDriftReasonCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        require_paper_only_flags("ResearchStrategyTeamScorecardDriftReasonCount", self)
        _reject_unsafe_public_payload("ResearchStrategyTeamScorecardDriftReasonCount", self)


@dataclass(frozen=True)
class ResearchStrategyTeamScorecardDriftReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    maximum_score_drop: Decimal
    average_score_delta: Decimal
    stale_snapshot_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyTeamScorecardDriftReasonCount, ...]
    rows: tuple[ResearchStrategyTeamScorecardDriftRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_snapshot_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("maximum_score_drop", "average_score_delta"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        if self.maximum_score_drop < ZERO:
            raise ValueError("maximum_score_drop must be nonnegative")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest(
            DERIVED_VALIDATION_DIGEST_FIELD,
            self.derived_validation_digest,
        )
        require_paper_only_flags("ResearchStrategyTeamScorecardDriftReport", self)
        _reject_unsafe_public_payload("ResearchStrategyTeamScorecardDriftReport", self)
        _validate_report(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _reject_unsafe_public_payload("ResearchStrategyTeamScorecardDriftReport.payload", payload)
        _validate_public_payload_digest(payload)
        return payload


def build_research_strategy_team_scorecard_drift_report(
    snapshots: Iterable[ResearchStrategyTeamScorecardDriftInput],
    *,
    config: ResearchStrategyTeamScorecardDriftConfig,
    generated_at: datetime,
) -> ResearchStrategyTeamScorecardDriftReport:
    if type(config) is not ResearchStrategyTeamScorecardDriftConfig:
        raise ValueError("config must be a ResearchStrategyTeamScorecardDriftConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    snapshot_rows = _normalize_snapshots(snapshots)
    rows = tuple(
        sorted(
            (
                _drift_row(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in snapshot_rows
            ),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "row_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "maximum_score_drop": _max_decimal(tuple(row.score_drop for row in rows)),
        "average_score_delta": _average_delta(rows),
        "stale_snapshot_count": _count(
            sum(1 for row in rows if "snapshot_stale_watch" in row.reason_codes),
        ),
        "status": _rollup_status(tuple(row.drift_status for row in rows)),
        "reason_codes": _rollup_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyTeamScorecardDriftReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_team_scorecard_drift_payload(
    report: ResearchStrategyTeamScorecardDriftReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyTeamScorecardDriftReport:
        require_paper_only_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = report.payload
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategyTeamScorecardDriftReport or payload")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _validate_public_payload_digest(payload)
    if type(report) is dict:
        return _report_from_payload(payload).payload
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


def _report_from_payload(payload: dict[str, Any]) -> ResearchStrategyTeamScorecardDriftReport:
    return ResearchStrategyTeamScorecardDriftReport(
        generated_at=_payload_datetime(payload, "generated_at"),
        config_version=_payload_string(payload, "config_version"),
        row_count=_payload_decimal(payload, "row_count"),
        pass_count=_payload_decimal(payload, "pass_count"),
        watch_count=_payload_decimal(payload, "watch_count"),
        block_count=_payload_decimal(payload, "block_count"),
        maximum_score_drop=_payload_decimal(payload, "maximum_score_drop"),
        average_score_delta=_payload_decimal(payload, "average_score_delta"),
        stale_snapshot_count=_payload_decimal(payload, "stale_snapshot_count"),
        status=_payload_string(payload, "status"),
        reason_codes=_payload_string_tuple(payload, "reason_codes"),
        reason_code_counts=tuple(
            _reason_count_from_payload(item)
            for item in _payload_object_list(payload, "reason_code_counts")
        ),
        rows=tuple(
            _row_from_payload(item)
            for item in _payload_object_list(payload, "rows")
        ),
        derived_validation_digest=_payload_string(
            payload,
            DERIVED_VALIDATION_DIGEST_FIELD,
        ),
        paper_only=_payload_true(payload, "paper_only"),
        report_only=_payload_true(payload, "report_only"),
        readonly=_payload_true(payload, "readonly"),
    )


def _row_from_payload(payload: dict[str, Any]) -> ResearchStrategyTeamScorecardDriftRow:
    return ResearchStrategyTeamScorecardDriftRow(
        subject_key=_payload_string(payload, "subject_key"),
        drift_status=_payload_string(payload, "drift_status"),
        baseline_score=_payload_decimal(payload, "baseline_score"),
        current_score=_payload_decimal(payload, "current_score"),
        score_delta=_payload_decimal(payload, "score_delta"),
        score_drop=_payload_decimal(payload, "score_drop"),
        baseline_status=_payload_string(payload, "baseline_status"),
        current_status=_payload_string(payload, "current_status"),
        status_drift=_payload_decimal(payload, "status_drift"),
        baseline_observed_at=_payload_datetime(payload, "baseline_observed_at"),
        current_observed_at=_payload_datetime(payload, "current_observed_at"),
        snapshot_age_seconds=_payload_decimal(payload, "snapshot_age_seconds"),
        reason_codes=_payload_string_tuple(payload, "reason_codes"),
        paper_only=_payload_true(payload, "paper_only"),
        report_only=_payload_true(payload, "report_only"),
        readonly=_payload_true(payload, "readonly"),
    )


def _reason_count_from_payload(
    payload: dict[str, Any],
) -> ResearchStrategyTeamScorecardDriftReasonCount:
    return ResearchStrategyTeamScorecardDriftReasonCount(
        reason_code=_payload_string(payload, "reason_code"),
        count=_payload_decimal(payload, "count"),
        paper_only=_payload_true(payload, "paper_only"),
        report_only=_payload_true(payload, "report_only"),
        readonly=_payload_true(payload, "readonly"),
    )


def _payload_required(payload: dict[str, Any], field_name: str) -> Any:
    try:
        return payload[field_name]
    except KeyError as exc:
        raise ValueError(f"{field_name} is required") from exc


def _payload_string(payload: dict[str, Any], field_name: str) -> str:
    value = _payload_required(payload, field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_true(payload: dict[str, Any], field_name: str) -> bool:
    value = _payload_required(payload, field_name)
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _payload_decimal(payload: dict[str, Any], field_name: str) -> Decimal:
    value = _payload_string(payload, field_name)
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _normalize_decimal(field_name, parsed)


def _payload_datetime(payload: dict[str, Any], field_name: str) -> datetime:
    value = _payload_string(payload, field_name)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_utc(field_name, parsed)


def _payload_string_tuple(payload: dict[str, Any], field_name: str) -> tuple[str, ...]:
    value = _payload_required(payload, field_name)
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    values: list[str] = []
    for item in value:
        if type(item) is not str:
            raise ValueError(f"{field_name} must contain strings")
        values.append(item)
    return tuple(values)


def _payload_object_list(
    payload: dict[str, Any],
    field_name: str,
) -> tuple[dict[str, Any], ...]:
    value = _payload_required(payload, field_name)
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    values: list[dict[str, Any]] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError(f"{field_name} must contain objects")
        values.append(item)
    return tuple(values)


def _drift_row(
    snapshot: ResearchStrategyTeamScorecardDriftInput,
    *,
    config: ResearchStrategyTeamScorecardDriftConfig,
    generated_at: datetime,
) -> ResearchStrategyTeamScorecardDriftRow:
    if snapshot.current_observed_at > generated_at:
        raise ValueError("current_observed_at must not be after generated_at")
    score_delta = _quantize(snapshot.current_score - snapshot.baseline_score)
    score_drop = _quantize(max(snapshot.baseline_score - snapshot.current_score, ZERO))
    status_drift = _count(
        max(
            STATUS_RANK[snapshot.current_status] - STATUS_RANK[snapshot.baseline_status],
            0,
        ),
    )
    snapshot_age_seconds = _age_seconds(generated_at, snapshot.current_observed_at)
    guard_reasons = _row_guard_reasons(
        score_drop=score_drop,
        status_drift=status_drift,
        snapshot_age_seconds=snapshot_age_seconds,
        config=config,
    )
    return ResearchStrategyTeamScorecardDriftRow(
        subject_key=_subject_key(snapshot.subject_ref),
        drift_status=_row_status(guard_reasons),
        baseline_score=snapshot.baseline_score,
        current_score=snapshot.current_score,
        score_delta=score_delta,
        score_drop=score_drop,
        baseline_status=snapshot.baseline_status,
        current_status=snapshot.current_status,
        status_drift=status_drift,
        baseline_observed_at=snapshot.baseline_observed_at,
        current_observed_at=snapshot.current_observed_at,
        snapshot_age_seconds=snapshot_age_seconds,
        reason_codes=_row_reason_codes(snapshot.reason_codes, guard_reasons),
    )


def _row_guard_reasons(
    *,
    score_drop: Decimal,
    status_drift: Decimal,
    snapshot_age_seconds: Decimal,
    config: ResearchStrategyTeamScorecardDriftConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if score_drop >= config.block_score_drop:
        reasons.append("score_drop_block")
    elif score_drop >= config.watch_score_drop:
        reasons.append("score_drop_watch")
    if status_drift >= Decimal("2.000000"):
        reasons.append("status_regression_block")
    elif status_drift >= Decimal("1.000000"):
        reasons.append("status_regression_watch")
    if snapshot_age_seconds > config.max_snapshot_age_seconds:
        reasons.append("snapshot_stale_watch")
    return tuple(reasons)


def _row_reason_codes(
    source_reasons: tuple[str, ...],
    guard_reasons: tuple[str, ...],
) -> tuple[str, ...]:
    if guard_reasons:
        return _normalize_reason_codes((*source_reasons, *guard_reasons))
    return _normalize_reason_codes(("scorecard_drift_clear", *source_reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _rollup_reason_codes(
    rows: tuple[ResearchStrategyTeamScorecardDriftRow, ...],
) -> tuple[str, ...]:
    status = _rollup_status(tuple(row.drift_status for row in rows))
    reasons = ["scorecard_drift_clear" if status == "pass" else f"scorecard_drift_{status}"]
    row_reasons = frozenset(reason for row in rows for reason in row.reason_codes)
    for reason in ROW_GUARD_REASONS:
        if reason in row_reasons:
            reasons.append(reason)
    return tuple(sorted(dict.fromkeys(reasons), key=_report_reason_key))


def _reason_code_counts(
    rows: tuple[ResearchStrategyTeamScorecardDriftRow, ...],
) -> tuple[ResearchStrategyTeamScorecardDriftReasonCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyTeamScorecardDriftReasonCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_snapshots(
    snapshots: Iterable[ResearchStrategyTeamScorecardDriftInput],
) -> tuple[ResearchStrategyTeamScorecardDriftInput, ...]:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be an iterable")
    try:
        rows = tuple(snapshots)
    except TypeError as exc:
        raise ValueError("snapshots must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyTeamScorecardDriftInput:
            raise ValueError(
                "snapshots must contain ResearchStrategyTeamScorecardDriftInput values",
            )
        require_paper_only_flags("snapshot", row)
        if row.subject_ref in seen:
            raise ValueError("snapshots must not contain duplicate subject refs")
        seen.add(row.subject_ref)
    return rows


def _normalize_rows(
    rows: Iterable[ResearchStrategyTeamScorecardDriftRow],
) -> tuple[ResearchStrategyTeamScorecardDriftRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyTeamScorecardDriftRow:
            raise ValueError("rows must contain ResearchStrategyTeamScorecardDriftRow values")
        require_paper_only_flags("row", row)
        if row.subject_key in seen:
            raise ValueError("rows must not contain duplicate subject keys")
        seen.add(row.subject_key)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return values


def _normalize_reason_code_counts(
    value: Iterable[ResearchStrategyTeamScorecardDriftReasonCount],
) -> tuple[ResearchStrategyTeamScorecardDriftReasonCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    previous_key: tuple[Decimal, str] | None = None
    for row in rows:
        if type(row) is not ResearchStrategyTeamScorecardDriftReasonCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        require_paper_only_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate values")
        key = (-row.count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must use deterministic sequence")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _validate_row(row: ResearchStrategyTeamScorecardDriftRow) -> None:
    if row.score_delta != _quantize(row.current_score - row.baseline_score):
        raise ValueError("score_delta must match row scores")
    if row.score_drop != _quantize(max(row.baseline_score - row.current_score, ZERO)):
        raise ValueError("score_drop must match row scores")
    expected_status_drift = _count(
        max(STATUS_RANK[row.current_status] - STATUS_RANK[row.baseline_status], 0),
    )
    if row.status_drift != expected_status_drift:
        raise ValueError("status_drift must match row statuses")
    if row.drift_status != _row_status(row.reason_codes):
        raise ValueError("drift_status must match reason_codes")
    if row.current_observed_at < row.baseline_observed_at:
        raise ValueError("current_observed_at must not precede baseline_observed_at")


def _validate_report(report: ResearchStrategyTeamScorecardDriftReport) -> None:
    rows = report.rows
    if report.row_count != _count(len(rows)):
        raise ValueError("row_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("block_count", "block"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.maximum_score_drop != _max_decimal(tuple(row.score_drop for row in rows)):
        raise ValueError("maximum_score_drop must match rows")
    if report.average_score_delta != _average_delta(rows):
        raise ValueError("average_score_delta must match rows")
    if report.stale_snapshot_count != _count(
        sum(1 for row in rows if "snapshot_stale_watch" in row.reason_codes),
    ):
        raise ValueError("stale_snapshot_count must match rows")
    if report.status != _rollup_status(tuple(row.drift_status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _report_values_without_digest(
    report: ResearchStrategyTeamScorecardDriftReport,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "row_count": report.row_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "maximum_score_drop": report.maximum_score_drop,
        "average_score_delta": report.average_score_delta,
        "stale_snapshot_count": report.stale_snapshot_count,
        "status": report.status,
        "reason_codes": report.reason_codes,
        "reason_code_counts": report.reason_code_counts,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_public_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(DERIVED_VALIDATION_DIGEST_FIELD)
    _require_sha256_digest(DERIVED_VALIDATION_DIGEST_FIELD, digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop(DERIVED_VALIDATION_DIGEST_FIELD)
    if digest != _report_digest_from_values(payload_without_digest):
        raise ValueError("derived_validation_digest must match payload")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_text(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
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
    if type(value) is dict:
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_text(item_path, key)
            if key in PHASE_FLAG_FIELDS and nested_value is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_text(path: str, value: str) -> None:
    if value.strip() != value:
        raise ValueError(f"{path} has unsafe public value")
    normalized = value.lower()
    if "://" in normalized or "?" in normalized:
        raise ValueError(f"{path} has unsafe public value")
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path} has unsafe public value")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must not contain duplicate values")
    return tuple(sorted(reason_codes, key=_row_reason_key))


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if reason_codes != tuple(sorted(reason_codes, key=_row_reason_key)):
        raise ValueError("reason_codes must use deterministic sequence")
    return reason_codes


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must not contain duplicate values")
    if reason_codes != tuple(sorted(reason_codes, key=_report_reason_key)):
        raise ValueError("reason_codes must use deterministic sequence")
    return reason_codes


def _row_reason_key(reason_code: str) -> tuple[int, str]:
    if reason_code == "scorecard_drift_clear":
        return (0, reason_code)
    if reason_code in ROW_GUARD_REASONS:
        return (2, reason_code)
    return (1, reason_code)


def _report_reason_key(reason_code: str) -> tuple[int, str]:
    return (REPORT_REASON_RANK.get(reason_code, len(REPORT_REASON_RANK)), reason_code)


def _row_sort_key(row: ResearchStrategyTeamScorecardDriftRow) -> tuple[Decimal, Decimal, str]:
    return (-STATUS_WEIGHT[row.drift_status], -row.score_drop, row.subject_key)


def _status_count(
    rows: tuple[ResearchStrategyTeamScorecardDriftRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.drift_status == status))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_decimal("max_decimal", max(values))


def _average_delta(rows: tuple[ResearchStrategyTeamScorecardDriftRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _quantize(sum((row.score_delta for row in rows), ZERO) / _count(len(rows)))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - observed_at).total_seconds()))
    age_seconds = _quantize(seconds)
    if age_seconds < ZERO:
        raise ValueError("current_observed_at must not be after generated_at")
    return age_seconds


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_text(field_name, value)


def _require_private_ref(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_subject_key(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 71 or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 key")
    _require_sha256_digest(field_name, value.removeprefix("sha256:"))


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be less than or equal to one")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _subject_key(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_SCORECARD_DRIFT_CONFIG_VERSION",
    "ResearchStrategyTeamScorecardDriftConfig",
    "ResearchStrategyTeamScorecardDriftReasonCount",
    "ResearchStrategyTeamScorecardDriftReport",
    "ResearchStrategyTeamScorecardDriftRow",
    "ResearchStrategyTeamScorecardDriftInput",
    "build_research_strategy_team_scorecard_drift_report",
    "research_strategy_team_scorecard_drift_payload",
)
