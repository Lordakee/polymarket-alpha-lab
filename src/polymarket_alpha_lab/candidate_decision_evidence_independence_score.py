"""Pure report-only evidence independence scoring."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
from typing import Any, Iterable


DEFAULT_CONFIG_VERSION = "candidate-decision-evidence-independence-score-v0"
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
_UNSAFE_TERM_PARTS = (
    ("candidate", "_id"),
    ("candidate", "-id"),
    ("market", "_id"),
    ("market", "_slug"),
    ("market", "-"),
    ("event", "_slug"),
    ("sl", "ug"),
    ("normalized_", "market_", "ques", "tion"),
    ("ques", "tion"),
    ("source", "_ref"),
    ("source", "_refs"),
    ("source", "_url"),
    ("source", "_text"),
    ("source", "_id"),
    ("source", "-ref"),
    ("source", "-url"),
    ("source", "-text"),
    ("source", "-id"),
    ("url",),
    ("://",),
    ("www", "."),
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
    ("au", "thor", "ization"),
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
    ("b", "uy"),
    ("se", "ll"),
    ("reco", "mmendation"),
    ("reco", "mmend"),
    ("position", "_sizing"),
    ("position", "-sizing"),
    ("position", "_size"),
    ("net", "work"),
    ("data", "base"),
    ("per", "sist"),
    ("li", "ve"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_ROW_DIGEST_FIELDS = (
    "config_version",
    "redacted_candidate_ref",
    "evidence_source_count",
    "independent_source_count",
    "independent_source_ratio",
    "shared_origin_ratio",
    "circular_reference_ratio",
    "corroboration_score",
    "source_quality_score",
    "evidence_independence_score",
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
    "max_evidence_independence_score",
    "min_evidence_independence_score",
    "average_evidence_independence_score",
    "report_status",
    "safety_flags",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
_WEIGHT_FIELDS = (
    "independent_source_weight",
    "shared_origin_weight",
    "circular_reference_weight",
    "corroboration_weight",
    "source_quality_weight",
)
_HEX_CHARS = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class CandidateDecisionEvidenceIndependenceScoreConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_pass_independence_score: Decimal = Decimal("0.700000")
    min_watch_independence_score: Decimal = Decimal("0.400000")
    min_pass_independent_source_count: Decimal = Decimal("3")
    min_watch_independent_source_count: Decimal = Decimal("2")
    min_watch_evidence_source_count: Decimal = Decimal("2")
    max_watch_shared_origin_ratio: Decimal = Decimal("0.350000")
    max_block_shared_origin_ratio: Decimal = Decimal("0.700000")
    max_watch_circular_reference_ratio: Decimal = Decimal("0.150000")
    max_block_circular_reference_ratio: Decimal = Decimal("0.400000")
    independent_source_weight: Decimal = Decimal("0.300000")
    shared_origin_weight: Decimal = Decimal("0.200000")
    circular_reference_weight: Decimal = Decimal("0.200000")
    corroboration_weight: Decimal = Decimal("0.150000")
    source_quality_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionEvidenceIndependenceScoreConfig:
            raise ValueError(
                "config must be exactly CandidateDecisionEvidenceIndependenceScoreConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the default config version")
        for field_name in (
            "min_pass_independence_score",
            "min_watch_independence_score",
            "max_watch_shared_origin_ratio",
            "max_block_shared_origin_ratio",
            "max_watch_circular_reference_ratio",
            "max_block_circular_reference_ratio",
        ) + _WEIGHT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_independent_source_count",
            "min_watch_independent_source_count",
            "min_watch_evidence_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_integral_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_independence_score > self.min_pass_independence_score:
            raise ValueError("min_watch_independence_score must not exceed pass threshold")
        if self.min_watch_independent_source_count > self.min_pass_independent_source_count:
            raise ValueError("min_watch_independent_source_count must not exceed pass threshold")
        if self.max_watch_shared_origin_ratio > self.max_block_shared_origin_ratio:
            raise ValueError("max_watch_shared_origin_ratio must not exceed block threshold")
        if self.max_watch_circular_reference_ratio > self.max_block_circular_reference_ratio:
            raise ValueError("max_watch_circular_reference_ratio must not exceed block threshold")
        if _sum_decimal(getattr(self, field_name) for field_name in _WEIGHT_FIELDS) != ONE:
            raise ValueError("weight fields must sum to 1.000000")
        _require_paper_flags("evidence independence config", self)
        reject_candidate_decision_evidence_independence_score_unsafe_payload(
            "evidence independence config",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionEvidenceIndependenceScoreInput:
    redacted_candidate_ref: str
    evidence_source_count: Decimal
    independent_source_count: Decimal
    shared_origin_ratio: Decimal
    circular_reference_ratio: Decimal
    corroboration_score: Decimal
    source_quality_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionEvidenceIndependenceScoreInput:
            raise ValueError(
                "score_input must be exactly CandidateDecisionEvidenceIndependenceScoreInput",
            )
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _normalize_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        for field_name in ("evidence_source_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.evidence_source_count:
            raise ValueError("independent_source_count must not exceed evidence_source_count")
        for field_name in (
            "shared_origin_ratio",
            "circular_reference_ratio",
            "corroboration_score",
            "source_quality_score",
        ):
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
        _require_paper_flags("evidence independence input", self)
        reject_candidate_decision_evidence_independence_score_unsafe_payload(
            "evidence independence input",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionEvidenceIndependenceScoreRow:
    config_version: str
    redacted_candidate_ref: str
    evidence_source_count: Decimal
    independent_source_count: Decimal
    independent_source_ratio: Decimal
    shared_origin_ratio: Decimal
    circular_reference_ratio: Decimal
    corroboration_score: Decimal
    source_quality_score: Decimal
    evidence_independence_score: Decimal
    status: str
    safety_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    hard_flag_codes: tuple[str, ...] = ()
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionEvidenceIndependenceScoreRow:
            raise ValueError("row must be exactly CandidateDecisionEvidenceIndependenceScoreRow")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _normalize_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        for field_name in ("evidence_source_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.evidence_source_count:
            raise ValueError("independent_source_count must not exceed evidence_source_count")
        for field_name in (
            "independent_source_ratio",
            "shared_origin_ratio",
            "circular_reference_ratio",
            "corroboration_score",
            "source_quality_score",
            "evidence_independence_score",
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
        _require_paper_flags("evidence independence row", self)
        reject_candidate_decision_evidence_independence_score_unsafe_payload(
            "evidence independence row",
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
        return candidate_decision_evidence_independence_score_payload(self)


@dataclass(frozen=True)
class CandidateDecisionEvidenceIndependenceScoreReport:
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_evidence_independence_score: Decimal
    min_evidence_independence_score: Decimal
    average_evidence_independence_score: Decimal
    report_status: str
    safety_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[CandidateDecisionEvidenceIndependenceScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionEvidenceIndependenceScoreReport:
            raise ValueError(
                "report must be exactly CandidateDecisionEvidenceIndependenceScoreReport",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_evidence_independence_score",
            "min_evidence_independence_score",
            "average_evidence_independence_score",
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
        _require_paper_flags("evidence independence report", self)
        reject_candidate_decision_evidence_independence_score_unsafe_payload(
            "evidence independence report",
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
        return candidate_decision_evidence_independence_score_payload(self)


def score_candidate_decision_evidence_independence(
    score_input: CandidateDecisionEvidenceIndependenceScoreInput,
    *,
    config: CandidateDecisionEvidenceIndependenceScoreConfig | None = None,
) -> CandidateDecisionEvidenceIndependenceScoreRow:
    if type(score_input) is not CandidateDecisionEvidenceIndependenceScoreInput:
        raise ValueError(
            "score_input must be a CandidateDecisionEvidenceIndependenceScoreInput",
        )
    score_config = config or CandidateDecisionEvidenceIndependenceScoreConfig()
    if type(score_config) is not CandidateDecisionEvidenceIndependenceScoreConfig:
        raise ValueError("config must be a CandidateDecisionEvidenceIndependenceScoreConfig")
    _require_paper_flags("evidence independence input", score_input)
    _require_paper_flags("evidence independence config", score_config)
    reject_candidate_decision_evidence_independence_score_unsafe_payload(
        "evidence independence input",
        score_input,
    )
    reject_candidate_decision_evidence_independence_score_unsafe_payload(
        "evidence independence config",
        score_config,
    )

    independent_source_ratio = _source_ratio(score_input)
    evidence_independence_score = _evidence_independence_score(score_input, score_config)
    hard_flag_codes = _hard_flag_codes(score_input, score_config)
    status = _status(score_input, score_config, evidence_independence_score, hard_flag_codes)
    return CandidateDecisionEvidenceIndependenceScoreRow(
        config_version=score_config.config_version,
        redacted_candidate_ref=score_input.redacted_candidate_ref,
        evidence_source_count=score_input.evidence_source_count,
        independent_source_count=score_input.independent_source_count,
        independent_source_ratio=independent_source_ratio,
        shared_origin_ratio=score_input.shared_origin_ratio,
        circular_reference_ratio=score_input.circular_reference_ratio,
        corroboration_score=score_input.corroboration_score,
        source_quality_score=score_input.source_quality_score,
        evidence_independence_score=evidence_independence_score,
        status=status,
        safety_flags=SAFETY_FLAGS,
        reason_codes=_row_reason_codes(
            score_input.reason_codes,
            score_input,
            score_config,
            evidence_independence_score,
            status,
            hard_flag_codes,
        ),
        hard_flag_codes=hard_flag_codes,
    )


def build_candidate_decision_evidence_independence_score_report(
    candidates: Iterable[CandidateDecisionEvidenceIndependenceScoreInput],
    *,
    config: CandidateDecisionEvidenceIndependenceScoreConfig | None = None,
) -> CandidateDecisionEvidenceIndependenceScoreReport:
    report_config = config or CandidateDecisionEvidenceIndependenceScoreConfig()
    if type(report_config) is not CandidateDecisionEvidenceIndependenceScoreConfig:
        raise ValueError("config must be a CandidateDecisionEvidenceIndependenceScoreConfig")
    _require_paper_flags("evidence independence config", report_config)
    input_rows = _normalize_inputs(candidates)
    rows = tuple(
        sorted(
            (
                score_candidate_decision_evidence_independence(
                    score_input,
                    config=report_config,
                )
                for score_input in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    candidate_count = _count(len(rows))
    pass_count = _count(sum(Decimal("1") for row in rows if row.status == "pass"))
    watch_count = _count(sum(Decimal("1") for row in rows if row.status == "watch"))
    block_count = _count(sum(Decimal("1") for row in rows if row.status == "block"))
    report_status = _report_status(rows)
    return CandidateDecisionEvidenceIndependenceScoreReport(
        config_version=report_config.config_version,
        candidate_count=candidate_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_evidence_independence_score=_max_score(rows),
        min_evidence_independence_score=_min_score(rows),
        average_evidence_independence_score=_average_score(rows),
        report_status=report_status,
        safety_flags=SAFETY_FLAGS,
        reason_codes=_report_reason_codes(
            pass_count=pass_count,
            watch_count=watch_count,
            block_count=block_count,
        ),
        rows=rows,
    )


def candidate_decision_evidence_independence_score_payload(
    value: CandidateDecisionEvidenceIndependenceScoreRow
    | CandidateDecisionEvidenceIndependenceScoreReport,
) -> dict[str, Any]:
    if type(value) is CandidateDecisionEvidenceIndependenceScoreRow:
        _require_paper_flags("evidence independence row", value)
        if value.derived_validation_digest != _row_digest(value):
            raise ValueError("derived_validation_digest must match row fields")
    elif type(value) is CandidateDecisionEvidenceIndependenceScoreReport:
        _require_paper_flags("evidence independence report", value)
        if value.derived_validation_digest != _report_digest(value):
            raise ValueError("derived_validation_digest must match report fields")
    else:
        raise ValueError("value must be an evidence independence row or report")
    reject_candidate_decision_evidence_independence_score_unsafe_payload(
        "evidence independence payload",
        value,
    )
    result = _public_value(value)
    if type(result) is not dict:
        raise ValueError("payload must be a dict")
    return result


def reject_candidate_decision_evidence_independence_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for path, item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}: {path}")


def _source_ratio(score_input: CandidateDecisionEvidenceIndependenceScoreInput) -> Decimal:
    if score_input.evidence_source_count == ZERO:
        return ZERO
    return _normalize_unit_decimal(
        "independent_source_ratio",
        score_input.independent_source_count / score_input.evidence_source_count,
    )


def _evidence_independence_score(
    score_input: CandidateDecisionEvidenceIndependenceScoreInput,
    config: CandidateDecisionEvidenceIndependenceScoreConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = _DECIMAL_CONTEXT_PRECISION
        independent_source_component = _source_count_component(
            score_input.independent_source_count,
            config.min_pass_independent_source_count,
        )
        score = (
            independent_source_component * config.independent_source_weight
            + (ONE - score_input.shared_origin_ratio) * config.shared_origin_weight
            + (ONE - score_input.circular_reference_ratio)
            * config.circular_reference_weight
            + score_input.corroboration_score * config.corroboration_weight
            + score_input.source_quality_score * config.source_quality_weight
        )
        if score_input.circular_reference_ratio >= config.max_block_circular_reference_ratio:
            score -= score_input.circular_reference_ratio * Decimal("0.100000")
        return _normalize_unit_decimal("evidence_independence_score", max(score, ZERO))


def _source_count_component(source_count: Decimal, source_count_cap: Decimal) -> Decimal:
    if source_count >= source_count_cap:
        return ONE
    return _normalize_unit_decimal("source_count_component", source_count / source_count_cap)


def _hard_flag_codes(
    score_input: CandidateDecisionEvidenceIndependenceScoreInput,
    config: CandidateDecisionEvidenceIndependenceScoreConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if score_input.evidence_source_count < config.min_watch_evidence_source_count:
        codes.append("evidence_source_count_block")
    if score_input.independent_source_count < config.min_watch_independent_source_count:
        codes.append("independent_source_count_block")
    if score_input.shared_origin_ratio >= config.max_block_shared_origin_ratio:
        codes.append("shared_origin_ratio_block")
    if score_input.circular_reference_ratio >= config.max_block_circular_reference_ratio:
        codes.append("circular_reference_ratio_block")
    return tuple(codes)


def _status(
    score_input: CandidateDecisionEvidenceIndependenceScoreInput,
    config: CandidateDecisionEvidenceIndependenceScoreConfig,
    evidence_independence_score: Decimal,
    hard_flag_codes: tuple[str, ...],
) -> str:
    if hard_flag_codes:
        return "block"
    if evidence_independence_score < config.min_watch_independence_score:
        return "block"
    if evidence_independence_score < config.min_pass_independence_score:
        return "watch"
    if score_input.independent_source_count < config.min_pass_independent_source_count:
        return "watch"
    if score_input.shared_origin_ratio > config.max_watch_shared_origin_ratio:
        return "watch"
    if score_input.circular_reference_ratio > config.max_watch_circular_reference_ratio:
        return "watch"
    return "pass"


def _row_reason_codes(
    existing: tuple[str, ...],
    score_input: CandidateDecisionEvidenceIndependenceScoreInput,
    config: CandidateDecisionEvidenceIndependenceScoreConfig,
    evidence_independence_score: Decimal,
    status: str,
    hard_flag_codes: tuple[str, ...],
) -> tuple[str, ...]:
    additions = [
        "candidate_decision_evidence_independence_score",
        f"evidence_independence_{status}",
        _independent_source_count_reason(score_input, config),
        _ratio_reason(
            "shared_origin_ratio",
            score_input.shared_origin_ratio,
            config.max_watch_shared_origin_ratio,
            config.max_block_shared_origin_ratio,
        ),
        _ratio_reason(
            "circular_reference_ratio",
            score_input.circular_reference_ratio,
            config.max_watch_circular_reference_ratio,
            config.max_block_circular_reference_ratio,
        ),
        _quality_reason("corroboration_score", score_input.corroboration_score),
        _quality_reason("source_quality_score", score_input.source_quality_score),
    ]
    additions.extend(hard_flag_codes)
    if hard_flag_codes:
        additions.append("hard_flag_present")
    elif evidence_independence_score >= config.min_pass_independence_score and status == "pass":
        additions.append("independence_score_pass_threshold_met")
    elif evidence_independence_score >= config.min_pass_independence_score and status == "watch":
        additions.append("independence_score_pass_but_overlap_watch")
    elif evidence_independence_score >= config.min_watch_independence_score:
        additions.append("independence_score_between_watch_and_pass")
    else:
        additions.append("independence_score_below_watch_threshold")
    return _append_reason_codes(existing, tuple(additions))


def _independent_source_count_reason(
    score_input: CandidateDecisionEvidenceIndependenceScoreInput,
    config: CandidateDecisionEvidenceIndependenceScoreConfig,
) -> str:
    if score_input.independent_source_count >= config.min_pass_independent_source_count:
        return "independent_source_count_pass"
    if score_input.independent_source_count >= config.min_watch_independent_source_count:
        return "independent_source_count_watch"
    return "independent_source_count_block"


def _ratio_reason(
    name: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value >= block_threshold:
        return f"{name}_block"
    if value > watch_threshold:
        return f"{name}_watch"
    return f"{name}_low"


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
    additions = ["candidate_decision_evidence_independence_score_report"]
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


def _validate_row(row: CandidateDecisionEvidenceIndependenceScoreRow) -> None:
    if row.independent_source_ratio != (
        ZERO
        if row.evidence_source_count == ZERO
        else _normalize_unit_decimal(
            "independent_source_ratio",
            row.independent_source_count / row.evidence_source_count,
        )
    ):
        raise ValueError("independent_source_ratio must match counts")
    if row.safety_flags != SAFETY_FLAGS:
        raise ValueError("safety_flags must match report-only flags")


def _validate_report(report: CandidateDecisionEvidenceIndependenceScoreReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(sum(Decimal("1") for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(Decimal("1") for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(Decimal("1") for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.max_evidence_independence_score != _max_score(rows):
        raise ValueError("max_evidence_independence_score must match rows")
    if report.min_evidence_independence_score != _min_score(rows):
        raise ValueError("min_evidence_independence_score must match rows")
    if report.average_evidence_independence_score != _average_score(rows):
        raise ValueError("average_evidence_independence_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.safety_flags != SAFETY_FLAGS:
        raise ValueError("safety_flags must match report-only flags")


def _normalize_inputs(
    candidates: Iterable[CandidateDecisionEvidenceIndependenceScoreInput],
) -> tuple[CandidateDecisionEvidenceIndependenceScoreInput, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of score inputs")
    values = tuple(candidates)
    seen: set[str] = set()
    for candidate in values:
        if type(candidate) is not CandidateDecisionEvidenceIndependenceScoreInput:
            raise ValueError(
                "candidates must contain CandidateDecisionEvidenceIndependenceScoreInput",
            )
        if candidate.redacted_candidate_ref in seen:
            raise ValueError("duplicate redacted_candidate_ref")
        seen.add(candidate.redacted_candidate_ref)
    return values


def _normalize_rows(
    rows: object,
) -> tuple[CandidateDecisionEvidenceIndependenceScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    normalized = tuple(sorted(rows, key=_row_sort_key))
    for row in normalized:
        if type(row) is not CandidateDecisionEvidenceIndependenceScoreRow:
            raise ValueError("rows must contain CandidateDecisionEvidenceIndependenceScoreRow")
        if row.redacted_candidate_ref in seen:
            raise ValueError("duplicate redacted_candidate_ref")
        seen.add(row.redacted_candidate_ref)
    return normalized


def _row_sort_key(row: CandidateDecisionEvidenceIndependenceScoreRow) -> tuple[Decimal, Decimal, str]:
    return (
        _STATUS_SORT_RANK[row.status],
        row.evidence_independence_score,
        row.redacted_candidate_ref,
    )


def _report_status(rows: tuple[CandidateDecisionEvidenceIndependenceScoreRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _max_score(rows: tuple[CandidateDecisionEvidenceIndependenceScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.evidence_independence_score for row in rows)


def _min_score(rows: tuple[CandidateDecisionEvidenceIndependenceScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.evidence_independence_score for row in rows)


def _average_score(rows: tuple[CandidateDecisionEvidenceIndependenceScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_unit_decimal(
        "average_evidence_independence_score",
        _sum_decimal(row.evidence_independence_score for row in rows) / _count(len(rows)),
    )


def _normalize_redacted_candidate_ref(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a redacted candidate ref")
    if not value.startswith(REDACTED_CANDIDATE_REF_PREFIX):
        raise ValueError(f"{field_name} must be a redacted candidate ref")
    suffix = value[len(REDACTED_CANDIDATE_REF_PREFIX) :]
    if not suffix:
        raise ValueError(f"{field_name} must be a redacted candidate ref")
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_TERMS):
        digest = sha256(f"{field_name}\0{value}".encode("utf-8")).hexdigest()[:16]
        return f"{REDACTED_CANDIDATE_REF_PREFIX}{digest}"
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


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_integral_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


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


def _require_paper_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _require_canonical_digest(value: str) -> None:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != 64 or any(char not in _HEX_CHARS for char in value):
        raise ValueError("derived_validation_digest must be a canonical sha256 digest")


def _row_digest(row: CandidateDecisionEvidenceIndependenceScoreRow) -> str:
    return _digest_from_fields(row, _ROW_DIGEST_FIELDS)


def _report_digest(report: CandidateDecisionEvidenceIndependenceScoreReport) -> str:
    return _digest_from_fields(report, _REPORT_DIGEST_FIELDS)


def _digest_from_fields(value: object, field_names: tuple[str, ...]) -> str:
    material = tuple((field_name, _public_value(getattr(value, field_name))) for field_name in field_names)
    return sha256(repr(material).encode("utf-8")).hexdigest()


def _public_value(value: object) -> object:
    if is_dataclass(value):
        return {
            field.name: _public_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != "derived_validation_digest"
        } | {"derived_validation_digest": getattr(value, "derived_validation_digest")}
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


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "STATUS_VALUES",
    "SAFETY_FLAGS",
    "CandidateDecisionEvidenceIndependenceScoreConfig",
    "CandidateDecisionEvidenceIndependenceScoreInput",
    "CandidateDecisionEvidenceIndependenceScoreRow",
    "CandidateDecisionEvidenceIndependenceScoreReport",
    "score_candidate_decision_evidence_independence",
    "build_candidate_decision_evidence_independence_score_report",
    "candidate_decision_evidence_independence_score_payload",
    "reject_candidate_decision_evidence_independence_score_unsafe_payload",
)
