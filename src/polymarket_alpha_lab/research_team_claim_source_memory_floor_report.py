"""Pure report-only reducer for claim evidence memory-floor checks."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_TEAM_CLAIM_SOURCE_MEMORY_FLOOR_REPORT_CONFIG_VERSION = (
    "research-team-claim-source-memory-floor-report-v0"
)
STATUSES = ("pass", "watch", "block")
NO_INPUTS_REASON = "memory_floor_no_inputs"
PASS_REASON = "memory_floor_pass"
WATCH_REASON = "memory_floor_watch"
BLOCK_REASON = "memory_floor_block"
STALE_REASON = "memory_floor_stale"
THIN_DIGESTS_REASON = "memory_floor_thin_digests"
REASON_CODE_SEQUENCE = (
    BLOCK_REASON,
    NO_INPUTS_REASON,
    PASS_REASON,
    STALE_REASON,
    THIN_DIGESTS_REASON,
    WATCH_REASON,
)
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


__all__ = (
    "DEFAULT_RESEARCH_TEAM_CLAIM_SOURCE_MEMORY_FLOOR_REPORT_CONFIG_VERSION",
    "ResearchTeamClaimSourceMemoryFloorConfig",
    "ResearchTeamClaimSourceMemoryFloorObservation",
    "ResearchTeamClaimSourceMemoryFloorReasonCodeCount",
    "ResearchTeamClaimSourceMemoryFloorReport",
    "ResearchTeamClaimSourceMemoryFloorRow",
    "build_research_team_claim_source_memory_floor_report",
    "research_team_claim_source_memory_floor_public_payload",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_VALUE_FRAGMENTS = frozenset(
    (
        "candidate",
        _join_parts("market", "_id"),
        _join_parts("market", "-id"),
        _join_parts("markets", "/"),
        _join_parts("slu", "g"),
        _join_parts("quest", "ion"),
        _join_parts("source", "_url"),
        _join_parts("source", "_", "text"),
        _join_parts("te", "xt"),
        _join_parts("d", "b"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("or", "der"),
        _join_parts("tra", "de"),
        _join_parts("bu", "y"),
        _join_parts("se", "ll"),
        _join_parts("siz", "e"),
        _join_parts("siz", "ing"),
        _join_parts("rec", "ommend"),
        _join_parts("rou", "te"),
        _join_parts("exec", "ute"),
        "secret",
        "postgres",
        "http://",
        "https://",
        "://",
    ),
)


@dataclass(frozen=True)
class ResearchTeamClaimSourceMemoryFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_CLAIM_SOURCE_MEMORY_FLOOR_REPORT_CONFIG_VERSION
    )
    pass_memory_floor: Decimal = Decimal("0.700000")
    watch_memory_floor: Decimal = Decimal("0.400000")
    stale_after_seconds: Decimal = Decimal("86400.000000")
    min_distinct_digest_count: Decimal = Decimal("2.000000")
    fresh_weight: Decimal = Decimal("0.600000")
    distinct_weight: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamClaimSourceMemoryFloorConfig:
            raise TypeError(
                "ResearchTeamClaimSourceMemoryFloorConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamClaimSourceMemoryFloorConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_CLAIM_SOURCE_MEMORY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported config version")
        for field_name in ("pass_memory_floor", "watch_memory_floor"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_memory_floor <= self.watch_memory_floor:
            raise ValueError("pass_memory_floor must exceed watch_memory_floor")
        object.__setattr__(
            self,
            "stale_after_seconds",
            _require_positive_decimal("stale_after_seconds", self.stale_after_seconds),
        )
        object.__setattr__(
            self,
            "min_distinct_digest_count",
            _require_positive_count_decimal(
                "min_distinct_digest_count",
                self.min_distinct_digest_count,
            ),
        )
        for field_name in ("fresh_weight", "distinct_weight"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_weight + self.distinct_weight != ONE:
            raise ValueError("fresh_weight and distinct_weight must sum to 1")
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamClaimSourceMemoryFloorObservation:
    claim_id: str
    team_id: str
    evidence_id: str
    evidence_locator: str
    evidence_excerpt: str
    observed_at: datetime
    memory_strength: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamClaimSourceMemoryFloorObservation:
            raise TypeError(
                "ResearchTeamClaimSourceMemoryFloorObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamClaimSourceMemoryFloorObservation,
            "observation",
        )
        for field_name in ("claim_id", "team_id", "evidence_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_canonical_string("evidence_locator", self.evidence_locator)
        _require_canonical_string("evidence_excerpt", self.evidence_excerpt)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "memory_strength",
            _require_ratio_decimal("memory_strength", self.memory_strength),
        )
        require_paper_only_flags("observation", self)


@dataclass(frozen=True)
class ResearchTeamClaimSourceMemoryFloorRow:
    claim_id: str
    team_id: str
    status: str
    observation_count: Decimal
    fresh_observation_count: Decimal
    stale_observation_count: Decimal
    distinct_digest_count: Decimal
    latest_age_seconds: Decimal
    average_memory_strength: Decimal
    freshness_score: Decimal
    distinct_digest_score: Decimal
    memory_floor_score: Decimal
    evidence_digests: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamClaimSourceMemoryFloorRow:
            raise TypeError(
                "ResearchTeamClaimSourceMemoryFloorRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamClaimSourceMemoryFloorRow, "row")
        _require_public_identifier("claim_id", self.claim_id)
        _require_public_identifier("team_id", self.team_id)
        _require_status("status", self.status)
        for field_name in (
            "observation_count",
            "fresh_observation_count",
            "stale_observation_count",
            "distinct_digest_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_age_seconds",
            _require_nonnegative_decimal("latest_age_seconds", self.latest_age_seconds),
        )
        for field_name in (
            "average_memory_strength",
            "freshness_score",
            "distinct_digest_score",
            "memory_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_digests",
            _normalize_digest_tuple("evidence_digests", self.evidence_digests),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchTeamClaimSourceMemoryFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamClaimSourceMemoryFloorReasonCodeCount:
            raise TypeError(
                "ResearchTeamClaimSourceMemoryFloorReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamClaimSourceMemoryFloorReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        require_paper_only_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamClaimSourceMemoryFloorReport:
    generated_at: datetime
    config_version: str
    status: str
    claim_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_memory_floor_score: Decimal
    rows: tuple[ResearchTeamClaimSourceMemoryFloorRow, ...]
    reason_code_counts: tuple[ResearchTeamClaimSourceMemoryFloorReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    payload_sha256: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamClaimSourceMemoryFloorReport:
            raise TypeError(
                "ResearchTeamClaimSourceMemoryFloorReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamClaimSourceMemoryFloorReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "claim_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_memory_floor_score",
            _require_ratio_decimal(
                "average_memory_floor_score",
                self.average_memory_floor_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _payload_digest(self)
        if self.payload_sha256:
            _require_full_sha256("payload_sha256", self.payload_sha256)
            if self.payload_sha256 != expected_digest:
                raise ValueError("payload_sha256 must match the public payload")
        else:
            object.__setattr__(self, "payload_sha256", expected_digest)


_PUBLIC_DATACLASS_TYPES = (
    ResearchTeamClaimSourceMemoryFloorConfig,
    ResearchTeamClaimSourceMemoryFloorObservation,
    ResearchTeamClaimSourceMemoryFloorReasonCodeCount,
    ResearchTeamClaimSourceMemoryFloorReport,
    ResearchTeamClaimSourceMemoryFloorRow,
)


def build_research_team_claim_source_memory_floor_report(
    observations: list[ResearchTeamClaimSourceMemoryFloorObservation]
    | tuple[ResearchTeamClaimSourceMemoryFloorObservation, ...],
    *,
    config: ResearchTeamClaimSourceMemoryFloorConfig,
    generated_at: datetime,
) -> ResearchTeamClaimSourceMemoryFloorReport:
    if type(config) is not ResearchTeamClaimSourceMemoryFloorConfig:
        raise ValueError("config must be a ResearchTeamClaimSourceMemoryFloorConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[tuple[str, str], list[ResearchTeamClaimSourceMemoryFloorObservation]] = {}
    for item in normalized:
        grouped.setdefault((item.claim_id, item.team_id), []).append(item)

    rows = tuple(
        _row_from_observations(
            grouped[key],
            config=config,
            generated_at=generated_at_utc,
        )
        for key in sorted(grouped)
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchTeamClaimSourceMemoryFloorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        claim_count=_decimal_count(len(rows)),
        observation_count=sum((row.observation_count for row in rows), ZERO),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_memory_floor_score=_average_memory_floor_score(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_team_claim_source_memory_floor_public_payload(
    report: ResearchTeamClaimSourceMemoryFloorReport,
) -> dict[str, object]:
    if type(report) is not ResearchTeamClaimSourceMemoryFloorReport:
        raise ValueError("report must be a ResearchTeamClaimSourceMemoryFloorReport")
    _require_public_value("report", report)
    _reconstruct_public_dataclass("report", report)
    payload = _public_payload_from_report(report, include_digest=True)
    _reject_unsafe_public_strings("public payload", payload)
    return payload


def _row_from_observations(
    observations: list[ResearchTeamClaimSourceMemoryFloorObservation],
    *,
    config: ResearchTeamClaimSourceMemoryFloorConfig,
    generated_at: datetime,
) -> ResearchTeamClaimSourceMemoryFloorRow:
    rows = tuple(
        sorted(
            observations,
            key=lambda item: (
                item.evidence_id,
                _evidence_digest(item),
            ),
        ),
    )
    latest_age_seconds = min(_age_seconds(generated_at, item.observed_at) for item in rows)
    stale_count = sum(
        1 for item in rows if _age_seconds(generated_at, item.observed_at) > config.stale_after_seconds
    )
    fresh_count = len(rows) - stale_count
    evidence_digests = tuple(dict.fromkeys(_evidence_digest(item) for item in rows))
    observation_count = _decimal_count(len(rows))
    freshness_score = _ratio(_decimal_count(fresh_count), observation_count)
    distinct_digest_score = min(
        ONE,
        _ratio(_decimal_count(len(evidence_digests)), config.min_distinct_digest_count),
    )
    average_memory_strength = _average_decimal(tuple(item.memory_strength for item in rows))
    support_score = _ratio(freshness_score + distinct_digest_score, TWO)
    memory_floor_score = _quantize(
        average_memory_strength * config.fresh_weight
        + support_score * config.distinct_weight,
    )
    status = _row_status(
        memory_floor_score=memory_floor_score,
        stale_count=stale_count,
        distinct_digest_count=_decimal_count(len(evidence_digests)),
        config=config,
    )
    return ResearchTeamClaimSourceMemoryFloorRow(
        claim_id=rows[0].claim_id,
        team_id=rows[0].team_id,
        status=status,
        observation_count=observation_count,
        fresh_observation_count=_decimal_count(fresh_count),
        stale_observation_count=_decimal_count(stale_count),
        distinct_digest_count=_decimal_count(len(evidence_digests)),
        latest_age_seconds=latest_age_seconds,
        average_memory_strength=average_memory_strength,
        freshness_score=freshness_score,
        distinct_digest_score=distinct_digest_score,
        memory_floor_score=memory_floor_score,
        evidence_digests=evidence_digests,
        reason_codes=_row_reason_codes(
            status=status,
            stale_count=stale_count,
            distinct_digest_count=_decimal_count(len(evidence_digests)),
            config=config,
        ),
    )


def _row_status(
    *,
    memory_floor_score: Decimal,
    stale_count: int,
    distinct_digest_count: Decimal,
    config: ResearchTeamClaimSourceMemoryFloorConfig,
) -> str:
    if memory_floor_score < config.watch_memory_floor:
        return "block"
    if memory_floor_score < config.pass_memory_floor:
        return "watch"
    if stale_count:
        return "watch"
    if distinct_digest_count < config.min_distinct_digest_count:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    stale_count: int,
    distinct_digest_count: Decimal,
    config: ResearchTeamClaimSourceMemoryFloorConfig,
) -> tuple[str, ...]:
    reason_codes = {f"memory_floor_{status}"}
    if stale_count:
        reason_codes.add(STALE_REASON)
    if distinct_digest_count < config.min_distinct_digest_count:
        reason_codes.add(THIN_DIGESTS_REASON)
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _report_status(rows: tuple[ResearchTeamClaimSourceMemoryFloorRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamClaimSourceMemoryFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in seen
    )


def _reason_code_counts(
    rows: tuple[ResearchTeamClaimSourceMemoryFloorRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamClaimSourceMemoryFloorReasonCodeCount, ...]:
    if reason_codes == (NO_INPUTS_REASON,):
        return (
            ResearchTeamClaimSourceMemoryFloorReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchTeamClaimSourceMemoryFloorReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in reason_codes
    )


def _normalize_observations(value: object) -> tuple[ResearchTeamClaimSourceMemoryFloorObservation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    observations = tuple(value)
    for item in observations:
        if type(item) is not ResearchTeamClaimSourceMemoryFloorObservation:
            raise ValueError("observations must contain exact observation values")
        require_paper_only_flags("observation", item)
    return observations


def _normalize_rows(value: object) -> tuple[ResearchTeamClaimSourceMemoryFloorRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    previous_key: tuple[str, str] | None = None
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchTeamClaimSourceMemoryFloorRow:
            raise ValueError("rows must contain exact row values")
        require_paper_only_flags("row", row)
        key = (row.claim_id, row.team_id)
        if key in seen:
            raise ValueError("rows must be unique")
        if previous_key is not None and previous_key > key:
            raise ValueError("rows must be sorted")
        previous_key = key
        seen.add(key)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamClaimSourceMemoryFloorReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    counts = tuple(value)
    seen: set[str] = set()
    previous_index: int | None = None
    for item in counts:
        if type(item) is not ResearchTeamClaimSourceMemoryFloorReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact count values")
        require_paper_only_flags("reason_code_count", item)
        current_index = REASON_CODE_SEQUENCE.index(item.reason_code)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        if previous_index is not None and previous_index > current_index:
            raise ValueError("reason_code_counts must be sorted")
        previous_index = current_index
        seen.add(item.reason_code)
    return counts


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must be nonempty")
    seen: set[str] = set()
    previous_index: int | None = None
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        current_index = REASON_CODE_SEQUENCE.index(reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous_index is not None and previous_index > current_index:
            raise ValueError(f"{field_name} must be sorted")
        previous_index = current_index
        seen.add(reason_code)
    return reason_codes


def _normalize_digest_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    digests = tuple(value)
    if not digests:
        raise ValueError(f"{field_name} must be nonempty")
    seen: set[str] = set()
    for digest in digests:
        _require_short_sha256(field_name, digest)
        if digest in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(digest)
    return digests


def _validate_row_consistency(row: ResearchTeamClaimSourceMemoryFloorRow) -> None:
    if row.observation_count <= ZERO:
        raise ValueError("observation_count must be positive")
    if row.fresh_observation_count + row.stale_observation_count != row.observation_count:
        raise ValueError("observation counts must tie")
    if row.distinct_digest_count > row.observation_count:
        raise ValueError("distinct_digest_count must not exceed observation_count")
    if row.distinct_digest_count != _decimal_count(len(row.evidence_digests)):
        raise ValueError("evidence_digests must match distinct_digest_count")
    status_reason = f"memory_floor_{row.status}"
    if status_reason not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    status_reason_count = sum(
        1
        for reason_code in row.reason_codes
        if reason_code in (PASS_REASON, WATCH_REASON, BLOCK_REASON)
    )
    if status_reason_count != 1:
        raise ValueError("reason_codes must contain exactly one status reason")
    if row.stale_observation_count > ZERO and STALE_REASON not in row.reason_codes:
        raise ValueError("reason_codes must include stale observations")


def _validate_report_consistency(report: ResearchTeamClaimSourceMemoryFloorReport) -> None:
    if report.claim_count != _decimal_count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.observation_count != sum((row.observation_count for row in report.rows), ZERO):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_memory_floor_score != _average_memory_floor_score(report.rows):
        raise ValueError("average_memory_floor_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _public_payload_from_report(
    report: ResearchTeamClaimSourceMemoryFloorReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {}
    for field in fields(report):
        if field.name == "payload_sha256" and not include_digest:
            continue
        payload[field.name] = _json_ready(getattr(report, field.name))
    return payload


def _payload_digest(report: ResearchTeamClaimSourceMemoryFloorReport) -> str:
    payload = _public_payload_from_report(report, include_digest=False)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("JSON value must be a supported public dataclass")
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        _require_six_decimal_json_decimal("JSON Decimal value", value)
        return str(value)
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is str or type(value) is bool or value is None:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (list, dict, set, frozenset)):
        raise ValueError("JSON value must not be a raw collection")
    raise ValueError("value is not JSON serializable")


def _require_public_value(field_name: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a supported public dataclass")
        require_paper_only_flags(field_name, value)
        for field in fields(value):
            _require_public_value(f"{field_name}.{field.name}", getattr(value, field.name))
        _reconstruct_public_dataclass(field_name, value)
        return
    if type(value) is Decimal:
        _require_six_decimal_json_decimal(field_name, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(field_name, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_public_value(f"{field_name}[{index}]", item)
        return
    if type(value) is str:
        return
    if type(value) is bool or value is None:
        return
    if type(value) is int:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if isinstance(value, (list, dict, set, frozenset)):
        raise ValueError(f"{field_name} must not be a raw collection")
    raise ValueError(f"{field_name} must remain constructor-normalized")


def _reconstruct_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid: {exc}") from exc


def _reject_unsafe_public_strings(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _contains_unsafe_public_value(key):
                raise ValueError(f"{label} contains raw material")
            _reject_unsafe_public_strings(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_strings(label, item)
        return
    if type(value) is str and _contains_unsafe_public_value(value):
        raise ValueError(f"{label} contains raw material")


def _contains_unsafe_public_value(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS)


def _evidence_digest(item: ResearchTeamClaimSourceMemoryFloorObservation) -> str:
    raw_digest_input = {
        "evidence_excerpt": item.evidence_excerpt,
        "evidence_id": item.evidence_id,
        "evidence_locator": item.evidence_locator,
    }
    digest = sha256(
        json.dumps(
            raw_digest_input,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    return f"sha256:{digest[:16]}"


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() != ZERO_SECONDS:
        raise ValueError(f"{field_name} must be normalized to UTC")


ZERO_SECONDS = datetime(2026, 1, 1, tzinfo=UTC).utcoffset()


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_count_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _require_six_decimal_json_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(QUANT)
    except ArithmeticError as exc:
        raise ValueError(f"{field_name} must use six decimal places") from exc
    if normalized != value or not value.same_quantum(QUANT):
        raise ValueError(f"{field_name} must use six decimal places")


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count input must be a nonnegative int")
    return Decimal(value).quantize(QUANT)


def _status_count(
    rows: tuple[ResearchTeamClaimSourceMemoryFloorRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(sum(values, ZERO), _decimal_count(len(values)))


def _average_memory_floor_score(
    rows: tuple[ResearchTeamClaimSourceMemoryFloorRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _average_decimal(tuple(row.memory_floor_score for row in rows))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    elapsed = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(elapsed.days * 86400 + elapsed.seconds)
            + (Decimal(elapsed.microseconds) / MICROSECONDS_PER_SECOND)
        ).quantize(QUANT)


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    normalized = _require_canonical_string(field_name, value)
    if _contains_unsafe_public_value(normalized):
        raise ValueError(f"{field_name} contains raw material")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_short_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or not value.startswith("sha256:") or len(value) != 23:
        raise ValueError(f"{field_name} must be a short sha256 value")
    suffix = value.removeprefix("sha256:")
    if not suffix or any(character not in "0123456789abcdef" for character in suffix):
        raise ValueError(f"{field_name} must be lowercase sha256 hex")


def _require_full_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a full sha256 value")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be lowercase sha256 hex")
