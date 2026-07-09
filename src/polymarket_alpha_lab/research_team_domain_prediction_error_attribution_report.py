"""Report-only domain team prediction error attribution reducer."""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_PREDICTION_ERROR_ATTRIBUTION_CONFIG_VERSION = (
    "research-team-domain-prediction-error-attribution-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_PREFIX = "domain_prediction_error_attribution_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
MATERIAL_PREDICTION_ERROR_REASON = f"{REASON_PREFIX}material_prediction_error"
EVIDENCE_GAP_REASON = f"{REASON_PREFIX}evidence_gap"
STALE_MEMORY_REASON = f"{REASON_PREFIX}stale_memory"
SOURCE_CONFLICT_HANDLING_REASON = f"{REASON_PREFIX}source_conflict_handling"
COST_ASSUMPTION_REASON = f"{REASON_PREFIX}cost_assumption"
RESOLUTION_AMBIGUITY_REASON = f"{REASON_PREFIX}resolution_ambiguity"
REVIEW_LATENCY_REASON = f"{REASON_PREFIX}review_latency"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    MATERIAL_PREDICTION_ERROR_REASON,
    EVIDENCE_GAP_REASON,
    STALE_MEMORY_REASON,
    SOURCE_CONFLICT_HANDLING_REASON,
    COST_ASSUMPTION_REASON,
    RESOLUTION_AMBIGUITY_REASON,
    REVIEW_LATENCY_REASON,
    PASS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_PREDICTION_ERROR_REASON,
    EVIDENCE_GAP_REASON,
    STALE_MEMORY_REASON,
    SOURCE_CONFLICT_HANDLING_REASON,
    COST_ASSUMPTION_REASON,
    RESOLUTION_AMBIGUITY_REASON,
    REVIEW_LATENCY_REASON,
    PASS_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_domain_prediction_error_attribution",
    STATUS_WATCH: "watch_report_only_domain_prediction_error_attribution",
    STATUS_BLOCK: "block_report_only_domain_prediction_error_attribution",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

_PUBLIC_REFERENCE_PREFIXES = ("public-", "public_")
_UNSAFE_KEY_FRAGMENTS = (
    "candidate_id",
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "url",
    "dsn",
    "table_name",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
)
_UNSAFE_VALUE_FRAGMENTS = (
    "candidate",
    "market_id",
    "market_slug",
    "question",
    "source_url",
    "dsn",
    "table_name",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "hidden",
    "private_key",
    "api_key",
    "secret",
)

_REPORT_PUBLIC_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "attribution_status",
        "next_step",
        "prediction_count",
        "pass_count",
        "watch_count",
        "block_count",
        "material_prediction_error_count",
        "evidence_gap_count",
        "stale_memory_count",
        "source_conflict_handling_count",
        "cost_assumption_count",
        "resolution_ambiguity_count",
        "review_latency_count",
        "average_prediction_error",
        "max_prediction_error",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PUBLIC_FIELDS = frozenset(
    (
        "review_key",
        "domain_team",
        "prediction_family",
        "prediction_made_at",
        "resolved_at",
        "review_started_at",
        "review_completed_at",
        "prediction_age_seconds",
        "review_latency_seconds",
        "predicted_probability",
        "resolved_probability",
        "prediction_error",
        "evidence_gap_score",
        "stale_memory_score",
        "source_conflict_handling_score",
        "cost_assumption_score",
        "resolution_ambiguity_score",
        "review_latency_score",
        "attribution_status",
        "redacted_attribution_reference",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REASON_CODE_COUNT_PUBLIC_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "prediction_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REPORT_COUNT_FIELDS = (
    "prediction_count",
    "pass_count",
    "watch_count",
    "block_count",
    "material_prediction_error_count",
    "evidence_gap_count",
    "stale_memory_count",
    "source_conflict_handling_count",
    "cost_assumption_count",
    "resolution_ambiguity_count",
    "review_latency_count",
)
_ROW_RATIO_FIELDS = (
    "predicted_probability",
    "resolved_probability",
    "prediction_error",
    "evidence_gap_score",
    "stale_memory_score",
    "source_conflict_handling_score",
    "cost_assumption_score",
    "resolution_ambiguity_score",
    "review_latency_score",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_PREDICTION_ERROR_ATTRIBUTION_CONFIG_VERSION",
    "ResearchTeamDomainPredictionErrorAttributionConfig",
    "ResearchTeamDomainPredictionErrorAttributionInputRow",
    "ResearchTeamDomainPredictionErrorAttributionRow",
    "ResearchTeamDomainPredictionErrorAttributionReasonCodeCount",
    "ResearchTeamDomainPredictionErrorAttributionReport",
    "build_research_team_domain_prediction_error_attribution_report",
    "research_team_domain_prediction_error_attribution_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamDomainPredictionErrorAttributionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_PREDICTION_ERROR_ATTRIBUTION_CONFIG_VERSION
    )
    material_error_watch_threshold: Decimal = Decimal("0.100000")
    material_error_block_threshold: Decimal = Decimal("0.350000")
    component_watch_threshold: Decimal = Decimal("0.200000")
    component_block_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainPredictionErrorAttributionConfig:
            raise TypeError(
                "ResearchTeamDomainPredictionErrorAttributionConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainPredictionErrorAttributionConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchTeamDomainPredictionErrorAttributionConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "material_error_watch_threshold",
            "material_error_block_threshold",
            "component_watch_threshold",
            "component_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.material_error_watch_threshold > self.material_error_block_threshold:
            raise ValueError(
                "material_error_block_threshold must be at least "
                "material_error_watch_threshold",
            )
        if self.component_watch_threshold > self.component_block_threshold:
            raise ValueError(
                "component_block_threshold must be at least component_watch_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainPredictionErrorAttributionInputRow:
    review_key: str
    domain_team: str
    prediction_family: str
    attribution_reference: str
    prediction_made_at: datetime
    resolved_at: datetime
    review_started_at: datetime
    review_completed_at: datetime
    predicted_probability: Decimal
    resolved_probability: Decimal
    evidence_gap_score: Decimal
    stale_memory_score: Decimal
    source_conflict_handling_score: Decimal
    cost_assumption_score: Decimal
    resolution_ambiguity_score: Decimal
    review_latency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainPredictionErrorAttributionInputRow:
            raise TypeError(
                "ResearchTeamDomainPredictionErrorAttributionInputRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainPredictionErrorAttributionInputRow:
            raise ValueError(
                "input row must be exactly "
                "ResearchTeamDomainPredictionErrorAttributionInputRow",
            )
        for field_name in ("review_key", "domain_team", "prediction_family"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("attribution_reference", self.attribution_reference)
        for field_name in (
            "prediction_made_at",
            "resolved_at",
            "review_started_at",
            "review_completed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        if self.resolved_at < self.prediction_made_at:
            raise ValueError("resolved_at must be on or after prediction_made_at")
        if self.review_started_at < self.prediction_made_at:
            raise ValueError("review_started_at must be on or after prediction_made_at")
        if self.review_completed_at < self.review_started_at:
            raise ValueError("review_completed_at must be on or after review_started_at")
        for field_name in (
            "predicted_probability",
            "resolved_probability",
            "evidence_gap_score",
            "stale_memory_score",
            "source_conflict_handling_score",
            "cost_assumption_score",
            "resolution_ambiguity_score",
            "review_latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchTeamDomainPredictionErrorAttributionRow:
    review_key: str
    domain_team: str
    prediction_family: str
    prediction_made_at: datetime
    resolved_at: datetime
    review_started_at: datetime
    review_completed_at: datetime
    prediction_age_seconds: Decimal
    review_latency_seconds: Decimal
    predicted_probability: Decimal
    resolved_probability: Decimal
    prediction_error: Decimal
    evidence_gap_score: Decimal
    stale_memory_score: Decimal
    source_conflict_handling_score: Decimal
    cost_assumption_score: Decimal
    resolution_ambiguity_score: Decimal
    review_latency_score: Decimal
    attribution_status: str
    redacted_attribution_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchTeamDomainPredictionErrorAttributionConfig | None
    ] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainPredictionErrorAttributionRow:
            raise TypeError(
                "ResearchTeamDomainPredictionErrorAttributionRow does not "
                "support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchTeamDomainPredictionErrorAttributionConfig | None,
    ) -> None:
        if type(self) is not ResearchTeamDomainPredictionErrorAttributionRow:
            raise ValueError(
                "row must be exactly ResearchTeamDomainPredictionErrorAttributionRow",
            )
        for field_name in ("review_key", "domain_team", "prediction_family"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "prediction_made_at",
            "resolved_at",
            "review_started_at",
            "review_completed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "prediction_age_seconds",
            _require_nonnegative_decimal(
                "prediction_age_seconds",
                self.prediction_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "review_latency_seconds",
            _require_nonnegative_decimal(
                "review_latency_seconds",
                self.review_latency_seconds,
            ),
        )
        for field_name in (
            "predicted_probability",
            "resolved_probability",
            "prediction_error",
            "evidence_gap_score",
            "stale_memory_score",
            "source_conflict_handling_score",
            "cost_assumption_score",
            "resolution_ambiguity_score",
            "review_latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("attribution_status", self.attribution_status)
        object.__setattr__(
            self,
            "redacted_attribution_reference",
            _require_redacted_reference(
                "redacted_attribution_reference",
                self.redacted_attribution_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainPredictionErrorAttributionReasonCodeCount:
    reason_code: str
    count: Decimal
    prediction_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainPredictionErrorAttributionReasonCodeCount:
            raise TypeError(
                "ResearchTeamDomainPredictionErrorAttributionReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainPredictionErrorAttributionReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchTeamDomainPredictionErrorAttributionReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "prediction_ratio",
            _require_ratio_decimal("prediction_ratio", self.prediction_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchTeamDomainPredictionErrorAttributionReport:
    generated_at: datetime
    config_version: str
    attribution_status: str
    next_step: str
    prediction_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    material_prediction_error_count: Decimal
    evidence_gap_count: Decimal
    stale_memory_count: Decimal
    source_conflict_handling_count: Decimal
    cost_assumption_count: Decimal
    resolution_ambiguity_count: Decimal
    review_latency_count: Decimal
    average_prediction_error: Decimal
    max_prediction_error: Decimal
    rows: tuple[ResearchTeamDomainPredictionErrorAttributionRow, ...]
    reason_code_counts: tuple[
        ResearchTeamDomainPredictionErrorAttributionReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainPredictionErrorAttributionReport:
            raise TypeError(
                "ResearchTeamDomainPredictionErrorAttributionReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainPredictionErrorAttributionReport:
            raise ValueError(
                "report must be exactly "
                "ResearchTeamDomainPredictionErrorAttributionReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("attribution_status", self.attribution_status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "prediction_count",
            "pass_count",
            "watch_count",
            "block_count",
            "material_prediction_error_count",
            "evidence_gap_count",
            "stale_memory_count",
            "source_conflict_handling_count",
            "cost_assumption_count",
            "resolution_ambiguity_count",
            "review_latency_count",
            "average_prediction_error",
            "max_prediction_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _set_or_validate_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_domain_prediction_error_attribution_report_payload(self)


def build_research_team_domain_prediction_error_attribution_report(
    input_rows: list[ResearchTeamDomainPredictionErrorAttributionInputRow]
    | tuple[ResearchTeamDomainPredictionErrorAttributionInputRow, ...],
    *,
    config: ResearchTeamDomainPredictionErrorAttributionConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamDomainPredictionErrorAttributionReport:
    cfg = config or ResearchTeamDomainPredictionErrorAttributionConfig()
    if type(cfg) is not ResearchTeamDomainPredictionErrorAttributionConfig:
        raise ValueError(
            "config must be a ResearchTeamDomainPredictionErrorAttributionConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(_build_row(row, config=cfg) for row in rows)
    ranked_rows = _ranked_rows(built_rows)
    prediction_count = _count(len(ranked_rows))
    pass_count = _count(
        sum(1 for row in ranked_rows if row.attribution_status == STATUS_PASS),
    )
    watch_count = _count(
        sum(1 for row in ranked_rows if row.attribution_status == STATUS_WATCH),
    )
    block_count = _count(
        sum(1 for row in ranked_rows if row.attribution_status == STATUS_BLOCK),
    )
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            ResearchTeamDomainPredictionErrorAttributionReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                prediction_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    attribution_status = _report_status(
        has_inputs=bool(ranked_rows),
        block_count=block_count,
        watch_count=watch_count,
    )
    return ResearchTeamDomainPredictionErrorAttributionReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        attribution_status=attribution_status,
        next_step=NEXT_STEPS[attribution_status],
        prediction_count=prediction_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        material_prediction_error_count=_count(
            sum(
                1
                for row in ranked_rows
                if MATERIAL_PREDICTION_ERROR_REASON in row.reason_codes
            ),
        ),
        evidence_gap_count=_count(
            sum(1 for row in ranked_rows if EVIDENCE_GAP_REASON in row.reason_codes),
        ),
        stale_memory_count=_count(
            sum(1 for row in ranked_rows if STALE_MEMORY_REASON in row.reason_codes),
        ),
        source_conflict_handling_count=_count(
            sum(
                1
                for row in ranked_rows
                if SOURCE_CONFLICT_HANDLING_REASON in row.reason_codes
            ),
        ),
        cost_assumption_count=_count(
            sum(1 for row in ranked_rows if COST_ASSUMPTION_REASON in row.reason_codes),
        ),
        resolution_ambiguity_count=_count(
            sum(
                1
                for row in ranked_rows
                if RESOLUTION_AMBIGUITY_REASON in row.reason_codes
            ),
        ),
        review_latency_count=_count(
            sum(1 for row in ranked_rows if REVIEW_LATENCY_REASON in row.reason_codes),
        ),
        average_prediction_error=_ratio(
            _sum_decimal(row.prediction_error for row in ranked_rows),
            prediction_count,
        ),
        max_prediction_error=max(
            (row.prediction_error for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_team_domain_prediction_error_attribution_report_payload(
    report: ResearchTeamDomainPredictionErrorAttributionReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainPredictionErrorAttributionReport:
        _require_hard_flags("report", report)
        _set_or_validate_digest(report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamDomainPredictionErrorAttributionReport "
            "or payload dict",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _validate_public_payload_schema(payload)
    supplied_digest = payload.get("derived_validation_digest")
    if type(supplied_digest) is not str:
        raise ValueError("derived_validation_digest is required")
    _require_sha256("derived_validation_digest", supplied_digest)
    if supplied_digest != _derived_validation_digest_from_payload(payload):
        raise ValueError("derived_validation_digest does not match report payload")
    _validate_public_payload_consistency(payload)
    return payload


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


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_exact_public_schema("payload", payload, _REPORT_PUBLIC_FIELDS)
    _require_public_datetime_string("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    _require_status("attribution_status", payload["attribution_status"])
    _require_public_string("next_step", payload["next_step"])
    if payload["next_step"] != NEXT_STEPS[payload["attribution_status"]]:
        raise ValueError("next_step must match attribution_status")
    for field_name in _REPORT_COUNT_FIELDS:
        _require_public_whole_decimal_string(field_name, payload[field_name])
    for field_name in ("average_prediction_error", "max_prediction_error"):
        _require_public_ratio_decimal_string(field_name, payload[field_name])
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for index, row in enumerate(rows):
        _validate_public_row_payload(f"rows[{index}]", row)
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for index, reason_code_count in enumerate(reason_code_counts):
        _validate_public_reason_code_count_payload(
            f"reason_code_counts[{index}]",
            reason_code_count,
        )
    reason_codes = payload["reason_codes"]
    if type(reason_codes) is not list:
        raise ValueError("reason_codes must be a list")
    _normalize_report_reason_codes(tuple(reason_codes))
    _require_sha256(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    _require_hard_flags("payload", _DictFlags(payload))


def _validate_public_payload_consistency(payload: dict[str, Any]) -> None:
    generated_at = datetime.fromisoformat(payload["generated_at"])
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    seen_keys: set[tuple[str, str, str]] = set()
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError(f"rows[{index}] must be a JSON object")
        _validate_public_row_consistency(
            f"rows[{index}]",
            row,
            generated_at=generated_at,
        )
        row_key = (
            row["review_key"],
            row["domain_team"],
            row["prediction_family"],
        )
        if row_key in seen_keys:
            raise ValueError("rows must not contain duplicate review keys")
        seen_keys.add(row_key)
    if rows != sorted(rows, key=_public_row_sort_key):
        raise ValueError("rows must be sorted deterministically")

    prediction_count = _public_decimal(payload["prediction_count"])
    if prediction_count != _count(len(rows)):
        raise ValueError("prediction_count must match rows")
    for field_name, status in (
        ("pass_count", STATUS_PASS),
        ("watch_count", STATUS_WATCH),
        ("block_count", STATUS_BLOCK),
    ):
        if _public_decimal(payload[field_name]) != _count(
            sum(1 for row in rows if row["attribution_status"] == status),
        ):
            raise ValueError(f"{field_name} must match rows")
    for field_name, reason_code in (
        ("material_prediction_error_count", MATERIAL_PREDICTION_ERROR_REASON),
        ("evidence_gap_count", EVIDENCE_GAP_REASON),
        ("stale_memory_count", STALE_MEMORY_REASON),
        ("source_conflict_handling_count", SOURCE_CONFLICT_HANDLING_REASON),
        ("cost_assumption_count", COST_ASSUMPTION_REASON),
        ("resolution_ambiguity_count", RESOLUTION_AMBIGUITY_REASON),
        ("review_latency_count", REVIEW_LATENCY_REASON),
    ):
        if _public_decimal(payload[field_name]) != _count(
            sum(1 for row in rows if reason_code in row["reason_codes"]),
        ):
            raise ValueError(f"{field_name} must match rows")
    prediction_errors = tuple(
        _public_decimal(row["prediction_error"]) for row in rows
    )
    if _public_decimal(payload["average_prediction_error"]) != _ratio(
        _sum_decimal(prediction_errors),
        prediction_count,
    ):
        raise ValueError("average_prediction_error must match rows")
    if _public_decimal(payload["max_prediction_error"]) != max(
        prediction_errors,
        default=ZERO,
    ):
        raise ValueError("max_prediction_error must match rows")

    expected_reason_code_counts = _public_reason_code_counts(rows)
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    if len(reason_code_counts) != len(expected_reason_code_counts):
        raise ValueError("reason_code_counts must match rows")
    for actual, expected in zip(
        reason_code_counts,
        expected_reason_code_counts,
        strict=True,
    ):
        if type(actual) is not dict:
            raise ValueError("reason_code_counts must contain JSON objects")
        expected_code, expected_count, expected_ratio = expected
        if (
            actual["reason_code"] != expected_code
            or _public_decimal(actual["count"]) != expected_count
            or _public_decimal(actual["prediction_ratio"]) != expected_ratio
        ):
            raise ValueError("reason_code_counts must match rows")
    expected_reason_codes = [item[0] for item in expected_reason_code_counts]
    if payload["reason_codes"] != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(rows),
        block_count=_public_decimal(payload["block_count"]),
        watch_count=_public_decimal(payload["watch_count"]),
    )
    if payload["attribution_status"] != expected_status:
        raise ValueError("attribution_status must match rows")


def _validate_public_row_consistency(
    label: str,
    row: dict[str, Any],
    *,
    generated_at: datetime,
) -> None:
    prediction_made_at = datetime.fromisoformat(row["prediction_made_at"])
    resolved_at = datetime.fromisoformat(row["resolved_at"])
    review_started_at = datetime.fromisoformat(row["review_started_at"])
    review_completed_at = datetime.fromisoformat(row["review_completed_at"])
    if resolved_at < prediction_made_at:
        raise ValueError(f"{label}.resolved_at must follow prediction_made_at")
    if review_started_at < prediction_made_at:
        raise ValueError(f"{label}.review_started_at must follow prediction_made_at")
    if review_completed_at < review_started_at:
        raise ValueError(f"{label}.review_completed_at must follow review_started_at")
    if resolved_at > generated_at or review_completed_at > generated_at:
        raise ValueError(f"{label} timestamps must be on or before generated_at")
    expected_error = _abs_decimal(
        _quantize(
            _public_decimal(row["resolved_probability"])
            - _public_decimal(row["predicted_probability"]),
        ),
    )
    if _public_decimal(row["prediction_error"]) != expected_error:
        raise ValueError(f"{label}.prediction_error must match probability inputs")
    if _public_decimal(row["prediction_age_seconds"]) != _datetime_delta_seconds(
        resolved_at,
        prediction_made_at,
    ):
        raise ValueError(f"{label}.prediction_age_seconds must match timestamps")
    if _public_decimal(row["review_latency_seconds"]) != _datetime_delta_seconds(
        review_completed_at,
        review_started_at,
    ):
        raise ValueError(f"{label}.review_latency_seconds must match timestamps")
    reason_codes = tuple(row["reason_codes"])
    if reason_codes == (PASS_REASON,):
        if row["attribution_status"] != STATUS_PASS:
            raise ValueError(f"{label}.attribution_status must match reason_codes")
    elif row["attribution_status"] == STATUS_PASS:
        raise ValueError(f"{label}.attribution_status must match reason_codes")


def _public_row_sort_key(row: dict[str, Any]) -> tuple[object, ...]:
    return (
        _status_rank(row["attribution_status"]),
        -_public_decimal(row["prediction_error"]),
        row["prediction_family"],
        row["domain_team"],
        row["review_key"],
    )


def _public_reason_code_counts(
    rows: list[dict[str, Any]],
) -> tuple[tuple[str, Decimal, Decimal], ...]:
    if not rows:
        return ((NO_INPUTS_REASON, ONE, ONE),)
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row["reason_codes"]:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        (
            reason_code,
            _count(counts[reason_code]),
            _ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _public_decimal(value: Any) -> Decimal:
    return Decimal(value)


def _validate_public_row_payload(label: str, value: object) -> None:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    _require_exact_public_schema(label, value, _ROW_PUBLIC_FIELDS)
    for field_name in ("review_key", "domain_team", "prediction_family"):
        _require_public_string(f"{label}.{field_name}", value[field_name])
    for field_name in (
        "prediction_made_at",
        "resolved_at",
        "review_started_at",
        "review_completed_at",
    ):
        _require_public_datetime_string(
            f"{label}.{field_name}",
            value[field_name],
        )
    for field_name in ("prediction_age_seconds", "review_latency_seconds"):
        _require_public_nonnegative_decimal_string(
            f"{label}.{field_name}",
            value[field_name],
        )
    for field_name in _ROW_RATIO_FIELDS:
        _require_public_ratio_decimal_string(
            f"{label}.{field_name}",
            value[field_name],
        )
    _require_status(f"{label}.attribution_status", value["attribution_status"])
    _require_redacted_reference(
        f"{label}.redacted_attribution_reference",
        value["redacted_attribution_reference"],
    )
    reason_codes = value["reason_codes"]
    if type(reason_codes) is not list:
        raise ValueError(f"{label}.reason_codes must be a list")
    _normalize_row_reason_codes(tuple(reason_codes))
    _require_hard_flags(label, _DictFlags(value))


def _validate_public_reason_code_count_payload(label: str, value: object) -> None:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    _require_exact_public_schema(
        label,
        value,
        _REASON_CODE_COUNT_PUBLIC_FIELDS,
    )
    _require_reason_code(
        f"{label}.reason_code",
        value["reason_code"],
        REASON_CODE_SEQUENCE,
    )
    _require_public_whole_decimal_string(
        f"{label}.count",
        value["count"],
    )
    _require_public_ratio_decimal_string(
        f"{label}.prediction_ratio",
        value["prediction_ratio"],
    )
    _require_hard_flags(label, _DictFlags(value))


def _require_exact_public_schema(
    label: str,
    value: dict[str, Any],
    expected_fields: frozenset[str],
) -> None:
    if frozenset(value) != expected_fields:
        raise ValueError(f"{label} must match the exact schema")


def _require_public_datetime_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime string",
        ) from exc
    if (
        parsed.tzinfo is None
        or parsed.utcoffset() is None
        or parsed.astimezone(UTC).isoformat() != value
    ):
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return parsed


def _require_public_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        decimal_value = Decimal(value)
        normalized = _quantize(decimal_value)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    if not decimal_value.is_finite() or format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _require_public_whole_decimal_string(
    field_name: str,
    value: object,
) -> Decimal:
    decimal_value = _require_public_decimal_string(field_name, value)
    if decimal_value < ZERO or decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal string")
    return decimal_value


def _require_public_nonnegative_decimal_string(
    field_name: str,
    value: object,
) -> Decimal:
    decimal_value = _require_public_decimal_string(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be a nonnegative Decimal string")
    return decimal_value


def _require_public_ratio_decimal_string(
    field_name: str,
    value: object,
) -> Decimal:
    decimal_value = _require_public_decimal_string(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be a Decimal string from 0 through 1")
    return decimal_value


def _build_row(
    row: ResearchTeamDomainPredictionErrorAttributionInputRow,
    *,
    config: ResearchTeamDomainPredictionErrorAttributionConfig,
) -> ResearchTeamDomainPredictionErrorAttributionRow:
    prediction_error = _abs_decimal(
        _quantize(row.resolved_probability - row.predicted_probability),
    )
    reason_codes = _row_reason_codes(
        prediction_error=prediction_error,
        evidence_gap_score=row.evidence_gap_score,
        stale_memory_score=row.stale_memory_score,
        source_conflict_handling_score=row.source_conflict_handling_score,
        cost_assumption_score=row.cost_assumption_score,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        review_latency_score=row.review_latency_score,
        config=config,
    )
    attribution_status = _row_status(
        reason_codes=reason_codes,
        prediction_error=prediction_error,
        evidence_gap_score=row.evidence_gap_score,
        stale_memory_score=row.stale_memory_score,
        source_conflict_handling_score=row.source_conflict_handling_score,
        cost_assumption_score=row.cost_assumption_score,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        review_latency_score=row.review_latency_score,
        config=config,
    )
    return ResearchTeamDomainPredictionErrorAttributionRow(
        review_key=row.review_key,
        domain_team=row.domain_team,
        prediction_family=row.prediction_family,
        prediction_made_at=row.prediction_made_at,
        resolved_at=row.resolved_at,
        review_started_at=row.review_started_at,
        review_completed_at=row.review_completed_at,
        prediction_age_seconds=_datetime_delta_seconds(
            row.resolved_at,
            row.prediction_made_at,
        ),
        review_latency_seconds=_datetime_delta_seconds(
            row.review_completed_at,
            row.review_started_at,
        ),
        predicted_probability=row.predicted_probability,
        resolved_probability=row.resolved_probability,
        prediction_error=prediction_error,
        evidence_gap_score=row.evidence_gap_score,
        stale_memory_score=row.stale_memory_score,
        source_conflict_handling_score=row.source_conflict_handling_score,
        cost_assumption_score=row.cost_assumption_score,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        review_latency_score=row.review_latency_score,
        attribution_status=attribution_status,
        redacted_attribution_reference=_redacted_reference(row.attribution_reference),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _normalize_input_rows(
    rows: list[ResearchTeamDomainPredictionErrorAttributionInputRow]
    | tuple[ResearchTeamDomainPredictionErrorAttributionInputRow, ...],
    generated_at: datetime,
) -> tuple[ResearchTeamDomainPredictionErrorAttributionInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchTeamDomainPredictionErrorAttributionInputRow:
            raise ValueError(
                "input rows must contain "
                "ResearchTeamDomainPredictionErrorAttributionInputRow",
            )
        _require_hard_flags("input row", row)
        if row.resolved_at > generated_at:
            raise ValueError("resolved_at must be on or before generated_at")
        if row.review_completed_at > generated_at:
            raise ValueError("review_completed_at must be on or before generated_at")
        key = (row.review_key, row.domain_team, row.prediction_family)
        if key in seen:
            raise ValueError("input rows must not contain duplicate review keys")
        seen.add(key)
    return normalized


def _row_reason_codes(
    *,
    prediction_error: Decimal,
    evidence_gap_score: Decimal,
    stale_memory_score: Decimal,
    source_conflict_handling_score: Decimal,
    cost_assumption_score: Decimal,
    resolution_ambiguity_score: Decimal,
    review_latency_score: Decimal,
    config: ResearchTeamDomainPredictionErrorAttributionConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if prediction_error >= config.material_error_watch_threshold:
        reason_codes.append(MATERIAL_PREDICTION_ERROR_REASON)
    if evidence_gap_score >= config.component_watch_threshold:
        reason_codes.append(EVIDENCE_GAP_REASON)
    if stale_memory_score >= config.component_watch_threshold:
        reason_codes.append(STALE_MEMORY_REASON)
    if source_conflict_handling_score >= config.component_watch_threshold:
        reason_codes.append(SOURCE_CONFLICT_HANDLING_REASON)
    if cost_assumption_score >= config.component_watch_threshold:
        reason_codes.append(COST_ASSUMPTION_REASON)
    if resolution_ambiguity_score >= config.component_watch_threshold:
        reason_codes.append(RESOLUTION_AMBIGUITY_REASON)
    if review_latency_score >= config.component_watch_threshold:
        reason_codes.append(REVIEW_LATENCY_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(
    *,
    reason_codes: tuple[str, ...],
    prediction_error: Decimal,
    evidence_gap_score: Decimal,
    stale_memory_score: Decimal,
    source_conflict_handling_score: Decimal,
    cost_assumption_score: Decimal,
    resolution_ambiguity_score: Decimal,
    review_latency_score: Decimal,
    config: ResearchTeamDomainPredictionErrorAttributionConfig,
) -> str:
    if prediction_error >= config.material_error_block_threshold:
        return STATUS_BLOCK
    if any(
        score >= config.component_block_threshold
        for score in (
            evidence_gap_score,
            stale_memory_score,
            source_conflict_handling_score,
            cost_assumption_score,
            resolution_ambiguity_score,
            review_latency_score,
        )
    ):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    block_count: Decimal,
    watch_count: Decimal,
) -> str:
    if not has_inputs or block_count > ZERO:
        return STATUS_BLOCK
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _ranked_rows(
    rows: tuple[ResearchTeamDomainPredictionErrorAttributionRow, ...],
) -> tuple[ResearchTeamDomainPredictionErrorAttributionRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.attribution_status),
                -row.prediction_error,
                row.prediction_family,
                row.domain_team,
                row.review_key,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainPredictionErrorAttributionRow, ...],
) -> tuple[ResearchTeamDomainPredictionErrorAttributionReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchTeamDomainPredictionErrorAttributionReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            prediction_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _validate_row(
    row: ResearchTeamDomainPredictionErrorAttributionRow,
    *,
    config: ResearchTeamDomainPredictionErrorAttributionConfig | None,
) -> None:
    if config is None:
        config = ResearchTeamDomainPredictionErrorAttributionConfig()
    if type(config) is not ResearchTeamDomainPredictionErrorAttributionConfig:
        raise ValueError(
            "validation_config must be a "
            "ResearchTeamDomainPredictionErrorAttributionConfig",
        )
    if row.resolved_at < row.prediction_made_at:
        raise ValueError("resolved_at must be on or after prediction_made_at")
    if row.review_started_at < row.prediction_made_at:
        raise ValueError("review_started_at must be on or after prediction_made_at")
    if row.review_completed_at < row.review_started_at:
        raise ValueError("review_completed_at must be on or after review_started_at")
    expected_error = _abs_decimal(
        _quantize(row.resolved_probability - row.predicted_probability),
    )
    if row.prediction_error != expected_error:
        raise ValueError("prediction_error must match probability inputs")
    expected_prediction_age = _datetime_delta_seconds(
        row.resolved_at,
        row.prediction_made_at,
    )
    if row.prediction_age_seconds != expected_prediction_age:
        raise ValueError("prediction_age_seconds must match row timestamps")
    expected_review_latency = _datetime_delta_seconds(
        row.review_completed_at,
        row.review_started_at,
    )
    if row.review_latency_seconds != expected_review_latency:
        raise ValueError("review_latency_seconds must match row timestamps")
    expected_reason_codes = _row_reason_codes(
        prediction_error=row.prediction_error,
        evidence_gap_score=row.evidence_gap_score,
        stale_memory_score=row.stale_memory_score,
        source_conflict_handling_score=row.source_conflict_handling_score,
        cost_assumption_score=row.cost_assumption_score,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        review_latency_score=row.review_latency_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    expected_status = _row_status(
        reason_codes=row.reason_codes,
        prediction_error=row.prediction_error,
        evidence_gap_score=row.evidence_gap_score,
        stale_memory_score=row.stale_memory_score,
        source_conflict_handling_score=row.source_conflict_handling_score,
        cost_assumption_score=row.cost_assumption_score,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        review_latency_score=row.review_latency_score,
        config=config,
    )
    if row.attribution_status != expected_status:
        raise ValueError("attribution_status must match reason_codes")
    if not _is_redacted_reference(row.redacted_attribution_reference):
        raise ValueError("redacted_attribution_reference must be redacted or public")


def _validate_report(report: ResearchTeamDomainPredictionErrorAttributionReport) -> None:
    if report.next_step != NEXT_STEPS[report.attribution_status]:
        raise ValueError("next_step must match attribution_status")
    if report.rows != _ranked_rows(report.rows):
        raise ValueError("rows must be sorted deterministically")
    if report.prediction_count != _count(len(report.rows)):
        raise ValueError("prediction_count must match rows")
    expected_pass = _count(
        sum(1 for row in report.rows if row.attribution_status == STATUS_PASS),
    )
    if report.pass_count != expected_pass:
        raise ValueError("pass_count must match rows")
    expected_watch = _count(
        sum(1 for row in report.rows if row.attribution_status == STATUS_WATCH),
    )
    if report.watch_count != expected_watch:
        raise ValueError("watch_count must match rows")
    expected_block = _count(
        sum(1 for row in report.rows if row.attribution_status == STATUS_BLOCK),
    )
    if report.block_count != expected_block:
        raise ValueError("block_count must match rows")
    if report.material_prediction_error_count != _count(
        sum(
            1
            for row in report.rows
            if MATERIAL_PREDICTION_ERROR_REASON in row.reason_codes
        ),
    ):
        raise ValueError("material_prediction_error_count must match rows")
    if report.evidence_gap_count != _count(
        sum(1 for row in report.rows if EVIDENCE_GAP_REASON in row.reason_codes),
    ):
        raise ValueError("evidence_gap_count must match rows")
    if report.stale_memory_count != _count(
        sum(1 for row in report.rows if STALE_MEMORY_REASON in row.reason_codes),
    ):
        raise ValueError("stale_memory_count must match rows")
    if report.source_conflict_handling_count != _count(
        sum(
            1
            for row in report.rows
            if SOURCE_CONFLICT_HANDLING_REASON in row.reason_codes
        ),
    ):
        raise ValueError("source_conflict_handling_count must match rows")
    if report.cost_assumption_count != _count(
        sum(1 for row in report.rows if COST_ASSUMPTION_REASON in row.reason_codes),
    ):
        raise ValueError("cost_assumption_count must match rows")
    if report.resolution_ambiguity_count != _count(
        sum(
            1
            for row in report.rows
            if RESOLUTION_AMBIGUITY_REASON in row.reason_codes
        ),
    ):
        raise ValueError("resolution_ambiguity_count must match rows")
    if report.review_latency_count != _count(
        sum(1 for row in report.rows if REVIEW_LATENCY_REASON in row.reason_codes),
    ):
        raise ValueError("review_latency_count must match rows")
    if report.average_prediction_error != _ratio(
        _sum_decimal(row.prediction_error for row in report.rows),
        report.prediction_count,
    ):
        raise ValueError("average_prediction_error must match rows")
    expected_max_error = max(
        (row.prediction_error for row in report.rows),
        default=ZERO,
    )
    if report.max_prediction_error != expected_max_error:
        raise ValueError("max_prediction_error must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchTeamDomainPredictionErrorAttributionReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                prediction_ratio=ONE,
            ),
        )
        expected_codes = (NO_INPUTS_REASON,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        block_count=report.block_count,
        watch_count=report.watch_count,
    )
    if report.attribution_status != expected_status:
        raise ValueError("attribution_status must match rows")


def _normalize_rows(
    value: object,
) -> tuple[ResearchTeamDomainPredictionErrorAttributionRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchTeamDomainPredictionErrorAttributionRow:
            raise ValueError(
                "rows must contain ResearchTeamDomainPredictionErrorAttributionRow",
            )
        _require_hard_flags("row", row)
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamDomainPredictionErrorAttributionReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in value:
        if type(row) is not ResearchTeamDomainPredictionErrorAttributionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamDomainPredictionErrorAttributionReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
    return value


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    if PASS_REASON in value and len(value) != 1:
        raise ValueError("reason_codes cannot mix pass with attribution reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    return normalized


def _set_or_validate_digest(
    report: ResearchTeamDomainPredictionErrorAttributionReport,
) -> None:
    current_digest = report.derived_validation_digest
    if current_digest == "":
        object.__setattr__(
            report,
            "derived_validation_digest",
            _derived_validation_digest_from_report(report),
        )
        return
    _require_sha256("derived_validation_digest", current_digest)
    if current_digest != _derived_validation_digest_from_report(report):
        raise ValueError("derived_validation_digest does not match report payload")


def _derived_validation_digest_from_report(
    report: ResearchTeamDomainPredictionErrorAttributionReport,
) -> str:
    return _derived_validation_digest_from_payload(_json_ready(asdict(report)))


def _derived_validation_digest_from_payload(payload: dict[str, Any]) -> str:
    digest_payload = _json_ready(payload)
    if type(digest_payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    digest_payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("derived_validation_digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK):
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_text(field_name, value)
    return value


def _require_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_redacted_reference(field_name: str, value: object) -> str:
    text = _require_public_string(field_name, value)
    if not _is_redacted_reference(text):
        raise ValueError(f"{field_name} must be redacted or public")
    return text


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be from 0 through 1")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, flag_name):
            raise ValueError(f"{field_name} must expose {flag_name}")
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")


def _require_sha256(field_name: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    later_utc = _as_utc("later", later)
    earlier_utc = _as_utc("earlier", earlier)
    if later_utc < earlier_utc:
        raise ValueError("later must be on or after earlier")
    delta = later_utc - earlier_utc
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days * 86400)
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    return _quantize(seconds)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: Any) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total = _quantize(total + value)
    return total


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return _quantize(-value)
    return _quantize(value)


def _redacted_reference(value: str) -> str:
    if _is_public_reference(value):
        _reject_unsafe_text("attribution_reference", value)
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _is_public_reference(value: str) -> bool:
    lowered = value.lower()
    return "://" not in lowered and lowered.startswith(_PUBLIC_REFERENCE_PREFIXES)


def _is_redacted_reference(value: str) -> bool:
    if value.startswith("sha256:") and len(value) == 71:
        digest = value.removeprefix("sha256:")
        return all(character in "0123456789abcdef" for character in digest)
    return _is_public_reference(value)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if value is None:
        return None
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("JSON datetime value", value).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) in (int, float):
        raise ValueError("JSON numeric values must use Decimal strings")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_key(key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str):
        _reject_unsafe_text("payload value", value)
        return
    if isinstance(value, Decimal):
        raise ValueError(f"{label} must serialize Decimal values")
    if isinstance(value, float):
        raise ValueError(f"{label} must not contain float values")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError(f"{label} must not contain integer values")


def _reject_unsafe_key(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"unsafe public payload key: {value}")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered:
        raise ValueError(f"{field_name} has unsafe value")
    if any(fragment in lowered for fragment in _UNSAFE_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe value")
