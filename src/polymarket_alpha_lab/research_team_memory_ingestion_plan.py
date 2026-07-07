"""Report-only research team memory ingestion planning.

This module builds a deterministic, redacted plan for how research team
long-term memory could be written to local Supabase/Postgres storage by a
separate adapter. It never opens storage connections and never emits storage
location details, credentials, raw references, or raw evidence.
"""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "RESEARCH_TEAM_MEMORY_INGESTION_PLAN_CONFIG_VERSION",
    "ResearchTeamMemoryIngestionPlanConfig",
    "ResearchTeamMemoryIngestionPlanInput",
    "ResearchTeamMemoryIngestionPlanReport",
    "ResearchTeamMemoryIngestionPlanRow",
    "build_research_team_memory_ingestion_plan",
    "research_team_memory_ingestion_plan_payload",
)


RESEARCH_TEAM_MEMORY_INGESTION_PLAN_CONFIG_VERSION = (
    "research-team-memory-ingestion-plan-v0"
)
INGESTION_PLAN_MODE = "local_supabase_postgres_report_only_memory_ingestion_plan"

MEMORY_SCOPES = (
    "long_term_research_memory",
    "source_summary_memory",
    "postmortem_learning_memory",
)
PUBLIC_STATUSES = ("pass", "watch", "block")
INGESTION_PLAN_ACTIONS = (
    "prepare_report_only_memory_ingestion_plan",
    "hold_report_only_memory_ingestion_plan_for_review",
    "block_report_only_memory_ingestion_plan",
)
NEXT_STEPS = {
    "pass": "prepare_redacted_memory_ingestion_contract",
    "watch": "review_memory_ingestion_coverage_gaps",
    "block": "block_memory_ingestion_until_plan_is_safe",
}

FIELD_FAMILIES_BY_SCOPE = {
    "long_term_research_memory": (
        "memory_identity",
        "claim_summary",
        "probability_context",
        "review_cadence",
        "outcome_feedback",
    ),
    "source_summary_memory": (
        "source_family",
        "authority_band",
        "evidence_window",
        "agreement_bucket",
        "redaction_state",
    ),
    "postmortem_learning_memory": (
        "review_identity",
        "resolution_result",
        "calibration_delta",
        "lesson_summary",
        "followup_state",
    ),
}
DEDUPE_KEYS_BY_SCOPE = {
    "long_term_research_memory": (
        "memory_key_digest",
        "event_family_digest",
        "claim_digest",
        "time_bucket",
    ),
    "source_summary_memory": (
        "source_family_digest",
        "evidence_window_bucket",
        "claim_family_digest",
        "authority_band",
    ),
    "postmortem_learning_memory": (
        "review_digest",
        "event_family_digest",
        "resolution_bucket",
        "lesson_digest",
    ),
}
POSTMORTEM_RECORDS_BY_SCOPE = {
    "long_term_research_memory": (
        "resolved_probability_bucket",
        "forecast_error_bucket",
        "lesson_digest",
        "review_state",
    ),
    "source_summary_memory": (
        "source_disagreement_bucket",
        "late_update_bucket",
        "source_gap_digest",
        "refresh_state",
    ),
    "postmortem_learning_memory": (
        "settlement_bucket",
        "calibration_bucket",
        "miss_reason_digest",
        "action_item_state",
    ),
}
SOURCE_SUMMARIES_BY_SCOPE = {
    "long_term_research_memory": (
        "source_family_digest",
        "evidence_window_bucket",
        "summary_digest",
        "agreement_bucket",
    ),
    "source_summary_memory": (
        "source_family_digest",
        "method_code",
        "recency_bucket",
        "summary_digest",
    ),
    "postmortem_learning_memory": (
        "source_family_digest",
        "resolution_evidence_bucket",
        "summary_digest",
        "confidence_bucket",
    ),
}
SAFETY_BOUNDARIES_BY_SCOPE = {
    "long_term_research_memory": (
        "credential_redaction",
        "storage_target_redaction",
        "raw_evidence_redaction",
        "report_only_no_write",
    ),
    "source_summary_memory": (
        "reference_digest_only",
        "storage_target_redaction",
        "raw_evidence_redaction",
        "report_only_no_write",
    ),
    "postmortem_learning_memory": (
        "review_digest_only",
        "storage_target_redaction",
        "raw_evidence_redaction",
        "report_only_no_write",
    ),
}

ROW_REASON_CODES = (
    "long_term_research_memory_scope",
    "source_summary_memory_scope",
    "postmortem_learning_memory_scope",
    "field_family_coverage_pass",
    "field_family_coverage_watch",
    "field_family_coverage_block",
    "dedupe_key_coverage_pass",
    "dedupe_key_coverage_watch",
    "dedupe_key_coverage_block",
    "postmortem_record_coverage_pass",
    "postmortem_record_coverage_watch",
    "postmortem_record_coverage_block",
    "source_summary_coverage_pass",
    "source_summary_coverage_watch",
    "source_summary_coverage_block",
    "safety_boundary_coverage_pass",
    "safety_boundary_coverage_watch",
    "safety_boundary_coverage_block",
    "memory_ingestion_plan_prepared",
    "memory_ingestion_plan_review_required",
    "memory_ingestion_plan_blocked",
)
REPORT_REASON_CODES = (
    "no_research_team_memory_ingestion_inputs",
    "research_team_memory_ingestion_plans_pass",
    "research_team_memory_ingestion_plans_watch",
    "research_team_memory_ingestion_plans_block",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_SCORE = Decimal("0.000000")

PAYLOAD_FIELDS = frozenset(
    (
        "config_version",
        "ingestion_plan_mode",
        "report_status",
        "next_step",
        "plan_count",
        "pass_count",
        "watch_count",
        "block_count",
        "prepare_count",
        "review_count",
        "blocked_count",
        "average_readiness_score",
        "rows",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "plan_rank",
        "plan_key",
        "memory_scope",
        "public_status",
        "ingestion_plan_action",
        "ingestion_allowed",
        "field_families",
        "dedupe_keys",
        "postmortem_records",
        "source_summaries",
        "safety_boundaries",
        "field_family_coverage",
        "dedupe_key_coverage",
        "postmortem_record_coverage",
        "source_summary_coverage",
        "safety_boundary_coverage",
        "readiness_score",
        "sanitized_plan_summary",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "api_key",
    "auth",
    "connection_string",
    "credential",
    "dsn",
    "private",
    "raw_reference",
    "raw_source_text",
    "raw_source_url",
    "secret",
    "service_role",
    "source_text",
    "source_url",
    "table",
    "token",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "api key",
    "api_key",
    "bearer ",
    "connection string",
    "connection_string",
    "credential=",
    "dsn",
    "private",
    "raw reference",
    "raw source text",
    "raw source url",
    "raw_source_text",
    "raw_source_url",
    "secret",
    "service role",
    "service_role",
    "source text",
    "source url",
    "source_text",
    "source_url",
    "table",
    "token",
    "://",
)


@dataclass(frozen=True)
class ResearchTeamMemoryIngestionPlanConfig:
    config_version: str = RESEARCH_TEAM_MEMORY_INGESTION_PLAN_CONFIG_VERSION
    min_pass_field_family_coverage: Decimal = Decimal("0.900000")
    min_watch_field_family_coverage: Decimal = Decimal("0.700000")
    min_pass_dedupe_key_coverage: Decimal = Decimal("0.850000")
    min_watch_dedupe_key_coverage: Decimal = Decimal("0.650000")
    min_pass_postmortem_record_coverage: Decimal = Decimal("0.800000")
    min_watch_postmortem_record_coverage: Decimal = Decimal("0.600000")
    min_pass_source_summary_coverage: Decimal = Decimal("0.850000")
    min_watch_source_summary_coverage: Decimal = Decimal("0.650000")
    min_pass_safety_boundary_coverage: Decimal = Decimal("0.950000")
    min_watch_safety_boundary_coverage: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryIngestionPlanConfig:
            raise TypeError(
                "ResearchTeamMemoryIngestionPlanConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryIngestionPlanConfig:
            raise ValueError(
                "config must be exactly ResearchTeamMemoryIngestionPlanConfig",
            )
        _require_public_string("config_version", self.config_version)
        if self.config_version != RESEARCH_TEAM_MEMORY_INGESTION_PLAN_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_field_family_coverage",
            "min_watch_field_family_coverage",
            "min_pass_dedupe_key_coverage",
            "min_watch_dedupe_key_coverage",
            "min_pass_postmortem_record_coverage",
            "min_watch_postmortem_record_coverage",
            "min_pass_source_summary_coverage",
            "min_watch_source_summary_coverage",
            "min_pass_safety_boundary_coverage",
            "min_watch_safety_boundary_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_order(
            "field_family_coverage",
            self.min_pass_field_family_coverage,
            self.min_watch_field_family_coverage,
        )
        _require_threshold_order(
            "dedupe_key_coverage",
            self.min_pass_dedupe_key_coverage,
            self.min_watch_dedupe_key_coverage,
        )
        _require_threshold_order(
            "postmortem_record_coverage",
            self.min_pass_postmortem_record_coverage,
            self.min_watch_postmortem_record_coverage,
        )
        _require_threshold_order(
            "source_summary_coverage",
            self.min_pass_source_summary_coverage,
            self.min_watch_source_summary_coverage,
        )
        _require_threshold_order(
            "safety_boundary_coverage",
            self.min_pass_safety_boundary_coverage,
            self.min_watch_safety_boundary_coverage,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryIngestionPlanInput:
    plan_digest: str
    memory_scope: str
    field_family_coverage: Decimal
    dedupe_key_coverage: Decimal
    postmortem_record_coverage: Decimal
    source_summary_coverage: Decimal
    safety_boundary_coverage: Decimal
    sanitized_plan_summary: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryIngestionPlanInput:
            raise TypeError(
                "ResearchTeamMemoryIngestionPlanInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryIngestionPlanInput:
            raise ValueError("input must be exactly ResearchTeamMemoryIngestionPlanInput")
        object.__setattr__(
            self,
            "plan_digest",
            _require_digest_string("plan_digest", self.plan_digest),
        )
        object.__setattr__(
            self,
            "memory_scope",
            _require_member("memory_scope", self.memory_scope, MEMORY_SCOPES),
        )
        for field_name in (
            "field_family_coverage",
            "dedupe_key_coverage",
            "postmortem_record_coverage",
            "source_summary_coverage",
            "safety_boundary_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_string("sanitized_plan_summary", self.sanitized_plan_summary)
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchTeamMemoryIngestionPlanRow:
    plan_rank: Decimal
    plan_key: str
    memory_scope: str
    public_status: str
    ingestion_plan_action: str
    ingestion_allowed: bool
    field_families: tuple[str, ...]
    dedupe_keys: tuple[str, ...]
    postmortem_records: tuple[str, ...]
    source_summaries: tuple[str, ...]
    safety_boundaries: tuple[str, ...]
    field_family_coverage: Decimal
    dedupe_key_coverage: Decimal
    postmortem_record_coverage: Decimal
    source_summary_coverage: Decimal
    safety_boundary_coverage: Decimal
    readiness_score: Decimal
    sanitized_plan_summary: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchTeamMemoryIngestionPlanConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryIngestionPlanRow:
            raise TypeError(
                "ResearchTeamMemoryIngestionPlanRow does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchTeamMemoryIngestionPlanConfig | None,
    ) -> None:
        if type(self) is not ResearchTeamMemoryIngestionPlanRow:
            raise ValueError("row must be exactly ResearchTeamMemoryIngestionPlanRow")
        object.__setattr__(
            self,
            "plan_rank",
            _require_positive_count_decimal("plan_rank", self.plan_rank),
        )
        _require_public_string("plan_key", self.plan_key)
        object.__setattr__(
            self,
            "memory_scope",
            _require_member("memory_scope", self.memory_scope, MEMORY_SCOPES),
        )
        object.__setattr__(
            self,
            "public_status",
            _require_status("public_status", self.public_status),
        )
        object.__setattr__(
            self,
            "ingestion_plan_action",
            _require_member(
                "ingestion_plan_action",
                self.ingestion_plan_action,
                INGESTION_PLAN_ACTIONS,
            ),
        )
        if type(self.ingestion_allowed) is not bool:
            raise ValueError("ingestion_allowed must be a bool")
        object.__setattr__(
            self,
            "field_families",
            _normalize_scope_items(
                "field_families",
                self.memory_scope,
                self.field_families,
                FIELD_FAMILIES_BY_SCOPE,
            ),
        )
        object.__setattr__(
            self,
            "dedupe_keys",
            _normalize_scope_items(
                "dedupe_keys",
                self.memory_scope,
                self.dedupe_keys,
                DEDUPE_KEYS_BY_SCOPE,
            ),
        )
        object.__setattr__(
            self,
            "postmortem_records",
            _normalize_scope_items(
                "postmortem_records",
                self.memory_scope,
                self.postmortem_records,
                POSTMORTEM_RECORDS_BY_SCOPE,
            ),
        )
        object.__setattr__(
            self,
            "source_summaries",
            _normalize_scope_items(
                "source_summaries",
                self.memory_scope,
                self.source_summaries,
                SOURCE_SUMMARIES_BY_SCOPE,
            ),
        )
        object.__setattr__(
            self,
            "safety_boundaries",
            _normalize_scope_items(
                "safety_boundaries",
                self.memory_scope,
                self.safety_boundaries,
                SAFETY_BOUNDARIES_BY_SCOPE,
            ),
        )
        for field_name in (
            "field_family_coverage",
            "dedupe_key_coverage",
            "postmortem_record_coverage",
            "source_summary_coverage",
            "safety_boundary_coverage",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_string("sanitized_plan_summary", self.sanitized_plan_summary)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self, config=validation_config)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamMemoryIngestionPlanReport:
    config_version: str
    ingestion_plan_mode: str
    report_status: str
    next_step: str
    plan_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    prepare_count: Decimal
    review_count: Decimal
    blocked_count: Decimal
    average_readiness_score: Decimal
    rows: tuple[ResearchTeamMemoryIngestionPlanRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryIngestionPlanReport:
            raise TypeError(
                "ResearchTeamMemoryIngestionPlanReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryIngestionPlanReport:
            raise ValueError("report must be exactly ResearchTeamMemoryIngestionPlanReport")
        _require_public_string("config_version", self.config_version)
        if self.config_version != RESEARCH_TEAM_MEMORY_INGESTION_PLAN_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_public_string("ingestion_plan_mode", self.ingestion_plan_mode)
        if self.ingestion_plan_mode != INGESTION_PLAN_MODE:
            raise ValueError("ingestion_plan_mode must match the report-only mode")
        object.__setattr__(
            self,
            "report_status",
            _require_status("report_status", self.report_status),
        )
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "plan_count",
            "pass_count",
            "watch_count",
            "block_count",
            "prepare_count",
            "review_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_readiness_score",
            _require_score_decimal(
                "average_readiness_score",
                self.average_readiness_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)


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


def build_research_team_memory_ingestion_plan(
    inputs: tuple[ResearchTeamMemoryIngestionPlanInput, ...],
    *,
    config: ResearchTeamMemoryIngestionPlanConfig | None = None,
) -> ResearchTeamMemoryIngestionPlanReport:
    cfg = config or ResearchTeamMemoryIngestionPlanConfig()
    if type(cfg) is not ResearchTeamMemoryIngestionPlanConfig:
        raise ValueError("config must be a ResearchTeamMemoryIngestionPlanConfig")
    _require_hard_flags("config", cfg)
    input_rows = _normalize_inputs(inputs)
    sorted_inputs = tuple(sorted(input_rows, key=_input_sort_key))
    rows = tuple(
        _build_row(index=index, input_row=input_row, config=cfg)
        for index, input_row in enumerate(sorted_inputs, start=1)
    )
    status = _report_status(rows)
    return ResearchTeamMemoryIngestionPlanReport(
        config_version=cfg.config_version,
        ingestion_plan_mode=INGESTION_PLAN_MODE,
        report_status=status,
        next_step=NEXT_STEPS[status],
        plan_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        prepare_count=_action_count(rows, "prepare_report_only_memory_ingestion_plan"),
        review_count=_action_count(
            rows,
            "hold_report_only_memory_ingestion_plan_for_review",
        ),
        blocked_count=_action_count(rows, "block_report_only_memory_ingestion_plan"),
        average_readiness_score=_average_readiness_score(rows),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_team_memory_ingestion_plan_payload(
    report: ResearchTeamMemoryIngestionPlanReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamMemoryIngestionPlanReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        _validate_payload_fields(report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchTeamMemoryIngestionPlanReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_payload_fields(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


def _build_row(
    *,
    index: int,
    input_row: ResearchTeamMemoryIngestionPlanInput,
    config: ResearchTeamMemoryIngestionPlanConfig,
) -> ResearchTeamMemoryIngestionPlanRow:
    status = _input_status(input_row, config)
    action = _ingestion_plan_action(status)
    return ResearchTeamMemoryIngestionPlanRow(
        plan_rank=_count(index),
        plan_key=f"redacted-research-team-memory-ingestion-plan-{index:03d}",
        memory_scope=input_row.memory_scope,
        public_status=status,
        ingestion_plan_action=action,
        ingestion_allowed=action == "prepare_report_only_memory_ingestion_plan",
        field_families=FIELD_FAMILIES_BY_SCOPE[input_row.memory_scope],
        dedupe_keys=DEDUPE_KEYS_BY_SCOPE[input_row.memory_scope],
        postmortem_records=POSTMORTEM_RECORDS_BY_SCOPE[input_row.memory_scope],
        source_summaries=SOURCE_SUMMARIES_BY_SCOPE[input_row.memory_scope],
        safety_boundaries=SAFETY_BOUNDARIES_BY_SCOPE[input_row.memory_scope],
        field_family_coverage=input_row.field_family_coverage,
        dedupe_key_coverage=input_row.dedupe_key_coverage,
        postmortem_record_coverage=input_row.postmortem_record_coverage,
        source_summary_coverage=input_row.source_summary_coverage,
        safety_boundary_coverage=input_row.safety_boundary_coverage,
        readiness_score=_readiness_score(input_row),
        sanitized_plan_summary=input_row.sanitized_plan_summary,
        reason_codes=_row_reason_codes(input_row, status, config),
        validation_config=config,
    )


def _input_sort_key(input_row: ResearchTeamMemoryIngestionPlanInput) -> tuple[int, str]:
    return (MEMORY_SCOPES.index(input_row.memory_scope), input_row.plan_digest)


def _row_sort_key(row: ResearchTeamMemoryIngestionPlanRow) -> tuple[Decimal, str]:
    return (row.plan_rank, row.plan_key)


def _input_status(
    input_row: ResearchTeamMemoryIngestionPlanInput,
    config: ResearchTeamMemoryIngestionPlanConfig,
) -> str:
    return _status_from_scores(
        field_family_coverage=input_row.field_family_coverage,
        dedupe_key_coverage=input_row.dedupe_key_coverage,
        postmortem_record_coverage=input_row.postmortem_record_coverage,
        source_summary_coverage=input_row.source_summary_coverage,
        safety_boundary_coverage=input_row.safety_boundary_coverage,
        config=config,
    )


def _status_from_scores(
    *,
    field_family_coverage: Decimal,
    dedupe_key_coverage: Decimal,
    postmortem_record_coverage: Decimal,
    source_summary_coverage: Decimal,
    safety_boundary_coverage: Decimal,
    config: ResearchTeamMemoryIngestionPlanConfig,
) -> str:
    if (
        field_family_coverage < config.min_watch_field_family_coverage
        or dedupe_key_coverage < config.min_watch_dedupe_key_coverage
        or postmortem_record_coverage < config.min_watch_postmortem_record_coverage
        or source_summary_coverage < config.min_watch_source_summary_coverage
        or safety_boundary_coverage < config.min_watch_safety_boundary_coverage
    ):
        return "block"
    if (
        field_family_coverage < config.min_pass_field_family_coverage
        or dedupe_key_coverage < config.min_pass_dedupe_key_coverage
        or postmortem_record_coverage < config.min_pass_postmortem_record_coverage
        or source_summary_coverage < config.min_pass_source_summary_coverage
        or safety_boundary_coverage < config.min_pass_safety_boundary_coverage
    ):
        return "watch"
    return "pass"


def _ingestion_plan_action(public_status: str) -> str:
    if public_status == "pass":
        return "prepare_report_only_memory_ingestion_plan"
    if public_status == "watch":
        return "hold_report_only_memory_ingestion_plan_for_review"
    return "block_report_only_memory_ingestion_plan"


def _readiness_score(input_row: ResearchTeamMemoryIngestionPlanInput) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            input_row.field_family_coverage * Decimal("0.250000")
            + input_row.dedupe_key_coverage * Decimal("0.200000")
            + input_row.postmortem_record_coverage * Decimal("0.200000")
            + input_row.source_summary_coverage * Decimal("0.200000")
            + input_row.safety_boundary_coverage * Decimal("0.150000")
        )
    return _require_score_decimal("readiness_score", value.quantize(SCORE_QUANTUM))


def _row_reason_codes(
    input_row: ResearchTeamMemoryIngestionPlanInput,
    public_status: str,
    config: ResearchTeamMemoryIngestionPlanConfig,
) -> tuple[str, ...]:
    codes = [
        f"{input_row.memory_scope}_scope",
        _quality_reason(
            "field_family_coverage",
            input_row.field_family_coverage,
            config.min_pass_field_family_coverage,
            config.min_watch_field_family_coverage,
        ),
        _quality_reason(
            "dedupe_key_coverage",
            input_row.dedupe_key_coverage,
            config.min_pass_dedupe_key_coverage,
            config.min_watch_dedupe_key_coverage,
        ),
        _quality_reason(
            "postmortem_record_coverage",
            input_row.postmortem_record_coverage,
            config.min_pass_postmortem_record_coverage,
            config.min_watch_postmortem_record_coverage,
        ),
        _quality_reason(
            "source_summary_coverage",
            input_row.source_summary_coverage,
            config.min_pass_source_summary_coverage,
            config.min_watch_source_summary_coverage,
        ),
        _quality_reason(
            "safety_boundary_coverage",
            input_row.safety_boundary_coverage,
            config.min_pass_safety_boundary_coverage,
            config.min_watch_safety_boundary_coverage,
        ),
    ]
    if public_status == "pass":
        codes.append("memory_ingestion_plan_prepared")
    elif public_status == "watch":
        codes.append("memory_ingestion_plan_review_required")
    else:
        codes.append("memory_ingestion_plan_blocked")
    return tuple(codes)


def _quality_reason(
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value >= pass_threshold:
        return f"{prefix}_pass"
    if value >= watch_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_block"


def _report_status(rows: tuple[ResearchTeamMemoryIngestionPlanRow, ...]) -> str:
    if not rows or any(row.public_status == "block" for row in rows):
        return "block"
    if any(row.public_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamMemoryIngestionPlanRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_research_team_memory_ingestion_inputs",)
    codes: list[str] = []
    if any(row.public_status == "pass" for row in rows):
        codes.append("research_team_memory_ingestion_plans_pass")
    if any(row.public_status == "watch" for row in rows):
        codes.append("research_team_memory_ingestion_plans_watch")
    if any(row.public_status == "block" for row in rows):
        codes.append("research_team_memory_ingestion_plans_block")
    return tuple(codes)


def _average_readiness_score(
    rows: tuple[ResearchTeamMemoryIngestionPlanRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        value = sum((row.readiness_score for row in rows), Decimal("0.000000")) / Decimal(
            len(rows),
        )
    return _require_score_decimal(
        "average_readiness_score",
        value.quantize(SCORE_QUANTUM),
    )


def _status_count(
    rows: tuple[ResearchTeamMemoryIngestionPlanRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.public_status == status)


def _action_count(
    rows: tuple[ResearchTeamMemoryIngestionPlanRow, ...],
    action: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.ingestion_plan_action == action))


def _validate_row(
    row: ResearchTeamMemoryIngestionPlanRow,
    *,
    config: ResearchTeamMemoryIngestionPlanConfig | None,
) -> None:
    cfg = config or ResearchTeamMemoryIngestionPlanConfig()
    expected_status = _status_from_scores(
        field_family_coverage=row.field_family_coverage,
        dedupe_key_coverage=row.dedupe_key_coverage,
        postmortem_record_coverage=row.postmortem_record_coverage,
        source_summary_coverage=row.source_summary_coverage,
        safety_boundary_coverage=row.safety_boundary_coverage,
        config=cfg,
    )
    if row.public_status != expected_status:
        raise ValueError("public_status does not match coverage thresholds")
    if row.ingestion_plan_action != _ingestion_plan_action(row.public_status):
        raise ValueError("ingestion_plan_action does not match public_status")
    if row.ingestion_allowed != (
        row.ingestion_plan_action == "prepare_report_only_memory_ingestion_plan"
    ):
        raise ValueError("ingestion_allowed does not match ingestion_plan_action")
    expected_input = ResearchTeamMemoryIngestionPlanInput(
        plan_digest="0" * 64,
        memory_scope=row.memory_scope,
        field_family_coverage=row.field_family_coverage,
        dedupe_key_coverage=row.dedupe_key_coverage,
        postmortem_record_coverage=row.postmortem_record_coverage,
        source_summary_coverage=row.source_summary_coverage,
        safety_boundary_coverage=row.safety_boundary_coverage,
        sanitized_plan_summary=row.sanitized_plan_summary,
    )
    if row.readiness_score != _readiness_score(expected_input):
        raise ValueError("readiness_score does not match coverage scores")
    if row.reason_codes != _row_reason_codes(expected_input, row.public_status, cfg):
        raise ValueError("reason_codes do not match row status")


def _validate_report(report: ResearchTeamMemoryIngestionPlanReport) -> None:
    rows = report.rows
    if report.report_status != _report_status(rows):
        raise ValueError("report_status does not match rows")
    if report.next_step != NEXT_STEPS[report.report_status]:
        raise ValueError("next_step does not match report_status")
    expected_counts = {
        "plan_count": _count(len(rows)),
        "pass_count": _count(_status_count(rows, "pass")),
        "watch_count": _count(_status_count(rows, "watch")),
        "block_count": _count(_status_count(rows, "block")),
        "prepare_count": _action_count(
            rows,
            "prepare_report_only_memory_ingestion_plan",
        ),
        "review_count": _action_count(
            rows,
            "hold_report_only_memory_ingestion_plan_for_review",
        ),
        "blocked_count": _action_count(
            rows,
            "block_report_only_memory_ingestion_plan",
        ),
    }
    for field_name, expected_value in expected_counts.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} does not match rows")
    if report.average_readiness_score != _average_readiness_score(rows):
        raise ValueError("average_readiness_score does not match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes do not match rows")


def _validate_payload_fields(payload: dict[str, Any]) -> None:
    if set(payload) != PAYLOAD_FIELDS:
        raise ValueError("payload fields do not match public contract")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain objects")
        if set(row) != ROW_PAYLOAD_FIELDS:
            raise ValueError("payload row fields do not match public contract")


def _normalize_inputs(
    inputs: tuple[ResearchTeamMemoryIngestionPlanInput, ...],
) -> tuple[ResearchTeamMemoryIngestionPlanInput, ...]:
    if type(inputs) is not tuple:
        raise ValueError("inputs must be a tuple")
    for item in inputs:
        if type(item) is not ResearchTeamMemoryIngestionPlanInput:
            raise ValueError("inputs must contain ResearchTeamMemoryIngestionPlanInput")
        _require_hard_flags("input", item)
    return inputs


def _normalize_rows(
    rows: tuple[ResearchTeamMemoryIngestionPlanRow, ...],
) -> tuple[ResearchTeamMemoryIngestionPlanRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for item in rows:
        if type(item) is not ResearchTeamMemoryIngestionPlanRow:
            raise ValueError("rows must contain ResearchTeamMemoryIngestionPlanRow")
        _require_hard_flags("row", item)
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("rows must be sorted by plan rank")
    return rows


def _normalize_scope_items(
    label: str,
    memory_scope: str,
    values: tuple[str, ...],
    expected_by_scope: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{label} must be a tuple")
    expected = expected_by_scope[memory_scope]
    if values != expected:
        raise ValueError(f"{label} must match the memory scope contract")
    for item in values:
        _require_public_string(label, item)
    return values


def _normalize_row_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for code in reason_codes:
        _require_member("reason_codes", code, ROW_REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    return reason_codes


def _normalize_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for code in reason_codes:
        _require_member("reason_codes", code, REPORT_REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    return reason_codes


def _require_threshold_order(
    label: str,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> None:
    if pass_threshold < watch_threshold:
        raise ValueError(f"{label} pass threshold must be at least watch threshold")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_member(label: str, value: str, allowed: tuple[str, ...]) -> str:
    _require_public_string(label, value)
    if value not in allowed:
        raise ValueError(f"{label} must be one of the supported values")
    return value


def _require_status(label: str, value: str) -> str:
    return _require_member(label, value, PUBLIC_STATUSES)


def _require_public_string(label: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{label} must be a non-empty public string")
    _reject_unsafe_public_text(label, value)
    return value


def _require_digest_string(label: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be a redacted lowercase sha256 digest")
    return value


def _require_score_decimal(label: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    if value < Decimal("0") or value > Decimal("1"):
        raise ValueError(f"{label} must be between 0 and 1")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{label} must use the required decimal precision")
    return value.quantize(SCORE_QUANTUM)


def _require_nonnegative_count_decimal(label: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be a Decimal")
    if not value.is_finite() or value < Decimal("0"):
        raise ValueError(f"{label} must be a nonnegative Decimal")
    if value != value.to_integral_value():
        raise ValueError(f"{label} must be an integer Decimal")
    return value.quantize(COUNT_QUANTUM)


def _require_positive_count_decimal(label: str, value: Decimal) -> Decimal:
    value = _require_nonnegative_count_decimal(label, value)
    if value <= Decimal("0"):
        raise ValueError(f"{label} must be positive")
    return value


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative integer")
    return Decimal(str(value)).quantize(COUNT_QUANTUM)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if type(value) is bool or type(value) is str:
        return value
    if type(value) in (int, float):
        raise ValueError("payload numeric values must use Decimal strings")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), allow_json_containers=True)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public payload keys must be strings")
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if allow_json_containers and type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is tuple:
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) in (int, float):
        raise ValueError(f"{label} public payload numeric values must be Decimal")


def _reject_unsafe_public_key(label: str, value: str) -> None:
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{label} has unsafe public key")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{label} has unsafe public text")
