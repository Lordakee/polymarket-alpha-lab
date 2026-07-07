"""Report-only public-web research scraping scope planner."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_SCRAPING_SCOPE_PLAN_CONFIG_VERSION",
    "ResearchScrapingScopePlanConfig",
    "ResearchScrapingScopePlanInput",
    "ResearchScrapingScopePlanReport",
    "ResearchScrapingScopePlanRow",
    "build_research_scraping_scope_plan_report",
    "research_scraping_scope_plan_payload",
)


DEFAULT_RESEARCH_SCRAPING_SCOPE_PLAN_CONFIG_VERSION = (
    "research-scraping-scope-plan-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SOURCE_CATEGORIES = ("official", "regulatory", "news")
STATUSES = ("pass", "watch", "block")
FRESHNESS_PRIORITIES = ("low", "medium", "high", "critical")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
NO_INPUTS_REASON = "research_scraping_scope_plan_no_inputs"

UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate-",
    "candidate_id",
    "candidate id",
    "market-",
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
    "http://",
    "https://",
    "www.",
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
UNSAFE_PUBLIC_WORDS = frozenset(("buy", "sell"))


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
class ResearchScrapingScopePlanConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_SCRAPING_SCOPE_PLAN_CONFIG_VERSION
    source_gap_watch_count: Decimal = Decimal("1.000000")
    source_gap_block_count: Decimal = Decimal("3.000000")
    conflict_block_count: Decimal = Decimal("1.000000")
    stale_watch_after_seconds: Decimal = Decimal("86400.000000")
    stale_block_after_seconds: Decimal = Decimal("604800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchScrapingScopePlanConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "source_gap_watch_count",
            "source_gap_block_count",
            "conflict_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_watch_after_seconds",
            "stale_block_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_most(
            "source_gap_watch_count",
            self.source_gap_watch_count,
            self.source_gap_block_count,
        )
        _require_at_most(
            "stale_watch_after_seconds",
            self.stale_watch_after_seconds,
            self.stale_block_after_seconds,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchScrapingScopePlanInput(_FinalPublicDataclass):
    scope_key: str
    topic_category: str
    source_category: str
    source_age_seconds: Decimal | None
    source_gap_count: Decimal
    conflict_count: Decimal
    collection_allowed: bool
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchScrapingScopePlanInput, "input")
        for field_name in ("scope_key", "topic_category"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("source_category", self.source_category, SOURCE_CATEGORIES)
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        for field_name in ("source_gap_count", "conflict_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _require_bool("collection_allowed", self.collection_allowed)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchScrapingScopePlanRow(_FinalPublicDataclass):
    collection_scope: str
    topic_category: str
    source_category: str
    freshness_priority: str
    scope_status: str
    source_age_seconds: Decimal | None
    source_gap_count: Decimal
    conflict_count: Decimal
    reason_codes: tuple[str, ...]
    scope_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchScrapingScopePlanRow, "row")
        for field_name in ("collection_scope", "topic_category"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("source_category", self.source_category, SOURCE_CATEGORIES)
        _require_member(
            "freshness_priority",
            self.freshness_priority,
            FRESHNESS_PRIORITIES,
        )
        _require_member("scope_status", self.scope_status, STATUSES)
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        for field_name in ("source_gap_count", "conflict_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.collection_scope != _collection_scope(
            self.topic_category,
            self.source_category,
        ):
            raise ValueError("collection_scope must match topic and source category")
        if self.scope_status != _row_status(self.reason_codes):
            raise ValueError("scope_status must match reason_codes")
        if self.scope_digest == "":
            object.__setattr__(self, "scope_digest", _row_digest(self))
        else:
            _require_digest("scope_digest", self.scope_digest)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchScrapingScopePlanReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    plan_status: str
    scope_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchScrapingScopePlanRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchScrapingScopePlanReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("plan_status", self.plan_status, STATUSES)
        for field_name in ("scope_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_research_scraping_scope_plan_report(
    inputs: Iterable[ResearchScrapingScopePlanInput],
    *,
    config: ResearchScrapingScopePlanConfig,
    generated_at: datetime,
) -> ResearchScrapingScopePlanReport:
    if type(config) is not ResearchScrapingScopePlanConfig:
        raise ValueError("config must be a ResearchScrapingScopePlanConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _build_row(value, config=config)
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchScrapingScopePlanReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        plan_status=_rollup_status(tuple(row.scope_status for row in rows)),
        scope_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        reason_codes=_rollup_reason_codes(rows),
        rows=rows,
    )


def research_scraping_scope_plan_payload(
    report: ResearchScrapingScopePlanReport,
) -> dict[str, Any]:
    if type(report) is not ResearchScrapingScopePlanReport:
        raise ValueError("report must be a ResearchScrapingScopePlanReport")
    _reject_unsafe_public_payload("report", report)
    _require_payload_safe_value("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
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


def _build_row(
    value: ResearchScrapingScopePlanInput,
    *,
    config: ResearchScrapingScopePlanConfig,
) -> ResearchScrapingScopePlanRow:
    reason_codes = _row_reason_codes(value, config=config)
    return ResearchScrapingScopePlanRow(
        collection_scope=_collection_scope(value.topic_category, value.source_category),
        topic_category=value.topic_category,
        source_category=value.source_category,
        freshness_priority=_freshness_priority(
            source_age_seconds=value.source_age_seconds,
            scope_status=_row_status(reason_codes),
            config=config,
        ),
        scope_status=_row_status(reason_codes),
        source_age_seconds=value.source_age_seconds,
        source_gap_count=value.source_gap_count,
        conflict_count=value.conflict_count,
        reason_codes=reason_codes,
        scope_digest=_input_digest(value),
    )


def _row_reason_codes(
    value: ResearchScrapingScopePlanInput,
    *,
    config: ResearchScrapingScopePlanConfig,
) -> tuple[str, ...]:
    reason_codes = list(value.reason_codes)
    if not value.collection_allowed:
        reason_codes.append("scraping_scope_collection_not_allowed_block")
    if value.conflict_count >= config.conflict_block_count:
        reason_codes.append("scraping_scope_conflict_block")
    if value.source_gap_count >= config.source_gap_block_count:
        reason_codes.append("scraping_scope_source_gap_block")
    elif value.source_gap_count >= config.source_gap_watch_count:
        reason_codes.append("scraping_scope_source_gap_watch")
    if value.source_age_seconds is None:
        reason_codes.append("scraping_scope_freshness_unknown_watch")
    elif value.source_age_seconds >= config.stale_block_after_seconds:
        reason_codes.append("scraping_scope_freshness_stale_block")
    elif value.source_age_seconds >= config.stale_watch_after_seconds:
        reason_codes.append("scraping_scope_freshness_stale_watch")
    if not any(code.endswith("_watch") or code.endswith("_block") for code in reason_codes):
        reason_codes.append("scraping_scope_public_research_ready")
    return tuple(sorted(reason_codes))


def _freshness_priority(
    *,
    source_age_seconds: Decimal | None,
    scope_status: str,
    config: ResearchScrapingScopePlanConfig,
) -> str:
    if scope_status == "block":
        return "critical"
    if source_age_seconds is None:
        return "high"
    if source_age_seconds >= config.stale_block_after_seconds:
        return "critical"
    if source_age_seconds >= config.stale_watch_after_seconds or scope_status == "watch":
        return "high"
    return "low"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _rollup_reason_codes(
    rows: tuple[ResearchScrapingScopePlanRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.scope_status for row in rows))
    reason_codes = [f"research_scraping_scope_plan_{status}"]
    row_reason_codes = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    )
    for reason_code in (
        "scraping_scope_collection_not_allowed_block",
        "scraping_scope_conflict_block",
        "scraping_scope_freshness_stale_block",
        "scraping_scope_freshness_stale_watch",
        "scraping_scope_freshness_unknown_watch",
        "scraping_scope_source_gap_block",
        "scraping_scope_source_gap_watch",
    ):
        if reason_code in row_reason_codes:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _status_count(rows: tuple[ResearchScrapingScopePlanRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.scope_status == status))


def _normalize_inputs(
    inputs: Iterable[ResearchScrapingScopePlanInput],
) -> tuple[ResearchScrapingScopePlanInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_scope_keys: set[str] = set()
    for value in values:
        if type(value) is not ResearchScrapingScopePlanInput:
            raise ValueError(
                "inputs must contain ResearchScrapingScopePlanInput values",
            )
        _require_hard_flags("input", value)
        if value.scope_key in seen_scope_keys:
            raise ValueError("inputs must not contain duplicate scope_key values")
        seen_scope_keys.add(value.scope_key)
    return values


def _normalize_rows(
    rows: Iterable[ResearchScrapingScopePlanRow],
) -> tuple[ResearchScrapingScopePlanRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_digests: set[str] = set()
    for row in values:
        if type(row) is not ResearchScrapingScopePlanRow:
            raise ValueError("rows must contain ResearchScrapingScopePlanRow values")
        _require_hard_flags("row", row)
        if row.scope_digest in seen_digests:
            raise ValueError("rows must not contain duplicate scope_digest values")
        seen_digests.add(row.scope_digest)
    expected = tuple(sorted(values, key=_row_sort_key))
    if values != expected:
        raise ValueError("rows must use canonical sequence")
    return values


def _row_sort_key(
    row: ResearchScrapingScopePlanRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.scope_status],
        -row.conflict_count,
        -row.source_gap_count,
        -(row.source_age_seconds if row.source_age_seconds is not None else ZERO),
        row.collection_scope,
        row.scope_digest,
    )


def _validate_report(report: ResearchScrapingScopePlanReport) -> None:
    rows = report.rows
    if report.scope_count != _count(len(rows)):
        raise ValueError("scope_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.plan_status != _rollup_status(tuple(row.scope_status for row in rows)):
        raise ValueError("plan_status must match rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes("reason_codes", value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if reason_codes != tuple(dict.fromkeys(reason_codes)):
        raise ValueError("reason_codes must not contain duplicates")
    return reason_codes


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reason_codes: list[str] = []
    for item in value:
        _require_public_string(field_name, item)
        reason_codes.append(item)
    return tuple(sorted(dict.fromkeys(reason_codes)))


def _collection_scope(topic_category: str, source_category: str) -> str:
    return f"{topic_category}:{source_category}:public-web"


def _input_digest(value: ResearchScrapingScopePlanInput) -> str:
    digest_source = "|".join(
        (
            value.scope_key,
            value.topic_category,
            value.source_category,
            str(value.source_age_seconds),
            str(value.source_gap_count),
            str(value.conflict_count),
            str(value.collection_allowed),
            ",".join(value.reason_codes),
        ),
    )
    return sha256(digest_source.encode("utf-8")).hexdigest()


def _row_digest(value: ResearchScrapingScopePlanRow) -> str:
    digest_source = "|".join(
        (
            value.collection_scope,
            value.topic_category,
            value.source_category,
            value.freshness_priority,
            value.scope_status,
            str(value.source_age_seconds),
            str(value.source_gap_count),
            str(value.conflict_count),
            ",".join(value.reason_codes),
        ),
    )
    return sha256(digest_source.encode("utf-8")).hexdigest()


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for char in value:
        if char not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    _reject_unsafe_public_text(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_at_most(field_name: str, value: Decimal, ceiling: Decimal) -> None:
    if value > ceiling:
        raise ValueError(f"{field_name} must be <= ceiling")


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        return _json_dict_ready(value)
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _json_dict_ready(value: dict[Any, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        ready[key] = _json_ready(item)
    return ready


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} must be a public dataclass value")
        _rebuild_public_dataclass(label, value)
        for field in fields(value):
            _require_payload_safe_value(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if type(value) in (Decimal, datetime, bool):
        return
    if type(value) is str:
        _require_public_string(label, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{label}[{index}]", item)
        return
    if value is None:
        return
    raise ValueError(f"{label} contains unsupported public payload value")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(f"{label} failed payload revalidation") from exc


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload key in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")
    words = {
        token
        for token in "".join(
            char.lower() if char.isalnum() else " "
            for char in value
        ).split()
    }
    if words & UNSAFE_PUBLIC_WORDS:
        raise ValueError(f"{field_name} contains unsafe public text")


_PUBLIC_DATACLASS_TYPES = (
    ResearchScrapingScopePlanConfig,
    ResearchScrapingScopePlanInput,
    ResearchScrapingScopePlanReport,
    ResearchScrapingScopePlanRow,
)
