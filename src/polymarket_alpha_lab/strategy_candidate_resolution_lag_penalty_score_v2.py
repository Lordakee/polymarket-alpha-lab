"""Phase 1 candidate resolution lag penalty report."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
from typing import Any


DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_LAG_PENALTY_SCORE_V2_CONFIG_VERSION = (
    "strategy-candidate-resolution-lag-penalty-score-v2"
)
ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("pass", "watch", "blocked")

_COUNT_QUANTUM = Decimal("1")
_RATIO_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_RATIO = Decimal("0.000000")
_ONE_RATIO = Decimal("1.000000")
_DAYS_PER_WEEK = Decimal("7.000000")
_DIGEST_PREFIX = "scrlps-v2:"
_ROW_STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}
_BAD_TEXT_BITS = frozenset(
    "".join(parts)
    for parts in (
        ("li", "ve"),
        ("au", "th"),
        ("wal", "let"),
        ("or", "der"),
        ("net", "work"),
        ("data", "base"),
        ("per", "sist"),
        ("sig", "ning"),
        ("muta", "tion"),
        ("b", "uy"),
        ("se", "ll"),
        ("tra", "de"),
    )
)


@dataclass(frozen=True)
class StrategyCandidateResolutionLagPenaltyScoreV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_LAG_PENALTY_SCORE_V2_CONFIG_VERSION
    )
    watch_resolution_lag_penalty_score: Decimal = Decimal("0.300000")
    blocked_resolution_lag_penalty_score: Decimal = Decimal("0.700000")
    delayed_settlement_penalty_per_signal: Decimal = Decimal("0.150000")
    max_delayed_settlement_penalty_score: Decimal = Decimal("0.300000")
    official_evidence_boost_per_signal: Decimal = Decimal("0.100000")
    max_official_evidence_boost_score: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionLagPenaltyScoreV2Config:
            raise ValueError(
                "config must be a StrategyCandidateResolutionLagPenaltyScoreV2Config",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_resolution_lag_penalty_score",
            "blocked_resolution_lag_penalty_score",
            "delayed_settlement_penalty_per_signal",
            "max_delayed_settlement_penalty_score",
            "official_evidence_boost_per_signal",
            "max_official_evidence_boost_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if (
            self.watch_resolution_lag_penalty_score
            > self.blocked_resolution_lag_penalty_score
        ):
            raise ValueError(
                "watch_resolution_lag_penalty_score must not exceed blocked threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateResolutionLagPenaltyScoreV2Input:
    candidate_id: str
    market_id: str
    observed_at: datetime
    expected_resolution_lag_days: Decimal
    unresolved_outcome_age_days: Decimal
    delayed_settlement_signal_count: Decimal
    official_evidence_signal_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionLagPenaltyScoreV2Input:
            raise ValueError(
                "input must be a StrategyCandidateResolutionLagPenaltyScoreV2Input",
            )
        for field_name in ("candidate_id", "market_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "expected_resolution_lag_days",
            "unresolved_outcome_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "delayed_settlement_signal_count",
            "official_evidence_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _reject_unsafe_public_payload("input", self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyCandidateResolutionLagPenaltyScoreV2Row:
    candidate_id: str
    market_id: str
    observed_at: datetime
    expected_resolution_lag_days: Decimal
    unresolved_outcome_age_days: Decimal
    delayed_settlement_signal_count: Decimal
    official_evidence_signal_count: Decimal
    base_resolution_lag_penalty_score: Decimal
    delayed_settlement_penalty_score: Decimal
    official_evidence_boost_score: Decimal
    resolution_lag_penalty_score: Decimal
    penalty_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionLagPenaltyScoreV2Row:
            raise ValueError("row must be a StrategyCandidateResolutionLagPenaltyScoreV2Row")
        for field_name in ("candidate_id", "market_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "expected_resolution_lag_days",
            "unresolved_outcome_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "delayed_settlement_signal_count",
            "official_evidence_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "base_resolution_lag_penalty_score",
            "delayed_settlement_penalty_score",
            "official_evidence_boost_score",
            "resolution_lag_penalty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("penalty_status", self.penalty_status, ROW_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        _set_or_require_digest(self, _row_digest(self))
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyCandidateResolutionLagPenaltyScoreV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_resolution_lag_penalty_score: Decimal
    average_resolution_lag_penalty_score: Decimal
    delayed_settlement_candidate_count: Decimal
    official_evidence_boosted_candidate_count: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCandidateResolutionLagPenaltyScoreV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionLagPenaltyScoreV2Report:
            raise ValueError(
                "report must be a StrategyCandidateResolutionLagPenaltyScoreV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "delayed_settlement_candidate_count",
            "official_evidence_boosted_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_resolution_lag_penalty_score",
            "average_resolution_lag_penalty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        rows = tuple(self.rows)
        for row in rows:
            if type(row) is not StrategyCandidateResolutionLagPenaltyScoreV2Row:
                raise ValueError("rows must contain penalty score rows")
            _require_row_digest(row)
            _require_hard_flags("row", row)
        object.__setattr__(self, "rows", rows)
        _validate_report(self)
        _set_or_require_digest(self, _report_digest(self))
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_strategy_candidate_resolution_lag_penalty_score_v2(
    candidates: (
        list[StrategyCandidateResolutionLagPenaltyScoreV2Input]
        | tuple[StrategyCandidateResolutionLagPenaltyScoreV2Input, ...]
    ),
    *,
    config: StrategyCandidateResolutionLagPenaltyScoreV2Config | None = None,
    generated_at: datetime,
) -> StrategyCandidateResolutionLagPenaltyScoreV2Report:
    if config is None:
        config = StrategyCandidateResolutionLagPenaltyScoreV2Config()
    if type(config) is not StrategyCandidateResolutionLagPenaltyScoreV2Config:
        raise ValueError("config must be a StrategyCandidateResolutionLagPenaltyScoreV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    candidate,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for candidate in normalized_candidates
            ),
            key=_row_key,
        ),
    )
    return StrategyCandidateResolutionLagPenaltyScoreV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.penalty_status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.penalty_status == "watch")),
        blocked_count=_count(sum(1 for row in rows if row.penalty_status == "blocked")),
        max_resolution_lag_penalty_score=_max_ratio(
            tuple(row.resolution_lag_penalty_score for row in rows),
        ),
        average_resolution_lag_penalty_score=_average_ratio(
            tuple(row.resolution_lag_penalty_score for row in rows),
        ),
        delayed_settlement_candidate_count=_count(
            sum(1 for row in rows if row.delayed_settlement_signal_count > _ZERO_COUNT),
        ),
        official_evidence_boosted_candidate_count=_count(
            sum(1 for row in rows if row.official_evidence_boost_score > _ZERO_RATIO),
        ),
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_candidate_resolution_lag_penalty_score_v2_payload(
    report: StrategyCandidateResolutionLagPenaltyScoreV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCandidateResolutionLagPenaltyScoreV2Report:
        _require_hard_flags("report", report)
        _require_report_digest(report)
        _validate_report(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyCandidateResolutionLagPenaltyScoreV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
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


def _normalize_candidates(
    candidates: (
        list[StrategyCandidateResolutionLagPenaltyScoreV2Input]
        | tuple[StrategyCandidateResolutionLagPenaltyScoreV2Input, ...]
    ),
) -> tuple[StrategyCandidateResolutionLagPenaltyScoreV2Input, ...]:
    if type(candidates) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    normalized = tuple(candidates)
    seen: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not StrategyCandidateResolutionLagPenaltyScoreV2Input:
            raise ValueError("candidates must contain penalty score inputs")
        _require_hard_flags("input", candidate)
        if candidate.candidate_id in seen:
            raise ValueError("candidates must not contain duplicate candidate_id values")
        seen.add(candidate.candidate_id)
    return normalized


def _row_from_input(
    candidate: StrategyCandidateResolutionLagPenaltyScoreV2Input,
    *,
    config: StrategyCandidateResolutionLagPenaltyScoreV2Config,
    generated_at: datetime,
) -> StrategyCandidateResolutionLagPenaltyScoreV2Row:
    if candidate.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    base_score = _base_resolution_lag_score(candidate)
    delayed_score = _delayed_settlement_penalty(candidate, config)
    boost_score = _official_evidence_boost(candidate, config)
    score = _bounded_ratio(base_score + delayed_score - boost_score)
    status = _status_for_score(score, config)
    return StrategyCandidateResolutionLagPenaltyScoreV2Row(
        candidate_id=candidate.candidate_id,
        market_id=candidate.market_id,
        observed_at=candidate.observed_at,
        expected_resolution_lag_days=candidate.expected_resolution_lag_days,
        unresolved_outcome_age_days=candidate.unresolved_outcome_age_days,
        delayed_settlement_signal_count=candidate.delayed_settlement_signal_count,
        official_evidence_signal_count=candidate.official_evidence_signal_count,
        base_resolution_lag_penalty_score=base_score,
        delayed_settlement_penalty_score=delayed_score,
        official_evidence_boost_score=boost_score,
        resolution_lag_penalty_score=score,
        penalty_status=status,
        reason_codes=_row_reason_codes(
            candidate,
            score=score,
            delayed_score=delayed_score,
            boost_score=boost_score,
            config=config,
        ),
    )


def _base_resolution_lag_score(
    candidate: StrategyCandidateResolutionLagPenaltyScoreV2Input,
) -> Decimal:
    return _bounded_ratio(
        max(
            candidate.expected_resolution_lag_days,
            candidate.unresolved_outcome_age_days,
        )
        / _DAYS_PER_WEEK,
    )


def _delayed_settlement_penalty(
    candidate: StrategyCandidateResolutionLagPenaltyScoreV2Input,
    config: StrategyCandidateResolutionLagPenaltyScoreV2Config,
) -> Decimal:
    return min(
        _bounded_ratio(
            candidate.delayed_settlement_signal_count
            * config.delayed_settlement_penalty_per_signal,
        ),
        config.max_delayed_settlement_penalty_score,
    )


def _official_evidence_boost(
    candidate: StrategyCandidateResolutionLagPenaltyScoreV2Input,
    config: StrategyCandidateResolutionLagPenaltyScoreV2Config,
) -> Decimal:
    return min(
        _bounded_ratio(
            candidate.official_evidence_signal_count
            * config.official_evidence_boost_per_signal,
        ),
        config.max_official_evidence_boost_score,
    )


def _row_reason_codes(
    candidate: StrategyCandidateResolutionLagPenaltyScoreV2Input,
    *,
    score: Decimal,
    delayed_score: Decimal,
    boost_score: Decimal,
    config: StrategyCandidateResolutionLagPenaltyScoreV2Config,
) -> tuple[str, ...]:
    reason_codes = list(candidate.reason_codes)
    if delayed_score > _ZERO_RATIO:
        reason_codes.append("delayed_settlement_penalty")
    if boost_score > _ZERO_RATIO:
        reason_codes.append("official_evidence_boost")
    if score >= config.blocked_resolution_lag_penalty_score:
        reason_codes.append("resolution_lag_penalty_blocked")
    elif score >= config.watch_resolution_lag_penalty_score:
        reason_codes.append("resolution_lag_penalty_watch")
    else:
        reason_codes.append("resolution_lag_penalty_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_row(row: StrategyCandidateResolutionLagPenaltyScoreV2Row) -> None:
    expected_status = _status_for_score(
        row.resolution_lag_penalty_score,
        StrategyCandidateResolutionLagPenaltyScoreV2Config(),
    )
    if row.penalty_status != expected_status:
        raise ValueError("penalty_status must match resolution_lag_penalty_score")
    if row.delayed_settlement_penalty_score > _ZERO_RATIO and (
        "delayed_settlement_penalty" not in row.reason_codes
    ):
        raise ValueError("reason_codes must include delayed settlement penalty")
    if row.official_evidence_boost_score > _ZERO_RATIO and (
        "official_evidence_boost" not in row.reason_codes
    ):
        raise ValueError("reason_codes must include official evidence boost")
    if row.penalty_status == "blocked" and (
        "resolution_lag_penalty_blocked" not in row.reason_codes
    ):
        raise ValueError("blocked rows must include blocked reason")
    if row.penalty_status == "watch" and (
        "resolution_lag_penalty_watch" not in row.reason_codes
    ):
        raise ValueError("watch rows must include watch reason")
    if row.penalty_status == "pass" and (
        "resolution_lag_penalty_pass" not in row.reason_codes
    ):
        raise ValueError("pass rows must include pass reason")


def _validate_report(report: StrategyCandidateResolutionLagPenaltyScoreV2Report) -> None:
    rows = report.rows
    if rows != tuple(sorted(rows, key=_row_key)):
        raise ValueError("rows must be sorted by status and score")
    if len({row.candidate_id for row in rows}) != len(rows):
        raise ValueError("rows must contain unique candidate_id values")
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.penalty_status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.penalty_status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count(
        sum(1 for row in rows if row.penalty_status == "blocked"),
    ):
        raise ValueError("blocked_count must match rows")
    scores = tuple(row.resolution_lag_penalty_score for row in rows)
    if report.max_resolution_lag_penalty_score != _max_ratio(scores):
        raise ValueError("max_resolution_lag_penalty_score must match rows")
    if report.average_resolution_lag_penalty_score != _average_ratio(scores):
        raise ValueError("average_resolution_lag_penalty_score must match rows")
    if report.delayed_settlement_candidate_count != _count(
        sum(1 for row in rows if row.delayed_settlement_signal_count > _ZERO_COUNT),
    ):
        raise ValueError("delayed_settlement_candidate_count must match rows")
    if report.official_evidence_boosted_candidate_count != _count(
        sum(1 for row in rows if row.official_evidence_boost_score > _ZERO_RATIO),
    ):
        raise ValueError("official_evidence_boosted_candidate_count must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _status_for_score(
    score: Decimal,
    config: StrategyCandidateResolutionLagPenaltyScoreV2Config,
) -> str:
    if score >= config.blocked_resolution_lag_penalty_score:
        return "blocked"
    if score >= config.watch_resolution_lag_penalty_score:
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[StrategyCandidateResolutionLagPenaltyScoreV2Row, ...],
) -> str:
    if any(row.penalty_status == "blocked" for row in rows):
        return "blocked"
    if any(row.penalty_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyCandidateResolutionLagPenaltyScoreV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_lag_penalty_report_empty",)
    status = _report_status(rows)
    reason_codes = [f"resolution_lag_penalty_report_{status}"]
    observed = {reason_code for row in rows for reason_code in row.reason_codes}
    for reason_code in (
        "resolution_lag_penalty_blocked",
        "resolution_lag_penalty_watch",
        "delayed_settlement_penalty",
        "official_evidence_boost",
        "resolution_lag_penalty_pass",
    ):
        if reason_code in observed:
            reason_codes.append(reason_code)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_key(
    row: StrategyCandidateResolutionLagPenaltyScoreV2Row,
) -> tuple[int, Decimal, datetime, str]:
    return (
        _ROW_STATUS_RANK[row.penalty_status],
        -row.resolution_lag_penalty_score,
        row.observed_at,
        row.candidate_id,
    )


def _row_digest(row: StrategyCandidateResolutionLagPenaltyScoreV2Row) -> str:
    return _digest(
        (
            "row",
            row.candidate_id,
            row.market_id,
            _datetime_payload(row.observed_at),
            _decimal_payload(row.expected_resolution_lag_days),
            _decimal_payload(row.unresolved_outcome_age_days),
            _decimal_payload(row.delayed_settlement_signal_count),
            _decimal_payload(row.official_evidence_signal_count),
            _decimal_payload(row.base_resolution_lag_penalty_score),
            _decimal_payload(row.delayed_settlement_penalty_score),
            _decimal_payload(row.official_evidence_boost_score),
            _decimal_payload(row.resolution_lag_penalty_score),
            row.penalty_status,
            "|".join(row.reason_codes),
            str(row.paper_only),
            str(row.report_only),
            str(row.readonly),
        ),
    )


def _report_digest(report: StrategyCandidateResolutionLagPenaltyScoreV2Report) -> str:
    return _digest(
        (
            "report",
            _datetime_payload(report.generated_at),
            report.config_version,
            _decimal_payload(report.candidate_count),
            _decimal_payload(report.pass_count),
            _decimal_payload(report.watch_count),
            _decimal_payload(report.blocked_count),
            _decimal_payload(report.max_resolution_lag_penalty_score),
            _decimal_payload(report.average_resolution_lag_penalty_score),
            _decimal_payload(report.delayed_settlement_candidate_count),
            _decimal_payload(report.official_evidence_boosted_candidate_count),
            report.report_status,
            "|".join(report.reason_codes),
            "|".join(row.derived_validation_digest for row in report.rows),
            str(report.paper_only),
            str(report.report_only),
            str(report.readonly),
        ),
    )


def _digest(parts: tuple[str, ...]) -> str:
    payload = "\0".join(parts).encode("utf-8")
    return f"{_DIGEST_PREFIX}{hashlib.sha256(payload).hexdigest()}"


def _set_or_require_digest(value: object, expected: str) -> None:
    current = getattr(value, "derived_validation_digest")
    if current == "":
        object.__setattr__(value, "derived_validation_digest", expected)
    elif current != expected:
        raise ValueError("derived_validation_digest must match report fields")
    _require_digest_text("derived_validation_digest", getattr(value, "derived_validation_digest"))


def _require_row_digest(row: StrategyCandidateResolutionLagPenaltyScoreV2Row) -> None:
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest tamper detected")


def _require_report_digest(report: StrategyCandidateResolutionLagPenaltyScoreV2Report) -> None:
    for row in report.rows:
        _require_row_digest(row)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest tamper detected")


def _require_digest_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value.startswith(_DIGEST_PREFIX):
        raise ValueError(f"{field_name} must be a derived digest")
    suffix = value[len(_DIGEST_PREFIX) :]
    if len(suffix) != 64 or any(character not in "0123456789abcdef" for character in suffix):
        raise ValueError(f"{field_name} must be a derived digest")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if type(value) is datetime:
        return _datetime_payload(value)
    if type(value) in (str, bool):
        return value
    if type(value) is int:
        raise ValueError("JSON numbers must be Decimal strings")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return _json_dict_ready(value)
    if _is_allowed_dataclass(value):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if is_dataclass(value) and not isinstance(value, type):
        raise ValueError("unsafe payload object must be a plain value")
    raise ValueError("value is not JSON serializable")


def _json_dict_ready(value: dict[Any, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        ready[key] = _json_ready(item)
    return ready


def _is_allowed_dataclass(value: object) -> bool:
    return type(value) in (
        StrategyCandidateResolutionLagPenaltyScoreV2Config,
        StrategyCandidateResolutionLagPenaltyScoreV2Input,
        StrategyCandidateResolutionLagPenaltyScoreV2Row,
        StrategyCandidateResolutionLagPenaltyScoreV2Report,
        _DictFlags,
    )


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if _is_allowed_dataclass(value):
        for field in fields(value):
            _reject_unsafe_public_payload(label, getattr(value, field.name))
        return
    if is_dataclass(value) and not isinstance(value, type):
        raise ValueError(f"unsafe payload object in {label}")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if isinstance(value, (Decimal, datetime, bool)) or value is None:
        return
    if type(value) in (int, float):
        return
    raise ValueError(f"unsafe payload object in {label}")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    if _has_bad_fragment(value):
        raise ValueError(f"unsafe public payload in {label}")


def _has_bad_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _BAD_TEXT_BITS)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    _reject_unsafe_public_text(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_RATIO_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    if quantized < _ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


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


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_RATIO_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    if quantized < _ZERO_RATIO or quantized > _ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return quantized


def _bounded_ratio(value: Decimal) -> Decimal:
    quantized = value.quantize(_RATIO_QUANTUM)
    if quantized < _ZERO_RATIO:
        return _ZERO_RATIO
    if quantized > _ONE_RATIO:
        return _ONE_RATIO
    return quantized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    for reason_code in reason_codes:
        _require_reason_code(reason_code)
    return reason_codes


def _require_reason_code(value: object) -> None:
    if type(value) is not str:
        raise ValueError("reason_codes must contain strings")
    if not value or value.strip() != value:
        raise ValueError("reason_codes must contain canonical strings")
    if value != value.lower() or value[0] == "_" or value[-1] == "_":
        raise ValueError("reason_codes must be lowercase snake_case strings")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError("reason_codes must be lowercase snake_case strings")
    _reject_unsafe_public_text("reason_codes", value)


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO_RATIO
    return max(values).quantize(_RATIO_QUANTUM)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO_RATIO
    return (sum(values, _ZERO_RATIO) / Decimal(len(values))).quantize(_RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return str(value)


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_LAG_PENALTY_SCORE_V2_CONFIG_VERSION",
    "ROW_STATUSES",
    "REPORT_STATUSES",
    "StrategyCandidateResolutionLagPenaltyScoreV2Config",
    "StrategyCandidateResolutionLagPenaltyScoreV2Input",
    "StrategyCandidateResolutionLagPenaltyScoreV2Row",
    "StrategyCandidateResolutionLagPenaltyScoreV2Report",
    "build_strategy_candidate_resolution_lag_penalty_score_v2",
    "strategy_candidate_resolution_lag_penalty_score_v2_payload",
)
