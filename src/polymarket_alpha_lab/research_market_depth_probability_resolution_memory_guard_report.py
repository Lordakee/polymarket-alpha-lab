"""Read-only depth, probability, and resolution-memory guard report."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_RESOLUTION_MEMORY_GUARD_CONFIG_VERSION = (
    "research-market-depth-probability-resolution-memory-guard-v0"
)

STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "depth_coverage_clear",
    "depth_coverage_watch",
    "depth_coverage_block",
    "probability_gap_clear",
    "probability_gap_watch",
    "probability_gap_block",
    "resolution_memory_fresh",
    "resolution_memory_stale",
    "resolution_memory_block",
)
REPORT_REASON_CODES = (
    "depth_probability_resolution_memory_clear",
    "no_observations",
    "depth_coverage_block",
    "probability_gap_block",
    "resolution_memory_block",
    "depth_coverage_watch",
    "probability_gap_watch",
    "resolution_memory_stale",
)
_REPORT_BLOCK_CODES = (
    "depth_coverage_block",
    "probability_gap_block",
    "resolution_memory_block",
)
_REPORT_WATCH_CODES = (
    "depth_coverage_watch",
    "probability_gap_watch",
    "resolution_memory_stale",
)
_REF_DIGEST_LENGTH = 16
_SHA256_HEX_LENGTH = 64
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "slug",
    "question",
    "source_url",
    "source_text",
    "source_dsn",
    "source_table",
    "source_" + "tok" + "en",
    "dsn",
    "table",
    "tok" + "en",
    "data" + "base",
    "d" + "b",
    "net" + "work",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "li" + "ve",
    "tra" + "de",
    "tra" + "ding",
    "siz" + "ing",
    "recomm" + "endation",
)
_UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "://",
    "secret",
    "private",
    "internal",
    "post" + "gresql",
    "tok" + "en",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "tra" + "ding",
    "siz" + "ing",
    "recomm" + "endation",
)


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityResolutionMemoryGuardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_RESOLUTION_MEMORY_GUARD_CONFIG_VERSION
    )
    watch_depth_coverage_ratio: Decimal = Decimal("0.750000")
    block_depth_coverage_ratio: Decimal = Decimal("0.500000")
    watch_probability_gap: Decimal = Decimal("0.080000")
    block_probability_gap: Decimal = Decimal("0.150000")
    watch_resolution_memory_age_hours: Decimal = Decimal("24.000000")
    block_resolution_memory_age_hours: Decimal = Decimal("72.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthProbabilityResolutionMemoryGuardConfig:
            raise TypeError(
                "ResearchMarketDepthProbabilityResolutionMemoryGuardConfig does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthProbabilityResolutionMemoryGuardConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchMarketDepthProbabilityResolutionMemoryGuardConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_RESOLUTION_MEMORY_GUARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "watch_depth_coverage_ratio",
            "block_depth_coverage_ratio",
            "watch_resolution_memory_age_hours",
            "block_resolution_memory_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_probability_gap", "block_probability_gap"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityResolutionMemoryGuardObservation:
    raw_candidate_id: str
    raw_market_id: str
    raw_market_slug: str
    raw_market_question: str
    raw_source_url: str
    raw_source_text: str
    raw_source_dsn: str
    raw_source_table: str
    raw_source_token: str
    market_probability: Decimal
    resolution_memory_probability: Decimal
    available_depth: Decimal
    required_depth_floor: Decimal
    resolution_memory_age_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthProbabilityResolutionMemoryGuardObservation:
            raise TypeError(
                "ResearchMarketDepthProbabilityResolutionMemoryGuardObservation does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthProbabilityResolutionMemoryGuardObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchMarketDepthProbabilityResolutionMemoryGuardObservation",
            )
        for field_name in (
            "raw_candidate_id",
            "raw_market_id",
            "raw_market_slug",
            "raw_market_question",
            "raw_source_url",
            "raw_source_text",
            "raw_source_dsn",
            "raw_source_table",
            "raw_source_token",
        ):
            _require_raw_string(field_name, getattr(self, field_name))
        for field_name in ("market_probability", "resolution_memory_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("available_depth", "resolution_memory_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_depth_floor",
            _normalize_positive_decimal("required_depth_floor", self.required_depth_floor),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityResolutionMemoryGuardRow:
    candidate_ref: str
    market_ref: str
    evidence_ref: str
    market_probability: Decimal
    resolution_memory_probability: Decimal
    probability_gap: Decimal
    available_depth: Decimal
    required_depth_floor: Decimal
    depth_coverage_ratio: Decimal
    resolution_memory_age_hours: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthProbabilityResolutionMemoryGuardRow:
            raise TypeError(
                "ResearchMarketDepthProbabilityResolutionMemoryGuardRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthProbabilityResolutionMemoryGuardRow:
            raise ValueError(
                "row must be exactly "
                "ResearchMarketDepthProbabilityResolutionMemoryGuardRow",
            )
        _require_ref("candidate_ref", self.candidate_ref, "candidate_ref_")
        _require_ref("market_ref", self.market_ref, "market_ref_")
        _require_ref("evidence_ref", self.evidence_ref, "evidence_ref_")
        for field_name in ("market_probability", "resolution_memory_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "probability_gap",
            "available_depth",
            "depth_coverage_ratio",
            "resolution_memory_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_depth_floor",
            _normalize_positive_decimal("required_depth_floor", self.required_depth_floor),
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
class ResearchMarketDepthProbabilityResolutionMemoryGuardReport:
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_depth_coverage_ratio: Decimal
    max_probability_gap: Decimal
    max_resolution_memory_age_hours: Decimal
    rows: tuple[ResearchMarketDepthProbabilityResolutionMemoryGuardRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthProbabilityResolutionMemoryGuardReport:
            raise TypeError(
                "ResearchMarketDepthProbabilityResolutionMemoryGuardReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthProbabilityResolutionMemoryGuardReport:
            raise ValueError(
                "report must be exactly "
                "ResearchMarketDepthProbabilityResolutionMemoryGuardReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc_exact_datetime("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_depth_coverage_ratio",
            "max_probability_gap",
            "max_resolution_memory_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_surface("report", self)


@dataclass(frozen=True)
class _PayloadFlags:
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


def build_research_market_depth_probability_resolution_memory_guard_report(
    observations: tuple[
        ResearchMarketDepthProbabilityResolutionMemoryGuardObservation,
        ...,
    ],
    *,
    config: ResearchMarketDepthProbabilityResolutionMemoryGuardConfig | None = None,
    generated_at: datetime,
) -> ResearchMarketDepthProbabilityResolutionMemoryGuardReport:
    if type(observations) is not tuple:
        observations = tuple(observations)
    cfg = config or ResearchMarketDepthProbabilityResolutionMemoryGuardConfig()
    if type(cfg) is not ResearchMarketDepthProbabilityResolutionMemoryGuardConfig:
        raise ValueError(
            "config must be a "
            "ResearchMarketDepthProbabilityResolutionMemoryGuardConfig",
        )
    generated_at_utc = _as_utc_exact_datetime("generated_at", generated_at)
    rows = tuple(_row_from_observation(observation, cfg) for observation in observations)
    rows = tuple(sorted(rows, key=_row_sort_key))
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows)
    observation_count = _count_decimal(len(rows))
    pass_count = _count_status(rows, "pass")
    watch_count = _count_status(rows, "watch")
    block_count = _count_status(rows, "block")
    min_depth_coverage_ratio = _min_decimal(
        tuple(row.depth_coverage_ratio for row in rows),
    )
    max_probability_gap = _max_decimal(tuple(row.probability_gap for row in rows))
    max_resolution_memory_age_hours = _max_decimal(
        tuple(row.resolution_memory_age_hours for row in rows),
    )
    unsigned_payload = _report_payload_mapping(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=status,
        observation_count=observation_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        min_depth_coverage_ratio=min_depth_coverage_ratio,
        max_probability_gap=max_probability_gap,
        max_resolution_memory_age_hours=max_resolution_memory_age_hours,
        rows=rows,
        reason_codes=reason_codes,
        derived_validation_digest=None,
    )
    digest = _canonical_digest(unsigned_payload)
    return ResearchMarketDepthProbabilityResolutionMemoryGuardReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=status,
        observation_count=observation_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        min_depth_coverage_ratio=min_depth_coverage_ratio,
        max_probability_gap=max_probability_gap,
        max_resolution_memory_age_hours=max_resolution_memory_age_hours,
        rows=rows,
        reason_codes=reason_codes,
        derived_validation_digest=digest,
    )


def research_market_depth_probability_resolution_memory_guard_report_payload(
    report: ResearchMarketDepthProbabilityResolutionMemoryGuardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketDepthProbabilityResolutionMemoryGuardReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _require_hard_flags("payload", _PayloadFlags(report))
        _reject_public_numerics(report)
        _reject_unsafe_public_surface("payload", report)
        _verify_public_payload_digest(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a "
            "ResearchMarketDepthProbabilityResolutionMemoryGuardReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _PayloadFlags(payload))
    _reject_public_numerics(payload)
    _reject_unsafe_public_surface("payload", payload)
    _verify_public_payload_digest(payload)
    return payload


def validate_research_market_depth_probability_resolution_memory_guard_report_payload(
    payload: dict[str, Any],
) -> bool:
    research_market_depth_probability_resolution_memory_guard_report_payload(payload)
    return True


def _row_from_observation(
    observation: ResearchMarketDepthProbabilityResolutionMemoryGuardObservation,
    config: ResearchMarketDepthProbabilityResolutionMemoryGuardConfig,
) -> ResearchMarketDepthProbabilityResolutionMemoryGuardRow:
    if type(observation) is not ResearchMarketDepthProbabilityResolutionMemoryGuardObservation:
        raise ValueError(
            "observations must contain "
            "ResearchMarketDepthProbabilityResolutionMemoryGuardObservation values",
        )
    _require_hard_flags("observation", observation)
    probability_gap = _abs_decimal(
        _subtract_decimal(
            observation.market_probability,
            observation.resolution_memory_probability,
        ),
    )
    depth_coverage_ratio = _ratio(
        observation.available_depth,
        observation.required_depth_floor,
    )
    status = _row_status(
        depth_coverage_ratio=depth_coverage_ratio,
        probability_gap=probability_gap,
        resolution_memory_age_hours=observation.resolution_memory_age_hours,
        config=config,
    )
    return ResearchMarketDepthProbabilityResolutionMemoryGuardRow(
        candidate_ref=_candidate_ref(observation.raw_candidate_id),
        market_ref=_market_ref(
            observation.raw_market_id,
            observation.raw_market_slug,
            observation.raw_market_question,
        ),
        evidence_ref=_evidence_ref(
            observation.raw_source_url,
            observation.raw_source_text,
            observation.raw_source_dsn,
            observation.raw_source_table,
            observation.raw_source_token,
        ),
        market_probability=observation.market_probability,
        resolution_memory_probability=observation.resolution_memory_probability,
        probability_gap=probability_gap,
        available_depth=observation.available_depth,
        required_depth_floor=observation.required_depth_floor,
        depth_coverage_ratio=depth_coverage_ratio,
        resolution_memory_age_hours=observation.resolution_memory_age_hours,
        status=status,
        reason_codes=_row_reason_codes(
            depth_coverage_ratio=depth_coverage_ratio,
            probability_gap=probability_gap,
            resolution_memory_age_hours=observation.resolution_memory_age_hours,
            config=config,
        ),
    )


def _row_status(
    *,
    depth_coverage_ratio: Decimal,
    probability_gap: Decimal,
    resolution_memory_age_hours: Decimal,
    config: ResearchMarketDepthProbabilityResolutionMemoryGuardConfig,
) -> str:
    if (
        depth_coverage_ratio <= config.block_depth_coverage_ratio
        or probability_gap >= config.block_probability_gap
        or resolution_memory_age_hours >= config.block_resolution_memory_age_hours
    ):
        return "block"
    if (
        depth_coverage_ratio <= config.watch_depth_coverage_ratio
        or probability_gap >= config.watch_probability_gap
        or resolution_memory_age_hours >= config.watch_resolution_memory_age_hours
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    depth_coverage_ratio: Decimal,
    probability_gap: Decimal,
    resolution_memory_age_hours: Decimal,
    config: ResearchMarketDepthProbabilityResolutionMemoryGuardConfig,
) -> tuple[str, ...]:
    depth_code = "depth_coverage_clear"
    if depth_coverage_ratio <= config.block_depth_coverage_ratio:
        depth_code = "depth_coverage_block"
    elif depth_coverage_ratio <= config.watch_depth_coverage_ratio:
        depth_code = "depth_coverage_watch"
    probability_code = "probability_gap_clear"
    if probability_gap >= config.block_probability_gap:
        probability_code = "probability_gap_block"
    elif probability_gap >= config.watch_probability_gap:
        probability_code = "probability_gap_watch"
    memory_code = "resolution_memory_fresh"
    if resolution_memory_age_hours >= config.block_resolution_memory_age_hours:
        memory_code = "resolution_memory_block"
    elif resolution_memory_age_hours >= config.watch_resolution_memory_age_hours:
        memory_code = "resolution_memory_stale"
    return (depth_code, probability_code, memory_code)


def _report_status(
    rows: tuple[ResearchMarketDepthProbabilityResolutionMemoryGuardRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketDepthProbabilityResolutionMemoryGuardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_observations",)
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    selected_codes = tuple(
        code
        for code in _REPORT_BLOCK_CODES + _REPORT_WATCH_CODES
        if code in row_codes
    )
    if selected_codes:
        return selected_codes
    return ("depth_probability_resolution_memory_clear",)


def _row_sort_key(
    row: ResearchMarketDepthProbabilityResolutionMemoryGuardRow,
) -> tuple[Decimal, str, str, str]:
    severity = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}
    return (severity[row.status], row.market_ref, row.candidate_ref, row.evidence_ref)


def _validate_config(
    config: ResearchMarketDepthProbabilityResolutionMemoryGuardConfig,
) -> None:
    if config.watch_depth_coverage_ratio <= config.block_depth_coverage_ratio:
        raise ValueError(
            "watch_depth_coverage_ratio must exceed block_depth_coverage_ratio",
        )
    if config.watch_probability_gap >= config.block_probability_gap:
        raise ValueError("watch_probability_gap must be less than block_probability_gap")
    if (
        config.watch_resolution_memory_age_hours
        >= config.block_resolution_memory_age_hours
    ):
        raise ValueError(
            "watch_resolution_memory_age_hours must be less than "
            "block_resolution_memory_age_hours",
        )


def _validate_row(
    row: ResearchMarketDepthProbabilityResolutionMemoryGuardRow,
) -> None:
    expected_gap = _abs_decimal(
        _subtract_decimal(row.market_probability, row.resolution_memory_probability),
    )
    if row.probability_gap != expected_gap:
        raise ValueError("probability_gap must match market and memory probabilities")
    expected_depth_coverage_ratio = _ratio(row.available_depth, row.required_depth_floor)
    if row.depth_coverage_ratio != expected_depth_coverage_ratio:
        raise ValueError("depth_coverage_ratio must match depth inputs")
    if row.status == "pass" and any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("pass rows must not include watch reason codes")
    if row.status == "pass" and any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("pass rows must not include block reason codes")


def _validate_report(
    report: ResearchMarketDepthProbabilityResolutionMemoryGuardReport,
) -> None:
    if report.observation_count != _count_decimal(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _count_status(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_status(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_status(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.min_depth_coverage_ratio != _min_decimal(
        tuple(row.depth_coverage_ratio for row in report.rows),
    ):
        raise ValueError("min_depth_coverage_ratio must match rows")
    if report.max_probability_gap != _max_decimal(
        tuple(row.probability_gap for row in report.rows),
    ):
        raise ValueError("max_probability_gap must match rows")
    if report.max_resolution_memory_age_hours != _max_decimal(
        tuple(row.resolution_memory_age_hours for row in report.rows),
    ):
        raise ValueError("max_resolution_memory_age_hours must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    expected_digest = _canonical_digest(_unsigned_report_payload(report))
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report")


def _unsigned_report_payload(
    report: ResearchMarketDepthProbabilityResolutionMemoryGuardReport,
) -> dict[str, Any]:
    return _report_payload_mapping(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        observation_count=report.observation_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        min_depth_coverage_ratio=report.min_depth_coverage_ratio,
        max_probability_gap=report.max_probability_gap,
        max_resolution_memory_age_hours=report.max_resolution_memory_age_hours,
        rows=report.rows,
        reason_codes=report.reason_codes,
        derived_validation_digest=None,
    )


def _report_payload_mapping(
    *,
    generated_at: datetime,
    config_version: str,
    status: str,
    observation_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    min_depth_coverage_ratio: Decimal,
    max_probability_gap: Decimal,
    max_resolution_memory_age_hours: Decimal,
    rows: tuple[ResearchMarketDepthProbabilityResolutionMemoryGuardRow, ...],
    reason_codes: tuple[str, ...],
    derived_validation_digest: str | None,
) -> dict[str, Any]:
    payload = {
        "generated_at": generated_at,
        "config_version": config_version,
        "status": status,
        "observation_count": observation_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "min_depth_coverage_ratio": min_depth_coverage_ratio,
        "max_probability_gap": max_probability_gap,
        "max_resolution_memory_age_hours": max_resolution_memory_age_hours,
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if derived_validation_digest is not None:
        payload["derived_validation_digest"] = derived_validation_digest
    return _json_ready(payload)


def _verify_public_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _canonical_digest(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


def _canonical_digest(payload: object) -> str:
    ready = _json_ready(payload)
    encoded = json.dumps(
        ready,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


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
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, (str, bool)):
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


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_value_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_key_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _has_unsafe_public_key_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_KEY_FRAGMENTS)


def _has_unsafe_public_value_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_VALUE_FRAGMENTS)


def _candidate_ref(raw_candidate_id: str) -> str:
    digest = sha256(raw_candidate_id.encode("utf-8")).hexdigest()[:_REF_DIGEST_LENGTH]
    return f"candidate_ref_{digest}"


def _market_ref(raw_market_id: str, raw_market_slug: str, raw_market_question: str) -> str:
    digest = _parts_digest(raw_market_id, raw_market_slug, raw_market_question)
    return f"market_ref_{digest}"


def _evidence_ref(
    raw_source_url: str,
    raw_source_text: str,
    raw_source_dsn: str,
    raw_source_table: str,
    raw_source_token: str,
) -> str:
    digest = _parts_digest(
        raw_source_url,
        raw_source_text,
        raw_source_dsn,
        raw_source_table,
        raw_source_token,
    )
    return f"evidence_ref_{digest}"


def _parts_digest(*parts: str) -> str:
    encoded = "\x1f".join(parts).encode("utf-8")
    return sha256(encoded).hexdigest()[:_REF_DIGEST_LENGTH]


def _require_ref(field_name: str, value: object, prefix: str) -> None:
    if type(value) is not str or not value.startswith(prefix):
        raise ValueError(f"{field_name} must be a redacted reference")
    digest = value[len(prefix) :]
    if len(digest) != _REF_DIGEST_LENGTH or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise ValueError(f"{field_name} must contain a redacted hex digest")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != _SHA256_HEX_LENGTH or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        _require_member(field_name, value, allowed_values)
        if value in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(value)
        normalized.append(value)
    return tuple(normalized)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchMarketDepthProbabilityResolutionMemoryGuardRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketDepthProbabilityResolutionMemoryGuardRow:
            raise ValueError(
                "rows must contain "
                "ResearchMarketDepthProbabilityResolutionMemoryGuardRow values",
            )
    return rows


def _require_raw_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a nonempty string")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a nonempty string")
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be canonical public text")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")


def _as_utc_exact_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be an exact datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a count Decimal")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < _QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(_QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return (left - right).quantize(_QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return abs(value).quantize(_QUANTUM)


def _count_decimal(value: int) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return Decimal(value).quantize(_QUANTUM)


def _count_status(
    rows: tuple[ResearchMarketDepthProbabilityResolutionMemoryGuardRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(Decimal("1") for row in rows if row.status == status))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return min(values)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return max(values)


__all__ = (
    "DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_RESOLUTION_MEMORY_GUARD_CONFIG_VERSION",
    "REPORT_REASON_CODES",
    "ROW_REASON_CODES",
    "STATUSES",
    "ResearchMarketDepthProbabilityResolutionMemoryGuardConfig",
    "ResearchMarketDepthProbabilityResolutionMemoryGuardObservation",
    "ResearchMarketDepthProbabilityResolutionMemoryGuardReport",
    "ResearchMarketDepthProbabilityResolutionMemoryGuardRow",
    "build_research_market_depth_probability_resolution_memory_guard_report",
    "research_market_depth_probability_resolution_memory_guard_report_payload",
    "validate_research_market_depth_probability_resolution_memory_guard_report_payload",
)
