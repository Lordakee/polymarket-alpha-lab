"""Pure report-only local research write-plan model.

The module prepares deterministic, redacted plans for local persistence surfaces.
It does not connect to a database, expose storage identifiers, or execute writes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "RESEARCH_LOCAL_SUPABASE_WRITE_PLAN_CONFIG_VERSION",
    "ResearchLocalSupabaseWritePlanConfig",
    "ResearchLocalSupabaseWritePlanItem",
    "ResearchLocalSupabaseWritePlanReport",
    "ResearchLocalSupabaseWritePlanRow",
    "build_research_local_supabase_write_plan",
    "research_local_supabase_write_plan_payload",
)


RESEARCH_LOCAL_SUPABASE_WRITE_PLAN_CONFIG_VERSION = (
    "research-local-supabase-write-plan-v0"
)
WRITE_PLAN_MODE = "report_only_redacted_local_research_write_plan"

PLAN_SCOPES = (
    "long_term_memory",
    "source_registry",
    "postmortem_summary",
)
PUBLIC_STATUSES = ("pass", "watch", "block")
WRITE_PLAN_ACTIONS = (
    "prepare_redacted_local_record",
    "hold_redacted_local_record_for_review",
    "suppress_redacted_local_record",
)

ROW_REASON_CODES = (
    "long_term_memory_scope",
    "source_registry_scope",
    "postmortem_summary_scope",
    "evidence_quality_pass",
    "evidence_quality_watch",
    "evidence_quality_block",
    "redaction_quality_pass",
    "redaction_quality_watch",
    "redaction_quality_block",
    "review_completeness_pass",
    "review_completeness_watch",
    "review_completeness_block",
    "local_write_plan_prepared",
    "local_write_plan_review_required",
    "local_write_plan_block",
)
REPORT_REASON_CODES = (
    "no_write_plan_items_supplied",
    "local_write_plans_prepared",
    "local_write_plans_review_required",
    "local_write_plans_blocked",
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
        "write_plan_mode",
        "report_status",
        "item_count",
        "pass_count",
        "watch_count",
        "block_count",
        "prepare_write_count",
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
        "plan_rank",
        "plan_key",
        "plan_scope",
        "public_status",
        "write_plan_action",
        "prepare_write",
        "evidence_quality",
        "redaction_quality",
        "review_completeness",
        "readiness_score",
        "sanitized_summary",
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
    "service_role",
    "source_ref",
    "source_text",
    "source_url",
    "table",
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
    "wallet",
    "www.",
    "://",
)


@dataclass(frozen=True)
class ResearchLocalSupabaseWritePlanConfig:
    config_version: str = RESEARCH_LOCAL_SUPABASE_WRITE_PLAN_CONFIG_VERSION
    min_pass_evidence_quality: Decimal = Decimal("0.750000")
    min_watch_evidence_quality: Decimal = Decimal("0.500000")
    min_pass_redaction_quality: Decimal = Decimal("0.900000")
    min_watch_redaction_quality: Decimal = Decimal("0.700000")
    min_pass_review_completeness: Decimal = Decimal("0.800000")
    min_watch_review_completeness: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchLocalSupabaseWritePlanConfig:
            raise TypeError(
                "ResearchLocalSupabaseWritePlanConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchLocalSupabaseWritePlanConfig:
            raise ValueError(
                "config must be exactly ResearchLocalSupabaseWritePlanConfig",
            )
        _require_public_string("config_version", self.config_version)
        if self.config_version != RESEARCH_LOCAL_SUPABASE_WRITE_PLAN_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_evidence_quality",
            "min_watch_evidence_quality",
            "min_pass_redaction_quality",
            "min_watch_redaction_quality",
            "min_pass_review_completeness",
            "min_watch_review_completeness",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_order(
            "evidence_quality",
            self.min_pass_evidence_quality,
            self.min_watch_evidence_quality,
        )
        _require_threshold_order(
            "redaction_quality",
            self.min_pass_redaction_quality,
            self.min_watch_redaction_quality,
        )
        _require_threshold_order(
            "review_completeness",
            self.min_pass_review_completeness,
            self.min_watch_review_completeness,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchLocalSupabaseWritePlanItem:
    item_digest: str
    plan_scope: str
    evidence_quality: Decimal
    redaction_quality: Decimal
    review_completeness: Decimal
    sanitized_summary: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchLocalSupabaseWritePlanItem:
            raise TypeError(
                "ResearchLocalSupabaseWritePlanItem does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchLocalSupabaseWritePlanItem:
            raise ValueError("item must be exactly ResearchLocalSupabaseWritePlanItem")
        object.__setattr__(
            self,
            "item_digest",
            _require_digest_string("item_digest", self.item_digest),
        )
        object.__setattr__(
            self,
            "plan_scope",
            _require_member("plan_scope", self.plan_scope, PLAN_SCOPES),
        )
        for field_name in (
            "evidence_quality",
            "redaction_quality",
            "review_completeness",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_string("sanitized_summary", self.sanitized_summary)
        _require_hard_flags("item", self)
        _reject_unsafe_public_payload("item", self)


@dataclass(frozen=True)
class ResearchLocalSupabaseWritePlanRow:
    plan_rank: Decimal
    plan_key: str
    plan_scope: str
    public_status: str
    write_plan_action: str
    prepare_write: bool
    evidence_quality: Decimal
    redaction_quality: Decimal
    review_completeness: Decimal
    readiness_score: Decimal
    sanitized_summary: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchLocalSupabaseWritePlanRow:
            raise TypeError(
                "ResearchLocalSupabaseWritePlanRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchLocalSupabaseWritePlanRow:
            raise ValueError("row must be exactly ResearchLocalSupabaseWritePlanRow")
        object.__setattr__(
            self,
            "plan_rank",
            _require_positive_count_decimal("plan_rank", self.plan_rank),
        )
        _require_public_string("plan_key", self.plan_key)
        object.__setattr__(
            self,
            "plan_scope",
            _require_member("plan_scope", self.plan_scope, PLAN_SCOPES),
        )
        object.__setattr__(
            self,
            "public_status",
            _require_status("public_status", self.public_status),
        )
        object.__setattr__(
            self,
            "write_plan_action",
            _require_member(
                "write_plan_action",
                self.write_plan_action,
                WRITE_PLAN_ACTIONS,
            ),
        )
        if type(self.prepare_write) is not bool:
            raise ValueError("prepare_write must be a bool")
        for field_name in (
            "evidence_quality",
            "redaction_quality",
            "review_completeness",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_string("sanitized_summary", self.sanitized_summary)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchLocalSupabaseWritePlanReport:
    config_version: str
    write_plan_mode: str
    report_status: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    prepare_write_count: Decimal
    review_count: Decimal
    suppress_count: Decimal
    average_readiness_score: Decimal
    rows: tuple[ResearchLocalSupabaseWritePlanRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchLocalSupabaseWritePlanReport:
            raise TypeError(
                "ResearchLocalSupabaseWritePlanReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchLocalSupabaseWritePlanReport:
            raise ValueError("report must be exactly ResearchLocalSupabaseWritePlanReport")
        _require_public_string("config_version", self.config_version)
        if self.config_version != RESEARCH_LOCAL_SUPABASE_WRITE_PLAN_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_public_string("write_plan_mode", self.write_plan_mode)
        if self.write_plan_mode != WRITE_PLAN_MODE:
            raise ValueError("write_plan_mode must be report-only and redacted")
        object.__setattr__(
            self,
            "report_status",
            _require_status("report_status", self.report_status),
        )
        for field_name in (
            "item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "prepare_write_count",
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


def build_research_local_supabase_write_plan(
    items: tuple[ResearchLocalSupabaseWritePlanItem, ...],
    *,
    config: ResearchLocalSupabaseWritePlanConfig | None = None,
) -> ResearchLocalSupabaseWritePlanReport:
    cfg = config or ResearchLocalSupabaseWritePlanConfig()
    if type(cfg) is not ResearchLocalSupabaseWritePlanConfig:
        raise ValueError("config must be a ResearchLocalSupabaseWritePlanConfig")
    _require_hard_flags("config", cfg)
    input_items = _normalize_items(items)
    sorted_items = tuple(sorted(input_items, key=_item_sort_key))
    rows = tuple(
        _build_row(index=index, item=item, config=cfg)
        for index, item in enumerate(sorted_items, start=1)
    )
    return ResearchLocalSupabaseWritePlanReport(
        config_version=cfg.config_version,
        write_plan_mode=WRITE_PLAN_MODE,
        report_status=_report_status(rows),
        item_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        prepare_write_count=_action_count(rows, "prepare_redacted_local_record"),
        review_count=_action_count(rows, "hold_redacted_local_record_for_review"),
        suppress_count=_action_count(rows, "suppress_redacted_local_record"),
        average_readiness_score=_average_readiness_score(rows),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_local_supabase_write_plan_payload(
    report: ResearchLocalSupabaseWritePlanReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchLocalSupabaseWritePlanReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        _validate_payload_fields(report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchLocalSupabaseWritePlanReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_payload_fields(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


def _build_row(
    *,
    index: int,
    item: ResearchLocalSupabaseWritePlanItem,
    config: ResearchLocalSupabaseWritePlanConfig,
) -> ResearchLocalSupabaseWritePlanRow:
    status = _item_status(item, config)
    action = _write_plan_action(status)
    return ResearchLocalSupabaseWritePlanRow(
        plan_rank=_count(index),
        plan_key=f"redacted-local-write-plan-{index:03d}",
        plan_scope=item.plan_scope,
        public_status=status,
        write_plan_action=action,
        prepare_write=action == "prepare_redacted_local_record",
        evidence_quality=item.evidence_quality,
        redaction_quality=item.redaction_quality,
        review_completeness=item.review_completeness,
        readiness_score=_readiness_score(item),
        sanitized_summary=item.sanitized_summary,
        reason_codes=_row_reason_codes(item, status, config),
    )


def _item_sort_key(item: ResearchLocalSupabaseWritePlanItem) -> tuple[int, str]:
    return (PLAN_SCOPES.index(item.plan_scope), item.item_digest)


def _row_sort_key(row: ResearchLocalSupabaseWritePlanRow) -> tuple[Decimal, str]:
    return (row.plan_rank, row.plan_key)


def _item_status(
    item: ResearchLocalSupabaseWritePlanItem,
    config: ResearchLocalSupabaseWritePlanConfig,
) -> str:
    if (
        item.evidence_quality < config.min_watch_evidence_quality
        or item.redaction_quality < config.min_watch_redaction_quality
        or item.review_completeness < config.min_watch_review_completeness
    ):
        return "block"
    if (
        item.evidence_quality < config.min_pass_evidence_quality
        or item.redaction_quality < config.min_pass_redaction_quality
        or item.review_completeness < config.min_pass_review_completeness
    ):
        return "watch"
    return "pass"


def _write_plan_action(public_status: str) -> str:
    if public_status == "pass":
        return "prepare_redacted_local_record"
    if public_status == "watch":
        return "hold_redacted_local_record_for_review"
    return "suppress_redacted_local_record"


def _readiness_score(item: ResearchLocalSupabaseWritePlanItem) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            item.evidence_quality * Decimal("0.400000")
            + item.redaction_quality * Decimal("0.350000")
            + item.review_completeness * Decimal("0.250000")
        )
    return _require_score_decimal("readiness_score", value)


def _row_reason_codes(
    item: ResearchLocalSupabaseWritePlanItem,
    public_status: str,
    config: ResearchLocalSupabaseWritePlanConfig,
) -> tuple[str, ...]:
    codes = [
        f"{item.plan_scope}_scope",
        _quality_reason(
            "evidence_quality",
            item.evidence_quality,
            config.min_pass_evidence_quality,
            config.min_watch_evidence_quality,
        ),
        _quality_reason(
            "redaction_quality",
            item.redaction_quality,
            config.min_pass_redaction_quality,
            config.min_watch_redaction_quality,
        ),
        _quality_reason(
            "review_completeness",
            item.review_completeness,
            config.min_pass_review_completeness,
            config.min_watch_review_completeness,
        ),
        {
            "pass": "local_write_plan_prepared",
            "watch": "local_write_plan_review_required",
            "block": "local_write_plan_block",
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


def _report_status(rows: tuple[ResearchLocalSupabaseWritePlanRow, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.public_status == "block" for row in rows):
        return "block"
    if any(row.public_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchLocalSupabaseWritePlanRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_write_plan_items_supplied",)
    codes: list[str] = []
    if any(row.public_status == "pass" for row in rows):
        codes.append("local_write_plans_prepared")
    if any(row.public_status == "watch" for row in rows):
        codes.append("local_write_plans_review_required")
    if any(row.public_status == "block" for row in rows):
        codes.append("local_write_plans_blocked")
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _average_readiness_score(
    rows: tuple[ResearchLocalSupabaseWritePlanRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        total = sum((row.readiness_score for row in rows), ZERO_SCORE)
        value = total / Decimal(len(rows))
    return _require_score_decimal("average_readiness_score", value)


def _status_count(
    rows: tuple[ResearchLocalSupabaseWritePlanRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.public_status == status)


def _action_count(
    rows: tuple[ResearchLocalSupabaseWritePlanRow, ...],
    action: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.write_plan_action == action))


def _normalize_items(value: object) -> tuple[ResearchLocalSupabaseWritePlanItem, ...]:
    if type(value) is not tuple:
        raise ValueError("items must be a tuple")
    seen_digests: set[str] = set()
    for item in value:
        if type(item) is not ResearchLocalSupabaseWritePlanItem:
            raise ValueError("items must contain ResearchLocalSupabaseWritePlanItem values")
        _require_hard_flags("item", item)
        if item.item_digest in seen_digests:
            raise ValueError("duplicate item_digest values are not allowed")
        seen_digests.add(item.item_digest)
    return value


def _normalize_rows(value: object) -> tuple[ResearchLocalSupabaseWritePlanRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_keys: set[str] = set()
    for row in value:
        if type(row) is not ResearchLocalSupabaseWritePlanRow:
            raise ValueError("rows must contain ResearchLocalSupabaseWritePlanRow values")
        _require_hard_flags("row", row)
        if row.plan_key in seen_keys:
            raise ValueError("duplicate plan_key values are not allowed")
        seen_keys.add(row.plan_key)
    if value != tuple(sorted(value, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
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


def _validate_row(row: ResearchLocalSupabaseWritePlanRow) -> None:
    if row.write_plan_action != _write_plan_action(row.public_status):
        raise ValueError("write_plan_action must match public_status")
    if row.prepare_write != (row.public_status == "pass"):
        raise ValueError("prepare_write must match public_status")
    expected_reason_codes = _row_reason_codes(
        ResearchLocalSupabaseWritePlanItem(
            item_digest="0" * 64,
            plan_scope=row.plan_scope,
            evidence_quality=row.evidence_quality,
            redaction_quality=row.redaction_quality,
            review_completeness=row.review_completeness,
            sanitized_summary=row.sanitized_summary,
        ),
        row.public_status,
        ResearchLocalSupabaseWritePlanConfig(),
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row fields")


def _validate_report(report: ResearchLocalSupabaseWritePlanReport) -> None:
    if report.item_count != _count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.prepare_write_count != _action_count(
        report.rows,
        "prepare_redacted_local_record",
    ):
        raise ValueError("prepare_write_count must match rows")
    if report.review_count != _action_count(
        report.rows,
        "hold_redacted_local_record_for_review",
    ):
        raise ValueError("review_count must match rows")
    if report.suppress_count != _action_count(
        report.rows,
        "suppress_redacted_local_record",
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
    return value.quantize(quantum)


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
        raise ValueError(f"{field_name} contains unsafe public text")


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value
