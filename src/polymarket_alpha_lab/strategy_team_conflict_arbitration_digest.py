"""Pure Phase 1 reducer for team recommendation conflict arbitration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_TEAM_CONFLICT_ARBITRATION_CONFIG_VERSION = (
    "strategy-team-conflict-arbitration-digest-v0"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ZERO_SECONDS = Decimal("0.000000")
ZERO_EDGE = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
NEGATIVE_ONE_RATIO = Decimal("-1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

REDACTED_EVIDENCE_REFERENCE = "<redacted-evidence-reference>"
SENSITIVE_PUBLIC_VALUE_TOKENS = (
    "secret",
    "token",
    "private",
    "key",
    "bearer",
    "dsn",
    "password",
)
UNSAFE_PUBLIC_VALUE_TOKENS = (
    "auth",
    "wallet",
    "account",
    "balance",
    "order",
    "cancel",
    "replace",
    "sign",
    "signed",
    "signing",
    "signature",
    "live",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "://",
    "sk_live",
    "pk_live",
    "exchange_mutation",
    "private_key",
)

SELECTED_SIDES = ("yes", "no")
INPUT_PAPER_RECOMMENDATION_STATUSES = ("recommend", "watch", "defer", "reject")
EVIDENCE_FRESHNESS_STATUSES = ("fresh", "stale")
CHOSEN_PAPER_RECOMMENDATION_STATUSES = (
    "paper_recommend",
    "paper_watch",
    "paper_defer",
)
REPORT_STATUSES = ("clear", "watch", "blocked")
DECISION_REASON_CODES = (
    "side_disagreement",
    "probability_dispersion_high",
    "stale_evidence",
    "low_historical_calibration",
    "negative_cost_adjusted_edge",
    "paper_defer_conflict_arbitration",
    "paper_watch_conflict_arbitration",
    "paper_recommend_conflict_arbitration",
)
REPORT_REASON_CODES = (
    "side_disagreement",
    "probability_dispersion_high",
    "stale_evidence",
    "low_historical_calibration",
    "negative_cost_adjusted_edge",
    "paper_defer_conflict_arbitration",
    "paper_watch_conflict_arbitration",
    "paper_recommend_conflict_arbitration",
    "team_conflict_arbitration_digest_clear",
)
DEFER_REASON_CODES = frozenset(
    (
        "stale_evidence",
        "low_historical_calibration",
        "negative_cost_adjusted_edge",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "side_disagreement",
        "probability_dispersion_high",
    ),
)
STATUS_REASON_CODE = {
    "paper_recommend": "paper_recommend_conflict_arbitration",
    "paper_watch": "paper_watch_conflict_arbitration",
    "paper_defer": "paper_defer_conflict_arbitration",
}
INPUT_STATUS_PRIORITY = {
    "recommend": Decimal("3"),
    "watch": Decimal("2"),
    "defer": Decimal("1"),
    "reject": Decimal("0"),
}
DECISION_STATUS_WEIGHT = {
    "paper_defer": Decimal("2"),
    "paper_watch": Decimal("1"),
    "paper_recommend": Decimal("0"),
}
REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "reason_codes",
        "input_count",
        "candidate_count",
        "paper_recommend_count",
        "paper_watch_count",
        "paper_defer_count",
        "max_conflict_severity",
        "conflicted_candidate_ratio",
        "reason_code_counts",
        "decisions",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
DECISION_PAYLOAD_FIELDS = frozenset(
    (
        "candidate_id",
        "chosen_recommendation_id",
        "team_id",
        "category_id",
        "selected_side",
        "model_probability",
        "confidence",
        "evidence_freshness",
        "evidence_age_seconds",
        "historical_calibration",
        "cost_adjusted_edge",
        "conflict_severity",
        "chosen_paper_recommendation_status",
        "team_count",
        "side_count",
        "source_config_version",
        "evidence_reference",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


@dataclass(frozen=True)
class StrategyTeamConflictArbitrationConfig:
    config_version: str = DEFAULT_STRATEGY_TEAM_CONFLICT_ARBITRATION_CONFIG_VERSION
    max_fresh_evidence_age_seconds: Decimal = Decimal("7200.000000")
    max_probability_dispersion: Decimal = Decimal("0.050000")
    min_historical_calibration: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyTeamConflictArbitrationConfig:
            raise ValueError(
                "config must be a StrategyTeamConflictArbitrationConfig",
            )
        _require_public_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_fresh_evidence_age_seconds",
            _normalize_positive_seconds(
                "max_fresh_evidence_age_seconds",
                self.max_fresh_evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "max_probability_dispersion",
            _normalize_ratio("max_probability_dispersion", self.max_probability_dispersion),
        )
        object.__setattr__(
            self,
            "min_historical_calibration",
            _normalize_ratio("min_historical_calibration", self.min_historical_calibration),
        )
        require_paper_only_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class StrategyTeamConflictRecommendation:
    recommendation_id: str
    candidate_id: str
    team_id: str
    category_id: str
    selected_side: str
    paper_recommendation_status: str
    model_probability: Decimal
    confidence: Decimal
    evidence_observed_at: datetime
    historical_calibration: Decimal
    cost_adjusted_edge: Decimal
    source_config_version: str
    evidence_reference: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyTeamConflictRecommendation:
            raise ValueError(
                "recommendation must be a StrategyTeamConflictRecommendation",
            )
        for field_name in (
            "recommendation_id",
            "candidate_id",
            "team_id",
            "category_id",
            "source_config_version",
        ):
            _require_public_canonical_string(field_name, getattr(self, field_name))
        _require_member("selected_side", self.selected_side, SELECTED_SIDES)
        _require_member(
            "paper_recommendation_status",
            self.paper_recommendation_status,
            INPUT_PAPER_RECOMMENDATION_STATUSES,
        )
        for field_name in (
            "model_probability",
            "confidence",
            "historical_calibration",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_edge("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "evidence_reference",
            _redact_evidence_reference(self.evidence_reference),
        )
        require_paper_only_flags("recommendation", self)
        _reject_unsafe_public_payload("recommendation", self)


@dataclass(frozen=True)
class StrategyTeamConflictArbitrationDecision:
    candidate_id: str
    chosen_recommendation_id: str
    team_id: str
    category_id: str
    selected_side: str
    model_probability: Decimal
    confidence: Decimal
    evidence_freshness: str
    evidence_age_seconds: Decimal
    historical_calibration: Decimal
    cost_adjusted_edge: Decimal
    conflict_severity: Decimal
    chosen_paper_recommendation_status: str
    team_count: Decimal
    side_count: Decimal
    source_config_version: str
    evidence_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyTeamConflictArbitrationDecision:
            raise ValueError(
                "decision must be a StrategyTeamConflictArbitrationDecision",
            )
        for field_name in (
            "candidate_id",
            "chosen_recommendation_id",
            "team_id",
            "category_id",
            "source_config_version",
        ):
            _require_public_canonical_string(field_name, getattr(self, field_name))
        _require_member("selected_side", self.selected_side, SELECTED_SIDES)
        _require_member(
            "evidence_freshness",
            self.evidence_freshness,
            EVIDENCE_FRESHNESS_STATUSES,
        )
        _require_member(
            "chosen_paper_recommendation_status",
            self.chosen_paper_recommendation_status,
            CHOSEN_PAPER_RECOMMENDATION_STATUSES,
        )
        for field_name in (
            "model_probability",
            "confidence",
            "historical_calibration",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_edge("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _normalize_seconds("evidence_age_seconds", self.evidence_age_seconds),
        )
        object.__setattr__(
            self,
            "conflict_severity",
            _normalize_count("conflict_severity", self.conflict_severity),
        )
        object.__setattr__(
            self,
            "team_count",
            _normalize_count("team_count", self.team_count),
        )
        object.__setattr__(
            self,
            "side_count",
            _normalize_count("side_count", self.side_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                DECISION_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "evidence_reference",
            _redact_evidence_reference(self.evidence_reference),
        )
        _validate_decision(self)
        require_paper_only_flags("decision", self)
        _reject_unsafe_public_payload("decision", self)


@dataclass(frozen=True)
class StrategyTeamConflictArbitrationReport:
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    input_count: Decimal
    candidate_count: Decimal
    paper_recommend_count: Decimal
    paper_watch_count: Decimal
    paper_defer_count: Decimal
    max_conflict_severity: Decimal
    conflicted_candidate_ratio: Decimal
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    decisions: tuple[StrategyTeamConflictArbitrationDecision, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyTeamConflictArbitrationReport:
            raise ValueError(
                "report must be a StrategyTeamConflictArbitrationReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_canonical_string("config_version", self.config_version)
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        for field_name in (
            "input_count",
            "candidate_count",
            "paper_recommend_count",
            "paper_watch_count",
            "paper_defer_count",
            "max_conflict_severity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "conflicted_candidate_ratio",
            _normalize_ratio("conflicted_candidate_ratio", self.conflicted_candidate_ratio),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "decisions", _normalize_decisions(self.decisions))
        _validate_report(self)
        require_paper_only_flags("report", self)
        _reject_unsafe_public_payload("report", self)


def build_strategy_team_conflict_arbitration_digest(
    recommendations: object,
    *,
    config: StrategyTeamConflictArbitrationConfig,
    generated_at: datetime,
) -> StrategyTeamConflictArbitrationReport:
    if type(config) is not StrategyTeamConflictArbitrationConfig:
        raise ValueError("config must be a StrategyTeamConflictArbitrationConfig")
    require_paper_only_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_recommendations(recommendations, generated_at_utc)
    decisions = tuple(
        sorted(
            (
                _decision_for_candidate(candidate_rows, generated_at_utc, config)
                for candidate_rows in _candidate_groups(rows)
            ),
            key=_decision_sort_key,
        ),
    )
    return StrategyTeamConflictArbitrationReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(decisions),
        reason_codes=_report_reason_codes(decisions),
        input_count=_count(len(rows)),
        candidate_count=_count(len(decisions)),
        paper_recommend_count=_decision_status_count(decisions, "paper_recommend"),
        paper_watch_count=_decision_status_count(decisions, "paper_watch"),
        paper_defer_count=_decision_status_count(decisions, "paper_defer"),
        max_conflict_severity=_max_conflict_severity(decisions),
        conflicted_candidate_ratio=_ratio(
            len(tuple(decision for decision in decisions if decision.conflict_severity > ZERO_COUNT)),
            len(decisions),
        ),
        reason_code_counts=_reason_code_counts(decisions),
        decisions=decisions,
    )


def strategy_team_conflict_arbitration_digest_payload(
    report: StrategyTeamConflictArbitrationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyTeamConflictArbitrationReport:
        require_paper_only_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = json_ready_no_floats(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("report payload", report)
        _reject_public_numeric_payload(report)
        payload = json_ready_no_floats(report)
    else:
        raise ValueError("report must be a StrategyTeamConflictArbitrationReport")
    if type(payload) is not dict:
        raise ValueError("report must convert to a JSON object")
    require_paper_only_flags("report payload", _DictFlags(payload))
    _reject_unsafe_public_payload("report payload", payload)
    _validate_report_payload(payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        if "paper_only" not in self.value:
            return None
        return self.value["paper_only"]

    @property
    def report_only(self) -> object:
        if "report_only" not in self.value:
            return None
        return self.value["report_only"]

    @property
    def readonly(self) -> object:
        if "readonly" not in self.value:
            return None
        return self.value["readonly"]


def _validate_report_payload(payload: dict[str, Any]) -> None:
    _require_payload_keys("report payload", payload, REPORT_PAYLOAD_FIELDS)
    report = StrategyTeamConflictArbitrationReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        status=_payload_string("status", payload["status"]),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        input_count=_payload_decimal("input_count", payload["input_count"]),
        candidate_count=_payload_decimal("candidate_count", payload["candidate_count"]),
        paper_recommend_count=_payload_decimal(
            "paper_recommend_count",
            payload["paper_recommend_count"],
        ),
        paper_watch_count=_payload_decimal(
            "paper_watch_count",
            payload["paper_watch_count"],
        ),
        paper_defer_count=_payload_decimal(
            "paper_defer_count",
            payload["paper_defer_count"],
        ),
        max_conflict_severity=_payload_decimal(
            "max_conflict_severity",
            payload["max_conflict_severity"],
        ),
        conflicted_candidate_ratio=_payload_decimal(
            "conflicted_candidate_ratio",
            payload["conflicted_candidate_ratio"],
        ),
        reason_code_counts=_payload_reason_code_counts(payload["reason_code_counts"]),
        decisions=_payload_decisions(payload["decisions"]),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )
    expected_payload = json_ready_no_floats(report)
    if expected_payload != payload:
        raise ValueError("report payload must match derived validation")


def _payload_decisions(
    value: object,
) -> tuple[StrategyTeamConflictArbitrationDecision, ...]:
    if type(value) is not list:
        raise ValueError("decisions must be a list")
    return tuple(_payload_decision(item) for item in value)


def _payload_decision(value: object) -> StrategyTeamConflictArbitrationDecision:
    if type(value) is not dict:
        raise ValueError("decisions must contain JSON objects")
    _require_payload_keys("decision payload", value, DECISION_PAYLOAD_FIELDS)
    return StrategyTeamConflictArbitrationDecision(
        candidate_id=_payload_string("candidate_id", value["candidate_id"]),
        chosen_recommendation_id=_payload_string(
            "chosen_recommendation_id",
            value["chosen_recommendation_id"],
        ),
        team_id=_payload_string("team_id", value["team_id"]),
        category_id=_payload_string("category_id", value["category_id"]),
        selected_side=_payload_string("selected_side", value["selected_side"]),
        model_probability=_payload_decimal(
            "model_probability",
            value["model_probability"],
        ),
        confidence=_payload_decimal("confidence", value["confidence"]),
        evidence_freshness=_payload_string(
            "evidence_freshness",
            value["evidence_freshness"],
        ),
        evidence_age_seconds=_payload_decimal(
            "evidence_age_seconds",
            value["evidence_age_seconds"],
        ),
        historical_calibration=_payload_decimal(
            "historical_calibration",
            value["historical_calibration"],
        ),
        cost_adjusted_edge=_payload_decimal(
            "cost_adjusted_edge",
            value["cost_adjusted_edge"],
        ),
        conflict_severity=_payload_decimal(
            "conflict_severity",
            value["conflict_severity"],
        ),
        chosen_paper_recommendation_status=_payload_string(
            "chosen_paper_recommendation_status",
            value["chosen_paper_recommendation_status"],
        ),
        team_count=_payload_decimal("team_count", value["team_count"]),
        side_count=_payload_decimal("side_count", value["side_count"]),
        source_config_version=_payload_string(
            "source_config_version",
            value["source_config_version"],
        ),
        evidence_reference=_payload_string(
            "evidence_reference",
            value["evidence_reference"],
        ),
        reason_codes=_payload_string_tuple("reason_codes", value["reason_codes"]),
        paper_only=_payload_flag("paper_only", value["paper_only"]),
        report_only=_payload_flag("report_only", value["report_only"]),
        readonly=_payload_flag("readonly", value["readonly"]),
    )


def _payload_reason_code_counts(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list")
    pairs: list[tuple[str, Decimal]] = []
    for item in value:
        if type(item) is not list or len(item) != 2:
            raise ValueError("reason_code_counts items must be pairs")
        pairs.append(
            (
                _payload_string("reason_code_counts", item[0]),
                _payload_decimal("reason_code_counts", item[1]),
            ),
        )
    return tuple(pairs)


def _require_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_fields: frozenset[str],
) -> None:
    fields = frozenset(payload)
    missing_fields = expected_fields - fields
    if missing_fields:
        raise ValueError(f"{label} missing fields: {', '.join(sorted(missing_fields))}")
    unexpected_fields = fields - expected_fields
    if unexpected_fields:
        raise ValueError(
            f"{label} unexpected fields: {', '.join(sorted(unexpected_fields))}",
        )


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc


def _payload_string(field_name: str, value: object) -> str:
    _require_public_canonical_string(field_name, value)
    return value


def _payload_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(_payload_string(field_name, item) for item in value)


def _payload_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True for report payload")
    return True


def _decision_for_candidate(
    rows: tuple[StrategyTeamConflictRecommendation, ...],
    generated_at: datetime,
    config: StrategyTeamConflictArbitrationConfig,
) -> StrategyTeamConflictArbitrationDecision:
    chosen = _choose_recommendation(rows, generated_at)
    evidence_age_seconds = _age_seconds(generated_at, chosen.evidence_observed_at)
    evidence_freshness = (
        "fresh"
        if evidence_age_seconds <= config.max_fresh_evidence_age_seconds
        else "stale"
    )
    side_count = _count(len(frozenset(row.selected_side for row in rows)))
    team_count = _count(len(frozenset(row.team_id for row in rows)))
    reason_codes_without_status = _decision_reasons(
        rows,
        chosen,
        evidence_freshness,
        config,
    )
    chosen_status = _chosen_paper_status(chosen, reason_codes_without_status)
    reason_codes = reason_codes_without_status + (STATUS_REASON_CODE[chosen_status],)
    return StrategyTeamConflictArbitrationDecision(
        candidate_id=chosen.candidate_id,
        chosen_recommendation_id=chosen.recommendation_id,
        team_id=chosen.team_id,
        category_id=chosen.category_id,
        selected_side=chosen.selected_side,
        model_probability=chosen.model_probability,
        confidence=chosen.confidence,
        evidence_freshness=evidence_freshness,
        evidence_age_seconds=evidence_age_seconds,
        historical_calibration=chosen.historical_calibration,
        cost_adjusted_edge=chosen.cost_adjusted_edge,
        conflict_severity=_count(len(reason_codes_without_status)),
        chosen_paper_recommendation_status=chosen_status,
        team_count=team_count,
        side_count=side_count,
        source_config_version=chosen.source_config_version,
        evidence_reference=chosen.evidence_reference,
        reason_codes=reason_codes,
    )


def _decision_reasons(
    rows: tuple[StrategyTeamConflictRecommendation, ...],
    chosen: StrategyTeamConflictRecommendation,
    evidence_freshness: str,
    config: StrategyTeamConflictArbitrationConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    sides = frozenset(row.selected_side for row in rows)
    if len(sides) > 1:
        reasons.append("side_disagreement")
    probabilities = tuple(row.model_probability for row in rows)
    with localcontext(DECIMAL_CONTEXT):
        probability_dispersion = (
            max(probabilities) - min(probabilities)
            if probabilities
            else ZERO_RATIO
        ).quantize(RATIO_QUANTUM)
    if probability_dispersion > config.max_probability_dispersion:
        reasons.append("probability_dispersion_high")
    if evidence_freshness == "stale":
        reasons.append("stale_evidence")
    if chosen.historical_calibration < config.min_historical_calibration:
        reasons.append("low_historical_calibration")
    if chosen.cost_adjusted_edge.is_signed() and chosen.cost_adjusted_edge <= ZERO_EDGE:
        reasons.append("negative_cost_adjusted_edge")
    if not reasons:
        return ()
    return _normalize_reason_codes("reason_codes", tuple(reasons), DECISION_REASON_CODES)

def _chosen_paper_status(
    chosen: StrategyTeamConflictRecommendation,
    reason_codes: tuple[str, ...],
) -> str:
    if chosen.paper_recommendation_status in ("defer", "reject"):
        return "paper_defer"
    if any(reason_code in DEFER_REASON_CODES for reason_code in reason_codes):
        return "paper_defer"
    if chosen.paper_recommendation_status == "watch":
        return "paper_watch"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "paper_watch"
    return "paper_recommend"


def _choose_recommendation(
    rows: tuple[StrategyTeamConflictRecommendation, ...],
    generated_at: datetime,
) -> StrategyTeamConflictRecommendation:
    return tuple(sorted(rows, key=lambda row: _recommendation_sort_key(row, generated_at)))[0]


def _recommendation_sort_key(
    row: StrategyTeamConflictRecommendation,
    generated_at: datetime,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str, str, str]:
    return (
        -INPUT_STATUS_PRIORITY[row.paper_recommendation_status],
        -row.cost_adjusted_edge,
        -row.confidence,
        -row.historical_calibration,
        -row.model_probability,
        _age_seconds(generated_at, row.evidence_observed_at),
        row.team_id,
        row.category_id,
        row.recommendation_id,
    )


def _candidate_groups(
    rows: tuple[StrategyTeamConflictRecommendation, ...],
) -> tuple[tuple[StrategyTeamConflictRecommendation, ...], ...]:
    grouped: dict[str, list[StrategyTeamConflictRecommendation]] = {}
    for row in rows:
        if row.candidate_id not in grouped:
            grouped[row.candidate_id] = []
        grouped[row.candidate_id].append(row)
    groups = []
    for candidate_id in sorted(grouped):
        groups.append(tuple(sorted(grouped[candidate_id], key=lambda row: row.recommendation_id)))
    return tuple(groups)


def _normalize_recommendations(
    value: object,
    generated_at: datetime,
) -> tuple[StrategyTeamConflictRecommendation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("recommendations must be a list or tuple")
    rows = tuple(value)
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyTeamConflictRecommendation:
            raise ValueError(
                "recommendations must contain StrategyTeamConflictRecommendation values",
            )
        require_paper_only_flags("recommendation", row)
        _reject_unsafe_public_payload("recommendation", row)
        if row.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must not be in the future")
        if row.recommendation_id in seen_ids:
            raise ValueError(
                "recommendations must not contain duplicate recommendation_id values",
            )
        seen_ids.add(row.recommendation_id)
    return tuple(sorted(rows, key=lambda row: (row.candidate_id, row.recommendation_id)))


def _normalize_decisions(
    value: object,
) -> tuple[StrategyTeamConflictArbitrationDecision, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("decisions must be a list or tuple")
    decisions = tuple(value)
    seen_candidates: set[str] = set()
    for decision in decisions:
        if type(decision) is not StrategyTeamConflictArbitrationDecision:
            raise ValueError(
                "decisions must contain StrategyTeamConflictArbitrationDecision values",
            )
        require_paper_only_flags("decision", decision)
        _reject_unsafe_public_payload("decision", decision)
        if decision.candidate_id in seen_candidates:
            raise ValueError("decisions must not contain duplicate candidate_id values")
        seen_candidates.add(decision.candidate_id)
    return decisions


def _decision_sort_key(
    decision: StrategyTeamConflictArbitrationDecision,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        -DECISION_STATUS_WEIGHT[decision.chosen_paper_recommendation_status],
        -decision.conflict_severity,
        -decision.cost_adjusted_edge,
        decision.candidate_id,
        decision.chosen_recommendation_id,
    )


def _validate_decision(decision: StrategyTeamConflictArbitrationDecision) -> None:
    status_reason = STATUS_REASON_CODE[decision.chosen_paper_recommendation_status]
    if status_reason not in decision.reason_codes:
        raise ValueError("reason_codes must include chosen status reason")
    status_reason_count = sum(
        1 for reason_code in decision.reason_codes if reason_code in STATUS_REASON_CODE.values()
    )
    if status_reason_count != 1:
        raise ValueError("reason_codes must include exactly one chosen status reason")
    expected_severity = _count(
        len(tuple(reason_code for reason_code in decision.reason_codes if reason_code != status_reason)),
    )
    if decision.conflict_severity != expected_severity:
        raise ValueError("conflict_severity must match reason_codes")
    if decision.team_count <= ZERO_COUNT:
        raise ValueError("team_count must be positive")
    if decision.side_count <= ZERO_COUNT:
        raise ValueError("side_count must be positive")
    if decision.evidence_freshness == "fresh" and "stale_evidence" in decision.reason_codes:
        raise ValueError("fresh evidence must not use stale_evidence reason")
    if (
        decision.chosen_paper_recommendation_status == "paper_recommend"
        and decision.conflict_severity != ZERO_COUNT
    ):
        raise ValueError("paper_recommend decisions must have zero conflict severity")


def _validate_report(report: StrategyTeamConflictArbitrationReport) -> None:
    if report.candidate_count != _count(len(report.decisions)):
        raise ValueError("candidate_count must match decisions")
    if report.input_count < report.candidate_count:
        raise ValueError("input_count must be greater than or equal to candidate_count")
    if report.paper_recommend_count != _decision_status_count(report.decisions, "paper_recommend"):
        raise ValueError("paper_recommend_count must match decisions")
    if report.paper_watch_count != _decision_status_count(report.decisions, "paper_watch"):
        raise ValueError("paper_watch_count must match decisions")
    if report.paper_defer_count != _decision_status_count(report.decisions, "paper_defer"):
        raise ValueError("paper_defer_count must match decisions")
    if report.max_conflict_severity != _max_conflict_severity(report.decisions):
        raise ValueError("max_conflict_severity must match decisions")
    if report.conflicted_candidate_ratio != _ratio(
        len(tuple(decision for decision in report.decisions if decision.conflict_severity > ZERO_COUNT)),
        len(report.decisions),
    ):
        raise ValueError("conflicted_candidate_ratio must match decisions")
    if report.reason_codes != _report_reason_codes(report.decisions):
        raise ValueError("reason_codes must match decisions")
    if report.reason_code_counts != _reason_code_counts(report.decisions):
        raise ValueError("reason_code_counts must match decisions")
    if report.status != _report_status(report.decisions):
        raise ValueError("status must match decisions")
    if report.decisions != tuple(sorted(report.decisions, key=_decision_sort_key)):
        raise ValueError("decisions must use stable sort")


def _report_status(
    decisions: tuple[StrategyTeamConflictArbitrationDecision, ...],
) -> str:
    if any(
        decision.chosen_paper_recommendation_status == "paper_defer"
        for decision in decisions
    ):
        return "blocked"
    if any(
        decision.chosen_paper_recommendation_status == "paper_watch"
        for decision in decisions
    ):
        return "watch"
    return "clear"


def _report_reason_codes(
    decisions: tuple[StrategyTeamConflictArbitrationDecision, ...],
) -> tuple[str, ...]:
    if not decisions:
        return ("team_conflict_arbitration_digest_clear",)
    decision_codes = tuple(
        reason_code
        for decision in decisions
        for reason_code in decision.reason_codes
    )
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in decision_codes),
        REPORT_REASON_CODES,
    )


def _reason_code_counts(
    decisions: tuple[StrategyTeamConflictArbitrationDecision, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, int] = {}
    for decision in decisions:
        for reason_code in decision.reason_codes:
            if reason_code in counts:
                counts[reason_code] += 1
            else:
                counts[reason_code] = 1
    normalized = []
    for reason_code in DECISION_REASON_CODES:
        if reason_code in counts:
            normalized.append((reason_code, _count(counts[reason_code])))
    return tuple(normalized)


def _decision_status_count(
    decisions: tuple[StrategyTeamConflictArbitrationDecision, ...],
    status: str,
) -> Decimal:
    return _count(
        sum(
            1
            for decision in decisions
            if decision.chosen_paper_recommendation_status == status
        ),
    )


def _max_conflict_severity(
    decisions: tuple[StrategyTeamConflictArbitrationDecision, ...],
) -> Decimal:
    if not decisions:
        return ZERO_COUNT
    return max(decision.conflict_severity for decision in decisions)


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(numerator) / Decimal(denominator)).quantize(RATIO_QUANTUM)


def _age_seconds(generated_at: datetime, earlier_at: datetime) -> Decimal:
    delta = _as_utc("generated_at", generated_at) - _as_utc("earlier_at", earlier_at)
    with localcontext(DECIMAL_CONTEXT):
        age_seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    if age_seconds < ZERO_SECONDS:
        raise ValueError("timestamp must not be in the future")
    return _normalize_seconds("age_seconds", age_seconds)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_seconds(field_name, value)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_seconds(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SECONDS_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    if quantized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(RATIO_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_edge(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < NEGATIVE_ONE_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between -1 and 1")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(RATIO_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[tuple[str, Decimal], ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    normalized: list[tuple[str, Decimal]] = []
    for item in counts:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("reason_code_counts items must be pairs")
        reason_code = item[0]
        _require_member("reason_code_counts", reason_code, DECISION_REASON_CODES)
        normalized.append(
            (
                reason_code,
                _normalize_nonnegative_count("reason_code_counts", item[1]),
            ),
        )
    if tuple(reason_code for reason_code, _count_value in normalized) != tuple(
        reason_code
        for reason_code in DECISION_REASON_CODES
        if reason_code in tuple(code for code, _count_value in normalized)
    ):
        raise ValueError("reason_code_counts must be deterministic")
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _redact_evidence_reference(value: object) -> str:
    _require_canonical_string("evidence_reference", value)
    return REDACTED_EVIDENCE_REFERENCE


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_canonical_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _contains_sensitive_public_text(value):
        raise ValueError(f"{field_name} must not contain sensitive content")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)
    for item in _iter_string_values(value):
        _require_no_sensitive_public_text(label, item)


def _require_no_sensitive_public_text(label: str, value: str) -> None:
    if _contains_sensitive_public_text(value):
        raise ValueError(f"sensitive string value in {label}")


def _contains_sensitive_public_text(value: str) -> bool:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        return True
    tokens = _split_public_text_tokens(normalized)
    return any(
        token in tokens
        for token in (*SENSITIVE_PUBLIC_VALUE_TOKENS, *UNSAFE_PUBLIC_VALUE_TOKENS)
    )


def _split_public_text_tokens(value: str) -> tuple[str, ...]:
    normalized = "".join(char if char.isalnum() else "_" for char in value)
    return tuple(part for part in normalized.split("_") if part)


def _iter_string_values(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _iter_string_values(json_ready_no_floats(value))
    if type(value) is str:
        return (value,)
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_iter_string_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_iter_string_values(item))
        return tuple(values)
    return ()


def _reject_public_numeric_payload(value: object) -> None:
    if isinstance(value, float):
        raise ValueError("payload must not contain float values")
    if type(value) is int:
        raise ValueError(
            "payload public numeric values must use Decimal-derived string values",
        )
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_payload(item)


__all__ = (
    "DEFAULT_STRATEGY_TEAM_CONFLICT_ARBITRATION_CONFIG_VERSION",
    "StrategyTeamConflictArbitrationConfig",
    "StrategyTeamConflictArbitrationDecision",
    "StrategyTeamConflictArbitrationReport",
    "StrategyTeamConflictRecommendation",
    "build_strategy_team_conflict_arbitration_digest",
    "strategy_team_conflict_arbitration_digest_payload",
)
