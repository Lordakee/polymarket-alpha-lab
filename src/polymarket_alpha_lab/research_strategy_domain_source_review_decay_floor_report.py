"""Pure report-only domain source review decay floor checks."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any, final


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_SOURCE_REVIEW_DECAY_FLOOR_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_DOMAIN_SOURCE_REVIEW_DECAY_FLOOR_REPORT_STATUSES",
    "ResearchStrategyDomainSourceReviewDecayFloorConfig",
    "ResearchStrategyDomainSourceReviewDecayFloorInput",
    "ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount",
    "ResearchStrategyDomainSourceReviewDecayFloorReport",
    "ResearchStrategyDomainSourceReviewDecayFloorRow",
    "build_research_strategy_domain_source_review_decay_floor_report",
    "research_strategy_domain_source_review_decay_floor_report_digest",
    "research_strategy_domain_source_review_decay_floor_report_payload",
    "validate_research_strategy_domain_source_review_decay_floor_public_payload",
    "validate_research_strategy_domain_source_review_decay_floor_report_digest",
)


DEFAULT_RESEARCH_STRATEGY_DOMAIN_SOURCE_REVIEW_DECAY_FLOOR_REPORT_CONFIG_VERSION = (
    "research-strategy-domain-source-review-decay-floor-report-v0"
)
RESEARCH_STRATEGY_DOMAIN_SOURCE_REVIEW_DECAY_FLOOR_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
STATUS_SORT_RANK = {"block": 0, "watch": 1, "pass": 2}

PREFIX = "research_strategy_domain_source_review_decay_floor"
NO_INPUTS_REASON = f"{PREFIX}_no_inputs"
CLEAR_REASON = f"{PREFIX}_clear"
REVIEW_SOURCE_BLOCK_REASON = f"{PREFIX}_review_source_block"
DOMAIN_SOURCE_BLOCK_REASON = f"{PREFIX}_domain_source_block"
FRESHNESS_DECAY_BLOCK_REASON = f"{PREFIX}_freshness_decay_block"
REVIEW_QUALITY_BLOCK_REASON = f"{PREFIX}_review_quality_block"
SOURCE_AUTHORITY_BLOCK_REASON = f"{PREFIX}_source_authority_block"
CONTRADICTION_PRESSURE_BLOCK_REASON = f"{PREFIX}_contradiction_pressure_block"
DECAY_FLOOR_BLOCK_REASON = f"{PREFIX}_decay_floor_block"
REVIEW_SOURCE_WATCH_REASON = f"{PREFIX}_review_source_watch"
DOMAIN_SOURCE_WATCH_REASON = f"{PREFIX}_domain_source_watch"
FRESHNESS_DECAY_WATCH_REASON = f"{PREFIX}_freshness_decay_watch"
REVIEW_QUALITY_WATCH_REASON = f"{PREFIX}_review_quality_watch"
SOURCE_AUTHORITY_WATCH_REASON = f"{PREFIX}_source_authority_watch"
CONTRADICTION_PRESSURE_WATCH_REASON = f"{PREFIX}_contradiction_pressure_watch"
DECAY_FLOOR_WATCH_REASON = f"{PREFIX}_decay_floor_watch"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    CLEAR_REASON,
    REVIEW_SOURCE_BLOCK_REASON,
    DOMAIN_SOURCE_BLOCK_REASON,
    FRESHNESS_DECAY_BLOCK_REASON,
    REVIEW_QUALITY_BLOCK_REASON,
    SOURCE_AUTHORITY_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    DECAY_FLOOR_BLOCK_REASON,
    REVIEW_SOURCE_WATCH_REASON,
    DOMAIN_SOURCE_WATCH_REASON,
    FRESHNESS_DECAY_WATCH_REASON,
    REVIEW_QUALITY_WATCH_REASON,
    SOURCE_AUTHORITY_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    DECAY_FLOOR_WATCH_REASON,
)
REASON_CODE_SET = frozenset(REASON_CODE_SEQUENCE)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_TEXT_PARTS = (
    _join_parts("raw", "_candidate"),
    _join_parts("raw", "candidate"),
    _join_parts("candidate", "_id"),
    _join_parts("candidate", "id"),
    _join_parts("market", "_id"),
    _join_parts("market", "id"),
    _join_parts("market", "_slug"),
    _join_parts("market", "slug"),
    _join_parts("market", "_question"),
    _join_parts("ques", "tion"),
    _join_parts("source", "_url"),
    _join_parts("source", "url"),
    _join_parts("source", "_text"),
    _join_parts("source", "text"),
    _join_parts("source", "_review_key"),
    _join_parts("domain", "_review_key"),
    _join_parts("source", "_id"),
    _join_parts("source", "_name"),
    _join_parts("source", "_slug"),
    _join_parts("team", "_id"),
    _join_parts("team", "_name"),
    _join_parts("team", "_slug"),
    _join_parts("private", "_team"),
    _join_parts("reviewer", "_id"),
    _join_parts("reviewer", "_name"),
    _join_parts("d", "sn"),
    _join_parts("table", "_name"),
    _join_parts("table", "name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("tra", "ding"),
    _join_parts("siz", "ing"),
    _join_parts("rec", "ommendation"),
    _join_parts("rec", "ommend"),
    _join_parts("auth", "_token"),
    _join_parts("auth", "token"),
    _join_parts("api", "_key"),
    _join_parts("private", "_key"),
    _join_parts("postgres", "://"),
    _join_parts("mysql", "://"),
    _join_parts("jdbc", ":"),
    _join_parts("http", "://"),
    _join_parts("https", "://"),
    "://",
)


class _FinalPublicDataclass:
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainSourceReviewDecayFloorConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_SOURCE_REVIEW_DECAY_FLOOR_REPORT_CONFIG_VERSION
    )
    min_review_source_count_pass: Decimal = Decimal("3.000000")
    min_review_source_count_watch: Decimal = Decimal("2.000000")
    min_domain_source_count_pass: Decimal = Decimal("2.000000")
    min_domain_source_count_watch: Decimal = Decimal("1.000000")
    max_latest_source_review_age_seconds_pass: Decimal = Decimal("1800.000000")
    max_latest_source_review_age_seconds_watch: Decimal = Decimal("7200.000000")
    review_quality_score_pass_floor: Decimal = Decimal("0.800000")
    review_quality_score_watch_floor: Decimal = Decimal("0.550000")
    source_authority_score_pass_floor: Decimal = Decimal("0.750000")
    source_authority_score_watch_floor: Decimal = Decimal("0.500000")
    contradiction_pressure_watch_ceiling: Decimal = Decimal("0.250000")
    contradiction_pressure_block_ceiling: Decimal = Decimal("0.600000")
    decay_floor_score_pass_floor: Decimal = Decimal("0.750000")
    decay_floor_score_watch_floor: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainSourceReviewDecayFloorConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_SOURCE_REVIEW_DECAY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_review_source_count_pass",
            "min_review_source_count_watch",
            "min_domain_source_count_pass",
            "min_domain_source_count_watch",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_latest_source_review_age_seconds_pass",
            "max_latest_source_review_age_seconds_watch",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "review_quality_score_pass_floor",
            "review_quality_score_watch_floor",
            "source_authority_score_pass_floor",
            "source_authority_score_watch_floor",
            "contradiction_pressure_watch_ceiling",
            "contradiction_pressure_block_ceiling",
            "decay_floor_score_pass_floor",
            "decay_floor_score_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "min_review_source_count_pass",
            self.min_review_source_count_pass,
            self.min_review_source_count_watch,
        )
        _require_at_least(
            "min_domain_source_count_pass",
            self.min_domain_source_count_pass,
            self.min_domain_source_count_watch,
        )
        _require_at_least(
            "max_latest_source_review_age_seconds_watch",
            self.max_latest_source_review_age_seconds_watch,
            self.max_latest_source_review_age_seconds_pass,
        )
        if (
            self.max_latest_source_review_age_seconds_pass
            >= self.max_latest_source_review_age_seconds_watch
        ):
            raise ValueError(
                "max_latest_source_review_age_seconds_pass must be below its watch level",
            )
        _require_at_least(
            "review_quality_score_pass_floor",
            self.review_quality_score_pass_floor,
            self.review_quality_score_watch_floor,
        )
        _require_at_least(
            "source_authority_score_pass_floor",
            self.source_authority_score_pass_floor,
            self.source_authority_score_watch_floor,
        )
        _require_at_least(
            "contradiction_pressure_block_ceiling",
            self.contradiction_pressure_block_ceiling,
            self.contradiction_pressure_watch_ceiling,
        )
        _require_at_least(
            "decay_floor_score_pass_floor",
            self.decay_floor_score_pass_floor,
            self.decay_floor_score_watch_floor,
        )
        _require_hard_flags("config", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainSourceReviewDecayFloorInput(_FinalPublicDataclass):
    source_review_key: str
    domain_review_key: str
    review_source_count: Decimal
    domain_source_count: Decimal
    latest_source_review_age_seconds: Decimal
    review_quality_score: Decimal
    source_authority_score: Decimal
    contradiction_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainSourceReviewDecayFloorInput,
            "input",
        )
        _require_canonical_string("source_review_key", self.source_review_key)
        _require_canonical_string("domain_review_key", self.domain_review_key)
        for field_name in ("review_source_count", "domain_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "latest_source_review_age_seconds",
            _normalize_nonnegative_decimal(
                "latest_source_review_age_seconds",
                self.latest_source_review_age_seconds,
            ),
        )
        for field_name in (
            "review_quality_score",
            "source_authority_score",
            "contradiction_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainSourceReviewDecayFloorRow(_FinalPublicDataclass):
    aggregate_row_number: Decimal
    source_review_digest: str
    domain_review_digest: str
    review_source_count: Decimal
    domain_source_count: Decimal
    latest_source_review_age_seconds: Decimal
    freshness_decay_score: Decimal
    review_quality_score: Decimal
    source_authority_score: Decimal
    contradiction_pressure_score: Decimal
    decay_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainSourceReviewDecayFloorRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_whole_decimal(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        _require_sha256_digest("source_review_digest", self.source_review_digest)
        _require_sha256_digest("domain_review_digest", self.domain_review_digest)
        for field_name in ("review_source_count", "domain_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "latest_source_review_age_seconds",
            _normalize_nonnegative_decimal(
                "latest_source_review_age_seconds",
                self.latest_source_review_age_seconds,
            ),
        )
        for field_name in (
            "freshness_decay_score",
            "review_quality_score",
            "source_authority_score",
            "contradiction_pressure_score",
            "decay_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainSourceReviewDecayFloorReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    config: ResearchStrategyDomainSourceReviewDecayFloorConfig
    review_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    review_source_attention_count: Decimal
    domain_source_attention_count: Decimal
    freshness_decay_attention_count: Decimal
    review_quality_attention_count: Decimal
    source_authority_attention_count: Decimal
    contradiction_pressure_attention_count: Decimal
    decay_floor_attention_count: Decimal
    mean_decay_floor_score: Decimal
    lowest_decay_floor_score: Decimal
    highest_contradiction_pressure_score: Decimal
    status: str
    rows: tuple[ResearchStrategyDomainSourceReviewDecayFloorRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainSourceReviewDecayFloorReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(self, "config", _validated_config_copy(self.config))
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_SOURCE_REVIEW_DECAY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in (
            "review_item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "review_source_attention_count",
            "domain_source_attention_count",
            "freshness_decay_attention_count",
            "review_quality_attention_count",
            "source_authority_attention_count",
            "contradiction_pressure_attention_count",
            "decay_floor_attention_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "mean_decay_floor_score",
            "lowest_decay_floor_score",
            "highest_contradiction_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self)
        expected_digest = _digest_unsigned_payload(_report_unsigned_payload(self))
        if self.public_digest:
            _require_sha256_digest("public_digest", self.public_digest)
            if self.public_digest != expected_digest:
                raise ValueError("public_digest must match report payload")
        else:
            object.__setattr__(self, "public_digest", expected_digest)


def build_research_strategy_domain_source_review_decay_floor_report(
    source_review_rows: Iterable[object],
    *,
    config: ResearchStrategyDomainSourceReviewDecayFloorConfig | None = None,
    generated_at: datetime,
) -> ResearchStrategyDomainSourceReviewDecayFloorReport:
    active_config = _validated_config_copy(
        ResearchStrategyDomainSourceReviewDecayFloorConfig()
        if config is None
        else config
    )
    _require_hard_flags("config", active_config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_input_rows(source_review_rows)
    rows = _build_rows(inputs, config=active_config)
    reason_codes = _report_reason_codes(rows)

    return ResearchStrategyDomainSourceReviewDecayFloorReport(
        generated_at=generated_at_utc,
        config_version=active_config.config_version,
        config=active_config,
        review_item_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        review_source_attention_count=_decimal_count(
            _reason_attention_count(
                rows,
                REVIEW_SOURCE_BLOCK_REASON,
                REVIEW_SOURCE_WATCH_REASON,
            ),
        ),
        domain_source_attention_count=_decimal_count(
            _reason_attention_count(
                rows,
                DOMAIN_SOURCE_BLOCK_REASON,
                DOMAIN_SOURCE_WATCH_REASON,
            ),
        ),
        freshness_decay_attention_count=_decimal_count(
            _reason_attention_count(
                rows,
                FRESHNESS_DECAY_BLOCK_REASON,
                FRESHNESS_DECAY_WATCH_REASON,
            ),
        ),
        review_quality_attention_count=_decimal_count(
            _reason_attention_count(
                rows,
                REVIEW_QUALITY_BLOCK_REASON,
                REVIEW_QUALITY_WATCH_REASON,
            ),
        ),
        source_authority_attention_count=_decimal_count(
            _reason_attention_count(
                rows,
                SOURCE_AUTHORITY_BLOCK_REASON,
                SOURCE_AUTHORITY_WATCH_REASON,
            ),
        ),
        contradiction_pressure_attention_count=_decimal_count(
            _reason_attention_count(
                rows,
                CONTRADICTION_PRESSURE_BLOCK_REASON,
                CONTRADICTION_PRESSURE_WATCH_REASON,
            ),
        ),
        decay_floor_attention_count=_decimal_count(
            _reason_attention_count(
                rows,
                DECAY_FLOOR_BLOCK_REASON,
                DECAY_FLOOR_WATCH_REASON,
            ),
        ),
        mean_decay_floor_score=_average_probability(
            tuple(row.decay_floor_score for row in rows),
        ),
        lowest_decay_floor_score=min(
            (row.decay_floor_score for row in rows),
            default=ZERO,
        ),
        highest_contradiction_pressure_score=max(
            (row.contradiction_pressure_score for row in rows),
            default=ZERO,
        ),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_domain_source_review_decay_floor_report_payload(
    report: ResearchStrategyDomainSourceReviewDecayFloorReport,
) -> "FrozenJsonObject":
    if type(report) is not ResearchStrategyDomainSourceReviewDecayFloorReport:
        raise ValueError(
            "report must be ResearchStrategyDomainSourceReviewDecayFloorReport",
        )
    validate_research_strategy_domain_source_review_decay_floor_report_digest(report)
    payload = _report_public_payload(report)
    validate_research_strategy_domain_source_review_decay_floor_public_payload(payload)
    return _freeze_json_object(payload)


def research_strategy_domain_source_review_decay_floor_report_digest(
    report: ResearchStrategyDomainSourceReviewDecayFloorReport,
) -> str:
    validate_research_strategy_domain_source_review_decay_floor_report_digest(report)
    return report.public_digest


def validate_research_strategy_domain_source_review_decay_floor_report_digest(
    report: ResearchStrategyDomainSourceReviewDecayFloorReport,
) -> None:
    if type(report) is not ResearchStrategyDomainSourceReviewDecayFloorReport:
        raise ValueError(
            "report must be ResearchStrategyDomainSourceReviewDecayFloorReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    _report_from_public_payload(_report_public_payload(report))


def validate_research_strategy_domain_source_review_decay_floor_public_payload(
    payload: object,
) -> None:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    public_digest = payload.get("public_digest")
    _require_sha256_digest("public_digest", public_digest)
    unsigned = dict(payload)
    unsigned.pop("public_digest", None)
    if public_digest != _digest_unsigned_payload(unsigned):
        raise ValueError("public_digest must match payload")
    _report_from_public_payload(payload)
    json.dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def _report_from_public_payload(
    payload: object,
) -> ResearchStrategyDomainSourceReviewDecayFloorReport:
    value = _require_exact_payload_schema(
        "report payload",
        payload,
        tuple(field.name for field in fields(ResearchStrategyDomainSourceReviewDecayFloorReport)),
    )
    config = _config_from_public_payload(value["config"])
    rows = tuple(
        _row_from_public_payload(item)
        for item in _require_json_array("rows", value["rows"])
    )
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(item)
        for item in _require_json_array(
            "reason_code_counts",
            value["reason_code_counts"],
        )
    )
    return ResearchStrategyDomainSourceReviewDecayFloorReport(
        generated_at=_parse_public_datetime("generated_at", value["generated_at"]),
        config_version=_parse_public_string("config_version", value["config_version"]),
        config=config,
        review_item_count=_parse_public_decimal(
            "review_item_count",
            value["review_item_count"],
        ),
        pass_count=_parse_public_decimal("pass_count", value["pass_count"]),
        watch_count=_parse_public_decimal("watch_count", value["watch_count"]),
        block_count=_parse_public_decimal("block_count", value["block_count"]),
        review_source_attention_count=_parse_public_decimal(
            "review_source_attention_count",
            value["review_source_attention_count"],
        ),
        domain_source_attention_count=_parse_public_decimal(
            "domain_source_attention_count",
            value["domain_source_attention_count"],
        ),
        freshness_decay_attention_count=_parse_public_decimal(
            "freshness_decay_attention_count",
            value["freshness_decay_attention_count"],
        ),
        review_quality_attention_count=_parse_public_decimal(
            "review_quality_attention_count",
            value["review_quality_attention_count"],
        ),
        source_authority_attention_count=_parse_public_decimal(
            "source_authority_attention_count",
            value["source_authority_attention_count"],
        ),
        contradiction_pressure_attention_count=_parse_public_decimal(
            "contradiction_pressure_attention_count",
            value["contradiction_pressure_attention_count"],
        ),
        decay_floor_attention_count=_parse_public_decimal(
            "decay_floor_attention_count",
            value["decay_floor_attention_count"],
        ),
        mean_decay_floor_score=_parse_public_decimal(
            "mean_decay_floor_score",
            value["mean_decay_floor_score"],
        ),
        lowest_decay_floor_score=_parse_public_decimal(
            "lowest_decay_floor_score",
            value["lowest_decay_floor_score"],
        ),
        highest_contradiction_pressure_score=_parse_public_decimal(
            "highest_contradiction_pressure_score",
            value["highest_contradiction_pressure_score"],
        ),
        status=_parse_public_string("status", value["status"]),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_parse_public_string_array(
            "reason_codes",
            value["reason_codes"],
        ),
        public_digest=_parse_public_digest("public_digest", value["public_digest"]),
        paper_only=_parse_required_true("paper_only", value["paper_only"]),
        report_only=_parse_required_true("report_only", value["report_only"]),
        readonly=_parse_required_true("readonly", value["readonly"]),
    )


def _config_from_public_payload(
    payload: object,
) -> ResearchStrategyDomainSourceReviewDecayFloorConfig:
    value = _require_exact_payload_schema(
        "config payload",
        payload,
        tuple(field.name for field in fields(ResearchStrategyDomainSourceReviewDecayFloorConfig)),
    )
    return ResearchStrategyDomainSourceReviewDecayFloorConfig(
        config_version=_parse_public_string("config_version", value["config_version"]),
        min_review_source_count_pass=_parse_public_decimal(
            "min_review_source_count_pass",
            value["min_review_source_count_pass"],
        ),
        min_review_source_count_watch=_parse_public_decimal(
            "min_review_source_count_watch",
            value["min_review_source_count_watch"],
        ),
        min_domain_source_count_pass=_parse_public_decimal(
            "min_domain_source_count_pass",
            value["min_domain_source_count_pass"],
        ),
        min_domain_source_count_watch=_parse_public_decimal(
            "min_domain_source_count_watch",
            value["min_domain_source_count_watch"],
        ),
        max_latest_source_review_age_seconds_pass=_parse_public_decimal(
            "max_latest_source_review_age_seconds_pass",
            value["max_latest_source_review_age_seconds_pass"],
        ),
        max_latest_source_review_age_seconds_watch=_parse_public_decimal(
            "max_latest_source_review_age_seconds_watch",
            value["max_latest_source_review_age_seconds_watch"],
        ),
        review_quality_score_pass_floor=_parse_public_decimal(
            "review_quality_score_pass_floor",
            value["review_quality_score_pass_floor"],
        ),
        review_quality_score_watch_floor=_parse_public_decimal(
            "review_quality_score_watch_floor",
            value["review_quality_score_watch_floor"],
        ),
        source_authority_score_pass_floor=_parse_public_decimal(
            "source_authority_score_pass_floor",
            value["source_authority_score_pass_floor"],
        ),
        source_authority_score_watch_floor=_parse_public_decimal(
            "source_authority_score_watch_floor",
            value["source_authority_score_watch_floor"],
        ),
        contradiction_pressure_watch_ceiling=_parse_public_decimal(
            "contradiction_pressure_watch_ceiling",
            value["contradiction_pressure_watch_ceiling"],
        ),
        contradiction_pressure_block_ceiling=_parse_public_decimal(
            "contradiction_pressure_block_ceiling",
            value["contradiction_pressure_block_ceiling"],
        ),
        decay_floor_score_pass_floor=_parse_public_decimal(
            "decay_floor_score_pass_floor",
            value["decay_floor_score_pass_floor"],
        ),
        decay_floor_score_watch_floor=_parse_public_decimal(
            "decay_floor_score_watch_floor",
            value["decay_floor_score_watch_floor"],
        ),
        paper_only=_parse_required_true("paper_only", value["paper_only"]),
        report_only=_parse_required_true("report_only", value["report_only"]),
        readonly=_parse_required_true("readonly", value["readonly"]),
    )


def _row_from_public_payload(
    payload: object,
) -> ResearchStrategyDomainSourceReviewDecayFloorRow:
    value = _require_exact_payload_schema(
        "row payload",
        payload,
        tuple(field.name for field in fields(ResearchStrategyDomainSourceReviewDecayFloorRow)),
    )
    return ResearchStrategyDomainSourceReviewDecayFloorRow(
        aggregate_row_number=_parse_public_decimal(
            "aggregate_row_number",
            value["aggregate_row_number"],
        ),
        source_review_digest=_parse_public_digest(
            "source_review_digest",
            value["source_review_digest"],
        ),
        domain_review_digest=_parse_public_digest(
            "domain_review_digest",
            value["domain_review_digest"],
        ),
        review_source_count=_parse_public_decimal(
            "review_source_count",
            value["review_source_count"],
        ),
        domain_source_count=_parse_public_decimal(
            "domain_source_count",
            value["domain_source_count"],
        ),
        latest_source_review_age_seconds=_parse_public_decimal(
            "latest_source_review_age_seconds",
            value["latest_source_review_age_seconds"],
        ),
        freshness_decay_score=_parse_public_decimal(
            "freshness_decay_score",
            value["freshness_decay_score"],
        ),
        review_quality_score=_parse_public_decimal(
            "review_quality_score",
            value["review_quality_score"],
        ),
        source_authority_score=_parse_public_decimal(
            "source_authority_score",
            value["source_authority_score"],
        ),
        contradiction_pressure_score=_parse_public_decimal(
            "contradiction_pressure_score",
            value["contradiction_pressure_score"],
        ),
        decay_floor_score=_parse_public_decimal(
            "decay_floor_score",
            value["decay_floor_score"],
        ),
        status=_parse_public_string("status", value["status"]),
        reason_codes=_parse_public_string_array(
            "reason_codes",
            value["reason_codes"],
        ),
        paper_only=_parse_required_true("paper_only", value["paper_only"]),
        report_only=_parse_required_true("report_only", value["report_only"]),
        readonly=_parse_required_true("readonly", value["readonly"]),
    )


def _reason_code_count_from_public_payload(
    payload: object,
) -> ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount:
    value = _require_exact_payload_schema(
        "reason code count payload",
        payload,
        tuple(
            field.name
            for field in fields(
                ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount,
            )
        ),
    )
    return ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount(
        reason_code=_parse_public_string("reason_code", value["reason_code"]),
        count=_parse_public_decimal("count", value["count"]),
        paper_only=_parse_required_true("paper_only", value["paper_only"]),
        report_only=_parse_required_true("report_only", value["report_only"]),
        readonly=_parse_required_true("readonly", value["readonly"]),
    )


def _require_exact_payload_schema(
    label: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    if any(type(key) is not str for key in value):
        raise ValueError(f"{label} must have exact schema")
    if set(value) != set(expected_fields):
        raise ValueError(f"{label} must have exact schema")
    return value


def _require_json_array(field_name: str, value: object) -> tuple[Any, ...]:
    if not isinstance(value, (list, FrozenJsonArray)):
        raise ValueError(f"{field_name} must be a JSON array")
    return tuple(value)


def _parse_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _parse_public_string_array(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    return tuple(
        _parse_public_string(field_name, item)
        for item in _require_json_array(field_name, value)
    )


def _parse_public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    normalized = _normalize_decimal(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical six-place Decimal string")
    return normalized


def _parse_public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _parse_public_digest(field_name: str, value: object) -> str:
    _require_sha256_digest(field_name, value)
    return value


def _parse_required_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _validated_config_copy(
    value: object,
) -> ResearchStrategyDomainSourceReviewDecayFloorConfig:
    _require_exact_type(
        value,
        ResearchStrategyDomainSourceReviewDecayFloorConfig,
        "config",
    )
    return ResearchStrategyDomainSourceReviewDecayFloorConfig(
        **{
            field.name: getattr(value, field.name)
            for field in fields(ResearchStrategyDomainSourceReviewDecayFloorConfig)
        },
    )


def _normalize_input_rows(
    source_review_rows: Iterable[object],
) -> tuple[ResearchStrategyDomainSourceReviewDecayFloorInput, ...]:
    if isinstance(source_review_rows, (str, bytes)):
        raise ValueError("source_review_rows must be an iterable")
    try:
        values = tuple(source_review_rows)
    except TypeError as exc:
        raise ValueError("source_review_rows must be an iterable") from exc
    normalized: list[ResearchStrategyDomainSourceReviewDecayFloorInput] = []
    for value in values:
        if type(value) is not ResearchStrategyDomainSourceReviewDecayFloorInput:
            raise ValueError(
                "source_review_rows must contain "
                "ResearchStrategyDomainSourceReviewDecayFloorInput values",
            )
        value = ResearchStrategyDomainSourceReviewDecayFloorInput(
            **{field.name: getattr(value, field.name) for field in fields(value)},
        )
        _require_hard_flags("input", value)
        normalized.append(value)
    return tuple(normalized)


def _build_rows(
    inputs: tuple[ResearchStrategyDomainSourceReviewDecayFloorInput, ...],
    *,
    config: ResearchStrategyDomainSourceReviewDecayFloorConfig,
) -> tuple[ResearchStrategyDomainSourceReviewDecayFloorRow, ...]:
    preliminary = tuple(_preliminary_row(item, config=config) for item in inputs)
    seen_keys: set[tuple[str, str]] = set()
    for row in preliminary:
        key = (row["source_review_digest"], row["domain_review_digest"])
        if key in seen_keys:
            raise ValueError("source_review_digest and domain_review_digest must be unique")
        seen_keys.add(key)
    sorted_rows = sorted(
        preliminary,
        key=lambda row: (
            STATUS_SORT_RANK[str(row["status"])],
            str(row["source_review_digest"]),
            str(row["domain_review_digest"]),
        ),
    )
    return tuple(
        ResearchStrategyDomainSourceReviewDecayFloorRow(
            aggregate_row_number=_decimal_count(index),
            source_review_digest=str(row["source_review_digest"]),
            domain_review_digest=str(row["domain_review_digest"]),
            review_source_count=_as_decimal(row["review_source_count"]),
            domain_source_count=_as_decimal(row["domain_source_count"]),
            latest_source_review_age_seconds=_as_decimal(
                row["latest_source_review_age_seconds"],
            ),
            freshness_decay_score=_as_decimal(row["freshness_decay_score"]),
            review_quality_score=_as_decimal(row["review_quality_score"]),
            source_authority_score=_as_decimal(row["source_authority_score"]),
            contradiction_pressure_score=_as_decimal(
                row["contradiction_pressure_score"],
            ),
            decay_floor_score=_as_decimal(row["decay_floor_score"]),
            status=str(row["status"]),
            reason_codes=_as_reason_codes(row["reason_codes"]),
        )
        for index, row in enumerate(sorted_rows, start=1)
    )


def _preliminary_row(
    item: ResearchStrategyDomainSourceReviewDecayFloorInput,
    *,
    config: ResearchStrategyDomainSourceReviewDecayFloorConfig,
) -> dict[str, object]:
    freshness_decay_score = _freshness_decay_score(
        item.latest_source_review_age_seconds,
        max_latest_source_review_age_seconds_watch=(
            config.max_latest_source_review_age_seconds_watch
        ),
    )
    decay_floor_score = _average_probability(
        (
            _count_floor_score(
                item.review_source_count,
                config.min_review_source_count_pass,
            ),
            _count_floor_score(
                item.domain_source_count,
                config.min_domain_source_count_pass,
            ),
            freshness_decay_score,
            item.review_quality_score,
            item.source_authority_score,
            _quantize(ONE - item.contradiction_pressure_score),
        ),
    )
    reason_codes = _row_reason_codes(
        item,
        freshness_decay_score=freshness_decay_score,
        decay_floor_score=decay_floor_score,
        config=config,
    )
    status = _row_status(reason_codes)
    return {
        "source_review_digest": _digest_text(item.source_review_key),
        "domain_review_digest": _digest_text(item.domain_review_key),
        "review_source_count": item.review_source_count,
        "domain_source_count": item.domain_source_count,
        "latest_source_review_age_seconds": item.latest_source_review_age_seconds,
        "freshness_decay_score": freshness_decay_score,
        "review_quality_score": item.review_quality_score,
        "source_authority_score": item.source_authority_score,
        "contradiction_pressure_score": item.contradiction_pressure_score,
        "decay_floor_score": decay_floor_score,
        "status": status,
        "reason_codes": reason_codes,
    }


def _row_reason_codes(
    item: ResearchStrategyDomainSourceReviewDecayFloorInput,
    *,
    freshness_decay_score: Decimal,
    decay_floor_score: Decimal,
    config: ResearchStrategyDomainSourceReviewDecayFloorConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_floor_reason(
        reason_codes,
        value=item.review_source_count,
        pass_floor=config.min_review_source_count_pass,
        watch_floor=config.min_review_source_count_watch,
        block_reason=REVIEW_SOURCE_BLOCK_REASON,
        watch_reason=REVIEW_SOURCE_WATCH_REASON,
    )
    _append_floor_reason(
        reason_codes,
        value=item.domain_source_count,
        pass_floor=config.min_domain_source_count_pass,
        watch_floor=config.min_domain_source_count_watch,
        block_reason=DOMAIN_SOURCE_BLOCK_REASON,
        watch_reason=DOMAIN_SOURCE_WATCH_REASON,
    )
    if (
        item.latest_source_review_age_seconds
        > config.max_latest_source_review_age_seconds_watch
    ):
        reason_codes.append(FRESHNESS_DECAY_BLOCK_REASON)
    elif (
        item.latest_source_review_age_seconds
        > config.max_latest_source_review_age_seconds_pass
    ):
        reason_codes.append(FRESHNESS_DECAY_WATCH_REASON)
    _append_floor_reason(
        reason_codes,
        value=item.review_quality_score,
        pass_floor=config.review_quality_score_pass_floor,
        watch_floor=config.review_quality_score_watch_floor,
        block_reason=REVIEW_QUALITY_BLOCK_REASON,
        watch_reason=REVIEW_QUALITY_WATCH_REASON,
    )
    _append_floor_reason(
        reason_codes,
        value=item.source_authority_score,
        pass_floor=config.source_authority_score_pass_floor,
        watch_floor=config.source_authority_score_watch_floor,
        block_reason=SOURCE_AUTHORITY_BLOCK_REASON,
        watch_reason=SOURCE_AUTHORITY_WATCH_REASON,
    )
    if item.contradiction_pressure_score > config.contradiction_pressure_block_ceiling:
        reason_codes.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif item.contradiction_pressure_score > config.contradiction_pressure_watch_ceiling:
        reason_codes.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    _append_floor_reason(
        reason_codes,
        value=decay_floor_score,
        pass_floor=config.decay_floor_score_pass_floor,
        watch_floor=config.decay_floor_score_watch_floor,
        block_reason=DECAY_FLOOR_BLOCK_REASON,
        watch_reason=DECAY_FLOOR_WATCH_REASON,
    )
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    _normalize_probability_decimal("freshness_decay_score", freshness_decay_score)
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _append_floor_reason(
    reason_codes: list[str],
    *,
    value: Decimal,
    pass_floor: Decimal,
    watch_floor: Decimal,
    block_reason: str,
    watch_reason: str,
) -> None:
    if value < watch_floor:
        reason_codes.append(block_reason)
    elif value < pass_floor:
        reason_codes.append(watch_reason)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategyDomainSourceReviewDecayFloorRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainSourceReviewDecayFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    codes = {reason_code for row in rows for reason_code in row.reason_codes}
    if codes == {CLEAR_REASON}:
        return (CLEAR_REASON,)
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in codes)


def _reason_code_counts(
    rows: tuple[ResearchStrategyDomainSourceReviewDecayFloorRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _reason_attention_count(
    rows: tuple[ResearchStrategyDomainSourceReviewDecayFloorRow, ...],
    block_reason: str,
    watch_reason: str,
) -> int:
    return sum(
        1
        for row in rows
        if block_reason in row.reason_codes or watch_reason in row.reason_codes
    )


def _status_count(
    rows: tuple[ResearchStrategyDomainSourceReviewDecayFloorRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _freshness_decay_score(
    latest_source_review_age_seconds: Decimal,
    *,
    max_latest_source_review_age_seconds_watch: Decimal,
) -> Decimal:
    if latest_source_review_age_seconds >= max_latest_source_review_age_seconds_watch:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            ONE
            - (
                latest_source_review_age_seconds
                / max_latest_source_review_age_seconds_watch
            ),
        )


def _count_floor_score(value: Decimal, pass_floor: Decimal) -> Decimal:
    if pass_floor <= ZERO:
        raise ValueError("pass_floor must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(min(ONE, value / pass_floor))


def _average_probability(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _validate_row_consistency(
    row: ResearchStrategyDomainSourceReviewDecayFloorRow,
    *,
    config: ResearchStrategyDomainSourceReviewDecayFloorConfig,
) -> None:
    expected = _preliminary_row(
        ResearchStrategyDomainSourceReviewDecayFloorInput(
            source_review_key="redacted-source-review",
            domain_review_key="redacted-domain-review",
            review_source_count=row.review_source_count,
            domain_source_count=row.domain_source_count,
            latest_source_review_age_seconds=row.latest_source_review_age_seconds,
            review_quality_score=row.review_quality_score,
            source_authority_score=row.source_authority_score,
            contradiction_pressure_score=row.contradiction_pressure_score,
        ),
        config=config,
    )
    for field_name in (
        "freshness_decay_score",
        "decay_floor_score",
        "status",
        "reason_codes",
    ):
        if getattr(row, field_name) != expected[field_name]:
            raise ValueError(f"{field_name} must match row inputs and config")


def _validate_report_consistency(
    report: ResearchStrategyDomainSourceReviewDecayFloorReport,
) -> None:
    rows = report.rows
    if report.config_version != report.config.config_version:
        raise ValueError("config_version must match config")
    for row in rows:
        _validate_row_consistency(row, config=report.config)
    if report.review_item_count != _decimal_count(len(rows)):
        raise ValueError("review_item_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.review_source_attention_count != _decimal_count(
        _reason_attention_count(
            rows,
            REVIEW_SOURCE_BLOCK_REASON,
            REVIEW_SOURCE_WATCH_REASON,
        ),
    ):
        raise ValueError("review_source_attention_count must match rows")
    if report.domain_source_attention_count != _decimal_count(
        _reason_attention_count(
            rows,
            DOMAIN_SOURCE_BLOCK_REASON,
            DOMAIN_SOURCE_WATCH_REASON,
        ),
    ):
        raise ValueError("domain_source_attention_count must match rows")
    if report.freshness_decay_attention_count != _decimal_count(
        _reason_attention_count(
            rows,
            FRESHNESS_DECAY_BLOCK_REASON,
            FRESHNESS_DECAY_WATCH_REASON,
        ),
    ):
        raise ValueError("freshness_decay_attention_count must match rows")
    if report.review_quality_attention_count != _decimal_count(
        _reason_attention_count(
            rows,
            REVIEW_QUALITY_BLOCK_REASON,
            REVIEW_QUALITY_WATCH_REASON,
        ),
    ):
        raise ValueError("review_quality_attention_count must match rows")
    if report.source_authority_attention_count != _decimal_count(
        _reason_attention_count(
            rows,
            SOURCE_AUTHORITY_BLOCK_REASON,
            SOURCE_AUTHORITY_WATCH_REASON,
        ),
    ):
        raise ValueError("source_authority_attention_count must match rows")
    if report.contradiction_pressure_attention_count != _decimal_count(
        _reason_attention_count(
            rows,
            CONTRADICTION_PRESSURE_BLOCK_REASON,
            CONTRADICTION_PRESSURE_WATCH_REASON,
        ),
    ):
        raise ValueError("contradiction_pressure_attention_count must match rows")
    if report.decay_floor_attention_count != _decimal_count(
        _reason_attention_count(
            rows,
            DECAY_FLOOR_BLOCK_REASON,
            DECAY_FLOOR_WATCH_REASON,
        ),
    ):
        raise ValueError("decay_floor_attention_count must match rows")
    if report.mean_decay_floor_score != _average_probability(
        tuple(row.decay_floor_score for row in rows),
    ):
        raise ValueError("mean_decay_floor_score must match rows")
    if report.lowest_decay_floor_score != min(
        (row.decay_floor_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("lowest_decay_floor_score must match rows")
    if report.highest_contradiction_pressure_score != max(
        (row.contradiction_pressure_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("highest_contradiction_pressure_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: tuple[ResearchStrategyDomainSourceReviewDecayFloorRow, ...],
) -> tuple[ResearchStrategyDomainSourceReviewDecayFloorRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized_rows: list[ResearchStrategyDomainSourceReviewDecayFloorRow] = []
    for row in rows:
        if type(row) is not ResearchStrategyDomainSourceReviewDecayFloorRow:
            raise ValueError(
                "rows must contain ResearchStrategyDomainSourceReviewDecayFloorRow",
            )
        normalized_rows.append(
            ResearchStrategyDomainSourceReviewDecayFloorRow(
                **{field.name: getattr(row, field.name) for field in fields(row)}
            ),
        )
    rows = tuple(normalized_rows)
    previous_number = ZERO
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_SORT_RANK[row.status],
                row.source_review_digest,
                row.domain_review_digest,
            ),
        ),
    )
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        _require_hard_flags("row", row)
        if row.aggregate_row_number != previous_number + ONE:
            raise ValueError("aggregate_row_number must be sequential")
        previous_number = row.aggregate_row_number
        key = (row.source_review_digest, row.domain_review_digest)
        if key in seen_keys:
            raise ValueError("rows must have unique source and domain review digests")
        seen_keys.add(key)
    return rows


def _normalize_reason_code_counts(
    values: tuple[
        ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount,
        ...,
    ],
) -> tuple[ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized_values: list[
        ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount
    ] = []
    seen_reason_codes: set[str] = set()
    for value in values:
        if (
            type(value)
            is not ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount",
            )
        normalized_value = ResearchStrategyDomainSourceReviewDecayFloorReasonCodeCount(
            **{field.name: getattr(value, field.name) for field in fields(value)}
        )
        if normalized_value.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen_reason_codes.add(normalized_value.reason_code)
        normalized_values.append(normalized_value)
    values = tuple(normalized_values)
    sorted_values = tuple(
        sorted(
            values,
            key=lambda value: REASON_CODE_SEQUENCE.index(value.reason_code),
        ),
    )
    if values != sorted_values:
        raise ValueError("reason_code_counts must be sorted")
    for value in values:
        _require_hard_flags("reason_code_count", value)
    return values


def _report_public_payload(
    report: ResearchStrategyDomainSourceReviewDecayFloorReport,
) -> dict[str, Any]:
    payload = _report_unsigned_payload(report)
    payload["public_digest"] = report.public_digest
    return payload


def _report_unsigned_payload(
    report: ResearchStrategyDomainSourceReviewDecayFloorReport,
) -> dict[str, Any]:
    return {
        field.name: _json_ready(getattr(report, field.name))
        for field in fields(report)
        if field.name != "public_digest"
    }


def _digest_unsigned_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    def visit(path: str, item: object) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                key_text = str(key)
                _reject_unsafe_text(f"{path}.{key_text}", key_text)
                visit(f"{path}.{key_text}", child)
            return
        if is_dataclass(item) and not isinstance(item, type):
            for field in fields(item):
                key_text = field.name
                _reject_unsafe_text(f"{path}.{key_text}", key_text)
                visit(f"{path}.{key_text}", getattr(item, field.name))
            return
        if isinstance(item, (list, tuple)):
            for index, child in enumerate(item):
                visit(f"{path}[{index}]", child)
            return
        if isinstance(item, str):
            _reject_unsafe_text(path, item)

    visit(label, value)


def _reject_unsafe_text(path: str, value: str) -> None:
    lowered = value.lower()
    compact = lowered.replace(" ", "").replace("-", "").replace("_", "")
    for unsafe in _UNSAFE_TEXT_PARTS:
        unsafe_lowered = unsafe.lower()
        unsafe_compact = unsafe_lowered.replace(" ", "").replace("-", "").replace("_", "")
        if unsafe_lowered in lowered or unsafe_compact in compact:
            raise ValueError(f"{path} contains unsafe public payload text")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _field_value(value: object, field_name: str) -> object:
    if isinstance(value, dict):
        if field_name not in value:
            raise ValueError(f"{field_name} is required")
        return value[field_name]
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    raise ValueError(f"{field_name} is required")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or any(character in value for character in "\n\r\t")
    ):
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_DOMAIN_SOURCE_REVIEW_DECAY_FLOOR_REPORT_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SET:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_reason_codes(
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values and not allow_empty:
        raise ValueError("reason_codes must be nonempty")
    seen_reason_codes: set[str] = set()
    for value in values:
        _require_reason_code("reason_codes", value)
        if value in seen_reason_codes:
            raise ValueError("reason_codes must contain unique values")
        seen_reason_codes.add(value)
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in seen_reason_codes
    )


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    normalized = _quantize(raw)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw)


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize(raw)


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize(raw)


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO or raw > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(raw)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _quantize(_require_raw_decimal(field_name, value))


def _require_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT) as context:
        try:
            normalized = value.quantize(QUANTUM, context=context)
        except InvalidOperation as exc:
            raise ValueError("Decimal value must be finite and quantizable") from exc
    if normalized.is_zero() and normalized.is_signed():
        return ZERO
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return _quantize(Decimal(value))


def _require_at_least(field_name: str, value: Decimal, floor: Decimal) -> None:
    if value < floor:
        raise ValueError(f"{field_name} pass threshold must be at least watch threshold")


def _digest_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _as_decimal(value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be an exact Decimal")
    return value


def _as_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    return value
