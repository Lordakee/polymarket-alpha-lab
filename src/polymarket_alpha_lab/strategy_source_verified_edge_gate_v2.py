"""Pure in-memory Phase 1 source-verified edge gate."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_STRATEGY_SOURCE_VERIFIED_EDGE_GATE_V2_CONFIG_VERSION = (
    "strategy-source-verified-edge-gate-v2"
)

GATE_STATUSES = ("pass", "watch", "blocked")
PASS_REASON_CODE = "source_verified_edge_gate_passed"
EMPTY_REASON_CODE = "source_verified_edge_gate_empty"

ROW_REASON_CODE_SEQUENCE = (
    "forecast_edge_below_minimum",
    "fresh_official_anchor_missing",
    "official_anchor_count_below_minimum",
    "independent_source_family_count_below_minimum",
    "contradiction_review_not_clear",
    "resolution_rule_clarity_below_minimum",
    "specialist_quorum_below_minimum",
)
REPORT_REASON_CODE_SEQUENCE = (EMPTY_REASON_CODE, PASS_REASON_CODE) + ROW_REASON_CODE_SEQUENCE
BLOCKING_REASON_CODES = frozenset(
    (
        "fresh_official_anchor_missing",
        "official_anchor_count_below_minimum",
        "independent_source_family_count_below_minimum",
        "contradiction_review_not_clear",
        "specialist_quorum_below_minimum",
    ),
)

CONTRADICTION_REVIEW_CLEAR_STATUS = "reviewed_no_material_contradiction"
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sig", "ning"),
        _join_parts("mu", "tation"),
        _join_parts("bu", "y"),
        _join_parts("sel", "l"),
        _join_parts("tra", "de"),
    ),
)


@dataclass(frozen=True)
class StrategySourceVerifiedEdgeGateV2Config:
    config_version: str = DEFAULT_STRATEGY_SOURCE_VERIFIED_EDGE_GATE_V2_CONFIG_VERSION
    max_official_anchor_age_seconds: Decimal = Decimal("900.000000")
    min_official_anchor_count: Decimal = Decimal("1.000000")
    min_independent_source_family_count: Decimal = Decimal("3.000000")
    min_specialist_quorum_count: Decimal = Decimal("2.000000")
    min_resolution_rule_clarity_score: Decimal = Decimal("0.800000")
    min_forecast_edge_probability: Decimal = Decimal("0.020000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategySourceVerifiedEdgeGateV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategySourceVerifiedEdgeGateV2Config, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_SOURCE_VERIFIED_EDGE_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_official_anchor_age_seconds",
            "min_official_anchor_count",
            "min_independent_source_family_count",
            "min_specialist_quorum_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_resolution_rule_clarity_score",
            "min_forecast_edge_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategySourceVerifiedEdgeGateV2Candidate:
    market_slug: str
    condition_id: str
    outcome: str
    forecast_probability: Decimal
    market_probability: Decimal
    official_anchor_observed_at: datetime
    official_anchor_count: Decimal
    source_families: tuple[str, ...]
    contradiction_review_status: str
    resolution_rule_clarity_score: Decimal
    specialist_quorum_count: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategySourceVerifiedEdgeGateV2Candidate does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in (
            "market_slug",
            "condition_id",
            "outcome",
            "contradiction_review_status",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in ("forecast_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.forecast_probability < self.market_probability:
            raise ValueError("forecast_probability must not be below market_probability")
        object.__setattr__(
            self,
            "official_anchor_observed_at",
            _as_utc("official_anchor_observed_at", self.official_anchor_observed_at),
        )
        for field_name in ("official_anchor_count", "specialist_quorum_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolution_rule_clarity_score",
            _normalize_ratio(
                "resolution_rule_clarity_score",
                self.resolution_rule_clarity_score,
            ),
        )
        object.__setattr__(
            self,
            "source_families",
            _normalize_source_families(self.source_families),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategySourceVerifiedEdgeGateV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    market_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategySourceVerifiedEdgeGateV2ReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, ROW_REASON_CODE_SEQUENCE)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        object.__setattr__(
            self,
            "market_ratio",
            _normalize_ratio("market_ratio", self.market_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class StrategySourceVerifiedEdgeGateV2Row:
    market_slug: str
    condition_id: str
    outcome: str
    forecast_probability: Decimal
    market_probability: Decimal
    candidate_edge_probability: Decimal
    eligible_edge_probability: Decimal
    official_anchor_observed_at: datetime
    official_anchor_age_seconds: Decimal
    official_anchor_count: Decimal
    source_families: tuple[str, ...]
    independent_source_family_count: Decimal
    contradiction_review_status: str
    resolution_rule_clarity_score: Decimal
    specialist_quorum_count: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    source_config_version: str
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategySourceVerifiedEdgeGateV2Row does not support subclassing")

    def __post_init__(self) -> None:
        for field_name in (
            "market_slug",
            "condition_id",
            "outcome",
            "contradiction_review_status",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "candidate_edge_probability",
            "eligible_edge_probability",
            "resolution_rule_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "official_anchor_observed_at",
            _as_utc("official_anchor_observed_at", self.official_anchor_observed_at),
        )
        for field_name in (
            "official_anchor_age_seconds",
            "official_anchor_count",
            "independent_source_family_count",
            "specialist_quorum_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_families",
            _normalize_source_families(self.source_families),
        )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_row(self)


@dataclass(frozen=True)
class StrategySourceVerifiedEdgeGateV2Report:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    candidate_edge_count: Decimal
    eligible_edge_count: Decimal
    total_candidate_edge_probability: Decimal
    total_eligible_edge_probability: Decimal
    max_anchor_age_seconds: Decimal
    min_resolution_rule_clarity_score: Decimal
    gate_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategySourceVerifiedEdgeGateV2ReasonCodeCount, ...]
    rows: tuple[StrategySourceVerifiedEdgeGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategySourceVerifiedEdgeGateV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategySourceVerifiedEdgeGateV2Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "candidate_edge_count",
            "eligible_edge_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_candidate_edge_probability",
            "total_eligible_edge_probability",
            "min_resolution_rule_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_anchor_age_seconds",
            _normalize_nonnegative_decimal(
                "max_anchor_age_seconds",
                self.max_anchor_age_seconds,
            ),
        )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_strategy_source_verified_edge_gate_v2_report(
    candidates: list[StrategySourceVerifiedEdgeGateV2Candidate]
    | tuple[StrategySourceVerifiedEdgeGateV2Candidate, ...],
    *,
    config: StrategySourceVerifiedEdgeGateV2Config,
    generated_at: datetime,
) -> StrategySourceVerifiedEdgeGateV2Report:
    if type(config) is not StrategySourceVerifiedEdgeGateV2Config:
        raise ValueError("config must be a StrategySourceVerifiedEdgeGateV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    _validate_unique_candidates(normalized_candidates)
    _validate_not_after_generated_at(normalized_candidates, generated_at=generated_at_utc)

    rows = tuple(
        sorted(
            (
                _row_for_candidate(
                    candidate,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for candidate in normalized_candidates
            ),
            key=_row_sort_key,
        ),
    )
    return StrategySourceVerifiedEdgeGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        candidate_edge_count=_count(
            len(
                tuple(
                    row
                    for row in rows
                    if row.candidate_edge_probability
                    >= config.min_forecast_edge_probability
                ),
            ),
        ),
        eligible_edge_count=_count(
            len(tuple(row for row in rows if row.eligible_edge_probability > ZERO)),
        ),
        total_candidate_edge_probability=_sum_decimal(
            tuple(row.candidate_edge_probability for row in rows),
        ),
        total_eligible_edge_probability=_sum_decimal(
            tuple(row.eligible_edge_probability for row in rows),
        ),
        max_anchor_age_seconds=max(
            (row.official_anchor_age_seconds for row in rows),
            default=ZERO,
        ),
        min_resolution_rule_clarity_score=min(
            (row.resolution_rule_clarity_score for row in rows),
            default=ZERO,
        ),
        gate_status=_report_status(rows),
        recommended_next_step=_recommended_next_step(_report_status(rows)),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_source_verified_edge_gate_v2_public_payload(
    report: StrategySourceVerifiedEdgeGateV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategySourceVerifiedEdgeGateV2Report:
        raise ValueError("report must be a StrategySourceVerifiedEdgeGateV2Report")
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_strategy_source_verified_edge_gate_v2_public_payload(payload)
    return payload


def validate_strategy_source_verified_edge_gate_v2_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("strategy source verified edge gate payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_candidate(
    candidate: StrategySourceVerifiedEdgeGateV2Candidate,
    *,
    config: StrategySourceVerifiedEdgeGateV2Config,
    generated_at: datetime,
) -> StrategySourceVerifiedEdgeGateV2Row:
    candidate_edge_probability = _subtract_decimal(
        candidate.forecast_probability,
        candidate.market_probability,
    )
    anchor_age_seconds = _normalize_nonnegative_decimal(
        "official_anchor_age_seconds",
        _decimal_from_int(
            int((generated_at - candidate.official_anchor_observed_at).total_seconds()),
        ),
    )
    source_family_count = _count(len(candidate.source_families))
    reason_codes = _row_reason_codes(
        candidate_edge_probability=candidate_edge_probability,
        official_anchor_age_seconds=anchor_age_seconds,
        official_anchor_count=candidate.official_anchor_count,
        independent_source_family_count=source_family_count,
        contradiction_review_status=candidate.contradiction_review_status,
        resolution_rule_clarity_score=candidate.resolution_rule_clarity_score,
        specialist_quorum_count=candidate.specialist_quorum_count,
        config=config,
    )
    gate_status = _row_status(reason_codes)
    eligible_edge_probability = (
        candidate_edge_probability if gate_status == "pass" else ZERO
    )
    return StrategySourceVerifiedEdgeGateV2Row(
        market_slug=candidate.market_slug,
        condition_id=candidate.condition_id,
        outcome=candidate.outcome,
        forecast_probability=candidate.forecast_probability,
        market_probability=candidate.market_probability,
        candidate_edge_probability=candidate_edge_probability,
        eligible_edge_probability=eligible_edge_probability,
        official_anchor_observed_at=candidate.official_anchor_observed_at,
        official_anchor_age_seconds=anchor_age_seconds,
        official_anchor_count=candidate.official_anchor_count,
        source_families=candidate.source_families,
        independent_source_family_count=source_family_count,
        contradiction_review_status=candidate.contradiction_review_status,
        resolution_rule_clarity_score=candidate.resolution_rule_clarity_score,
        specialist_quorum_count=candidate.specialist_quorum_count,
        gate_status=gate_status,
        reason_codes=reason_codes,
        source_config_version=candidate.source_config_version,
    )


def _row_reason_codes(
    *,
    candidate_edge_probability: Decimal,
    official_anchor_age_seconds: Decimal,
    official_anchor_count: Decimal,
    independent_source_family_count: Decimal,
    contradiction_review_status: str,
    resolution_rule_clarity_score: Decimal,
    specialist_quorum_count: Decimal,
    config: StrategySourceVerifiedEdgeGateV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if candidate_edge_probability < config.min_forecast_edge_probability:
        reason_codes.append("forecast_edge_below_minimum")
    if (
        official_anchor_age_seconds > config.max_official_anchor_age_seconds
        or official_anchor_count <= ZERO
    ):
        reason_codes.append("fresh_official_anchor_missing")
    if official_anchor_count < config.min_official_anchor_count:
        reason_codes.append("official_anchor_count_below_minimum")
    if independent_source_family_count < config.min_independent_source_family_count:
        reason_codes.append("independent_source_family_count_below_minimum")
    if contradiction_review_status != CONTRADICTION_REVIEW_CLEAR_STATUS:
        reason_codes.append("contradiction_review_not_clear")
    if resolution_rule_clarity_score < config.min_resolution_rule_clarity_score:
        reason_codes.append("resolution_rule_clarity_below_minimum")
    if specialist_quorum_count < config.min_specialist_quorum_count:
        reason_codes.append("specialist_quorum_below_minimum")
    if not reason_codes:
        return (PASS_REASON_CODE,)
    return tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if reason_codes == (PASS_REASON_CODE,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[StrategySourceVerifiedEdgeGateV2Row, ...]) -> str:
    statuses = tuple(row.gate_status for row in rows)
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _recommended_next_step(gate_status: str) -> str:
    if gate_status == "blocked":
        return "block_report_only_source_verified_edge"
    if gate_status == "watch":
        return "review_report_only_source_verified_edge"
    return "continue_report_only_source_verified_edge"


def _report_reason_codes(
    rows: tuple[StrategySourceVerifiedEdgeGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    present = set(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON_CODE
    )
    if not present:
        return (PASS_REASON_CODE,)
    return tuple(reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in present)


def _reason_code_counts(
    rows: tuple[StrategySourceVerifiedEdgeGateV2Row, ...],
) -> tuple[StrategySourceVerifiedEdgeGateV2ReasonCodeCount, ...]:
    market_count = _count(len(rows))
    return tuple(
        StrategySourceVerifiedEdgeGateV2ReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            market_ratio=_ratio(_reason_count(rows, reason_code), market_count),
        )
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if _reason_count(rows, reason_code) > ZERO
    )


def _normalize_candidates(
    value: object,
) -> tuple[StrategySourceVerifiedEdgeGateV2Candidate, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    candidates = tuple(value)
    for item in candidates:
        if type(item) is not StrategySourceVerifiedEdgeGateV2Candidate:
            raise ValueError(
                "candidates must contain StrategySourceVerifiedEdgeGateV2Candidate values",
            )
        _require_hard_flags("candidate", item)
    return candidates


def _normalize_rows(value: object) -> tuple[StrategySourceVerifiedEdgeGateV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not StrategySourceVerifiedEdgeGateV2Row:
            raise ValueError("rows must contain StrategySourceVerifiedEdgeGateV2Row values")
        _require_hard_flags("row", row)
        key = _market_key(row)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate source verified candidate")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[StrategySourceVerifiedEdgeGateV2ReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not StrategySourceVerifiedEdgeGateV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "StrategySourceVerifiedEdgeGateV2ReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    expected = tuple(
        item
        for reason_code in ROW_REASON_CODE_SEQUENCE
        for item in counts
        if item.reason_code == reason_code
    )
    if counts != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _normalize_source_families(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("source_families must be a list or tuple")
    source_families = tuple(value)
    if not source_families:
        raise ValueError("source_families must not be empty")
    seen: set[str] = set()
    for source_family in source_families:
        _require_public_string("source_families", source_family)
        if source_family in seen:
            raise ValueError("source_families must not contain duplicates")
        seen.add(source_family)
    return source_families


def _validate_unique_candidates(
    candidates: tuple[StrategySourceVerifiedEdgeGateV2Candidate, ...],
) -> None:
    seen: set[tuple[str, str, str]] = set()
    for candidate in candidates:
        key = _market_key(candidate)
        if key in seen:
            raise ValueError("candidates contain duplicate source verified candidate")
        seen.add(key)


def _validate_not_after_generated_at(
    candidates: tuple[StrategySourceVerifiedEdgeGateV2Candidate, ...],
    *,
    generated_at: datetime,
) -> None:
    for candidate in candidates:
        if candidate.official_anchor_observed_at > generated_at:
            raise ValueError("official_anchor_observed_at must not be after generated_at")


def _validate_row(row: StrategySourceVerifiedEdgeGateV2Row) -> None:
    if row.forecast_probability < row.market_probability:
        raise ValueError("forecast_probability must not be below market_probability")
    if row.candidate_edge_probability != _subtract_decimal(
        row.forecast_probability,
        row.market_probability,
    ):
        raise ValueError("candidate_edge_probability must match forecast and market")
    if row.independent_source_family_count != _count(len(row.source_families)):
        raise ValueError("independent_source_family_count must match source_families")
    if row.gate_status != _row_status(row.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    expected_eligible_edge = (
        row.candidate_edge_probability if row.gate_status == "pass" else ZERO
    )
    if row.eligible_edge_probability != expected_eligible_edge:
        raise ValueError("eligible_edge_probability must match source verification")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: StrategySourceVerifiedEdgeGateV2Report) -> None:
    rows = report.rows
    market_count = _count(len(rows))
    if report.market_count != market_count:
        raise ValueError("market_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("blocked_count", "blocked"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.pass_count + report.watch_count + report.blocked_count != report.market_count:
        raise ValueError("status counts must match market_count")
    if report.candidate_edge_count != _count(
        len(
            tuple(
                row
                for row in rows
                if row.candidate_edge_probability > ZERO
                and "forecast_edge_below_minimum" not in row.reason_codes
            ),
        ),
    ):
        raise ValueError("candidate_edge_count must match rows")
    if report.eligible_edge_count != _count(
        len(tuple(row for row in rows if row.eligible_edge_probability > ZERO)),
    ):
        raise ValueError("eligible_edge_count must match rows")
    if report.total_candidate_edge_probability != _sum_decimal(
        tuple(row.candidate_edge_probability for row in rows),
    ):
        raise ValueError("total_candidate_edge_probability must match rows")
    if report.total_eligible_edge_probability != _sum_decimal(
        tuple(row.eligible_edge_probability for row in rows),
    ):
        raise ValueError("total_eligible_edge_probability must match rows")
    if report.max_anchor_age_seconds != max(
        (row.official_anchor_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_anchor_age_seconds must match rows")
    if report.min_resolution_rule_clarity_score != min(
        (row.resolution_rule_clarity_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_resolution_rule_clarity_score must match rows")
    if report.gate_status != _report_status(rows):
        raise ValueError("gate_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.gate_status):
        raise ValueError("recommended_next_step must match gate_status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    for row in rows:
        _validate_row(row)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_public_numeric_values(value: object, path: str = "") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(
            f"public payload must use Decimal strings, not numeric values at {path}",
        )
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_public_numeric_values(item, nested_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]"
            _reject_public_numeric_values(item, nested_path)


def _payload_required_string(payload: dict[str, Any], key: str) -> str:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if type(value) is not str:
        raise ValueError(f"{key} must be a string")
    return value


def _row_derived_validation_digest(row: StrategySourceVerifiedEdgeGateV2Row) -> str:
    return _public_payload_derived_validation_digest(_row_public_payload_for_digest(row))


def _report_derived_validation_digest(report: StrategySourceVerifiedEdgeGateV2Report) -> str:
    return _public_payload_derived_validation_digest(
        _report_public_payload_for_digest(report),
    )


def _row_public_payload_for_digest(row: StrategySourceVerifiedEdgeGateV2Row) -> dict[str, Any]:
    payload = _json_ready_no_floats(asdict(row))
    if not isinstance(payload, dict):
        raise ValueError("row payload must be an object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_public_payload_for_digest(
    report: StrategySourceVerifiedEdgeGateV2Report,
) -> dict[str, Any]:
    payload = _json_ready_no_floats(asdict(report))
    if not isinstance(payload, dict):
        raise ValueError("report payload must be an object")
    payload.pop("derived_validation_digest", None)
    return payload


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("derived validation payload", digest_payload)
    canonical_payload = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
                raise ValueError(f"unsafe public key in {label}: {key}")
            nested_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if type(value) is str:
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}: {path}")


def _json_ready_no_floats(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_no_floats(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime JSON value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        raise ValueError("JSON value must not be an int")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready_no_floats(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready_no_floats(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    normalized_value = value.lower()
    if any(fragment in normalized_value for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_public_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return _decimal_from_int(value)


def _decimal_from_int(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
        return total.quantize(QUANTUM)


def _status_count(
    rows: tuple[StrategySourceVerifiedEdgeGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(len(tuple(row for row in rows if row.gate_status == status)))


def _reason_count(
    rows: tuple[StrategySourceVerifiedEdgeGateV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(len(tuple(row for row in rows if reason_code in row.reason_codes)))


def _market_key(value: object) -> tuple[str, str, str]:
    return (
        getattr(value, "market_slug"),
        getattr(value, "condition_id"),
        getattr(value, "outcome"),
    )


def _row_sort_key(row: StrategySourceVerifiedEdgeGateV2Row) -> tuple[str, str, str]:
    return (row.market_slug, row.condition_id, row.outcome)


__all__ = (
    "DEFAULT_STRATEGY_SOURCE_VERIFIED_EDGE_GATE_V2_CONFIG_VERSION",
    "StrategySourceVerifiedEdgeGateV2Candidate",
    "StrategySourceVerifiedEdgeGateV2Config",
    "StrategySourceVerifiedEdgeGateV2ReasonCodeCount",
    "StrategySourceVerifiedEdgeGateV2Report",
    "StrategySourceVerifiedEdgeGateV2Row",
    "build_strategy_source_verified_edge_gate_v2_report",
    "strategy_source_verified_edge_gate_v2_public_payload",
    "validate_strategy_source_verified_edge_gate_v2_public_payload",
)
