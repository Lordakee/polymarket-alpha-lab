from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


PUBLIC_STATUSES = ("pass", "watch", "block")
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO_COUNT = Decimal("2")
DECIMAL_PRECISION = 64

PAYLOAD_FIELDS = (
    "public_status",
    "score_count",
    "pass_score_count",
    "watch_score_count",
    "block_score_count",
    "weighted_score",
    "rows",
    "reason_codes",
    "review_notes",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_FIELDS = (
    "score_name",
    "status",
    "score",
    "weight",
    "weighted_score",
    "summary",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)

BASE_REASON_CODES = (
    "decision_explanation_pass",
    "decision_explanation_watch",
    "decision_explanation_block",
    "status_conflict_present",
)

RESTRICTED_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "raw_candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "ref_url",
    "http://",
    "https://",
    "url",
    "dsn",
    "schema.",
    " public.",
    "token",
    "secret",
    "password",
    "credential",
    "private_key",
    "api_key",
    "wal" + "let",
    "a" + "uth",
    "or" + "der",
    "tr" + "ade",
    "pos" + "ition",
    "b" + "uy",
    "se" + "ll",
    "rec" + "ommend",
)


@dataclass(frozen=True)
class StrategyDecisionExplainerScore:
    score_name: str
    status: str
    score: Decimal
    weight: Decimal
    summary: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "score_name",
            _normalize_token("score_name", self.score_name),
        )
        _require_member("status", self.status, PUBLIC_STATUSES)
        object.__setattr__(self, "score", _normalize_probability("score", self.score))
        object.__setattr__(
            self,
            "weight",
            _normalize_nonnegative_decimal("weight", self.weight),
        )
        object.__setattr__(
            self,
            "summary",
            _normalize_public_text("summary", self.summary),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("score", self)


@dataclass(frozen=True)
class StrategyDecisionExplanationRow:
    score_name: str
    status: str
    score: Decimal
    weight: Decimal
    weighted_score: Decimal
    summary: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "score_name",
            _normalize_token("score_name", self.score_name),
        )
        _require_member("status", self.status, PUBLIC_STATUSES)
        object.__setattr__(self, "score", _normalize_probability("score", self.score))
        object.__setattr__(
            self,
            "weight",
            _normalize_nonnegative_decimal("weight", self.weight),
        )
        object.__setattr__(
            self,
            "weighted_score",
            _normalize_nonnegative_decimal("weighted_score", self.weighted_score),
        )
        object.__setattr__(
            self,
            "summary",
            _normalize_public_text("summary", self.summary),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class StrategyDecisionExplanation:
    public_status: str
    score_count: Decimal
    pass_score_count: Decimal
    watch_score_count: Decimal
    block_score_count: Decimal
    weighted_score: Decimal | None
    rows: tuple[StrategyDecisionExplanationRow, ...]
    reason_codes: tuple[str, ...]
    review_notes: tuple[str, ...]
    explanation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        for field_name in (
            "score_count",
            "pass_score_count",
            "watch_score_count",
            "block_score_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        if self.weighted_score is not None:
            object.__setattr__(
                self,
                "weighted_score",
                _normalize_probability("weighted_score", self.weighted_score),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "review_notes",
            _normalize_review_notes(self.review_notes),
        )
        _require_digest(self.explanation_digest)
        _require_hard_flags("explanation", self)
        _validate_explanation(self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_decision_explanation_payload(self)


def build_strategy_decision_explanation(
    scores: tuple[StrategyDecisionExplainerScore, ...]
    | list[StrategyDecisionExplainerScore],
) -> StrategyDecisionExplanation:
    rows = tuple(
        sorted(
            (_row_from_score(score) for score in _normalize_scores(scores)),
            key=_row_sort_key,
        ),
    )
    public_status = _public_status(rows)
    weighted_score = _weighted_score(rows)
    reason_codes = _explanation_reason_codes(rows, public_status)
    review_notes = _review_notes(rows, public_status)
    payload = _payload_from_parts(
        public_status=public_status,
        score_count=_count(len(rows)),
        pass_score_count=_status_count(rows, "pass"),
        watch_score_count=_status_count(rows, "watch"),
        block_score_count=_status_count(rows, "block"),
        weighted_score=weighted_score,
        rows=rows,
        reason_codes=reason_codes,
        review_notes=review_notes,
    )
    return StrategyDecisionExplanation(
        public_status=public_status,
        score_count=_count(len(rows)),
        pass_score_count=_status_count(rows, "pass"),
        watch_score_count=_status_count(rows, "watch"),
        block_score_count=_status_count(rows, "block"),
        weighted_score=weighted_score,
        rows=rows,
        reason_codes=reason_codes,
        review_notes=review_notes,
        explanation_digest=strategy_decision_explanation_digest(payload),
    )


def strategy_decision_explanation_payload(
    payload: StrategyDecisionExplanation | dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is StrategyDecisionExplanation:
        _require_hard_flags("explanation", payload)
        ready = _payload_from_parts(
            public_status=payload.public_status,
            score_count=payload.score_count,
            pass_score_count=payload.pass_score_count,
            watch_score_count=payload.watch_score_count,
            block_score_count=payload.block_score_count,
            weighted_score=payload.weighted_score,
            rows=payload.rows,
            reason_codes=payload.reason_codes,
            review_notes=payload.review_notes,
        )
    elif type(payload) is dict:
        _reject_unsupported_payload_fields(payload)
        _require_hard_flags("payload", payload)
        if "public_status" in payload:
            _require_member("public_status", payload["public_status"], PUBLIC_STATUSES)
        ready = _json_ready(payload)
    else:
        raise ValueError("payload must be a StrategyDecisionExplanation")
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsupported_payload_fields(ready)
    _reject_public_payload_text(ready)
    return ready


def strategy_decision_explanation_digest(payload: dict[str, Any]) -> str:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    ready = strategy_decision_explanation_payload(payload)
    canonical = json.dumps(
        ready,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _row_from_score(score: StrategyDecisionExplainerScore) -> StrategyDecisionExplanationRow:
    return StrategyDecisionExplanationRow(
        score_name=score.score_name,
        status=score.status,
        score=score.score,
        weight=score.weight,
        weighted_score=_quantize(score.score * score.weight),
        summary=score.summary,
        reason_codes=score.reason_codes,
    )


def _payload_from_parts(
    *,
    public_status: str,
    score_count: Decimal,
    pass_score_count: Decimal,
    watch_score_count: Decimal,
    block_score_count: Decimal,
    weighted_score: Decimal | None,
    rows: tuple[StrategyDecisionExplanationRow, ...],
    reason_codes: tuple[str, ...],
    review_notes: tuple[str, ...],
) -> dict[str, Any]:
    payload = {
        "public_status": public_status,
        "score_count": score_count,
        "pass_score_count": pass_score_count,
        "watch_score_count": watch_score_count,
        "block_score_count": block_score_count,
        "weighted_score": weighted_score,
        "rows": [_row_payload(row) for row in rows],
        "reason_codes": list(reason_codes),
        "review_notes": list(review_notes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_public_payload_text(ready)
    return ready


def _row_payload(row: StrategyDecisionExplanationRow) -> dict[str, Any]:
    _require_hard_flags("row", row)
    return {
        "score_name": row.score_name,
        "status": row.status,
        "score": row.score,
        "weight": row.weight,
        "weighted_score": row.weighted_score,
        "summary": row.summary,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _weighted_score(rows: tuple[StrategyDecisionExplanationRow, ...]) -> Decimal | None:
    total_weight = sum((row.weight for row in rows), ZERO)
    if not rows or total_weight == ZERO:
        return None
    weighted_total = sum((row.weighted_score for row in rows), ZERO)
    with localcontext() as ctx:
        ctx.prec = DECIMAL_PRECISION
        return _normalize_probability("weighted_score", weighted_total / total_weight)


def _public_status(rows: tuple[StrategyDecisionExplanationRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _explanation_reason_codes(
    rows: tuple[StrategyDecisionExplanationRow, ...],
    public_status: str,
) -> tuple[str, ...]:
    codes = [f"decision_explanation_{public_status}"]
    conflict = _has_status_conflict(rows, public_status)
    if conflict:
        codes.append("status_conflict_present")
        selected_rows = rows
    elif public_status == "pass":
        selected_rows = rows
    else:
        selected_rows = tuple(row for row in rows if row.status == public_status)
    for row in selected_rows:
        codes.extend(row.reason_codes)
    return _dedupe_reason_codes(tuple(codes))


def _review_notes(
    rows: tuple[StrategyDecisionExplanationRow, ...],
    public_status: str,
) -> tuple[str, ...]:
    notes: list[str] = []
    if _has_status_conflict(rows, public_status):
        notes.append("conflicting score statuses require review")
    notes.extend(
        f"{row.score_name}: {row.summary}"
        for row in rows
        if row.status in ("watch", "block")
    )
    return tuple(notes)


def _has_status_conflict(
    rows: tuple[StrategyDecisionExplanationRow, ...],
    public_status: str,
) -> bool:
    statuses = frozenset(row.status for row in rows)
    return (
        public_status == "watch"
        and _count(len(rows)) > TWO_COUNT
        and "pass" in statuses
        and "watch" in statuses
        and "block" not in statuses
    )


def _status_count(
    rows: tuple[StrategyDecisionExplanationRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(ONE for row in rows if row.status == status))


def _row_sort_key(row: StrategyDecisionExplanationRow) -> str:
    return row.score_name


def _normalize_scores(
    scores: tuple[StrategyDecisionExplainerScore, ...]
    | list[StrategyDecisionExplainerScore],
) -> tuple[StrategyDecisionExplainerScore, ...]:
    if type(scores) not in (list, tuple):
        raise ValueError("scores must be a list or tuple")
    normalized = tuple(scores)
    seen_names: set[str] = set()
    for score in normalized:
        if type(score) is not StrategyDecisionExplainerScore:
            raise ValueError("scores must contain StrategyDecisionExplainerScore values")
        _require_hard_flags("score", score)
        if score.score_name in seen_names:
            raise ValueError("score_name values must be unique")
        seen_names.add(score.score_name)
    return normalized


def _normalize_rows(
    rows: tuple[StrategyDecisionExplanationRow, ...],
) -> tuple[StrategyDecisionExplanationRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_names: set[str] = set()
    for row in normalized:
        if type(row) is not StrategyDecisionExplanationRow:
            raise ValueError("rows must contain StrategyDecisionExplanationRow values")
        _require_hard_flags("row", row)
        if row.score_name in seen_names:
            raise ValueError("row score_name values must be unique")
        seen_names.add(row.score_name)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by score_name")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a list or tuple")
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    seen_codes: set[str] = set()
    for code in codes:
        _normalize_token(field_name, code)
        if code in seen_codes:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen_codes.add(code)
    return codes


def _dedupe_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    seen_codes: set[str] = set()
    codes: list[str] = []
    for code in value:
        _normalize_token("reason_codes", code)
        if code not in seen_codes:
            codes.append(code)
            seen_codes.add(code)
    return tuple(codes)


def _normalize_review_notes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("review_notes must be a list or tuple")
    if type(value) not in (list, tuple):
        raise ValueError("review_notes must be a list or tuple")
    notes = tuple(_normalize_public_text("review_notes", note) for note in value)
    if len(set(notes)) != len(notes):
        raise ValueError("review_notes must not contain duplicates")
    return notes


def _normalize_token(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if not all(char.islower() or char.isdigit() or char == "_" for char in value):
        raise ValueError(f"{field_name} must be lower snake case")
    _reject_restricted_public_text(field_name, value)
    return value


def _normalize_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a single line")
    _reject_restricted_public_text(field_name, value)
    return value


def _reject_restricted_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in RESTRICTED_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains restricted public text")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    normalized = decimal_value.quantize(COUNT_QUANTUM)
    if normalized != decimal_value or normalized < Decimal("0"):
        raise ValueError(f"{field_name} must be a nonnegative count")
    return normalized


def _count(value: object) -> Decimal:
    return Decimal(str(value)).quantize(COUNT_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        return value.quantize(RATIO_QUANTUM)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if _field_value(value, "paper_only") is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if _field_value(value, "report_only") is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if _field_value(value, "readonly") is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _field_value(value: object, field_name: str) -> object:
    if type(value) is dict:
        return value.get(field_name)
    return getattr(value, field_name, None)


def _require_digest(value: object) -> None:
    if type(value) is not str:
        raise ValueError("explanation_digest must be a string")
    if len(value) != 64 or not all(char in "0123456789abcdef" for char in value):
        raise ValueError("explanation_digest must be canonical")


def _validate_row(row: StrategyDecisionExplanationRow) -> None:
    if row.weighted_score != _quantize(row.score * row.weight):
        raise ValueError("weighted_score must match score and weight")


def _validate_explanation(explanation: StrategyDecisionExplanation) -> None:
    rows = explanation.rows
    if explanation.score_count != _count(len(rows)):
        raise ValueError("score_count must match rows")
    if explanation.pass_score_count != _status_count(rows, "pass"):
        raise ValueError("pass_score_count must match rows")
    if explanation.watch_score_count != _status_count(rows, "watch"):
        raise ValueError("watch_score_count must match rows")
    if explanation.block_score_count != _status_count(rows, "block"):
        raise ValueError("block_score_count must match rows")
    if explanation.public_status != _public_status(rows):
        raise ValueError("public_status must match rows")
    if explanation.weighted_score != _weighted_score(rows):
        raise ValueError("weighted_score must match rows")
    expected_reason_codes = _explanation_reason_codes(rows, explanation.public_status)
    if explanation.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_review_notes = _review_notes(rows, explanation.public_status)
    if explanation.review_notes != expected_review_notes:
        raise ValueError("review_notes must match rows")
    if explanation.explanation_digest != strategy_decision_explanation_digest(
        explanation.payload,
    ):
        raise ValueError("explanation_digest must match payload")


def _reject_unsupported_payload_fields(payload: dict[str, Any]) -> None:
    for key, value in payload.items():
        if type(key) is not str:
            raise ValueError("payload keys must be strings")
        if key not in PAYLOAD_FIELDS:
            raise ValueError("payload field is not supported")
        if key == "rows":
            if type(value) is not list:
                raise ValueError("rows must be a list")
            for row in value:
                if type(row) is not dict:
                    raise ValueError("rows must contain JSON objects")
                for row_key in row:
                    if type(row_key) is not str:
                        raise ValueError("row payload keys must be strings")
                    if row_key not in ROW_PAYLOAD_FIELDS:
                        raise ValueError("row payload field is not supported")


def _reject_public_payload_text(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _reject_restricted_public_text("payload field", key)
            _reject_public_payload_text(item)
    elif type(value) is list:
        for item in value:
            _reject_public_payload_text(item)
    elif type(value) is str:
        _reject_restricted_public_text("payload value", value)


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) in (int, float):
        raise ValueError("public numeric payload value must use Decimal")
    if type(value) is dict:
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


__all__ = (
    "PUBLIC_STATUSES",
    "StrategyDecisionExplainerScore",
    "StrategyDecisionExplanationRow",
    "StrategyDecisionExplanation",
    "build_strategy_decision_explanation",
    "strategy_decision_explanation_payload",
    "strategy_decision_explanation_digest",
)
