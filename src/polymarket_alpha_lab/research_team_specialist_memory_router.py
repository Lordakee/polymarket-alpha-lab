"""Pure report-only specialist memory routing plan builder."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_ROUTER_CONFIG_VERSION = (
    "research-team-specialist-memory-router-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

PASS_REASON = "research_team_specialist_memory_router_pass"
WATCH_EVIDENCE_REASON = "research_team_specialist_memory_router_watch_evidence"
WATCH_COVERAGE_REASON = "research_team_specialist_memory_router_watch_coverage"
WATCH_MEMORY_FIT_REASON = "research_team_specialist_memory_router_watch_memory_fit"
LOW_EVIDENCE_REASON = "research_team_specialist_memory_router_low_evidence"
LOW_COVERAGE_REASON = "research_team_specialist_memory_router_low_coverage"
LOW_MEMORY_FIT_REASON = "research_team_specialist_memory_router_low_memory_fit"
EMPTY_INPUT_REASON = "research_team_specialist_memory_router_empty_input"

REASON_CODE_SEQUENCE = (
    LOW_EVIDENCE_REASON,
    LOW_COVERAGE_REASON,
    LOW_MEMORY_FIT_REASON,
    WATCH_EVIDENCE_REASON,
    WATCH_COVERAGE_REASON,
    WATCH_MEMORY_FIT_REASON,
    PASS_REASON,
    EMPTY_INPUT_REASON,
)

STATUS_NEXT_STEPS = {
    STATUS_PASS: "allow_local_memory_queue_plan",
    STATUS_WATCH: "watch_local_memory_queue_plan",
    STATUS_BLOCK: "block_local_memory_queue_plan",
}

PUBLIC_CATEGORY_TO_TEAM = {
    "politics": "politics",
    "crypto": "crypto",
    "finance.crypto.btc": "crypto",
    "finance.crypto.eth": "crypto",
    "macro": "macro",
    "finance.macro.rates": "macro",
    "gold": "gold",
    "finance.commodities.gold": "gold",
    "soccer": "soccer",
    "sports.soccer": "soccer",
    "basketball": "basketball",
    "sports.basketball": "basketball",
}

PUBLIC_STATUSES = tuple(STATUS_NEXT_STEPS)
SPECIALIST_TEAM_IDS = (
    "politics",
    "crypto",
    "macro",
    "gold",
    "soccer",
    "basketball",
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
THREE = Decimal("3.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join_parts("raw"),
        _join_parts("can", "didate"),
        _join_parts("mar", "ket"),
        _join_parts("slug"),
        _join_parts("ques", "tion"),
        _join_parts("sou", "rce"),
        _join_parts("ref"),
        _join_parts("ur", "l"),
        _join_parts("ht", "tp"),
        _join_parts("te", "xt"),
        _join_parts("ds", "n"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("or", "der"),
        _join_parts("tra", "de"),
        _join_parts("posi", "tion"),
        _join_parts("b", "uy"),
        _join_parts("se", "ll"),
        _join_parts("recom", "mend"),
    ),
)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRouterConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_ROUTER_CONFIG_VERSION
    pass_min_score: Decimal = Decimal("0.700000")
    block_min_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRouterConfig:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRouterConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistMemoryRouterConfig:
            raise ValueError(
                "config must be exactly ResearchTeamSpecialistMemoryRouterConfig",
            )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "pass_min_score",
            _require_ratio_decimal("pass_min_score", self.pass_min_score),
        )
        object.__setattr__(
            self,
            "block_min_score",
            _require_ratio_decimal("block_min_score", self.block_min_score),
        )
        if self.block_min_score >= self.pass_min_score:
            raise ValueError("block_min_score must be below pass_min_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRouterInput:
    public_event_key: str
    event_category: str
    evidence_score: Decimal
    coverage_score: Decimal
    memory_fit_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRouterInput:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRouterInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistMemoryRouterInput:
            raise ValueError(
                "input must be exactly ResearchTeamSpecialistMemoryRouterInput",
            )
        _require_public_string("public_event_key", self.public_event_key)
        _require_public_category("event_category", self.event_category)
        for field_name in ("evidence_score", "coverage_score", "memory_fit_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_tuple("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRouterRow:
    public_event_key: str
    event_category: str
    specialist_team_id: str
    memory_queue_key: str
    public_status: str
    routing_score: Decimal
    evidence_score: Decimal
    coverage_score: Decimal
    memory_fit_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRouterRow:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRouterRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistMemoryRouterRow:
            raise ValueError("row must be exactly ResearchTeamSpecialistMemoryRouterRow")
        _require_public_string("public_event_key", self.public_event_key)
        _require_public_category("event_category", self.event_category)
        _require_specialist_team_id("specialist_team_id", self.specialist_team_id)
        _require_public_string("memory_queue_key", self.memory_queue_key)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        object.__setattr__(
            self,
            "routing_score",
            _require_ratio_decimal("routing_score", self.routing_score),
        )
        for field_name in ("evidence_score", "coverage_score", "memory_fit_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRouterDigest:
    public_status: str
    next_step: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    team_status_counts: tuple[tuple[str, str, Decimal], ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRouterDigest:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRouterDigest does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistMemoryRouterDigest:
            raise ValueError(
                "digest must be exactly ResearchTeamSpecialistMemoryRouterDigest",
            )
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        if self.next_step != STATUS_NEXT_STEPS[self.public_status]:
            raise ValueError("next_step must match public_status")
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_status_counts",
            _normalize_team_status_counts(self.team_status_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_digest_consistency(self)
        _require_hard_flags("digest", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRouterReport:
    generated_at: datetime
    config_version: str
    public_status: str
    next_step: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    rows: tuple[ResearchTeamSpecialistMemoryRouterRow, ...]
    digest: ResearchTeamSpecialistMemoryRouterDigest
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRouterReport:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRouterReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecialistMemoryRouterReport:
            raise ValueError("report must be exactly ResearchTeamSpecialistMemoryRouterReport")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        if self.next_step != STATUS_NEXT_STEPS[self.public_status]:
            raise ValueError("next_step must match public_status")
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows("rows", self.rows))
        if type(self.digest) is not ResearchTeamSpecialistMemoryRouterDigest:
            raise ValueError("digest must be ResearchTeamSpecialistMemoryRouterDigest")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_research_team_specialist_memory_router_report(
    rows: tuple[ResearchTeamSpecialistMemoryRouterInput, ...],
    *,
    config: ResearchTeamSpecialistMemoryRouterConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamSpecialistMemoryRouterReport:
    cfg = config or ResearchTeamSpecialistMemoryRouterConfig()
    if type(cfg) is not ResearchTeamSpecialistMemoryRouterConfig:
        raise TypeError(
            "config must be exactly ResearchTeamSpecialistMemoryRouterConfig",
        )
    observed_at = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows("rows", rows)
    report_rows = tuple(
        sorted(
            (_build_row(row, config=cfg) for row in input_rows),
            key=lambda row: (
                _status_rank(row.public_status),
                row.specialist_team_id,
                row.public_event_key,
            ),
        ),
    )
    public_status = _public_status(report_rows)
    reason_codes = _report_reason_codes(report_rows)
    digest = ResearchTeamSpecialistMemoryRouterDigest(
        public_status=public_status,
        next_step=STATUS_NEXT_STEPS[public_status],
        event_count=_count_decimal(report_rows),
        pass_count=_status_count(report_rows, STATUS_PASS),
        watch_count=_status_count(report_rows, STATUS_WATCH),
        block_count=_status_count(report_rows, STATUS_BLOCK),
        team_status_counts=_team_status_counts(report_rows),
        reason_codes=reason_codes,
    )
    return ResearchTeamSpecialistMemoryRouterReport(
        generated_at=observed_at,
        config_version=cfg.config_version,
        public_status=digest.public_status,
        next_step=digest.next_step,
        event_count=digest.event_count,
        pass_count=digest.pass_count,
        watch_count=digest.watch_count,
        block_count=digest.block_count,
        rows=report_rows,
        digest=digest,
        reason_codes=reason_codes,
    )


def public_supabase_memory_router_payload(
    report: ResearchTeamSpecialistMemoryRouterReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamSpecialistMemoryRouterReport:
        raise TypeError("report must be exactly ResearchTeamSpecialistMemoryRouterReport")
    _require_hard_flags("report", report)
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "public_status": report.public_status,
        "next_step": report.next_step,
        "event_count": str(report.event_count),
        "pass_count": str(report.pass_count),
        "watch_count": str(report.watch_count),
        "block_count": str(report.block_count),
        "digest": {
            "public_status": report.digest.public_status,
            "next_step": report.digest.next_step,
            "event_count": str(report.digest.event_count),
            "pass_count": str(report.digest.pass_count),
            "watch_count": str(report.digest.watch_count),
            "block_count": str(report.digest.block_count),
            "team_status_counts": [
                {
                    "specialist_team_id": team_id,
                    "public_status": public_status,
                    "event_count": str(event_count),
                }
                for team_id, public_status, event_count in report.digest.team_status_counts
            ],
            "reason_codes": list(report.digest.reason_codes),
        },
        "local_supabase_plan": [
            {
                "public_event_key": row.public_event_key,
                "event_category": row.event_category,
                "specialist_team_id": row.specialist_team_id,
                "memory_queue_key": row.memory_queue_key,
                "public_status": row.public_status,
                "routing_score": str(row.routing_score),
                "evidence_score": str(row.evidence_score),
                "coverage_score": str(row.coverage_score),
                "memory_fit_score": str(row.memory_fit_score),
                "reason_codes": list(row.reason_codes),
            }
            for row in report.rows
        ],
        "reason_codes": list(report.reason_codes),
    }
    _reject_public_payload_leaks(payload)
    return payload


def _build_row(
    row: ResearchTeamSpecialistMemoryRouterInput,
    *,
    config: ResearchTeamSpecialistMemoryRouterConfig,
) -> ResearchTeamSpecialistMemoryRouterRow:
    team_id = PUBLIC_CATEGORY_TO_TEAM[row.event_category]
    routing_score = _ratio(
        row.evidence_score + row.coverage_score + row.memory_fit_score,
        THREE,
    )
    public_status, reason_codes = _row_status_and_reasons(row, config=config)
    return ResearchTeamSpecialistMemoryRouterRow(
        public_event_key=row.public_event_key,
        event_category=row.event_category,
        specialist_team_id=team_id,
        memory_queue_key=f"team_memory.{team_id}.{public_status}",
        public_status=public_status,
        routing_score=routing_score,
        evidence_score=row.evidence_score,
        coverage_score=row.coverage_score,
        memory_fit_score=row.memory_fit_score,
        reason_codes=reason_codes,
    )


def _row_status_and_reasons(
    row: ResearchTeamSpecialistMemoryRouterInput,
    *,
    config: ResearchTeamSpecialistMemoryRouterConfig,
) -> tuple[str, tuple[str, ...]]:
    low_reasons: list[str] = []
    if row.evidence_score < config.block_min_score:
        low_reasons.append(LOW_EVIDENCE_REASON)
    if row.coverage_score < config.block_min_score:
        low_reasons.append(LOW_COVERAGE_REASON)
    if row.memory_fit_score < config.block_min_score:
        low_reasons.append(LOW_MEMORY_FIT_REASON)
    if low_reasons:
        return STATUS_BLOCK, tuple(low_reasons)

    watch_reasons: list[str] = []
    if row.evidence_score < config.pass_min_score:
        watch_reasons.append(WATCH_EVIDENCE_REASON)
    if row.coverage_score < config.pass_min_score:
        watch_reasons.append(WATCH_COVERAGE_REASON)
    if row.memory_fit_score < config.pass_min_score:
        watch_reasons.append(WATCH_MEMORY_FIT_REASON)
    if watch_reasons:
        return STATUS_WATCH, tuple(watch_reasons)
    return STATUS_PASS, (PASS_REASON,)


def _public_status(rows: tuple[ResearchTeamSpecialistMemoryRouterRow, ...]) -> str:
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistMemoryRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_INPUT_REASON,)
    reason_codes = frozenset(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in reason_codes
    )


def _team_status_counts(
    rows: tuple[ResearchTeamSpecialistMemoryRouterRow, ...],
) -> tuple[tuple[str, str, Decimal], ...]:
    counts: dict[tuple[str, str], Decimal] = {}
    for row in rows:
        key = (row.specialist_team_id, row.public_status)
        counts[key] = counts.get(key, ZERO) + ONE
    return tuple(
        (team_id, public_status, count.quantize(QUANT))
        for (team_id, public_status), count in sorted(counts.items())
    )


def _normalize_input_rows(
    field_name: str,
    value: tuple[ResearchTeamSpecialistMemoryRouterInput, ...],
) -> tuple[ResearchTeamSpecialistMemoryRouterInput, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    public_event_keys: set[str] = set()
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchTeamSpecialistMemoryRouterInput:
            raise ValueError(
                f"{field_name} must contain ResearchTeamSpecialistMemoryRouterInput",
            )
        _require_hard_flags("input row", row)
        if row.public_event_key in public_event_keys:
            raise ValueError("public_event_key values must be unique")
        public_event_keys.add(row.public_event_key)
    return rows


def _normalize_rows(
    field_name: str,
    value: tuple[ResearchTeamSpecialistMemoryRouterRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryRouterRow, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    rows = tuple(value)
    expected_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.public_status),
                row.specialist_team_id,
                row.public_event_key,
            ),
        ),
    )
    if rows != expected_rows:
        raise ValueError(f"{field_name} must be sorted deterministically")
    public_event_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamSpecialistMemoryRouterRow:
            raise ValueError(
                f"{field_name} must contain ResearchTeamSpecialistMemoryRouterRow",
            )
        _require_hard_flags("row", row)
        if row.public_event_key in public_event_keys:
            raise ValueError("public_event_key values must be unique")
        public_event_keys.add(row.public_event_key)
    return rows


def _normalize_team_status_counts(
    value: tuple[tuple[str, str, Decimal], ...],
) -> tuple[tuple[str, str, Decimal], ...]:
    if not isinstance(value, tuple):
        raise TypeError("team_status_counts must be a tuple")
    normalized: list[tuple[str, str, Decimal]] = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 3:
            raise ValueError("team_status_counts must contain three-value tuples")
        team_id, public_status, event_count = item
        _require_specialist_team_id("team_status_counts team_id", team_id)
        _require_member("team_status_counts public_status", public_status, PUBLIC_STATUSES)
        normalized.append(
            (
                team_id,
                public_status,
                _require_nonnegative_decimal("team_status_counts event_count", event_count),
            ),
        )
    ordered = tuple(sorted(normalized))
    if tuple(normalized) != ordered:
        raise ValueError("team_status_counts must be sorted")
    if len(set((team_id, status) for team_id, status, _ in ordered)) != len(ordered):
        raise ValueError("team_status_counts must be unique")
    return ordered


def _validate_row_consistency(row: ResearchTeamSpecialistMemoryRouterRow) -> None:
    if PUBLIC_CATEGORY_TO_TEAM[row.event_category] != row.specialist_team_id:
        raise ValueError("specialist_team_id must match event_category")
    if row.memory_queue_key != (
        f"team_memory.{row.specialist_team_id}.{row.public_status}"
    ):
        raise ValueError("memory_queue_key must match team and public_status")
    expected_score = _ratio(
        row.evidence_score + row.coverage_score + row.memory_fit_score,
        THREE,
    )
    if row.routing_score != expected_score:
        raise ValueError("routing_score must match component scores")
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.public_status != expected_status:
        raise ValueError("public_status must match reason_codes")


def _validate_digest_consistency(
    digest: ResearchTeamSpecialistMemoryRouterDigest,
) -> None:
    if digest.event_count != digest.pass_count + digest.watch_count + digest.block_count:
        raise ValueError("event_count must match status counts")
    if _sum_decimal(count for _, _, count in digest.team_status_counts) != digest.event_count:
        raise ValueError("team_status_counts must match event_count")


def _validate_report_consistency(
    report: ResearchTeamSpecialistMemoryRouterReport,
) -> None:
    if report.public_status != _public_status(report.rows):
        raise ValueError("public_status must match rows")
    if report.event_count != _count_decimal(report.rows):
        raise ValueError("event_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    expected_digest = ResearchTeamSpecialistMemoryRouterDigest(
        public_status=report.public_status,
        next_step=report.next_step,
        event_count=report.event_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        team_status_counts=_team_status_counts(report.rows),
        reason_codes=report.reason_codes,
    )
    if report.digest != expected_digest:
        raise ValueError("digest must match report")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code in (LOW_EVIDENCE_REASON, LOW_COVERAGE_REASON, LOW_MEMORY_FIT_REASON)
        for reason_code in reason_codes
    ):
        return STATUS_BLOCK
    if any(
        reason_code
        in (WATCH_EVIDENCE_REASON, WATCH_COVERAGE_REASON, WATCH_MEMORY_FIT_REASON)
        for reason_code in reason_codes
    ):
        return STATUS_WATCH
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    raise ValueError("reason_codes must imply a public_status")


def _normalize_reason_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    unique_values = frozenset(value)
    if len(unique_values) != len(value):
        raise ValueError(f"{field_name} must be unique")
    for reason_code in value:
        if reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError(f"{field_name} contains unknown reason_code")
    return tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in unique_values
    )


def _normalize_public_tuple(
    field_name: str,
    value: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for item in value:
        _require_public_string(field_name, item)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _require_public_category(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if value not in PUBLIC_CATEGORY_TO_TEAM:
        raise ValueError(f"{field_name} must be a known public category")
    return value


def _require_specialist_team_id(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if value not in SPECIALIST_TEAM_IDS:
        raise ValueError(f"{field_name} must be a known specialist team")
    return value


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be canonical")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _require_member(
    field_name: str,
    value: str,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} must keep {flag_name}=True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be a whole second")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANT)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the unit interval")
    return decimal_value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(QUANT)


def _count_decimal(values: tuple[object, ...]) -> Decimal:
    return Decimal(len(values)).quantize(QUANT)


def _status_count(
    rows: tuple[ResearchTeamSpecialistMemoryRouterRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.public_status == status)).quantize(QUANT)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return total.quantize(QUANT)


def _status_rank(status: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[status]


def _reject_public_payload_leaks(value: object) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError("payload contains unsafe public text")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_payload_leaks(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload_leaks(item)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_ROUTER_CONFIG_VERSION",
    "ResearchTeamSpecialistMemoryRouterConfig",
    "ResearchTeamSpecialistMemoryRouterDigest",
    "ResearchTeamSpecialistMemoryRouterInput",
    "ResearchTeamSpecialistMemoryRouterReport",
    "ResearchTeamSpecialistMemoryRouterRow",
    "build_research_team_specialist_memory_router_report",
    "public_supabase_memory_router_payload",
)
