"""Pure report-only research source collection runbook.

This module accepts caller-supplied, already-redacted scope, registry,
freshness, and audit trail controls. It returns deterministic collection
runbook steps only. It does not retrieve data, write data, or execute any
market operation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_COLLECTION_RUNBOOK_CONFIG_VERSION = (
    "research-source-collection-runbook-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64

STATUSES = ("pass", "watch", "block")
SOURCE_CATEGORIES = (
    "analysis",
    "community",
    "data_vendor",
    "news",
    "official",
    "regulator",
    "regulatory",
    "venue",
)
AUDIT_TRAIL_STATES = ("complete", "partial", "missing")
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")

STEP_CODES = (
    "verify_public_scope_control",
    "confirm_registry_control",
    "check_freshness_control",
    "review_audit_trail_control",
    "prepare_readonly_collection_notes",
    "complete_watch_review",
    "hold_collection_controls",
)
STEP_DETAILS = {
    "verify_public_scope_control": "Verify deidentified scope control",
    "confirm_registry_control": "Confirm redacted registry control",
    "check_freshness_control": "Check freshness control",
    "review_audit_trail_control": "Review audit trail control",
    "prepare_readonly_collection_notes": "Prepare readonly research collection notes",
    "complete_watch_review": "Complete watch review before collection",
    "hold_collection_controls": "Hold collection until controls clear",
}
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}

NO_INPUTS_REASON = "collection_runbook_no_inputs"
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_candidate",
    "raw-candidate",
    "candidate_id",
    "candidate id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "question",
    "source_ref",
    "source ref",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "recommendation",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "://",
    "auth",
    "candidate id",
    "candidate_id",
    "dsn",
    "market id",
    "market slug",
    "market-",
    "market_id",
    "market_slug",
    "order",
    "position",
    "question",
    "raw candidate",
    "raw-candidate",
    "recommend",
    "source ref",
    "source text",
    "source url",
    "source_ref",
    "source_text",
    "source_url",
    "table",
    "token",
    "trade",
    "wallet",
    "www.",
)
UNSAFE_PUBLIC_WORDS = ("buy", "sell")

_REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "config_version",
        "collection_status",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "step_count",
        "rows",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_FIELDS = frozenset(
    (
        "runbook_rank",
        "collection_scope",
        "registry_key",
        "source_category",
        "scope_status",
        "registry_status",
        "freshness_status",
        "freshness_age_seconds",
        "audit_trail_state",
        "audit_event_count",
        "collection_status",
        "runbook_steps",
        "reason_codes",
        "runbook_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_STEP_PAYLOAD_FIELDS = frozenset(
    (
        "step_rank",
        "step_code",
        "step_status",
        "step_detail",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

__all__ = (
    "AUDIT_TRAIL_STATES",
    "DEFAULT_RESEARCH_SOURCE_COLLECTION_RUNBOOK_CONFIG_VERSION",
    "ResearchSourceCollectionRunbookConfig",
    "ResearchSourceCollectionRunbookInput",
    "ResearchSourceCollectionRunbookReport",
    "ResearchSourceCollectionRunbookRow",
    "ResearchSourceCollectionRunbookStep",
    "SOURCE_CATEGORIES",
    "STATUSES",
    "build_research_source_collection_runbook",
    "research_source_collection_runbook_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchSourceCollectionRunbookConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_SOURCE_COLLECTION_RUNBOOK_CONFIG_VERSION
    min_pass_audit_event_count: Decimal = Decimal("2.000000")
    min_watch_audit_event_count: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceCollectionRunbookConfig, "config")
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SOURCE_COLLECTION_RUNBOOK_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "min_pass_audit_event_count",
            _normalize_positive_count(
                "min_pass_audit_event_count",
                self.min_pass_audit_event_count,
            ),
        )
        object.__setattr__(
            self,
            "min_watch_audit_event_count",
            _normalize_nonnegative_count(
                "min_watch_audit_event_count",
                self.min_watch_audit_event_count,
            ),
        )
        if self.min_watch_audit_event_count >= self.min_pass_audit_event_count:
            raise ValueError(
                "min_watch_audit_event_count must be below min_pass_audit_event_count",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", asdict(self))


@dataclass(frozen=True)
class ResearchSourceCollectionRunbookInput(_FinalPublicDataclass):
    collection_scope: str
    registry_key: str
    source_category: str
    scope_status: str
    registry_status: str
    freshness_status: str
    freshness_age_seconds: Decimal | None
    audit_trail_state: str
    audit_event_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceCollectionRunbookInput, "input")
        for field_name in ("collection_scope", "registry_key"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_category",
            _require_member("source_category", self.source_category, SOURCE_CATEGORIES),
        )
        for field_name in ("scope_status", "registry_status", "freshness_status"):
            object.__setattr__(
                self,
                field_name,
                _require_member(field_name, getattr(self, field_name), STATUSES),
            )
        object.__setattr__(
            self,
            "freshness_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "freshness_age_seconds",
                self.freshness_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "audit_trail_state",
            _require_member(
                "audit_trail_state",
                self.audit_trail_state,
                AUDIT_TRAIL_STATES,
            ),
        )
        object.__setattr__(
            self,
            "audit_event_count",
            _normalize_nonnegative_count("audit_event_count", self.audit_event_count),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", asdict(self))


@dataclass(frozen=True)
class ResearchSourceCollectionRunbookStep(_FinalPublicDataclass):
    step_rank: Decimal
    step_code: str
    step_status: str
    step_detail: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceCollectionRunbookStep, "step")
        object.__setattr__(
            self,
            "step_rank",
            _normalize_positive_count("step_rank", self.step_rank),
        )
        object.__setattr__(
            self,
            "step_code",
            _require_member("step_code", self.step_code, STEP_CODES),
        )
        object.__setattr__(
            self,
            "step_status",
            _require_member("step_status", self.step_status, STATUSES),
        )
        _require_public_string("step_detail", self.step_detail)
        if self.step_detail != STEP_DETAILS[self.step_code]:
            raise ValueError("step_detail must match step_code")
        _require_hard_flags("step", self)
        _reject_unsafe_public_payload("step", asdict(self))


@dataclass(frozen=True)
class ResearchSourceCollectionRunbookRow(_FinalPublicDataclass):
    runbook_rank: Decimal
    collection_scope: str
    registry_key: str
    source_category: str
    scope_status: str
    registry_status: str
    freshness_status: str
    freshness_age_seconds: Decimal | None
    audit_trail_state: str
    audit_event_count: Decimal
    collection_status: str
    runbook_steps: tuple[ResearchSourceCollectionRunbookStep, ...]
    reason_codes: tuple[str, ...]
    runbook_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceCollectionRunbookRow, "row")
        object.__setattr__(
            self,
            "runbook_rank",
            _normalize_positive_count("runbook_rank", self.runbook_rank),
        )
        for field_name in ("collection_scope", "registry_key"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_category",
            _require_member("source_category", self.source_category, SOURCE_CATEGORIES),
        )
        for field_name in (
            "scope_status",
            "registry_status",
            "freshness_status",
            "collection_status",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_member(field_name, getattr(self, field_name), STATUSES),
            )
        object.__setattr__(
            self,
            "freshness_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "freshness_age_seconds",
                self.freshness_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "audit_trail_state",
            _require_member(
                "audit_trail_state",
                self.audit_trail_state,
                AUDIT_TRAIL_STATES,
            ),
        )
        object.__setattr__(
            self,
            "audit_event_count",
            _normalize_nonnegative_count("audit_event_count", self.audit_event_count),
        )
        object.__setattr__(self, "runbook_steps", _normalize_steps(self.runbook_steps))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if not self.reason_codes:
            raise ValueError("reason_codes must not be empty")
        if self.collection_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("collection_status must match reason_codes")
        for step in self.runbook_steps:
            if step.step_status != self.collection_status:
                raise ValueError("runbook step statuses must match row status")
        if self.runbook_digest == "":
            object.__setattr__(self, "runbook_digest", _row_digest(self))
        else:
            _require_digest("runbook_digest", self.runbook_digest)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", asdict(self))


@dataclass(frozen=True)
class ResearchSourceCollectionRunbookReport(_FinalPublicDataclass):
    config_version: str
    collection_status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    step_count: Decimal
    rows: tuple[ResearchSourceCollectionRunbookRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceCollectionRunbookReport, "report")
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SOURCE_COLLECTION_RUNBOOK_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "collection_status",
            _require_member("collection_status", self.collection_status, STATUSES),
        )
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "step_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if not self.reason_codes:
            raise ValueError("reason_codes must not be empty")
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", asdict(self))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _derived_validation_digest(self),
            )
        else:
            _require_digest(DERIVED_VALIDATION_DIGEST_FIELD, self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest must match report")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("runbook payload must be an object")
        _validate_payload_fields(payload)
        _require_hard_flags("payload", _DictFlags(payload))
        _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
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


def build_research_source_collection_runbook(
    inputs: object,
    *,
    config: ResearchSourceCollectionRunbookConfig | None = None,
) -> ResearchSourceCollectionRunbookReport:
    if config is None:
        config = ResearchSourceCollectionRunbookConfig()
    if type(config) is not ResearchSourceCollectionRunbookConfig:
        raise ValueError("config must be a ResearchSourceCollectionRunbookConfig")
    _require_hard_flags("config", config)
    input_items = _normalize_inputs(inputs)
    unranked_rows = tuple(_row_from_input(item, config=config) for item in input_items)
    rows = tuple(
        _ranked_row(row, rank=index)
        for index, row in enumerate(sorted(unranked_rows, key=_row_sort_key), start=1)
    )
    status = _rollup_status(rows)
    return ResearchSourceCollectionRunbookReport(
        config_version=config.config_version,
        collection_status=status,
        input_count=_count(len(input_items)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        step_count=_count(sum(len(row.runbook_steps) for row in rows)),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_source_collection_runbook_payload(
    report: ResearchSourceCollectionRunbookReport | dict[str, Any],
) -> dict[str, object]:
    if type(report) is ResearchSourceCollectionRunbookReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        payload = report.payload
    elif type(report) is dict:
        _validate_payload_fields(report)
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchSourceCollectionRunbookReport")
    if type(payload) is not dict:
        raise ValueError("runbook payload must be an object")
    _validate_payload_fields(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


def _row_from_input(
    value: ResearchSourceCollectionRunbookInput,
    *,
    config: ResearchSourceCollectionRunbookConfig,
) -> ResearchSourceCollectionRunbookRow:
    reason_codes = _row_reason_codes(value, config=config)
    status = _status_from_reason_codes(reason_codes)
    return ResearchSourceCollectionRunbookRow(
        runbook_rank=ONE,
        collection_scope=value.collection_scope,
        registry_key=value.registry_key,
        source_category=value.source_category,
        scope_status=value.scope_status,
        registry_status=value.registry_status,
        freshness_status=value.freshness_status,
        freshness_age_seconds=value.freshness_age_seconds,
        audit_trail_state=value.audit_trail_state,
        audit_event_count=value.audit_event_count,
        collection_status=status,
        runbook_steps=_runbook_steps(status),
        reason_codes=reason_codes,
    )


def _ranked_row(
    row: ResearchSourceCollectionRunbookRow,
    *,
    rank: int,
) -> ResearchSourceCollectionRunbookRow:
    return ResearchSourceCollectionRunbookRow(
        runbook_rank=_count(rank),
        collection_scope=row.collection_scope,
        registry_key=row.registry_key,
        source_category=row.source_category,
        scope_status=row.scope_status,
        registry_status=row.registry_status,
        freshness_status=row.freshness_status,
        freshness_age_seconds=row.freshness_age_seconds,
        audit_trail_state=row.audit_trail_state,
        audit_event_count=row.audit_event_count,
        collection_status=row.collection_status,
        runbook_steps=row.runbook_steps,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    value: ResearchSourceCollectionRunbookInput,
    *,
    config: ResearchSourceCollectionRunbookConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if value.scope_status == "block":
        reason_codes.append("scope_control_block")
    elif value.scope_status == "watch":
        reason_codes.append("scope_control_watch")
    if value.registry_status == "block":
        reason_codes.append("registry_control_block")
    elif value.registry_status == "watch":
        reason_codes.append("registry_control_watch")
    if value.freshness_status == "block":
        reason_codes.append("freshness_control_block")
    elif value.freshness_status == "watch":
        reason_codes.append("freshness_control_watch")
    if value.audit_trail_state == "missing":
        reason_codes.append("audit_trail_missing_block")
    elif value.audit_trail_state == "partial":
        reason_codes.append("audit_trail_partial_watch")
    if value.audit_event_count < config.min_watch_audit_event_count:
        reason_codes.append("audit_event_count_missing_block")
    elif value.audit_event_count < config.min_pass_audit_event_count:
        reason_codes.append("audit_event_count_low_watch")
    if not reason_codes:
        reason_codes.append("collection_controls_ready")
    return tuple(sorted(reason_codes))


def _runbook_steps(status: str) -> tuple[ResearchSourceCollectionRunbookStep, ...]:
    step_codes = [
        "verify_public_scope_control",
        "confirm_registry_control",
        "check_freshness_control",
        "review_audit_trail_control",
    ]
    if status == "pass":
        step_codes.append("prepare_readonly_collection_notes")
    elif status == "watch":
        step_codes.append("complete_watch_review")
    elif status == "block":
        step_codes.append("hold_collection_controls")
    else:
        raise ValueError("status must be known")
    return tuple(
        ResearchSourceCollectionRunbookStep(
            step_rank=_count(index),
            step_code=step_code,
            step_status=status,
            step_detail=STEP_DETAILS[step_code],
        )
        for index, step_code in enumerate(step_codes, start=1)
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(rows: tuple[ResearchSourceCollectionRunbookRow, ...]) -> str:
    if not rows:
        return "block"
    statuses = tuple(row.collection_status for row in rows)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceCollectionRunbookRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(rows)
    if status == "pass":
        return ("collection_runbook_pass",)
    row_reason_codes = sorted(
        {
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if reason_code != "collection_controls_ready"
        },
    )
    return tuple(row_reason_codes + [f"collection_runbook_{status}"])


def _row_sort_key(
    row: ResearchSourceCollectionRunbookRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        -STATUS_WEIGHT[row.collection_status],
        -(row.freshness_age_seconds if row.freshness_age_seconds is not None else ZERO),
        row.collection_scope,
        row.registry_key,
        row.runbook_digest,
    )


def _status_count(
    rows: tuple[ResearchSourceCollectionRunbookRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.collection_status == status))


def _normalize_inputs(inputs: object) -> tuple[ResearchSourceCollectionRunbookInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for value in values:
        if type(value) is not ResearchSourceCollectionRunbookInput:
            raise ValueError(
                "inputs must contain ResearchSourceCollectionRunbookInput values",
            )
        _require_hard_flags("input", value)
        key = (value.collection_scope, value.registry_key)
        if key in seen:
            raise ValueError("inputs must be unique by collection_scope and registry_key")
        seen.add(key)
    return values


def _normalize_steps(
    steps: object,
) -> tuple[ResearchSourceCollectionRunbookStep, ...]:
    if isinstance(steps, (str, bytes)):
        raise ValueError("runbook_steps must be an iterable")
    try:
        values = tuple(steps)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("runbook_steps must be an iterable") from exc
    if not values:
        raise ValueError("runbook_steps must not be empty")
    expected_rank = ONE
    for step in values:
        if type(step) is not ResearchSourceCollectionRunbookStep:
            raise ValueError(
                "runbook_steps must contain ResearchSourceCollectionRunbookStep values",
            )
        _require_hard_flags("step", step)
        if step.step_rank != expected_rank:
            raise ValueError("runbook_steps must use canonical ranks")
        expected_rank = _count(int(expected_rank) + 1)
    return values


def _normalize_rows(rows: object) -> tuple[ResearchSourceCollectionRunbookRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in values:
        if type(row) is not ResearchSourceCollectionRunbookRow:
            raise ValueError("rows must contain ResearchSourceCollectionRunbookRow values")
        _require_hard_flags("row", row)
        if row.runbook_digest in seen:
            raise ValueError("rows must not contain duplicate runbook_digest values")
        seen.add(row.runbook_digest)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reason_codes: list[str] = []
    for item in value:
        _require_public_string(field_name, item)
        reason_codes.append(item)
    normalized = tuple(dict.fromkeys(reason_codes))
    if len(normalized) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _validate_report(report: ResearchSourceCollectionRunbookReport) -> None:
    rows = report.rows
    if report.input_count != _count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.step_count != _count(sum(len(row.runbook_steps) for row in rows)):
        raise ValueError("step_count must match rows")
    if report.collection_status != _rollup_status(rows):
        raise ValueError("collection_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_payload_fields(payload: dict[str, Any]) -> None:
    if frozenset(payload) != _REPORT_PAYLOAD_FIELDS:
        raise ValueError("payload fields are unsupported")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must be objects")
        if frozenset(row) != _ROW_PAYLOAD_FIELDS:
            raise ValueError("payload row fields are unsupported")
        steps = row.get("runbook_steps")
        if not isinstance(steps, list):
            raise ValueError("payload runbook_steps must be a list")
        for step in steps:
            if type(step) is not dict:
                raise ValueError("payload runbook_steps must be objects")
            if frozenset(step) != _STEP_PAYLOAD_FIELDS:
                raise ValueError("payload step fields are unsupported")


def _row_digest(value: ResearchSourceCollectionRunbookRow) -> str:
    digest_source = "|".join(
        (
            str(value.runbook_rank),
            value.collection_scope,
            value.registry_key,
            value.source_category,
            value.scope_status,
            value.registry_status,
            value.freshness_status,
            str(value.freshness_age_seconds),
            value.audit_trail_state,
            str(value.audit_event_count),
            value.collection_status,
            ",".join(step.step_code for step in value.runbook_steps),
            ",".join(value.reason_codes),
        ),
    )
    return sha256(digest_source.encode("utf-8")).hexdigest()


def _derived_validation_digest(
    report: ResearchSourceCollectionRunbookReport,
) -> str:
    payload = asdict(report)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = ""
    safe_payload = _json_ready(payload)
    encoded = json.dumps(safe_payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for char in value:
        if char not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be a known value")
    return value


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    _reject_unsafe_public_text(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(DECIMAL_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a finite Decimal") from exc
    if normalized != value:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(DECIMAL_QUANTUM)


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError(f"unsupported payload value {value!r}")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, tuple) or (allow_json_containers and isinstance(value, list)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, list):
        raise ValueError(f"{label} contains unsupported public payload container")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if value is None or type(value) in (Decimal, bool):
        return
    raise ValueError(f"{label} contains unsupported public payload value")


def _reject_unsafe_public_key(label: str, key: object) -> None:
    if type(key) is not str:
        raise ValueError(f"{label} public payload keys must be strings")
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public payload key")


def _reject_unsafe_public_text(label: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public payload text")
    normalized = lowered.replace("_", " ").replace("-", " ").replace("/", " ")
    padded = f" {normalized} "
    if any(f" {word} " in padded for word in UNSAFE_PUBLIC_WORDS):
        raise ValueError(f"{label} contains unsafe public payload text")
