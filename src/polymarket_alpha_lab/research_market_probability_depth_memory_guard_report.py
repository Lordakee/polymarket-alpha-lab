"""Read-only market probability depth memory guard report."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_MARKET_PROBABILITY_DEPTH_MEMORY_GUARD_CONFIG_VERSION = (
    "research-market-probability-depth-memory-guard-v0"
)

STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "cost_depth_clear",
    "depth_cost_watch",
    "depth_cost_block",
    "impact_clear",
    "impact_watch",
    "impact_block",
    "memory_fresh",
    "memory_stale",
)
REPORT_REASON_CODES = (
    "no_observations",
    "market_probability_depth_memory_guard_clear",
    "depth_cost_block",
    "impact_block",
    "depth_cost_watch",
    "impact_watch",
    "memory_stale",
)
_REPORT_WATCH_CODES = (
    "depth_cost_watch",
    "impact_watch",
    "memory_stale",
)
_REPORT_BLOCK_CODES = (
    "depth_cost_block",
    "impact_block",
)
_REF_DIGEST_LENGTH = 16
_SHA256_HEX_LENGTH = 64
_COUNT_QUANTUM = Decimal("1")
_RATIO_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_RATIO = Decimal("0.000000")
_ONE_RATIO = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PUBLIC_RAW_KEY_FRAGMENTS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "question",
    "raw_candidate_id",
    "raw_market_id",
    "raw_source_url",
    "raw_source_text",
    "raw_source_dsn",
    "raw_source_table",
    "raw_source_token",
    "source_url",
    "source_text",
    "source_dsn",
    "source_table",
    "source_" + "tok" + "en",
)
_UNSAFE_KEY_FRAGMENTS = (
    "au" + "th",
    "wal" + "let",
    "net" + "work",
    "data" + "base",
    "d" + "b",
    "or" + "der",
    "tra" + "de",
    "tra" + "ding",
    "siz" + "ing",
    "recomm" + "endation",
    "exe" + "cution",
    "live",
    "sur" + "face",
)
_UNSAFE_VALUE_FRAGMENTS = (
    "secret",
    "private",
    "://" ,
    "tok" + "en",
    "post" + "gresql",
    "internal",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "siz" + "ing",
    "recomm" + "endation",
    "exe" + "cution",
    "live",
    "sur" + "face",
)
_PUBLIC_REPORT_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_cost_to_limit_ratio",
        "max_market_impact_probability",
        "mean_estimated_cost",
        "status",
        "reason_codes",
        "rows",
        "payload_sha256",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_PUBLIC_ROW_KEYS = frozenset(
    (
        "candidate_ref",
        "market_ref",
        "source_ref",
        "quoted_probability",
        "target_probability",
        "probability_gap",
        "available_depth",
        "estimated_cost",
        "memory_cost_limit",
        "cost_to_limit_ratio",
        "market_impact_probability",
        "age_hours",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


@dataclass(frozen=True)
class ResearchMarketProbabilityDepthMemoryGuardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_DEPTH_MEMORY_GUARD_CONFIG_VERSION
    )
    watch_cost_to_limit_ratio: Decimal = Decimal("0.500000")
    block_cost_to_limit_ratio: Decimal = Decimal("0.900000")
    watch_impact_probability: Decimal = Decimal("0.020000")
    block_impact_probability: Decimal = Decimal("0.050000")
    stale_age_hours: Decimal = Decimal("24.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketProbabilityDepthMemoryGuardConfig:
            raise TypeError(
                "ResearchMarketProbabilityDepthMemoryGuardConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketProbabilityDepthMemoryGuardConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchMarketProbabilityDepthMemoryGuardConfig",
            )
        _require_supported_config_version(self.config_version)
        object.__setattr__(
            self,
            "watch_cost_to_limit_ratio",
            _normalize_nonnegative_ratio(
                "watch_cost_to_limit_ratio",
                self.watch_cost_to_limit_ratio,
            ),
        )
        object.__setattr__(
            self,
            "block_cost_to_limit_ratio",
            _normalize_nonnegative_ratio(
                "block_cost_to_limit_ratio",
                self.block_cost_to_limit_ratio,
            ),
        )
        object.__setattr__(
            self,
            "watch_impact_probability",
            _normalize_probability(
                "watch_impact_probability",
                self.watch_impact_probability,
            ),
        )
        object.__setattr__(
            self,
            "block_impact_probability",
            _normalize_probability(
                "block_impact_probability",
                self.block_impact_probability,
            ),
        )
        object.__setattr__(
            self,
            "stale_age_hours",
            _normalize_nonnegative_ratio("stale_age_hours", self.stale_age_hours),
        )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityDepthMemoryGuardObservation:
    raw_candidate_id: str
    raw_market_id: str
    raw_source_url: str
    raw_source_text: str
    raw_source_dsn: str
    raw_source_table: str
    raw_source_token: str
    quoted_probability: Decimal
    target_probability: Decimal
    available_depth: Decimal
    estimated_cost: Decimal
    memory_cost_limit: Decimal
    market_impact_probability: Decimal
    age_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketProbabilityDepthMemoryGuardObservation:
            raise TypeError(
                "ResearchMarketProbabilityDepthMemoryGuardObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketProbabilityDepthMemoryGuardObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchMarketProbabilityDepthMemoryGuardObservation",
            )
        for field_name in (
            "raw_candidate_id",
            "raw_market_id",
            "raw_source_url",
            "raw_source_text",
            "raw_source_dsn",
            "raw_source_table",
            "raw_source_token",
        ):
            _require_public_source_string(field_name, getattr(self, field_name))
        for field_name in ("quoted_probability", "target_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("available_depth", "estimated_cost", "age_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_cost_limit",
            _normalize_positive_ratio("memory_cost_limit", self.memory_cost_limit),
        )
        object.__setattr__(
            self,
            "market_impact_probability",
            _normalize_probability(
                "market_impact_probability",
                self.market_impact_probability,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityDepthMemoryGuardRow:
    candidate_ref: str
    market_ref: str
    source_ref: str
    quoted_probability: Decimal
    target_probability: Decimal
    probability_gap: Decimal
    available_depth: Decimal
    estimated_cost: Decimal
    memory_cost_limit: Decimal
    cost_to_limit_ratio: Decimal
    market_impact_probability: Decimal
    age_hours: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketProbabilityDepthMemoryGuardRow:
            raise TypeError(
                "ResearchMarketProbabilityDepthMemoryGuardRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketProbabilityDepthMemoryGuardRow:
            raise ValueError(
                "row must be exactly ResearchMarketProbabilityDepthMemoryGuardRow",
            )
        _require_ref("candidate_ref", self.candidate_ref, "candidate_ref_")
        _require_ref("market_ref", self.market_ref, "market_ref_")
        _require_ref("source_ref", self.source_ref, "source_ref_")
        for field_name in ("quoted_probability", "target_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "probability_gap",
            "available_depth",
            "estimated_cost",
            "cost_to_limit_ratio",
            "market_impact_probability",
            "age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_cost_limit",
            _normalize_positive_ratio("memory_cost_limit", self.memory_cost_limit),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityDepthMemoryGuardReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_cost_to_limit_ratio: Decimal
    max_market_impact_probability: Decimal
    mean_estimated_cost: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketProbabilityDepthMemoryGuardRow, ...]
    payload_sha256: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketProbabilityDepthMemoryGuardReport:
            raise TypeError(
                "ResearchMarketProbabilityDepthMemoryGuardReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketProbabilityDepthMemoryGuardReport:
            raise ValueError(
                "report must be exactly "
                "ResearchMarketProbabilityDepthMemoryGuardReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_supported_config_version(self.config_version)
        for field_name in ("observation_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_cost_to_limit_ratio",
            "max_market_impact_probability",
            "mean_estimated_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_hex("payload_sha256", self.payload_sha256)
        _validate_report(self)
        _require_hard_flags("report", self)
        if self.payload_sha256 != _payload_digest(_report_payload_without_digest(self)):
            raise ValueError("payload_sha256 must match public payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_probability_depth_memory_guard_report_payload(self)


def build_research_market_probability_depth_memory_guard_report(
    observations: list[ResearchMarketProbabilityDepthMemoryGuardObservation]
    | tuple[ResearchMarketProbabilityDepthMemoryGuardObservation, ...],
    *,
    config: ResearchMarketProbabilityDepthMemoryGuardConfig,
    generated_at: datetime,
) -> ResearchMarketProbabilityDepthMemoryGuardReport:
    if type(config) is not ResearchMarketProbabilityDepthMemoryGuardConfig:
        raise ValueError(
            "config must be a ResearchMarketProbabilityDepthMemoryGuardConfig",
        )
    _require_hard_flags("config", config)
    source_rows = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (_row_from_observation(observation, config) for observation in source_rows),
            key=_row_sort_key,
        ),
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    observation_count = _count(len(rows))
    pass_count = _count(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count(sum(1 for row in rows if row.status == "watch"))
    block_count = _count(sum(1 for row in rows if row.status == "block"))
    max_cost_to_limit_ratio = _max_ratio(tuple(row.cost_to_limit_ratio for row in rows))
    max_market_impact_probability = _max_ratio(
        tuple(row.market_impact_probability for row in rows),
    )
    mean_estimated_cost = _mean(tuple(row.estimated_cost for row in rows))
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows)
    public_payload = _public_payload_without_digest(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=observation_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_cost_to_limit_ratio=max_cost_to_limit_ratio,
        max_market_impact_probability=max_market_impact_probability,
        mean_estimated_cost=mean_estimated_cost,
        status=status,
        reason_codes=reason_codes,
        rows=rows,
    )
    return ResearchMarketProbabilityDepthMemoryGuardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=observation_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_cost_to_limit_ratio=max_cost_to_limit_ratio,
        max_market_impact_probability=max_market_impact_probability,
        mean_estimated_cost=mean_estimated_cost,
        status=status,
        reason_codes=reason_codes,
        rows=rows,
        payload_sha256=_payload_digest(public_payload),
    )


def research_market_probability_depth_memory_guard_report_payload(
    report: ResearchMarketProbabilityDepthMemoryGuardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketProbabilityDepthMemoryGuardReport:
        _require_hard_flags("report", report)
        payload = _report_payload(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketProbabilityDepthMemoryGuardReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    if type(report) is dict:
        _validate_payload_sha256(payload)
        _validate_public_report_payload(payload)
    return payload


def validate_research_market_probability_depth_memory_guard_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    research_market_probability_depth_memory_guard_report_payload(payload)
    return True


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


def _validate_config(config: ResearchMarketProbabilityDepthMemoryGuardConfig) -> None:
    if config.watch_cost_to_limit_ratio > config.block_cost_to_limit_ratio:
        raise ValueError("watch_cost_to_limit_ratio must not exceed block_cost_to_limit_ratio")
    if config.watch_impact_probability > config.block_impact_probability:
        raise ValueError("watch_impact_probability must not exceed block_impact_probability")


def _require_supported_config_version(value: object) -> None:
    _require_canonical_string("config_version", value)
    if value != DEFAULT_RESEARCH_MARKET_PROBABILITY_DEPTH_MEMORY_GUARD_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _normalize_observations(
    observations: list[ResearchMarketProbabilityDepthMemoryGuardObservation]
    | tuple[ResearchMarketProbabilityDepthMemoryGuardObservation, ...],
) -> tuple[ResearchMarketProbabilityDepthMemoryGuardObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    rows = tuple(observations)
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchMarketProbabilityDepthMemoryGuardObservation:
            raise ValueError(
                "observations must contain ResearchMarketProbabilityDepthMemoryGuardObservation values",
            )
        _require_hard_flags("observation", row)
        key = (row.raw_candidate_id, row.raw_market_id, row.raw_source_url)
        if key in seen:
            raise ValueError("observations must not contain duplicate raw identities")
        seen.add(key)
    return rows


def _row_from_observation(
    observation: ResearchMarketProbabilityDepthMemoryGuardObservation,
    config: ResearchMarketProbabilityDepthMemoryGuardConfig,
) -> ResearchMarketProbabilityDepthMemoryGuardRow:
    cost_to_limit_ratio = _ratio(
        observation.estimated_cost,
        observation.memory_cost_limit,
    )
    status = _row_status(observation, config, cost_to_limit_ratio)
    return ResearchMarketProbabilityDepthMemoryGuardRow(
        candidate_ref=_redacted_ref("candidate_ref_", observation.raw_candidate_id),
        market_ref=_redacted_ref("market_ref_", observation.raw_market_id),
        source_ref=_source_ref(observation),
        quoted_probability=observation.quoted_probability,
        target_probability=observation.target_probability,
        probability_gap=_abs_ratio(
            observation.quoted_probability - observation.target_probability,
        ),
        available_depth=observation.available_depth,
        estimated_cost=observation.estimated_cost,
        memory_cost_limit=observation.memory_cost_limit,
        cost_to_limit_ratio=cost_to_limit_ratio,
        market_impact_probability=observation.market_impact_probability,
        age_hours=observation.age_hours,
        status=status,
        reason_codes=_row_reason_codes(observation, config, cost_to_limit_ratio),
    )


def _source_ref(observation: ResearchMarketProbabilityDepthMemoryGuardObservation) -> str:
    return _redacted_ref(
        "source_ref_",
        "\x1f".join(
            (
                observation.raw_source_url,
                observation.raw_source_text,
                observation.raw_source_dsn,
                observation.raw_source_table,
                observation.raw_source_token,
            ),
        ),
    )


def _row_status(
    observation: ResearchMarketProbabilityDepthMemoryGuardObservation,
    config: ResearchMarketProbabilityDepthMemoryGuardConfig,
    cost_to_limit_ratio: Decimal,
) -> str:
    if (
        cost_to_limit_ratio >= config.block_cost_to_limit_ratio
        or observation.market_impact_probability >= config.block_impact_probability
    ):
        return "block"
    if (
        cost_to_limit_ratio >= config.watch_cost_to_limit_ratio
        or observation.market_impact_probability >= config.watch_impact_probability
        or observation.age_hours >= config.stale_age_hours
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: ResearchMarketProbabilityDepthMemoryGuardObservation,
    config: ResearchMarketProbabilityDepthMemoryGuardConfig,
    cost_to_limit_ratio: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if cost_to_limit_ratio >= config.block_cost_to_limit_ratio:
        codes.append("depth_cost_block")
    elif cost_to_limit_ratio >= config.watch_cost_to_limit_ratio:
        codes.append("depth_cost_watch")
    else:
        codes.append("cost_depth_clear")
    if observation.market_impact_probability >= config.block_impact_probability:
        codes.append("impact_block")
    elif observation.market_impact_probability >= config.watch_impact_probability:
        codes.append("impact_watch")
    else:
        codes.append("impact_clear")
    if observation.age_hours >= config.stale_age_hours:
        codes.append("memory_stale")
    else:
        codes.append("memory_fresh")
    return tuple(codes)


def _report_status(
    rows: tuple[ResearchMarketProbabilityDepthMemoryGuardRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketProbabilityDepthMemoryGuardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_observations",)
    if all(row.status == "pass" for row in rows):
        return ("market_probability_depth_memory_guard_clear",)
    codes: list[str] = []
    for code in _REPORT_BLOCK_CODES + _REPORT_WATCH_CODES:
        if any(code in row.reason_codes for row in rows):
            codes.append(code)
    return tuple(codes)


def _row_sort_key(
    row: ResearchMarketProbabilityDepthMemoryGuardRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        _status_rank(row.status),
        -row.cost_to_limit_ratio,
        -row.market_impact_probability,
        row.candidate_ref,
        row.market_ref,
    )


def _status_rank(status: str) -> Decimal:
    if status == "block":
        return Decimal("0")
    if status == "watch":
        return Decimal("1")
    return Decimal("2")


def _validate_row(row: ResearchMarketProbabilityDepthMemoryGuardRow) -> None:
    if row.probability_gap != _abs_ratio(row.quoted_probability - row.target_probability):
        raise ValueError("probability_gap must match probabilities")
    if row.cost_to_limit_ratio != _ratio(row.estimated_cost, row.memory_cost_limit):
        raise ValueError("cost_to_limit_ratio must match estimated cost and limit")
    if row.status == "pass" and any(
        code in row.reason_codes
        for code in (
            "depth_cost_watch",
            "depth_cost_block",
            "impact_watch",
            "impact_block",
            "memory_stale",
        )
    ):
        raise ValueError("pass rows must contain clear reason codes")
    if row.status == "watch" and not any(
        code in row.reason_codes for code in _REPORT_WATCH_CODES
    ):
        raise ValueError("watch rows must contain watch reason codes")
    if row.status == "block" and not any(
        code in row.reason_codes for code in _REPORT_BLOCK_CODES
    ):
        raise ValueError("block rows must contain block reason codes")


def _validate_report(report: ResearchMarketProbabilityDepthMemoryGuardReport) -> None:
    if report.observation_count != _count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.max_cost_to_limit_ratio != _max_ratio(
        tuple(row.cost_to_limit_ratio for row in report.rows),
    ):
        raise ValueError("max_cost_to_limit_ratio must match rows")
    if report.max_market_impact_probability != _max_ratio(
        tuple(row.market_impact_probability for row in report.rows),
    ):
        raise ValueError("max_market_impact_probability must match rows")
    if report.mean_estimated_cost != _mean(
        tuple(row.estimated_cost for row in report.rows),
    ):
        raise ValueError("mean_estimated_cost must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministic")


def _report_payload(
    report: ResearchMarketProbabilityDepthMemoryGuardReport,
) -> dict[str, Any]:
    payload = _report_payload_without_digest(report)
    payload["payload_sha256"] = report.payload_sha256
    return payload


def _report_payload_without_digest(
    report: ResearchMarketProbabilityDepthMemoryGuardReport,
) -> dict[str, Any]:
    return _public_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        observation_count=report.observation_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        max_cost_to_limit_ratio=report.max_cost_to_limit_ratio,
        max_market_impact_probability=report.max_market_impact_probability,
        mean_estimated_cost=report.mean_estimated_cost,
        status=report.status,
        reason_codes=report.reason_codes,
        rows=report.rows,
    )


def _public_payload_without_digest(
    *,
    generated_at: datetime,
    config_version: str,
    observation_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    max_cost_to_limit_ratio: Decimal,
    max_market_impact_probability: Decimal,
    mean_estimated_cost: Decimal,
    status: str,
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchMarketProbabilityDepthMemoryGuardRow, ...],
) -> dict[str, Any]:
    return {
        "generated_at": _json_ready(generated_at),
        "config_version": config_version,
        "observation_count": _json_ready(observation_count),
        "pass_count": _json_ready(pass_count),
        "watch_count": _json_ready(watch_count),
        "block_count": _json_ready(block_count),
        "max_cost_to_limit_ratio": _json_ready(max_cost_to_limit_ratio),
        "max_market_impact_probability": _json_ready(max_market_impact_probability),
        "mean_estimated_cost": _json_ready(mean_estimated_cost),
        "status": status,
        "reason_codes": list(reason_codes),
        "rows": [_row_payload(row) for row in rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: ResearchMarketProbabilityDepthMemoryGuardRow) -> dict[str, Any]:
    return {
        "candidate_ref": row.candidate_ref,
        "market_ref": row.market_ref,
        "source_ref": row.source_ref,
        "quoted_probability": _json_ready(row.quoted_probability),
        "target_probability": _json_ready(row.target_probability),
        "probability_gap": _json_ready(row.probability_gap),
        "available_depth": _json_ready(row.available_depth),
        "estimated_cost": _json_ready(row.estimated_cost),
        "memory_cost_limit": _json_ready(row.memory_cost_limit),
        "cost_to_limit_ratio": _json_ready(row.cost_to_limit_ratio),
        "market_impact_probability": _json_ready(row.market_impact_probability),
        "age_hours": _json_ready(row.age_hours),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _payload_digest(payload_without_digest: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("payload", payload_without_digest)
    encoded = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_payload_sha256(payload: dict[str, Any]) -> None:
    if "payload_sha256" not in payload:
        raise ValueError("payload_sha256 is required")
    supplied = payload["payload_sha256"]
    if type(supplied) is not str:
        raise ValueError("payload_sha256 must be a string")
    _require_sha256_hex("payload_sha256", supplied)
    comparable = dict(payload)
    comparable.pop("payload_sha256")
    if supplied != _payload_digest(comparable):
        raise ValueError("payload_sha256 must match public payload")


def _validate_public_report_payload(payload: dict[str, Any]) -> None:
    _require_public_keys("payload", payload, _PUBLIC_REPORT_KEYS)
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(_public_row(row) for row in rows_value)
    ResearchMarketProbabilityDepthMemoryGuardReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=_public_string("config_version", payload["config_version"]),
        observation_count=_public_count("observation_count", payload["observation_count"]),
        pass_count=_public_count("pass_count", payload["pass_count"]),
        watch_count=_public_count("watch_count", payload["watch_count"]),
        block_count=_public_count("block_count", payload["block_count"]),
        max_cost_to_limit_ratio=_public_ratio(
            "max_cost_to_limit_ratio",
            payload["max_cost_to_limit_ratio"],
        ),
        max_market_impact_probability=_public_ratio(
            "max_market_impact_probability",
            payload["max_market_impact_probability"],
        ),
        mean_estimated_cost=_public_ratio(
            "mean_estimated_cost",
            payload["mean_estimated_cost"],
        ),
        status=_public_string("status", payload["status"]),
        reason_codes=_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            REPORT_REASON_CODES,
        ),
        rows=rows,
        payload_sha256=_public_string("payload_sha256", payload["payload_sha256"]),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _public_row(value: object) -> ResearchMarketProbabilityDepthMemoryGuardRow:
    if type(value) is not dict:
        raise ValueError("row must be a JSON object")
    _require_hard_flags("row", _DictFlags(value))
    _require_public_keys("row", value, _PUBLIC_ROW_KEYS)
    return ResearchMarketProbabilityDepthMemoryGuardRow(
        candidate_ref=_public_string("candidate_ref", value["candidate_ref"]),
        market_ref=_public_string("market_ref", value["market_ref"]),
        source_ref=_public_string("source_ref", value["source_ref"]),
        quoted_probability=_public_probability(
            "quoted_probability",
            value["quoted_probability"],
        ),
        target_probability=_public_probability(
            "target_probability",
            value["target_probability"],
        ),
        probability_gap=_public_ratio("probability_gap", value["probability_gap"]),
        available_depth=_public_ratio("available_depth", value["available_depth"]),
        estimated_cost=_public_ratio("estimated_cost", value["estimated_cost"]),
        memory_cost_limit=_public_positive_ratio(
            "memory_cost_limit",
            value["memory_cost_limit"],
        ),
        cost_to_limit_ratio=_public_ratio(
            "cost_to_limit_ratio",
            value["cost_to_limit_ratio"],
        ),
        market_impact_probability=_public_probability(
            "market_impact_probability",
            value["market_impact_probability"],
        ),
        age_hours=_public_ratio("age_hours", value["age_hours"]),
        status=_public_string("status", value["status"]),
        reason_codes=_public_reason_codes(
            "reason_codes",
            value["reason_codes"],
            ROW_REASON_CODES,
        ),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _require_public_keys(
    label: str,
    value: dict[str, Any],
    expected: frozenset[str],
) -> None:
    if frozenset(value.keys()) != expected:
        raise ValueError(f"{label} has unsupported public fields")


def _public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    return value


def _public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    return _as_utc(field_name, parsed)


def _public_count(field_name: str, value: object) -> Decimal:
    return _public_decimal(field_name, value, _normalize_nonnegative_count)


def _public_ratio(field_name: str, value: object) -> Decimal:
    return _public_decimal(field_name, value, _normalize_nonnegative_ratio)


def _public_positive_ratio(field_name: str, value: object) -> Decimal:
    return _public_decimal(field_name, value, _normalize_positive_ratio)


def _public_probability(field_name: str, value: object) -> Decimal:
    return _public_decimal(field_name, value, _normalize_probability)


def _public_decimal(field_name: str, value: object, normalizer: Any) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = normalizer(field_name, decimal_value)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _public_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(field_name, tuple(value), allowed)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in _UNSAFE_VALUE_FRAGMENTS):
            raise ValueError(f"sensitive value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in _PUBLIC_RAW_KEY_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}")
            if any(fragment in lowered_key for fragment in _UNSAFE_KEY_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _redacted_ref(prefix: str, value: str) -> str:
    _require_canonical_string("prefix", prefix)
    _require_canonical_string("ref source", value)
    return f"{prefix}{sha256(value.encode('utf-8')).hexdigest()[:_REF_DIGEST_LENGTH]}"


def _require_ref(field_name: str, value: object, prefix: str) -> None:
    _require_canonical_string(field_name, value)
    if not str(value).startswith(prefix):
        raise ValueError(f"{field_name} must be a safe ref")
    digest = str(value).removeprefix(prefix)
    if len(digest) != _REF_DIGEST_LENGTH:
        raise ValueError(f"{field_name} must be a safe ref")
    if any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{field_name} must be a safe ref")


def _require_sha256_hex(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if len(str(value)) != _SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in str(value)):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_source_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _normalize_rows(
    value: object,
) -> tuple[ResearchMarketProbabilityDepthMemoryGuardRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    for row in rows:
        if type(row) is not ResearchMarketProbabilityDepthMemoryGuardRow:
            raise ValueError(
                "rows must contain ResearchMarketProbabilityDepthMemoryGuardRow values",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    for code in codes:
        _require_member(field_name, code, allowed)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return codes


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO_RATIO or decimal_value > _ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize_ratio(decimal_value)


def _normalize_nonnegative_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_ratio(decimal_value)


def _normalize_positive_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= _ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize_ratio(decimal_value)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value.quantize(_COUNT_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize_ratio(numerator / denominator)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO_RATIO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize_ratio(sum(values, _ZERO_RATIO) / Decimal(len(values)))


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO_RATIO
    return max(values).quantize(_RATIO_QUANTUM)


def _abs_ratio(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return abs(value).quantize(_RATIO_QUANTUM)


__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_DEPTH_MEMORY_GUARD_CONFIG_VERSION",
    "REPORT_REASON_CODES",
    "ROW_REASON_CODES",
    "STATUSES",
    "ResearchMarketProbabilityDepthMemoryGuardConfig",
    "ResearchMarketProbabilityDepthMemoryGuardObservation",
    "ResearchMarketProbabilityDepthMemoryGuardReport",
    "ResearchMarketProbabilityDepthMemoryGuardRow",
    "build_research_market_probability_depth_memory_guard_report",
    "research_market_probability_depth_memory_guard_report_payload",
    "validate_research_market_probability_depth_memory_guard_report_payload",
)
