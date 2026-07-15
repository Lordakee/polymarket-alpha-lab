"""Report-only Scrapling authority latency floor reducer.

The caller supplies already-collected observations. This module is pure,
read-only reporting logic: no database, network, wallet, order, authentication,
trade execution, sizing, or recommendation behavior is exposed.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, final


DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_LATENCY_FLOOR_REPORT_CONFIG_VERSION = (
    "research-source-scrapling-authority-latency-floor-report-v0"
)
RESEARCH_SOURCE_SCRAPLING_AUTHORITY_LATENCY_FLOOR_STATUSES = (
    "pass",
    "watch",
    "block",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECOND_DIVISOR = Decimal("1000000")
FLOOR_SCORE_STABILITY_BONUS = Decimal("0.024283")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

NO_INPUTS_REASON = "scrapling_authority_latency_floor_no_inputs"
PASS_REASON = "scrapling_authority_latency_floor_pass"
FLOOR_BELOW_PASS_REASON = "authority_latency_floor_score_below_pass_threshold"
FLOOR_BELOW_WATCH_REASON = "authority_latency_floor_score_below_watch_threshold"
SCRAPLING_ABOVE_PASS_REASON = "scrapling_latency_above_pass_threshold"
SCRAPLING_ABOVE_WATCH_REASON = "scrapling_latency_above_watch_threshold"
AUTHORITY_ABOVE_PASS_REASON = "authority_latency_above_pass_threshold"
AUTHORITY_ABOVE_WATCH_REASON = "authority_latency_above_watch_threshold"
GAP_ABOVE_WATCH_REASON = "latency_gap_above_watch_threshold"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    FLOOR_BELOW_WATCH_REASON,
    SCRAPLING_ABOVE_WATCH_REASON,
    AUTHORITY_ABOVE_WATCH_REASON,
    GAP_ABOVE_WATCH_REASON,
    FLOOR_BELOW_PASS_REASON,
    SCRAPLING_ABOVE_PASS_REASON,
    AUTHORITY_ABOVE_PASS_REASON,
    PASS_REASON,
)
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "candidate id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "slug",
    "question",
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
    "order",
    "trade",
    "live",
    "sizing",
    "recommend",
)
UNSAFE_PUBLIC_KEYS = tuple(
    "".join(character for character in fragment.casefold() if character.isalnum())
    for fragment in UNSAFE_PUBLIC_FRAGMENTS
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_LATENCY_FLOOR_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_SCRAPLING_AUTHORITY_LATENCY_FLOOR_STATUSES",
    "ResearchSourceScraplingAuthorityLatencyFloorConfig",
    "ResearchSourceScraplingAuthorityLatencyFloorInput",
    "ResearchSourceScraplingAuthorityLatencyFloorObservation",
    "ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount",
    "ResearchSourceScraplingAuthorityLatencyFloorReport",
    "ResearchSourceScraplingAuthorityLatencyFloorRow",
    "build_research_source_scrapling_authority_latency_floor_report",
    "research_source_scrapling_authority_latency_floor_report_digest",
    "research_source_scrapling_authority_latency_floor_report_payload",
    "validate_research_source_scrapling_authority_latency_floor_report_payload",
)


@final
@dataclass(frozen=True)
class ResearchSourceScraplingAuthorityLatencyFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_LATENCY_FLOOR_REPORT_CONFIG_VERSION
    )
    scrapling_latency_pass_threshold_seconds: Decimal = Decimal("1200.000000")
    scrapling_latency_watch_threshold_seconds: Decimal = Decimal("3600.000000")
    authority_latency_pass_threshold_seconds: Decimal = Decimal("1800.000000")
    authority_latency_watch_threshold_seconds: Decimal = Decimal("7200.000000")
    latency_gap_watch_threshold_seconds: Decimal = Decimal("3000.000000")
    authority_latency_floor_pass_score: Decimal = Decimal("0.900000")
    authority_latency_floor_watch_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAuthorityLatencyFloorConfig:
            raise TypeError(
                "ResearchSourceScraplingAuthorityLatencyFloorConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraplingAuthorityLatencyFloorConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_LATENCY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "scrapling_latency_pass_threshold_seconds",
            "scrapling_latency_watch_threshold_seconds",
            "authority_latency_pass_threshold_seconds",
            "authority_latency_watch_threshold_seconds",
            "latency_gap_watch_threshold_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.scrapling_latency_pass_threshold_seconds
            >= self.scrapling_latency_watch_threshold_seconds
        ):
            raise ValueError("scrapling latency pass threshold must be below watch")
        if (
            self.authority_latency_pass_threshold_seconds
            >= self.authority_latency_watch_threshold_seconds
        ):
            raise ValueError("authority latency pass threshold must be below watch")
        for field_name in (
            "authority_latency_floor_pass_score",
            "authority_latency_floor_watch_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.authority_latency_floor_watch_score > self.authority_latency_floor_pass_score:
            raise ValueError("floor watch score must not exceed floor pass score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload(self)


@final
@dataclass(frozen=True)
class ResearchSourceScraplingAuthorityLatencyFloorObservation:
    private_latency_ref: str
    observed_at: datetime
    scrapling_latency_seconds: Decimal
    authority_latency_seconds: Decimal
    scrapling_freshness_score: Decimal
    authority_freshness_score: Decimal
    authority_recheck_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAuthorityLatencyFloorObservation:
            raise TypeError(
                "ResearchSourceScraplingAuthorityLatencyFloorObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingAuthorityLatencyFloorObservation,
            "observation",
        )
        _require_private_string("private_latency_ref", self.private_latency_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "scrapling_latency_seconds",
            "authority_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "scrapling_freshness_score",
            "authority_freshness_score",
            "authority_recheck_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@final
@dataclass(frozen=True)
class ResearchSourceScraplingAuthorityLatencyFloorRow:
    row_index: Decimal
    observed_at: datetime
    observed_age_seconds: Decimal
    scrapling_latency_seconds: Decimal
    authority_latency_seconds: Decimal
    latency_gap_seconds: Decimal
    scrapling_freshness_score: Decimal
    authority_freshness_score: Decimal
    authority_recheck_confidence_score: Decimal
    authority_latency_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAuthorityLatencyFloorRow:
            raise TypeError(
                "ResearchSourceScraplingAuthorityLatencyFloorRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraplingAuthorityLatencyFloorRow, "row")
        object.__setattr__(
            self,
            "row_index",
            _require_positive_whole_decimal("row_index", self.row_index),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "observed_age_seconds",
            "scrapling_latency_seconds",
            "authority_latency_seconds",
            "latency_gap_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "scrapling_freshness_score",
            "authority_freshness_score",
            "authority_recheck_confidence_score",
            "authority_latency_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _reject_unsafe_public_payload(self)


@final
@dataclass(frozen=True)
class ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount:
            raise TypeError(
                "ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_nonnegative_whole_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload(self)


@final
@dataclass(frozen=True)
class ResearchSourceScraplingAuthorityLatencyFloorReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_scrapling_latency_seconds: Decimal
    average_authority_latency_seconds: Decimal
    highest_latency_gap_seconds: Decimal
    average_authority_latency_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchSourceScraplingAuthorityLatencyFloorRow, ...]
    config: ResearchSourceScraplingAuthorityLatencyFloorConfig = field(
        default_factory=ResearchSourceScraplingAuthorityLatencyFloorConfig,
    )
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAuthorityLatencyFloorReport:
            raise TypeError(
                "ResearchSourceScraplingAuthorityLatencyFloorReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraplingAuthorityLatencyFloorReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_exact_type(
            self.config,
            ResearchSourceScraplingAuthorityLatencyFloorConfig,
            "config",
        )
        self.config.__post_init__()
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_LATENCY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in (
            "observation_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_scrapling_latency_seconds",
            "average_authority_latency_seconds",
            "highest_latency_gap_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_authority_latency_floor_score",
            _require_ratio_decimal(
                "average_authority_latency_floor_score",
                self.average_authority_latency_floor_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_scrapling_authority_latency_floor_report_payload(self)


REPORT_PAYLOAD_KEY_ORDER = tuple(
    dataclass_field.name
    for dataclass_field in fields(ResearchSourceScraplingAuthorityLatencyFloorReport)
)
ROW_PAYLOAD_KEY_ORDER = tuple(
    dataclass_field.name
    for dataclass_field in fields(ResearchSourceScraplingAuthorityLatencyFloorRow)
)
REASON_CODE_COUNT_PAYLOAD_KEY_ORDER = tuple(
    dataclass_field.name
    for dataclass_field in fields(ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount)
)
CONFIG_PAYLOAD_KEY_ORDER = tuple(
    dataclass_field.name
    for dataclass_field in fields(ResearchSourceScraplingAuthorityLatencyFloorConfig)
)


def build_research_source_scrapling_authority_latency_floor_report(
    observations: Iterable[ResearchSourceScraplingAuthorityLatencyFloorObservation],
    *,
    generated_at: datetime,
    config: ResearchSourceScraplingAuthorityLatencyFloorConfig | None = None,
) -> ResearchSourceScraplingAuthorityLatencyFloorReport:
    if config is None:
        config = ResearchSourceScraplingAuthorityLatencyFloorConfig()
    if type(config) is not ResearchSourceScraplingAuthorityLatencyFloorConfig:
        raise ValueError(
            "config must be exactly ResearchSourceScraplingAuthorityLatencyFloorConfig",
        )
    config.__post_init__()
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        _row_from_observation(
            observation,
            row_index=index,
            config=config,
            generated_at=generated_at,
        )
        for index, observation in enumerate(normalized_observations, start=1)
    )
    pass_count = _count(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count(sum(1 for row in rows if row.status == "watch"))
    block_count = _count(sum(1 for row in rows if row.status == "block"))
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows)
    return ResearchSourceScraplingAuthorityLatencyFloorReport(
        generated_at=generated_at,
        config_version=config.config_version,
        observation_count=_count(len(normalized_observations)),
        row_count=_count(len(rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_scrapling_latency_seconds=_average(
            row.scrapling_latency_seconds for row in rows
        ),
        average_authority_latency_seconds=_average(
            row.authority_latency_seconds for row in rows
        ),
        highest_latency_gap_seconds=max(
            (row.latency_gap_seconds for row in rows),
            default=ZERO,
        ),
        average_authority_latency_floor_score=_average(
            row.authority_latency_floor_score for row in rows
        ),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
        config=config,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_scrapling_authority_latency_floor_report_payload(
    report: ResearchSourceScraplingAuthorityLatencyFloorReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceScraplingAuthorityLatencyFloorReport:
        raise ValueError(
            "report must be exactly ResearchSourceScraplingAuthorityLatencyFloorReport",
        )
    report.__post_init__()
    _validate_report_consistency(report)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def research_source_scrapling_authority_latency_floor_report_digest(
    report: ResearchSourceScraplingAuthorityLatencyFloorReport,
) -> str:
    payload = research_source_scrapling_authority_latency_floor_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_source_scrapling_authority_latency_floor_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        return False
    try:
        _validate_public_payload(payload)
        _validate_public_payload_schema(payload)
        digest = payload.get("derived_validation_digest")
        if type(digest) is not str or not DIGEST_RE.fullmatch(digest):
            return False
        unsigned = dict(payload)
        unsigned.pop("derived_validation_digest")
        encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        if sha256(encoded).hexdigest() != digest:
            return False
        report = _report_from_public_payload(payload)
        return _json_ready(asdict(report)) == payload
    except (InvalidOperation, KeyError, TypeError, ValueError):
        return False


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_exact_payload_keys(
        "report payload",
        payload,
        REPORT_PAYLOAD_KEY_ORDER,
    )
    config_payload = _require_payload_dict("config", payload["config"])
    _require_exact_payload_keys("config", config_payload, CONFIG_PAYLOAD_KEY_ORDER)
    _require_payload_list("reason_codes", payload["reason_codes"])
    rows = _require_payload_list("rows", payload["rows"])
    for index, value in enumerate(rows):
        row_payload = _require_payload_dict(f"rows[{index}]", value)
        _require_exact_payload_keys(
            f"rows[{index}]",
            row_payload,
            ROW_PAYLOAD_KEY_ORDER,
        )
        _require_payload_list(f"rows[{index}].reason_codes", row_payload["reason_codes"])
    reason_code_counts = _require_payload_list(
        "reason_code_counts",
        payload["reason_code_counts"],
    )
    for index, value in enumerate(reason_code_counts):
        count_payload = _require_payload_dict(f"reason_code_counts[{index}]", value)
        _require_exact_payload_keys(
            f"reason_code_counts[{index}]",
            count_payload,
            REASON_CODE_COUNT_PAYLOAD_KEY_ORDER,
        )


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceScraplingAuthorityLatencyFloorReport:
    return ResearchSourceScraplingAuthorityLatencyFloorReport(
        generated_at=_datetime_from_payload("generated_at", payload["generated_at"]),
        config_version=_string_from_payload("config_version", payload["config_version"]),
        observation_count=_decimal_from_payload(
            "observation_count",
            payload["observation_count"],
        ),
        row_count=_decimal_from_payload("row_count", payload["row_count"]),
        pass_count=_decimal_from_payload("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_payload("watch_count", payload["watch_count"]),
        block_count=_decimal_from_payload("block_count", payload["block_count"]),
        average_scrapling_latency_seconds=_decimal_from_payload(
            "average_scrapling_latency_seconds",
            payload["average_scrapling_latency_seconds"],
        ),
        average_authority_latency_seconds=_decimal_from_payload(
            "average_authority_latency_seconds",
            payload["average_authority_latency_seconds"],
        ),
        highest_latency_gap_seconds=_decimal_from_payload(
            "highest_latency_gap_seconds",
            payload["highest_latency_gap_seconds"],
        ),
        average_authority_latency_floor_score=_decimal_from_payload(
            "average_authority_latency_floor_score",
            payload["average_authority_latency_floor_score"],
        ),
        status=_string_from_payload("status", payload["status"]),
        reason_codes=_reason_codes_from_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        reason_code_counts=tuple(
            _reason_code_count_from_public_payload(value)
            for value in _require_payload_list(
                "reason_code_counts",
                payload["reason_code_counts"],
            )
        ),
        rows=tuple(
            _row_from_public_payload(value, config=_config_from_public_payload(payload["config"]))
            for value in _require_payload_list("rows", payload["rows"])
        ),
        config=_config_from_public_payload(payload["config"]),
        derived_validation_digest=_string_from_payload(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(
    value: object,
    *,
    config: ResearchSourceScraplingAuthorityLatencyFloorConfig,
) -> ResearchSourceScraplingAuthorityLatencyFloorRow:
    payload = _require_payload_dict("row payload", value)
    row = ResearchSourceScraplingAuthorityLatencyFloorRow(
        row_index=_decimal_from_payload("row_index", payload["row_index"]),
        observed_at=_datetime_from_payload("observed_at", payload["observed_at"]),
        observed_age_seconds=_decimal_from_payload(
            "observed_age_seconds",
            payload["observed_age_seconds"],
        ),
        scrapling_latency_seconds=_decimal_from_payload(
            "scrapling_latency_seconds",
            payload["scrapling_latency_seconds"],
        ),
        authority_latency_seconds=_decimal_from_payload(
            "authority_latency_seconds",
            payload["authority_latency_seconds"],
        ),
        latency_gap_seconds=_decimal_from_payload(
            "latency_gap_seconds",
            payload["latency_gap_seconds"],
        ),
        scrapling_freshness_score=_decimal_from_payload(
            "scrapling_freshness_score",
            payload["scrapling_freshness_score"],
        ),
        authority_freshness_score=_decimal_from_payload(
            "authority_freshness_score",
            payload["authority_freshness_score"],
        ),
        authority_recheck_confidence_score=_decimal_from_payload(
            "authority_recheck_confidence_score",
            payload["authority_recheck_confidence_score"],
        ),
        authority_latency_floor_score=_decimal_from_payload(
            "authority_latency_floor_score",
            payload["authority_latency_floor_score"],
        ),
        status=_string_from_payload("status", payload["status"]),
        reason_codes=_reason_codes_from_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    _validate_row_consistency(
        row,
        config=config,
    )
    return row


def _config_from_public_payload(
    value: object,
) -> ResearchSourceScraplingAuthorityLatencyFloorConfig:
    payload = _require_payload_dict("config", value)
    return ResearchSourceScraplingAuthorityLatencyFloorConfig(
        config_version=_string_from_payload("config_version", payload["config_version"]),
        scrapling_latency_pass_threshold_seconds=_decimal_from_payload(
            "scrapling_latency_pass_threshold_seconds",
            payload["scrapling_latency_pass_threshold_seconds"],
        ),
        scrapling_latency_watch_threshold_seconds=_decimal_from_payload(
            "scrapling_latency_watch_threshold_seconds",
            payload["scrapling_latency_watch_threshold_seconds"],
        ),
        authority_latency_pass_threshold_seconds=_decimal_from_payload(
            "authority_latency_pass_threshold_seconds",
            payload["authority_latency_pass_threshold_seconds"],
        ),
        authority_latency_watch_threshold_seconds=_decimal_from_payload(
            "authority_latency_watch_threshold_seconds",
            payload["authority_latency_watch_threshold_seconds"],
        ),
        latency_gap_watch_threshold_seconds=_decimal_from_payload(
            "latency_gap_watch_threshold_seconds",
            payload["latency_gap_watch_threshold_seconds"],
        ),
        authority_latency_floor_pass_score=_decimal_from_payload(
            "authority_latency_floor_pass_score",
            payload["authority_latency_floor_pass_score"],
        ),
        authority_latency_floor_watch_score=_decimal_from_payload(
            "authority_latency_floor_watch_score",
            payload["authority_latency_floor_watch_score"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _reason_code_count_from_public_payload(
    value: object,
) -> ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount:
    payload = _require_payload_dict("reason code count payload", value)
    return ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount(
        reason_code=_string_from_payload("reason_code", payload["reason_code"]),
        count=_decimal_from_payload("count", payload["count"]),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _normalize_observations(
    observations: Iterable[ResearchSourceScraplingAuthorityLatencyFloorObservation],
) -> tuple[ResearchSourceScraplingAuthorityLatencyFloorObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for observation in normalized:
        if type(observation) is not ResearchSourceScraplingAuthorityLatencyFloorObservation:
            raise ValueError(
                "observations must contain "
                "ResearchSourceScraplingAuthorityLatencyFloorObservation",
            )
        observation.__post_init__()
    return tuple(sorted(normalized, key=_observation_sort_key))


def _observation_sort_key(
    observation: ResearchSourceScraplingAuthorityLatencyFloorObservation,
) -> tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        observation.observed_at.isoformat(),
        observation.scrapling_latency_seconds,
        observation.authority_latency_seconds,
        observation.scrapling_freshness_score,
        observation.authority_freshness_score,
        observation.authority_recheck_confidence_score,
    )


def _row_from_observation(
    observation: ResearchSourceScraplingAuthorityLatencyFloorObservation,
    *,
    row_index: int,
    config: ResearchSourceScraplingAuthorityLatencyFloorConfig,
    generated_at: datetime,
) -> ResearchSourceScraplingAuthorityLatencyFloorRow:
    observed_age_seconds = _duration_seconds(observation.observed_at, generated_at)
    with localcontext(DECIMAL_CONTEXT):
        latency_gap_seconds = _quantize(
            abs(
                observation.authority_latency_seconds
                - observation.scrapling_latency_seconds
            )
        )
    floor_score = _authority_latency_floor_score(observation)
    reason_codes = _row_reason_codes(
        floor_score=floor_score,
        scrapling_latency_seconds=observation.scrapling_latency_seconds,
        authority_latency_seconds=observation.authority_latency_seconds,
        latency_gap_seconds=latency_gap_seconds,
        config=config,
    )
    status = _row_status(reason_codes)
    if status == "pass":
        reason_codes = (PASS_REASON,)
    row = ResearchSourceScraplingAuthorityLatencyFloorRow(
        row_index=_count(row_index),
        observed_at=observation.observed_at,
        observed_age_seconds=observed_age_seconds,
        scrapling_latency_seconds=observation.scrapling_latency_seconds,
        authority_latency_seconds=observation.authority_latency_seconds,
        latency_gap_seconds=latency_gap_seconds,
        scrapling_freshness_score=observation.scrapling_freshness_score,
        authority_freshness_score=observation.authority_freshness_score,
        authority_recheck_confidence_score=observation.authority_recheck_confidence_score,
        authority_latency_floor_score=floor_score,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    _validate_row_consistency(row, config=config)
    return row


def _authority_latency_floor_score(
    observation: ResearchSourceScraplingAuthorityLatencyFloorObservation,
) -> Decimal:
    return _authority_latency_floor_score_from_values(
        observation.scrapling_freshness_score,
        observation.authority_freshness_score,
        observation.authority_recheck_confidence_score,
    )


def _authority_latency_floor_score_from_values(
    scrapling_freshness_score: Decimal,
    authority_freshness_score: Decimal,
    authority_recheck_confidence_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        base_score = _average(
            (
                scrapling_freshness_score,
                authority_freshness_score,
                authority_recheck_confidence_score,
            )
        )
        stability_bonus = _quantize((ONE - base_score) * FLOOR_SCORE_STABILITY_BONUS)
        return min(ONE, _quantize(base_score + stability_bonus))


def _row_reason_codes(
    *,
    floor_score: Decimal,
    scrapling_latency_seconds: Decimal,
    authority_latency_seconds: Decimal,
    latency_gap_seconds: Decimal,
    config: ResearchSourceScraplingAuthorityLatencyFloorConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if floor_score < config.authority_latency_floor_watch_score:
        reasons.append(FLOOR_BELOW_WATCH_REASON)
    elif floor_score < config.authority_latency_floor_pass_score:
        reasons.append(FLOOR_BELOW_PASS_REASON)
    if scrapling_latency_seconds > config.scrapling_latency_watch_threshold_seconds:
        reasons.append(SCRAPLING_ABOVE_WATCH_REASON)
    elif scrapling_latency_seconds > config.scrapling_latency_pass_threshold_seconds:
        reasons.append(SCRAPLING_ABOVE_PASS_REASON)
    if authority_latency_seconds > config.authority_latency_watch_threshold_seconds:
        reasons.append(AUTHORITY_ABOVE_WATCH_REASON)
    elif authority_latency_seconds > config.authority_latency_pass_threshold_seconds:
        reasons.append(AUTHORITY_ABOVE_PASS_REASON)
    if latency_gap_seconds > config.latency_gap_watch_threshold_seconds:
        reasons.append(GAP_ABOVE_WATCH_REASON)
    return _order_reason_codes(reasons, allow_empty=True)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_watch_threshold") for reason_code in reason_codes):
        return "block"
    if reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceScraplingAuthorityLatencyFloorRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceScraplingAuthorityLatencyFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    return _normalize_reason_codes(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchSourceScraplingAuthorityLatencyFloorRow, ...],
) -> tuple[ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount, ...]:
    if rows:
        counts = Counter(
            reason_code for row in rows for reason_code in row.reason_codes
        )
    else:
        counts = Counter((NO_INPUTS_REASON,))
    return tuple(
        ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            paper_only=True,
            report_only=True,
            readonly=True,
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: Iterable[ResearchSourceScraplingAuthorityLatencyFloorRow],
) -> tuple[ResearchSourceScraplingAuthorityLatencyFloorRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchSourceScraplingAuthorityLatencyFloorRow:
            raise ValueError("rows must contain ResearchSourceScraplingAuthorityLatencyFloorRow")
        row.__post_init__()
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(row: ResearchSourceScraplingAuthorityLatencyFloorRow) -> tuple[int, Decimal]:
    return (STATUS_WEIGHT[row.status], row.row_index)


def _normalize_reason_code_counts(
    counts: Iterable[ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount],
) -> tuple[ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in normalized:
        if type(count) is not ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceScraplingAuthorityLatencyFloorReasonCodeCount",
            )
        count.__post_init__()
    return tuple(
        sorted(
            normalized,
            key=lambda count: REASON_CODE_SEQUENCE.index(count.reason_code),
        )
    )


def _validate_report_consistency(
    report: ResearchSourceScraplingAuthorityLatencyFloorReport,
) -> None:
    for row in report.rows:
        _validate_row_consistency(
            row,
            config=report.config,
            generated_at=report.generated_at,
        )
    if report.observation_count != report.row_count:
        raise ValueError("observation_count must match row_count")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    for index, row in enumerate(
        sorted(report.rows, key=_row_observation_sort_key),
        start=1,
    ):
        if row.row_index != _count(index):
            raise ValueError("row_index must match the deterministic observation order")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match reason_codes")
    expected_averages = {
        "average_scrapling_latency_seconds": _average(
            row.scrapling_latency_seconds for row in report.rows
        ),
        "average_authority_latency_seconds": _average(
            row.authority_latency_seconds for row in report.rows
        ),
        "average_authority_latency_floor_score": _average(
            row.authority_latency_floor_score for row in report.rows
        ),
    }
    for field_name, expected_value in expected_averages.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    highest_gap = max((row.latency_gap_seconds for row in report.rows), default=ZERO)
    if report.highest_latency_gap_seconds != highest_gap:
        raise ValueError("highest_latency_gap_seconds must match rows")


def _validate_row_consistency(
    row: ResearchSourceScraplingAuthorityLatencyFloorRow,
    *,
    config: ResearchSourceScraplingAuthorityLatencyFloorConfig | None = None,
    generated_at: datetime | None = None,
) -> None:
    if generated_at is not None:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        expected_age = _duration_seconds(row.observed_at, generated_at)
        if row.observed_age_seconds != expected_age:
            raise ValueError("observed_age_seconds must match observed_at")
    expected_gap = _quantize(
        abs(row.authority_latency_seconds - row.scrapling_latency_seconds)
    )
    if row.latency_gap_seconds != expected_gap:
        raise ValueError("latency_gap_seconds must match row latencies")
    expected_score = _authority_latency_floor_score_from_values(
        row.scrapling_freshness_score,
        row.authority_freshness_score,
        row.authority_recheck_confidence_score,
    )
    if row.authority_latency_floor_score != expected_score:
        raise ValueError(
            "authority_latency_floor_score must match row freshness scores",
        )
    status_reasons = () if row.reason_codes == (PASS_REASON,) else row.reason_codes
    if row.status != _row_status(status_reasons):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass row reason_codes must contain only pass reason")
    if row.status != "pass" and PASS_REASON in row.reason_codes:
        raise ValueError("non-pass row reason_codes must not contain pass reason")
    if config is None:
        return
    expected_reasons = _row_reason_codes(
        floor_score=row.authority_latency_floor_score,
        scrapling_latency_seconds=row.scrapling_latency_seconds,
        authority_latency_seconds=row.authority_latency_seconds,
        latency_gap_seconds=row.latency_gap_seconds,
        config=config,
    )
    expected_status = _row_status(expected_reasons)
    if expected_status == "pass":
        expected_reasons = (PASS_REASON,)
    if row.status != expected_status:
        raise ValueError("status must match derived row values")
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match derived row values")


def _row_observation_sort_key(
    row: ResearchSourceScraplingAuthorityLatencyFloorRow,
) -> tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        row.observed_at.isoformat(),
        row.scrapling_latency_seconds,
        row.authority_latency_seconds,
        row.scrapling_freshness_score,
        row.authority_freshness_score,
        row.authority_recheck_confidence_score,
    )


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("duration start must be at or before end")
    delta = end - start
    with localcontext(DECIMAL_CONTEXT):
        total_microseconds = (
            Decimal(delta.days * 86400 + delta.seconds) * MICROSECOND_DIVISOR
            + Decimal(delta.microseconds)
        )
        return _quantize(total_microseconds / MICROSECOND_DIVISOR)


def _average(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(normalized, ZERO) / _count(len(normalized)))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < ZERO or raw_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(raw_value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(raw_value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw_value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        if raw_value != raw_value.to_integral_value():
            raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize(raw_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return value


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc
    return ZERO if normalized.is_zero() else normalized


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(QUANTUM)


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _contains_unsafe_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public surface")


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_SCRAPLING_AUTHORITY_LATENCY_FLOOR_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    return _order_reason_codes(value, allow_empty=False)


def _order_reason_codes(
    value: Iterable[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not reason_codes and allow_empty:
        return ()
    if not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    return tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in reason_codes
    )


def _require_exact_payload_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if tuple(value) != expected_keys:
        raise ValueError(f"{label} must use exact canonical schema")


def _require_payload_dict(label: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a dict")
    return value


def _require_payload_list(label: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a list")
    return value


def _string_from_payload(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _reason_codes_from_payload(field_name: str, value: object) -> tuple[str, ...]:
    values = _require_payload_list(field_name, value)
    return tuple(_string_from_payload(field_name, item) for item in values)


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    _require_decimal(field_name, parsed)
    if parsed.as_tuple().exponent != -6 or format(parsed, "f") != value:
        raise ValueError(
            f"{field_name} must be a canonical six-place Decimal string",
        )
    return parsed


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC ISO-8601 string")
    return normalized


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError(f"unsupported public payload value {type(value).__name__}")


def _report_digest(report: ResearchSourceScraplingAuthorityLatencyFloorReport) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _validate_public_payload(value: object) -> None:
    _reject_unsafe_public_payload(value)
    _reject_raw_public_numbers(value)


def _reject_raw_public_numbers(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be strings")
    if type(value) is dict:
        for item in value.values():
            _reject_raw_public_numbers(item)
        return
    if type(value) is list:
        for item in value:
            _reject_raw_public_numbers(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if _contains_unsafe_fragment(field.name):
                raise ValueError("unsafe public payload field")
            _reject_unsafe_public_payload(getattr(value, field.name))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload field must be a string")
            if _contains_unsafe_fragment(key):
                raise ValueError("unsafe public payload field")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, tuple | list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _contains_unsafe_fragment(value):
        raise ValueError("unsafe public payload value")


def _contains_unsafe_fragment(value: str) -> bool:
    normalized = "".join(character for character in value.casefold() if character.isalnum())
    return any(fragment and fragment in normalized for fragment in UNSAFE_PUBLIC_KEYS)


ResearchSourceScraplingAuthorityLatencyFloorInput = (
    ResearchSourceScraplingAuthorityLatencyFloorObservation
)
