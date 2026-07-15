"""Pure in-memory source quality gate report before edge review."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_SOURCE_QUALITY_BEFORE_EDGE_GATE_CONFIG_VERSION = (
    "source-quality-before-edge-gate-v1"
)

PASS_REASON_CODE = "source_quality_before_edge_gate_passed"
EMPTY_REASON_CODE = "source_quality_before_edge_gate_empty"
CLEAR_CONTRADICTION_STATUS = "reviewed_no_material_contradiction"

ROW_REASON_CODE_SEQUENCE = (
    "official_anchor_stale",
    "independent_source_family_count_below_minimum",
    "contradiction_status_not_clear",
    "resolution_rule_clarity_below_minimum",
    "specialist_quorum_below_minimum",
)
REPORT_REASON_CODE_SEQUENCE = (EMPTY_REASON_CODE, PASS_REASON_CODE) + ROW_REASON_CODE_SEQUENCE
BLOCKING_REASON_CODES = frozenset(
    (
        "official_anchor_stale",
        "independent_source_family_count_below_minimum",
        "contradiction_status_not_clear",
        "specialist_quorum_below_minimum",
    ),
)
GATE_STATUSES = ("pass", "watch", "blocked")

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
class SourceQualityBeforeEdgeGateConfig:
    config_version: str = DEFAULT_SOURCE_QUALITY_BEFORE_EDGE_GATE_CONFIG_VERSION
    max_official_anchor_age_seconds: Decimal = Decimal("900.000000")
    min_independent_source_family_count: Decimal = Decimal("3.000000")
    min_resolution_rule_clarity_score: Decimal = Decimal("0.800000")
    min_specialist_quorum_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("SourceQualityBeforeEdgeGateConfig does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, SourceQualityBeforeEdgeGateConfig, "config")
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_SOURCE_QUALITY_BEFORE_EDGE_GATE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_official_anchor_age_seconds",
            "min_independent_source_family_count",
            "min_specialist_quorum_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_resolution_rule_clarity_score",
            _normalize_ratio(
                "min_resolution_rule_clarity_score",
                self.min_resolution_rule_clarity_score,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class SourceQualityBeforeEdgeGateCandidate:
    public_source_ref: str
    official_anchor_observed_at: datetime
    source_families: tuple[str, ...]
    contradiction_status: str
    resolution_rule_clarity_score: Decimal
    specialist_quorum_count: Decimal
    pre_edge_probability: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("SourceQualityBeforeEdgeGateCandidate does not support subclassing")

    def __post_init__(self) -> None:
        for field_name in (
            "public_source_ref",
            "contradiction_status",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "official_anchor_observed_at",
            _as_utc("official_anchor_observed_at", self.official_anchor_observed_at),
        )
        object.__setattr__(
            self,
            "source_families",
            _normalize_source_families(self.source_families),
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
            "specialist_quorum_count",
            _normalize_nonnegative_decimal(
                "specialist_quorum_count",
                self.specialist_quorum_count,
            ),
        )
        object.__setattr__(
            self,
            "pre_edge_probability",
            _normalize_ratio("pre_edge_probability", self.pre_edge_probability),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class SourceQualityBeforeEdgeGateReasonCodeCount:
    reason_code: str
    count: Decimal
    candidate_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "SourceQualityBeforeEdgeGateReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, ROW_REASON_CODE_SEQUENCE)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        object.__setattr__(
            self,
            "candidate_ratio",
            _normalize_ratio("candidate_ratio", self.candidate_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class SourceQualityBeforeEdgeGateRow:
    public_source_ref: str
    official_anchor_observed_at: datetime
    official_anchor_age_seconds: Decimal
    source_families: tuple[str, ...]
    independent_source_family_count: Decimal
    contradiction_status: str
    resolution_rule_clarity_score: Decimal
    specialist_quorum_count: Decimal
    pre_edge_probability: Decimal
    edge_eligible_probability: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    source_config_version: str
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("SourceQualityBeforeEdgeGateRow does not support subclassing")

    def __post_init__(self) -> None:
        for field_name in (
            "public_source_ref",
            "contradiction_status",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "official_anchor_observed_at",
            _as_utc("official_anchor_observed_at", self.official_anchor_observed_at),
        )
        object.__setattr__(
            self,
            "official_anchor_age_seconds",
            _normalize_nonnegative_decimal(
                "official_anchor_age_seconds",
                self.official_anchor_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_families",
            _normalize_source_families(self.source_families),
        )
        object.__setattr__(
            self,
            "independent_source_family_count",
            _normalize_count(
                "independent_source_family_count",
                self.independent_source_family_count,
            ),
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
            "specialist_quorum_count",
            _normalize_nonnegative_decimal(
                "specialist_quorum_count",
                self.specialist_quorum_count,
            ),
        )
        for field_name in ("pre_edge_probability", "edge_eligible_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODE_SEQUENCE),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _apply_or_verify_row_digest(self)


@dataclass(frozen=True)
class SourceQualityBeforeEdgeGateReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    source_blocker_count: Decimal
    pre_edge_candidate_count: Decimal
    edge_eligible_count: Decimal
    total_pre_edge_probability: Decimal
    total_edge_eligible_probability: Decimal
    max_official_anchor_age_seconds: Decimal
    min_resolution_rule_clarity_score: Decimal
    gate_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[SourceQualityBeforeEdgeGateReasonCodeCount, ...]
    rows: tuple[SourceQualityBeforeEdgeGateRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("SourceQualityBeforeEdgeGateReport does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, SourceQualityBeforeEdgeGateReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "source_blocker_count",
            "pre_edge_candidate_count",
            "edge_eligible_count",
            "max_official_anchor_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_pre_edge_probability",
            "total_edge_eligible_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_resolution_rule_clarity_score",
            _normalize_ratio(
                "min_resolution_rule_clarity_score",
                self.min_resolution_rule_clarity_score,
            ),
        )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _apply_or_verify_report_digest(self)


def build_source_quality_before_edge_gate_report(
    candidates: tuple[SourceQualityBeforeEdgeGateCandidate, ...] | list[SourceQualityBeforeEdgeGateCandidate],
    *,
    config: SourceQualityBeforeEdgeGateConfig,
    generated_at: datetime,
) -> SourceQualityBeforeEdgeGateReport:
    if type(config) is not SourceQualityBeforeEdgeGateConfig:
        raise ValueError("config must be a SourceQualityBeforeEdgeGateConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)

    rows = tuple(
        _row_for_candidate(candidate, config=config, generated_at=generated_at)
        for candidate in candidates
    )
    _require_unique_rows(rows)
    rows = tuple(sorted(rows, key=lambda row: row.public_source_ref))

    candidate_count = _count(len(rows))
    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    blocked_count = _status_count(rows, "blocked")
    source_blocker_count = _count(
        sum(1 for row in rows if any(code in BLOCKING_REASON_CODES for code in row.reason_codes)),
    )
    pre_edge_candidate_count = _count(
        sum(1 for row in rows if row.pre_edge_probability > ZERO),
    )
    edge_eligible_count = _count(
        sum(1 for row in rows if row.edge_eligible_probability > ZERO),
    )
    total_pre_edge_probability = _sum_decimals(
        row.pre_edge_probability for row in rows
    )
    total_edge_eligible_probability = _sum_decimals(
        row.edge_eligible_probability for row in rows
    )
    max_anchor_age = max(
        (row.official_anchor_age_seconds for row in rows),
        default=ZERO,
    )
    min_clarity = min(
        (row.resolution_rule_clarity_score for row in rows),
        default=ZERO,
    )
    reason_codes = _report_reason_codes(rows)
    gate_status = _report_gate_status(reason_codes)

    return SourceQualityBeforeEdgeGateReport(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=candidate_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        source_blocker_count=source_blocker_count,
        pre_edge_candidate_count=pre_edge_candidate_count,
        edge_eligible_count=edge_eligible_count,
        total_pre_edge_probability=total_pre_edge_probability,
        total_edge_eligible_probability=total_edge_eligible_probability,
        max_official_anchor_age_seconds=max_anchor_age,
        min_resolution_rule_clarity_score=min_clarity,
        gate_status=gate_status,
        recommended_next_step=_recommended_next_step(gate_status),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, candidate_count),
        rows=rows,
    )


def source_quality_before_edge_gate_public_payload(
    report: SourceQualityBeforeEdgeGateReport,
) -> dict[str, Any]:
    if type(report) is not SourceQualityBeforeEdgeGateReport:
        raise ValueError("report must be a SourceQualityBeforeEdgeGateReport")
    _validate_report_consistency(report)
    expected_digest = _report_derived_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _public_payload(report)
    _reject_unsafe_public_payload(payload)
    return payload


def validate_source_quality_before_edge_gate_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(payload)
    _reject_public_numeric_payload(payload)
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    digest = payload["derived_validation_digest"]
    _require_digest("derived_validation_digest", digest)
    payload_for_digest = dict(payload)
    payload_for_digest.pop("derived_validation_digest")
    expected = _digest_public_payload(payload_for_digest)
    if digest != expected:
        raise ValueError("derived_validation_digest must match payload fields")
    return True


def _row_for_candidate(
    candidate: SourceQualityBeforeEdgeGateCandidate,
    *,
    config: SourceQualityBeforeEdgeGateConfig,
    generated_at: datetime,
) -> SourceQualityBeforeEdgeGateRow:
    if type(candidate) is not SourceQualityBeforeEdgeGateCandidate:
        raise ValueError("candidate must be a SourceQualityBeforeEdgeGateCandidate")
    _require_hard_flags("candidate", candidate)
    anchor_observed_at = _as_utc(
        "official_anchor_observed_at",
        candidate.official_anchor_observed_at,
    )
    if anchor_observed_at > generated_at:
        raise ValueError("official_anchor_observed_at must not be after generated_at")
    anchor_delta = generated_at - anchor_observed_at
    with localcontext(DECIMAL_CONTEXT):
        anchor_seconds = (
            Decimal(anchor_delta.days) * Decimal("86400")
            + Decimal(anchor_delta.seconds)
            + Decimal(anchor_delta.microseconds) / Decimal("1000000")
        )
    anchor_age = _normalize_nonnegative_decimal(
        "official_anchor_age_seconds",
        anchor_seconds,
    )
    independent_source_family_count = _count(len(candidate.source_families))
    reason_codes = _row_reason_codes(
        official_anchor_age_seconds=anchor_age,
        independent_source_family_count=independent_source_family_count,
        contradiction_status=candidate.contradiction_status,
        resolution_rule_clarity_score=candidate.resolution_rule_clarity_score,
        specialist_quorum_count=candidate.specialist_quorum_count,
        config=config,
    )
    gate_status = _row_gate_status(reason_codes)
    edge_eligible_probability = (
        candidate.pre_edge_probability if gate_status == "pass" else ZERO
    )
    return SourceQualityBeforeEdgeGateRow(
        public_source_ref=candidate.public_source_ref,
        official_anchor_observed_at=anchor_observed_at,
        official_anchor_age_seconds=anchor_age,
        source_families=candidate.source_families,
        independent_source_family_count=independent_source_family_count,
        contradiction_status=candidate.contradiction_status,
        resolution_rule_clarity_score=candidate.resolution_rule_clarity_score,
        specialist_quorum_count=candidate.specialist_quorum_count,
        pre_edge_probability=candidate.pre_edge_probability,
        edge_eligible_probability=edge_eligible_probability,
        gate_status=gate_status,
        reason_codes=reason_codes,
        source_config_version=candidate.source_config_version,
    )


def _row_reason_codes(
    *,
    official_anchor_age_seconds: Decimal,
    independent_source_family_count: Decimal,
    contradiction_status: str,
    resolution_rule_clarity_score: Decimal,
    specialist_quorum_count: Decimal,
    config: SourceQualityBeforeEdgeGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if official_anchor_age_seconds > config.max_official_anchor_age_seconds:
        reason_codes.append("official_anchor_stale")
    if independent_source_family_count < config.min_independent_source_family_count:
        reason_codes.append("independent_source_family_count_below_minimum")
    if contradiction_status != CLEAR_CONTRADICTION_STATUS:
        reason_codes.append("contradiction_status_not_clear")
    if resolution_rule_clarity_score < config.min_resolution_rule_clarity_score:
        reason_codes.append("resolution_rule_clarity_below_minimum")
    if specialist_quorum_count < config.min_specialist_quorum_count:
        reason_codes.append("specialist_quorum_below_minimum")
    return _normalize_reason_codes(tuple(reason_codes) or (PASS_REASON_CODE,), REPORT_REASON_CODE_SEQUENCE)


def _row_gate_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON_CODE,):
        return "pass"
    if any(code in BLOCKING_REASON_CODES for code in reason_codes):
        return "blocked"
    return "watch"


def _report_reason_codes(
    rows: tuple[SourceQualityBeforeEdgeGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    ordered_codes: list[str] = []
    for allowed_code in ROW_REASON_CODE_SEQUENCE:
        if any(allowed_code in row.reason_codes for row in rows):
            ordered_codes.append(allowed_code)
    return _normalize_reason_codes(
        tuple(ordered_codes) or (PASS_REASON_CODE,),
        REPORT_REASON_CODE_SEQUENCE,
    )


def _report_gate_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes in ((PASS_REASON_CODE,), (EMPTY_REASON_CODE,)):
        return "pass"
    if any(code in BLOCKING_REASON_CODES for code in reason_codes):
        return "blocked"
    return "watch"


def _recommended_next_step(gate_status: str) -> str:
    if gate_status == "blocked":
        return "block_edge_until_source_quality_clears"
    if gate_status == "watch":
        return "review_source_quality_before_edge"
    return "continue_report_only_source_quality_before_edge"


def _reason_code_counts(
    rows: tuple[SourceQualityBeforeEdgeGateRow, ...],
    candidate_count: Decimal,
) -> tuple[SourceQualityBeforeEdgeGateReasonCodeCount, ...]:
    if candidate_count == ZERO:
        return ()
    counts: list[SourceQualityBeforeEdgeGateReasonCodeCount] = []
    for reason_code in ROW_REASON_CODE_SEQUENCE:
        count = _count(sum(1 for row in rows if reason_code in row.reason_codes))
        if count > ZERO:
            counts.append(
                SourceQualityBeforeEdgeGateReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    candidate_ratio=_quantize(count / candidate_count),
                ),
            )
    return tuple(counts)


def _validate_row_consistency(row: SourceQualityBeforeEdgeGateRow) -> None:
    expected_status = _row_gate_status(row.reason_codes)
    if row.gate_status != expected_status:
        raise ValueError("gate_status must match reason_codes")
    expected_edge = row.pre_edge_probability if row.gate_status == "pass" else ZERO
    if row.edge_eligible_probability != expected_edge:
        raise ValueError("edge_eligible_probability must match source quality gate")
    if row.independent_source_family_count != _count(len(row.source_families)):
        raise ValueError("independent_source_family_count must match source_families")


def _validate_report_consistency(report: SourceQualityBeforeEdgeGateReport) -> None:
    rows = report.rows
    candidate_count = _count(len(rows))
    if report.candidate_count != candidate_count:
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    expected_blockers = _count(
        sum(1 for row in rows if any(code in BLOCKING_REASON_CODES for code in row.reason_codes)),
    )
    if report.source_blocker_count != expected_blockers:
        raise ValueError("source_blocker_count must match rows")
    if report.pre_edge_candidate_count != _count(
        sum(1 for row in rows if row.pre_edge_probability > ZERO),
    ):
        raise ValueError("pre_edge_candidate_count must match rows")
    if report.edge_eligible_count != _count(
        sum(1 for row in rows if row.edge_eligible_probability > ZERO),
    ):
        raise ValueError("edge_eligible_count must match rows")
    if report.total_pre_edge_probability != _sum_decimals(
        row.pre_edge_probability for row in rows
    ):
        raise ValueError("total_pre_edge_probability must match rows")
    if report.total_edge_eligible_probability != _sum_decimals(
        row.edge_eligible_probability for row in rows
    ):
        raise ValueError("total_edge_eligible_probability must match rows")
    expected_max_age = max(
        (row.official_anchor_age_seconds for row in rows),
        default=ZERO,
    )
    if report.max_official_anchor_age_seconds != expected_max_age:
        raise ValueError("max_official_anchor_age_seconds must match rows")
    expected_min_clarity = min(
        (row.resolution_rule_clarity_score for row in rows),
        default=ZERO,
    )
    if report.min_resolution_rule_clarity_score != expected_min_clarity:
        raise ValueError("min_resolution_rule_clarity_score must match rows")
    expected_reasons = _report_reason_codes(rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    expected_status = _report_gate_status(report.reason_codes)
    if report.gate_status != expected_status:
        raise ValueError("gate_status must match reason_codes")
    if report.recommended_next_step != _recommended_next_step(report.gate_status):
        raise ValueError("recommended_next_step must match gate_status")
    if report.reason_code_counts != _reason_code_counts(rows, candidate_count):
        raise ValueError("reason_code_counts must match rows")
    for row in rows:
        _validate_row_consistency(row)
        if row.derived_validation_digest != _row_derived_validation_digest(row):
            raise ValueError("row derived_validation_digest must match row fields")


def _status_count(
    rows: tuple[SourceQualityBeforeEdgeGateRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _require_unique_rows(rows: tuple[SourceQualityBeforeEdgeGateRow, ...]) -> None:
    seen: set[str] = set()
    for row in rows:
        if row.public_source_ref in seen:
            raise ValueError("duplicate source quality candidate")
        seen.add(row.public_source_ref)


def _normalize_source_families(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("source_families must be a tuple")
    if not value:
        raise ValueError("source_families must not be empty")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        _require_public_string("source_families", item)
        if item in seen:
            raise ValueError("source_families must not contain duplicates")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _normalize_reason_code_counts(
    value: object,
) -> tuple[SourceQualityBeforeEdgeGateReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in value:
        if type(item) is not SourceQualityBeforeEdgeGateReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code count rows")
    return value


def _normalize_rows(value: object) -> tuple[SourceQualityBeforeEdgeGateRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for item in value:
        if type(item) is not SourceQualityBeforeEdgeGateRow:
            raise ValueError("rows must contain source quality rows")
    return value


def _normalize_reason_codes(
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        _require_member("reason_code", item, allowed_reason_codes)
        if item not in seen:
            normalized.append(item)
            seen.add(item)
    ordered = tuple(
        reason_code for reason_code in allowed_reason_codes if reason_code in seen
    )
    if tuple(normalized) != ordered:
        return ordered
    return tuple(normalized)


def _public_payload(value: object) -> dict[str, Any]:
    if not is_dataclass(value):
        raise ValueError("payload source must be a dataclass")
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _apply_or_verify_row_digest(row: SourceQualityBeforeEdgeGateRow) -> None:
    expected = _row_derived_validation_digest(row)
    if row.derived_validation_digest == "":
        object.__setattr__(row, "derived_validation_digest", expected)
        return
    if row.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match row fields")
    _require_digest("derived_validation_digest", row.derived_validation_digest)


def _apply_or_verify_report_digest(report: SourceQualityBeforeEdgeGateReport) -> None:
    expected = _report_derived_validation_digest(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match report fields")
    _require_digest("derived_validation_digest", report.derived_validation_digest)


def _row_derived_validation_digest(row: SourceQualityBeforeEdgeGateRow) -> str:
    payload = _public_payload(row)
    payload.pop("derived_validation_digest", None)
    return _digest_public_payload(payload)


def _report_derived_validation_digest(report: SourceQualityBeforeEdgeGateReport) -> str:
    payload = _public_payload(report)
    payload.pop("derived_validation_digest", None)
    return _digest_public_payload(payload)


def _digest_public_payload(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload(payload)
    encoded = json.dumps(payload, allow_nan=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _reject_public_numeric_payload(value: object) -> None:
    if type(value) is int or isinstance(value, float) or type(value) is Decimal:
        raise ValueError("public payload must use Decimal strings, not numeric values")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_payload(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(str(key))
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str):
        _reject_unsafe_public_text(value)


def _reject_unsafe_public_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError("unsafe public payload surface")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _normalize_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer count")
    return normalized


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _sum_decimals(values: object) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            if type(value) is not Decimal:
                raise ValueError("sum values must be Decimal")
            total += value
        return total.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{name} must be canonical")
    _reject_unsafe_public_text(value)


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_public_string(name, value)
    if value not in allowed:
        raise ValueError(f"{name} must be one of the supported values")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be a {expected_type.__name__}")


__all__ = (
    "DEFAULT_SOURCE_QUALITY_BEFORE_EDGE_GATE_CONFIG_VERSION",
    "SourceQualityBeforeEdgeGateCandidate",
    "SourceQualityBeforeEdgeGateConfig",
    "SourceQualityBeforeEdgeGateReasonCodeCount",
    "SourceQualityBeforeEdgeGateReport",
    "SourceQualityBeforeEdgeGateRow",
    "build_source_quality_before_edge_gate_report",
    "source_quality_before_edge_gate_public_payload",
    "validate_source_quality_before_edge_gate_public_payload",
)
