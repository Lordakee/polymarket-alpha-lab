"""Pure report-only Scrapling retrieval reliability scorecard reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_SCRAPLING_RETRIEVAL_RELIABILITY_SCORECARD_REPORT_CONFIG_VERSION = (
    "research-source-scrapling-retrieval-reliability-scorecard-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HALF = Decimal("0.500000")
MICROSECOND_DIVISOR = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

NO_INPUTS_REASON = "scrapling_retrieval_reliability_no_inputs"
PASS_REASON = "scrapling_retrieval_reliability_pass"
WATCH_REASON = "scrapling_retrieval_reliability_watch"
BLOCK_REASON = "scrapling_retrieval_reliability_block"
REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    "success_ratio_block",
    "success_ratio_watch",
    "content_freshness_block",
    "content_freshness_watch",
    "primary_source_match_block",
    "primary_source_match_watch",
    "parse_completeness_block",
    "parse_completeness_watch",
    "contradiction_count_block",
    "contradiction_count_watch",
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "raw candidate",
    "candidate_id",
    "candidate id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "http://",
    "https://",
    "www.",
    "dsn",
    "token",
    "api_key",
    "secret",
    "password",
    "credential",
    "bearer",
    "authentication",
    "authorization",
    "wallet",
    "order",
    "trade",
    "live",
    "sizing",
    "recommendation",
    "execution",
    "execute",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPLING_RETRIEVAL_RELIABILITY_SCORECARD_REPORT_CONFIG_VERSION",
    "ResearchSourceScraplingRetrievalReliabilityObservation",
    "ResearchSourceScraplingRetrievalReliabilityScorecardConfig",
    "ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount",
    "ResearchSourceScraplingRetrievalReliabilityScorecardReport",
    "ResearchSourceScraplingRetrievalReliabilityScorecardRow",
    "STATUSES",
    "build_research_source_scrapling_retrieval_reliability_scorecard_report",
    "research_source_scrapling_retrieval_reliability_scorecard_report_digest",
    "research_source_scrapling_retrieval_reliability_scorecard_report_payload",
    "validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceScraplingRetrievalReliabilityScorecardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPLING_RETRIEVAL_RELIABILITY_SCORECARD_REPORT_CONFIG_VERSION
    )
    fresh_content_max_age_seconds: Decimal = Decimal("3600.000000")
    stale_content_block_age_seconds: Decimal = Decimal("86400.000000")
    min_success_ratio_pass: Decimal = Decimal("0.900000")
    min_success_ratio_watch: Decimal = Decimal("0.650000")
    min_primary_source_match_ratio_pass: Decimal = Decimal("0.800000")
    min_primary_source_match_ratio_watch: Decimal = Decimal("0.500000")
    min_parse_completeness_ratio_pass: Decimal = Decimal("0.900000")
    min_parse_completeness_ratio_watch: Decimal = Decimal("0.600000")
    max_contradiction_count_pass: Decimal = Decimal("0")
    max_contradiction_count_watch: Decimal = Decimal("2")
    min_reliability_score_pass: Decimal = Decimal("0.800000")
    min_reliability_score_watch: Decimal = Decimal("0.500000")
    success_ratio_weight: Decimal = Decimal("0.250000")
    content_freshness_weight: Decimal = Decimal("0.200000")
    primary_source_match_weight: Decimal = Decimal("0.200000")
    parse_completeness_weight: Decimal = Decimal("0.200000")
    contradiction_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingRetrievalReliabilityScorecardConfig:
            raise TypeError(
                "ResearchSourceScraplingRetrievalReliabilityScorecardConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingRetrievalReliabilityScorecardConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_RETRIEVAL_RELIABILITY_SCORECARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_content_max_age_seconds",
            "stale_content_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_content_max_age_seconds >= self.stale_content_block_age_seconds:
            raise ValueError(
                "fresh_content_max_age_seconds must be below "
                "stale_content_block_age_seconds",
            )
        for field_name in (
            "min_success_ratio_pass",
            "min_success_ratio_watch",
            "min_primary_source_match_ratio_pass",
            "min_primary_source_match_ratio_watch",
            "min_parse_completeness_ratio_pass",
            "min_parse_completeness_ratio_watch",
            "min_reliability_score_pass",
            "min_reliability_score_watch",
            "success_ratio_weight",
            "content_freshness_weight",
            "primary_source_match_weight",
            "parse_completeness_weight",
            "contradiction_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_contradiction_count_pass",
            "max_contradiction_count_watch",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_lower_threshold_pair(
            "min_success_ratio_watch",
            self.min_success_ratio_watch,
            "min_success_ratio_pass",
            self.min_success_ratio_pass,
        )
        _require_lower_threshold_pair(
            "min_primary_source_match_ratio_watch",
            self.min_primary_source_match_ratio_watch,
            "min_primary_source_match_ratio_pass",
            self.min_primary_source_match_ratio_pass,
        )
        _require_lower_threshold_pair(
            "min_parse_completeness_ratio_watch",
            self.min_parse_completeness_ratio_watch,
            "min_parse_completeness_ratio_pass",
            self.min_parse_completeness_ratio_pass,
        )
        _require_lower_threshold_pair(
            "min_reliability_score_watch",
            self.min_reliability_score_watch,
            "min_reliability_score_pass",
            self.min_reliability_score_pass,
        )
        if self.max_contradiction_count_pass > self.max_contradiction_count_watch:
            raise ValueError(
                "max_contradiction_count_pass must not exceed "
                "max_contradiction_count_watch",
            )
        weight_sum = _sum_decimals(
            (
                self.success_ratio_weight,
                self.content_freshness_weight,
                self.primary_source_match_weight,
                self.parse_completeness_weight,
                self.contradiction_weight,
            ),
        )
        if weight_sum != ONE:
            raise ValueError("reliability score weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScraplingRetrievalReliabilityObservation:
    private_retrieval_ref: str
    retrieved_at: datetime
    retrieval_attempt_count: Decimal
    retrieval_success_count: Decimal
    primary_source_match_count: Decimal
    parsed_field_count: Decimal
    expected_field_count: Decimal
    contradiction_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingRetrievalReliabilityObservation:
            raise TypeError(
                "ResearchSourceScraplingRetrievalReliabilityObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingRetrievalReliabilityObservation,
            "observation",
        )
        _require_private_string("private_retrieval_ref", self.private_retrieval_ref)
        object.__setattr__(self, "retrieved_at", _as_utc("retrieved_at", self.retrieved_at))
        for field_name in (
            "retrieval_attempt_count",
            "retrieval_success_count",
            "primary_source_match_count",
            "parsed_field_count",
            "expected_field_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _validate_count_consistency(
            retrieval_attempt_count=self.retrieval_attempt_count,
            retrieval_success_count=self.retrieval_success_count,
            primary_source_match_count=self.primary_source_match_count,
            parsed_field_count=self.parsed_field_count,
            expected_field_count=self.expected_field_count,
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceScraplingRetrievalReliabilityScorecardRow:
    row_label: str
    content_age_seconds: Decimal
    retrieval_attempt_count: Decimal
    retrieval_success_count: Decimal
    primary_source_match_count: Decimal
    parsed_field_count: Decimal
    expected_field_count: Decimal
    contradiction_count: Decimal
    success_ratio: Decimal
    content_freshness_score: Decimal
    primary_source_match_ratio: Decimal
    parse_completeness_ratio: Decimal
    contradiction_score: Decimal
    reliability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingRetrievalReliabilityScorecardRow:
            raise TypeError(
                "ResearchSourceScraplingRetrievalReliabilityScorecardRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingRetrievalReliabilityScorecardRow,
            "row",
        )
        _require_public_identifier("row_label", self.row_label)
        object.__setattr__(
            self,
            "content_age_seconds",
            _normalize_nonnegative_decimal(
                "content_age_seconds",
                self.content_age_seconds,
            ),
        )
        for field_name in (
            "retrieval_attempt_count",
            "retrieval_success_count",
            "primary_source_match_count",
            "parsed_field_count",
            "expected_field_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _validate_count_consistency(
            retrieval_attempt_count=self.retrieval_attempt_count,
            retrieval_success_count=self.retrieval_success_count,
            primary_source_match_count=self.primary_source_match_count,
            parsed_field_count=self.parsed_field_count,
            expected_field_count=self.expected_field_count,
        )
        for field_name in (
            "success_ratio",
            "content_freshness_score",
            "primary_source_match_ratio",
            "parse_completeness_ratio",
            "contradiction_score",
            "reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.success_ratio != _safe_ratio(
            self.retrieval_success_count,
            self.retrieval_attempt_count,
        ):
            raise ValueError("success_ratio must match retrieval counts")
        if self.primary_source_match_ratio != _safe_ratio(
            self.primary_source_match_count,
            self.retrieval_success_count,
        ):
            raise ValueError("primary_source_match_ratio must match retrieval counts")
        if self.parse_completeness_ratio != _safe_ratio(
            self.parsed_field_count,
            self.expected_field_count,
        ):
            raise ValueError("parse_completeness_ratio must match field counts")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount:
            raise TypeError(
                "ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchSourceScraplingRetrievalReliabilityScorecardReport:
    generated_at: datetime
    config_version: str
    config: ResearchSourceScraplingRetrievalReliabilityScorecardConfig
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    max_content_age_seconds: Decimal
    contradiction_count: Decimal
    average_success_ratio: Decimal
    average_content_freshness_score: Decimal
    average_primary_source_match_ratio: Decimal
    average_parse_completeness_ratio: Decimal
    average_contradiction_score: Decimal
    average_reliability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchSourceScraplingRetrievalReliabilityScorecardRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingRetrievalReliabilityScorecardReport:
            raise TypeError(
                "ResearchSourceScraplingRetrievalReliabilityScorecardReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingRetrievalReliabilityScorecardReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if type(self.config) is not (
            ResearchSourceScraplingRetrievalReliabilityScorecardConfig
        ):
            raise ValueError(
                "config must be exactly "
                "ResearchSourceScraplingRetrievalReliabilityScorecardConfig",
            )
        ResearchSourceScraplingRetrievalReliabilityScorecardConfig.__post_init__(
            self.config,
        )
        _require_hard_flags("config", self.config)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "attention_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_content_age_seconds",
            _normalize_nonnegative_decimal(
                "max_content_age_seconds",
                self.max_content_age_seconds,
            ),
        )
        for field_name in (
            "average_success_ratio",
            "average_content_freshness_score",
            "average_primary_source_match_ratio",
            "average_parse_completeness_ratio",
            "average_contradiction_score",
            "average_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return (
            research_source_scrapling_retrieval_reliability_scorecard_report_payload(
                self,
            )
        )

    @property
    def digest(self) -> str:
        return research_source_scrapling_retrieval_reliability_scorecard_report_digest(
            self,
        )


def build_research_source_scrapling_retrieval_reliability_scorecard_report(
    observations: Iterable[
        ResearchSourceScraplingRetrievalReliabilityObservation
    ],
    *,
    config: ResearchSourceScraplingRetrievalReliabilityScorecardConfig,
    generated_at: datetime,
) -> ResearchSourceScraplingRetrievalReliabilityScorecardReport:
    if type(config) is not (
        ResearchSourceScraplingRetrievalReliabilityScorecardConfig
    ):
        raise ValueError(
            "config must be exactly "
            "ResearchSourceScraplingRetrievalReliabilityScorecardConfig",
        )
    ResearchSourceScraplingRetrievalReliabilityScorecardConfig.__post_init__(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.retrieved_at > generated_at:
            raise ValueError("retrieved_at cannot be after generated_at")

    rows = tuple(
        _row_from_observation(
            observation,
            row_number=index,
            config=config,
            generated_at=generated_at,
        )
        for index, observation in enumerate(normalized_observations, start=1)
    )
    rows = tuple(sorted(rows, key=_row_sort_key))
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows, status)

    return ResearchSourceScraplingRetrievalReliabilityScorecardReport(
        generated_at=generated_at,
        config_version=config.config_version,
        config=config,
        input_count=_count_decimal(len(normalized_observations)),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        attention_count=_sum_decimals(
            (
                _status_count(rows, "watch"),
                _status_count(rows, "block"),
            ),
        ),
        max_content_age_seconds=max(
            (row.content_age_seconds for row in rows),
            default=ZERO,
        ),
        contradiction_count=_sum_decimals(
            tuple(row.contradiction_count for row in rows),
        ),
        average_success_ratio=_average(row.success_ratio for row in rows),
        average_content_freshness_score=_average(
            row.content_freshness_score for row in rows
        ),
        average_primary_source_match_ratio=_average(
            row.primary_source_match_ratio for row in rows
        ),
        average_parse_completeness_ratio=_average(
            row.parse_completeness_ratio for row in rows
        ),
        average_contradiction_score=_average(
            row.contradiction_score for row in rows
        ),
        average_reliability_score=_average(row.reliability_score for row in rows),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_scrapling_retrieval_reliability_scorecard_report_payload(
    report: ResearchSourceScraplingRetrievalReliabilityScorecardReport,
) -> dict[str, Any]:
    if type(report) is not (
        ResearchSourceScraplingRetrievalReliabilityScorecardReport
    ):
        raise ValueError(
            "report must be exactly "
            "ResearchSourceScraplingRetrievalReliabilityScorecardReport",
        )
    ResearchSourceScraplingRetrievalReliabilityScorecardReport.__post_init__(
        report,
    )
    _validate_report_consistency(report)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def research_source_scrapling_retrieval_reliability_scorecard_report_digest(
    report: ResearchSourceScraplingRetrievalReliabilityScorecardReport,
) -> str:
    payload = (
        research_source_scrapling_retrieval_reliability_scorecard_report_payload(
            report,
        )
    )
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        return False
    try:
        _validate_public_payload(payload)
        digest = payload.get("derived_validation_digest")
        if type(digest) is not str or DIGEST_RE.fullmatch(digest) is None:
            return False
        unsigned = dict(payload)
        unsigned.pop("derived_validation_digest")
        encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        if sha256(encoded).hexdigest() != digest:
            return False
        report = _report_from_payload(payload)
        return (
            research_source_scrapling_retrieval_reliability_scorecard_report_payload(
                report,
            )
            == payload
        )
    except (
        DecimalException,
        KeyError,
        OverflowError,
        RecursionError,
        TypeError,
        ValueError,
    ):
        return False


def _report_from_payload(
    payload: dict[str, Any],
) -> ResearchSourceScraplingRetrievalReliabilityScorecardReport:
    _require_payload_keys(
        "report payload",
        payload,
        ResearchSourceScraplingRetrievalReliabilityScorecardReport,
    )
    return ResearchSourceScraplingRetrievalReliabilityScorecardReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        config=_config_from_payload(payload["config"]),
        input_count=_payload_decimal("input_count", payload["input_count"]),
        row_count=_payload_decimal("row_count", payload["row_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        attention_count=_payload_decimal(
            "attention_count",
            payload["attention_count"],
        ),
        max_content_age_seconds=_payload_decimal(
            "max_content_age_seconds",
            payload["max_content_age_seconds"],
        ),
        contradiction_count=_payload_decimal(
            "contradiction_count",
            payload["contradiction_count"],
        ),
        average_success_ratio=_payload_decimal(
            "average_success_ratio",
            payload["average_success_ratio"],
        ),
        average_content_freshness_score=_payload_decimal(
            "average_content_freshness_score",
            payload["average_content_freshness_score"],
        ),
        average_primary_source_match_ratio=_payload_decimal(
            "average_primary_source_match_ratio",
            payload["average_primary_source_match_ratio"],
        ),
        average_parse_completeness_ratio=_payload_decimal(
            "average_parse_completeness_ratio",
            payload["average_parse_completeness_ratio"],
        ),
        average_contradiction_score=_payload_decimal(
            "average_contradiction_score",
            payload["average_contradiction_score"],
        ),
        average_reliability_score=_payload_decimal(
            "average_reliability_score",
            payload["average_reliability_score"],
        ),
        status=_payload_string("status", payload["status"]),
        reason_codes=_payload_string_tuple(
            "reason_codes",
            payload["reason_codes"],
        ),
        reason_code_counts=_payload_tuple(
            "reason_code_counts",
            payload["reason_code_counts"],
            _reason_code_count_from_payload,
        ),
        rows=_payload_tuple("rows", payload["rows"], _row_from_payload),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _config_from_payload(
    payload: Any,
) -> ResearchSourceScraplingRetrievalReliabilityScorecardConfig:
    _require_payload_keys(
        "config payload",
        payload,
        ResearchSourceScraplingRetrievalReliabilityScorecardConfig,
    )
    return ResearchSourceScraplingRetrievalReliabilityScorecardConfig(
        config_version=_payload_string("config_version", payload["config_version"]),
        fresh_content_max_age_seconds=_payload_decimal(
            "fresh_content_max_age_seconds",
            payload["fresh_content_max_age_seconds"],
        ),
        stale_content_block_age_seconds=_payload_decimal(
            "stale_content_block_age_seconds",
            payload["stale_content_block_age_seconds"],
        ),
        min_success_ratio_pass=_payload_decimal(
            "min_success_ratio_pass",
            payload["min_success_ratio_pass"],
        ),
        min_success_ratio_watch=_payload_decimal(
            "min_success_ratio_watch",
            payload["min_success_ratio_watch"],
        ),
        min_primary_source_match_ratio_pass=_payload_decimal(
            "min_primary_source_match_ratio_pass",
            payload["min_primary_source_match_ratio_pass"],
        ),
        min_primary_source_match_ratio_watch=_payload_decimal(
            "min_primary_source_match_ratio_watch",
            payload["min_primary_source_match_ratio_watch"],
        ),
        min_parse_completeness_ratio_pass=_payload_decimal(
            "min_parse_completeness_ratio_pass",
            payload["min_parse_completeness_ratio_pass"],
        ),
        min_parse_completeness_ratio_watch=_payload_decimal(
            "min_parse_completeness_ratio_watch",
            payload["min_parse_completeness_ratio_watch"],
        ),
        max_contradiction_count_pass=_payload_decimal(
            "max_contradiction_count_pass",
            payload["max_contradiction_count_pass"],
        ),
        max_contradiction_count_watch=_payload_decimal(
            "max_contradiction_count_watch",
            payload["max_contradiction_count_watch"],
        ),
        min_reliability_score_pass=_payload_decimal(
            "min_reliability_score_pass",
            payload["min_reliability_score_pass"],
        ),
        min_reliability_score_watch=_payload_decimal(
            "min_reliability_score_watch",
            payload["min_reliability_score_watch"],
        ),
        success_ratio_weight=_payload_decimal(
            "success_ratio_weight",
            payload["success_ratio_weight"],
        ),
        content_freshness_weight=_payload_decimal(
            "content_freshness_weight",
            payload["content_freshness_weight"],
        ),
        primary_source_match_weight=_payload_decimal(
            "primary_source_match_weight",
            payload["primary_source_match_weight"],
        ),
        parse_completeness_weight=_payload_decimal(
            "parse_completeness_weight",
            payload["parse_completeness_weight"],
        ),
        contradiction_weight=_payload_decimal(
            "contradiction_weight",
            payload["contradiction_weight"],
        ),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _row_from_payload(
    payload: Any,
) -> ResearchSourceScraplingRetrievalReliabilityScorecardRow:
    _require_payload_keys(
        "row payload",
        payload,
        ResearchSourceScraplingRetrievalReliabilityScorecardRow,
    )
    return ResearchSourceScraplingRetrievalReliabilityScorecardRow(
        row_label=_payload_string("row_label", payload["row_label"]),
        content_age_seconds=_payload_decimal(
            "content_age_seconds",
            payload["content_age_seconds"],
        ),
        retrieval_attempt_count=_payload_decimal(
            "retrieval_attempt_count",
            payload["retrieval_attempt_count"],
        ),
        retrieval_success_count=_payload_decimal(
            "retrieval_success_count",
            payload["retrieval_success_count"],
        ),
        primary_source_match_count=_payload_decimal(
            "primary_source_match_count",
            payload["primary_source_match_count"],
        ),
        parsed_field_count=_payload_decimal(
            "parsed_field_count",
            payload["parsed_field_count"],
        ),
        expected_field_count=_payload_decimal(
            "expected_field_count",
            payload["expected_field_count"],
        ),
        contradiction_count=_payload_decimal(
            "contradiction_count",
            payload["contradiction_count"],
        ),
        success_ratio=_payload_decimal("success_ratio", payload["success_ratio"]),
        content_freshness_score=_payload_decimal(
            "content_freshness_score",
            payload["content_freshness_score"],
        ),
        primary_source_match_ratio=_payload_decimal(
            "primary_source_match_ratio",
            payload["primary_source_match_ratio"],
        ),
        parse_completeness_ratio=_payload_decimal(
            "parse_completeness_ratio",
            payload["parse_completeness_ratio"],
        ),
        contradiction_score=_payload_decimal(
            "contradiction_score",
            payload["contradiction_score"],
        ),
        reliability_score=_payload_decimal(
            "reliability_score",
            payload["reliability_score"],
        ),
        status=_payload_string("status", payload["status"]),
        reason_codes=_payload_string_tuple(
            "reason_codes",
            payload["reason_codes"],
        ),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _reason_code_count_from_payload(
    payload: Any,
) -> ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount:
    _require_payload_keys(
        "reason code count payload",
        payload,
        ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount,
    )
    return ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount(
        reason_code=_payload_string("reason_code", payload["reason_code"]),
        count=_payload_decimal("count", payload["count"]),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _row_from_observation(
    observation: ResearchSourceScraplingRetrievalReliabilityObservation,
    *,
    row_number: int,
    config: ResearchSourceScraplingRetrievalReliabilityScorecardConfig,
    generated_at: datetime,
) -> ResearchSourceScraplingRetrievalReliabilityScorecardRow:
    content_age_seconds = _age_seconds(generated_at, observation.retrieved_at)
    success_ratio = _safe_ratio(
        observation.retrieval_success_count,
        observation.retrieval_attempt_count,
    )
    content_freshness_score = _content_freshness_score(
        content_age_seconds,
        config,
    )
    primary_source_match_ratio = _safe_ratio(
        observation.primary_source_match_count,
        observation.retrieval_success_count,
    )
    parse_completeness_ratio = _safe_ratio(
        observation.parsed_field_count,
        observation.expected_field_count,
    )
    contradiction_score = _contradiction_score(
        observation.contradiction_count,
        config,
    )
    reliability_score = _reliability_score(
        success_ratio=success_ratio,
        content_freshness_score=content_freshness_score,
        primary_source_match_ratio=primary_source_match_ratio,
        parse_completeness_ratio=parse_completeness_ratio,
        contradiction_score=contradiction_score,
        config=config,
    )
    component_reasons = _row_component_reason_codes(
        success_ratio=success_ratio,
        content_age_seconds=content_age_seconds,
        content_freshness_score=content_freshness_score,
        primary_source_match_ratio=primary_source_match_ratio,
        parse_completeness_ratio=parse_completeness_ratio,
        contradiction_count=observation.contradiction_count,
        config=config,
    )
    status = _row_status(component_reasons, reliability_score, config)
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        (*component_reasons, _status_reason(status)),
    )
    return ResearchSourceScraplingRetrievalReliabilityScorecardRow(
        row_label=f"redacted-scrapling-retrieval-{row_number:06d}",
        content_age_seconds=content_age_seconds,
        retrieval_attempt_count=observation.retrieval_attempt_count,
        retrieval_success_count=observation.retrieval_success_count,
        primary_source_match_count=observation.primary_source_match_count,
        parsed_field_count=observation.parsed_field_count,
        expected_field_count=observation.expected_field_count,
        contradiction_count=observation.contradiction_count,
        success_ratio=success_ratio,
        content_freshness_score=content_freshness_score,
        primary_source_match_ratio=primary_source_match_ratio,
        parse_completeness_ratio=parse_completeness_ratio,
        contradiction_score=contradiction_score,
        reliability_score=reliability_score,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _content_freshness_score(
    content_age_seconds: Decimal,
    config: ResearchSourceScraplingRetrievalReliabilityScorecardConfig,
) -> Decimal:
    if content_age_seconds <= config.fresh_content_max_age_seconds:
        return ONE
    if content_age_seconds >= config.stale_content_block_age_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        stale_window = (
            config.stale_content_block_age_seconds
            - config.fresh_content_max_age_seconds
        )
        stale_progress = _safe_ratio(
            content_age_seconds - config.fresh_content_max_age_seconds,
            stale_window,
        )
        return _quantize(ONE - stale_progress)


def _contradiction_score(
    contradiction_count: Decimal,
    config: ResearchSourceScraplingRetrievalReliabilityScorecardConfig,
) -> Decimal:
    if contradiction_count <= config.max_contradiction_count_pass:
        return ONE
    if contradiction_count <= config.max_contradiction_count_watch:
        return HALF
    return ZERO


def _reliability_score(
    *,
    success_ratio: Decimal,
    content_freshness_score: Decimal,
    primary_source_match_ratio: Decimal,
    parse_completeness_ratio: Decimal,
    contradiction_score: Decimal,
    config: ResearchSourceScraplingRetrievalReliabilityScorecardConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            success_ratio * config.success_ratio_weight
            + content_freshness_score * config.content_freshness_weight
            + primary_source_match_ratio * config.primary_source_match_weight
            + parse_completeness_ratio * config.parse_completeness_weight
            + contradiction_score * config.contradiction_weight,
        )


def _row_component_reason_codes(
    *,
    success_ratio: Decimal,
    content_age_seconds: Decimal,
    content_freshness_score: Decimal,
    primary_source_match_ratio: Decimal,
    parse_completeness_ratio: Decimal,
    contradiction_count: Decimal,
    config: ResearchSourceScraplingRetrievalReliabilityScorecardConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if success_ratio < config.min_success_ratio_watch:
        reason_codes.append("success_ratio_block")
    elif success_ratio < config.min_success_ratio_pass:
        reason_codes.append("success_ratio_watch")

    if content_age_seconds >= config.stale_content_block_age_seconds:
        reason_codes.append("content_freshness_block")
    elif content_freshness_score < ONE:
        reason_codes.append("content_freshness_watch")

    if primary_source_match_ratio < config.min_primary_source_match_ratio_watch:
        reason_codes.append("primary_source_match_block")
    elif primary_source_match_ratio < config.min_primary_source_match_ratio_pass:
        reason_codes.append("primary_source_match_watch")

    if parse_completeness_ratio < config.min_parse_completeness_ratio_watch:
        reason_codes.append("parse_completeness_block")
    elif parse_completeness_ratio < config.min_parse_completeness_ratio_pass:
        reason_codes.append("parse_completeness_watch")

    if contradiction_count > config.max_contradiction_count_watch:
        reason_codes.append("contradiction_count_block")
    elif contradiction_count > config.max_contradiction_count_pass:
        reason_codes.append("contradiction_count_watch")

    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _row_status(
    component_reasons: tuple[str, ...],
    reliability_score: Decimal,
    config: ResearchSourceScraplingRetrievalReliabilityScorecardConfig,
) -> str:
    if any(reason_code.endswith("_block") for reason_code in component_reasons):
        return "block"
    if reliability_score < config.min_reliability_score_watch:
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in component_reasons):
        return "watch"
    if reliability_score < config.min_reliability_score_pass:
        return "watch"
    return "pass"


def _status_reason(status: str) -> str:
    if status == "pass":
        return PASS_REASON
    if status == "watch":
        return WATCH_REASON
    if status == "block":
        return BLOCK_REASON
    raise ValueError("status must be pass, watch, or block")


def _report_status(
    rows: tuple[ResearchSourceScraplingRetrievalReliabilityScorecardRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceScraplingRetrievalReliabilityScorecardRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON, BLOCK_REASON)
    reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    reason_codes.add(_status_reason(status))
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchSourceScraplingRetrievalReliabilityScorecardRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[
    ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount,
    ...,
]:
    counts: Counter[str] = Counter()
    if rows:
        for row in rows:
            counts.update(row.reason_codes)
    else:
        counts.update(reason_codes)
    return tuple(
        ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counts[reason_code]),
            paper_only=True,
            report_only=True,
            readonly=True,
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _validate_row_consistency(
    row: ResearchSourceScraplingRetrievalReliabilityScorecardRow,
    config: ResearchSourceScraplingRetrievalReliabilityScorecardConfig,
) -> None:
    expected_freshness = _content_freshness_score(
        row.content_age_seconds,
        config,
    )
    if row.content_freshness_score != expected_freshness:
        raise ValueError("content_freshness_score must match content age")
    expected_contradiction_score = _contradiction_score(
        row.contradiction_count,
        config,
    )
    if row.contradiction_score != expected_contradiction_score:
        raise ValueError("contradiction_score must match contradiction_count")
    expected_reliability_score = _reliability_score(
        success_ratio=row.success_ratio,
        content_freshness_score=row.content_freshness_score,
        primary_source_match_ratio=row.primary_source_match_ratio,
        parse_completeness_ratio=row.parse_completeness_ratio,
        contradiction_score=row.contradiction_score,
        config=config,
    )
    if row.reliability_score != expected_reliability_score:
        raise ValueError("reliability_score must match component scores")
    component_reasons = _row_component_reason_codes(
        success_ratio=row.success_ratio,
        content_age_seconds=row.content_age_seconds,
        content_freshness_score=row.content_freshness_score,
        primary_source_match_ratio=row.primary_source_match_ratio,
        parse_completeness_ratio=row.parse_completeness_ratio,
        contradiction_count=row.contradiction_count,
        config=config,
    )
    expected_status = _row_status(
        component_reasons,
        row.reliability_score,
        config,
    )
    if row.status != expected_status:
        raise ValueError("row status must match derived reliability logic")
    expected_reasons = _normalize_reason_codes(
        "reason_codes",
        (*component_reasons, _status_reason(expected_status)),
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("row reason_codes must match derived reliability logic")


def _validate_report_consistency(
    report: ResearchSourceScraplingRetrievalReliabilityScorecardReport,
) -> None:
    for row in report.rows:
        _validate_row_consistency(row, report.config)
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.attention_count != _sum_decimals(
        (report.watch_count, report.block_count),
    ):
        raise ValueError("attention_count must match watch and block counts")
    if report.max_content_age_seconds != max(
        (row.content_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_content_age_seconds must match rows")
    if report.contradiction_count != _sum_decimals(
        tuple(row.contradiction_count for row in report.rows),
    ):
        raise ValueError("contradiction_count must match rows")
    expected_averages = {
        "average_success_ratio": _average(
            row.success_ratio for row in report.rows
        ),
        "average_content_freshness_score": _average(
            row.content_freshness_score for row in report.rows
        ),
        "average_primary_source_match_ratio": _average(
            row.primary_source_match_ratio for row in report.rows
        ),
        "average_parse_completeness_ratio": _average(
            row.parse_completeness_ratio for row in report.rows
        ),
        "average_contradiction_score": _average(
            row.contradiction_score for row in report.rows
        ),
        "average_reliability_score": _average(
            row.reliability_score for row in report.rows
        ),
    }
    for field_name, expected_value in expected_averages.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    expected_reasons = _report_reason_codes(report.rows, expected_status)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows and status")
    expected_counts = _reason_code_counts(report.rows, expected_reasons)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows and reason_codes")


def _validate_count_consistency(
    *,
    retrieval_attempt_count: Decimal,
    retrieval_success_count: Decimal,
    primary_source_match_count: Decimal,
    parsed_field_count: Decimal,
    expected_field_count: Decimal,
) -> None:
    if retrieval_attempt_count <= ZERO:
        raise ValueError("retrieval_attempt_count must be positive")
    if retrieval_success_count > retrieval_attempt_count:
        raise ValueError(
            "retrieval_success_count must not exceed retrieval_attempt_count",
        )
    if primary_source_match_count > retrieval_success_count:
        raise ValueError(
            "primary_source_match_count must not exceed retrieval_success_count",
        )
    if expected_field_count <= ZERO:
        raise ValueError("expected_field_count must be positive")
    if parsed_field_count > expected_field_count:
        raise ValueError("parsed_field_count must not exceed expected_field_count")


def _normalize_observations(
    observations: Iterable[
        ResearchSourceScraplingRetrievalReliabilityObservation
    ],
) -> tuple[ResearchSourceScraplingRetrievalReliabilityObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for observation in normalized:
        if type(observation) is not (
            ResearchSourceScraplingRetrievalReliabilityObservation
        ):
            raise ValueError(
                "observations must contain "
                "ResearchSourceScraplingRetrievalReliabilityObservation",
            )
        ResearchSourceScraplingRetrievalReliabilityObservation.__post_init__(
            observation,
        )
        _require_hard_flags("observation", observation)
    return tuple(sorted(normalized, key=_observation_sort_key))


def _observation_sort_key(
    observation: ResearchSourceScraplingRetrievalReliabilityObservation,
) -> tuple[
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    str,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
]:
    return (
        _safe_ratio(
            observation.retrieval_success_count,
            observation.retrieval_attempt_count,
        ).copy_negate(),
        _safe_ratio(
            observation.primary_source_match_count,
            observation.retrieval_success_count,
        ).copy_negate(),
        _safe_ratio(
            observation.parsed_field_count,
            observation.expected_field_count,
        ).copy_negate(),
        observation.contradiction_count,
        observation.retrieved_at.isoformat(),
        observation.retrieval_attempt_count,
        observation.retrieval_success_count,
        observation.primary_source_match_count,
        observation.parsed_field_count,
        observation.expected_field_count,
    )


def _normalize_rows(
    rows: tuple[ResearchSourceScraplingRetrievalReliabilityScorecardRow, ...],
) -> tuple[ResearchSourceScraplingRetrievalReliabilityScorecardRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchSourceScraplingRetrievalReliabilityScorecardRow:
            raise ValueError(
                "rows must contain "
                "ResearchSourceScraplingRetrievalReliabilityScorecardRow",
            )
        ResearchSourceScraplingRetrievalReliabilityScorecardRow.__post_init__(row)
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(normalized, key=_row_sort_key))
    if normalized != sorted_rows:
        raise ValueError("rows must be sorted")
    if len({row.row_label for row in normalized}) != len(normalized):
        raise ValueError("rows must have unique row_label values")
    expected_labels = {
        f"redacted-scrapling-retrieval-{index:06d}"
        for index in range(1, len(normalized) + 1)
    }
    if {row.row_label for row in normalized} != expected_labels:
        raise ValueError("rows must use canonical redacted row_label values")
    identity_sorted_rows = tuple(sorted(normalized, key=_row_identity_sort_key))
    for index, row in enumerate(identity_sorted_rows, start=1):
        expected_label = f"redacted-scrapling-retrieval-{index:06d}"
        if row.row_label != expected_label:
            raise ValueError("row_label must match canonical public row identity rank")
    return normalized


def _row_sort_key(
    row: ResearchSourceScraplingRetrievalReliabilityScorecardRow,
) -> tuple[Any, ...]:
    return (
        STATUS_WEIGHT[row.status],
        row.reliability_score,
        row.success_ratio,
        row.content_freshness_score,
        row.primary_source_match_ratio,
        row.parse_completeness_ratio,
        row.contradiction_score,
        *_row_identity_sort_key(row),
        row.reason_codes,
        row.row_label,
    )


def _row_identity_sort_key(
    row: ResearchSourceScraplingRetrievalReliabilityScorecardRow,
) -> tuple[
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
]:
    return (
        row.success_ratio.copy_negate(),
        row.primary_source_match_ratio.copy_negate(),
        row.parse_completeness_ratio.copy_negate(),
        row.contradiction_count,
        row.content_age_seconds.copy_negate(),
        row.retrieval_attempt_count,
        row.retrieval_success_count,
        row.primary_source_match_count,
        row.parsed_field_count,
        row.expected_field_count,
    )


def _normalize_reason_code_counts(
    counts: tuple[
        ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount,
        ...,
    ],
) -> tuple[
    ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount,
    ...,
]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in normalized:
        if type(count) is not (
            ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount",
            )
        ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount.__post_init__(
            count,
        )
        _require_hard_flags("reason count", count)
    sorted_counts = tuple(
        sorted(
            normalized,
            key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )
    if normalized != sorted_counts:
        raise ValueError("reason_code_counts must be sorted")
    if len({item.reason_code for item in normalized}) != len(normalized):
        raise ValueError("reason_code_counts must be unique")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _status_count(
    rows: tuple[ResearchSourceScraplingRetrievalReliabilityScorecardRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _average(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _safe_ratio(
        _sum_decimals(normalized),
        _count_decimal(len(normalized)),
    )


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _age_seconds(generated_at: datetime, retrieved_at: datetime) -> Decimal:
    delta = generated_at - retrieved_at
    if delta.days < 0:
        raise ValueError("content age seconds must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            Decimal(delta.days * 86400 + delta.seconds)
            + Decimal(delta.microseconds) / MICROSECOND_DIVISOR,
        )


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(QUANTUM)
    except DecimalException as exc:
        raise ValueError("Decimal value is outside the supported range") from exc
    if normalized.is_zero():
        return ZERO
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if raw != raw.to_integral_value(context=DECIMAL_CONTEXT):
        raise ValueError(f"{field_name} must be a whole number")
    return _quantize(raw)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO or raw > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(raw)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _quantize(_require_raw_decimal(field_name, value))


def _require_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    try:
        utc_offset = value.utcoffset()
    except Exception as exc:
        raise ValueError(f"{field_name} must have a valid UTC offset") from exc
    if utc_offset is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    try:
        return value.astimezone(UTC)
    except Exception as exc:
        raise ValueError(f"{field_name} must be representable in UTC") from exc


def _require_lower_threshold_pair(
    lower_field_name: str,
    lower_value: Decimal,
    upper_field_name: str,
    upper_value: Decimal,
) -> None:
    if lower_value > upper_value:
        raise ValueError(
            f"{lower_field_name} must not exceed {upper_field_name}",
        )


def _require_exact_type(
    value: object,
    expected_type: type[object],
    label: str,
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str or value == "":
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_text(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    _reject_unsafe_public_text(field_name, value)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _report_digest(
    report: ResearchSourceScraplingRetrievalReliabilityScorecardReport,
) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _validate_public_payload(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) in (int, float):
        raise ValueError("JSON value must not contain raw numeric values")
    if type(value) in (str, bool):
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


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    ready = _json_ready(
        asdict(value)
        if is_dataclass(value) and not isinstance(value, type)
        else value,
    )
    _validate_public_payload(ready, label=label)


def _validate_public_payload(value: Any, *, label: str = "payload") -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_text(label, key)
            _validate_public_payload(item, label=key)
        return
    if type(value) is list:
        for item in value:
            _validate_public_payload(item, label=label)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) in (int, float, Decimal):
        raise ValueError(f"{label} must not expose raw numeric values")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} has unsafe public surface")


def _payload_tuple(
    field_name: str,
    value: Any,
    item_parser: Any,
) -> tuple[Any, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(item_parser(item) for item in value)


def _payload_string_tuple(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(_payload_string(field_name, item) for item in value)


def _payload_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        return Decimal(value)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must be a valid Decimal string") from exc


def _payload_datetime(field_name: str, value: Any) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    return datetime.fromisoformat(value)


def _payload_string(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_bool(field_name: str, value: Any) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_payload_keys(
    label: str,
    payload: Any,
    dataclass_type: type[object],
) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    expected_keys = tuple(field.name for field in fields(dataclass_type))
    if tuple(payload) != expected_keys:
        raise ValueError(f"{label} must match the report schema")
