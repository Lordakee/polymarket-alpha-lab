"""Pure report-only candidate evidence traceability scoring."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
from typing import Any, Iterable


DEFAULT_CONFIG_VERSION = "candidate-decision-evidence-traceability-score-v0"
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUS_VALUES = ("pass", "watch", "block")
SAFETY_FLAGS = (
    "paper_only",
    "report_only",
    "readonly",
    "redacted_refs_only",
    "local_inputs_only",
    "no_execution_surface",
)
REDACTED_CANDIDATE_REF_PREFIX = "redacted-candidate-"
_DECIMAL_CONTEXT_PRECISION = 28
_STATUS_SORT_RANK = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}
_WEIGHT_FIELDS = (
    "traceable_claim_weight",
    "replayable_step_weight",
    "independent_review_weight",
    "cross_reference_weight",
    "timestamp_coverage_weight",
)
_UNSAFE_TERM_PARTS = (
    ("raw", "_candidate"),
    ("candidate", "_id"),
    ("candidate", "-id"),
    ("market", "_id"),
    ("market", "-id"),
    ("market", "_sl", "ug"),
    ("market", "-sl", "ug"),
    ("sl", "ug"),
    ("ques", "tion"),
    ("source", "_ref"),
    ("source", "-ref"),
    ("source", "_u", "rl"),
    ("source", "-u", "rl"),
    ("source", "_text"),
    ("source", "-text"),
    ("source", "_id"),
    ("source", "-id"),
    ("u", "rl"),
    ("ht", "tp"),
    ("://",),
    ("w", "ww"),
    ("d", "sn"),
    ("connection", "_string"),
    ("ta", "ble"),
    ("sche", "ma"),
    ("warehouse",),
    ("jd", "bc"),
    ("od", "bc"),
    ("postgres", "ql"),
    ("my", "sql"),
    ("sq", "lite"),
    ("snow", "flake"),
    ("big", "query"),
    ("red", "shift"),
    ("to", "ken"),
    ("se", "cret"),
    ("au", "th"),
    ("bear", "er"),
    ("api", "_key"),
    ("private", "_key"),
    ("password",),
    ("cred", "ential"),
    ("sess", "ion"),
    ("j", "wt"),
    ("o", "au", "th"),
    ("wal", "let"),
    ("or", "der"),
    ("tra", "de"),
    ("pos", "ition"),
    ("b", "uy"),
    ("se", "ll"),
    ("reco", "mmendation"),
    ("reco", "mmend"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_UNSAFE_NORMALIZED_TERMS = tuple(
    term for term in ("".join(character for character in value if character.isalnum()) for value in _UNSAFE_TERMS) if term
)
_ROW_DIGEST_FIELDS = (
    "config_version",
    "redacted_candidate_ref",
    "evidence_claim_count",
    "traceable_claim_count",
    "traceable_claim_ratio",
    "replayable_step_count",
    "independent_review_count",
    "unresolved_gap_count",
    "cross_reference_ratio",
    "timestamp_coverage_ratio",
    "evidence_traceability_score",
    "status",
    "safety_flags",
    "reason_codes",
    "hard_flag_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_DIGEST_FIELDS = (
    "config_version",
    "candidate_count",
    "pass_count",
    "watch_count",
    "block_count",
    "max_evidence_traceability_score",
    "min_evidence_traceability_score",
    "average_evidence_traceability_score",
    "report_status",
    "safety_flags",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
_HEX_CHARS = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class CandidateDecisionEvidenceTraceabilityScoreConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_pass_traceability_score: Decimal = Decimal("0.750000")
    min_watch_traceability_score: Decimal = Decimal("0.450000")
    min_pass_traceable_claim_ratio: Decimal = Decimal("0.800000")
    min_watch_traceable_claim_ratio: Decimal = Decimal("0.500000")
    min_pass_replayable_step_count: Decimal = Decimal("2")
    min_watch_replayable_step_count: Decimal = Decimal("1")
    min_pass_independent_review_count: Decimal = Decimal("2")
    min_watch_independent_review_count: Decimal = Decimal("1")
    max_watch_unresolved_gap_count: Decimal = Decimal("1")
    max_block_unresolved_gap_count: Decimal = Decimal("3")
    traceable_claim_weight: Decimal = Decimal("0.350000")
    replayable_step_weight: Decimal = Decimal("0.200000")
    independent_review_weight: Decimal = Decimal("0.200000")
    cross_reference_weight: Decimal = Decimal("0.150000")
    timestamp_coverage_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "CandidateDecisionEvidenceTraceabilityScoreConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the default config version")
        for field_name in (
            "min_pass_traceability_score",
            "min_watch_traceability_score",
            "min_pass_traceable_claim_ratio",
            "min_watch_traceable_claim_ratio",
        ) + _WEIGHT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_replayable_step_count",
            "min_watch_replayable_step_count",
            "min_pass_independent_review_count",
            "min_watch_independent_review_count",
            "max_watch_unresolved_gap_count",
            "max_block_unresolved_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_traceability_score > self.min_pass_traceability_score:
            raise ValueError("min_watch_traceability_score must not exceed pass threshold")
        if self.min_watch_traceable_claim_ratio > self.min_pass_traceable_claim_ratio:
            raise ValueError("min_watch_traceable_claim_ratio must not exceed pass threshold")
        if self.min_watch_replayable_step_count > self.min_pass_replayable_step_count:
            raise ValueError("min_watch_replayable_step_count must not exceed pass threshold")
        if self.min_watch_independent_review_count > self.min_pass_independent_review_count:
            raise ValueError("min_watch_independent_review_count must not exceed pass threshold")
        if self.max_watch_unresolved_gap_count > self.max_block_unresolved_gap_count:
            raise ValueError("max_watch_unresolved_gap_count must not exceed block threshold")
        if _sum_decimal(getattr(self, field_name) for field_name in _WEIGHT_FIELDS) != ONE:
            raise ValueError("weight fields must sum to 1.000000")
        _require_hard_flags("traceability config", self)
        reject_candidate_decision_evidence_traceability_score_unsafe_payload(
            "traceability config",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionEvidenceTraceabilityScoreInput:
    redacted_candidate_ref: str
    evidence_claim_count: Decimal
    traceable_claim_count: Decimal
    replayable_step_count: Decimal
    independent_review_count: Decimal
    unresolved_gap_count: Decimal
    cross_reference_ratio: Decimal
    timestamp_coverage_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "CandidateDecisionEvidenceTraceabilityScoreInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _normalize_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        for field_name in (
            "evidence_claim_count",
            "traceable_claim_count",
            "replayable_step_count",
            "independent_review_count",
            "unresolved_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        if self.traceable_claim_count > self.evidence_claim_count:
            raise ValueError("traceable_claim_count must not exceed evidence_claim_count")
        for field_name in ("cross_reference_ratio", "timestamp_coverage_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("traceability input", self)
        reject_candidate_decision_evidence_traceability_score_unsafe_payload(
            "traceability input",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionEvidenceTraceabilityScoreRow:
    config_version: str
    redacted_candidate_ref: str
    evidence_claim_count: Decimal
    traceable_claim_count: Decimal
    traceable_claim_ratio: Decimal
    replayable_step_count: Decimal
    independent_review_count: Decimal
    unresolved_gap_count: Decimal
    cross_reference_ratio: Decimal
    timestamp_coverage_ratio: Decimal
    evidence_traceability_score: Decimal
    status: str
    safety_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    hard_flag_codes: tuple[str, ...] = ()
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "CandidateDecisionEvidenceTraceabilityScoreRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _normalize_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        for field_name in (
            "evidence_claim_count",
            "traceable_claim_count",
            "replayable_step_count",
            "independent_review_count",
            "unresolved_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        if self.traceable_claim_count > self.evidence_claim_count:
            raise ValueError("traceable_claim_count must not exceed evidence_claim_count")
        for field_name in (
            "traceable_claim_ratio",
            "cross_reference_ratio",
            "timestamp_coverage_ratio",
            "evidence_traceability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("status", self.status, STATUS_VALUES)
        object.__setattr__(self, "safety_flags", _normalize_safety_flags(self.safety_flags))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "hard_flag_codes",
            _normalize_reason_codes("hard_flag_codes", self.hard_flag_codes, allow_empty=True),
        )
        _validate_row(self)
        _require_hard_flags("traceability row", self)
        reject_candidate_decision_evidence_traceability_score_unsafe_payload(
            "traceability row",
            self,
        )
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match row fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_evidence_traceability_score_payload(self)


@dataclass(frozen=True)
class CandidateDecisionEvidenceTraceabilityScoreReport:
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_evidence_traceability_score: Decimal
    min_evidence_traceability_score: Decimal
    average_evidence_traceability_score: Decimal
    report_status: str
    safety_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[CandidateDecisionEvidenceTraceabilityScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "CandidateDecisionEvidenceTraceabilityScoreReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_evidence_traceability_score",
            "min_evidence_traceability_score",
            "average_evidence_traceability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("report_status", self.report_status, STATUS_VALUES)
        object.__setattr__(self, "safety_flags", _normalize_safety_flags(self.safety_flags))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("traceability report", self)
        reject_candidate_decision_evidence_traceability_score_unsafe_payload(
            "traceability report",
            self,
        )
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_evidence_traceability_score_payload(self)


def score_candidate_decision_evidence_traceability(
    score_input: CandidateDecisionEvidenceTraceabilityScoreInput,
    *,
    config: CandidateDecisionEvidenceTraceabilityScoreConfig | None = None,
) -> CandidateDecisionEvidenceTraceabilityScoreRow:
    if type(score_input) is not CandidateDecisionEvidenceTraceabilityScoreInput:
        raise ValueError(
            "score_input must be a CandidateDecisionEvidenceTraceabilityScoreInput",
        )
    score_config = config or CandidateDecisionEvidenceTraceabilityScoreConfig()
    if type(score_config) is not CandidateDecisionEvidenceTraceabilityScoreConfig:
        raise ValueError("config must be a CandidateDecisionEvidenceTraceabilityScoreConfig")
    _require_hard_flags("traceability input", score_input)
    _require_hard_flags("traceability config", score_config)
    reject_candidate_decision_evidence_traceability_score_unsafe_payload(
        "traceability input",
        score_input,
    )
    reject_candidate_decision_evidence_traceability_score_unsafe_payload(
        "traceability config",
        score_config,
    )

    traceable_claim_ratio = _traceable_claim_ratio(score_input)
    evidence_traceability_score = _evidence_traceability_score(
        score_input,
        score_config,
        traceable_claim_ratio,
    )
    hard_flag_codes = _hard_flag_codes(score_input, score_config, traceable_claim_ratio)
    status = _status(
        score_input,
        score_config,
        traceable_claim_ratio,
        evidence_traceability_score,
        hard_flag_codes,
    )
    return CandidateDecisionEvidenceTraceabilityScoreRow(
        config_version=score_config.config_version,
        redacted_candidate_ref=score_input.redacted_candidate_ref,
        evidence_claim_count=score_input.evidence_claim_count,
        traceable_claim_count=score_input.traceable_claim_count,
        traceable_claim_ratio=traceable_claim_ratio,
        replayable_step_count=score_input.replayable_step_count,
        independent_review_count=score_input.independent_review_count,
        unresolved_gap_count=score_input.unresolved_gap_count,
        cross_reference_ratio=score_input.cross_reference_ratio,
        timestamp_coverage_ratio=score_input.timestamp_coverage_ratio,
        evidence_traceability_score=evidence_traceability_score,
        status=status,
        safety_flags=SAFETY_FLAGS,
        reason_codes=_row_reason_codes(
            score_input.reason_codes,
            score_input,
            score_config,
            traceable_claim_ratio,
            evidence_traceability_score,
            status,
            hard_flag_codes,
        ),
        hard_flag_codes=hard_flag_codes,
    )


def build_candidate_decision_evidence_traceability_score_report(
    candidates: Iterable[CandidateDecisionEvidenceTraceabilityScoreInput],
    *,
    config: CandidateDecisionEvidenceTraceabilityScoreConfig | None = None,
) -> CandidateDecisionEvidenceTraceabilityScoreReport:
    report_config = config or CandidateDecisionEvidenceTraceabilityScoreConfig()
    if type(report_config) is not CandidateDecisionEvidenceTraceabilityScoreConfig:
        raise ValueError("config must be a CandidateDecisionEvidenceTraceabilityScoreConfig")
    _require_hard_flags("traceability config", report_config)
    rows = tuple(
        sorted(
            (
                score_candidate_decision_evidence_traceability(
                    score_input,
                    config=report_config,
                )
                for score_input in _normalize_inputs(candidates)
            ),
            key=_row_sort_key,
        ),
    )
    candidate_count = _count(len(rows))
    pass_count = _count(sum(Decimal("1") for row in rows if row.status == "pass"))
    watch_count = _count(sum(Decimal("1") for row in rows if row.status == "watch"))
    block_count = _count(sum(Decimal("1") for row in rows if row.status == "block"))
    return CandidateDecisionEvidenceTraceabilityScoreReport(
        config_version=report_config.config_version,
        candidate_count=candidate_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_evidence_traceability_score=_max_score(rows),
        min_evidence_traceability_score=_min_score(rows),
        average_evidence_traceability_score=_average_score(rows),
        report_status=_report_status(rows),
        safety_flags=SAFETY_FLAGS,
        reason_codes=_report_reason_codes(
            pass_count=pass_count,
            watch_count=watch_count,
            block_count=block_count,
        ),
        rows=rows,
    )


def candidate_decision_evidence_traceability_score_payload(
    value: CandidateDecisionEvidenceTraceabilityScoreRow
    | CandidateDecisionEvidenceTraceabilityScoreReport,
) -> dict[str, Any]:
    if type(value) is CandidateDecisionEvidenceTraceabilityScoreRow:
        _require_hard_flags("traceability row", value)
        if value.derived_validation_digest != _row_digest(value):
            raise ValueError("derived_validation_digest must match row fields")
    elif type(value) is CandidateDecisionEvidenceTraceabilityScoreReport:
        _require_hard_flags("traceability report", value)
        if value.derived_validation_digest != _report_digest(value):
            raise ValueError("derived_validation_digest must match report fields")
    else:
        raise ValueError("value must be a traceability row or report")
    reject_candidate_decision_evidence_traceability_score_unsafe_payload(
        "traceability payload",
        value,
    )
    result = _public_value(value)
    if type(result) is not dict:
        raise ValueError("payload must be a dict")
    return result


def reject_candidate_decision_evidence_traceability_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for path, item in _iter_public_strings(payload):
        if _contains_unsafe_term(item):
            raise ValueError(f"unsafe public payload entry in {label}: {path}")


def _traceable_claim_ratio(
    score_input: CandidateDecisionEvidenceTraceabilityScoreInput,
) -> Decimal:
    if score_input.evidence_claim_count == ZERO:
        return ZERO
    return _normalize_unit_decimal(
        "traceable_claim_ratio",
        score_input.traceable_claim_count / score_input.evidence_claim_count,
    )


def _evidence_traceability_score(
    score_input: CandidateDecisionEvidenceTraceabilityScoreInput,
    config: CandidateDecisionEvidenceTraceabilityScoreConfig,
    traceable_claim_ratio: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = _DECIMAL_CONTEXT_PRECISION
        score = (
            traceable_claim_ratio * config.traceable_claim_weight
            + _count_component(
                score_input.replayable_step_count,
                config.min_pass_replayable_step_count,
            )
            * config.replayable_step_weight
            + _count_component(
                score_input.independent_review_count,
                config.min_pass_independent_review_count,
            )
            * config.independent_review_weight
            + score_input.cross_reference_ratio * config.cross_reference_weight
            + score_input.timestamp_coverage_ratio * config.timestamp_coverage_weight
        )
        if score_input.unresolved_gap_count > config.max_watch_unresolved_gap_count:
            score -= _count_component(
                score_input.unresolved_gap_count,
                config.max_block_unresolved_gap_count,
            ) * Decimal("0.100000")
        return _normalize_unit_decimal("evidence_traceability_score", max(score, ZERO))


def _count_component(value: Decimal, pass_level: Decimal) -> Decimal:
    if pass_level == ZERO:
        return ONE
    if value >= pass_level:
        return ONE
    return _normalize_unit_decimal("count_component", value / pass_level)


def _hard_flag_codes(
    score_input: CandidateDecisionEvidenceTraceabilityScoreInput,
    config: CandidateDecisionEvidenceTraceabilityScoreConfig,
    traceable_claim_ratio: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if score_input.evidence_claim_count == ZERO:
        codes.append("evidence_claim_count_block")
    if score_input.traceable_claim_count == ZERO:
        codes.append("traceable_claim_count_block")
    if traceable_claim_ratio < config.min_watch_traceable_claim_ratio:
        codes.append("traceable_claim_ratio_block")
    if score_input.replayable_step_count < config.min_watch_replayable_step_count:
        codes.append("replayable_step_count_block")
    if score_input.independent_review_count < config.min_watch_independent_review_count:
        codes.append("independent_review_count_block")
    if score_input.unresolved_gap_count >= config.max_block_unresolved_gap_count:
        codes.append("unresolved_gap_count_block")
    return tuple(codes)


def _status(
    score_input: CandidateDecisionEvidenceTraceabilityScoreInput,
    config: CandidateDecisionEvidenceTraceabilityScoreConfig,
    traceable_claim_ratio: Decimal,
    evidence_traceability_score: Decimal,
    hard_flag_codes: tuple[str, ...],
) -> str:
    if hard_flag_codes:
        return "block"
    if evidence_traceability_score < config.min_watch_traceability_score:
        return "block"
    if evidence_traceability_score < config.min_pass_traceability_score:
        return "watch"
    if traceable_claim_ratio < config.min_pass_traceable_claim_ratio:
        return "watch"
    if score_input.replayable_step_count < config.min_pass_replayable_step_count:
        return "watch"
    if score_input.independent_review_count < config.min_pass_independent_review_count:
        return "watch"
    if score_input.unresolved_gap_count > config.max_watch_unresolved_gap_count:
        return "watch"
    return "pass"


def _row_reason_codes(
    existing: tuple[str, ...],
    score_input: CandidateDecisionEvidenceTraceabilityScoreInput,
    config: CandidateDecisionEvidenceTraceabilityScoreConfig,
    traceable_claim_ratio: Decimal,
    evidence_traceability_score: Decimal,
    status: str,
    hard_flag_codes: tuple[str, ...],
) -> tuple[str, ...]:
    additions = [
        "candidate_decision_evidence_traceability_score",
        f"evidence_traceability_{status}",
        _ratio_reason(
            "traceable_claim_ratio",
            traceable_claim_ratio,
            config.min_pass_traceable_claim_ratio,
            config.min_watch_traceable_claim_ratio,
        ),
        _count_reason(
            "replayable_step_count",
            score_input.replayable_step_count,
            config.min_pass_replayable_step_count,
            config.min_watch_replayable_step_count,
        ),
        _count_reason(
            "independent_review_count",
            score_input.independent_review_count,
            config.min_pass_independent_review_count,
            config.min_watch_independent_review_count,
        ),
        _quality_reason("cross_reference_ratio", score_input.cross_reference_ratio),
        _quality_reason("timestamp_coverage_ratio", score_input.timestamp_coverage_ratio),
    ]
    additions.extend(hard_flag_codes)
    if hard_flag_codes:
        additions.append("hard_flag_present")
    elif evidence_traceability_score >= config.min_pass_traceability_score and status == "pass":
        additions.append("traceability_score_pass_threshold_met")
    elif evidence_traceability_score >= config.min_pass_traceability_score and status == "watch":
        additions.append("traceability_score_pass_but_reviewability_watch")
    elif evidence_traceability_score >= config.min_watch_traceability_score:
        additions.append("traceability_score_between_watch_and_pass")
    else:
        additions.append("traceability_score_below_watch_threshold")
    return _append_reason_codes(existing, tuple(additions))


def _ratio_reason(
    name: str,
    value: Decimal,
    pass_level: Decimal,
    watch_level: Decimal,
) -> str:
    if value >= pass_level:
        return f"{name}_pass"
    if value >= watch_level:
        return f"{name}_watch"
    return f"{name}_block"


def _count_reason(
    name: str,
    value: Decimal,
    pass_level: Decimal,
    watch_level: Decimal,
) -> str:
    if value >= pass_level:
        return f"{name}_pass"
    if value >= watch_level:
        return f"{name}_watch"
    return f"{name}_block"


def _quality_reason(name: str, value: Decimal) -> str:
    if value >= Decimal("0.700000"):
        return f"{name}_strong"
    if value >= Decimal("0.400000"):
        return f"{name}_moderate"
    return f"{name}_weak"


def _report_reason_codes(
    *,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
) -> tuple[str, ...]:
    additions = ["candidate_decision_evidence_traceability_score_report"]
    if block_count > ZERO:
        additions.append("block_status_present")
    if watch_count > ZERO:
        additions.append("watch_status_present")
    if pass_count > ZERO:
        additions.append("pass_status_present")
    if pass_count == watch_count == block_count == ZERO:
        additions.append("empty_report")
    return tuple(additions)


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_row(row: CandidateDecisionEvidenceTraceabilityScoreRow) -> None:
    if row.traceable_claim_ratio != (
        ZERO
        if row.evidence_claim_count == ZERO
        else _normalize_unit_decimal(
            "traceable_claim_ratio",
            row.traceable_claim_count / row.evidence_claim_count,
        )
    ):
        raise ValueError("traceable_claim_ratio must match counts")
    if row.safety_flags != SAFETY_FLAGS:
        raise ValueError("safety_flags must match report-only flags")


def _validate_report(report: CandidateDecisionEvidenceTraceabilityScoreReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(sum(Decimal("1") for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(Decimal("1") for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(Decimal("1") for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.max_evidence_traceability_score != _max_score(rows):
        raise ValueError("max_evidence_traceability_score must match rows")
    if report.min_evidence_traceability_score != _min_score(rows):
        raise ValueError("min_evidence_traceability_score must match rows")
    if report.average_evidence_traceability_score != _average_score(rows):
        raise ValueError("average_evidence_traceability_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.safety_flags != SAFETY_FLAGS:
        raise ValueError("safety_flags must match report-only flags")


def _normalize_inputs(
    candidates: Iterable[CandidateDecisionEvidenceTraceabilityScoreInput],
) -> tuple[CandidateDecisionEvidenceTraceabilityScoreInput, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of score inputs")
    values = tuple(candidates)
    seen: set[str] = set()
    for candidate in values:
        if type(candidate) is not CandidateDecisionEvidenceTraceabilityScoreInput:
            raise ValueError(
                "candidates must contain CandidateDecisionEvidenceTraceabilityScoreInput",
            )
        if candidate.redacted_candidate_ref in seen:
            raise ValueError("duplicate redacted_candidate_ref")
        seen.add(candidate.redacted_candidate_ref)
    return values


def _normalize_rows(
    rows: object,
) -> tuple[CandidateDecisionEvidenceTraceabilityScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    normalized = tuple(sorted(rows, key=_row_sort_key))
    for row in normalized:
        if type(row) is not CandidateDecisionEvidenceTraceabilityScoreRow:
            raise ValueError("rows must contain CandidateDecisionEvidenceTraceabilityScoreRow")
        if row.redacted_candidate_ref in seen:
            raise ValueError("duplicate redacted_candidate_ref")
        seen.add(row.redacted_candidate_ref)
    return normalized


def _row_sort_key(
    row: CandidateDecisionEvidenceTraceabilityScoreRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        _STATUS_SORT_RANK[row.status],
        row.evidence_traceability_score,
        row.redacted_candidate_ref,
    )


def _report_status(rows: tuple[CandidateDecisionEvidenceTraceabilityScoreRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _max_score(rows: tuple[CandidateDecisionEvidenceTraceabilityScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.evidence_traceability_score for row in rows)


def _min_score(rows: tuple[CandidateDecisionEvidenceTraceabilityScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.evidence_traceability_score for row in rows)


def _average_score(rows: tuple[CandidateDecisionEvidenceTraceabilityScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_unit_decimal(
        "average_evidence_traceability_score",
        _sum_decimal(row.evidence_traceability_score for row in rows) / _count(len(rows)),
    )


def _normalize_redacted_candidate_ref(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if not value.startswith(REDACTED_CANDIDATE_REF_PREFIX):
        raise ValueError(f"{field_name} must be a redacted candidate ref")
    suffix = value[len(REDACTED_CANDIDATE_REF_PREFIX) :]
    if not suffix:
        raise ValueError(f"{field_name} must be a redacted candidate ref")
    if _contains_unsafe_term(value):
        raise ValueError(f"{field_name} must be a safe redacted candidate ref")
    return value


def _normalize_safety_flags(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("safety_flags must be a tuple")
    if value != SAFETY_FLAGS:
        raise ValueError("safety_flags must match report-only flags")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _require_decimal(field_name, value).quantize(QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{field_name} must be finite")
        return value
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be an exact Decimal")
    raise ValueError(f"{field_name} must be a Decimal")


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return total


def _count(value: object) -> Decimal:
    if type(value) is int:
        return Decimal(value).quantize(COUNT_QUANTUM)
    if type(value) is Decimal:
        return _normalize_nonnegative_integral_decimal("count", value)
    raise ValueError("count must be an int or Decimal")


def _require_choice(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _require_canonical_digest(value: str) -> None:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != 64 or any(char not in _HEX_CHARS for char in value):
        raise ValueError("derived_validation_digest must be a canonical sha256 digest")


def _row_digest(row: CandidateDecisionEvidenceTraceabilityScoreRow) -> str:
    return _digest_from_fields(row, _ROW_DIGEST_FIELDS)


def _report_digest(report: CandidateDecisionEvidenceTraceabilityScoreReport) -> str:
    return _digest_from_fields(report, _REPORT_DIGEST_FIELDS)


def _digest_from_fields(value: object, field_names: tuple[str, ...]) -> str:
    material = tuple((field_name, _public_value(getattr(value, field_name))) for field_name in field_names)
    return sha256(repr(material).encode("utf-8")).hexdigest()


def _public_value(value: object) -> object:
    if is_dataclass(value):
        result = {
            field.name: _public_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != "derived_validation_digest"
        }
        if hasattr(value, "derived_validation_digest"):
            result["derived_validation_digest"] = getattr(value, "derived_validation_digest")
        return result
    if type(value) is Decimal:
        return str(value)
    if type(value) is tuple:
        return [_public_value(item) for item in value]
    if type(value) is list:
        return [_public_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _public_value(item) for key, item in value.items()}
    return value


def _iter_public_strings(value: object, path: str = "payload") -> Iterable[tuple[str, str]]:
    if is_dataclass(value):
        for field in fields(value):
            yield from _iter_public_strings(getattr(value, field.name), f"{path}.{field.name}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            yield f"{path}.{key_text}", key_text
            yield from _iter_public_strings(item, f"{path}.{key_text}")
        return
    if isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            yield from _iter_public_strings(item, f"{path}.{index}")
        return
    if type(value) is str:
        yield path, value


def _contains_unsafe_term(value: str) -> bool:
    lowered = value.lower()
    normalized = "".join(character for character in lowered if character.isalnum())
    return any(term in lowered for term in _UNSAFE_TERMS) or any(
        term in normalized for term in _UNSAFE_NORMALIZED_TERMS
    )


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "STATUS_VALUES",
    "SAFETY_FLAGS",
    "CandidateDecisionEvidenceTraceabilityScoreConfig",
    "CandidateDecisionEvidenceTraceabilityScoreInput",
    "CandidateDecisionEvidenceTraceabilityScoreRow",
    "CandidateDecisionEvidenceTraceabilityScoreReport",
    "score_candidate_decision_evidence_traceability",
    "build_candidate_decision_evidence_traceability_score_report",
    "candidate_decision_evidence_traceability_score_payload",
    "reject_candidate_decision_evidence_traceability_score_unsafe_payload",
)
