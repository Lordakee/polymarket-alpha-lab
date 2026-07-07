"""Report-only long-horizon performance scorecard for research teams."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_TEAM_PERFORMANCE_SCORECARD_CONFIG_VERSION",
    "ResearchTeamPerformanceScorecardConfig",
    "ResearchTeamPerformanceScorecardInput",
    "ResearchTeamPerformanceScorecardReasonCodeCount",
    "ResearchTeamPerformanceScorecardReport",
    "ResearchTeamPerformanceScorecardRow",
    "build_research_team_performance_scorecard_report",
    "research_team_performance_scorecard_payload",
)


DEFAULT_RESEARCH_TEAM_PERFORMANCE_SCORECARD_CONFIG_VERSION = (
    "research-team-performance-scorecard-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SCORE_DIMENSION_COUNT = Decimal("4.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
STATUSES = ("pass", "watch", "block")
DOMAINS = ("politics", "finance", "sports", "macro", "crypto", "economics", "general")
DERIVED_DIGEST_FIELD = "derived_validation_digest"
STATUS_WEIGHT = {
    "block": Decimal("3.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
BLOCK_REASON_CODES = frozenset(
    (
        "calibration_error_block",
        "evaluation_count_block",
        "evidence_quality_block",
        "memory_update_quality_block",
        "review_completion_rate_block",
        "team_performance_block",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "calibration_error_watch",
        "evidence_quality_watch",
        "memory_update_quality_watch",
        "review_completion_rate_watch",
        "team_performance_watch",
    ),
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        "raw",
        "candidate",
        "market",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "buy",
        "sell",
        "trade",
        "position",
        "recommend",
        "live",
        "auth",
        "wallet",
        "order",
        "mutation",
        "network",
        "database",
        "persist",
        "write",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__bases__ != (_FinalPublicDataclass,):
            raise TypeError("public dataclasses are final")


@dataclass(frozen=True)
class ResearchTeamPerformanceScorecardConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_TEAM_PERFORMANCE_SCORECARD_CONFIG_VERSION
    maximum_pass_calibration_error: Decimal = Decimal("0.100000")
    maximum_watch_calibration_error: Decimal = Decimal("0.250000")
    minimum_pass_evidence_quality: Decimal = Decimal("0.750000")
    minimum_watch_evidence_quality: Decimal = Decimal("0.500000")
    minimum_pass_review_completion_rate: Decimal = Decimal("0.800000")
    minimum_watch_review_completion_rate: Decimal = Decimal("0.600000")
    minimum_pass_memory_update_quality: Decimal = Decimal("0.750000")
    minimum_watch_memory_update_quality: Decimal = Decimal("0.500000")
    minimum_evaluation_count: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamPerformanceScorecardConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "maximum_pass_calibration_error",
            "maximum_watch_calibration_error",
            "minimum_pass_evidence_quality",
            "minimum_watch_evidence_quality",
            "minimum_pass_review_completion_rate",
            "minimum_watch_review_completion_rate",
            "minimum_pass_memory_update_quality",
            "minimum_watch_memory_update_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_evaluation_count",
            _normalize_positive_count(
                "minimum_evaluation_count",
                self.minimum_evaluation_count,
            ),
        )
        if self.maximum_pass_calibration_error > self.maximum_watch_calibration_error:
            raise ValueError(
                "maximum_pass_calibration_error must not exceed "
                "maximum_watch_calibration_error",
            )
        for pass_field, watch_field in (
            ("minimum_pass_evidence_quality", "minimum_watch_evidence_quality"),
            (
                "minimum_pass_review_completion_rate",
                "minimum_watch_review_completion_rate",
            ),
            ("minimum_pass_memory_update_quality", "minimum_watch_memory_update_quality"),
        ):
            if getattr(self, pass_field) < getattr(self, watch_field):
                raise ValueError(f"{pass_field} must not be below {watch_field}")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamPerformanceScorecardInput(_FinalPublicDataclass):
    team_id: str
    domain: str
    calibration_error: Decimal
    evidence_quality: Decimal
    review_completion_rate: Decimal
    memory_update_quality: Decimal
    evaluation_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamPerformanceScorecardInput, "input")
        _require_canonical_string("team_id", self.team_id)
        _require_domain("domain", self.domain)
        for field_name in (
            "calibration_error",
            "evidence_quality",
            "review_completion_rate",
            "memory_update_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evaluation_count",
            _normalize_nonnegative_count("evaluation_count", self.evaluation_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_order(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamPerformanceScorecardRow(_FinalPublicDataclass):
    team_id: str
    domain: str
    status: str
    calibration_error: Decimal
    calibration_score: Decimal
    evidence_quality: Decimal
    review_completion_rate: Decimal
    memory_update_quality: Decimal
    evaluation_count: Decimal
    composite_score: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamPerformanceScorecardRow, "row")
        _require_canonical_string("team_id", self.team_id)
        _require_domain("domain", self.domain)
        _require_status("status", self.status)
        for field_name in (
            "calibration_error",
            "calibration_score",
            "evidence_quality",
            "review_completion_rate",
            "memory_update_quality",
            "composite_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evaluation_count",
            _normalize_nonnegative_count("evaluation_count", self.evaluation_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_order(self.reason_codes),
        )
        _require_hard_flags("row", self)
        if self.derived_validation_digest:
            _validate_derived_digest("row", _row_digest_payload(self))
            return
        _validate_row_consistency(self)
        object.__setattr__(
            self,
            DERIVED_DIGEST_FIELD,
            _derived_digest(_row_digest_payload(self)),
        )


@dataclass(frozen=True)
class ResearchTeamPerformanceScorecardReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamPerformanceScorecardReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamPerformanceScorecardReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_composite_score: Decimal
    max_composite_score: Decimal
    min_composite_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamPerformanceScorecardReasonCodeCount, ...]
    rows: tuple[ResearchTeamPerformanceScorecardRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamPerformanceScorecardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("team_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_composite_score",
            "max_composite_score",
            "min_composite_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
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
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        if self.derived_validation_digest:
            _validate_derived_digest("report", _report_digest_payload(self))
        else:
            object.__setattr__(
                self,
                DERIVED_DIGEST_FIELD,
                _derived_digest(_report_digest_payload(self)),
            )


def build_research_team_performance_scorecard_report(
    teams: Iterable[ResearchTeamPerformanceScorecardInput],
    *,
    config: ResearchTeamPerformanceScorecardConfig,
    generated_at: datetime,
) -> ResearchTeamPerformanceScorecardReport:
    if type(config) is not ResearchTeamPerformanceScorecardConfig:
        raise ValueError("config must be a ResearchTeamPerformanceScorecardConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(teams)
    rows = tuple(
        sorted(
            (_scorecard_row(row, config=config) for row in input_rows),
            key=_row_sort_key,
        ),
    )
    return ResearchTeamPerformanceScorecardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_composite_score=_average_score(rows),
        max_composite_score=_max_score(rows),
        min_composite_score=_min_score(rows),
        status=_summary_status(rows),
        reason_codes=_summary_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_performance_scorecard_payload(
    report: ResearchTeamPerformanceScorecardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamPerformanceScorecardReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("team performance report", report)
        _validate_derived_digest("report", _report_digest_payload(report))
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("team performance payload", report)
        _reject_flag_downgrades("payload", report)
        payload = _json_ready(report)
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_public_payload_digest(payload)
    else:
        raise ValueError("report must be a ResearchTeamPerformanceScorecardReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("team performance payload", payload)
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


def _scorecard_row(
    team: ResearchTeamPerformanceScorecardInput,
    *,
    config: ResearchTeamPerformanceScorecardConfig,
) -> ResearchTeamPerformanceScorecardRow:
    calibration_score = _calibration_score(team.calibration_error)
    composite_score = _score(
        (
            calibration_score,
            team.evidence_quality,
            team.review_completion_rate,
            team.memory_update_quality,
        ),
    )
    reason_codes = _row_reason_codes(team, config=config)
    return ResearchTeamPerformanceScorecardRow(
        team_id=team.team_id,
        domain=team.domain,
        status=_row_status(reason_codes),
        calibration_error=team.calibration_error,
        calibration_score=calibration_score,
        evidence_quality=team.evidence_quality,
        review_completion_rate=team.review_completion_rate,
        memory_update_quality=team.memory_update_quality,
        evaluation_count=team.evaluation_count,
        composite_score=composite_score,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    team: ResearchTeamPerformanceScorecardInput,
    *,
    config: ResearchTeamPerformanceScorecardConfig,
) -> tuple[str, ...]:
    reason_codes = list(team.reason_codes)
    block_codes: list[str] = []
    if team.calibration_error > config.maximum_watch_calibration_error:
        block_codes.append("calibration_error_block")
    if team.evaluation_count < config.minimum_evaluation_count:
        block_codes.append("evaluation_count_block")
    if team.evidence_quality < config.minimum_watch_evidence_quality:
        block_codes.append("evidence_quality_block")
    if team.memory_update_quality < config.minimum_watch_memory_update_quality:
        block_codes.append("memory_update_quality_block")
    if team.review_completion_rate < config.minimum_watch_review_completion_rate:
        block_codes.append("review_completion_rate_block")

    watch_codes: list[str] = []
    if not block_codes:
        if team.calibration_error > config.maximum_pass_calibration_error:
            watch_codes.append("calibration_error_watch")
        if team.evidence_quality < config.minimum_pass_evidence_quality:
            watch_codes.append("evidence_quality_watch")
        if team.memory_update_quality < config.minimum_pass_memory_update_quality:
            watch_codes.append("memory_update_quality_watch")
        if team.review_completion_rate < config.minimum_pass_review_completion_rate:
            watch_codes.append("review_completion_rate_watch")

    reason_codes.extend(sorted(block_codes))
    reason_codes.extend(sorted(watch_codes))
    if block_codes:
        reason_codes.append("team_performance_block")
    elif watch_codes:
        reason_codes.append("team_performance_watch")
    else:
        reason_codes.append("team_performance_pass")
    return _normalize_reason_codes_preserving_order(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _summary_status(rows: tuple[ResearchTeamPerformanceScorecardRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchTeamPerformanceScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("team_performance_no_rows_block",)
    status = _summary_status(rows)
    row_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code
        not in {
            "team_performance_pass",
            "team_performance_watch",
            "team_performance_block",
        }
    }
    return (f"team_performance_{status}", *tuple(sorted(row_codes)))


def _reason_code_counts(
    rows: tuple[ResearchTeamPerformanceScorecardRow, ...],
) -> tuple[ResearchTeamPerformanceScorecardReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchTeamPerformanceScorecardReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _calibration_score(calibration_error: Decimal) -> Decimal:
    return _quantize(ONE - calibration_error)


def _score(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return _quantize(total / SCORE_DIMENSION_COUNT)


def _average_score(rows: tuple[ResearchTeamPerformanceScorecardRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    total = ZERO
    for row in rows:
        total = _quantize(total + row.composite_score)
    return _quantize(total / _count(len(rows)))


def _max_score(rows: tuple[ResearchTeamPerformanceScorecardRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_ratio("max_composite_score", max(row.composite_score for row in rows))


def _min_score(rows: tuple[ResearchTeamPerformanceScorecardRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_ratio("min_composite_score", min(row.composite_score for row in rows))


def _status_count(
    rows: tuple[ResearchTeamPerformanceScorecardRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _validate_row_consistency(row: ResearchTeamPerformanceScorecardRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    expected_calibration_score = _calibration_score(row.calibration_error)
    if row.calibration_score != expected_calibration_score:
        raise ValueError("calibration_score must match calibration_error")
    expected_composite_score = _score(
        (
            row.calibration_score,
            row.evidence_quality,
            row.review_completion_rate,
            row.memory_update_quality,
        ),
    )
    if row.composite_score != expected_composite_score:
        raise ValueError("composite_score must match scorecard inputs")


def _validate_report_consistency(report: ResearchTeamPerformanceScorecardReport) -> None:
    rows = report.rows
    if report.team_count != _count(len(rows)):
        raise ValueError("team_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("block_count", "block"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.average_composite_score != _average_score(rows):
        raise ValueError("average_composite_score must match rows")
    if report.max_composite_score != _max_score(rows):
        raise ValueError("max_composite_score must match rows")
    if report.min_composite_score != _min_score(rows):
        raise ValueError("min_composite_score must match rows")
    if report.status != _summary_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    teams: Iterable[ResearchTeamPerformanceScorecardInput],
) -> tuple[ResearchTeamPerformanceScorecardInput, ...]:
    if isinstance(teams, (str, bytes)):
        raise ValueError("teams must be an iterable")
    try:
        rows = tuple(teams)
    except TypeError as exc:
        raise ValueError("teams must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamPerformanceScorecardInput:
            raise ValueError(
                "teams must contain ResearchTeamPerformanceScorecardInput values",
            )
        _require_hard_flags("team", row)
        if row.team_id in seen_ids:
            raise ValueError("teams must not contain duplicate ids")
        seen_ids.add(row.team_id)
    return rows


def _normalize_rows(
    rows: Iterable[ResearchTeamPerformanceScorecardRow],
) -> tuple[ResearchTeamPerformanceScorecardRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in values:
        if type(row) is not ResearchTeamPerformanceScorecardRow:
            raise ValueError("rows must contain ResearchTeamPerformanceScorecardRow values")
        _require_hard_flags("row", row)
        _validate_derived_digest("row", _row_digest_payload(row))
        _validate_row_consistency(row)
        if row.team_id in seen_ids:
            raise ValueError("rows must not contain duplicate ids")
        seen_ids.add(row.team_id)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use stable sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchTeamPerformanceScorecardReasonCodeCount],
) -> tuple[ResearchTeamPerformanceScorecardReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    previous_code: str | None = None
    for row in values:
        if type(row) is not ResearchTeamPerformanceScorecardReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code count rows")
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate values")
        if previous_code is not None and previous_code > row.reason_code:
            raise ValueError("reason_code_counts must use stable sequence")
        previous_code = row.reason_code
        seen_codes.add(row.reason_code)
    return values


def _row_sort_key(row: ResearchTeamPerformanceScorecardRow) -> tuple[Decimal, Decimal, str]:
    return (-STATUS_WEIGHT[row.status], -_row_severity(row), row.team_id)


def _row_severity(row: ResearchTeamPerformanceScorecardRow) -> Decimal:
    return _count(
        sum(
            1
            for reason_code in row.reason_codes
            if reason_code in BLOCK_REASON_CODES or reason_code in WATCH_REASON_CODES
        ),
    )


def _validate_public_payload_digest(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    if rows is None:
        raise ValueError("rows must be present")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        _validate_derived_digest("row", row)
    _validate_derived_digest("report", payload)


def _row_digest_payload(row: ResearchTeamPerformanceScorecardRow) -> dict[str, Any]:
    return asdict(row)


def _report_digest_payload(report: ResearchTeamPerformanceScorecardReport) -> dict[str, Any]:
    return asdict(report)


def _validate_derived_digest(label: str, payload: dict[str, Any]) -> None:
    observed = payload.get(DERIVED_DIGEST_FIELD)
    if type(observed) is not str or len(observed) != 64:
        raise ValueError(f"{label} derived_validation_digest must be a sha256 hex digest")
    expected = _derived_digest(payload)
    if observed != expected:
        raise ValueError(f"{label} derived_validation_digest mismatch")


def _derived_digest(payload: dict[str, Any]) -> str:
    digest_payload = {
        key: value for key, value in payload.items() if key != DERIVED_DIGEST_FIELD
    }
    canonical = json.dumps(
        _json_ready(digest_payload),
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be exactly datetime")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    _reject_unsafe_payload_value(label, payload)


def _reject_unsafe_payload_value(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload_value(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {path or label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            nested_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_payload_value(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_payload_value(label, item, nested_path)


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for field_name in PHASE_FLAG_FIELDS:
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True for {label}")
        for item in value.values():
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_domain(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DOMAINS:
        raise ValueError(f"{field_name} must be a supported research domain")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public text")


def _normalize_reason_codes_preserving_order(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicate values")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


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
    if reason_codes != tuple(sorted(reason_codes)) and not reason_codes[0].startswith(
        "team_performance_",
    ):
        raise ValueError("reason_codes must use stable sequence")
    return reason_codes


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _normalize_whole_count(field_name, normalized)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _normalize_whole_count(field_name, normalized)


def _normalize_whole_count(field_name: str, value: Decimal) -> Decimal:
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return value.quantize(COUNT_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)
