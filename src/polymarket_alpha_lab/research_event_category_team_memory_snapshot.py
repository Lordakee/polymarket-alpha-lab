"""Pure report-only category memory snapshot reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_EVENT_CATEGORY_TEAM_MEMORY_SNAPSHOT_CONFIG_VERSION = (
    "research-event-category-team-memory-snapshot-v0"
)

PUBLIC_STATUS_PASS = "pass"
PUBLIC_STATUS_WATCH = "watch"
PUBLIC_STATUS_BLOCK = "block"
PUBLIC_STATUSES = (PUBLIC_STATUS_PASS, PUBLIC_STATUS_WATCH, PUBLIC_STATUS_BLOCK)

RESEARCH_EVENT_CATEGORY_TEAM_MEMORY_SNAPSHOT_CATEGORIES = (
    "politics",
    "crypto",
    "macro",
    "gold",
    "soccer",
    "basketball",
)

PASS_REASON = "team_memory_snapshot_pass"
WATCH_REASON = "team_memory_snapshot_watch"
BLOCK_REASON = "team_memory_snapshot_block"
NO_MEMORY_REASON = "team_memory_snapshot_no_memory_coverage"
COVERAGE_BELOW_WATCH_REASON = "team_memory_snapshot_coverage_below_watch"
COVERAGE_BELOW_PASS_REASON = "team_memory_snapshot_coverage_below_pass"
STALE_ABOVE_WATCH_REASON = "team_memory_snapshot_stale_ratio_above_watch"
STALE_ABOVE_PASS_REASON = "team_memory_snapshot_stale_ratio_above_pass"
BLOCKED_ABOVE_WATCH_REASON = "team_memory_snapshot_blocked_ratio_above_watch"
BLOCKED_ABOVE_PASS_REASON = "team_memory_snapshot_blocked_ratio_above_pass"

REASON_CODE_PRIORITY = (
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
    NO_MEMORY_REASON,
    COVERAGE_BELOW_WATCH_REASON,
    COVERAGE_BELOW_PASS_REASON,
    STALE_ABOVE_WATCH_REASON,
    STALE_ABOVE_PASS_REASON,
    BLOCKED_ABOVE_WATCH_REASON,
    BLOCKED_ABOVE_PASS_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")

_CATEGORY_KEYWORDS = (
    ("politics", ("politics", "election", "policy", "congress", "senate", "vote")),
    ("crypto", ("crypto", "btc", "bitcoin", "ethereum", "eth")),
    ("macro", ("macro", "fomc", "rates", "inflation", "cpi", "fed")),
    ("gold", ("gold", "xau", "bullion", "metals", "metal")),
    ("soccer", ("soccer", "football", "premier", "uefa", "fifa")),
    ("basketball", ("basketball", "nba", "wnba", "ncaa")),
)

_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "auth",
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
        "secret",
        "private",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_CATEGORY_TEAM_MEMORY_SNAPSHOT_CONFIG_VERSION",
    "RESEARCH_EVENT_CATEGORY_TEAM_MEMORY_SNAPSHOT_CATEGORIES",
    "ResearchEventCategoryTeamMemoryInput",
    "ResearchEventCategoryTeamMemorySnapshotCategoryRow",
    "ResearchEventCategoryTeamMemorySnapshotConfig",
    "ResearchEventCategoryTeamMemorySnapshotReasonCodeCount",
    "ResearchEventCategoryTeamMemorySnapshotReport",
    "build_research_event_category_team_memory_snapshot",
    "research_event_category_team_memory_snapshot_digest",
    "research_event_category_team_memory_snapshot_payload",
)


@dataclass(frozen=True)
class ResearchEventCategoryTeamMemorySnapshotConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_CATEGORY_TEAM_MEMORY_SNAPSHOT_CONFIG_VERSION
    min_pass_coverage_ratio: Decimal = Decimal("0.700000")
    min_watch_coverage_ratio: Decimal = Decimal("0.400000")
    max_pass_stale_ratio: Decimal = Decimal("0.200000")
    max_watch_stale_ratio: Decimal = Decimal("0.500000")
    max_pass_blocked_ratio: Decimal = Decimal("0.000000")
    max_watch_blocked_ratio: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCategoryTeamMemorySnapshotConfig:
            raise TypeError("ResearchEventCategoryTeamMemorySnapshotConfig is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCategoryTeamMemorySnapshotConfig:
            raise ValueError(
                "config must be exactly ResearchEventCategoryTeamMemorySnapshotConfig",
            )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "min_pass_coverage_ratio",
            "min_watch_coverage_ratio",
            "max_pass_stale_ratio",
            "max_watch_stale_ratio",
            "max_pass_blocked_ratio",
            "max_watch_blocked_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_coverage_ratio < self.min_watch_coverage_ratio:
            raise ValueError("min_pass_coverage_ratio must not be below watch")
        if self.max_pass_stale_ratio > self.max_watch_stale_ratio:
            raise ValueError("max_pass_stale_ratio must not exceed watch")
        if self.max_pass_blocked_ratio > self.max_watch_blocked_ratio:
            raise ValueError("max_pass_blocked_ratio must not exceed watch")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventCategoryTeamMemoryInput:
    team_id: str
    event_category_hint: str
    memory_entry_count: Decimal
    passing_memory_entry_count: Decimal
    watch_memory_entry_count: Decimal
    blocked_memory_entry_count: Decimal
    stale_memory_entry_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCategoryTeamMemoryInput:
            raise TypeError("ResearchEventCategoryTeamMemoryInput is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCategoryTeamMemoryInput:
            raise ValueError("input must be exactly ResearchEventCategoryTeamMemoryInput")
        _require_public_text("team_id", self.team_id)
        _require_public_text("event_category_hint", self.event_category_hint)
        for field_name in (
            "memory_entry_count",
            "passing_memory_entry_count",
            "watch_memory_entry_count",
            "blocked_memory_entry_count",
            "stale_memory_entry_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.passing_memory_entry_count
            + self.watch_memory_entry_count
            + self.blocked_memory_entry_count
            != self.memory_entry_count
        ):
            raise ValueError("memory coverage counts must sum to memory_entry_count")
        if self.stale_memory_entry_count > self.memory_entry_count:
            raise ValueError("stale_memory_entry_count must not exceed memory_entry_count")
        _category_for_memory(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventCategoryTeamMemorySnapshotCategoryRow:
    category_id: str
    team_count: Decimal
    memory_entry_count: Decimal
    passing_memory_entry_count: Decimal
    watch_memory_entry_count: Decimal
    blocked_memory_entry_count: Decimal
    stale_memory_entry_count: Decimal
    coverage_ratio: Decimal
    watch_ratio: Decimal
    blocked_ratio: Decimal
    stale_ratio: Decimal
    public_status: str
    reason_codes: tuple[str, ...]
    public_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCategoryTeamMemorySnapshotCategoryRow:
            raise TypeError("ResearchEventCategoryTeamMemorySnapshotCategoryRow is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCategoryTeamMemorySnapshotCategoryRow:
            raise ValueError(
                "row must be exactly ResearchEventCategoryTeamMemorySnapshotCategoryRow",
            )
        _require_public_category_id("category_id", self.category_id)
        for field_name in (
            "team_count",
            "memory_entry_count",
            "passing_memory_entry_count",
            "watch_memory_entry_count",
            "blocked_memory_entry_count",
            "stale_memory_entry_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "coverage_ratio",
            "watch_ratio",
            "blocked_ratio",
            "stale_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_status("public_status", self.public_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_sha256_digest("public_digest", self.public_digest)
        _validate_category_row(self)
        _require_hard_flags("row", self)
        if self.public_digest != _digest_payload(_category_row_payload(self, digest=False)):
            raise ValueError("public_digest does not match category row")


@dataclass(frozen=True)
class ResearchEventCategoryTeamMemorySnapshotReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCategoryTeamMemorySnapshotReasonCodeCount:
            raise TypeError("ResearchEventCategoryTeamMemorySnapshotReasonCodeCount is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCategoryTeamMemorySnapshotReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchEventCategoryTeamMemorySnapshotReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_count_decimal("count", self.count),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchEventCategoryTeamMemorySnapshotReport:
    generated_at: datetime
    config_version: str
    category_count: Decimal
    observed_category_count: Decimal
    team_count: Decimal
    pass_category_count: Decimal
    watch_category_count: Decimal
    block_category_count: Decimal
    memory_entry_count: Decimal
    passing_memory_entry_count: Decimal
    watch_memory_entry_count: Decimal
    blocked_memory_entry_count: Decimal
    stale_memory_entry_count: Decimal
    coverage_ratio: Decimal
    watch_ratio: Decimal
    blocked_ratio: Decimal
    stale_ratio: Decimal
    public_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventCategoryTeamMemorySnapshotReasonCodeCount, ...]
    category_rows: tuple[ResearchEventCategoryTeamMemorySnapshotCategoryRow, ...]
    public_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCategoryTeamMemorySnapshotReport:
            raise TypeError("ResearchEventCategoryTeamMemorySnapshotReport is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCategoryTeamMemorySnapshotReport:
            raise ValueError(
                "report must be exactly ResearchEventCategoryTeamMemorySnapshotReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "category_count",
            "observed_category_count",
            "team_count",
            "pass_category_count",
            "watch_category_count",
            "block_category_count",
            "memory_entry_count",
            "passing_memory_entry_count",
            "watch_memory_entry_count",
            "blocked_memory_entry_count",
            "stale_memory_entry_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "coverage_ratio",
            "watch_ratio",
            "blocked_ratio",
            "stale_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_status("public_status", self.public_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "category_rows",
            _normalize_category_rows(self.category_rows),
        )
        _require_sha256_digest("public_digest", self.public_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        if self.public_digest != _digest_payload(_report_payload(self, digest=False)):
            raise ValueError("public_digest does not match report")

    @property
    def public_payload(self) -> dict[str, object]:
        return research_event_category_team_memory_snapshot_payload(self)


def build_research_event_category_team_memory_snapshot(
    memory_rows: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchEventCategoryTeamMemorySnapshotConfig | None = None,
) -> ResearchEventCategoryTeamMemorySnapshotReport:
    cfg = config or ResearchEventCategoryTeamMemorySnapshotConfig()
    if type(cfg) is not ResearchEventCategoryTeamMemorySnapshotConfig:
        raise ValueError(
            "config must be a ResearchEventCategoryTeamMemorySnapshotConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", cfg)
    inputs = _normalize_inputs(memory_rows)
    by_category = _inputs_by_category(inputs)
    category_rows = tuple(
        _category_row(category_id, by_category[category_id], config=cfg)
        for category_id in RESEARCH_EVENT_CATEGORY_TEAM_MEMORY_SNAPSHOT_CATEGORIES
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": cfg.config_version,
        "category_count": _count_decimal(len(category_rows)),
        "observed_category_count": _count_decimal(
            sum(1 for row in category_rows if row.team_count > ZERO_COUNT),
        ),
        "team_count": _sum_rows(category_rows, "team_count"),
        "pass_category_count": _status_count(category_rows, PUBLIC_STATUS_PASS),
        "watch_category_count": _status_count(category_rows, PUBLIC_STATUS_WATCH),
        "block_category_count": _status_count(category_rows, PUBLIC_STATUS_BLOCK),
        "memory_entry_count": _sum_rows(category_rows, "memory_entry_count"),
        "passing_memory_entry_count": _sum_rows(
            category_rows,
            "passing_memory_entry_count",
        ),
        "watch_memory_entry_count": _sum_rows(category_rows, "watch_memory_entry_count"),
        "blocked_memory_entry_count": _sum_rows(
            category_rows,
            "blocked_memory_entry_count",
        ),
        "stale_memory_entry_count": _sum_rows(category_rows, "stale_memory_entry_count"),
        "coverage_ratio": _ratio(
            _sum_rows(category_rows, "passing_memory_entry_count"),
            _sum_rows(category_rows, "memory_entry_count"),
        ),
        "watch_ratio": _ratio(
            _sum_rows(category_rows, "watch_memory_entry_count"),
            _sum_rows(category_rows, "memory_entry_count"),
        ),
        "blocked_ratio": _ratio(
            _sum_rows(category_rows, "blocked_memory_entry_count"),
            _sum_rows(category_rows, "memory_entry_count"),
        ),
        "stale_ratio": _ratio(
            _sum_rows(category_rows, "stale_memory_entry_count"),
            _sum_rows(category_rows, "memory_entry_count"),
        ),
        "public_status": _rollup_public_status(
            tuple(row.public_status for row in category_rows),
        ),
        "reason_codes": _report_reason_codes(category_rows),
        "reason_code_counts": _reason_code_counts(category_rows),
        "category_rows": category_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventCategoryTeamMemorySnapshotReport(
        **values,
        public_digest=_digest_payload(_report_values_payload(values)),
    )


def research_event_category_team_memory_snapshot_payload(
    report: ResearchEventCategoryTeamMemorySnapshotReport,
) -> dict[str, object]:
    if type(report) is not ResearchEventCategoryTeamMemorySnapshotReport:
        raise ValueError("report must be a ResearchEventCategoryTeamMemorySnapshotReport")
    _require_hard_flags("report", report)
    payload = _report_payload(report, digest=True)
    _reject_unsafe_public_payload("public payload", payload, allow_json=True)
    return payload


def research_event_category_team_memory_snapshot_digest(
    report: ResearchEventCategoryTeamMemorySnapshotReport,
) -> str:
    if type(report) is not ResearchEventCategoryTeamMemorySnapshotReport:
        raise ValueError("report must be a ResearchEventCategoryTeamMemorySnapshotReport")
    _require_hard_flags("report", report)
    if report.public_digest != _digest_payload(_report_payload(report, digest=False)):
        raise ValueError("public_digest does not match report")
    return report.public_digest


def _normalize_inputs(memory_rows: Iterable[object]) -> tuple[ResearchEventCategoryTeamMemoryInput, ...]:
    if type(memory_rows) not in (list, tuple):
        raise ValueError("memory rows must be a list or tuple")
    rows = tuple(memory_rows)
    seen_team_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventCategoryTeamMemoryInput:
            raise ValueError("memory rows must contain ResearchEventCategoryTeamMemoryInput")
        _require_hard_flags("memory row", row)
        if row.team_id in seen_team_ids:
            raise ValueError("memory rows must be unique")
        seen_team_ids.add(row.team_id)
    return rows


def _inputs_by_category(
    rows: tuple[ResearchEventCategoryTeamMemoryInput, ...],
) -> dict[str, tuple[ResearchEventCategoryTeamMemoryInput, ...]]:
    grouped: dict[str, list[ResearchEventCategoryTeamMemoryInput]] = {
        category_id: []
        for category_id in RESEARCH_EVENT_CATEGORY_TEAM_MEMORY_SNAPSHOT_CATEGORIES
    }
    for row in rows:
        grouped[_category_for_memory(row)].append(row)
    return {
        category_id: tuple(category_rows)
        for category_id, category_rows in grouped.items()
    }


def _category_for_memory(row: ResearchEventCategoryTeamMemoryInput) -> str:
    searchable = f"{row.team_id} {row.event_category_hint}".lower()
    for category_id, keywords in _CATEGORY_KEYWORDS:
        if any(keyword in searchable for keyword in keywords):
            return category_id
    raise ValueError("memory category route must be supported")


def _category_row(
    category_id: str,
    rows: tuple[ResearchEventCategoryTeamMemoryInput, ...],
    *,
    config: ResearchEventCategoryTeamMemorySnapshotConfig,
) -> ResearchEventCategoryTeamMemorySnapshotCategoryRow:
    memory_entry_count = _sum_inputs(rows, "memory_entry_count")
    passing_memory_entry_count = _sum_inputs(rows, "passing_memory_entry_count")
    watch_memory_entry_count = _sum_inputs(rows, "watch_memory_entry_count")
    blocked_memory_entry_count = _sum_inputs(rows, "blocked_memory_entry_count")
    stale_memory_entry_count = _sum_inputs(rows, "stale_memory_entry_count")
    coverage_ratio = _ratio(passing_memory_entry_count, memory_entry_count)
    watch_ratio = _ratio(watch_memory_entry_count, memory_entry_count)
    blocked_ratio = _ratio(blocked_memory_entry_count, memory_entry_count)
    stale_ratio = _ratio(stale_memory_entry_count, memory_entry_count)
    public_status = _category_public_status(
        memory_entry_count=memory_entry_count,
        coverage_ratio=coverage_ratio,
        stale_ratio=stale_ratio,
        blocked_ratio=blocked_ratio,
        config=config,
    )
    reason_codes = _category_reason_codes(
        memory_entry_count=memory_entry_count,
        public_status=public_status,
        coverage_ratio=coverage_ratio,
        stale_ratio=stale_ratio,
        blocked_ratio=blocked_ratio,
        config=config,
    )
    values: dict[str, object] = {
        "category_id": category_id,
        "team_count": _count_decimal(len(rows)),
        "memory_entry_count": memory_entry_count,
        "passing_memory_entry_count": passing_memory_entry_count,
        "watch_memory_entry_count": watch_memory_entry_count,
        "blocked_memory_entry_count": blocked_memory_entry_count,
        "stale_memory_entry_count": stale_memory_entry_count,
        "coverage_ratio": coverage_ratio,
        "watch_ratio": watch_ratio,
        "blocked_ratio": blocked_ratio,
        "stale_ratio": stale_ratio,
        "public_status": public_status,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventCategoryTeamMemorySnapshotCategoryRow(
        **values,
        public_digest=_digest_payload(_category_row_values_payload(values)),
    )


def _category_public_status(
    *,
    memory_entry_count: Decimal,
    coverage_ratio: Decimal,
    stale_ratio: Decimal,
    blocked_ratio: Decimal,
    config: ResearchEventCategoryTeamMemorySnapshotConfig,
) -> str:
    if memory_entry_count == ZERO_COUNT:
        return PUBLIC_STATUS_BLOCK
    if (
        coverage_ratio < config.min_watch_coverage_ratio
        or stale_ratio > config.max_watch_stale_ratio
        or blocked_ratio > config.max_watch_blocked_ratio
    ):
        return PUBLIC_STATUS_BLOCK
    if (
        coverage_ratio < config.min_pass_coverage_ratio
        or stale_ratio > config.max_pass_stale_ratio
        or blocked_ratio > config.max_pass_blocked_ratio
    ):
        return PUBLIC_STATUS_WATCH
    return PUBLIC_STATUS_PASS


def _category_reason_codes(
    *,
    memory_entry_count: Decimal,
    public_status: str,
    coverage_ratio: Decimal,
    stale_ratio: Decimal,
    blocked_ratio: Decimal,
    config: ResearchEventCategoryTeamMemorySnapshotConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = [_status_reason(public_status)]
    if memory_entry_count == ZERO_COUNT:
        reason_codes.append(NO_MEMORY_REASON)
    elif public_status == PUBLIC_STATUS_BLOCK:
        if coverage_ratio < config.min_watch_coverage_ratio:
            reason_codes.append(COVERAGE_BELOW_WATCH_REASON)
        if stale_ratio > config.max_watch_stale_ratio:
            reason_codes.append(STALE_ABOVE_WATCH_REASON)
        if blocked_ratio > config.max_watch_blocked_ratio:
            reason_codes.append(BLOCKED_ABOVE_WATCH_REASON)
    elif public_status == PUBLIC_STATUS_WATCH:
        if coverage_ratio < config.min_pass_coverage_ratio:
            reason_codes.append(COVERAGE_BELOW_PASS_REASON)
        if stale_ratio > config.max_pass_stale_ratio:
            reason_codes.append(STALE_ABOVE_PASS_REASON)
        if blocked_ratio > config.max_pass_blocked_ratio:
            reason_codes.append(BLOCKED_ABOVE_PASS_REASON)
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _status_reason(public_status: str) -> str:
    if public_status == PUBLIC_STATUS_PASS:
        return PASS_REASON
    if public_status == PUBLIC_STATUS_WATCH:
        return WATCH_REASON
    if public_status == PUBLIC_STATUS_BLOCK:
        return BLOCK_REASON
    raise ValueError("public_status must be pass, watch, or block")


def _rollup_public_status(statuses: tuple[str, ...]) -> str:
    if PUBLIC_STATUS_BLOCK in statuses:
        return PUBLIC_STATUS_BLOCK
    if PUBLIC_STATUS_WATCH in statuses:
        return PUBLIC_STATUS_WATCH
    return PUBLIC_STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchEventCategoryTeamMemorySnapshotCategoryRow, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _reason_code_counts(
    rows: tuple[ResearchEventCategoryTeamMemorySnapshotCategoryRow, ...],
) -> tuple[ResearchEventCategoryTeamMemorySnapshotReasonCodeCount, ...]:
    reason_codes = _report_reason_codes(rows)
    return tuple(
        ResearchEventCategoryTeamMemorySnapshotReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
        )
        for reason_code in reason_codes
    )


def _validate_category_row(row: ResearchEventCategoryTeamMemorySnapshotCategoryRow) -> None:
    if (
        row.passing_memory_entry_count
        + row.watch_memory_entry_count
        + row.blocked_memory_entry_count
        != row.memory_entry_count
    ):
        raise ValueError("category memory counts must sum to memory_entry_count")
    if row.stale_memory_entry_count > row.memory_entry_count:
        raise ValueError("stale_memory_entry_count must not exceed memory_entry_count")
    if row.coverage_ratio != _ratio(
        row.passing_memory_entry_count,
        row.memory_entry_count,
    ):
        raise ValueError("coverage_ratio must match category row counts")
    if row.watch_ratio != _ratio(row.watch_memory_entry_count, row.memory_entry_count):
        raise ValueError("watch_ratio must match category row counts")
    if row.blocked_ratio != _ratio(
        row.blocked_memory_entry_count,
        row.memory_entry_count,
    ):
        raise ValueError("blocked_ratio must match category row counts")
    if row.stale_ratio != _ratio(row.stale_memory_entry_count, row.memory_entry_count):
        raise ValueError("stale_ratio must match category row counts")
    if row.reason_codes[0] != _status_reason(row.public_status):
        raise ValueError("reason_codes must match public_status")


def _validate_report(report: ResearchEventCategoryTeamMemorySnapshotReport) -> None:
    rows = report.category_rows
    if report.category_count != _count_decimal(len(rows)):
        raise ValueError("category_count must match category_rows")
    if report.observed_category_count != _count_decimal(
        sum(1 for row in rows if row.team_count > ZERO_COUNT),
    ):
        raise ValueError("observed_category_count must match category_rows")
    checks = (
        ("team_count", report.team_count, _sum_rows(rows, "team_count")),
        (
            "pass_category_count",
            report.pass_category_count,
            _status_count(rows, PUBLIC_STATUS_PASS),
        ),
        (
            "watch_category_count",
            report.watch_category_count,
            _status_count(rows, PUBLIC_STATUS_WATCH),
        ),
        (
            "block_category_count",
            report.block_category_count,
            _status_count(rows, PUBLIC_STATUS_BLOCK),
        ),
        (
            "memory_entry_count",
            report.memory_entry_count,
            _sum_rows(rows, "memory_entry_count"),
        ),
        (
            "passing_memory_entry_count",
            report.passing_memory_entry_count,
            _sum_rows(rows, "passing_memory_entry_count"),
        ),
        (
            "watch_memory_entry_count",
            report.watch_memory_entry_count,
            _sum_rows(rows, "watch_memory_entry_count"),
        ),
        (
            "blocked_memory_entry_count",
            report.blocked_memory_entry_count,
            _sum_rows(rows, "blocked_memory_entry_count"),
        ),
        (
            "stale_memory_entry_count",
            report.stale_memory_entry_count,
            _sum_rows(rows, "stale_memory_entry_count"),
        ),
    )
    for field_name, actual, expected in checks:
        if actual != expected:
            raise ValueError(f"{field_name} must match category_rows")
    if report.coverage_ratio != _ratio(
        report.passing_memory_entry_count,
        report.memory_entry_count,
    ):
        raise ValueError("coverage_ratio must match report counts")
    if report.watch_ratio != _ratio(
        report.watch_memory_entry_count,
        report.memory_entry_count,
    ):
        raise ValueError("watch_ratio must match report counts")
    if report.blocked_ratio != _ratio(
        report.blocked_memory_entry_count,
        report.memory_entry_count,
    ):
        raise ValueError("blocked_ratio must match report counts")
    if report.stale_ratio != _ratio(
        report.stale_memory_entry_count,
        report.memory_entry_count,
    ):
        raise ValueError("stale_ratio must match report counts")
    if report.public_status != _rollup_public_status(
        tuple(row.public_status for row in rows),
    ):
        raise ValueError("public_status must match category_rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match category_rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match category_rows")


def _normalize_category_rows(
    rows: object,
) -> tuple[ResearchEventCategoryTeamMemorySnapshotCategoryRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("category_rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchEventCategoryTeamMemorySnapshotCategoryRow:
            raise ValueError(
                "category_rows must contain ResearchEventCategoryTeamMemorySnapshotCategoryRow",
            )
        _require_hard_flags("category row", row)
    sorted_rows = tuple(sorted(normalized, key=_category_row_sort_key))
    if tuple(row.category_id for row in sorted_rows) != (
        RESEARCH_EVENT_CATEGORY_TEAM_MEMORY_SNAPSHOT_CATEGORIES
    ):
        raise ValueError("category_rows must contain exactly the public categories")
    return sorted_rows


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchEventCategoryTeamMemorySnapshotReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    reason_counts = tuple(values)
    for value in reason_counts:
        if type(value) is not ResearchEventCategoryTeamMemorySnapshotReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventCategoryTeamMemorySnapshotReasonCodeCount",
            )
        _require_hard_flags("reason count", value)
    return tuple(sorted(reason_counts, key=lambda item: _reason_sort_key(item.reason_code)))


def _normalize_reason_codes(
    values: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(values)
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    return tuple(sorted(tuple(dict.fromkeys(reason_codes)), key=_reason_sort_key))


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain public reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain public reason codes")
    if not all(part and part.isalnum() and part == part.lower() for part in value.split("_")):
        raise ValueError(f"{field_name} must contain public reason codes")
    _reject_unsafe_public_text(field_name, value)


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in REASON_CODE_PRIORITY:
        return (REASON_CODE_PRIORITY.index(reason_code), reason_code)
    return (len(REASON_CODE_PRIORITY), reason_code)


def _category_row_sort_key(
    row: ResearchEventCategoryTeamMemorySnapshotCategoryRow,
) -> tuple[int, str]:
    return (
        RESEARCH_EVENT_CATEGORY_TEAM_MEMORY_SNAPSHOT_CATEGORIES.index(row.category_id),
        row.category_id,
    )


def _sum_inputs(
    rows: tuple[ResearchEventCategoryTeamMemoryInput, ...],
    field_name: str,
) -> Decimal:
    total = ZERO_COUNT
    for row in rows:
        total += getattr(row, field_name)
    return _normalize_count_decimal(field_name, total)


def _sum_rows(
    rows: tuple[ResearchEventCategoryTeamMemorySnapshotCategoryRow, ...],
    field_name: str,
) -> Decimal:
    total = ZERO_COUNT
    for row in rows:
        total += getattr(row, field_name)
    return _normalize_count_decimal(field_name, total)


def _status_count(
    rows: tuple[ResearchEventCategoryTeamMemorySnapshotCategoryRow, ...],
    public_status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.public_status == public_status))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value)


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    integral = value.to_integral_value(rounding=ROUND_HALF_EVEN)
    if value != integral:
        raise ValueError(f"{field_name} must be an integer Decimal")
    return integral


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_category_id(field_name: str, value: object) -> None:
    _require_public_text(field_name, value)
    if value not in RESEARCH_EVENT_CATEGORY_TEAM_MEMORY_SNAPSHOT_CATEGORIES:
        raise ValueError(f"{field_name} must be a supported public category")


def _require_public_status(field_name: str, value: object) -> None:
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be public text")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be public text")
    _reject_unsafe_public_text(field_name, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if "://" in normalized or "?" in normalized:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")
    _reject_unsafe_public_payload(label, value)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_text(field.name, field.name)
            _reject_unsafe_public_payload(label, getattr(value, field.name))
        return
    if type(value) is dict:
        if not allow_json:
            raise ValueError(f"{label} must stay constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(key, key)
            _reject_unsafe_public_payload(label, item, allow_json=True)
        return
    if type(value) is list:
        if not allow_json:
            raise ValueError(f"{label} must stay constructor-normalized")
        for item in value:
            _reject_unsafe_public_payload(label, item, allow_json=True)
        return
    if type(value) is tuple:
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) in (Decimal, datetime) or value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{label} must use Decimal-derived public values")
    raise ValueError(f"{label} contains unsupported public value")


def _category_row_values_payload(values: dict[str, object]) -> dict[str, object]:
    return {
        "category_id": values["category_id"],
        "team_count": _decimal_payload(values["team_count"]),
        "memory_entry_count": _decimal_payload(values["memory_entry_count"]),
        "passing_memory_entry_count": _decimal_payload(
            values["passing_memory_entry_count"],
        ),
        "watch_memory_entry_count": _decimal_payload(values["watch_memory_entry_count"]),
        "blocked_memory_entry_count": _decimal_payload(
            values["blocked_memory_entry_count"],
        ),
        "stale_memory_entry_count": _decimal_payload(values["stale_memory_entry_count"]),
        "coverage_ratio": _decimal_payload(values["coverage_ratio"]),
        "watch_ratio": _decimal_payload(values["watch_ratio"]),
        "blocked_ratio": _decimal_payload(values["blocked_ratio"]),
        "stale_ratio": _decimal_payload(values["stale_ratio"]),
        "public_status": values["public_status"],
        "reason_codes": list(values["reason_codes"]),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _category_row_payload(
    row: ResearchEventCategoryTeamMemorySnapshotCategoryRow,
    *,
    digest: bool,
) -> dict[str, object]:
    payload = _category_row_values_payload(
        {
            "category_id": row.category_id,
            "team_count": row.team_count,
            "memory_entry_count": row.memory_entry_count,
            "passing_memory_entry_count": row.passing_memory_entry_count,
            "watch_memory_entry_count": row.watch_memory_entry_count,
            "blocked_memory_entry_count": row.blocked_memory_entry_count,
            "stale_memory_entry_count": row.stale_memory_entry_count,
            "coverage_ratio": row.coverage_ratio,
            "watch_ratio": row.watch_ratio,
            "blocked_ratio": row.blocked_ratio,
            "stale_ratio": row.stale_ratio,
            "public_status": row.public_status,
            "reason_codes": row.reason_codes,
        },
    )
    if digest:
        payload["public_digest"] = row.public_digest
    return payload


def _reason_count_payload(
    reason_count: ResearchEventCategoryTeamMemorySnapshotReasonCodeCount,
) -> dict[str, object]:
    return {
        "reason_code": reason_count.reason_code,
        "count": _decimal_payload(reason_count.count),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_values_payload(values: dict[str, object]) -> dict[str, object]:
    return {
        "generated_at": _datetime_payload(values["generated_at"]),
        "config_version": values["config_version"],
        "category_count": _decimal_payload(values["category_count"]),
        "observed_category_count": _decimal_payload(values["observed_category_count"]),
        "team_count": _decimal_payload(values["team_count"]),
        "pass_category_count": _decimal_payload(values["pass_category_count"]),
        "watch_category_count": _decimal_payload(values["watch_category_count"]),
        "block_category_count": _decimal_payload(values["block_category_count"]),
        "memory_entry_count": _decimal_payload(values["memory_entry_count"]),
        "passing_memory_entry_count": _decimal_payload(
            values["passing_memory_entry_count"],
        ),
        "watch_memory_entry_count": _decimal_payload(values["watch_memory_entry_count"]),
        "blocked_memory_entry_count": _decimal_payload(
            values["blocked_memory_entry_count"],
        ),
        "stale_memory_entry_count": _decimal_payload(values["stale_memory_entry_count"]),
        "coverage_ratio": _decimal_payload(values["coverage_ratio"]),
        "watch_ratio": _decimal_payload(values["watch_ratio"]),
        "blocked_ratio": _decimal_payload(values["blocked_ratio"]),
        "stale_ratio": _decimal_payload(values["stale_ratio"]),
        "public_status": values["public_status"],
        "reason_codes": list(values["reason_codes"]),
        "reason_code_counts": [
            _reason_count_payload(reason_count)
            for reason_count in values["reason_code_counts"]
        ],
        "category_rows": [
            _category_row_payload(row, digest=True)
            for row in values["category_rows"]
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_payload(
    report: ResearchEventCategoryTeamMemorySnapshotReport,
    *,
    digest: bool,
) -> dict[str, object]:
    payload = _report_values_payload(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "category_count": report.category_count,
            "observed_category_count": report.observed_category_count,
            "team_count": report.team_count,
            "pass_category_count": report.pass_category_count,
            "watch_category_count": report.watch_category_count,
            "block_category_count": report.block_category_count,
            "memory_entry_count": report.memory_entry_count,
            "passing_memory_entry_count": report.passing_memory_entry_count,
            "watch_memory_entry_count": report.watch_memory_entry_count,
            "blocked_memory_entry_count": report.blocked_memory_entry_count,
            "stale_memory_entry_count": report.stale_memory_entry_count,
            "coverage_ratio": report.coverage_ratio,
            "watch_ratio": report.watch_ratio,
            "blocked_ratio": report.blocked_ratio,
            "stale_ratio": report.stale_ratio,
            "public_status": report.public_status,
            "reason_codes": report.reason_codes,
            "reason_code_counts": report.reason_code_counts,
            "category_rows": report.category_rows,
        },
    )
    if digest:
        payload["public_digest"] = report.public_digest
    return payload


def _decimal_payload(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("public numeric value must be a Decimal")
    return format(value, "f")


def _datetime_payload(value: object) -> str:
    return _as_utc("generated_at", value).isoformat()


def _digest_payload(payload: dict[str, object]) -> str:
    _reject_unsafe_public_payload("digest payload", payload, allow_json=True)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()
