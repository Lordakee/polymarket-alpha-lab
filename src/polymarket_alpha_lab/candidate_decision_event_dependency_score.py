"""Pure report-only event dependency risk scoring."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any, Iterable


DEFAULT_CONFIG_VERSION = "candidate-decision-event-dependency-score-v0"
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT_PRECISION = 28
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
_STATUS_SORT_RANK = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}
_WEIGHT_FIELDS = (
    "dependency_count_weight",
    "unresolved_dependency_count_weight",
    "dominant_dependency_weight_weight",
    "dependency_correlation_weight",
    "upstream_uncertainty_weight",
    "evidence_support_weight",
)
_ROW_DIGEST_FIELDS = (
    "config",
    "config_version",
    "redacted_candidate_ref",
    "dependency_count",
    "unresolved_dependency_count",
    "dominant_dependency_weight",
    "dependency_correlation_score",
    "upstream_uncertainty_score",
    "evidence_support_score",
    "dependency_pressure_score",
    "status",
    "safety_flags",
    "reason_codes",
    "hard_flag_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_DIGEST_FIELDS = (
    "config",
    "config_version",
    "candidate_count",
    "pass_count",
    "watch_count",
    "block_count",
    "max_dependency_pressure_score",
    "min_dependency_pressure_score",
    "average_dependency_pressure_score",
    "report_status",
    "safety_flags",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
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
    ("position", "-", "sizing"),
    ("position", "_size"),
    ("net", "work"),
    ("data", "base"),
    ("per", "sist"),
    ("li", "ve"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_HEX_CHARS = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class CandidateDecisionEventDependencyScoreConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    max_pass_dependency_pressure_score: Decimal = Decimal("0.200000")
    max_watch_dependency_pressure_score: Decimal = Decimal("0.600000")
    dependency_count_cap: Decimal = Decimal("6")
    unresolved_dependency_count_cap: Decimal = Decimal("3")
    max_watch_unresolved_dependency_count: Decimal = Decimal("0")
    max_block_unresolved_dependency_count: Decimal = Decimal("3")
    max_watch_dominant_dependency_weight: Decimal = Decimal("0.500000")
    max_block_dominant_dependency_weight: Decimal = Decimal("0.800000")
    max_watch_dependency_correlation_score: Decimal = Decimal("0.500000")
    max_block_dependency_correlation_score: Decimal = Decimal("0.850000")
    max_watch_upstream_uncertainty_score: Decimal = Decimal("0.500000")
    max_block_upstream_uncertainty_score: Decimal = Decimal("0.850000")
    min_watch_evidence_support_score: Decimal = Decimal("0.500000")
    min_block_evidence_support_score: Decimal = Decimal("0.200000")
    dependency_count_weight: Decimal = Decimal("0.091875")
    unresolved_dependency_count_weight: Decimal = Decimal("0.270625")
    dominant_dependency_weight_weight: Decimal = Decimal("0.287500")
    dependency_correlation_weight: Decimal = Decimal("0.100000")
    upstream_uncertainty_weight: Decimal = Decimal("0.150000")
    evidence_support_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionEventDependencyScoreConfig:
            raise TypeError(
                "CandidateDecisionEventDependencyScoreConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionEventDependencyScoreConfig:
            raise ValueError(
                "config must be exactly CandidateDecisionEventDependencyScoreConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the default config version")
        for field_name in (
            "max_pass_dependency_pressure_score",
            "max_watch_dependency_pressure_score",
            "max_watch_dominant_dependency_weight",
            "max_block_dominant_dependency_weight",
            "max_watch_dependency_correlation_score",
            "max_block_dependency_correlation_score",
            "max_watch_upstream_uncertainty_score",
            "max_block_upstream_uncertainty_score",
            "min_watch_evidence_support_score",
            "min_block_evidence_support_score",
        ) + _WEIGHT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "dependency_count_cap",
            "unresolved_dependency_count_cap",
            "max_block_unresolved_dependency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_integral_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_watch_unresolved_dependency_count",
            _normalize_nonnegative_integral_decimal(
                "max_watch_unresolved_dependency_count",
                self.max_watch_unresolved_dependency_count,
            ),
        )
        if self.max_pass_dependency_pressure_score > self.max_watch_dependency_pressure_score:
            raise ValueError("pass pressure threshold must not exceed watch threshold")
        if self.max_watch_unresolved_dependency_count >= self.max_block_unresolved_dependency_count:
            raise ValueError("watch unresolved threshold must be below block threshold")
        if self.max_watch_dominant_dependency_weight > self.max_block_dominant_dependency_weight:
            raise ValueError("watch dominant threshold must not exceed block threshold")
        if (
            self.max_watch_dependency_correlation_score
            > self.max_block_dependency_correlation_score
        ):
            raise ValueError("watch correlation threshold must not exceed block threshold")
        if self.max_watch_upstream_uncertainty_score > self.max_block_upstream_uncertainty_score:
            raise ValueError("watch uncertainty threshold must not exceed block threshold")
        if self.min_block_evidence_support_score > self.min_watch_evidence_support_score:
            raise ValueError("block evidence support threshold must not exceed watch threshold")
        if _sum_decimal(getattr(self, field_name) for field_name in _WEIGHT_FIELDS) != ONE:
            raise ValueError("weight fields must sum to 1.000000")
        _require_paper_flags("event dependency config", self)
        reject_candidate_decision_event_dependency_score_unsafe_payload(
            "event dependency config",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionEventDependencyScoreInput:
    redacted_candidate_ref: str
    dependency_count: Decimal
    unresolved_dependency_count: Decimal
    dominant_dependency_weight: Decimal
    dependency_correlation_score: Decimal
    upstream_uncertainty_score: Decimal
    evidence_support_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionEventDependencyScoreInput:
            raise TypeError(
                "CandidateDecisionEventDependencyScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionEventDependencyScoreInput:
            raise ValueError(
                "score_input must be exactly CandidateDecisionEventDependencyScoreInput",
            )
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _normalize_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        for field_name in ("dependency_count", "unresolved_dependency_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        if self.unresolved_dependency_count > self.dependency_count:
            raise ValueError("unresolved_dependency_count must not exceed dependency_count")
        for field_name in (
            "dominant_dependency_weight",
            "dependency_correlation_score",
            "upstream_uncertainty_score",
            "evidence_support_score",
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
        _require_paper_flags("event dependency input", self)
        reject_candidate_decision_event_dependency_score_unsafe_payload(
            "event dependency input",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionEventDependencyScoreRow:
    config: CandidateDecisionEventDependencyScoreConfig
    config_version: str
    redacted_candidate_ref: str
    dependency_count: Decimal
    unresolved_dependency_count: Decimal
    dominant_dependency_weight: Decimal
    dependency_correlation_score: Decimal
    upstream_uncertainty_score: Decimal
    evidence_support_score: Decimal
    dependency_pressure_score: Decimal
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
        if cls is not CandidateDecisionEventDependencyScoreRow:
            raise TypeError(
                "CandidateDecisionEventDependencyScoreRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionEventDependencyScoreRow:
            raise ValueError("row must be exactly CandidateDecisionEventDependencyScoreRow")
        if type(self.config) is not CandidateDecisionEventDependencyScoreConfig:
            raise ValueError("config must be exactly CandidateDecisionEventDependencyScoreConfig")
        _require_paper_flags("event dependency config", self.config)
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _normalize_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        for field_name in ("dependency_count", "unresolved_dependency_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        if self.unresolved_dependency_count > self.dependency_count:
            raise ValueError("unresolved_dependency_count must not exceed dependency_count")
        for field_name in (
            "dominant_dependency_weight",
            "dependency_correlation_score",
            "upstream_uncertainty_score",
            "evidence_support_score",
            "dependency_pressure_score",
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
        _require_paper_flags("event dependency row", self)
        reject_candidate_decision_event_dependency_score_unsafe_payload(
            "event dependency row",
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
        return candidate_decision_event_dependency_score_payload(self)


@dataclass(frozen=True)
class CandidateDecisionEventDependencyScoreReport:
    config: CandidateDecisionEventDependencyScoreConfig
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_dependency_pressure_score: Decimal
    min_dependency_pressure_score: Decimal
    average_dependency_pressure_score: Decimal
    report_status: str
    safety_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[CandidateDecisionEventDependencyScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionEventDependencyScoreReport:
            raise TypeError(
                "CandidateDecisionEventDependencyScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionEventDependencyScoreReport:
            raise ValueError(
                "report must be exactly CandidateDecisionEventDependencyScoreReport",
            )
        if type(self.config) is not CandidateDecisionEventDependencyScoreConfig:
            raise ValueError("config must be exactly CandidateDecisionEventDependencyScoreConfig")
        _require_paper_flags("event dependency config", self.config)
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_dependency_pressure_score",
            "min_dependency_pressure_score",
            "average_dependency_pressure_score",
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
        _require_paper_flags("event dependency report", self)
        reject_candidate_decision_event_dependency_score_unsafe_payload(
            "event dependency report",
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
        return candidate_decision_event_dependency_score_payload(self)


def score_candidate_decision_event_dependency(
    score_input: CandidateDecisionEventDependencyScoreInput,
    *,
    config: CandidateDecisionEventDependencyScoreConfig | None = None,
) -> CandidateDecisionEventDependencyScoreRow:
    if type(score_input) is not CandidateDecisionEventDependencyScoreInput:
        raise ValueError(
            "score_input must be a CandidateDecisionEventDependencyScoreInput",
        )
    score_config = config or CandidateDecisionEventDependencyScoreConfig()
    if type(score_config) is not CandidateDecisionEventDependencyScoreConfig:
        raise ValueError("config must be a CandidateDecisionEventDependencyScoreConfig")
    _require_paper_flags("event dependency input", score_input)
    _require_paper_flags("event dependency config", score_config)
    reject_candidate_decision_event_dependency_score_unsafe_payload(
        "event dependency input",
        score_input,
    )
    reject_candidate_decision_event_dependency_score_unsafe_payload(
        "event dependency config",
        score_config,
    )

    dependency_pressure_score = _dependency_pressure_score(score_input, score_config)
    hard_flag_codes = _hard_flag_codes(score_input, score_config)
    status = _status(score_input, score_config, dependency_pressure_score, hard_flag_codes)
    return CandidateDecisionEventDependencyScoreRow(
        config=score_config,
        config_version=score_config.config_version,
        redacted_candidate_ref=score_input.redacted_candidate_ref,
        dependency_count=score_input.dependency_count,
        unresolved_dependency_count=score_input.unresolved_dependency_count,
        dominant_dependency_weight=score_input.dominant_dependency_weight,
        dependency_correlation_score=score_input.dependency_correlation_score,
        upstream_uncertainty_score=score_input.upstream_uncertainty_score,
        evidence_support_score=score_input.evidence_support_score,
        dependency_pressure_score=dependency_pressure_score,
        status=status,
        safety_flags=SAFETY_FLAGS,
        reason_codes=_row_reason_codes(
            score_input.reason_codes,
            score_input,
            score_config,
            dependency_pressure_score,
            status,
            hard_flag_codes,
        ),
        hard_flag_codes=hard_flag_codes,
    )


def build_candidate_decision_event_dependency_score_report(
    candidates: Iterable[CandidateDecisionEventDependencyScoreInput],
    *,
    config: CandidateDecisionEventDependencyScoreConfig | None = None,
) -> CandidateDecisionEventDependencyScoreReport:
    report_config = config or CandidateDecisionEventDependencyScoreConfig()
    if type(report_config) is not CandidateDecisionEventDependencyScoreConfig:
        raise ValueError("config must be a CandidateDecisionEventDependencyScoreConfig")
    _require_paper_flags("event dependency config", report_config)
    input_rows = _normalize_inputs(candidates)
    rows = tuple(
        sorted(
            (
                score_candidate_decision_event_dependency(
                    score_input,
                    config=report_config,
                )
                for score_input in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    pass_count = _count(sum((ONE for row in rows if row.status == "pass"), ZERO))
    watch_count = _count(sum((ONE for row in rows if row.status == "watch"), ZERO))
    block_count = _count(sum((ONE for row in rows if row.status == "block"), ZERO))
    return CandidateDecisionEventDependencyScoreReport(
        config=report_config,
        config_version=report_config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_dependency_pressure_score=_max_score(rows),
        min_dependency_pressure_score=_min_score(rows),
        average_dependency_pressure_score=_average_score(rows),
        report_status=_report_status(rows),
        safety_flags=SAFETY_FLAGS,
        reason_codes=_report_reason_codes(
            pass_count=pass_count,
            watch_count=watch_count,
            block_count=block_count,
        ),
        rows=rows,
    )


def candidate_decision_event_dependency_score_payload(
    value: CandidateDecisionEventDependencyScoreRow
    | CandidateDecisionEventDependencyScoreReport,
) -> dict[str, Any]:
    if type(value) is CandidateDecisionEventDependencyScoreRow:
        _require_paper_flags("event dependency row", value)
        if value.derived_validation_digest != _row_digest(value):
            raise ValueError("derived_validation_digest must match row fields")
    elif type(value) is CandidateDecisionEventDependencyScoreReport:
        _require_paper_flags("event dependency report", value)
        if value.derived_validation_digest != _report_digest(value):
            raise ValueError("derived_validation_digest must match report fields")
    else:
        raise ValueError("value must be an event dependency row or report")
    reject_candidate_decision_event_dependency_score_unsafe_payload(
        "event dependency payload",
        value,
    )
    result = _public_value(value)
    if type(result) is not dict:
        raise ValueError("payload must be a dict")
    return result


def reject_candidate_decision_event_dependency_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for path, item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}: {path}")


def _dependency_pressure_score(
    score_input: CandidateDecisionEventDependencyScoreInput
    | CandidateDecisionEventDependencyScoreRow,
    config: CandidateDecisionEventDependencyScoreConfig,
) -> Decimal:
    with localcontext() as context:
        _set_decimal_context(context)
        dependency_count_component = _count_component(
            score_input.dependency_count,
            config.dependency_count_cap,
        )
        unresolved_dependency_count_component = _count_component(
            score_input.unresolved_dependency_count,
            config.unresolved_dependency_count_cap,
        )
        evidence_gap_component = ONE - score_input.evidence_support_score
        score = (
            dependency_count_component * config.dependency_count_weight
            + unresolved_dependency_count_component
            * config.unresolved_dependency_count_weight
            + score_input.dominant_dependency_weight
            * config.dominant_dependency_weight_weight
            + score_input.dependency_correlation_score
            * config.dependency_correlation_weight
            + score_input.upstream_uncertainty_score
            * config.upstream_uncertainty_weight
            + evidence_gap_component * config.evidence_support_weight
        )
        return _normalize_unit_decimal("dependency_pressure_score", score)


def _count_component(value: Decimal, cap: Decimal) -> Decimal:
    if value >= cap:
        return ONE
    return _normalize_unit_decimal("count_component", value / cap)


def _hard_flag_codes(
    score_input: CandidateDecisionEventDependencyScoreInput
    | CandidateDecisionEventDependencyScoreRow,
    config: CandidateDecisionEventDependencyScoreConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if score_input.unresolved_dependency_count >= config.max_block_unresolved_dependency_count:
        codes.append("unresolved_dependency_count_block")
    if score_input.dominant_dependency_weight >= config.max_block_dominant_dependency_weight:
        codes.append("dominant_dependency_weight_block")
    if score_input.dependency_correlation_score >= config.max_block_dependency_correlation_score:
        codes.append("dependency_correlation_score_block")
    if score_input.upstream_uncertainty_score >= config.max_block_upstream_uncertainty_score:
        codes.append("upstream_uncertainty_score_block")
    if score_input.evidence_support_score <= config.min_block_evidence_support_score:
        codes.append("evidence_support_score_block")
    return tuple(codes)


def _status(
    score_input: CandidateDecisionEventDependencyScoreInput
    | CandidateDecisionEventDependencyScoreRow,
    config: CandidateDecisionEventDependencyScoreConfig,
    dependency_pressure_score: Decimal,
    hard_flag_codes: tuple[str, ...],
) -> str:
    if hard_flag_codes:
        return "block"
    if dependency_pressure_score > config.max_watch_dependency_pressure_score:
        return "block"
    if dependency_pressure_score > config.max_pass_dependency_pressure_score:
        return "watch"
    if score_input.unresolved_dependency_count > config.max_watch_unresolved_dependency_count:
        return "watch"
    if score_input.dominant_dependency_weight > config.max_watch_dominant_dependency_weight:
        return "watch"
    if score_input.dependency_correlation_score > config.max_watch_dependency_correlation_score:
        return "watch"
    if score_input.upstream_uncertainty_score > config.max_watch_upstream_uncertainty_score:
        return "watch"
    if score_input.evidence_support_score < config.min_watch_evidence_support_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    existing: tuple[str, ...],
    score_input: CandidateDecisionEventDependencyScoreInput
    | CandidateDecisionEventDependencyScoreRow,
    config: CandidateDecisionEventDependencyScoreConfig,
    dependency_pressure_score: Decimal,
    status: str,
    hard_flag_codes: tuple[str, ...],
) -> tuple[str, ...]:
    values = [
        *existing,
        "candidate_decision_event_dependency_score",
        f"event_dependency_{status}",
        _count_reason("dependency_count", score_input.dependency_count),
        _count_reason("unresolved_dependencies", score_input.unresolved_dependency_count),
        _dominant_dependency_reason(score_input, config),
        _threshold_reason(
            "dependency_correlation",
            score_input.dependency_correlation_score,
            config.max_watch_dependency_correlation_score,
            "low",
            "elevated",
        ),
        _threshold_reason(
            "upstream_uncertainty",
            score_input.upstream_uncertainty_score,
            config.max_watch_upstream_uncertainty_score,
            "low",
            "elevated",
        ),
        _support_reason(score_input.evidence_support_score, config),
    ]
    if hard_flag_codes:
        values.extend(_hard_flag_reason_codes(hard_flag_codes))
    elif score_input.unresolved_dependency_count > config.max_watch_unresolved_dependency_count:
        values.append("unresolved_dependencies_require_watch")
    elif dependency_pressure_score > config.max_watch_dependency_pressure_score:
        values.append("dependency_pressure_requires_block")
    elif dependency_pressure_score > config.max_pass_dependency_pressure_score:
        values.append("dependency_pressure_requires_watch")
    else:
        values.append("dependency_pressure_below_watch_threshold")
    return _dedupe(values)


def _count_reason(label: str, value: Decimal) -> str:
    if value == ZERO:
        return f"{label}_clear"
    return f"{label}_present"


def _dominant_dependency_reason(
    score_input: CandidateDecisionEventDependencyScoreInput
    | CandidateDecisionEventDependencyScoreRow,
    config: CandidateDecisionEventDependencyScoreConfig,
) -> str:
    if score_input.dominant_dependency_weight >= config.max_block_dominant_dependency_weight:
        return "dominant_dependency_hard_block"
    if score_input.dominant_dependency_weight > config.max_watch_dominant_dependency_weight:
        return "dominant_dependency_elevated"
    return "dominant_dependency_low"


def _threshold_reason(
    label: str,
    value: Decimal,
    watch_threshold: Decimal,
    low_suffix: str,
    high_suffix: str,
) -> str:
    if value > watch_threshold:
        return f"{label}_{high_suffix}"
    return f"{label}_{low_suffix}"


def _support_reason(
    evidence_support_score: Decimal,
    config: CandidateDecisionEventDependencyScoreConfig,
) -> str:
    if evidence_support_score <= config.min_block_evidence_support_score:
        return "evidence_support_hard_block"
    if evidence_support_score < config.min_watch_evidence_support_score:
        return "evidence_support_weak"
    return "evidence_support_strong"


def _hard_flag_reason_codes(hard_flag_codes: tuple[str, ...]) -> tuple[str, ...]:
    values: list[str] = []
    if "unresolved_dependency_count_block" in hard_flag_codes:
        values.append("unresolved_dependency_count_hard_block")
    if "dominant_dependency_weight_block" in hard_flag_codes:
        values.append("dominant_dependency_hard_block")
    if "dependency_correlation_score_block" in hard_flag_codes:
        values.append("dependency_correlation_hard_block")
    if "upstream_uncertainty_score_block" in hard_flag_codes:
        values.append("upstream_uncertainty_hard_block")
    if "evidence_support_score_block" in hard_flag_codes:
        values.append("evidence_support_hard_block")
    values.append("dependency_pressure_block_by_hard_flag")
    return tuple(values)


def _normalize_inputs(
    candidates: Iterable[CandidateDecisionEventDependencyScoreInput],
) -> tuple[CandidateDecisionEventDependencyScoreInput, ...]:
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Iterable):
        raise ValueError("candidates must be an iterable of event dependency inputs")
    rows = tuple(candidates)
    for row in rows:
        if type(row) is not CandidateDecisionEventDependencyScoreInput:
            raise ValueError("candidates must contain event dependency inputs")
        _require_paper_flags("event dependency input", row)
    return rows


def _normalize_rows(
    rows: tuple[CandidateDecisionEventDependencyScoreRow, ...],
) -> tuple[CandidateDecisionEventDependencyScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not CandidateDecisionEventDependencyScoreRow:
            raise ValueError("rows must contain event dependency rows")
        _require_paper_flags("event dependency row", row)
    return rows


def _row_sort_key(row: CandidateDecisionEventDependencyScoreRow) -> tuple[Decimal, str]:
    return (_STATUS_SORT_RANK[row.status], row.redacted_candidate_ref)


def _report_status(rows: tuple[CandidateDecisionEventDependencyScoreRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
) -> tuple[str, ...]:
    status = "block" if block_count > ZERO else "watch" if watch_count > ZERO else "pass"
    values = [f"candidate_decision_event_dependency_report_{status}"]
    if block_count > ZERO:
        values.append("event_dependency_block_candidate_present")
    if watch_count > ZERO:
        values.append("event_dependency_watch_candidate_present")
    if pass_count > ZERO:
        values.append("event_dependency_pass_candidate_present")
    return tuple(values)


def _max_score(rows: tuple[CandidateDecisionEventDependencyScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.dependency_pressure_score for row in rows)


def _min_score(rows: tuple[CandidateDecisionEventDependencyScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.dependency_pressure_score for row in rows)


def _average_score(rows: tuple[CandidateDecisionEventDependencyScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext() as context:
        _set_decimal_context(context)
        return _normalize_unit_decimal(
            "average_dependency_pressure_score",
            _sum_decimal(row.dependency_pressure_score for row in rows) / _count(len(rows)),
        )


def _validate_row(row: CandidateDecisionEventDependencyScoreRow) -> None:
    config = row.config
    expected_score = _dependency_pressure_score(row, config)
    if row.dependency_pressure_score != expected_score:
        raise ValueError("dependency_pressure_score must match dependency inputs")
    expected_hard_flag_codes = _hard_flag_codes(row, config)
    if row.hard_flag_codes != expected_hard_flag_codes:
        raise ValueError("hard_flag_codes must match dependency inputs")
    expected_status = _status(row, config, row.dependency_pressure_score, row.hard_flag_codes)
    if row.status != expected_status:
        raise ValueError("status must match dependency inputs")
    expected_generated_codes = _row_reason_codes(
        (),
        row,
        config,
        row.dependency_pressure_score,
        row.status,
        row.hard_flag_codes,
    )
    if row.reason_codes[-len(expected_generated_codes) :] != expected_generated_codes:
        raise ValueError("reason_codes must match dependency inputs")
    if row.safety_flags != SAFETY_FLAGS:
        raise ValueError("safety_flags must match event dependency contract")


def _validate_report(report: CandidateDecisionEventDependencyScoreReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and redacted_candidate_ref")
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(sum((ONE for row in report.rows if row.status == "pass"), ZERO)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(
        sum((ONE for row in report.rows if row.status == "watch"), ZERO),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(
        sum((ONE for row in report.rows if row.status == "block"), ZERO),
    ):
        raise ValueError("block_count must match rows")
    if report.max_dependency_pressure_score != _max_score(report.rows):
        raise ValueError("max_dependency_pressure_score must match rows")
    if report.min_dependency_pressure_score != _min_score(report.rows):
        raise ValueError("min_dependency_pressure_score must match rows")
    if report.average_dependency_pressure_score != _average_score(report.rows):
        raise ValueError("average_dependency_pressure_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    expected_reason_codes = _report_reason_codes(
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.safety_flags != SAFETY_FLAGS:
        raise ValueError("safety_flags must match event dependency contract")


def _count(value: int | Decimal) -> Decimal:
    if type(value) is Decimal:
        count_value = value
    else:
        count_value = Decimal(str(value))
    return count_value.quantize(COUNT_QUANTUM)


def _normalize_unit_decimal(field_name: str, value: Decimal) -> Decimal:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    with localcontext() as context:
        _set_decimal_context(context)
        return value.quantize(QUANTUM)


def _normalize_nonnegative_integral_decimal(field_name: str, value: Decimal) -> Decimal:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_integral_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_integral_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _normalize_redacted_candidate_ref(field_name: str, value: str) -> str:
    _require_canonical_string(field_name, value)
    if not value.startswith(REDACTED_CANDIDATE_REF_PREFIX):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _normalize_safety_flags(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("safety_flags must be a tuple")
    if value != SAFETY_FLAGS:
        raise ValueError("safety_flags must match event dependency contract")
    for item in value:
        _require_canonical_string("safety_flags", item)
    return value


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not values:
        raise ValueError(f"{field_name} must contain at least one value")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for value in values:
        _require_canonical_string(field_name, value)
    return values


def _require_choice(field_name: str, value: str, choices: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_canonical_digest(value: str) -> None:
    _require_canonical_string("derived_validation_digest", value)
    if len(value) != 64 or any(character not in _HEX_CHARS for character in value):
        raise ValueError("derived_validation_digest must be a sha256 hex digest")


def _row_digest(row: CandidateDecisionEventDependencyScoreRow) -> str:
    return _digest_for_fields(row, _ROW_DIGEST_FIELDS)


def _report_digest(report: CandidateDecisionEventDependencyScoreReport) -> str:
    return _digest_for_fields(report, _REPORT_DIGEST_FIELDS)


def _digest_for_fields(value: object, field_names: tuple[str, ...]) -> str:
    digest_payload = tuple((field_name, _public_value(getattr(value, field_name))) for field_name in field_names)
    return sha256(repr(digest_payload).encode("utf-8")).hexdigest()


def _public_value(value: Any) -> Any:
    if type(value) is Decimal:
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _public_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_public_value(item) for item in value]
    if isinstance(value, list):
        return [_public_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _public_value(item) for key, item in value.items()}
    return value


def _iter_public_strings(value: object, path: str = "$") -> Iterable[tuple[str, str]]:
    if type(value) is str:
        yield path, value
        return
    if type(value) is Decimal or type(value) is bool or value is None:
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            field_path = f"{path}.{field.name}"
            yield field_path, field.name
            yield from _iter_public_strings(getattr(value, field.name), field_path)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            item_path = f"{path}.{key_text}"
            yield item_path, key_text
            yield from _iter_public_strings(item, item_path)
        return
    if isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            yield from _iter_public_strings(item, f"{path}[{index}]")


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext() as context:
        _set_decimal_context(context)
        total = ZERO
        for value in values:
            _require_decimal("decimal_sum", value)
            total += value
        return total.quantize(QUANTUM)


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _set_decimal_context(context: Any) -> None:
    context.prec = DECIMAL_CONTEXT_PRECISION
    context.rounding = ROUND_HALF_EVEN


__all__ = (
    "STATUS_VALUES",
    "SAFETY_FLAGS",
    "CandidateDecisionEventDependencyScoreConfig",
    "CandidateDecisionEventDependencyScoreInput",
    "CandidateDecisionEventDependencyScoreRow",
    "CandidateDecisionEventDependencyScoreReport",
    "score_candidate_decision_event_dependency",
    "build_candidate_decision_event_dependency_score_report",
    "candidate_decision_event_dependency_score_payload",
    "reject_candidate_decision_event_dependency_score_unsafe_payload",
)
