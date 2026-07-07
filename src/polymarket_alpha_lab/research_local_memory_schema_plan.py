"""Pure report-only local research memory schema-plan model.

The module prepares deterministic, redacted schema plans for local memory
surfaces. It does not connect to storage, expose storage identifiers, or
execute persistence operations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "RESEARCH_LOCAL_MEMORY_SCHEMA_PLAN_CONFIG_VERSION",
    "ResearchLocalMemorySchemaPlanConfig",
    "ResearchLocalMemorySchemaPlanInput",
    "ResearchLocalMemorySchemaPlanReport",
    "ResearchLocalMemorySchemaPlanRow",
    "build_research_local_memory_schema_plan",
    "research_local_memory_schema_plan_payload",
)


RESEARCH_LOCAL_MEMORY_SCHEMA_PLAN_CONFIG_VERSION = "research-local-memory-schema-plan-v0"
SCHEMA_PLAN_MODE = "report_only_redacted_local_supabase_memory_schema_plan"

MEMORY_SCOPES = (
    "long_term_memory",
    "source_registry",
    "postmortem_result",
)
PUBLIC_STATUSES = ("pass", "watch", "block")
SCHEMA_PLAN_ACTIONS = (
    "prepare_redacted_schema_plan",
    "hold_redacted_schema_plan_for_review",
    "suppress_redacted_schema_plan",
)
FIELD_GROUPS_BY_SCOPE = {
    "long_term_memory": (
        "memory_key_digest",
        "topic_family_code",
        "sanitized_claim_digest",
        "confidence_bucket",
        "last_review_bucket",
    ),
    "source_registry": (
        "source_family_digest",
        "publication_window_bucket",
        "evidence_method_code",
        "recency_bucket",
        "redaction_state",
    ),
    "postmortem_result": (
        "review_digest",
        "settlement_bucket",
        "calibration_bucket",
        "lesson_digest",
        "review_state",
    ),
}

ROW_REASON_CODES = (
    "long_term_memory_scope",
    "source_registry_scope",
    "postmortem_result_scope",
    "redaction_coverage_pass",
    "redaction_coverage_watch",
    "redaction_coverage_block",
    "lineage_coverage_pass",
    "lineage_coverage_watch",
    "lineage_coverage_block",
    "review_coverage_pass",
    "review_coverage_watch",
    "review_coverage_block",
    "local_memory_schema_plan_prepared",
    "local_memory_schema_plan_review_required",
    "local_memory_schema_plan_blocked",
)
REPORT_REASON_CODES = (
    "no_local_memory_schema_inputs_supplied",
    "local_memory_schema_plans_prepared",
    "local_memory_schema_plans_review_required",
    "local_memory_schema_plans_blocked",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_SCORE = Decimal("0.000000")
ONE_SCORE = Decimal("1.000000")
ZERO_COUNT = Decimal("0")

PAYLOAD_FIELDS = frozenset(
    (
        "config_version",
        "schema_plan_mode",
        "report_status",
        "schema_count",
        "pass_count",
        "watch_count",
        "block_count",
        "prepare_schema_count",
        "review_count",
        "suppress_count",
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
        "schema_rank",
        "schema_key",
        "memory_scope",
        "public_status",
        "schema_plan_action",
        "prepare_schema",
        "field_groups",
        "redaction_coverage",
        "lineage_coverage",
        "review_coverage",
        "readiness_score",
        "sanitized_schema_notes",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "auth",
    "candidate_id",
    "connection_string",
    "database_url",
    "dsn",
    "market_id",
    "market_question",
    "market_slug",
    "private_key",
    "raw_candidate",
    "real_table",
    "service_role",
    "source_ref",
    "source_text",
    "source_url",
    "table_name",
    "token",
    "wallet",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "api_key",
    "auth",
    "bearer ",
    "buy",
    "candidate id",
    "candidate_id",
    "connection string",
    "connection_string",
    "database_url",
    "dsn",
    "market id",
    "market question",
    "market slug",
    "market_id",
    "market_question",
    "market_slug",
    "open order",
    "order",
    "position",
    "postgres://",
    "postgresql://",
    "raw candidate",
    "raw-candidate",
    "raw_candidate",
    "real table",
    "recommend",
    "recommendation",
    "sell",
    "service_role",
    "source ref",
    "source text",
    "source url",
    "source_ref",
    "source_text",
    "source_url",
    "table ",
    "table:",
    "table_name",
    "token",
    "trade",
    "url",
    "wallet",
    "www.",
    "://",
)


@dataclass(frozen=True)
class ResearchLocalMemorySchemaPlanConfig:
    config_version: str = RESEARCH_LOCAL_MEMORY_SCHEMA_PLAN_CONFIG_VERSION
    min_pass_redaction_coverage: Decimal = Decimal("0.900000")
    min_watch_redaction_coverage: Decimal = Decimal("0.700000")
    min_pass_lineage_coverage: Decimal = Decimal("0.850000")
    min_watch_lineage_coverage: Decimal = Decimal("0.650000")
    min_pass_review_coverage: Decimal = Decimal("0.800000")
    min_watch_review_coverage: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchLocalMemorySchemaPlanConfig:
            raise TypeError(
                "ResearchLocalMemorySchemaPlanConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchLocalMemorySchemaPlanConfig:
            raise ValueError(
                "config must be exactly ResearchLocalMemorySchemaPlanConfig",
            )
        _require_public_string("config_version", self.config_version)
        if self.config_version != RESEARCH_LOCAL_MEMORY_SCHEMA_PLAN_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_redaction_coverage",
            "min_watch_redaction_coverage",
            "min_pass_lineage_coverage",
            "min_watch_lineage_coverage",
            "min_pass_review_coverage",
            "min_watch_review_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_order(
            "redaction_coverage",
            self.min_pass_redaction_coverage,
            self.min_watch_redaction_coverage,
        )
        _require_threshold_order(
            "lineage_coverage",
            self.min_pass_lineage_coverage,
            self.min_watch_lineage_coverage,
        )
        _require_threshold_order(
            "review_coverage",
            self.min_pass_review_coverage,
            self.min_watch_review_coverage,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchLocalMemorySchemaPlanInput:
    schema_digest: str
    memory_scope: str
    redaction_coverage: Decimal
    lineage_coverage: Decimal
    review_coverage: Decimal
    sanitized_schema_notes: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchLocalMemorySchemaPlanInput:
            raise TypeError(
                "ResearchLocalMemorySchemaPlanInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchLocalMemorySchemaPlanInput:
            raise ValueError("input must be exactly ResearchLocalMemorySchemaPlanInput")
        object.__setattr__(
            self,
            "schema_digest",
            _require_digest_string("schema_digest", self.schema_digest),
        )
        object.__setattr__(
            self,
            "memory_scope",
            _require_member("memory_scope", self.memory_scope, MEMORY_SCOPES),
        )
        for field_name in (
            "redaction_coverage",
            "lineage_coverage",
            "review_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_string("sanitized_schema_notes", self.sanitized_schema_notes)
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchLocalMemorySchemaPlanRow:
    schema_rank: Decimal
    schema_key: str
    memory_scope: str
    public_status: str
    schema_plan_action: str
    prepare_schema: bool
    field_groups: tuple[str, ...]
    redaction_coverage: Decimal
    lineage_coverage: Decimal
    review_coverage: Decimal
    readiness_score: Decimal
    sanitized_schema_notes: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchLocalMemorySchemaPlanRow:
            raise TypeError(
                "ResearchLocalMemorySchemaPlanRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchLocalMemorySchemaPlanRow:
            raise ValueError("row must be exactly ResearchLocalMemorySchemaPlanRow")
        object.__setattr__(
            self,
            "schema_rank",
            _require_positive_count_decimal("schema_rank", self.schema_rank),
        )
        _require_public_string("schema_key", self.schema_key)
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
            "schema_plan_action",
            _require_member(
                "schema_plan_action",
                self.schema_plan_action,
                SCHEMA_PLAN_ACTIONS,
            ),
        )
        if type(self.prepare_schema) is not bool:
            raise ValueError("prepare_schema must be a bool")
        object.__setattr__(
            self,
            "field_groups",
            _normalize_field_groups(self.memory_scope, self.field_groups),
        )
        for field_name in (
            "redaction_coverage",
            "lineage_coverage",
            "review_coverage",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_string("sanitized_schema_notes", self.sanitized_schema_notes)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchLocalMemorySchemaPlanReport:
    config_version: str
    schema_plan_mode: str
    report_status: str
    schema_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    prepare_schema_count: Decimal
    review_count: Decimal
    suppress_count: Decimal
    average_readiness_score: Decimal
    rows: tuple[ResearchLocalMemorySchemaPlanRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchLocalMemorySchemaPlanReport:
            raise TypeError(
                "ResearchLocalMemorySchemaPlanReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchLocalMemorySchemaPlanReport:
            raise ValueError("report must be exactly ResearchLocalMemorySchemaPlanReport")
        _require_public_string("config_version", self.config_version)
        if self.config_version != RESEARCH_LOCAL_MEMORY_SCHEMA_PLAN_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_public_string("schema_plan_mode", self.schema_plan_mode)
        if self.schema_plan_mode != SCHEMA_PLAN_MODE:
            raise ValueError("schema_plan_mode must be report-only and redacted")
        object.__setattr__(
            self,
            "report_status",
            _require_status("report_status", self.report_status),
        )
        for field_name in (
            "schema_count",
            "pass_count",
            "watch_count",
            "block_count",
            "prepare_schema_count",
            "review_count",
            "suppress_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
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


def build_research_local_memory_schema_plan(
    inputs: tuple[ResearchLocalMemorySchemaPlanInput, ...],
    *,
    config: ResearchLocalMemorySchemaPlanConfig | None = None,
) -> ResearchLocalMemorySchemaPlanReport:
    cfg = config or ResearchLocalMemorySchemaPlanConfig()
    if type(cfg) is not ResearchLocalMemorySchemaPlanConfig:
        raise ValueError("config must be a ResearchLocalMemorySchemaPlanConfig")
    _require_hard_flags("config", cfg)
    input_rows = _normalize_inputs(inputs)
    sorted_inputs = tuple(sorted(input_rows, key=_input_sort_key))
    rows = tuple(
        _build_row(index=index, input_row=input_row, config=cfg)
        for index, input_row in enumerate(sorted_inputs, start=1)
    )
    return ResearchLocalMemorySchemaPlanReport(
        config_version=cfg.config_version,
        schema_plan_mode=SCHEMA_PLAN_MODE,
        report_status=_report_status(rows),
        schema_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        prepare_schema_count=_action_count(rows, "prepare_redacted_schema_plan"),
        review_count=_action_count(rows, "hold_redacted_schema_plan_for_review"),
        suppress_count=_action_count(rows, "suppress_redacted_schema_plan"),
        average_readiness_score=_average_readiness_score(rows),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_local_memory_schema_plan_payload(
    report: ResearchLocalMemorySchemaPlanReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchLocalMemorySchemaPlanReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        _validate_payload_fields(report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchLocalMemorySchemaPlanReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_payload_fields(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


def _build_row(
    *,
    index: int,
    input_row: ResearchLocalMemorySchemaPlanInput,
    config: ResearchLocalMemorySchemaPlanConfig,
) -> ResearchLocalMemorySchemaPlanRow:
    status = _input_status(input_row, config)
    action = _schema_plan_action(status)
    return ResearchLocalMemorySchemaPlanRow(
        schema_rank=_count(index),
        schema_key=f"redacted-local-memory-schema-{index:03d}",
        memory_scope=input_row.memory_scope,
        public_status=status,
        schema_plan_action=action,
        prepare_schema=action == "prepare_redacted_schema_plan",
        field_groups=FIELD_GROUPS_BY_SCOPE[input_row.memory_scope],
        redaction_coverage=input_row.redaction_coverage,
        lineage_coverage=input_row.lineage_coverage,
        review_coverage=input_row.review_coverage,
        readiness_score=_readiness_score(input_row),
        sanitized_schema_notes=input_row.sanitized_schema_notes,
        reason_codes=_row_reason_codes(input_row, status, config),
    )


def _input_sort_key(input_row: ResearchLocalMemorySchemaPlanInput) -> tuple[int, str]:
    return (MEMORY_SCOPES.index(input_row.memory_scope), input_row.schema_digest)


def _row_sort_key(row: ResearchLocalMemorySchemaPlanRow) -> tuple[Decimal, str]:
    return (row.schema_rank, row.schema_key)


def _input_status(
    input_row: ResearchLocalMemorySchemaPlanInput,
    config: ResearchLocalMemorySchemaPlanConfig,
) -> str:
    if (
        input_row.redaction_coverage < config.min_watch_redaction_coverage
        or input_row.lineage_coverage < config.min_watch_lineage_coverage
        or input_row.review_coverage < config.min_watch_review_coverage
    ):
        return "block"
    if (
        input_row.redaction_coverage < config.min_pass_redaction_coverage
        or input_row.lineage_coverage < config.min_pass_lineage_coverage
        or input_row.review_coverage < config.min_pass_review_coverage
    ):
        return "watch"
    return "pass"


def _schema_plan_action(public_status: str) -> str:
    if public_status == "pass":
        return "prepare_redacted_schema_plan"
    if public_status == "watch":
        return "hold_redacted_schema_plan_for_review"
    return "suppress_redacted_schema_plan"


def _readiness_score(input_row: ResearchLocalMemorySchemaPlanInput) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            input_row.redaction_coverage * Decimal("0.400000")
            + input_row.lineage_coverage * Decimal("0.350000")
            + input_row.review_coverage * Decimal("0.250000")
        )
    return _require_score_decimal("readiness_score", value)


def _row_reason_codes(
    input_row: ResearchLocalMemorySchemaPlanInput,
    public_status: str,
    config: ResearchLocalMemorySchemaPlanConfig,
) -> tuple[str, ...]:
    codes = [
        f"{input_row.memory_scope}_scope",
        _quality_reason(
            "redaction_coverage",
            input_row.redaction_coverage,
            config.min_pass_redaction_coverage,
            config.min_watch_redaction_coverage,
        ),
        _quality_reason(
            "lineage_coverage",
            input_row.lineage_coverage,
            config.min_pass_lineage_coverage,
            config.min_watch_lineage_coverage,
        ),
        _quality_reason(
            "review_coverage",
            input_row.review_coverage,
            config.min_pass_review_coverage,
            config.min_watch_review_coverage,
        ),
        {
            "pass": "local_memory_schema_plan_prepared",
            "watch": "local_memory_schema_plan_review_required",
            "block": "local_memory_schema_plan_blocked",
        }[public_status],
    ]
    return tuple(code for code in ROW_REASON_CODES if code in codes)


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


def _report_status(rows: tuple[ResearchLocalMemorySchemaPlanRow, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.public_status == "block" for row in rows):
        return "block"
    if any(row.public_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchLocalMemorySchemaPlanRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_local_memory_schema_inputs_supplied",)
    codes: list[str] = []
    if any(row.public_status == "pass" for row in rows):
        codes.append("local_memory_schema_plans_prepared")
    if any(row.public_status == "watch" for row in rows):
        codes.append("local_memory_schema_plans_review_required")
    if any(row.public_status == "block" for row in rows):
        codes.append("local_memory_schema_plans_blocked")
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _average_readiness_score(
    rows: tuple[ResearchLocalMemorySchemaPlanRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        total = sum((row.readiness_score for row in rows), ZERO_SCORE)
        value = total / Decimal(len(rows))
    return _require_score_decimal(
        "average_readiness_score",
        value.quantize(SCORE_QUANTUM),
    )


def _status_count(
    rows: tuple[ResearchLocalMemorySchemaPlanRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.public_status == status)


def _action_count(
    rows: tuple[ResearchLocalMemorySchemaPlanRow, ...],
    action: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.schema_plan_action == action))


def _normalize_inputs(value: object) -> tuple[ResearchLocalMemorySchemaPlanInput, ...]:
    if type(value) is not tuple:
        raise ValueError("inputs must be a tuple")
    seen_digests: set[str] = set()
    for input_row in value:
        if type(input_row) is not ResearchLocalMemorySchemaPlanInput:
            raise ValueError("inputs must contain ResearchLocalMemorySchemaPlanInput values")
        _require_hard_flags("input", input_row)
        if input_row.schema_digest in seen_digests:
            raise ValueError("duplicate schema_digest values are not allowed")
        seen_digests.add(input_row.schema_digest)
    return value


def _normalize_rows(value: object) -> tuple[ResearchLocalMemorySchemaPlanRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_keys: set[str] = set()
    for row in value:
        if type(row) is not ResearchLocalMemorySchemaPlanRow:
            raise ValueError("rows must contain ResearchLocalMemorySchemaPlanRow values")
        _require_hard_flags("row", row)
        if row.schema_key in seen_keys:
            raise ValueError("duplicate schema_key values are not allowed")
        seen_keys.add(row.schema_key)
    if value != tuple(sorted(value, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return value


def _normalize_field_groups(
    memory_scope: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("field_groups must be a tuple")
    expected = FIELD_GROUPS_BY_SCOPE[memory_scope]
    if value != expected:
        raise ValueError("field_groups must match memory_scope")
    for field_group in value:
        _require_public_string("field_groups", field_group)
        _reject_unsafe_text("field_groups", field_group, key_mode=False)
    return value


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    unique_values = frozenset(value)
    if len(unique_values) != len(value):
        raise ValueError("reason_codes must not contain duplicates")
    for code in value:
        _require_member("reason_code", code, ROW_REASON_CODES)
    return tuple(code for code in ROW_REASON_CODES if code in unique_values)


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    unique_values = frozenset(value)
    if len(unique_values) != len(value):
        raise ValueError("reason_codes must not contain duplicates")
    for code in value:
        _require_member("reason_code", code, REPORT_REASON_CODES)
    return tuple(code for code in REPORT_REASON_CODES if code in unique_values)


def _validate_row(row: ResearchLocalMemorySchemaPlanRow) -> None:
    if row.schema_plan_action != _schema_plan_action(row.public_status):
        raise ValueError("schema_plan_action must match public_status")
    if row.prepare_schema != (row.public_status == "pass"):
        raise ValueError("prepare_schema must match public_status")
    expected_reason_codes = _row_reason_codes(
        ResearchLocalMemorySchemaPlanInput(
            schema_digest="0" * 64,
            memory_scope=row.memory_scope,
            redaction_coverage=row.redaction_coverage,
            lineage_coverage=row.lineage_coverage,
            review_coverage=row.review_coverage,
            sanitized_schema_notes=row.sanitized_schema_notes,
        ),
        row.public_status,
        ResearchLocalMemorySchemaPlanConfig(),
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row fields")


def _validate_report(report: ResearchLocalMemorySchemaPlanReport) -> None:
    if report.schema_count != _count(len(report.rows)):
        raise ValueError("schema_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.prepare_schema_count != _action_count(
        report.rows,
        "prepare_redacted_schema_plan",
    ):
        raise ValueError("prepare_schema_count must match rows")
    if report.review_count != _action_count(
        report.rows,
        "hold_redacted_schema_plan_for_review",
    ):
        raise ValueError("review_count must match rows")
    if report.suppress_count != _action_count(
        report.rows,
        "suppress_redacted_schema_plan",
    ):
        raise ValueError("suppress_count must match rows")
    if report.average_readiness_score != _average_readiness_score(report.rows):
        raise ValueError("average_readiness_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")


def _validate_payload_fields(payload: dict[str, Any]) -> None:
    if frozenset(payload) != PAYLOAD_FIELDS:
        raise ValueError("payload contains unsupported fields")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain JSON objects")
        if frozenset(row) != ROW_PAYLOAD_FIELDS:
            raise ValueError("payload row contains unsupported fields")


def _require_threshold_order(
    field_name: str,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> None:
    if pass_threshold <= watch_threshold:
        raise ValueError(f"min_pass_{field_name} must exceed watch threshold")


def _require_digest_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    _reject_unsafe_text(field_name, value, key_mode=False)
    return value


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    _require_public_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _require_status(field_name: str, value: object) -> str:
    return _require_member(field_name, value, PUBLIC_STATUSES)


def _require_decimal(field_name: str, value: object, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(quantum)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    return decimal_value


def _require_score_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value, SCORE_QUANTUM)
    if decimal_value < ZERO_SCORE or decimal_value > ONE_SCORE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value, COUNT_QUANTUM)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} must keep {flag_name}=True")


def _reject_unsafe_public_payload(
    field_name: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{field_name} has unsafe public key")
            _reject_unsafe_text(f"{field_name}.{key}", key, key_mode=True)
            _reject_unsafe_public_payload(
                f"{field_name}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers and isinstance(value, list):
            raise ValueError(f"{field_name} has unsafe public list")
        for item in value:
            _reject_unsafe_public_payload(
                field_name,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_text(field_name, value, key_mode=False)
        return
    if type(value) in (Decimal, bool) or value is None:
        return
    raise ValueError(f"{field_name} has unsupported public value")


def _reject_unsafe_text(field_name: str, value: str, *, key_mode: bool) -> None:
    lowered = value.lower()
    fragments = (
        UNSAFE_PUBLIC_KEY_FRAGMENTS if key_mode else UNSAFE_PUBLIC_TEXT_FRAGMENTS
    )
    if any(fragment in lowered for fragment in fragments):
        raise ValueError(f"{field_name} contains unsafe public material")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if type(value) in (str, bool):
        return value
    if type(value) is int:
        raise ValueError("JSON payload must not expose int values")
    if type(value) is float:
        raise ValueError("JSON payload must not expose float values")
    if type(value) is dict:
        return _json_dict_ready(value)
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _json_dict_ready(value: dict[Any, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        ready[key] = _json_ready(item)
    return ready
