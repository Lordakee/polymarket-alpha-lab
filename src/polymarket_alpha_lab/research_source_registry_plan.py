"""Pure report-only research source registry planning policy.

The module accepts caller-supplied, already-redacted source candidates and returns
a deterministic upstream registry write plan. It has no side effects and never
retrieves external data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from typing import Any


__all__ = (
    "ResearchSourceRegistryCandidate",
    "ResearchSourceRegistryCategoryPlan",
    "ResearchSourceRegistryPlanConfig",
    "ResearchSourceRegistryPlanReport",
    "ResearchSourceRegistryPlanRow",
    "build_research_source_registry_plan",
    "research_source_registry_plan_payload",
)


CONFIG_VERSION = "research-source-registry-plan-v0"
UPSTREAM_WRITE_PLAN = "report_only_registry_upsert_plan"

DECIMAL_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
DAILY_REFRESH_MINUTES = Decimal("1440.000000")
WEEKLY_REFRESH_MINUTES = Decimal("10080.000000")

SOURCE_CATEGORIES = (
    "analysis",
    "community",
    "data_vendor",
    "news",
    "official",
    "regulator",
    "venue",
)
AUDIT_TRAIL_STATES = ("complete", "partial", "missing")
STATUSES = ("pass", "watch", "block")
RELIABILITY_TIERS = ("high", "medium", "low")
REFRESH_FREQUENCY_TIERS = ("daily", "weekly", "stale")
HARD_FLAGS = ("paper_only", "report_only", "readonly")

PAYLOAD_FIELDS = frozenset(
    (
        "config_version",
        "upstream_write_plan",
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "status",
        "rows",
        "category_plans",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

ROW_PAYLOAD_FIELDS = frozenset(
    (
        "plan_rank",
        "registry_key",
        "source_category",
        "reliability_score",
        "reliability_tier",
        "refresh_frequency_minutes",
        "refresh_frequency_tier",
        "audit_trail_state",
        "audit_event_count",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

CATEGORY_PAYLOAD_FIELDS = frozenset(
    (
        "source_category",
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

UNSAFE_KEY_FRAGMENTS = (
    "auth",
    "candidate_id",
    "dsn",
    "market_id",
    "market_slug",
    "market_url",
    "order",
    "question",
    "source_ref",
    "source_text",
    "source_url",
    "table",
    "token",
    "trade",
    "wallet",
)

UNSAFE_TEXT_FRAGMENTS = (
    "://",
    "auth",
    "buy",
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
    "sell",
    "source ref",
    "source text",
    "source url",
    "source_ref",
    "source_text",
    "source_url",
    "supabase",
    "table",
    "token",
    "trade",
    "wallet",
    "www.",
)


@dataclass(frozen=True)
class ResearchSourceRegistryPlanConfig:
    config_version: str = CONFIG_VERSION
    min_pass_reliability_score: Decimal = Decimal("0.750000")
    min_watch_reliability_score: Decimal = Decimal("0.500000")
    max_pass_refresh_frequency_minutes: Decimal = DAILY_REFRESH_MINUTES
    max_watch_refresh_frequency_minutes: Decimal = WEEKLY_REFRESH_MINUTES
    min_pass_audit_event_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRegistryPlanConfig:
            raise TypeError("ResearchSourceRegistryPlanConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRegistryPlanConfig:
            raise ValueError("config must be exactly ResearchSourceRegistryPlanConfig")
        _require_public_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_pass_reliability_score",
            _require_probability_decimal(
                "min_pass_reliability_score",
                self.min_pass_reliability_score,
            ),
        )
        object.__setattr__(
            self,
            "min_watch_reliability_score",
            _require_probability_decimal(
                "min_watch_reliability_score",
                self.min_watch_reliability_score,
            ),
        )
        if self.min_pass_reliability_score <= self.min_watch_reliability_score:
            raise ValueError(
                "min_pass_reliability_score must be greater than "
                "min_watch_reliability_score",
            )
        object.__setattr__(
            self,
            "max_pass_refresh_frequency_minutes",
            _require_positive_whole_decimal(
                "max_pass_refresh_frequency_minutes",
                self.max_pass_refresh_frequency_minutes,
            ),
        )
        object.__setattr__(
            self,
            "max_watch_refresh_frequency_minutes",
            _require_positive_whole_decimal(
                "max_watch_refresh_frequency_minutes",
                self.max_watch_refresh_frequency_minutes,
            ),
        )
        if (
            self.max_watch_refresh_frequency_minutes
            <= self.max_pass_refresh_frequency_minutes
        ):
            raise ValueError(
                "max_watch_refresh_frequency_minutes must be greater than "
                "max_pass_refresh_frequency_minutes",
            )
        object.__setattr__(
            self,
            "min_pass_audit_event_count",
            _require_positive_whole_decimal(
                "min_pass_audit_event_count",
                self.min_pass_audit_event_count,
            ),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceRegistryCandidate:
    source_category: str
    reliability_score: Decimal
    refresh_frequency_minutes: Decimal
    audit_trail_state: str
    audit_event_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRegistryCandidate:
            raise TypeError("ResearchSourceRegistryCandidate does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRegistryCandidate:
            raise ValueError("candidate must be exactly ResearchSourceRegistryCandidate")
        object.__setattr__(
            self,
            "source_category",
            _require_member("source_category", self.source_category, SOURCE_CATEGORIES),
        )
        object.__setattr__(
            self,
            "reliability_score",
            _require_probability_decimal("reliability_score", self.reliability_score),
        )
        object.__setattr__(
            self,
            "refresh_frequency_minutes",
            _require_positive_whole_decimal(
                "refresh_frequency_minutes",
                self.refresh_frequency_minutes,
            ),
        )
        object.__setattr__(
            self,
            "audit_trail_state",
            _require_member("audit_trail_state", self.audit_trail_state, AUDIT_TRAIL_STATES),
        )
        object.__setattr__(
            self,
            "audit_event_count",
            _require_nonnegative_whole_decimal(
                "audit_event_count",
                self.audit_event_count,
            ),
        )
        _require_hard_flags("candidate", self)
        _reject_unsafe_public_payload("candidate", self)


@dataclass(frozen=True)
class ResearchSourceRegistryPlanRow:
    plan_rank: Decimal
    registry_key: str
    source_category: str
    reliability_score: Decimal
    reliability_tier: str
    refresh_frequency_minutes: Decimal
    refresh_frequency_tier: str
    audit_trail_state: str
    audit_event_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRegistryPlanRow:
            raise TypeError("ResearchSourceRegistryPlanRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRegistryPlanRow:
            raise ValueError("row must be exactly ResearchSourceRegistryPlanRow")
        object.__setattr__(
            self,
            "plan_rank",
            _require_positive_whole_decimal("plan_rank", self.plan_rank),
        )
        _require_public_string("registry_key", self.registry_key)
        object.__setattr__(
            self,
            "source_category",
            _require_member("source_category", self.source_category, SOURCE_CATEGORIES),
        )
        object.__setattr__(
            self,
            "reliability_score",
            _require_probability_decimal("reliability_score", self.reliability_score),
        )
        object.__setattr__(
            self,
            "reliability_tier",
            _require_member("reliability_tier", self.reliability_tier, RELIABILITY_TIERS),
        )
        object.__setattr__(
            self,
            "refresh_frequency_minutes",
            _require_positive_whole_decimal(
                "refresh_frequency_minutes",
                self.refresh_frequency_minutes,
            ),
        )
        object.__setattr__(
            self,
            "refresh_frequency_tier",
            _require_member(
                "refresh_frequency_tier",
                self.refresh_frequency_tier,
                REFRESH_FREQUENCY_TIERS,
            ),
        )
        object.__setattr__(
            self,
            "audit_trail_state",
            _require_member("audit_trail_state", self.audit_trail_state, AUDIT_TRAIL_STATES),
        )
        object.__setattr__(
            self,
            "audit_event_count",
            _require_nonnegative_whole_decimal(
                "audit_event_count",
                self.audit_event_count,
            ),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceRegistryCategoryPlan:
    source_category: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRegistryCategoryPlan:
            raise TypeError(
                "ResearchSourceRegistryCategoryPlan does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRegistryCategoryPlan:
            raise ValueError("category plan must be exactly ResearchSourceRegistryCategoryPlan")
        object.__setattr__(
            self,
            "source_category",
            _require_member("source_category", self.source_category, SOURCE_CATEGORIES),
        )
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("category plan", self)
        _validate_category_plan_consistency(self)
        _reject_unsafe_public_payload("category plan", self)


@dataclass(frozen=True)
class ResearchSourceRegistryPlanReport:
    config_version: str
    upstream_write_plan: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    rows: tuple[ResearchSourceRegistryPlanRow, ...]
    category_plans: tuple[ResearchSourceRegistryCategoryPlan, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRegistryPlanReport:
            raise TypeError("ResearchSourceRegistryPlanReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRegistryPlanReport:
            raise ValueError("report must be exactly ResearchSourceRegistryPlanReport")
        _require_public_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_public_string("upstream_write_plan", self.upstream_write_plan)
        if self.upstream_write_plan != UPSTREAM_WRITE_PLAN:
            raise ValueError("upstream_write_plan must be report-only")
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "category_plans",
            _normalize_category_plans(self.category_plans),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
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


def build_research_source_registry_plan(
    candidates: tuple[ResearchSourceRegistryCandidate, ...],
    *,
    config: ResearchSourceRegistryPlanConfig,
) -> ResearchSourceRegistryPlanReport:
    if type(config) is not ResearchSourceRegistryPlanConfig:
        raise ValueError("config must be a ResearchSourceRegistryPlanConfig")
    _require_hard_flags("config", config)
    candidate_items = _normalize_candidates(candidates)
    rows = _build_rows(candidate_items, config)
    category_plans = _build_category_plans(rows)
    reason_codes = _report_reason_codes(rows)
    return ResearchSourceRegistryPlanReport(
        config_version=config.config_version,
        upstream_write_plan=UPSTREAM_WRITE_PLAN,
        candidate_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        status=_summary_status(rows),
        rows=rows,
        category_plans=category_plans,
        reason_codes=reason_codes,
    )


def research_source_registry_plan_payload(
    report: ResearchSourceRegistryPlanReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceRegistryPlanReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _validate_payload_fields(report)
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchSourceRegistryPlanReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_payload_fields(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


def _build_rows(
    candidates: tuple[ResearchSourceRegistryCandidate, ...],
    config: ResearchSourceRegistryPlanConfig,
) -> tuple[ResearchSourceRegistryPlanRow, ...]:
    sorted_candidates = tuple(
        sorted(
            candidates,
            key=lambda item: (
                item.source_category,
                -item.reliability_score,
                item.refresh_frequency_minutes,
                item.audit_trail_state,
                -item.audit_event_count,
            ),
        ),
    )
    rows: list[ResearchSourceRegistryPlanRow] = []
    for index, item in enumerate(sorted_candidates, start=1):
        status = _row_status(item, config)
        rows.append(
            ResearchSourceRegistryPlanRow(
                plan_rank=_count(index),
                registry_key=f"redacted-source-registry-{index:03d}",
                source_category=item.source_category,
                reliability_score=item.reliability_score,
                reliability_tier=_reliability_tier(item, config),
                refresh_frequency_minutes=item.refresh_frequency_minutes,
                refresh_frequency_tier=_refresh_frequency_tier(item, config),
                audit_trail_state=item.audit_trail_state,
                audit_event_count=item.audit_event_count,
                status=status,
                reason_codes=_row_reason_codes(item, config, status),
            ),
        )
    return tuple(rows)


def _build_category_plans(
    rows: tuple[ResearchSourceRegistryPlanRow, ...],
) -> tuple[ResearchSourceRegistryCategoryPlan, ...]:
    grouped: dict[str, list[ResearchSourceRegistryPlanRow]] = {}
    for row in rows:
        grouped.setdefault(row.source_category, []).append(row)
    return tuple(
        _category_plan(source_category, tuple(grouped[source_category]))
        for source_category in sorted(grouped)
    )


def _category_plan(
    source_category: str,
    rows: tuple[ResearchSourceRegistryPlanRow, ...],
) -> ResearchSourceRegistryCategoryPlan:
    status = _summary_status(rows)
    return ResearchSourceRegistryCategoryPlan(
        source_category=source_category,
        candidate_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        status=status,
        reason_codes=(f"category_registry_{status}",),
    )


def _row_status(
    item: ResearchSourceRegistryCandidate,
    config: ResearchSourceRegistryPlanConfig,
) -> str:
    if (
        item.reliability_score < config.min_watch_reliability_score
        or item.refresh_frequency_minutes > config.max_watch_refresh_frequency_minutes
        or item.audit_trail_state == "missing"
        or item.audit_event_count == ZERO
    ):
        return "block"
    if (
        item.reliability_score < config.min_pass_reliability_score
        or item.refresh_frequency_minutes > config.max_pass_refresh_frequency_minutes
        or item.audit_trail_state == "partial"
        or item.audit_event_count < config.min_pass_audit_event_count
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchSourceRegistryCandidate,
    config: ResearchSourceRegistryPlanConfig,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.audit_event_count == ZERO:
        reason_codes.append("audit_event_count_missing")
    elif item.audit_event_count < config.min_pass_audit_event_count:
        reason_codes.append("audit_event_count_below_pass_threshold")
    if item.audit_trail_state == "missing":
        reason_codes.append("audit_trail_missing")
    elif item.audit_trail_state == "partial":
        reason_codes.append("audit_trail_partial")
    if item.refresh_frequency_minutes > config.max_watch_refresh_frequency_minutes:
        reason_codes.append("refresh_frequency_above_watch_threshold")
    elif item.refresh_frequency_minutes > config.max_pass_refresh_frequency_minutes:
        reason_codes.append("refresh_frequency_above_pass_threshold")
    if item.reliability_score < config.min_watch_reliability_score:
        reason_codes.append("reliability_below_watch_threshold")
    elif item.reliability_score < config.min_pass_reliability_score:
        reason_codes.append("reliability_below_pass_threshold")
    reason_codes.append(f"registry_plan_{status}")
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[ResearchSourceRegistryPlanRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_registry_candidates", "research_source_registry_plan_block")
    status = _summary_status(rows)
    if status == "pass":
        return ("research_source_registry_plan_pass",)
    return tuple(
        sorted(
            {
                reason_code
                for row in rows
                for reason_code in row.reason_codes
                if reason_code != f"registry_plan_{row.status}"
            },
        )
        + [f"research_source_registry_plan_{status}"],
    )


def _summary_status(rows: tuple[Any, ...]) -> str:
    if not rows:
        return "block"
    statuses = tuple(row.status for row in rows)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _status_count(rows: tuple[Any, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _reliability_tier(
    item: ResearchSourceRegistryCandidate,
    config: ResearchSourceRegistryPlanConfig,
) -> str:
    if item.reliability_score >= config.min_pass_reliability_score:
        return "high"
    if item.reliability_score >= config.min_watch_reliability_score:
        return "medium"
    return "low"


def _refresh_frequency_tier(
    item: ResearchSourceRegistryCandidate,
    config: ResearchSourceRegistryPlanConfig,
) -> str:
    if item.refresh_frequency_minutes <= config.max_pass_refresh_frequency_minutes:
        return "daily"
    if item.refresh_frequency_minutes <= config.max_watch_refresh_frequency_minutes:
        return "weekly"
    return "stale"


def _normalize_candidates(
    candidates: tuple[ResearchSourceRegistryCandidate, ...],
) -> tuple[ResearchSourceRegistryCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        candidate_items = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    for candidate in candidate_items:
        if type(candidate) is not ResearchSourceRegistryCandidate:
            raise ValueError("candidate must be a ResearchSourceRegistryCandidate")
        _require_hard_flags("candidate", candidate)
    return candidate_items


def _normalize_rows(
    rows: tuple[ResearchSourceRegistryPlanRow, ...],
) -> tuple[ResearchSourceRegistryPlanRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        row_items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in row_items:
        if type(row) is not ResearchSourceRegistryPlanRow:
            raise ValueError("row must be a ResearchSourceRegistryPlanRow")
        _require_hard_flags("row", row)
    return row_items


def _normalize_category_plans(
    category_plans: tuple[ResearchSourceRegistryCategoryPlan, ...],
) -> tuple[ResearchSourceRegistryCategoryPlan, ...]:
    if isinstance(category_plans, (str, bytes)):
        raise ValueError("category_plans must be an iterable")
    try:
        category_plan_items = tuple(category_plans)
    except TypeError as exc:
        raise ValueError("category_plans must be an iterable") from exc
    for category_plan in category_plan_items:
        if type(category_plan) is not ResearchSourceRegistryCategoryPlan:
            raise ValueError("category plan must be a ResearchSourceRegistryCategoryPlan")
        _require_hard_flags("category plan", category_plan)
    return category_plan_items


def _validate_row_consistency(row: ResearchSourceRegistryPlanRow) -> None:
    if row.reason_codes[-1:] != (f"registry_plan_{row.status}",):
        raise ValueError("reason_codes must match status")


def _validate_category_plan_consistency(
    category_plan: ResearchSourceRegistryCategoryPlan,
) -> None:
    if (
        category_plan.pass_count
        + category_plan.watch_count
        + category_plan.block_count
        != category_plan.candidate_count
    ):
        raise ValueError("category status counts must match candidate_count")
    if category_plan.reason_codes != (f"category_registry_{category_plan.status}",):
        raise ValueError("reason_codes must match category status")


def _validate_report_consistency(report: ResearchSourceRegistryPlanReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.category_plans != _build_category_plans(report.rows):
        raise ValueError("category_plans must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _validate_payload_fields(payload: dict[str, Any]) -> None:
    for key, value in payload.items():
        if type(key) is not str:
            raise ValueError("payload keys must be strings")
        if key not in PAYLOAD_FIELDS:
            raise ValueError("payload field is unsupported")
        _reject_unsafe_key("payload", key)
        if key == "rows":
            _validate_nested_payload_fields("row payload", value, ROW_PAYLOAD_FIELDS)
        elif key == "category_plans":
            _validate_nested_payload_fields(
                "category plan payload",
                value,
                CATEGORY_PAYLOAD_FIELDS,
            )


def _validate_nested_payload_fields(
    label: str,
    value: object,
    allowed_fields: frozenset[str],
) -> None:
    if type(value) is not list:
        raise ValueError(f"{label} must be a list")
    for item in value:
        if type(item) is not dict:
            raise ValueError(f"{label} items must be objects")
        for key in item:
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            if key not in allowed_fields:
                raise ValueError(f"{label} field is unsupported")
            _reject_unsafe_key(label, key)


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value.quantize(DECIMAL_QUANTUM))
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool or value is None:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, float):
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        _reject_unsafe_text("JSON string", value)
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_key("JSON object", key)
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value, DECIMAL_QUANTUM)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(DECIMAL_QUANTUM)


def _normalize_decimal(
    field_name: str,
    value: object,
    quantum: Decimal,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(quantum)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    return value.quantize(DECIMAL_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(DECIMAL_QUANTUM)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(field_name, value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    _reject_unsafe_text(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    return _require_member(field_name, value, STATUSES)


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in reason_codes:
        _require_public_string(field_name, reason_code)
    return reason_codes


def _require_hard_flags(label: str, value: object) -> None:
    for flag in HARD_FLAGS:
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{label} {flag} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), allow_json_containers=True)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{label} contains unsafe numeric detail")
        return
    if type(value) is bool or value is None:
        return
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{label} contains unsafe numeric detail")
    if type(value) is str:
        _reject_unsafe_text(label, value)
        return
    if isinstance(value, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if allow_json_containers and isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if allow_json_containers and isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_key(label, key)
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    raise ValueError(f"{label} contains unsafe public payload")


def _reject_unsafe_key(label: str, key: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public key")


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public text")
