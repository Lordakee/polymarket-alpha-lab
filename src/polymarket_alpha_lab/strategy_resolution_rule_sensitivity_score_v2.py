"""Phase 1 readonly/report-only/paper-only resolution rule sensitivity score v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, InvalidOperation
import hashlib
from typing import Any


SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

REQUIRED_OBJECTIVE_RESOLUTION_CLAUSE_COUNT = Decimal("4.000000")
REQUIRED_SOURCE_BACKED_CLAUSE_COUNT = Decimal("3.000000")
REQUIRED_EDGE_CASE_EXCEPTION_COUNT = Decimal("2.000000")
REQUIRED_ADJUDICATION_PATH_COUNT = Decimal("1.000000")
AMBIGUOUS_WORDING_CAP = Decimal("5.000000")

WEIGHT_OBJECTIVE_CLAUSE_GAP = Decimal("0.200000")
WEIGHT_SOURCE_BACKING_GAP = Decimal("0.250000")
WEIGHT_AMBIGUOUS_WORDING = Decimal("0.350000")
WEIGHT_EDGE_CASE_GAP = Decimal("0.100000")
WEIGHT_ADJUDICATION_PATH_GAP = Decimal("0.100000")

WATCH_SENSITIVITY_THRESHOLD = Decimal("0.250000")
BLOCKED_SENSITIVITY_THRESHOLD = Decimal("0.750000")

SENSITIVITY_STATUSES = ("pass", "watch", "blocked")
RECOMMENDED_ACTIONS = (
    "keep_rule_in_candidate_scoring",
    "review_resolution_wording_before_scoring",
    "exclude_until_resolution_rule_is_rewritten",
)
REASON_CODES = (
    "sensitivity_status_pass",
    "sensitivity_status_watch",
    "sensitivity_status_blocked",
    "objective_resolution_clauses_complete",
    "objective_resolution_clauses_partial",
    "objective_resolution_clauses_missing",
    "source_backed_clarity_complete",
    "source_backed_clarity_partial",
    "source_backed_clarity_missing",
    "ambiguous_wording_clear",
    "ambiguous_wording_present",
    "ambiguous_wording_heavy",
    "edge_case_exceptions_complete",
    "edge_case_exceptions_partial",
    "edge_case_exceptions_missing",
    "adjudication_paths_complete",
    "adjudication_paths_missing",
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
PAYLOAD_FIELDS = (
    "rule_id",
    "rule_text_excerpt",
    "objective_resolution_clause_count",
    "source_backed_clause_count",
    "ambiguous_wording_count",
    "edge_case_exception_count",
    "adjudication_path_count",
    "objective_clause_gap_score",
    "source_backed_clarity_boost_score",
    "source_backing_gap_score",
    "ambiguous_wording_penalty_score",
    "edge_case_gap_score",
    "adjudication_path_gap_score",
    "rule_sensitivity_score",
    "sensitivity_status",
    "recommended_action",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
DIGEST_FIELDS = tuple(field for field in PAYLOAD_FIELDS if field != "derived_validation_digest")


@dataclass(frozen=True)
class StrategyResolutionRuleSensitivityScoreV2Config:
    config_version: str = "strategy-resolution-rule-sensitivity-score-v2"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionRuleSensitivityScoreV2Config:
            raise ValueError(
                "config must be a StrategyResolutionRuleSensitivityScoreV2Config",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_hard_flags(self)
        _reject_unsafe_public_payload("config", asdict(self))


@dataclass(frozen=True)
class StrategyResolutionRuleSensitivityScoreV2Input:
    rule_id: str
    rule_text_excerpt: str
    objective_resolution_clause_count: Decimal
    source_backed_clause_count: Decimal
    ambiguous_wording_count: Decimal
    edge_case_exception_count: Decimal
    adjudication_path_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionRuleSensitivityScoreV2Input:
            raise ValueError(
                "input_row must be a StrategyResolutionRuleSensitivityScoreV2Input",
            )
        _require_identifier("rule_id", self.rule_id)
        _require_canonical_string("rule_text_excerpt", self.rule_text_excerpt)
        for field_name in (
            "objective_resolution_clause_count",
            "source_backed_clause_count",
            "ambiguous_wording_count",
            "edge_case_exception_count",
            "adjudication_path_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.source_backed_clause_count > self.objective_resolution_clause_count:
            raise ValueError(
                "source_backed_clause_count cannot exceed "
                "objective_resolution_clause_count",
            )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("input_row", asdict(self))


@dataclass(frozen=True)
class StrategyResolutionRuleSensitivityScoreV2Report:
    rule_id: str
    rule_text_excerpt: str
    objective_resolution_clause_count: Decimal
    source_backed_clause_count: Decimal
    ambiguous_wording_count: Decimal
    edge_case_exception_count: Decimal
    adjudication_path_count: Decimal
    objective_clause_gap_score: Decimal
    source_backed_clarity_boost_score: Decimal
    source_backing_gap_score: Decimal
    ambiguous_wording_penalty_score: Decimal
    edge_case_gap_score: Decimal
    adjudication_path_gap_score: Decimal
    rule_sensitivity_score: Decimal
    sensitivity_status: str
    recommended_action: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionRuleSensitivityScoreV2Report:
            raise ValueError(
                "report must be a StrategyResolutionRuleSensitivityScoreV2Report",
            )
        _require_identifier("rule_id", self.rule_id)
        _require_canonical_string("rule_text_excerpt", self.rule_text_excerpt)
        for field_name in (
            "objective_resolution_clause_count",
            "source_backed_clause_count",
            "ambiguous_wording_count",
            "edge_case_exception_count",
            "adjudication_path_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.source_backed_clause_count > self.objective_resolution_clause_count:
            raise ValueError(
                "source_backed_clause_count cannot exceed "
                "objective_resolution_clause_count",
            )
        for field_name in (
            "objective_clause_gap_score",
            "source_backed_clarity_boost_score",
            "source_backing_gap_score",
            "ambiguous_wording_penalty_score",
            "edge_case_gap_score",
            "adjudication_path_gap_score",
            "rule_sensitivity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_choice("sensitivity_status", self.sensitivity_status, SENSITIVITY_STATUSES)
        _require_choice("recommended_action", self.recommended_action, RECOMMENDED_ACTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("report", asdict(self))
        _validate_report_consistency(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_derived_validation_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("payload", payload)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        return payload

    @classmethod
    def from_payload(
        cls,
        payload: object,
    ) -> StrategyResolutionRuleSensitivityScoreV2Report:
        _reject_unsafe_public_payload("payload", payload)
        payload_dict = _payload_dict("payload", payload)
        _require_payload_fields(payload_dict, PAYLOAD_FIELDS)
        values = _report_values_from_payload(payload_dict)
        expected_digest = _derived_validation_digest_values(**values)
        supplied_digest = _normalize_derived_validation_digest(
            "derived_validation_digest",
            payload_dict["derived_validation_digest"],
        )
        if supplied_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        return cls(**values, derived_validation_digest=supplied_digest)


def build_strategy_resolution_rule_sensitivity_score_v2(
    input_row: StrategyResolutionRuleSensitivityScoreV2Input,
) -> StrategyResolutionRuleSensitivityScoreV2Report:
    if type(input_row) is not StrategyResolutionRuleSensitivityScoreV2Input:
        raise ValueError("input_row must be a StrategyResolutionRuleSensitivityScoreV2Input")
    _require_hard_flags(input_row)
    _reject_unsafe_public_payload("input_row", asdict(input_row))

    scores = _score_values(input_row)
    sensitivity_status = _sensitivity_status(scores["rule_sensitivity_score"])
    return StrategyResolutionRuleSensitivityScoreV2Report(
        rule_id=input_row.rule_id,
        rule_text_excerpt=input_row.rule_text_excerpt,
        objective_resolution_clause_count=input_row.objective_resolution_clause_count,
        source_backed_clause_count=input_row.source_backed_clause_count,
        ambiguous_wording_count=input_row.ambiguous_wording_count,
        edge_case_exception_count=input_row.edge_case_exception_count,
        adjudication_path_count=input_row.adjudication_path_count,
        objective_clause_gap_score=scores["objective_clause_gap_score"],
        source_backed_clarity_boost_score=scores[
            "source_backed_clarity_boost_score"
        ],
        source_backing_gap_score=scores["source_backing_gap_score"],
        ambiguous_wording_penalty_score=scores["ambiguous_wording_penalty_score"],
        edge_case_gap_score=scores["edge_case_gap_score"],
        adjudication_path_gap_score=scores["adjudication_path_gap_score"],
        rule_sensitivity_score=scores["rule_sensitivity_score"],
        sensitivity_status=sensitivity_status,
        recommended_action=_recommended_action(sensitivity_status),
        reason_codes=_reason_codes(input_row, sensitivity_status),
    )


def strategy_resolution_rule_sensitivity_score_v2_payload(
    report: StrategyResolutionRuleSensitivityScoreV2Report,
) -> dict[str, object]:
    if type(report) is not StrategyResolutionRuleSensitivityScoreV2Report:
        raise ValueError("report must be a StrategyResolutionRuleSensitivityScoreV2Report")
    _require_hard_flags(report)
    _reject_unsafe_public_payload("report", asdict(report))
    return report.payload


def _score_values(
    input_row: StrategyResolutionRuleSensitivityScoreV2Input,
) -> dict[str, Decimal]:
    objective_clause_gap_score = ONE - _ratio_capped(
        input_row.objective_resolution_clause_count,
        REQUIRED_OBJECTIVE_RESOLUTION_CLAUSE_COUNT,
    )
    source_backed_clarity_boost_score = _ratio_capped(
        input_row.source_backed_clause_count,
        REQUIRED_SOURCE_BACKED_CLAUSE_COUNT,
    )
    source_backing_gap_score = ONE - source_backed_clarity_boost_score
    ambiguous_wording_penalty_score = _ratio_capped(
        input_row.ambiguous_wording_count,
        AMBIGUOUS_WORDING_CAP,
    )
    edge_case_gap_score = ONE - _ratio_capped(
        input_row.edge_case_exception_count,
        REQUIRED_EDGE_CASE_EXCEPTION_COUNT,
    )
    adjudication_path_gap_score = ONE - _ratio_capped(
        input_row.adjudication_path_count,
        REQUIRED_ADJUDICATION_PATH_COUNT,
    )
    rule_sensitivity_score = _q(
        (objective_clause_gap_score * WEIGHT_OBJECTIVE_CLAUSE_GAP)
        + (source_backing_gap_score * WEIGHT_SOURCE_BACKING_GAP)
        + (ambiguous_wording_penalty_score * WEIGHT_AMBIGUOUS_WORDING)
        + (edge_case_gap_score * WEIGHT_EDGE_CASE_GAP)
        + (adjudication_path_gap_score * WEIGHT_ADJUDICATION_PATH_GAP),
    )
    return {
        "objective_clause_gap_score": objective_clause_gap_score,
        "source_backed_clarity_boost_score": source_backed_clarity_boost_score,
        "source_backing_gap_score": source_backing_gap_score,
        "ambiguous_wording_penalty_score": ambiguous_wording_penalty_score,
        "edge_case_gap_score": edge_case_gap_score,
        "adjudication_path_gap_score": adjudication_path_gap_score,
        "rule_sensitivity_score": rule_sensitivity_score,
    }


def _sensitivity_status(rule_sensitivity_score: Decimal) -> str:
    if rule_sensitivity_score >= BLOCKED_SENSITIVITY_THRESHOLD:
        return "blocked"
    if rule_sensitivity_score >= WATCH_SENSITIVITY_THRESHOLD:
        return "watch"
    return "pass"


def _recommended_action(sensitivity_status: str) -> str:
    if sensitivity_status == "pass":
        return "keep_rule_in_candidate_scoring"
    if sensitivity_status == "watch":
        return "review_resolution_wording_before_scoring"
    if sensitivity_status == "blocked":
        return "exclude_until_resolution_rule_is_rewritten"
    raise ValueError("sensitivity_status must be supported")


def _reason_codes(
    input_row: StrategyResolutionRuleSensitivityScoreV2Input,
    sensitivity_status: str,
) -> tuple[str, ...]:
    return (
        f"sensitivity_status_{sensitivity_status}",
        _objective_clause_reason(input_row.objective_resolution_clause_count),
        _source_backed_reason(input_row.source_backed_clause_count),
        _ambiguous_wording_reason(input_row.ambiguous_wording_count),
        _edge_case_reason(input_row.edge_case_exception_count),
        _adjudication_path_reason(input_row.adjudication_path_count),
    )


def _objective_clause_reason(value: Decimal) -> str:
    score = _ratio_capped(value, REQUIRED_OBJECTIVE_RESOLUTION_CLAUSE_COUNT)
    if score == ONE:
        return "objective_resolution_clauses_complete"
    if score == ZERO:
        return "objective_resolution_clauses_missing"
    return "objective_resolution_clauses_partial"


def _source_backed_reason(value: Decimal) -> str:
    score = _ratio_capped(value, REQUIRED_SOURCE_BACKED_CLAUSE_COUNT)
    if score == ONE:
        return "source_backed_clarity_complete"
    if score == ZERO:
        return "source_backed_clarity_missing"
    return "source_backed_clarity_partial"


def _ambiguous_wording_reason(value: Decimal) -> str:
    score = _ratio_capped(value, AMBIGUOUS_WORDING_CAP)
    if score == ONE:
        return "ambiguous_wording_heavy"
    if value > ZERO:
        return "ambiguous_wording_present"
    return "ambiguous_wording_clear"


def _edge_case_reason(value: Decimal) -> str:
    score = _ratio_capped(value, REQUIRED_EDGE_CASE_EXCEPTION_COUNT)
    if score == ONE:
        return "edge_case_exceptions_complete"
    if score == ZERO:
        return "edge_case_exceptions_missing"
    return "edge_case_exceptions_partial"


def _adjudication_path_reason(value: Decimal) -> str:
    if _ratio_capped(value, REQUIRED_ADJUDICATION_PATH_COUNT) == ONE:
        return "adjudication_paths_complete"
    return "adjudication_paths_missing"


def _validate_report_consistency(
    report: StrategyResolutionRuleSensitivityScoreV2Report,
) -> None:
    input_row = StrategyResolutionRuleSensitivityScoreV2Input(
        rule_id=report.rule_id,
        rule_text_excerpt=report.rule_text_excerpt,
        objective_resolution_clause_count=report.objective_resolution_clause_count,
        source_backed_clause_count=report.source_backed_clause_count,
        ambiguous_wording_count=report.ambiguous_wording_count,
        edge_case_exception_count=report.edge_case_exception_count,
        adjudication_path_count=report.adjudication_path_count,
    )
    scores = _score_values(input_row)
    for field_name, expected_value in scores.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match derived score")
    expected_status = _sensitivity_status(report.rule_sensitivity_score)
    if report.sensitivity_status != expected_status:
        raise ValueError("sensitivity_status must match rule_sensitivity_score")
    expected_action = _recommended_action(report.sensitivity_status)
    if report.recommended_action != expected_action:
        raise ValueError("recommended_action must match sensitivity_status")
    expected_reason_codes = _reason_codes(input_row, report.sensitivity_status)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match report fields")


def _ratio_capped(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    if numerator <= ZERO:
        return ZERO
    value = numerator / denominator
    if value >= ONE:
        return ONE
    return _q(value)


def _normalize_whole_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return decimal_value


def _normalize_probability(name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return decimal_value


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        return value.quantize(SCORE_QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must use six decimal places") from exc


def _q(value: Decimal) -> Decimal:
    try:
        return value.quantize(SCORE_QUANT)
    except InvalidOperation as exc:
        raise ValueError("score must use six decimal places") from exc


def _require_identifier(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    if not str(value).replace("-", "").replace("_", "").isalnum():
        raise ValueError(f"{name} must be an identifier")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{name} must be a canonical non-empty string")


def _require_choice(name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{name} must be supported")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or len(value) == 0:
        raise ValueError("reason_codes must be a non-empty tuple")
    values: list[str] = []
    for item in value:
        _require_choice("reason_codes", item, REASON_CODES)
        values.append(item)
    return tuple(values)


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_term(key):
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_payload(f"{label}.{key}", child)
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", child)
        return
    if type(value) is str and _has_unsafe_public_term(value):
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is int:
        raise ValueError(f"{label} must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError(f"{label} must not use float values")


def _has_unsafe_public_term(value: str) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in UNSAFE_PUBLIC_TERMS)


def _payload_value(value: Any) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return str(value)
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if type(value) in (int, float):
        raise ValueError("payload numeric values must be Decimal")
    if isinstance(value, dict):
        payload: dict[str, object] = {}
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            payload[key] = _payload_value(child)
        return payload
    if isinstance(value, (list, tuple)):
        return [_payload_value(child) for child in value]
    raise ValueError("payload value is not JSON serializable")


def _payload_dict(label: str, value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    return value


def _require_payload_fields(
    payload: dict[str, object],
    expected_fields: tuple[str, ...],
) -> None:
    expected_set = set(expected_fields)
    actual_set = set(payload)
    missing = expected_set - actual_set
    extra = actual_set - expected_set
    if missing:
        raise ValueError(f"payload missing field {sorted(missing)[0]}")
    if extra:
        raise ValueError(f"payload has unexpected field {sorted(extra)[0]}")


def _report_values_from_payload(
    payload: dict[str, object],
) -> dict[str, object]:
    values: dict[str, object] = {
        "rule_id": payload["rule_id"],
        "rule_text_excerpt": payload["rule_text_excerpt"],
        "objective_resolution_clause_count": _decimal_from_payload(
            "objective_resolution_clause_count",
            payload["objective_resolution_clause_count"],
        ),
        "source_backed_clause_count": _decimal_from_payload(
            "source_backed_clause_count",
            payload["source_backed_clause_count"],
        ),
        "ambiguous_wording_count": _decimal_from_payload(
            "ambiguous_wording_count",
            payload["ambiguous_wording_count"],
        ),
        "edge_case_exception_count": _decimal_from_payload(
            "edge_case_exception_count",
            payload["edge_case_exception_count"],
        ),
        "adjudication_path_count": _decimal_from_payload(
            "adjudication_path_count",
            payload["adjudication_path_count"],
        ),
        "objective_clause_gap_score": _decimal_from_payload(
            "objective_clause_gap_score",
            payload["objective_clause_gap_score"],
        ),
        "source_backed_clarity_boost_score": _decimal_from_payload(
            "source_backed_clarity_boost_score",
            payload["source_backed_clarity_boost_score"],
        ),
        "source_backing_gap_score": _decimal_from_payload(
            "source_backing_gap_score",
            payload["source_backing_gap_score"],
        ),
        "ambiguous_wording_penalty_score": _decimal_from_payload(
            "ambiguous_wording_penalty_score",
            payload["ambiguous_wording_penalty_score"],
        ),
        "edge_case_gap_score": _decimal_from_payload(
            "edge_case_gap_score",
            payload["edge_case_gap_score"],
        ),
        "adjudication_path_gap_score": _decimal_from_payload(
            "adjudication_path_gap_score",
            payload["adjudication_path_gap_score"],
        ),
        "rule_sensitivity_score": _decimal_from_payload(
            "rule_sensitivity_score",
            payload["rule_sensitivity_score"],
        ),
        "sensitivity_status": payload["sensitivity_status"],
        "recommended_action": payload["recommended_action"],
        "reason_codes": _string_tuple_from_payload("reason_codes", payload["reason_codes"]),
        "paper_only": payload["paper_only"],
        "report_only": payload["report_only"],
        "readonly": payload["readonly"],
    }
    return values


def _decimal_from_payload(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc
    return _normalize_decimal(name, decimal_value)


def _string_tuple_from_payload(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list")
    values: list[str] = []
    for item in value:
        if type(item) is not str:
            raise ValueError(f"{name} values must be strings")
        values.append(item)
    return tuple(values)


def _normalize_derived_validation_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a sha256 hex digest") from exc
    return value.lower()


def _derived_validation_digest(
    report: StrategyResolutionRuleSensitivityScoreV2Report,
) -> str:
    values = {
        field: getattr(report, field)
        for field in DIGEST_FIELDS
    }
    return _derived_validation_digest_values(**values)


def _derived_validation_digest_values(**values: object) -> str:
    payload = {
        field: _payload_value(values[field])
        for field in DIGEST_FIELDS
    }
    _reject_unsafe_public_payload("digest payload", payload)
    blob = _canonical_digest_blob(payload)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _canonical_digest_blob(value: object) -> str:
    if type(value) is dict:
        parts = []
        for key in sorted(value):
            parts.append(f"{key}:{_canonical_digest_blob(value[key])}")
        return "{" + ",".join(parts) + "}"
    if type(value) is list:
        return "[" + ",".join(_canonical_digest_blob(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return repr(value)
    if value is None:
        return "null"
    raise ValueError("digest payload is not canonical")


__all__ = (
    "SENSITIVITY_STATUSES",
    "RECOMMENDED_ACTIONS",
    "REASON_CODES",
    "StrategyResolutionRuleSensitivityScoreV2Config",
    "StrategyResolutionRuleSensitivityScoreV2Input",
    "StrategyResolutionRuleSensitivityScoreV2Report",
    "build_strategy_resolution_rule_sensitivity_score_v2",
    "strategy_resolution_rule_sensitivity_score_v2_payload",
)
