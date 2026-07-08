"""Pure report-only rollup for cross-team research candidate priority."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_CANDIDATE_RESEARCH_PRIORITY_ROLLUP_DASHBOARD_CONFIG_VERSION = (
    "research-candidate-research-priority-rollup-dashboard-v0"
)
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_SET = frozenset(PUBLIC_STATUSES)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

TIMING_WEIGHT = Decimal("0.285775")
UNCERTAINTY_WEIGHT = Decimal("0.506046")
FRESHNESS_WEIGHT = Decimal("0.091323")
DIVERSITY_WEIGHT = Decimal("0.050000")
COST_WEIGHT = Decimal("0.100000")

REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "summary_count",
        "team_count",
        "pass_count",
        "watch_count",
        "block_count",
        "status",
        "top_summary_ref",
        "top_team_ref",
        "max_priority_score",
        "average_priority_score",
        "public_summary",
        "reason_codes",
        "team_rollups",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
TEAM_PAYLOAD_KEYS = frozenset(
    (
        "team_ref",
        "summary_count",
        "pass_count",
        "watch_count",
        "block_count",
        "status",
        "max_priority_score",
        "average_priority_score",
        "public_summary",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "summary_ref",
        "team_ref",
        "category_ref",
        "observed_at",
        "status",
        "priority_score",
        "evidence_freshness_score",
        "source_diversity_score",
        "market_timing_score",
        "uncertainty_score",
        "cost_friction_score",
        "public_summary",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REPORT_DECIMAL_FIELDS = frozenset(
    (
        "summary_count",
        "team_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_priority_score",
    ),
)
OPTIONAL_REPORT_DECIMAL_FIELDS = frozenset(("average_priority_score",))
TEAM_DECIMAL_FIELDS = frozenset(
    (
        "summary_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_priority_score",
    ),
)
OPTIONAL_TEAM_DECIMAL_FIELDS = frozenset(("average_priority_score",))
ROW_DECIMAL_FIELDS = frozenset(
    (
        "priority_score",
        "evidence_freshness_score",
        "source_diversity_score",
        "market_timing_score",
        "uncertainty_score",
        "cost_friction_score",
    ),
)
UNSAFE_FIELD_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "raw_candidate",
        "raw_payload",
        "source_ref",
        "source_url",
        "source_text",
        "private",
        "secret",
        "token",
        "dsn",
        "table",
        "bro" + "ker",
        "li" + "ve",
        "exec",
        "db",
        "data" + "base",
        "net" + "work",
        "wal" + "let",
        "au" + "th",
        "ord" + "er",
        "tra" + "de",
        "bu" + "y",
        "sel" + "l",
        "rec" + "ommend",
    ),
)
UNSAFE_VALUE_FRAGMENTS = frozenset(
    (
        "http://",
        "https://",
        "source_url",
        "source_text",
        "private",
        "secret",
        "token",
        "dsn",
        "table:",
        "bro" + "ker",
        "li" + "ve",
        "exec",
        "data" + "base",
        "net" + "work",
        "wal" + "let",
        "au" + "th",
        "ord" + "er",
        "tra" + "de",
        "bu" + "y",
        "sel" + "l",
        "rec" + "ommend",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} subclassing is not allowed")


@dataclass(frozen=True)
class ResearchCandidateResearchPriorityRollupConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_CANDIDATE_RESEARCH_PRIORITY_ROLLUP_DASHBOARD_CONFIG_VERSION
    )
    watch_priority_threshold: Decimal = Decimal("0.450000")
    min_evidence_freshness_score: Decimal = Decimal("0.250000")
    min_source_diversity_score: Decimal = Decimal("0.300000")
    max_cost_friction_score: Decimal = Decimal("0.750000")
    urgent_market_timing_threshold: Decimal = Decimal("0.800000")
    high_uncertainty_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchCandidateResearchPriorityRollupConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_CANDIDATE_RESEARCH_PRIORITY_ROLLUP_DASHBOARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_priority_threshold",
            "min_evidence_freshness_score",
            "min_source_diversity_score",
            "max_cost_friction_score",
            "urgent_market_timing_threshold",
            "high_uncertainty_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchCandidateResearchPriorityInput(_FinalPublicDataclass):
    summary_ref: str
    team_ref: str
    category_ref: str
    observed_at: datetime
    evidence_freshness_score: Decimal
    source_diversity_score: Decimal
    market_timing_score: Decimal
    uncertainty_score: Decimal
    cost_friction_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCandidateResearchPriorityInput, "input")
        for field_name in ("summary_ref", "team_ref", "category_ref"):
            _require_public_ref(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "evidence_freshness_score",
            "source_diversity_score",
            "market_timing_score",
            "uncertainty_score",
            "cost_friction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_surface("input", self)


@dataclass(frozen=True)
class ResearchCandidateResearchPriorityRow(_FinalPublicDataclass):
    summary_ref: str
    team_ref: str
    category_ref: str
    observed_at: datetime
    status: str
    priority_score: Decimal
    evidence_freshness_score: Decimal
    source_diversity_score: Decimal
    market_timing_score: Decimal
    uncertainty_score: Decimal
    cost_friction_score: Decimal
    public_summary: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCandidateResearchPriorityRow, "row")
        for field_name in ("summary_ref", "team_ref", "category_ref"):
            _require_public_ref(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        for field_name in ROW_DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_string("public_summary", self.public_summary)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchCandidateResearchPriorityTeamRollup(_FinalPublicDataclass):
    team_ref: str
    summary_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    max_priority_score: Decimal
    average_priority_score: Decimal | None
    public_summary: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCandidateResearchPriorityTeamRollup, "team")
        _require_public_ref("team_ref", self.team_ref)
        for field_name in TEAM_DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_priority_score",
            _require_optional_probability_decimal(
                "average_priority_score",
                self.average_priority_score,
            ),
        )
        _require_status("status", self.status)
        _require_public_string("public_summary", self.public_summary)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("team", self)
        _validate_team_consistency(self)
        _reject_unsafe_public_surface("team", self)


@dataclass(frozen=True)
class ResearchCandidateResearchPriorityRollupDashboard(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    summary_count: Decimal
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    top_summary_ref: str | None
    top_team_ref: str | None
    max_priority_score: Decimal
    average_priority_score: Decimal | None
    public_summary: tuple[str, ...]
    reason_codes: tuple[str, ...]
    team_rollups: tuple[ResearchCandidateResearchPriorityTeamRollup, ...]
    rows: tuple[ResearchCandidateResearchPriorityRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchCandidateResearchPriorityRollupDashboard,
            "dashboard",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_CANDIDATE_RESEARCH_PRIORITY_ROLLUP_DASHBOARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in REPORT_DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_priority_score",
            _require_optional_probability_decimal(
                "average_priority_score",
                self.average_priority_score,
            ),
        )
        _require_status("status", self.status)
        for field_name in ("top_summary_ref", "top_team_ref"):
            value = getattr(self, field_name)
            if value is not None:
                _require_public_ref(field_name, value)
        object.__setattr__(
            self,
            "public_summary",
            _require_public_string_tuple(
                "public_summary",
                self.public_summary,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        if type(self.team_rollups) is not tuple:
            raise ValueError("team_rollups must be a tuple")
        for team in self.team_rollups:
            if type(team) is not ResearchCandidateResearchPriorityTeamRollup:
                raise ValueError("team_rollups must contain team rollups")
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchCandidateResearchPriorityRow:
                raise ValueError("rows must contain dashboard rows")
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("dashboard", self)
        _validate_dashboard_consistency(self)
        _reject_unsafe_public_surface("dashboard", self)
        if self.derived_validation_digest != _dashboard_digest(self):
            raise ValueError("derived_validation_digest must match dashboard values")


def build_research_candidate_research_priority_rollup_dashboard(
    inputs: Iterable[ResearchCandidateResearchPriorityInput],
    *,
    config: ResearchCandidateResearchPriorityRollupConfig,
    generated_at: datetime,
) -> ResearchCandidateResearchPriorityRollupDashboard:
    if type(config) is not ResearchCandidateResearchPriorityRollupConfig:
        raise ValueError("config must be a ResearchCandidateResearchPriorityRollupConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_inputs(inputs)
    for item in items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    rows = tuple(_row_from_input(item, config) for item in items)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    team_rollups = _team_rollups(sorted_rows)
    status = _summary_status(sorted_rows)
    reason_codes = _dashboard_reason_codes(sorted_rows)
    max_score = max((row.priority_score for row in sorted_rows), default=ZERO)
    top_row = sorted_rows[0] if sorted_rows else None
    average_score = _average_decimal(tuple(row.priority_score for row in sorted_rows))
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "summary_count": _decimal_count(len(sorted_rows)),
        "team_count": _decimal_count(len(team_rollups)),
        "pass_count": _status_count(sorted_rows, "pass"),
        "watch_count": _status_count(sorted_rows, "watch"),
        "block_count": _status_count(sorted_rows, "block"),
        "status": status,
        "top_summary_ref": top_row.summary_ref if top_row is not None else None,
        "top_team_ref": top_row.team_ref if top_row is not None else None,
        "max_priority_score": max_score,
        "average_priority_score": average_score,
        "public_summary": _dashboard_public_summary(status, sorted_rows),
        "reason_codes": reason_codes,
        "team_rollups": team_rollups,
        "rows": sorted_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    digest = _digest_payload(_json_ready(values))
    return ResearchCandidateResearchPriorityRollupDashboard(
        **values,
        derived_validation_digest=digest,
    )


def research_candidate_research_priority_rollup_dashboard_payload(
    dashboard: ResearchCandidateResearchPriorityRollupDashboard | dict[str, Any],
) -> dict[str, Any]:
    if type(dashboard) is ResearchCandidateResearchPriorityRollupDashboard:
        _require_hard_flags("dashboard", dashboard)
        payload = _json_ready(dashboard)
    elif type(dashboard) is dict:
        payload = _json_ready(dashboard)
    else:
        raise ValueError(
            "dashboard must be a ResearchCandidateResearchPriorityRollupDashboard",
        )
    if type(payload) is not dict:
        raise ValueError("dashboard payload must be a JSON object")
    validate_research_candidate_research_priority_rollup_dashboard_payload(payload)
    return payload


def validate_research_candidate_research_priority_rollup_dashboard_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("payload", payload)
    _reject_public_numbers(payload)
    _validate_dashboard_payload(payload)
    return True


def _normalize_inputs(
    inputs: Iterable[ResearchCandidateResearchPriorityInput],
) -> tuple[ResearchCandidateResearchPriorityInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized: list[ResearchCandidateResearchPriorityInput] = []
    seen_summary_refs: set[str] = set()
    for item in inputs:
        if type(item) is not ResearchCandidateResearchPriorityInput:
            raise ValueError("inputs must contain ResearchCandidateResearchPriorityInput")
        _require_hard_flags("input", item)
        _reject_unsafe_public_surface("input", item)
        if item.summary_ref in seen_summary_refs:
            raise ValueError("duplicate summary_ref")
        seen_summary_refs.add(item.summary_ref)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.summary_ref))


def _row_from_input(
    item: ResearchCandidateResearchPriorityInput,
    config: ResearchCandidateResearchPriorityRollupConfig,
) -> ResearchCandidateResearchPriorityRow:
    priority_score = _priority_score(item)
    block_reasons = _block_reasons(item, config)
    watch_reasons = _watch_reasons(item, config, priority_score)
    if block_reasons:
        status = "block"
        status_reason = ("research_priority_block",)
    elif watch_reasons:
        status = "watch"
        status_reason = ("research_priority_watch",)
    else:
        status = "pass"
        status_reason = ("research_priority_clear",)
    return ResearchCandidateResearchPriorityRow(
        summary_ref=item.summary_ref,
        team_ref=item.team_ref,
        category_ref=item.category_ref,
        observed_at=item.observed_at,
        status=status,
        priority_score=priority_score,
        evidence_freshness_score=item.evidence_freshness_score,
        source_diversity_score=item.source_diversity_score,
        market_timing_score=item.market_timing_score,
        uncertainty_score=item.uncertainty_score,
        cost_friction_score=item.cost_friction_score,
        public_summary=_row_public_summary(status),
        reason_codes=_unique_sorted_reason_codes(
            (*block_reasons, *watch_reasons, *item.reason_codes, *status_reason),
        ),
    )


def _priority_score(item: ResearchCandidateResearchPriorityInput) -> Decimal:
    value = (
        item.market_timing_score * TIMING_WEIGHT
        + item.uncertainty_score * UNCERTAINTY_WEIGHT
        + item.evidence_freshness_score * FRESHNESS_WEIGHT
        + item.source_diversity_score * DIVERSITY_WEIGHT
        + item.cost_friction_score * COST_WEIGHT
    )
    return _quantize_probability(value)


def _block_reasons(
    item: ResearchCandidateResearchPriorityInput,
    config: ResearchCandidateResearchPriorityRollupConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.cost_friction_score > config.max_cost_friction_score:
        reasons.append("cost_friction_limit")
    if item.evidence_freshness_score < config.min_evidence_freshness_score:
        reasons.append("evidence_freshness_gap")
    if item.source_diversity_score < config.min_source_diversity_score:
        reasons.append("source_diversity_gap")
    return tuple(reasons)


def _watch_reasons(
    item: ResearchCandidateResearchPriorityInput,
    config: ResearchCandidateResearchPriorityRollupConfig,
    priority_score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.market_timing_score >= config.urgent_market_timing_threshold:
        reasons.append("market_timing_pressure")
    if item.uncertainty_score >= config.high_uncertainty_threshold:
        reasons.append("uncertainty_high")
    if priority_score >= config.watch_priority_threshold and not reasons:
        reasons.append("research_priority_threshold")
    return tuple(reasons)


def _team_rollups(
    rows: tuple[ResearchCandidateResearchPriorityRow, ...],
) -> tuple[ResearchCandidateResearchPriorityTeamRollup, ...]:
    team_refs = tuple(sorted({row.team_ref for row in rows}))
    rollups = tuple(_team_rollup(team_ref, rows) for team_ref in team_refs)
    return tuple(sorted(rollups, key=_team_sort_key))


def _team_rollup(
    team_ref: str,
    rows: tuple[ResearchCandidateResearchPriorityRow, ...],
) -> ResearchCandidateResearchPriorityTeamRollup:
    team_rows = tuple(row for row in rows if row.team_ref == team_ref)
    status = _summary_status(team_rows)
    reason_codes = _team_reason_codes(team_rows)
    return ResearchCandidateResearchPriorityTeamRollup(
        team_ref=team_ref,
        summary_count=_decimal_count(len(team_rows)),
        pass_count=_status_count(team_rows, "pass"),
        watch_count=_status_count(team_rows, "watch"),
        block_count=_status_count(team_rows, "block"),
        status=status,
        max_priority_score=max((row.priority_score for row in team_rows), default=ZERO),
        average_priority_score=_average_decimal(
            tuple(row.priority_score for row in team_rows),
        ),
        public_summary=_team_public_summary(status),
        reason_codes=reason_codes,
    )


def _dashboard_reason_codes(
    rows: tuple[ResearchCandidateResearchPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("research_priority_rollup_empty",)
    reason_codes: list[str] = []
    if any(row.status == "block" for row in rows):
        reason_codes.append("research_priority_block_present")
    if any("cost_friction_limit" in row.reason_codes for row in rows):
        reason_codes.append("cost_friction_limit_present")
    if any("evidence_freshness_gap" in row.reason_codes for row in rows):
        reason_codes.append("evidence_freshness_gap_present")
    if any("source_diversity_gap" in row.reason_codes for row in rows):
        reason_codes.append("source_diversity_gap_present")
    if any(row.status == "watch" for row in rows):
        reason_codes.append("research_priority_watch_present")
    if not reason_codes:
        reason_codes.append("research_priority_rollup_clear")
    return tuple(reason_codes)


def _team_reason_codes(
    rows: tuple[ResearchCandidateResearchPriorityRow, ...],
) -> tuple[str, ...]:
    if any(row.status == "block" for row in rows):
        return ("team_research_priority_block_present",)
    if any(row.status == "watch" for row in rows):
        return ("team_research_priority_watch_present",)
    return ("team_research_priority_clear",)


def _summary_status(rows: tuple[ResearchCandidateResearchPriorityRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _dashboard_public_summary(
    status: str,
    rows: tuple[ResearchCandidateResearchPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("pass: no research candidates supplied",)
    if status == "block":
        summary = ("block: research queue has freshness diversity or cost gates to clear",)
        if any(row.status == "watch" for row in rows):
            summary = (*summary, "watch: prioritize timing and uncertainty follow-up")
        return summary
    if status == "watch":
        return ("watch: prioritize timing and uncertainty follow-up",)
    return ("pass: research queue clear",)


def _row_public_summary(status: str) -> str:
    if status == "block":
        return "block: freshness diversity or cost gates require research follow-up"
    if status == "watch":
        return "watch: timing or uncertainty requires research follow-up"
    return "pass: research inputs clear current priority gates"


def _team_public_summary(status: str) -> str:
    if status == "block":
        return "block: team has research priority gates to clear"
    if status == "watch":
        return "watch: team has research priority follow-up"
    return "pass: team research candidates clear current gates"


def _row_sort_key(row: ResearchCandidateResearchPriorityRow) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), -row.priority_score, row.summary_ref)


def _team_sort_key(
    team: ResearchCandidateResearchPriorityTeamRollup,
) -> tuple[int, Decimal, str]:
    return (_status_rank(team.status), -team.max_priority_score, team.team_ref)


def _status_rank(status: str) -> int:
    return {"block": 0, "watch": 1, "pass": 2}[status]


def _unique_sorted_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(reason_codes)))


def _status_count(
    rows: tuple[ResearchCandidateResearchPriorityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize_decimal(sum(values, ZERO) / Decimal(len(values)))


def _quantize_probability(value: Decimal) -> Decimal:
    return min(_quantize_decimal(value), ONE)


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return decimal_value


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_ref(field_name: str, value: object) -> str:
    public_value = _require_public_string(field_name, value)
    normalized = public_value.lower()
    if normalized.startswith(("candidate-", "candidate_", "market-", "market_")):
        raise ValueError(f"{field_name} must be a public-safe reference")
    return public_value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_string_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    for item in value:
        _require_public_string(field_name, item)
    return value


def _require_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    codes = _require_public_string_tuple(field_name, value, allow_empty=allow_empty)
    if tuple(dict.fromkeys(codes)) != codes:
        raise ValueError(f"{field_name} must be unique")
    return codes


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUS_SET:
        raise ValueError(f"{field_name} must be one of pass watch block")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _validate_team_consistency(
    team: ResearchCandidateResearchPriorityTeamRollup,
) -> None:
    if team.summary_count != team.pass_count + team.watch_count + team.block_count:
        raise ValueError("summary_count must match team status counts")
    if team.status == "block" and team.block_count == ZERO:
        raise ValueError("status must match team block_count")
    if team.status == "watch" and team.watch_count == ZERO:
        raise ValueError("status must match team watch_count")
    if team.status == "pass" and (team.watch_count != ZERO or team.block_count != ZERO):
        raise ValueError("status must match team status counts")


def _validate_dashboard_consistency(
    dashboard: ResearchCandidateResearchPriorityRollupDashboard,
) -> None:
    rows = dashboard.rows
    teams = dashboard.team_rollups
    if dashboard.summary_count != _decimal_count(len(rows)):
        raise ValueError("summary_count must match rows")
    if dashboard.team_count != _decimal_count(len(teams)):
        raise ValueError("team_count must match team_rollups")
    if dashboard.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if dashboard.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if dashboard.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if dashboard.status != _summary_status(rows):
        raise ValueError("status must match rows")
    expected_top = rows[0] if rows else None
    if dashboard.top_summary_ref != (
        expected_top.summary_ref if expected_top is not None else None
    ):
        raise ValueError("top_summary_ref must match rows")
    if dashboard.top_team_ref != (expected_top.team_ref if expected_top is not None else None):
        raise ValueError("top_team_ref must match rows")
    if dashboard.max_priority_score != max(
        (row.priority_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_priority_score must match rows")
    if dashboard.average_priority_score != _average_decimal(
        tuple(row.priority_score for row in rows),
    ):
        raise ValueError("average_priority_score must match rows")
    if dashboard.reason_codes != _dashboard_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if dashboard.public_summary != _dashboard_public_summary(dashboard.status, rows):
        raise ValueError("public_summary must match rows")
    if teams != _team_rollups(rows):
        raise ValueError("team_rollups must match rows")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be a Decimal")
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be a datetime")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, str) or type(value) is bool:
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
    raise ValueError("value is not JSON serializable")


def _validate_dashboard_payload(payload: dict[str, Any]) -> None:
    _reject_unknown_keys("payload", payload, REPORT_PAYLOAD_KEYS)
    _require_datetime_string("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_CANDIDATE_RESEARCH_PRIORITY_ROLLUP_DASHBOARD_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in REPORT_DECIMAL_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    for field_name in OPTIONAL_REPORT_DECIMAL_FIELDS:
        _require_optional_decimal_string(field_name, payload[field_name])
    _require_status("status", payload["status"])
    for field_name in ("top_summary_ref", "top_team_ref"):
        value = payload[field_name]
        if value is not None:
            _require_public_ref(field_name, value)
    _validate_public_string_list("public_summary", payload["public_summary"])
    _validate_public_string_list("reason_codes", payload["reason_codes"])
    if type(payload["team_rollups"]) is not list:
        raise ValueError("team_rollups must be a list")
    for index, team in enumerate(payload["team_rollups"]):
        _validate_team_payload(f"team_rollups[{index}]", team)
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for index, row in enumerate(payload["rows"]):
        _validate_row_payload(f"rows[{index}]", row)
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if payload["derived_validation_digest"] != _digest_payload(unsigned_payload):
        raise ValueError("derived_validation_digest must match payload values")


def _validate_team_payload(label: str, payload: object) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    _reject_unknown_keys(label, payload, TEAM_PAYLOAD_KEYS)
    _require_public_ref(f"{label}.team_ref", payload["team_ref"])
    for field_name in TEAM_DECIMAL_FIELDS:
        _require_decimal_string(f"{label}.{field_name}", payload[field_name])
    for field_name in OPTIONAL_TEAM_DECIMAL_FIELDS:
        _require_optional_decimal_string(f"{label}.{field_name}", payload[field_name])
    _require_status(f"{label}.status", payload["status"])
    _require_public_string(f"{label}.public_summary", payload["public_summary"])
    _validate_public_string_list(f"{label}.reason_codes", payload["reason_codes"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _validate_row_payload(label: str, payload: object) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    _reject_unknown_keys(label, payload, ROW_PAYLOAD_KEYS)
    for field_name in ("summary_ref", "team_ref", "category_ref"):
        _require_public_ref(f"{label}.{field_name}", payload[field_name])
    _require_datetime_string(f"{label}.observed_at", payload["observed_at"])
    _require_status(f"{label}.status", payload["status"])
    for field_name in ROW_DECIMAL_FIELDS:
        _require_decimal_string(f"{label}.{field_name}", payload[field_name])
    _require_public_string(f"{label}.public_summary", payload["public_summary"])
    _validate_public_string_list(f"{label}.reason_codes", payload["reason_codes"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _validate_public_string_list(field_name: str, value: object) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    for item in value:
        _require_public_string(field_name, item)


def _require_datetime_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_utc(field_name, parsed)


def _require_optional_decimal_string(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_decimal_string(field_name, value)


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} public payload value must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:  # pragma: no cover
        raise ValueError(f"{field_name} public payload value must be a Decimal string") from exc
    if not decimal_value.is_finite() or decimal_value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} public payload value must use six decimal places")
    return decimal_value


def _reject_unknown_keys(
    label: str,
    payload: dict[str, Any],
    allowed_keys: frozenset[str],
) -> None:
    for key in payload:
        if key not in allowed_keys:
            raise ValueError(f"unknown public field in {label}: {key}")


def _reject_public_numbers(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload values must use Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numbers(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numbers(item)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in UNSAFE_FIELD_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    normalized_value = value.lower()
    if any(fragment in normalized_value for fragment in UNSAFE_VALUE_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


def _digest_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _dashboard_digest(
    dashboard: ResearchCandidateResearchPriorityRollupDashboard,
) -> str:
    payload = _json_ready(dashboard)
    if type(payload) is not dict:
        raise ValueError("dashboard payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _digest_payload(payload)


__all__ = (
    "DEFAULT_RESEARCH_CANDIDATE_RESEARCH_PRIORITY_ROLLUP_DASHBOARD_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "ResearchCandidateResearchPriorityInput",
    "ResearchCandidateResearchPriorityRollupConfig",
    "ResearchCandidateResearchPriorityRollupDashboard",
    "ResearchCandidateResearchPriorityRow",
    "ResearchCandidateResearchPriorityTeamRollup",
    "build_research_candidate_research_priority_rollup_dashboard",
    "research_candidate_research_priority_rollup_dashboard_payload",
    "validate_research_candidate_research_priority_rollup_dashboard_payload",
)
