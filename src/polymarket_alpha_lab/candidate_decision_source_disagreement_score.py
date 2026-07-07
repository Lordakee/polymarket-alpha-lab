"""Pure report-only source disagreement risk scoring for candidate decisions."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_CANDIDATE_DECISION_SOURCE_DISAGREEMENT_SCORE_CONFIG_VERSION = (
    "candidate-decision-source-disagreement-score-v0"
)
DISAGREEMENT_STATUSES = ("pass", "watch", "block")
SAFETY_FLAGS = (
    "paper_only",
    "report_only",
    "readonly",
    "local_public_facts_only",
    "redacted_candidate_refs_only",
    "no_execution_surface",
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT_PRECISION = 64

REDACTED_CANDIDATE_REF_PREFIX = "redacted-candidate-"
STATUS_SORT_RANK = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}

RAW_REFERENCE_TERMS = (
    "candidate_id",
    "candidate-id",
    "candidate_slug",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "condition_id",
    "question",
    "source_ref",
    "source-ref",
    "source_refs",
    "source_url",
    "source-url",
    "source_uri",
    "source_text",
    "source_excerpt",
    "source_title",
    "raw_text",
    "url",
    "http://",
    "https://",
    "www.",
    "://",
)
UNSAFE_PUBLIC_TERMS = (
    "api_key",
    "auth",
    "bearer",
    "buy",
    "connection_string",
    "credential",
    "database",
    "dsn",
    "jwt",
    "oauth",
    "order",
    "password",
    "position sizing",
    "position-sizing",
    "position_sizing",
    "private_key",
    "recommendation",
    "secret",
    "sell",
    "session",
    "table",
    "token",
    "trade",
    "trading",
    "wallet",
)
PUBLIC_STATUS_ALIASES = ("ready", "blocked", "matched", "supported")

ROW_DIGEST_FIELDS = (
    "redacted_candidate_ref",
    "source_count",
    "disagreeing_source_count",
    "disagreement_ratio",
    "disagreement_severity_score",
    "source_quality_score",
    "independent_source_ratio",
    "recency_score",
    "disagreement_ratio_component",
    "disagreement_severity_component",
    "source_quality_gap_component",
    "independent_source_gap_component",
    "recency_gap_component",
    "disagreement_risk_score",
    "disagreement_status",
    "hard_flag_codes",
    "safety_flags",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_DIGEST_FIELDS = (
    "config_version",
    "candidate_count",
    "pass_count",
    "watch_count",
    "block_count",
    "max_disagreement_risk_score",
    "min_disagreement_risk_score",
    "average_disagreement_risk_score",
    "report_status",
    "safety_flags",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class CandidateDecisionSourceDisagreementScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_SOURCE_DISAGREEMENT_SCORE_CONFIG_VERSION
    )
    max_pass_disagreement_risk_score: Decimal = Decimal("0.300000")
    max_watch_disagreement_risk_score: Decimal = Decimal("0.650000")
    min_pass_source_count: Decimal = Decimal("3")
    min_watch_source_count: Decimal = Decimal("1")
    max_pass_disagreement_ratio: Decimal = Decimal("0.100000")
    max_watch_disagreement_ratio: Decimal = Decimal("0.300000")
    max_pass_disagreement_severity_score: Decimal = Decimal("0.250000")
    max_watch_disagreement_severity_score: Decimal = Decimal("0.600000")
    min_pass_source_quality_score: Decimal = Decimal("0.700000")
    min_watch_source_quality_score: Decimal = Decimal("0.400000")
    min_pass_independent_source_ratio: Decimal = Decimal("0.670000")
    min_watch_independent_source_ratio: Decimal = Decimal("0.340000")
    min_pass_recency_score: Decimal = Decimal("0.700000")
    min_watch_recency_score: Decimal = Decimal("0.400000")
    disagreement_ratio_weight: Decimal = Decimal("0.300000")
    disagreement_severity_weight: Decimal = Decimal("0.300000")
    source_quality_gap_weight: Decimal = Decimal("0.150000")
    independent_source_gap_weight: Decimal = Decimal("0.150000")
    recency_gap_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceDisagreementScoreConfig:
            raise TypeError(
                "CandidateDecisionSourceDisagreementScoreConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, CandidateDecisionSourceDisagreementScoreConfig)
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_SOURCE_DISAGREEMENT_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in ("min_pass_source_count", "min_watch_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "max_pass_disagreement_risk_score",
            "max_watch_disagreement_risk_score",
            "max_pass_disagreement_ratio",
            "max_watch_disagreement_ratio",
            "max_pass_disagreement_severity_score",
            "max_watch_disagreement_severity_score",
            "min_pass_source_quality_score",
            "min_watch_source_quality_score",
            "min_pass_independent_source_ratio",
            "min_watch_independent_source_ratio",
            "min_pass_recency_score",
            "min_watch_recency_score",
            "disagreement_ratio_weight",
            "disagreement_severity_weight",
            "source_quality_gap_weight",
            "independent_source_gap_weight",
            "recency_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_phase_flags("config", self)
        reject_candidate_decision_source_disagreement_score_unsafe_payload(
            "source disagreement config",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionSourceDisagreementScoreInput:
    redacted_candidate_ref: str
    source_count: Decimal
    disagreeing_source_count: Decimal
    disagreement_severity_score: Decimal
    source_quality_score: Decimal
    independent_source_ratio: Decimal
    recency_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceDisagreementScoreInput:
            raise TypeError(
                "CandidateDecisionSourceDisagreementScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("score input", self, CandidateDecisionSourceDisagreementScoreInput)
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        for field_name in ("source_count", "disagreeing_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "disagreement_severity_score",
            "source_quality_score",
            "independent_source_ratio",
            "recency_score",
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
        _validate_input(self)
        _require_phase_flags("score input", self)
        reject_candidate_decision_source_disagreement_score_unsafe_payload(
            "source disagreement input",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionSourceDisagreementScoreRow:
    redacted_candidate_ref: str
    source_count: Decimal
    disagreeing_source_count: Decimal
    disagreement_ratio: Decimal
    disagreement_severity_score: Decimal
    source_quality_score: Decimal
    independent_source_ratio: Decimal
    recency_score: Decimal
    disagreement_ratio_component: Decimal
    disagreement_severity_component: Decimal
    source_quality_gap_component: Decimal
    independent_source_gap_component: Decimal
    recency_gap_component: Decimal
    disagreement_risk_score: Decimal
    disagreement_status: str
    hard_flag_codes: tuple[str, ...]
    safety_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceDisagreementScoreRow:
            raise TypeError(
                "CandidateDecisionSourceDisagreementScoreRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, CandidateDecisionSourceDisagreementScoreRow)
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        for field_name in ("source_count", "disagreeing_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "disagreement_ratio",
            "disagreement_severity_score",
            "source_quality_score",
            "independent_source_ratio",
            "recency_score",
            "disagreement_ratio_component",
            "disagreement_severity_component",
            "source_quality_gap_component",
            "independent_source_gap_component",
            "recency_gap_component",
            "disagreement_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("disagreement_status", self.disagreement_status, DISAGREEMENT_STATUSES)
        object.__setattr__(
            self,
            "hard_flag_codes",
            _normalize_reason_codes(
                "hard_flag_codes",
                self.hard_flag_codes,
                allow_empty=True,
            ),
        )
        object.__setattr__(self, "safety_flags", _normalize_safety_flags(self.safety_flags))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        _require_phase_flags("row", self)
        reject_candidate_decision_source_disagreement_score_unsafe_payload(
            "source disagreement row",
            self,
        )
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match row fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_source_disagreement_score_payload(self)


@dataclass(frozen=True)
class CandidateDecisionSourceDisagreementScoreReport:
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_disagreement_risk_score: Decimal
    min_disagreement_risk_score: Decimal
    average_disagreement_risk_score: Decimal
    report_status: str
    safety_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[CandidateDecisionSourceDisagreementScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceDisagreementScoreReport:
            raise TypeError(
                "CandidateDecisionSourceDisagreementScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, CandidateDecisionSourceDisagreementScoreReport)
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_SOURCE_DISAGREEMENT_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "max_disagreement_risk_score",
            "min_disagreement_risk_score",
            "average_disagreement_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("report_status", self.report_status, DISAGREEMENT_STATUSES)
        object.__setattr__(self, "safety_flags", _normalize_safety_flags(self.safety_flags))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_phase_flags("report", self)
        reject_candidate_decision_source_disagreement_score_unsafe_payload(
            "source disagreement report",
            self,
        )
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_source_disagreement_score_payload(self)


def score_candidate_decision_source_disagreement(
    score_input: CandidateDecisionSourceDisagreementScoreInput,
    *,
    config: CandidateDecisionSourceDisagreementScoreConfig | None = None,
) -> CandidateDecisionSourceDisagreementScoreRow:
    if type(score_input) is not CandidateDecisionSourceDisagreementScoreInput:
        raise ValueError(
            "score_input must be a CandidateDecisionSourceDisagreementScoreInput",
        )
    score_config = config or CandidateDecisionSourceDisagreementScoreConfig()
    if type(score_config) is not CandidateDecisionSourceDisagreementScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionSourceDisagreementScoreConfig",
        )
    _require_phase_flags("score input", score_input)
    _require_phase_flags("config", score_config)
    reject_candidate_decision_source_disagreement_score_unsafe_payload(
        "source disagreement input",
        score_input,
    )
    reject_candidate_decision_source_disagreement_score_unsafe_payload(
        "source disagreement config",
        score_config,
    )
    return CandidateDecisionSourceDisagreementScoreRow(**_row_values(score_input, score_config))


def build_candidate_decision_source_disagreement_score_report(
    candidates: Iterable[CandidateDecisionSourceDisagreementScoreInput],
    *,
    config: CandidateDecisionSourceDisagreementScoreConfig | None = None,
) -> CandidateDecisionSourceDisagreementScoreReport:
    report_config = config or CandidateDecisionSourceDisagreementScoreConfig()
    if type(report_config) is not CandidateDecisionSourceDisagreementScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionSourceDisagreementScoreConfig",
        )
    _require_phase_flags("config", report_config)
    input_rows = _normalize_inputs(candidates)
    rows = tuple(
        sorted(
            (
                score_candidate_decision_source_disagreement(
                    item,
                    config=report_config,
                )
                for item in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    report_status = _report_status(tuple(row.disagreement_status for row in rows))
    return CandidateDecisionSourceDisagreementScoreReport(
        config_version=report_config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.disagreement_status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.disagreement_status == "watch")),
        block_count=_count(sum(1 for row in rows if row.disagreement_status == "block")),
        max_disagreement_risk_score=_max_disagreement_risk_score(rows),
        min_disagreement_risk_score=_min_disagreement_risk_score(rows),
        average_disagreement_risk_score=_average_disagreement_risk_score(rows),
        report_status=report_status,
        safety_flags=SAFETY_FLAGS,
        reason_codes=_report_reason_codes(rows, report_status),
        rows=rows,
    )


def candidate_decision_source_disagreement_score_payload(
    value: CandidateDecisionSourceDisagreementScoreRow
    | CandidateDecisionSourceDisagreementScoreReport,
) -> dict[str, Any]:
    if type(value) is CandidateDecisionSourceDisagreementScoreRow:
        _require_phase_flags("row", value)
        _validate_row(value)
        if value.derived_validation_digest != _row_digest(value):
            raise ValueError("derived_validation_digest must match row fields")
    elif type(value) is CandidateDecisionSourceDisagreementScoreReport:
        _require_phase_flags("report", value)
        _validate_report(value)
        if value.derived_validation_digest != _report_digest(value):
            raise ValueError("derived_validation_digest must match report fields")
    else:
        raise ValueError("value must be a source disagreement row or report")
    reject_candidate_decision_source_disagreement_score_unsafe_payload(
        "source disagreement payload",
        value,
    )
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_source_disagreement_score_public_payload(payload)
    return payload


def validate_candidate_decision_source_disagreement_score_public_payload(
    payload: object,
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_numbers(payload)
    for path, item in _iter_public_entries(payload):
        lowered = item.lower()
        if any(term in lowered for term in PUBLIC_STATUS_ALIASES):
            raise ValueError(f"unsafe public payload status in source disagreement: {path}")
    reject_candidate_decision_source_disagreement_score_unsafe_payload(
        "source disagreement public payload",
        payload,
    )


def reject_candidate_decision_source_disagreement_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for path, item in _iter_public_entries(payload):
        lowered = item.lower()
        if any(term in lowered for term in RAW_REFERENCE_TERMS):
            raise ValueError(f"raw reference public payload entry in {label}: {path}")
        if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}: {path}")


def _row_values(
    score_input: CandidateDecisionSourceDisagreementScoreInput,
    config: CandidateDecisionSourceDisagreementScoreConfig,
) -> dict[str, object]:
    disagreement_ratio = _disagreement_ratio(
        score_input.disagreeing_source_count,
        score_input.source_count,
    )
    ratio_component = _upper_risk_component(
        disagreement_ratio,
        config.max_pass_disagreement_ratio,
        config.max_watch_disagreement_ratio,
    )
    severity_component = _upper_risk_component(
        score_input.disagreement_severity_score,
        config.max_pass_disagreement_severity_score,
        config.max_watch_disagreement_severity_score,
    )
    quality_component = _lower_gap_component(
        score_input.source_quality_score,
        config.min_watch_source_quality_score,
        config.min_pass_source_quality_score,
    )
    independent_component = _lower_gap_component(
        score_input.independent_source_ratio,
        config.min_watch_independent_source_ratio,
        config.min_pass_independent_source_ratio,
    )
    recency_component = _lower_gap_component(
        score_input.recency_score,
        config.min_watch_recency_score,
        config.min_pass_recency_score,
    )
    risk_score = _risk_score(
        ratio_component,
        severity_component,
        quality_component,
        independent_component,
        recency_component,
        config,
    )
    hard_flags = _hard_flag_codes(
        score_input,
        disagreement_ratio,
        risk_score,
        config,
    )
    disagreement_status = _disagreement_status(
        score_input,
        disagreement_ratio,
        risk_score,
        hard_flags,
        config,
    )
    return {
        "redacted_candidate_ref": score_input.redacted_candidate_ref,
        "source_count": score_input.source_count,
        "disagreeing_source_count": score_input.disagreeing_source_count,
        "disagreement_ratio": disagreement_ratio,
        "disagreement_severity_score": score_input.disagreement_severity_score,
        "source_quality_score": score_input.source_quality_score,
        "independent_source_ratio": score_input.independent_source_ratio,
        "recency_score": score_input.recency_score,
        "disagreement_ratio_component": ratio_component,
        "disagreement_severity_component": severity_component,
        "source_quality_gap_component": quality_component,
        "independent_source_gap_component": independent_component,
        "recency_gap_component": recency_component,
        "disagreement_risk_score": risk_score,
        "disagreement_status": disagreement_status,
        "hard_flag_codes": hard_flags,
        "safety_flags": SAFETY_FLAGS,
        "reason_codes": _reason_codes(
            score_input.reason_codes,
            score_input,
            disagreement_ratio,
            risk_score,
            disagreement_status,
            config,
        ),
    }


def _disagreement_ratio(disagreeing_source_count: Decimal, source_count: Decimal) -> Decimal:
    if source_count <= ZERO:
        return ONE
    return _safe_unit_ratio(disagreeing_source_count, source_count)


def _upper_risk_component(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> Decimal:
    if value <= pass_threshold:
        return ZERO
    if value >= watch_threshold:
        return ONE
    numerator = _subtract_nonnegative("upper_risk_component_numerator", value, pass_threshold)
    denominator = _subtract_nonnegative(
        "upper_risk_component_denominator",
        watch_threshold,
        pass_threshold,
    )
    return _safe_unit_ratio(numerator, denominator)


def _lower_gap_component(
    value: Decimal,
    watch_threshold: Decimal,
    pass_threshold: Decimal,
) -> Decimal:
    if value >= pass_threshold:
        return ZERO
    if value <= watch_threshold:
        return ONE
    numerator = _subtract_nonnegative("lower_gap_component_numerator", pass_threshold, value)
    denominator = _subtract_nonnegative(
        "lower_gap_component_denominator",
        pass_threshold,
        watch_threshold,
    )
    return _safe_unit_ratio(numerator, denominator)


def _risk_score(
    ratio_component: Decimal,
    severity_component: Decimal,
    quality_component: Decimal,
    independent_component: Decimal,
    recency_component: Decimal,
    config: CandidateDecisionSourceDisagreementScoreConfig,
) -> Decimal:
    with localcontext() as context:
        _set_decimal_context(context)
        return _normalize_unit_decimal(
            "disagreement_risk_score",
            (
                ratio_component * config.disagreement_ratio_weight
                + severity_component * config.disagreement_severity_weight
                + quality_component * config.source_quality_gap_weight
                + independent_component * config.independent_source_gap_weight
                + recency_component * config.recency_gap_weight
            ),
        )


def _hard_flag_codes(
    score_input: CandidateDecisionSourceDisagreementScoreInput
    | CandidateDecisionSourceDisagreementScoreRow,
    disagreement_ratio: Decimal,
    risk_score: Decimal,
    config: CandidateDecisionSourceDisagreementScoreConfig
    | CandidateDecisionSourceDisagreementScoreReport,
) -> tuple[str, ...]:
    codes: list[str] = []
    if score_input.source_count < config.min_watch_source_count:
        codes.append("source_count_block")
    if disagreement_ratio > config.max_watch_disagreement_ratio:
        codes.append("disagreement_ratio_block")
    if score_input.disagreement_severity_score > config.max_watch_disagreement_severity_score:
        codes.append("disagreement_severity_block")
    if score_input.source_quality_score < config.min_watch_source_quality_score:
        codes.append("source_quality_block")
    if score_input.independent_source_ratio < config.min_watch_independent_source_ratio:
        codes.append("independent_source_ratio_block")
    if score_input.recency_score < config.min_watch_recency_score:
        codes.append("recency_score_block")
    if risk_score > config.max_watch_disagreement_risk_score:
        codes.append("disagreement_risk_score_block")
    return tuple(codes)


def _disagreement_status(
    score_input: CandidateDecisionSourceDisagreementScoreInput
    | CandidateDecisionSourceDisagreementScoreRow,
    disagreement_ratio: Decimal,
    risk_score: Decimal,
    hard_flags: tuple[str, ...],
    config: CandidateDecisionSourceDisagreementScoreConfig
    | CandidateDecisionSourceDisagreementScoreReport,
) -> str:
    if hard_flags:
        return "block"
    if (
        score_input.source_count < config.min_pass_source_count
        or disagreement_ratio > config.max_pass_disagreement_ratio
        or score_input.disagreement_severity_score > config.max_pass_disagreement_severity_score
        or score_input.source_quality_score < config.min_pass_source_quality_score
        or score_input.independent_source_ratio < config.min_pass_independent_source_ratio
        or score_input.recency_score < config.min_pass_recency_score
        or risk_score > config.max_pass_disagreement_risk_score
    ):
        return "watch"
    return "pass"


def _reason_codes(
    existing_reason_codes: tuple[str, ...],
    score_input: CandidateDecisionSourceDisagreementScoreInput
    | CandidateDecisionSourceDisagreementScoreRow,
    disagreement_ratio: Decimal,
    risk_score: Decimal,
    status: str,
    config: CandidateDecisionSourceDisagreementScoreConfig
    | CandidateDecisionSourceDisagreementScoreReport,
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "reason_codes",
        (
            *existing_reason_codes,
            f"source_disagreement_risk_{status}",
            _lower_reason(
                "source_count",
                score_input.source_count,
                config.min_watch_source_count,
                config.min_pass_source_count,
            ),
            _upper_reason(
                "disagreement_ratio",
                disagreement_ratio,
                config.max_pass_disagreement_ratio,
                config.max_watch_disagreement_ratio,
            ),
            _upper_reason(
                "disagreement_severity",
                score_input.disagreement_severity_score,
                config.max_pass_disagreement_severity_score,
                config.max_watch_disagreement_severity_score,
            ),
            _lower_reason(
                "source_quality",
                score_input.source_quality_score,
                config.min_watch_source_quality_score,
                config.min_pass_source_quality_score,
            ),
            _lower_reason(
                "independent_source_ratio",
                score_input.independent_source_ratio,
                config.min_watch_independent_source_ratio,
                config.min_pass_independent_source_ratio,
            ),
            _lower_reason(
                "recency_score",
                score_input.recency_score,
                config.min_watch_recency_score,
                config.min_pass_recency_score,
            ),
            _upper_reason(
                "disagreement_risk_score",
                risk_score,
                config.max_pass_disagreement_risk_score,
                config.max_watch_disagreement_risk_score,
            ),
        ),
        allow_empty=False,
    )


def _upper_reason(name: str, value: Decimal, pass_threshold: Decimal, watch_threshold: Decimal) -> str:
    if value <= pass_threshold:
        return f"{name}_pass"
    if value <= watch_threshold:
        return f"{name}_watch"
    return f"{name}_block"


def _lower_reason(name: str, value: Decimal, watch_threshold: Decimal, pass_threshold: Decimal) -> str:
    if value >= pass_threshold:
        return f"{name}_pass"
    if value >= watch_threshold:
        return f"{name}_watch"
    return f"{name}_block"


def _report_status(statuses: tuple[str, ...]) -> str:
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[CandidateDecisionSourceDisagreementScoreRow, ...],
    report_status: str,
) -> tuple[str, ...]:
    codes = [f"source_disagreement_score_report_{report_status}"]
    if not rows:
        codes.append("source_disagreement_score_report_empty")
    if any(row.disagreement_status == "pass" for row in rows):
        codes.append("source_disagreement_score_report_has_pass")
    if any(row.disagreement_status == "watch" for row in rows):
        codes.append("source_disagreement_score_report_has_watch")
    if any(row.disagreement_status == "block" for row in rows):
        codes.append("source_disagreement_score_report_has_block")
    if any(row.hard_flag_codes for row in rows):
        codes.append("source_disagreement_score_report_hard_flags")
    return _normalize_reason_codes("reason_codes", tuple(codes), allow_empty=False)


def _normalize_inputs(
    candidates: Iterable[CandidateDecisionSourceDisagreementScoreInput],
) -> tuple[CandidateDecisionSourceDisagreementScoreInput, ...]:
    if type(candidates) is str or type(candidates) is bytes:
        raise ValueError("candidates must be an iterable of source disagreement inputs")
    try:
        items = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable of source disagreement inputs") from exc
    seen_refs: set[str] = set()
    for item in items:
        if type(item) is not CandidateDecisionSourceDisagreementScoreInput:
            raise ValueError("candidates must contain source disagreement inputs")
        _require_phase_flags("score input", item)
        reject_candidate_decision_source_disagreement_score_unsafe_payload(
            "source disagreement input",
            item,
        )
        if item.redacted_candidate_ref in seen_refs:
            raise ValueError("duplicate redacted_candidate_ref")
        seen_refs.add(item.redacted_candidate_ref)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[CandidateDecisionSourceDisagreementScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_refs: set[str] = set()
    for row in rows:
        if type(row) is not CandidateDecisionSourceDisagreementScoreRow:
            raise ValueError("rows must contain source disagreement rows")
        if row.redacted_candidate_ref in seen_refs:
            raise ValueError("duplicate redacted_candidate_ref")
        seen_refs.add(row.redacted_candidate_ref)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted")
    return rows


def _row_sort_key(row: CandidateDecisionSourceDisagreementScoreRow) -> tuple[Decimal | str, ...]:
    return (
        STATUS_SORT_RANK[row.disagreement_status],
        -row.disagreement_risk_score,
        row.redacted_candidate_ref,
    )


def _validate_config(
    config: CandidateDecisionSourceDisagreementScoreConfig
    | CandidateDecisionSourceDisagreementScoreReport,
) -> None:
    if config.max_pass_disagreement_risk_score > config.max_watch_disagreement_risk_score:
        raise ValueError("max_pass_disagreement_risk_score must not exceed watch threshold")
    if config.min_watch_source_count > config.min_pass_source_count:
        raise ValueError("min_watch_source_count must not exceed pass threshold")
    if config.max_pass_disagreement_ratio > config.max_watch_disagreement_ratio:
        raise ValueError("max_pass_disagreement_ratio must not exceed watch threshold")
    if (
        config.max_pass_disagreement_severity_score
        > config.max_watch_disagreement_severity_score
    ):
        raise ValueError(
            "max_pass_disagreement_severity_score must not exceed watch threshold",
        )
    for watch_field, pass_field in (
        ("min_watch_source_quality_score", "min_pass_source_quality_score"),
        ("min_watch_independent_source_ratio", "min_pass_independent_source_ratio"),
        ("min_watch_recency_score", "min_pass_recency_score"),
    ):
        if getattr(config, watch_field) > getattr(config, pass_field):
            raise ValueError(f"{watch_field} must not exceed pass threshold")
    if _weight_total(config) != ONE:
        raise ValueError("score weights must sum to 1")


def _validate_input(score_input: CandidateDecisionSourceDisagreementScoreInput) -> None:
    if score_input.disagreeing_source_count > score_input.source_count:
        raise ValueError("disagreeing_source_count must not exceed source_count")


def _validate_row(row: CandidateDecisionSourceDisagreementScoreRow) -> None:
    _validate_input(row)
    if row.safety_flags != SAFETY_FLAGS:
        raise ValueError("safety_flags must match paper boundary")
    if f"source_disagreement_risk_{row.disagreement_status}" not in row.reason_codes:
        raise ValueError("reason_codes must include disagreement status")
    if row.disagreement_status != "block" and row.hard_flag_codes:
        raise ValueError("hard_flag_codes require block status")


def _validate_report(report: CandidateDecisionSourceDisagreementScoreReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.disagreement_status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.disagreement_status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.disagreement_status == "block")):
        raise ValueError("block_count must match rows")
    if report.max_disagreement_risk_score != _max_disagreement_risk_score(rows):
        raise ValueError("max_disagreement_risk_score must match rows")
    if report.min_disagreement_risk_score != _min_disagreement_risk_score(rows):
        raise ValueError("min_disagreement_risk_score must match rows")
    if report.average_disagreement_risk_score != _average_disagreement_risk_score(rows):
        raise ValueError("average_disagreement_risk_score must match rows")
    expected_status = _report_status(tuple(row.disagreement_status for row in rows))
    if report.report_status != expected_status:
        raise ValueError("report_status must match rows")
    if report.safety_flags != SAFETY_FLAGS:
        raise ValueError("safety_flags must match paper boundary")
    if report.reason_codes != _report_reason_codes(rows, report.report_status):
        raise ValueError("reason_codes must match report rows")


def _count(value: int) -> Decimal:
    return Decimal(str(value)).quantize(COUNT_QUANTUM)


def _max_disagreement_risk_score(
    rows: tuple[CandidateDecisionSourceDisagreementScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_unit_decimal(
        "max_disagreement_risk_score",
        max(row.disagreement_risk_score for row in rows),
    )


def _min_disagreement_risk_score(
    rows: tuple[CandidateDecisionSourceDisagreementScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_unit_decimal(
        "min_disagreement_risk_score",
        min(row.disagreement_risk_score for row in rows),
    )


def _average_disagreement_risk_score(
    rows: tuple[CandidateDecisionSourceDisagreementScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext() as context:
        _set_decimal_context(context)
        total = sum((row.disagreement_risk_score for row in rows), ZERO)
        return _normalize_unit_decimal(
            "average_disagreement_risk_score",
            total / _count(len(rows)),
        )


def _weight_total(
    config: CandidateDecisionSourceDisagreementScoreConfig
    | CandidateDecisionSourceDisagreementScoreReport,
) -> Decimal:
    with localcontext() as context:
        _set_decimal_context(context)
        return _normalize_unit_decimal(
            "score_weights_total",
            (
                config.disagreement_ratio_weight
                + config.disagreement_severity_weight
                + config.source_quality_gap_weight
                + config.independent_source_gap_weight
                + config.recency_gap_weight
            ),
        )


def _row_digest(row: CandidateDecisionSourceDisagreementScoreRow) -> str:
    return _digest_from_fields(row, ROW_DIGEST_FIELDS)


def _report_digest(report: CandidateDecisionSourceDisagreementScoreReport) -> str:
    return _digest_from_fields(report, REPORT_DIGEST_FIELDS)


def _digest_from_fields(value: object, field_names: tuple[str, ...]) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(value, field_name))}"
        for field_name in field_names
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if type(value) is Decimal:
        return str(value)
    if type(value) is str:
        return value
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is tuple:
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if is_dataclass(value) and not isinstance(value, type):
        return "{" + ",".join(
            f"{field.name}={_digest_value(getattr(value, field.name))}"
            for field in fields(value)
            if field.name != "derived_validation_digest"
        ) + "}"
    raise ValueError("digest value must be public scalar data")


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) is str or type(value) is bool or value is None:
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    raise ValueError("payload contains unsupported public value")


def _iter_public_entries(value: object, path: str = "payload") -> Iterable[tuple[str, str]]:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            yield from _iter_public_entries(getattr(value, field.name), f"{path}.{field.name}")
        return
    if type(value) is dict:
        for key, item in value.items():
            yield from _iter_public_entries(str(key), f"{path}.{key}.key")
            yield from _iter_public_entries(item, f"{path}.{key}")
        return
    if type(value) is tuple or type(value) is list:
        for index, item in enumerate(value):
            yield from _iter_public_entries(item, f"{path}[{index}]")
        return
    if type(value) is str:
        yield path, value


def _reject_public_numbers(value: object) -> None:
    if type(value) is Decimal or type(value) is float:
        raise ValueError("public payload must not contain numeric runtime values")
    if type(value) is int and type(value) is not bool:
        raise ValueError("public payload must not contain numeric runtime values")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numbers(item)
    if type(value) is list:
        for item in value:
            _reject_public_numbers(item)


def _normalize_safety_flags(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("safety_flags must be a tuple")
    if value != SAFETY_FLAGS:
        raise ValueError("safety_flags must match paper boundary")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    codes: list[str] = []
    for item in value:
        codes.append(_require_canonical_string(field_name, item))
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    return tuple(codes)


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    with localcontext() as context:
        _set_decimal_context(context)
        integral = normalized.quantize(COUNT_QUANTUM, rounding=ROUND_HALF_EVEN)
    if normalized != integral:
        raise ValueError(f"{field_name} must be integral")
    return integral


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, Decimal) and type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext() as context:
        _set_decimal_context(context, value)
        return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _safe_unit_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ONE
    with localcontext() as context:
        _set_decimal_context(context)
        return _normalize_unit_decimal("ratio", numerator / denominator)


def _subtract_nonnegative(field_name: str, minuend: Decimal, subtrahend: Decimal) -> Decimal:
    with localcontext() as context:
        _set_decimal_context(context)
        return _normalize_nonnegative_decimal(field_name, minuend - subtrahend)


def _set_decimal_context(context: Any, value: Decimal | None = None) -> None:
    context.prec = DECIMAL_CONTEXT_PRECISION
    if value is not None:
        context.prec = max(context.prec, len(value.as_tuple().digits))
    context.rounding = ROUND_HALF_EVEN


def _require_redacted_candidate_ref(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    if not text.startswith(REDACTED_CANDIDATE_REF_PREFIX):
        raise ValueError(f"{field_name} must be redacted")
    return text


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")
    return value


def _require_choice(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64 or set(value) - set("0123456789abcdef"):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_phase_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label} {flag_name} must be True")
