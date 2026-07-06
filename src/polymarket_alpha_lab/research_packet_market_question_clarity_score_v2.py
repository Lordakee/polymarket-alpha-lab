"""Phase 1 paper-only market question clarity scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_PACKET_MARKET_QUESTION_CLARITY_SCORE_V2_CONFIG_VERSION = (
    "research-packet-market-question-clarity-score-v2"
)

_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")

_QUESTION_FORM_BOOST = Decimal("0.100000")
_BINARY_OUTCOME_BOOST = Decimal("0.100000")
_DEADLINE_BOOST = Decimal("0.100000")

_PASS_REASON = "question_clarity_pass"
_LOW_SCORE_REASON = "clarity_score_below_pass_threshold"
_BLOCKED_SCORE_REASON = "clarity_score_below_watch_threshold"
_MEASURABLE_RESOLUTION_REASON = "measurable_resolution_missing"
_VAGUE_CONDITION_REASON = "vague_conditions_detected"
_EMPTY_REASON = "no_market_questions"

_UNSAFE_PUBLIC_TERMS = (
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
_UNSAFE_PUBLIC_TERM_PATTERN = re.compile(
    r"(?<![a-z0-9])("
    + "|".join(re.escape(term) for term in _UNSAFE_PUBLIC_TERMS)
    + r")(?![a-z0-9])",
)

_VAGUE_TERMS = (
    "approximately",
    "around",
    "big",
    "important",
    "likely",
    "major",
    "material",
    "maybe",
    "notable",
    "roughly",
    "significant",
    "soon",
    "substantial",
    "unclear",
)
_MEASURABLE_TERMS = (
    "at least",
    "certified",
    "final",
    "greater than",
    "less than",
    "no later than",
    "official",
    "published",
    "present",
    "reported",
    "result",
    "results",
    "score",
    "settles",
)
_BINARY_STARTERS = ("will ", "does ", "do ", "is ", "are ", "has ", "have ", "can ")
_DEADLINE_PATTERN = re.compile(
    r"\b(20\d{2}-\d{2}-\d{2}|20\d{2}|by|before|after|on|through|until)\b",
)


__all__ = (
    "DEFAULT_RESEARCH_PACKET_MARKET_QUESTION_CLARITY_SCORE_V2_CONFIG_VERSION",
    "ResearchPacketMarketQuestionClarityScoreV2Config",
    "ResearchPacketMarketQuestionClarityScoreV2Input",
    "ResearchPacketMarketQuestionClarityScoreV2Row",
    "ResearchPacketMarketQuestionClarityScoreV2Report",
    "build_research_packet_market_question_clarity_score_v2",
    "research_packet_market_question_clarity_score_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketMarketQuestionClarityScoreV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_MARKET_QUESTION_CLARITY_SCORE_V2_CONFIG_VERSION
    )
    min_pass_clarity_score: Decimal = Decimal("0.750000")
    min_watch_clarity_score: Decimal = Decimal("0.600000")
    measurable_resolution_boost: Decimal = Decimal("0.200000")
    vague_condition_penalty_per_term: Decimal = Decimal("0.080000")
    max_vague_condition_penalty: Decimal = Decimal("0.320000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketMarketQuestionClarityScoreV2Config:
            raise ValueError(
                "config must be exactly "
                "ResearchPacketMarketQuestionClarityScoreV2Config",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        for field_name in (
            "min_pass_clarity_score",
            "min_watch_clarity_score",
            "measurable_resolution_boost",
            "vague_condition_penalty_per_term",
            "max_vague_condition_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.min_watch_clarity_score > self.min_pass_clarity_score:
            raise ValueError(
                "min_watch_clarity_score must be less than or equal to "
                "min_pass_clarity_score",
            )
        if self.max_vague_condition_penalty < self.vague_condition_penalty_per_term:
            raise ValueError(
                "max_vague_condition_penalty must be greater than or equal to "
                "vague_condition_penalty_per_term",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketMarketQuestionClarityScoreV2Input:
    market_reference: str
    question: str
    resolution_criteria: str
    source_config_version: str = (
        DEFAULT_RESEARCH_PACKET_MARKET_QUESTION_CLARITY_SCORE_V2_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketMarketQuestionClarityScoreV2Input:
            raise ValueError(
                "input must be exactly "
                "ResearchPacketMarketQuestionClarityScoreV2Input",
            )
        object.__setattr__(
            self,
            "market_reference",
            _require_canonical_string("market_reference", self.market_reference),
        )
        object.__setattr__(
            self,
            "question",
            _require_public_text("question", self.question, allow_empty=False),
        )
        object.__setattr__(
            self,
            "resolution_criteria",
            _require_public_text(
                "resolution_criteria",
                self.resolution_criteria,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "source_config_version",
            _require_canonical_string(
                "source_config_version",
                self.source_config_version,
            ),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchPacketMarketQuestionClarityScoreV2Row:
    market_reference: str
    question: str
    question_clarity_score: Decimal
    measurable_resolution_score: Decimal
    vague_condition_penalty: Decimal
    clarity_status: str
    reason_codes: tuple[str, ...]
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketMarketQuestionClarityScoreV2Row:
            raise ValueError(
                "row must be exactly ResearchPacketMarketQuestionClarityScoreV2Row",
            )
        object.__setattr__(
            self,
            "market_reference",
            _require_canonical_string("market_reference", self.market_reference),
        )
        object.__setattr__(
            self,
            "question",
            _require_public_text("question", self.question, allow_empty=False),
        )
        for field_name in (
            "question_clarity_score",
            "measurable_resolution_score",
            "vague_condition_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "clarity_status",
            _require_member("clarity_status", self.clarity_status, ("pass", "watch", "blocked")),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "source_config_version",
            _require_canonical_string(
                "source_config_version",
                self.source_config_version,
            ),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchPacketMarketQuestionClarityScoreV2Report:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_question_clarity_score: Decimal
    average_measurable_resolution_score: Decimal
    average_vague_condition_penalty: Decimal
    min_question_clarity_score: Decimal
    rows: tuple[ResearchPacketMarketQuestionClarityScoreV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketMarketQuestionClarityScoreV2Report:
            raise ValueError(
                "report must be exactly "
                "ResearchPacketMarketQuestionClarityScoreV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_question_clarity_score",
            "average_measurable_resolution_score",
            "average_vague_condition_penalty",
            "min_question_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_report_counts(self)
        _require_hard_flags("report", self)
        expected_digest = _report_validation_digest(self)
        if self.derived_validation_digest is None:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report contents")
        _reject_unsafe_public_payload("report", self)


def build_research_packet_market_question_clarity_score_v2(
    inputs: list[ResearchPacketMarketQuestionClarityScoreV2Input]
    | tuple[ResearchPacketMarketQuestionClarityScoreV2Input, ...],
    *,
    config: ResearchPacketMarketQuestionClarityScoreV2Config,
    generated_at: datetime,
) -> ResearchPacketMarketQuestionClarityScoreV2Report:
    if type(config) is not ResearchPacketMarketQuestionClarityScoreV2Config:
        raise ValueError(
            "config must be a ResearchPacketMarketQuestionClarityScoreV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_score_input(row, config=config) for row in normalized_inputs),
            key=lambda row: row.market_reference,
        )
    )
    return ResearchPacketMarketQuestionClarityScoreV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        row_count=_count_decimal(len(rows)),
        pass_count=_count_status(rows, "pass"),
        watch_count=_count_status(rows, "watch"),
        blocked_count=_count_status(rows, "blocked"),
        average_question_clarity_score=_average(
            tuple(row.question_clarity_score for row in rows),
        ),
        average_measurable_resolution_score=_average(
            tuple(row.measurable_resolution_score for row in rows),
        ),
        average_vague_condition_penalty=_average(
            tuple(row.vague_condition_penalty for row in rows),
        ),
        min_question_clarity_score=_minimum(
            tuple(row.question_clarity_score for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_packet_market_question_clarity_score_v2_payload(
    report: ResearchPacketMarketQuestionClarityScoreV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketMarketQuestionClarityScoreV2Report:
        _require_hard_flags("report", report)
        _validate_report_digest(report)
        payload = _report_payload_without_digest(report)
        payload["derived_validation_digest"] = report.derived_validation_digest
        _reject_unsafe_public_payload("payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        return payload
    if type(report) is dict:
        payload = _json_ready_no_numbers(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _reject_unsafe_public_payload("payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        if "derived_validation_digest" in payload:
            _require_sha256("derived_validation_digest", payload["derived_validation_digest"])
            expected_digest = _digest_for_payload(payload)
            if payload["derived_validation_digest"] != expected_digest:
                raise ValueError("derived_validation_digest does not match payload contents")
        return payload
    raise ValueError(
        "report must be a ResearchPacketMarketQuestionClarityScoreV2Report",
    )


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


def _score_input(
    row: ResearchPacketMarketQuestionClarityScoreV2Input,
    *,
    config: ResearchPacketMarketQuestionClarityScoreV2Config,
) -> ResearchPacketMarketQuestionClarityScoreV2Row:
    question_text = row.question.strip()
    resolution_text = row.resolution_criteria.strip()
    combined_text = f"{question_text} {resolution_text}".lower()

    score = Decimal("0.350000")
    if _has_clear_question_form(question_text):
        score += _QUESTION_FORM_BOOST
    if question_text.lower().startswith(_BINARY_STARTERS):
        score += _BINARY_OUTCOME_BOOST
    if _DEADLINE_PATTERN.search(combined_text) is not None:
        score += _DEADLINE_BOOST

    measurable_resolution_score = _measurable_resolution_score(resolution_text)
    score += measurable_resolution_score * config.measurable_resolution_boost

    vague_condition_penalty = _vague_condition_penalty(
        combined_text,
        config=config,
    )
    score -= vague_condition_penalty
    question_clarity_score = _clamp_ratio(score)

    reason_codes = _row_reason_codes(
        question_clarity_score=question_clarity_score,
        measurable_resolution_score=measurable_resolution_score,
        vague_condition_penalty=vague_condition_penalty,
        config=config,
    )
    return ResearchPacketMarketQuestionClarityScoreV2Row(
        market_reference=row.market_reference,
        question=row.question,
        question_clarity_score=question_clarity_score,
        measurable_resolution_score=measurable_resolution_score,
        vague_condition_penalty=vague_condition_penalty,
        clarity_status=_row_status(question_clarity_score, config=config),
        reason_codes=reason_codes,
        source_config_version=row.source_config_version,
    )


def _has_clear_question_form(question: str) -> bool:
    lowered = question.lower()
    return question.endswith("?") and lowered.startswith(_BINARY_STARTERS)


def _measurable_resolution_score(resolution_criteria: str) -> Decimal:
    if not resolution_criteria:
        return _ZERO
    normalized = resolution_criteria.lower()
    match_count = sum(1 for term in _MEASURABLE_TERMS if term in normalized)
    if match_count >= 3:
        return _ONE
    if match_count == 2:
        return Decimal("0.750000")
    if match_count == 1:
        return Decimal("0.500000")
    return Decimal("0.250000")


def _vague_condition_penalty(
    value: str,
    *,
    config: ResearchPacketMarketQuestionClarityScoreV2Config,
) -> Decimal:
    vague_count = sum(
        1
        for term in _VAGUE_TERMS
        if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", value)
        is not None
    )
    penalty = _count_decimal(vague_count) * config.vague_condition_penalty_per_term
    return _clamp_ratio(min(penalty, config.max_vague_condition_penalty))


def _row_reason_codes(
    *,
    question_clarity_score: Decimal,
    measurable_resolution_score: Decimal,
    vague_condition_penalty: Decimal,
    config: ResearchPacketMarketQuestionClarityScoreV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if question_clarity_score < config.min_watch_clarity_score:
        reason_codes.append(_BLOCKED_SCORE_REASON)
    elif question_clarity_score < config.min_pass_clarity_score:
        reason_codes.append(_LOW_SCORE_REASON)
    if measurable_resolution_score == _ZERO:
        reason_codes.append(_MEASURABLE_RESOLUTION_REASON)
    if vague_condition_penalty > _ZERO:
        reason_codes.append(_VAGUE_CONDITION_REASON)
    if not reason_codes:
        reason_codes.append(_PASS_REASON)
    return tuple(sorted(reason_codes))


def _row_status(
    question_clarity_score: Decimal,
    *,
    config: ResearchPacketMarketQuestionClarityScoreV2Config,
) -> str:
    if question_clarity_score >= config.min_pass_clarity_score:
        return "pass"
    if question_clarity_score >= config.min_watch_clarity_score:
        return "watch"
    return "blocked"


def _report_reason_codes(
    rows: tuple[ResearchPacketMarketQuestionClarityScoreV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    reason_codes = sorted({reason for row in rows for reason in row.reason_codes})
    if len(reason_codes) > 1 and _PASS_REASON in reason_codes:
        reason_codes.remove(_PASS_REASON)
    return tuple(reason_codes)


def _report_payload_without_digest(
    report: ResearchPacketMarketQuestionClarityScoreV2Report,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "row_count": _decimal_payload(report.row_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "blocked_count": _decimal_payload(report.blocked_count),
        "average_question_clarity_score": _decimal_payload(
            report.average_question_clarity_score,
        ),
        "average_measurable_resolution_score": _decimal_payload(
            report.average_measurable_resolution_score,
        ),
        "average_vague_condition_penalty": _decimal_payload(
            report.average_vague_condition_penalty,
        ),
        "min_question_clarity_score": _decimal_payload(
            report.min_question_clarity_score,
        ),
        "rows": [_row_payload(row) for row in report.rows],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: ResearchPacketMarketQuestionClarityScoreV2Row) -> dict[str, Any]:
    if type(row) is not ResearchPacketMarketQuestionClarityScoreV2Row:
        raise ValueError("row must be a ResearchPacketMarketQuestionClarityScoreV2Row")
    _require_hard_flags("row", row)
    return {
        "market_reference": row.market_reference,
        "question": row.question,
        "question_clarity_score": _decimal_payload(row.question_clarity_score),
        "measurable_resolution_score": _decimal_payload(row.measurable_resolution_score),
        "vague_condition_penalty": _decimal_payload(row.vague_condition_penalty),
        "clarity_status": row.clarity_status,
        "reason_codes": list(row.reason_codes),
        "source_config_version": row.source_config_version,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_validation_digest(
    report: ResearchPacketMarketQuestionClarityScoreV2Report,
) -> str:
    return _digest_for_payload(_report_payload_without_digest(report))


def _digest_for_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_report_digest(
    report: ResearchPacketMarketQuestionClarityScoreV2Report,
) -> None:
    if report.derived_validation_digest != _report_validation_digest(report):
        raise ValueError("derived_validation_digest does not match report contents")


def _validate_report_counts(
    report: ResearchPacketMarketQuestionClarityScoreV2Report,
) -> None:
    rows = report.rows
    if report.row_count != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _count_status(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_status(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count_status(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.average_question_clarity_score != _average(
        tuple(row.question_clarity_score for row in rows),
    ):
        raise ValueError("average_question_clarity_score must match rows")
    if report.average_measurable_resolution_score != _average(
        tuple(row.measurable_resolution_score for row in rows),
    ):
        raise ValueError("average_measurable_resolution_score must match rows")
    if report.average_vague_condition_penalty != _average(
        tuple(row.vague_condition_penalty for row in rows),
    ):
        raise ValueError("average_vague_condition_penalty must match rows")
    if report.min_question_clarity_score != _minimum(
        tuple(row.question_clarity_score for row in rows),
    ):
        raise ValueError("min_question_clarity_score must match rows")


def _normalize_inputs(
    inputs: list[ResearchPacketMarketQuestionClarityScoreV2Input]
    | tuple[ResearchPacketMarketQuestionClarityScoreV2Input, ...],
) -> tuple[ResearchPacketMarketQuestionClarityScoreV2Input, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    for row in normalized:
        if type(row) is not ResearchPacketMarketQuestionClarityScoreV2Input:
            raise ValueError(
                "inputs must contain ResearchPacketMarketQuestionClarityScoreV2Input",
            )
        _require_hard_flags("input", row)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchPacketMarketQuestionClarityScoreV2Row, ...],
) -> tuple[ResearchPacketMarketQuestionClarityScoreV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchPacketMarketQuestionClarityScoreV2Row:
            raise ValueError(
                "rows must contain ResearchPacketMarketQuestionClarityScoreV2Row",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        normalized.append(_require_canonical_string("reason_code", reason_code))
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(sorted(set(normalized)))


def _count_status(
    rows: tuple[ResearchPacketMarketQuestionClarityScoreV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.clarity_status == status))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _clamp_ratio(sum(values, _ZERO) / _count_decimal(len(values)))


def _minimum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _clamp_ratio(min(values))


def _count_decimal(value: int) -> Decimal:
    return Decimal(value)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return value.quantize(_QUANT)


def _require_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return value.quantize(_QUANT)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return value.to_integral_value()


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload numeric values must be Decimal")
    if not value.is_finite():
        raise ValueError("payload numeric values must be finite")
    return format(value, "f")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    if "://" in value or "?" in value:
        raise ValueError(f"{field_name} has unsafe value")
    if _UNSAFE_PUBLIC_TERM_PATTERN.search(value.lower()) is not None:
        raise ValueError(f"{field_name} has unsafe value")
    return value


def _require_public_text(field_name: str, value: object, *, allow_empty: bool) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    if "://" in value:
        raise ValueError(f"{field_name} has unsafe value")
    if _UNSAFE_PUBLIC_TERM_PATTERN.search(value.lower()) is not None:
        raise ValueError(f"{field_name} has unsafe value")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            ResearchPacketMarketQuestionClarityScoreV2Config,
            ResearchPacketMarketQuestionClarityScoreV2Input,
            ResearchPacketMarketQuestionClarityScoreV2Row,
            ResearchPacketMarketQuestionClarityScoreV2Report,
            _DictFlags,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _UNSAFE_PUBLIC_TERM_PATTERN.search(key.lower()) is not None:
                raise ValueError(f"{key} has unsafe field")
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
            )
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
            )
        return
    if type(value) is str:
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe value")
        if "://" in value:
            raise ValueError(f"{current_path} has unsafe value")
        if _UNSAFE_PUBLIC_TERM_PATTERN.search(value.lower()) is not None:
            raise ValueError(f"{current_path} has unsafe value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is datetime:
        _as_utc(current_path, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON serializable")


def _json_ready_no_numbers(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_no_numbers(asdict(value))
    if type(value) is dict:
        return {key: _json_ready_no_numbers(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_json_ready_no_numbers(item) for item in value]
    if type(value) is Decimal:
        return _decimal_payload(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if value is None or type(value) in (bool, str):
        return value
    if type(value) in (int, float):
        raise ValueError("payload numeric values must be serialized from Decimal")
    raise ValueError("payload value is not JSON serializable")
