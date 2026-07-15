"""Read-only local Postgres schema plan safety report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn


DEFAULT_LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_SAFETY_CONFIG_VERSION = (
    "local-supabase-schema-migration-plan-safety-report-v0"
)
LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_SAFETY_STATUSES = (
    "ready",
    "attention",
    "blocker",
)
LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_REQUIRED_SURFACES = (
    "paper_research_packets",
    "paper_recommendation_reports",
    "paper_cycle_snapshots",
    "paper_trade_journal",
    "paper_nav_snapshots",
    "paper_operator_evidence",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
REQUIRED_CHECK_COUNT = Decimal("10.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {"ready": 0, "attention": 1, "blocker": 2}

SURFACE_MISSING_REASON_CODES = {
    surface: f"{surface}_migration_plan_missing_blocker"
    for surface in LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_REQUIRED_SURFACES
}
PLAN_REASON_SEQUENCE = (
    "local_supabase_postgres_only_missing_blocker",
    "dsn_validator_not_validate_local_postgres_dsn_blocker",
    "durable_jsonl_fallback_present_blocker",
    "hosted_database_plan_present_blocker",
    "sqlite_plan_present_blocker",
    "redis_plan_present_blocker",
    "mongo_plan_present_blocker",
    "sqlalchemy_plan_present_blocker",
    "paper_evidence_only_missing_blocker",
    "migration_execution_present_blocker",
    "local_supabase_schema_migration_plan_ready",
)
REPORT_REASON_SEQUENCE = (
    SURFACE_MISSING_REASON_CODES["paper_research_packets"],
    SURFACE_MISSING_REASON_CODES["paper_recommendation_reports"],
    SURFACE_MISSING_REASON_CODES["paper_cycle_snapshots"],
    SURFACE_MISSING_REASON_CODES["paper_trade_journal"],
    SURFACE_MISSING_REASON_CODES["paper_nav_snapshots"],
    SURFACE_MISSING_REASON_CODES["paper_operator_evidence"],
    *PLAN_REASON_SEQUENCE,
)

__all__ = (
    "DEFAULT_LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_SAFETY_CONFIG_VERSION",
    "LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_SAFETY_STATUSES",
    "LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_REQUIRED_SURFACES",
    "LocalSupabaseSchemaMigrationPlanSafetySignal",
    "LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount",
    "LocalSupabaseSchemaMigrationPlanSafetyReport",
    "LocalSupabaseSchemaMigrationPlanSafetyRow",
    "build_local_supabase_schema_migration_plan_safety_report",
    "local_supabase_schema_migration_plan_safety_report_payload",
)


@dataclass(frozen=True)
class LocalSupabaseSchemaMigrationPlanSafetySignal:
    migration_surface: str
    local_supabase_postgres_only: bool
    dsn_validator_name: str
    sqlite_absent: bool
    redis_absent: bool
    mongo_absent: bool
    sqlalchemy_absent: bool
    hosted_database_absent: bool
    durable_jsonl_fallback_absent: bool
    paper_evidence_only: bool
    migration_execution_absent: bool
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_surface(self.migration_surface)
        _require_dsn_validator_name(self.dsn_validator_name)
        for field_name in (
            "local_supabase_postgres_only",
            "sqlite_absent",
            "redis_absent",
            "mongo_absent",
            "sqlalchemy_absent",
            "hosted_database_absent",
            "durable_jsonl_fallback_absent",
            "paper_evidence_only",
            "migration_execution_absent",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("plan signal", self)


@dataclass(frozen=True)
class LocalSupabaseSchemaMigrationPlanSafetyRow:
    migration_surface: str
    status: str
    local_supabase_postgres_only: bool
    dsn_validator_name: str
    sqlite_absent: bool
    redis_absent: bool
    mongo_absent: bool
    sqlalchemy_absent: bool
    hosted_database_absent: bool
    durable_jsonl_fallback_absent: bool
    paper_evidence_only: bool
    migration_execution_absent: bool
    ready_check_count: Decimal
    required_check_count: Decimal
    readiness_ratio: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_surface(self.migration_surface)
        _require_status("status", self.status)
        _require_dsn_validator_name(self.dsn_validator_name)
        for field_name in (
            "local_supabase_postgres_only",
            "sqlite_absent",
            "redis_absent",
            "mongo_absent",
            "sqlalchemy_absent",
            "hosted_database_absent",
            "durable_jsonl_fallback_absent",
            "paper_evidence_only",
            "migration_execution_absent",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "ready_check_count",
            _require_count_decimal("ready_check_count", self.ready_check_count),
        )
        object.__setattr__(
            self,
            "required_check_count",
            _require_count_decimal("required_check_count", self.required_check_count),
        )
        object.__setattr__(
            self,
            "readiness_ratio",
            _require_ratio_decimal("readiness_ratio", self.readiness_ratio),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount:
    reason_code: str
    count: Decimal
    ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_codes((self.reason_code,), require_nonempty=True)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(self, "ratio", _require_ratio_decimal("ratio", self.ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class LocalSupabaseSchemaMigrationPlanSafetyReport:
    generated_at: datetime
    config_version: str
    migration_surface_count: Decimal
    required_surface_count: Decimal
    missing_required_surface_count: Decimal
    ready_count: Decimal
    attention_count: Decimal
    blocker_count: Decimal
    ready_ratio: Decimal
    status: str
    missing_required_surfaces: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount, ...]
    rows: tuple[LocalSupabaseSchemaMigrationPlanSafetyRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        if self.config_version != DEFAULT_LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_SAFETY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "migration_surface_count",
            "required_surface_count",
            "missing_required_surface_count",
            "ready_count",
            "attention_count",
            "blocker_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "missing_required_surfaces",
            _require_missing_surfaces(self.missing_required_surfaces),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)


def build_local_supabase_schema_migration_plan_safety_report(
    plans: Iterable[LocalSupabaseSchemaMigrationPlanSafetySignal],
    *,
    generated_at: datetime,
) -> LocalSupabaseSchemaMigrationPlanSafetyReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_plans = _normalize_plans(plans, generated_at=generated_at_utc)
    rows = tuple(
        sorted((_row_from_plan(plan) for plan in normalized_plans), key=_row_sort_key),
    )
    missing_required_surfaces = _missing_required_surfaces(rows)
    reason_codes = _report_reason_codes(rows, missing_required_surfaces)
    total_required = _count(len(LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_REQUIRED_SURFACES))

    return LocalSupabaseSchemaMigrationPlanSafetyReport(
        generated_at=generated_at_utc,
        config_version=DEFAULT_LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_SAFETY_CONFIG_VERSION,
        migration_surface_count=_count(len(rows)),
        required_surface_count=total_required,
        missing_required_surface_count=_count(len(missing_required_surfaces)),
        ready_count=_status_count(rows, "ready"),
        attention_count=_status_count(rows, "attention"),
        blocker_count=_status_count(rows, "blocker"),
        ready_ratio=_ratio(_status_count(rows, "ready"), total_required),
        status=_report_status(rows, missing_required_surfaces),
        missing_required_surfaces=missing_required_surfaces,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, missing_required_surfaces, reason_codes),
        rows=rows,
    )


def local_supabase_schema_migration_plan_safety_report_payload(
    report: LocalSupabaseSchemaMigrationPlanSafetyReport,
) -> dict[str, object]:
    if type(report) is not LocalSupabaseSchemaMigrationPlanSafetyReport:
        raise ValueError("report must be a LocalSupabaseSchemaMigrationPlanSafetyReport")
    _require_hard_flags("report", report)
    for row in report.rows:
        _require_hard_flags("row", row)
    for item in report.reason_code_counts:
        _require_hard_flags("reason code count", item)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_plan(
    plan: LocalSupabaseSchemaMigrationPlanSafetySignal,
) -> LocalSupabaseSchemaMigrationPlanSafetyRow:
    checks = (
        plan.local_supabase_postgres_only,
        plan.dsn_validator_name == validate_local_postgres_dsn.__name__,
        plan.sqlite_absent,
        plan.redis_absent,
        plan.mongo_absent,
        plan.sqlalchemy_absent,
        plan.hosted_database_absent,
        plan.durable_jsonl_fallback_absent,
        plan.paper_evidence_only,
        plan.migration_execution_absent,
    )
    ready_check_count = _count(sum(checks))
    reason_codes = _row_reason_codes(plan)
    return LocalSupabaseSchemaMigrationPlanSafetyRow(
        migration_surface=plan.migration_surface,
        status=_row_status(reason_codes),
        local_supabase_postgres_only=plan.local_supabase_postgres_only,
        dsn_validator_name=plan.dsn_validator_name,
        sqlite_absent=plan.sqlite_absent,
        redis_absent=plan.redis_absent,
        mongo_absent=plan.mongo_absent,
        sqlalchemy_absent=plan.sqlalchemy_absent,
        hosted_database_absent=plan.hosted_database_absent,
        durable_jsonl_fallback_absent=plan.durable_jsonl_fallback_absent,
        paper_evidence_only=plan.paper_evidence_only,
        migration_execution_absent=plan.migration_execution_absent,
        ready_check_count=ready_check_count,
        required_check_count=REQUIRED_CHECK_COUNT,
        readiness_ratio=_ratio(ready_check_count, REQUIRED_CHECK_COUNT),
        observed_at=plan.observed_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    plan: LocalSupabaseSchemaMigrationPlanSafetySignal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not plan.local_supabase_postgres_only:
        reason_codes.append("local_supabase_postgres_only_missing_blocker")
    if plan.dsn_validator_name != validate_local_postgres_dsn.__name__:
        reason_codes.append("dsn_validator_not_validate_local_postgres_dsn_blocker")
    if not plan.sqlite_absent:
        reason_codes.append("sqlite_plan_present_blocker")
    if not plan.redis_absent:
        reason_codes.append("redis_plan_present_blocker")
    if not plan.mongo_absent:
        reason_codes.append("mongo_plan_present_blocker")
    if not plan.sqlalchemy_absent:
        reason_codes.append("sqlalchemy_plan_present_blocker")
    if not plan.hosted_database_absent:
        reason_codes.append("hosted_database_plan_present_blocker")
    if not plan.durable_jsonl_fallback_absent:
        reason_codes.append("durable_jsonl_fallback_present_blocker")
    if not plan.paper_evidence_only:
        reason_codes.append("paper_evidence_only_missing_blocker")
    if not plan.migration_execution_absent:
        reason_codes.append("migration_execution_present_blocker")
    if not reason_codes:
        reason_codes.append("local_supabase_schema_migration_plan_ready")
    return _require_reason_codes(tuple(reason_codes), require_nonempty=True)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocker") for reason_code in reason_codes):
        return "blocker"
    if any(reason_code.endswith("_attention") for reason_code in reason_codes):
        return "attention"
    return "ready"


def _report_status(
    rows: tuple[LocalSupabaseSchemaMigrationPlanSafetyRow, ...],
    missing_required_surfaces: tuple[str, ...],
) -> str:
    if missing_required_surfaces or any(row.status == "blocker" for row in rows):
        return "blocker"
    if any(row.status == "attention" for row in rows):
        return "attention"
    return "ready"


def _report_reason_codes(
    rows: tuple[LocalSupabaseSchemaMigrationPlanSafetyRow, ...],
    missing_required_surfaces: tuple[str, ...],
) -> tuple[str, ...]:
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    for surface in missing_required_surfaces:
        found.add(SURFACE_MISSING_REASON_CODES[surface])
    return tuple(reason_code for reason_code in REPORT_REASON_SEQUENCE if reason_code in found)


def _reason_code_counts(
    rows: tuple[LocalSupabaseSchemaMigrationPlanSafetyRow, ...],
    missing_required_surfaces: tuple[str, ...],
    reason_codes: tuple[str, ...],
) -> tuple[LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount, ...]:
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    for surface in missing_required_surfaces:
        counts[SURFACE_MISSING_REASON_CODES[surface]] += 1
    total = _count(len(LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_REQUIRED_SURFACES))
    return tuple(
        LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            ratio=_ratio(_count(counts[reason_code]), total),
        )
        for reason_code in reason_codes
        if reason_code in counts
    )


def _missing_required_surfaces(
    rows: tuple[LocalSupabaseSchemaMigrationPlanSafetyRow, ...],
) -> tuple[str, ...]:
    found = {row.migration_surface for row in rows}
    return tuple(
        surface
        for surface in LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_REQUIRED_SURFACES
        if surface not in found
    )


def _row_sort_key(row: LocalSupabaseSchemaMigrationPlanSafetyRow) -> tuple[int, int]:
    return (
        -STATUS_RANK[row.status],
        LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_REQUIRED_SURFACES.index(row.migration_surface),
    )


def _status_count(
    rows: tuple[LocalSupabaseSchemaMigrationPlanSafetyRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_plans(
    plans: Iterable[LocalSupabaseSchemaMigrationPlanSafetySignal],
    *,
    generated_at: datetime,
) -> tuple[LocalSupabaseSchemaMigrationPlanSafetySignal, ...]:
    if isinstance(plans, (str, bytes)) or plans is None:
        raise ValueError("plans must be an iterable")
    try:
        values = tuple(plans)
    except TypeError as exc:
        raise ValueError("plans must be an iterable") from exc
    surfaces: set[str] = set()
    for value in values:
        if type(value) is not LocalSupabaseSchemaMigrationPlanSafetySignal:
            raise ValueError("plans must contain LocalSupabaseSchemaMigrationPlanSafetySignal values")
        _require_hard_flags("plan signal", value)
        if value.migration_surface in surfaces:
            raise ValueError("duplicate migration_surface values are not allowed")
        surfaces.add(value.migration_surface)
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return values


def _require_rows(
    rows: Iterable[LocalSupabaseSchemaMigrationPlanSafetyRow],
) -> tuple[LocalSupabaseSchemaMigrationPlanSafetyRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    values = tuple(rows)
    surfaces: set[str] = set()
    previous_sort_key: tuple[int, int] | None = None
    for row in values:
        if type(row) is not LocalSupabaseSchemaMigrationPlanSafetyRow:
            raise ValueError("rows must contain LocalSupabaseSchemaMigrationPlanSafetyRow values")
        _require_hard_flags("row", row)
        if row.migration_surface in surfaces:
            raise ValueError("rows must have unique migration_surface values")
        surfaces.add(row.migration_surface)
        sort_key = _row_sort_key(row)
        if previous_sort_key is not None and previous_sort_key > sort_key:
            raise ValueError("rows must be deterministically arranged")
        previous_sort_key = sort_key
    return values


def _require_reason_code_counts(
    values: Iterable[LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount],
) -> tuple[LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    items = tuple(values)
    previous_index = -1
    seen: set[str] = set()
    for item in items:
        if type(item) is not LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount values",
            )
        _require_hard_flags("reason code count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
        index = REPORT_REASON_SEQUENCE.index(item.reason_code)
        if index <= previous_index:
            raise ValueError("reason_code_counts must be deterministically arranged")
        previous_index = index
    return items


def _validate_report(report: LocalSupabaseSchemaMigrationPlanSafetyReport) -> None:
    rows = report.rows
    missing_required_surfaces = _missing_required_surfaces(rows)
    total_required = _count(len(LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_REQUIRED_SURFACES))
    if report.migration_surface_count != _count(len(rows)):
        raise ValueError("migration_surface_count must match rows")
    if report.required_surface_count != total_required:
        raise ValueError("required_surface_count must match required surfaces")
    if report.missing_required_surface_count != _count(len(missing_required_surfaces)):
        raise ValueError("missing_required_surface_count must match rows")
    if report.ready_count != _status_count(rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.attention_count != _status_count(rows, "attention"):
        raise ValueError("attention_count must match rows")
    if report.blocker_count != _status_count(rows, "blocker"):
        raise ValueError("blocker_count must match rows")
    if report.ready_ratio != _ratio(report.ready_count, total_required):
        raise ValueError("ready_ratio must match rows")
    if report.status != _report_status(rows, missing_required_surfaces):
        raise ValueError("status must match rows")
    if report.missing_required_surfaces != missing_required_surfaces:
        raise ValueError("missing_required_surfaces must match rows")
    reason_codes = _report_reason_codes(rows, missing_required_surfaces)
    if report.reason_codes != reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, missing_required_surfaces, reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _require_missing_surfaces(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("missing_required_surfaces must be an iterable")
    surfaces = tuple(values)
    previous_index = -1
    seen: set[str] = set()
    for surface in surfaces:
        _require_surface(surface)
        if surface in seen:
            raise ValueError("missing_required_surfaces must be unique")
        seen.add(surface)
        index = LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_REQUIRED_SURFACES.index(surface)
        if index <= previous_index:
            raise ValueError("missing_required_surfaces must be deterministically arranged")
        previous_index = index
    return surfaces


def _require_report_reason_codes(values: Iterable[str]) -> tuple[str, ...]:
    reason_codes = _require_reason_codes(tuple(values), require_nonempty=True)
    previous_index = -1
    for reason_code in reason_codes:
        index = REPORT_REASON_SEQUENCE.index(reason_code)
        if index <= previous_index:
            raise ValueError("reason_codes must be deterministically arranged")
        previous_index = index
    return reason_codes


def _require_reason_codes(
    values: Iterable[str],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    reason_codes = tuple(values)
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_codes must contain strings")
        if reason_code not in REPORT_REASON_SEQUENCE:
            raise ValueError("reason_code is not supported")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return reason_codes


def _require_surface(value: object) -> None:
    if value not in LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_REQUIRED_SURFACES:
        raise ValueError("migration_surface must be a supported paper evidence surface")


def _require_dsn_validator_name(value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError("dsn_validator_name must be a nonempty string")


def _require_status(name: str, value: object) -> None:
    if value not in LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_SAFETY_STATUSES:
        raise ValueError(f"{name} must be a supported safety status")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_count_decimal(name, value)
    if decimal_value > ONE:
        raise ValueError(f"{name} must be <= 1.000000")
    return decimal_value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_hard_flags(name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{name} must keep {flag_name}=True")


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value
