"""Pure report-only team memory retrieval policy planner."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_TEAM_MEMORY_RETRIEVAL_POLICY_CONFIG_VERSION = (
    "research-team-memory-retrieval-policy-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_PLAN_STATUSES = frozenset(("pass", "watch", "block"))
_PLAN_STATUS_ORDER = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_ROW_REASON_CODE_SEQUENCE = (
    "memory_retrieval_policy_pass",
    "memory_retrieval_policy_watch",
    "memory_retrieval_policy_block",
    "evidence_similarity_strong",
    "evidence_similarity_watch",
    "evidence_similarity_weak",
    "historical_error_pattern_clear",
    "historical_error_pattern_elevated",
    "historical_error_pattern_severe",
    "analog_event_depth_sufficient",
    "analog_event_depth_thin",
    "analog_event_depth_missing",
    "memory_age_fresh",
    "memory_age_stale",
    "memory_age_expired",
)
_REPORT_REASON_CODE_SEQUENCE = (
    "no_memory_retrieval_rows_supplied",
    "memory_retrieval_policy_passed",
    "memory_retrieval_policy_watch_rows",
    "memory_retrieval_policy_block_rows",
)
_UNSAFE_PUBLIC_TERMS = (
    "raw-candidate",
    "raw_candidate",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "question",
    "source_ref",
    "source-ref",
    "source_url",
    "source-url",
    "source_text",
    "source-text",
    "source.example",
    "token",
    "secret",
    "dsn",
    "postgres",
    "supabase",
    "table",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommend",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_MEMORY_RETRIEVAL_POLICY_CONFIG_VERSION",
    "ResearchTeamMemoryRetrievalPolicyConfig",
    "ResearchTeamMemoryRetrievalPolicyMemory",
    "ResearchTeamMemoryRetrievalPolicyReport",
    "ResearchTeamMemoryRetrievalPolicyRow",
    "build_research_team_memory_retrieval_policy_report",
    "research_team_memory_retrieval_policy_payload",
)


@dataclass(frozen=True)
class ResearchTeamMemoryRetrievalPolicyConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_MEMORY_RETRIEVAL_POLICY_CONFIG_VERSION
    evidence_similarity_weight: Decimal = Decimal("0.450000")
    error_health_weight: Decimal = Decimal("0.250000")
    analog_event_depth_weight: Decimal = Decimal("0.166667")
    memory_recency_weight: Decimal = Decimal("0.133333")
    max_historical_error_pattern_count: Decimal = Decimal("6.000000")
    max_analog_event_count: Decimal = Decimal("5.000000")
    max_memory_age_days: Decimal = Decimal("120.000000")
    pass_score_floor: Decimal = Decimal("0.850000")
    watch_score_floor: Decimal = Decimal("0.500000")
    watch_error_risk_floor: Decimal = Decimal("0.250000")
    block_error_risk_floor: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryRetrievalPolicyConfig:
            raise TypeError(
                "ResearchTeamMemoryRetrievalPolicyConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryRetrievalPolicyConfig:
            raise ValueError(
                "config must be exactly ResearchTeamMemoryRetrievalPolicyConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_TEAM_MEMORY_RETRIEVAL_POLICY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "evidence_similarity_weight",
            "error_health_weight",
            "analog_event_depth_weight",
            "memory_recency_weight",
            "pass_score_floor",
            "watch_score_floor",
            "watch_error_risk_floor",
            "block_error_risk_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_historical_error_pattern_count",
            "max_analog_event_count",
            "max_memory_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryRetrievalPolicyMemory:
    team_id: str
    domain: str
    event_type: str
    retrieval_reference: str
    evidence_similarity_score: Decimal
    historical_error_rate: Decimal
    historical_error_pattern_count: Decimal
    analog_event_count: Decimal
    memory_age_days: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryRetrievalPolicyMemory:
            raise TypeError(
                "ResearchTeamMemoryRetrievalPolicyMemory does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryRetrievalPolicyMemory:
            raise ValueError(
                "memory must be exactly ResearchTeamMemoryRetrievalPolicyMemory",
            )
        for field_name in ("team_id", "domain", "event_type"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_raw_reference("retrieval_reference", self.retrieval_reference)
        object.__setattr__(
            self,
            "evidence_similarity_score",
            _require_ratio_decimal(
                "evidence_similarity_score",
                self.evidence_similarity_score,
            ),
        )
        object.__setattr__(
            self,
            "historical_error_rate",
            _require_ratio_decimal("historical_error_rate", self.historical_error_rate),
        )
        for field_name in (
            "historical_error_pattern_count",
            "analog_event_count",
            "memory_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("memory", self)


@dataclass(frozen=True)
class ResearchTeamMemoryRetrievalPolicyRow:
    retrieval_rank: Decimal
    team_id: str
    domain: str
    event_type: str
    memory_digest: str
    evidence_similarity_score: Decimal
    error_risk_score: Decimal
    analog_event_depth_score: Decimal
    memory_recency_score: Decimal
    retrieval_score: Decimal
    plan_status: str
    plan_focus: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryRetrievalPolicyRow:
            raise TypeError(
                "ResearchTeamMemoryRetrievalPolicyRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryRetrievalPolicyRow:
            raise ValueError("row must be exactly ResearchTeamMemoryRetrievalPolicyRow")
        for field_name in ("team_id", "domain", "event_type", "plan_focus"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "retrieval_rank",
            _require_positive_decimal("retrieval_rank", self.retrieval_rank),
        )
        _require_sha256_digest("memory_digest", self.memory_digest)
        for field_name in (
            "evidence_similarity_score",
            "error_risk_score",
            "analog_event_depth_score",
            "memory_recency_score",
            "retrieval_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_plan_status("plan_status", self.plan_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamMemoryRetrievalPolicyReport:
    generated_at: datetime
    config_version: str
    plan_status: str
    memory_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_retrieval_score: Decimal
    highest_error_risk_score: Decimal
    rows: tuple[ResearchTeamMemoryRetrievalPolicyRow, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryRetrievalPolicyReport:
            raise TypeError(
                "ResearchTeamMemoryRetrievalPolicyReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryRetrievalPolicyReport:
            raise ValueError(
                "report must be exactly ResearchTeamMemoryRetrievalPolicyReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_TEAM_MEMORY_RETRIEVAL_POLICY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_plan_status("plan_status", self.plan_status)
        for field_name in (
            "memory_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_retrieval_score", "highest_error_risk_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _REPORT_REASON_CODE_SEQUENCE),
        )
        _require_sha256_digest("validation_digest", self.validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.validation_digest != expected_digest:
            raise ValueError("validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchTeamMemoryRetrievalPolicyReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_team_memory_retrieval_policy_report(
    memories: Sequence[ResearchTeamMemoryRetrievalPolicyMemory],
    *,
    generated_at: datetime,
    config: ResearchTeamMemoryRetrievalPolicyConfig | None = None,
) -> ResearchTeamMemoryRetrievalPolicyReport:
    if config is None:
        config = ResearchTeamMemoryRetrievalPolicyConfig()
    if type(config) is not ResearchTeamMemoryRetrievalPolicyConfig:
        raise ValueError("config must be a ResearchTeamMemoryRetrievalPolicyConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_memories = _normalize_memories(memories)
    rows = _rank_rows(
        tuple(_row_without_rank(memory, config) for memory in normalized_memories),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "plan_status": _report_status(rows),
        "memory_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_retrieval_score": _average(tuple(row.retrieval_score for row in rows)),
        "highest_error_risk_score": _highest_error_risk_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamMemoryRetrievalPolicyReport(
        **values,
        validation_digest=_report_digest_from_values(values),
    )


def research_team_memory_retrieval_policy_payload(
    report: ResearchTeamMemoryRetrievalPolicyReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamMemoryRetrievalPolicyReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = report.payload
        _require_hard_flags("payload", _DictFlags(payload))
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        return payload
    raise ValueError(
        "report must be a ResearchTeamMemoryRetrievalPolicyReport or payload",
    )


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


def _row_without_rank(
    memory: ResearchTeamMemoryRetrievalPolicyMemory,
    config: ResearchTeamMemoryRetrievalPolicyConfig,
) -> ResearchTeamMemoryRetrievalPolicyRow:
    error_risk_score = _error_risk_score(memory, config)
    analog_event_depth_score = _clamp_ratio(
        memory.analog_event_count / config.max_analog_event_count,
    )
    memory_recency_score = _clamp_ratio(
        _ONE - memory.memory_age_days / config.max_memory_age_days,
    )
    retrieval_score = _retrieval_score(
        evidence_similarity_score=memory.evidence_similarity_score,
        error_risk_score=error_risk_score,
        analog_event_depth_score=analog_event_depth_score,
        memory_recency_score=memory_recency_score,
        config=config,
    )
    plan_status = _row_status(
        retrieval_score=retrieval_score,
        error_risk_score=error_risk_score,
        analog_event_depth_score=analog_event_depth_score,
        memory_recency_score=memory_recency_score,
        config=config,
    )
    return ResearchTeamMemoryRetrievalPolicyRow(
        retrieval_rank=_ONE,
        team_id=memory.team_id,
        domain=memory.domain,
        event_type=memory.event_type,
        memory_digest=_memory_digest(memory),
        evidence_similarity_score=memory.evidence_similarity_score,
        error_risk_score=error_risk_score,
        analog_event_depth_score=analog_event_depth_score,
        memory_recency_score=memory_recency_score,
        retrieval_score=retrieval_score,
        plan_status=plan_status,
        plan_focus=_plan_focus(plan_status, error_risk_score),
        reason_codes=_row_reason_codes(
            plan_status=plan_status,
            evidence_similarity_score=memory.evidence_similarity_score,
            error_risk_score=error_risk_score,
            analog_event_depth_score=analog_event_depth_score,
            memory_recency_score=memory_recency_score,
            config=config,
        ),
    )


def _rank_rows(
    rows: tuple[ResearchTeamMemoryRetrievalPolicyRow, ...],
) -> tuple[ResearchTeamMemoryRetrievalPolicyRow, ...]:
    ranked_rows = []
    for index, row in enumerate(
        sorted(
            rows,
            key=lambda item: (
                _PLAN_STATUS_ORDER[item.plan_status],
                item.retrieval_score,
                -item.error_risk_score,
                item.team_id,
                item.domain,
                item.event_type,
                item.memory_digest,
            ),
        ),
        start=1,
    ):
        ranked_rows.append(replace(row, retrieval_rank=_decimal_count(index)))
    return tuple(ranked_rows)


def _error_risk_score(
    memory: ResearchTeamMemoryRetrievalPolicyMemory,
    config: ResearchTeamMemoryRetrievalPolicyConfig,
) -> Decimal:
    return _clamp_ratio(
        memory.historical_error_rate
        + memory.historical_error_pattern_count / config.max_historical_error_pattern_count,
    )


def _retrieval_score(
    *,
    evidence_similarity_score: Decimal,
    error_risk_score: Decimal,
    analog_event_depth_score: Decimal,
    memory_recency_score: Decimal,
    config: ResearchTeamMemoryRetrievalPolicyConfig,
) -> Decimal:
    return _clamp_ratio(
        evidence_similarity_score * config.evidence_similarity_weight
        + (_ONE - error_risk_score) * config.error_health_weight
        + analog_event_depth_score * config.analog_event_depth_weight
        + memory_recency_score * config.memory_recency_weight,
    )


def _row_status(
    *,
    retrieval_score: Decimal,
    error_risk_score: Decimal,
    analog_event_depth_score: Decimal,
    memory_recency_score: Decimal,
    config: ResearchTeamMemoryRetrievalPolicyConfig,
) -> str:
    if (
        error_risk_score >= config.block_error_risk_floor
        or analog_event_depth_score <= _ZERO
        or memory_recency_score <= _ZERO
    ):
        return "block"
    if retrieval_score >= config.pass_score_floor:
        return "pass"
    if retrieval_score >= config.watch_score_floor:
        return "watch"
    return "block"


def _report_status(rows: tuple[ResearchTeamMemoryRetrievalPolicyRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.plan_status == "block" for row in rows):
        return "block"
    if any(row.plan_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _plan_focus(plan_status: str, error_risk_score: Decimal) -> str:
    if plan_status == "block":
        return "domain_event_error_pattern_review"
    if plan_status == "watch" or error_risk_score >= Decimal("0.250000"):
        return "domain_event_similarity_review"
    return "domain_event_similarity_refresh"


def _row_reason_codes(
    *,
    plan_status: str,
    evidence_similarity_score: Decimal,
    error_risk_score: Decimal,
    analog_event_depth_score: Decimal,
    memory_recency_score: Decimal,
    config: ResearchTeamMemoryRetrievalPolicyConfig,
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        (
            f"memory_retrieval_policy_{plan_status}",
            _similarity_reason(evidence_similarity_score),
            _error_reason(error_risk_score, config),
            _analog_reason(analog_event_depth_score),
            _age_reason(memory_recency_score),
        ),
        _ROW_REASON_CODE_SEQUENCE,
    )


def _similarity_reason(value: Decimal) -> str:
    if value >= Decimal("0.800000"):
        return "evidence_similarity_strong"
    if value >= Decimal("0.500000"):
        return "evidence_similarity_watch"
    return "evidence_similarity_weak"


def _error_reason(
    value: Decimal,
    config: ResearchTeamMemoryRetrievalPolicyConfig,
) -> str:
    if value >= config.block_error_risk_floor:
        return "historical_error_pattern_severe"
    if value >= config.watch_error_risk_floor:
        return "historical_error_pattern_elevated"
    return "historical_error_pattern_clear"


def _analog_reason(value: Decimal) -> str:
    if value <= _ZERO:
        return "analog_event_depth_missing"
    if value < Decimal("0.500000"):
        return "analog_event_depth_thin"
    return "analog_event_depth_sufficient"


def _age_reason(value: Decimal) -> str:
    if value <= _ZERO:
        return "memory_age_expired"
    if value < Decimal("0.500000"):
        return "memory_age_stale"
    return "memory_age_fresh"


def _report_reason_codes(
    rows: tuple[ResearchTeamMemoryRetrievalPolicyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_memory_retrieval_rows_supplied",)
    reason_codes: list[str] = []
    if all(row.plan_status == "pass" for row in rows):
        reason_codes.append("memory_retrieval_policy_passed")
    if any(row.plan_status == "watch" for row in rows):
        reason_codes.append("memory_retrieval_policy_watch_rows")
    if any(row.plan_status == "block" for row in rows):
        reason_codes.append("memory_retrieval_policy_block_rows")
    return _normalize_reason_codes(tuple(reason_codes), _REPORT_REASON_CODE_SEQUENCE)


def _status_count(
    rows: tuple[ResearchTeamMemoryRetrievalPolicyRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.plan_status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _highest_error_risk_score(
    rows: tuple[ResearchTeamMemoryRetrievalPolicyRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return max(row.error_risk_score for row in rows)


def _validate_config(config: ResearchTeamMemoryRetrievalPolicyConfig) -> None:
    weights_total = _quantize(
        config.evidence_similarity_weight
        + config.error_health_weight
        + config.analog_event_depth_weight
        + config.memory_recency_weight,
    )
    if weights_total != _ONE:
        raise ValueError("weights must sum to 1.000000")
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must not exceed pass_score_floor")
    if config.watch_error_risk_floor > config.block_error_risk_floor:
        raise ValueError(
            "watch_error_risk_floor must not exceed block_error_risk_floor",
        )


def _validate_row_consistency(row: ResearchTeamMemoryRetrievalPolicyRow) -> None:
    if row.plan_status == "pass" and "memory_retrieval_policy_pass" not in row.reason_codes:
        raise ValueError("pass rows must include memory_retrieval_policy_pass")
    if row.plan_status == "watch" and "memory_retrieval_policy_watch" not in row.reason_codes:
        raise ValueError("watch rows must include memory_retrieval_policy_watch")
    if row.plan_status == "block" and "memory_retrieval_policy_block" not in row.reason_codes:
        raise ValueError("block rows must include memory_retrieval_policy_block")


def _validate_report_consistency(report: ResearchTeamMemoryRetrievalPolicyReport) -> None:
    rows = report.rows
    if report.memory_count != _decimal_count(len(rows)):
        raise ValueError("memory_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_retrieval_score != _average(tuple(row.retrieval_score for row in rows)):
        raise ValueError("average_retrieval_score must match rows")
    if report.highest_error_risk_score != _highest_error_risk_score(rows):
        raise ValueError("highest_error_risk_score must match rows")
    if report.plan_status != _report_status(rows):
        raise ValueError("plan_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    _validate_rows_sorted(rows)


def _validate_rows_sorted(rows: tuple[ResearchTeamMemoryRetrievalPolicyRow, ...]) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                _PLAN_STATUS_ORDER[row.plan_status],
                row.retrieval_score,
                -row.error_risk_score,
                row.team_id,
                row.domain,
                row.event_type,
                row.memory_digest,
            ),
        ),
    )
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(rows) + 1))
    if rows != expected or tuple(row.retrieval_rank for row in rows) != expected_ranks:
        raise ValueError("rows must be sorted by retrieval policy rank")


def _normalize_memories(
    memories: Sequence[ResearchTeamMemoryRetrievalPolicyMemory],
) -> tuple[ResearchTeamMemoryRetrievalPolicyMemory, ...]:
    if isinstance(memories, (str, bytes)) or not isinstance(memories, Sequence):
        raise ValueError("memories must be a sequence")
    normalized: list[ResearchTeamMemoryRetrievalPolicyMemory] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for memory in memories:
        if type(memory) is not ResearchTeamMemoryRetrievalPolicyMemory:
            raise ValueError(
                "memories must contain ResearchTeamMemoryRetrievalPolicyMemory",
            )
        key = (memory.team_id, memory.domain, memory.event_type)
        if key in seen_keys:
            raise ValueError("duplicate memory retrieval key")
        seen_keys.add(key)
        normalized.append(memory)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (item.team_id, item.domain, item.event_type),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchTeamMemoryRetrievalPolicyRow],
) -> tuple[ResearchTeamMemoryRetrievalPolicyRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchTeamMemoryRetrievalPolicyRow] = []
    for row in rows:
        if type(row) is not ResearchTeamMemoryRetrievalPolicyRow:
            raise ValueError("rows must contain ResearchTeamMemoryRetrievalPolicyRow")
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.retrieval_rank))


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in supported:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason_code for reason_code in supported if reason_code in normalized)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_raw_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be nonempty canonical text")
    return value


def _require_plan_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _PLAN_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize(value)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _memory_digest(memory: ResearchTeamMemoryRetrievalPolicyMemory) -> str:
    encoded = json.dumps(
        {
            "team_id": memory.team_id,
            "domain": memory.domain,
            "event_type": memory.event_type,
            "retrieval_reference": memory.retrieval_reference,
        },
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _report_values_without_digest(
    report: ResearchTeamMemoryRetrievalPolicyReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest payload", payload, allow_json_containers=True)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return _json_dict_ready(value)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if type(value) is int:
        raise ValueError("payload must not contain int values")
    raise ValueError("payload contains unsupported value")


def _json_dict_ready(value: dict[Any, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("payload object keys must be strings")
        ready[key] = _json_ready(item)
    return ready


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    value = _json_ready(value) if not allow_json_containers else value
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} has unsafe public field")
            _reject_unsafe_public_key(key, label)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if type(value) is float:
        raise ValueError(f"{label} must not contain float values")
    if type(value) is int:
        raise ValueError(f"{label} must not contain int values")
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")
