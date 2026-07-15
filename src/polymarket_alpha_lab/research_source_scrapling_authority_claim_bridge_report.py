"""Report-only Scrapling authority claim bridge diagnostics.

Callers provide already-sanitized authority claim bridge observations. This
module performs no database, network, wallet, order, sizing, auth, or trading
work and exposes only a deterministic public report with Decimal-only numerics
and SHA-256 digest validation.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_CLAIM_BRIDGE_REPORT_CONFIG_VERSION = (
    "research-source-scrapling-authority-claim-bridge-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_SOURCE_SCRAPLING_AUTHORITY_CLAIM_BRIDGE_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

NO_INPUTS_REASON = "scrapling_authority_claim_bridge_no_inputs"
PASS_REASON = "scrapling_authority_claim_bridge_pass"
BRIDGE_SCORE_BLOCK_REASON = "bridge_authority_score_below_watch_threshold"
DUAL_CLAIM_FLOOR_BLOCK_REASON = "dual_claim_floor_below_watch_threshold"
CLAIM_GAP_BLOCK_REASON = "claim_gap_above_watch_threshold"
CONTRADICTION_BLOCK_REASON = "contradiction_pressure_above_watch_threshold"
UNRESOLVED_GAP_BLOCK_REASON = "unresolved_authority_gap_above_watch_threshold"
BRIDGE_SCORE_WATCH_REASON = "bridge_authority_score_below_pass_threshold"
DUAL_CLAIM_FLOOR_WATCH_REASON = "dual_claim_floor_below_pass_threshold"
CLAIM_GAP_WATCH_REASON = "claim_gap_above_pass_threshold"
CONTRADICTION_WATCH_REASON = "contradiction_pressure_above_pass_threshold"
UNRESOLVED_GAP_WATCH_REASON = "unresolved_authority_gap_above_pass_threshold"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    BRIDGE_SCORE_BLOCK_REASON,
    DUAL_CLAIM_FLOOR_BLOCK_REASON,
    CLAIM_GAP_BLOCK_REASON,
    CONTRADICTION_BLOCK_REASON,
    UNRESOLVED_GAP_BLOCK_REASON,
    BRIDGE_SCORE_WATCH_REASON,
    DUAL_CLAIM_FLOOR_WATCH_REASON,
    CLAIM_GAP_WATCH_REASON,
    CONTRADICTION_WATCH_REASON,
    UNRESOLVED_GAP_WATCH_REASON,
    PASS_REASON,
)
BLOCK_REASON_CODES = frozenset(
    reason_code
    for reason_code in REASON_CODE_SEQUENCE
    if reason_code.endswith("_watch_threshold")
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=50, rounding=ROUND_HALF_UP)
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_",
    "_raw",
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "raw_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "sizing",
    "recommend",
    "private",
    "secret",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "raw_candidate",
    "candidate id",
    "candidate_id",
    "market id",
    "market_id",
    "market_slug",
    "source_url",
    "source_text",
    "raw_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "sizing",
    "recommend",
    "private",
    "secret",
)

REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "config",
    "observation_count",
    "row_count",
    "average_scrapling_claim_score",
    "average_authority_claim_score",
    "average_claim_semantic_alignment_score",
    "average_claim_freshness_score",
    "average_bridge_authority_score",
    "average_dual_claim_floor_score",
    "average_claim_gap_ratio",
    "highest_claim_gap_ratio",
    "highest_contradiction_pressure_score",
    "highest_unresolved_authority_gap_score",
    "pass_count",
    "watch_count",
    "block_count",
    "status",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
CONFIG_PAYLOAD_KEYS = (
    "config_version",
    "min_pass_bridge_authority_score",
    "min_watch_bridge_authority_score",
    "min_pass_dual_claim_floor_score",
    "min_watch_dual_claim_floor_score",
    "max_pass_claim_gap_ratio",
    "max_watch_claim_gap_ratio",
    "max_pass_contradiction_pressure_score",
    "max_watch_contradiction_pressure_score",
    "max_pass_unresolved_authority_gap_score",
    "max_watch_unresolved_authority_gap_score",
    "bridge_claim_consensus_weight",
    "bridge_semantic_alignment_weight",
    "bridge_freshness_weight",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "row_index",
    "observed_at",
    "scrapling_claim_capture_score",
    "scrapling_claim_extraction_score",
    "authority_claim_match_score",
    "authority_source_confidence_score",
    "scrapling_claim_score",
    "authority_claim_score",
    "claim_semantic_alignment_score",
    "claim_freshness_score",
    "contradiction_pressure_score",
    "unresolved_authority_gap_score",
    "claim_gap_ratio",
    "dual_claim_floor_score",
    "bridge_authority_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_CODE_COUNT_PAYLOAD_KEYS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_CLAIM_BRIDGE_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_SCRAPLING_AUTHORITY_CLAIM_BRIDGE_STATUSES",
    "ResearchSourceScraplingAuthorityClaimBridgeConfig",
    "ResearchSourceScraplingAuthorityClaimBridgeObservation",
    "ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount",
    "ResearchSourceScraplingAuthorityClaimBridgeReport",
    "ResearchSourceScraplingAuthorityClaimBridgeRow",
    "build_research_source_scrapling_authority_claim_bridge_report",
    "research_source_scrapling_authority_claim_bridge_report_digest",
    "research_source_scrapling_authority_claim_bridge_report_payload",
    "validate_research_source_scrapling_authority_claim_bridge_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceScraplingAuthorityClaimBridgeConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_CLAIM_BRIDGE_REPORT_CONFIG_VERSION
    )
    min_pass_bridge_authority_score: Decimal = Decimal("0.850000")
    min_watch_bridge_authority_score: Decimal = Decimal("0.550000")
    min_pass_dual_claim_floor_score: Decimal = Decimal("0.750000")
    min_watch_dual_claim_floor_score: Decimal = Decimal("0.500000")
    max_pass_claim_gap_ratio: Decimal = Decimal("0.100000")
    max_watch_claim_gap_ratio: Decimal = Decimal("0.300000")
    max_pass_contradiction_pressure_score: Decimal = Decimal("0.100000")
    max_watch_contradiction_pressure_score: Decimal = Decimal("0.350000")
    max_pass_unresolved_authority_gap_score: Decimal = Decimal("0.100000")
    max_watch_unresolved_authority_gap_score: Decimal = Decimal("0.300000")
    bridge_claim_consensus_weight: Decimal = Decimal("0.500000")
    bridge_semantic_alignment_weight: Decimal = Decimal("0.320313")
    bridge_freshness_weight: Decimal = Decimal("0.179687")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAuthorityClaimBridgeConfig:
            raise TypeError(
                "ResearchSourceScraplingAuthorityClaimBridgeConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingAuthorityClaimBridgeConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_CLAIM_BRIDGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_bridge_authority_score",
            "min_watch_bridge_authority_score",
            "min_pass_dual_claim_floor_score",
            "min_watch_dual_claim_floor_score",
            "max_pass_claim_gap_ratio",
            "max_watch_claim_gap_ratio",
            "max_pass_contradiction_pressure_score",
            "max_watch_contradiction_pressure_score",
            "max_pass_unresolved_authority_gap_score",
            "max_watch_unresolved_authority_gap_score",
            "bridge_claim_consensus_weight",
            "bridge_semantic_alignment_weight",
            "bridge_freshness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_ordered_floor(
            "bridge authority score",
            self.min_watch_bridge_authority_score,
            self.min_pass_bridge_authority_score,
        )
        _require_ordered_floor(
            "dual claim floor",
            self.min_watch_dual_claim_floor_score,
            self.min_pass_dual_claim_floor_score,
        )
        _require_ordered_ceiling(
            "claim gap",
            self.max_pass_claim_gap_ratio,
            self.max_watch_claim_gap_ratio,
        )
        _require_ordered_ceiling(
            "contradiction pressure",
            self.max_pass_contradiction_pressure_score,
            self.max_watch_contradiction_pressure_score,
        )
        _require_ordered_ceiling(
            "unresolved authority gap",
            self.max_pass_unresolved_authority_gap_score,
            self.max_watch_unresolved_authority_gap_score,
        )
        with localcontext(_DECIMAL_CONTEXT):
            weight_sum = _quantize(
                self.bridge_claim_consensus_weight
                + self.bridge_semantic_alignment_weight
                + self.bridge_freshness_weight,
            )
        if weight_sum != ONE:
            raise ValueError("bridge authority weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAuthorityClaimBridgeObservation:
    private_bridge_ref: str
    observed_at: datetime
    scrapling_claim_capture_score: Decimal
    scrapling_claim_extraction_score: Decimal
    authority_claim_match_score: Decimal
    authority_source_confidence_score: Decimal
    claim_semantic_alignment_score: Decimal
    claim_freshness_score: Decimal
    contradiction_pressure_score: Decimal
    unresolved_authority_gap_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAuthorityClaimBridgeObservation:
            raise TypeError(
                "ResearchSourceScraplingAuthorityClaimBridgeObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingAuthorityClaimBridgeObservation,
            "observation",
        )
        _require_private_string("private_bridge_ref", self.private_bridge_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "scrapling_claim_capture_score",
            "scrapling_claim_extraction_score",
            "authority_claim_match_score",
            "authority_source_confidence_score",
            "claim_semantic_alignment_score",
            "claim_freshness_score",
            "contradiction_pressure_score",
            "unresolved_authority_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAuthorityClaimBridgeRow:
    row_index: Decimal
    observed_at: datetime
    scrapling_claim_capture_score: Decimal
    scrapling_claim_extraction_score: Decimal
    authority_claim_match_score: Decimal
    authority_source_confidence_score: Decimal
    scrapling_claim_score: Decimal
    authority_claim_score: Decimal
    claim_semantic_alignment_score: Decimal
    claim_freshness_score: Decimal
    contradiction_pressure_score: Decimal
    unresolved_authority_gap_score: Decimal
    claim_gap_ratio: Decimal
    dual_claim_floor_score: Decimal
    bridge_authority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAuthorityClaimBridgeRow:
            raise TypeError(
                "ResearchSourceScraplingAuthorityClaimBridgeRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraplingAuthorityClaimBridgeRow, "row")
        object.__setattr__(
            self,
            "row_index",
            _normalize_positive_count("row_index", self.row_index),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "scrapling_claim_capture_score",
            "scrapling_claim_extraction_score",
            "authority_claim_match_score",
            "authority_source_confidence_score",
            "scrapling_claim_score",
            "authority_claim_score",
            "claim_semantic_alignment_score",
            "claim_freshness_score",
            "contradiction_pressure_score",
            "unresolved_authority_gap_score",
            "claim_gap_ratio",
            "dual_claim_floor_score",
            "bridge_authority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.status != _status_from_reasons(self.reason_codes):
            raise ValueError("row status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount:
            raise TypeError(
                "ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _normalize_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAuthorityClaimBridgeReport:
    generated_at: datetime
    config_version: str
    config: ResearchSourceScraplingAuthorityClaimBridgeConfig
    observation_count: Decimal
    row_count: Decimal
    average_scrapling_claim_score: Decimal
    average_authority_claim_score: Decimal
    average_claim_semantic_alignment_score: Decimal
    average_claim_freshness_score: Decimal
    average_bridge_authority_score: Decimal
    average_dual_claim_floor_score: Decimal
    average_claim_gap_ratio: Decimal
    highest_claim_gap_ratio: Decimal
    highest_contradiction_pressure_score: Decimal
    highest_unresolved_authority_gap_score: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchSourceScraplingAuthorityClaimBridgeRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAuthorityClaimBridgeReport:
            raise TypeError(
                "ResearchSourceScraplingAuthorityClaimBridgeReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingAuthorityClaimBridgeReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_CLAIM_BRIDGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(self, "config", _require_config(self.config))
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
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_scrapling_claim_score",
            "average_authority_claim_score",
            "average_claim_semantic_alignment_score",
            "average_claim_freshness_score",
            "average_bridge_authority_score",
            "average_dual_claim_floor_score",
            "average_claim_gap_ratio",
            "highest_claim_gap_ratio",
            "highest_contradiction_pressure_score",
            "highest_unresolved_authority_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_scrapling_authority_claim_bridge_report_payload(self)


def build_research_source_scrapling_authority_claim_bridge_report(
    observations: Sequence[ResearchSourceScraplingAuthorityClaimBridgeObservation],
    *,
    config: ResearchSourceScraplingAuthorityClaimBridgeConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceScraplingAuthorityClaimBridgeReport:
    cfg = (
        ResearchSourceScraplingAuthorityClaimBridgeConfig()
        if config is None
        else _require_config(config)
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        _row_from_observation(
            row_index=_decimal_from_int(index),
            observation=observation,
            config=cfg,
            generated_at=generated_at_utc,
        )
        for index, observation in enumerate(
            sorted(normalized_observations, key=_observation_sort_key),
            start=1,
        )
    )
    return ResearchSourceScraplingAuthorityClaimBridgeReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        config=cfg,
        observation_count=_decimal_from_int(len(normalized_observations)),
        row_count=_decimal_from_int(len(rows)),
        average_scrapling_claim_score=_average_probability(
            tuple(row.scrapling_claim_score for row in rows),
        ),
        average_authority_claim_score=_average_probability(
            tuple(row.authority_claim_score for row in rows),
        ),
        average_claim_semantic_alignment_score=_average_probability(
            tuple(row.claim_semantic_alignment_score for row in rows),
        ),
        average_claim_freshness_score=_average_probability(
            tuple(row.claim_freshness_score for row in rows),
        ),
        average_bridge_authority_score=_average_probability(
            tuple(row.bridge_authority_score for row in rows),
        ),
        average_dual_claim_floor_score=_average_probability(
            tuple(row.dual_claim_floor_score for row in rows),
        ),
        average_claim_gap_ratio=_average_probability(
            tuple(row.claim_gap_ratio for row in rows),
        ),
        highest_claim_gap_ratio=_max_probability(tuple(row.claim_gap_ratio for row in rows)),
        highest_contradiction_pressure_score=_max_probability(
            tuple(row.contradiction_pressure_score for row in rows),
        ),
        highest_unresolved_authority_gap_score=_max_probability(
            tuple(row.unresolved_authority_gap_score for row in rows),
        ),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_source_scrapling_authority_claim_bridge_report_payload(
    value: ResearchSourceScraplingAuthorityClaimBridgeReport | Mapping[str, object],
) -> dict[str, Any]:
    if type(value) is ResearchSourceScraplingAuthorityClaimBridgeReport:
        _require_hard_flags("report", value)
        _validate_report_digest(value)
        payload = _json_ready(asdict(value))
    elif isinstance(value, Mapping):
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchSourceScraplingAuthorityClaimBridgeReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_schema(payload)
    _validate_status_values_in_payload(payload)
    _validate_public_payload_digest(payload)
    _report_from_public_payload(payload)
    return payload


def research_source_scrapling_authority_claim_bridge_report_digest(
    report: ResearchSourceScraplingAuthorityClaimBridgeReport,
) -> str:
    _require_exact_type(report, ResearchSourceScraplingAuthorityClaimBridgeReport, "report")
    _require_hard_flags("report", report)
    return _report_digest_from_values(_report_values_without_digest(report))


def validate_research_source_scrapling_authority_claim_bridge_report_payload(
    payload: Mapping[str, object],
) -> bool:
    try:
        research_source_scrapling_authority_claim_bridge_report_payload(payload)
    except ValueError:
        return False
    return True


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_exact_payload_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    config = _require_payload_dict("report config", payload["config"])
    _require_exact_payload_keys("report config", config, CONFIG_PAYLOAD_KEYS)
    _require_payload_list("report reason_codes", payload["reason_codes"])
    rows = _require_payload_list("report rows", payload["rows"])
    for index, row in enumerate(rows):
        row_payload = _require_payload_dict(f"rows[{index}]", row)
        _require_exact_payload_keys(f"rows[{index}]", row_payload, ROW_PAYLOAD_KEYS)
        _require_payload_list(f"rows[{index}].reason_codes", row_payload["reason_codes"])
    reason_code_counts = _require_payload_list(
        "report reason_code_counts",
        payload["reason_code_counts"],
    )
    for index, reason_code_count in enumerate(reason_code_counts):
        count_payload = _require_payload_dict(
            f"reason_code_counts[{index}]",
            reason_code_count,
        )
        _require_exact_payload_keys(
            f"reason_code_counts[{index}]",
            count_payload,
            REASON_CODE_COUNT_PAYLOAD_KEYS,
        )


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceScraplingAuthorityClaimBridgeReport:
    return ResearchSourceScraplingAuthorityClaimBridgeReport(
        generated_at=_datetime_from_payload("generated_at", payload["generated_at"]),
        config_version=_string_from_payload("config_version", payload["config_version"]),
        config=_config_from_public_payload(payload["config"]),
        observation_count=_decimal_from_payload(
            "observation_count",
            payload["observation_count"],
        ),
        row_count=_decimal_from_payload("row_count", payload["row_count"]),
        average_scrapling_claim_score=_decimal_from_payload(
            "average_scrapling_claim_score",
            payload["average_scrapling_claim_score"],
        ),
        average_authority_claim_score=_decimal_from_payload(
            "average_authority_claim_score",
            payload["average_authority_claim_score"],
        ),
        average_claim_semantic_alignment_score=_decimal_from_payload(
            "average_claim_semantic_alignment_score",
            payload["average_claim_semantic_alignment_score"],
        ),
        average_claim_freshness_score=_decimal_from_payload(
            "average_claim_freshness_score",
            payload["average_claim_freshness_score"],
        ),
        average_bridge_authority_score=_decimal_from_payload(
            "average_bridge_authority_score",
            payload["average_bridge_authority_score"],
        ),
        average_dual_claim_floor_score=_decimal_from_payload(
            "average_dual_claim_floor_score",
            payload["average_dual_claim_floor_score"],
        ),
        average_claim_gap_ratio=_decimal_from_payload(
            "average_claim_gap_ratio",
            payload["average_claim_gap_ratio"],
        ),
        highest_claim_gap_ratio=_decimal_from_payload(
            "highest_claim_gap_ratio",
            payload["highest_claim_gap_ratio"],
        ),
        highest_contradiction_pressure_score=_decimal_from_payload(
            "highest_contradiction_pressure_score",
            payload["highest_contradiction_pressure_score"],
        ),
        highest_unresolved_authority_gap_score=_decimal_from_payload(
            "highest_unresolved_authority_gap_score",
            payload["highest_unresolved_authority_gap_score"],
        ),
        pass_count=_decimal_from_payload("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_payload("watch_count", payload["watch_count"]),
        block_count=_decimal_from_payload("block_count", payload["block_count"]),
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
            _row_from_public_payload(value)
            for value in _require_payload_list("rows", payload["rows"])
        ),
        derived_validation_digest=_string_from_payload(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _config_from_public_payload(
    value: object,
) -> ResearchSourceScraplingAuthorityClaimBridgeConfig:
    payload = _require_payload_dict("config payload", value)
    return ResearchSourceScraplingAuthorityClaimBridgeConfig(
        config_version=_string_from_payload("config_version", payload["config_version"]),
        min_pass_bridge_authority_score=_decimal_from_payload(
            "min_pass_bridge_authority_score",
            payload["min_pass_bridge_authority_score"],
        ),
        min_watch_bridge_authority_score=_decimal_from_payload(
            "min_watch_bridge_authority_score",
            payload["min_watch_bridge_authority_score"],
        ),
        min_pass_dual_claim_floor_score=_decimal_from_payload(
            "min_pass_dual_claim_floor_score",
            payload["min_pass_dual_claim_floor_score"],
        ),
        min_watch_dual_claim_floor_score=_decimal_from_payload(
            "min_watch_dual_claim_floor_score",
            payload["min_watch_dual_claim_floor_score"],
        ),
        max_pass_claim_gap_ratio=_decimal_from_payload(
            "max_pass_claim_gap_ratio",
            payload["max_pass_claim_gap_ratio"],
        ),
        max_watch_claim_gap_ratio=_decimal_from_payload(
            "max_watch_claim_gap_ratio",
            payload["max_watch_claim_gap_ratio"],
        ),
        max_pass_contradiction_pressure_score=_decimal_from_payload(
            "max_pass_contradiction_pressure_score",
            payload["max_pass_contradiction_pressure_score"],
        ),
        max_watch_contradiction_pressure_score=_decimal_from_payload(
            "max_watch_contradiction_pressure_score",
            payload["max_watch_contradiction_pressure_score"],
        ),
        max_pass_unresolved_authority_gap_score=_decimal_from_payload(
            "max_pass_unresolved_authority_gap_score",
            payload["max_pass_unresolved_authority_gap_score"],
        ),
        max_watch_unresolved_authority_gap_score=_decimal_from_payload(
            "max_watch_unresolved_authority_gap_score",
            payload["max_watch_unresolved_authority_gap_score"],
        ),
        bridge_claim_consensus_weight=_decimal_from_payload(
            "bridge_claim_consensus_weight",
            payload["bridge_claim_consensus_weight"],
        ),
        bridge_semantic_alignment_weight=_decimal_from_payload(
            "bridge_semantic_alignment_weight",
            payload["bridge_semantic_alignment_weight"],
        ),
        bridge_freshness_weight=_decimal_from_payload(
            "bridge_freshness_weight",
            payload["bridge_freshness_weight"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(
    value: object,
) -> ResearchSourceScraplingAuthorityClaimBridgeRow:
    payload = _require_payload_dict("row payload", value)
    return ResearchSourceScraplingAuthorityClaimBridgeRow(
        row_index=_decimal_from_payload("row_index", payload["row_index"]),
        observed_at=_datetime_from_payload("observed_at", payload["observed_at"]),
        scrapling_claim_capture_score=_decimal_from_payload(
            "scrapling_claim_capture_score",
            payload["scrapling_claim_capture_score"],
        ),
        scrapling_claim_extraction_score=_decimal_from_payload(
            "scrapling_claim_extraction_score",
            payload["scrapling_claim_extraction_score"],
        ),
        authority_claim_match_score=_decimal_from_payload(
            "authority_claim_match_score",
            payload["authority_claim_match_score"],
        ),
        authority_source_confidence_score=_decimal_from_payload(
            "authority_source_confidence_score",
            payload["authority_source_confidence_score"],
        ),
        scrapling_claim_score=_decimal_from_payload(
            "scrapling_claim_score",
            payload["scrapling_claim_score"],
        ),
        authority_claim_score=_decimal_from_payload(
            "authority_claim_score",
            payload["authority_claim_score"],
        ),
        claim_semantic_alignment_score=_decimal_from_payload(
            "claim_semantic_alignment_score",
            payload["claim_semantic_alignment_score"],
        ),
        claim_freshness_score=_decimal_from_payload(
            "claim_freshness_score",
            payload["claim_freshness_score"],
        ),
        contradiction_pressure_score=_decimal_from_payload(
            "contradiction_pressure_score",
            payload["contradiction_pressure_score"],
        ),
        unresolved_authority_gap_score=_decimal_from_payload(
            "unresolved_authority_gap_score",
            payload["unresolved_authority_gap_score"],
        ),
        claim_gap_ratio=_decimal_from_payload(
            "claim_gap_ratio",
            payload["claim_gap_ratio"],
        ),
        dual_claim_floor_score=_decimal_from_payload(
            "dual_claim_floor_score",
            payload["dual_claim_floor_score"],
        ),
        bridge_authority_score=_decimal_from_payload(
            "bridge_authority_score",
            payload["bridge_authority_score"],
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


def _reason_code_count_from_public_payload(
    value: object,
) -> ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount:
    payload = _require_payload_dict("reason code count payload", value)
    return ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount(
        reason_code=_string_from_payload("reason_code", payload["reason_code"]),
        count=_decimal_from_payload("count", payload["count"]),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _constructor_values(value: object) -> dict[str, object]:
    return {
        field.name: getattr(value, field.name)
        for field in fields(value)
    }


def _require_config(
    config: ResearchSourceScraplingAuthorityClaimBridgeConfig,
) -> ResearchSourceScraplingAuthorityClaimBridgeConfig:
    _require_exact_type(config, ResearchSourceScraplingAuthorityClaimBridgeConfig, "config")
    return ResearchSourceScraplingAuthorityClaimBridgeConfig(
        **_constructor_values(config),
    )


def _normalize_observations(
    observations: Sequence[ResearchSourceScraplingAuthorityClaimBridgeObservation],
) -> tuple[ResearchSourceScraplingAuthorityClaimBridgeObservation, ...]:
    if isinstance(observations, (str, bytes, dict)):
        raise ValueError("observations must be a sequence of authority claim bridge observations")
    normalized: list[ResearchSourceScraplingAuthorityClaimBridgeObservation] = []
    for observation in observations:
        _require_exact_type(
            observation,
            ResearchSourceScraplingAuthorityClaimBridgeObservation,
            "observation",
        )
        normalized.append(
            ResearchSourceScraplingAuthorityClaimBridgeObservation(
                **_constructor_values(observation),
            ),
        )
    return tuple(normalized)


def _observation_sort_key(
    observation: ResearchSourceScraplingAuthorityClaimBridgeObservation,
) -> tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        observation.observed_at.isoformat(),
        observation.scrapling_claim_capture_score,
        observation.scrapling_claim_extraction_score,
        observation.authority_claim_match_score,
        observation.authority_source_confidence_score,
        observation.claim_semantic_alignment_score,
        observation.claim_freshness_score,
        observation.contradiction_pressure_score,
        observation.unresolved_authority_gap_score,
    )


def _row_sort_key(
    row: ResearchSourceScraplingAuthorityClaimBridgeRow,
) -> tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        row.observed_at.isoformat(),
        row.scrapling_claim_capture_score,
        row.scrapling_claim_extraction_score,
        row.authority_claim_match_score,
        row.authority_source_confidence_score,
        row.claim_semantic_alignment_score,
        row.claim_freshness_score,
        row.contradiction_pressure_score,
        row.unresolved_authority_gap_score,
    )


def _row_from_observation(
    *,
    row_index: Decimal,
    observation: ResearchSourceScraplingAuthorityClaimBridgeObservation,
    config: ResearchSourceScraplingAuthorityClaimBridgeConfig,
    generated_at: datetime,
) -> ResearchSourceScraplingAuthorityClaimBridgeRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    with localcontext(_DECIMAL_CONTEXT):
        scrapling_claim_score = _average_probability(
            (
                observation.scrapling_claim_capture_score,
                observation.scrapling_claim_extraction_score,
            ),
        )
        authority_claim_score = _average_probability(
            (
                observation.authority_claim_match_score,
                observation.authority_source_confidence_score,
            ),
        )
        claim_gap_ratio = _normalize_probability(
            "claim_gap_ratio",
            abs(
                observation.scrapling_claim_capture_score
                - observation.authority_claim_match_score
            )
            / Decimal("2.000000"),
        )
        dual_claim_floor_score = min(scrapling_claim_score, authority_claim_score)
        bridge_authority_score = _bridge_authority_score(
            scrapling_claim_score=scrapling_claim_score,
            authority_claim_score=authority_claim_score,
            claim_semantic_alignment_score=observation.claim_semantic_alignment_score,
            claim_freshness_score=observation.claim_freshness_score,
            config=config,
        )
    reason_codes = _row_reason_codes(
        bridge_authority_score=bridge_authority_score,
        dual_claim_floor_score=dual_claim_floor_score,
        claim_gap_ratio=claim_gap_ratio,
        contradiction_pressure_score=observation.contradiction_pressure_score,
        unresolved_authority_gap_score=observation.unresolved_authority_gap_score,
        config=config,
    )
    return ResearchSourceScraplingAuthorityClaimBridgeRow(
        row_index=row_index,
        observed_at=observation.observed_at,
        scrapling_claim_capture_score=observation.scrapling_claim_capture_score,
        scrapling_claim_extraction_score=observation.scrapling_claim_extraction_score,
        authority_claim_match_score=observation.authority_claim_match_score,
        authority_source_confidence_score=observation.authority_source_confidence_score,
        scrapling_claim_score=scrapling_claim_score,
        authority_claim_score=authority_claim_score,
        claim_semantic_alignment_score=observation.claim_semantic_alignment_score,
        claim_freshness_score=observation.claim_freshness_score,
        contradiction_pressure_score=observation.contradiction_pressure_score,
        unresolved_authority_gap_score=observation.unresolved_authority_gap_score,
        claim_gap_ratio=claim_gap_ratio,
        dual_claim_floor_score=dual_claim_floor_score,
        bridge_authority_score=bridge_authority_score,
        status=_status_from_reasons(reason_codes),
        reason_codes=reason_codes,
    )


def _bridge_authority_score(
    *,
    scrapling_claim_score: Decimal,
    authority_claim_score: Decimal,
    claim_semantic_alignment_score: Decimal,
    claim_freshness_score: Decimal,
    config: ResearchSourceScraplingAuthorityClaimBridgeConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        claim_consensus_score = _average_probability(
            (scrapling_claim_score, authority_claim_score),
        )
        return _normalize_probability(
            "bridge_authority_score",
            claim_consensus_score * config.bridge_claim_consensus_weight
            + claim_semantic_alignment_score * config.bridge_semantic_alignment_weight
            + claim_freshness_score * config.bridge_freshness_weight,
        )


def _row_reason_codes(
    *,
    bridge_authority_score: Decimal,
    dual_claim_floor_score: Decimal,
    claim_gap_ratio: Decimal,
    contradiction_pressure_score: Decimal,
    unresolved_authority_gap_score: Decimal,
    config: ResearchSourceScraplingAuthorityClaimBridgeConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    if bridge_authority_score < config.min_watch_bridge_authority_score:
        block_reasons.append(BRIDGE_SCORE_BLOCK_REASON)
    if dual_claim_floor_score < config.min_watch_dual_claim_floor_score:
        block_reasons.append(DUAL_CLAIM_FLOOR_BLOCK_REASON)
    if claim_gap_ratio > config.max_watch_claim_gap_ratio:
        block_reasons.append(CLAIM_GAP_BLOCK_REASON)
    if contradiction_pressure_score > config.max_watch_contradiction_pressure_score:
        block_reasons.append(CONTRADICTION_BLOCK_REASON)
    if unresolved_authority_gap_score > config.max_watch_unresolved_authority_gap_score:
        block_reasons.append(UNRESOLVED_GAP_BLOCK_REASON)
    if block_reasons:
        return _normalize_reason_codes(tuple(block_reasons))

    watch_reasons: list[str] = []
    if bridge_authority_score < config.min_pass_bridge_authority_score:
        watch_reasons.append(BRIDGE_SCORE_WATCH_REASON)
    if dual_claim_floor_score < config.min_pass_dual_claim_floor_score:
        watch_reasons.append(DUAL_CLAIM_FLOOR_WATCH_REASON)
    if claim_gap_ratio > config.max_pass_claim_gap_ratio:
        watch_reasons.append(CLAIM_GAP_WATCH_REASON)
    if contradiction_pressure_score > config.max_pass_contradiction_pressure_score:
        watch_reasons.append(CONTRADICTION_WATCH_REASON)
    if unresolved_authority_gap_score > config.max_pass_unresolved_authority_gap_score:
        watch_reasons.append(UNRESOLVED_GAP_WATCH_REASON)
    return _normalize_reason_codes(tuple(watch_reasons))


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchSourceScraplingAuthorityClaimBridgeRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchSourceScraplingAuthorityClaimBridgeRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    detail_reasons = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    }
    if detail_reasons:
        return tuple(
            reason_code
            for reason_code in REASON_CODE_SEQUENCE
            if reason_code in detail_reasons
        )
    return (PASS_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchSourceScraplingAuthorityClaimBridgeRow, ...],
) -> tuple[ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=Decimal("1.000000"),
            ),
        )
    report_reasons = tuple(
        reason_code
        for row in rows
        for reason_code in (row.reason_codes or (PASS_REASON,))
    )
    counts = Counter(report_reasons)
    return tuple(
        ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_from_int(counts[reason_code]),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if counts[reason_code] > 0
    )


def _validate_report_consistency(
    report: ResearchSourceScraplingAuthorityClaimBridgeReport,
) -> None:
    row_sort_keys = tuple(_row_sort_key(row) for row in report.rows)
    if row_sort_keys != tuple(sorted(row_sort_keys)):
        raise ValueError("rows must use canonical stable ordering")
    for index, row in enumerate(report.rows, start=1):
        if row.row_index != _decimal_from_int(index):
            raise ValueError("row_index must match canonical row rank")
        _validate_row_consistency(
            row,
            config=report.config,
            generated_at=report.generated_at,
        )
    if report.observation_count != _decimal_from_int(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.row_count != _decimal_from_int(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.average_scrapling_claim_score != _average_probability(
        tuple(row.scrapling_claim_score for row in report.rows),
    ):
        raise ValueError("average_scrapling_claim_score must match rows")
    if report.average_authority_claim_score != _average_probability(
        tuple(row.authority_claim_score for row in report.rows),
    ):
        raise ValueError("average_authority_claim_score must match rows")
    if report.average_claim_semantic_alignment_score != _average_probability(
        tuple(row.claim_semantic_alignment_score for row in report.rows),
    ):
        raise ValueError("average_claim_semantic_alignment_score must match rows")
    if report.average_claim_freshness_score != _average_probability(
        tuple(row.claim_freshness_score for row in report.rows),
    ):
        raise ValueError("average_claim_freshness_score must match rows")
    if report.average_bridge_authority_score != _average_probability(
        tuple(row.bridge_authority_score for row in report.rows),
    ):
        raise ValueError("average_bridge_authority_score must match rows")
    if report.average_dual_claim_floor_score != _average_probability(
        tuple(row.dual_claim_floor_score for row in report.rows),
    ):
        raise ValueError("average_dual_claim_floor_score must match rows")
    if report.average_claim_gap_ratio != _average_probability(
        tuple(row.claim_gap_ratio for row in report.rows),
    ):
        raise ValueError("average_claim_gap_ratio must match rows")
    if report.highest_claim_gap_ratio != _max_probability(
        tuple(row.claim_gap_ratio for row in report.rows),
    ):
        raise ValueError("highest_claim_gap_ratio must match rows")
    if report.highest_contradiction_pressure_score != _max_probability(
        tuple(row.contradiction_pressure_score for row in report.rows),
    ):
        raise ValueError("highest_contradiction_pressure_score must match rows")
    if report.highest_unresolved_authority_gap_score != _max_probability(
        tuple(row.unresolved_authority_gap_score for row in report.rows),
    ):
        raise ValueError("highest_unresolved_authority_gap_score must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _validate_row_consistency(
    row: ResearchSourceScraplingAuthorityClaimBridgeRow,
    *,
    config: ResearchSourceScraplingAuthorityClaimBridgeConfig,
    generated_at: datetime,
) -> None:
    if row.observed_at > generated_at:
        raise ValueError("row observed_at must not be after generated_at")
    with localcontext(_DECIMAL_CONTEXT):
        scrapling_claim_score = _average_probability(
            (
                row.scrapling_claim_capture_score,
                row.scrapling_claim_extraction_score,
            ),
        )
        authority_claim_score = _average_probability(
            (
                row.authority_claim_match_score,
                row.authority_source_confidence_score,
            ),
        )
        claim_gap_ratio = _normalize_probability(
            "claim_gap_ratio",
            abs(
                row.scrapling_claim_capture_score
                - row.authority_claim_match_score
            )
            / Decimal("2.000000"),
        )
        dual_claim_floor_score = min(
            scrapling_claim_score,
            authority_claim_score,
        )
        bridge_authority_score = _bridge_authority_score(
            scrapling_claim_score=scrapling_claim_score,
            authority_claim_score=authority_claim_score,
            claim_semantic_alignment_score=row.claim_semantic_alignment_score,
            claim_freshness_score=row.claim_freshness_score,
            config=config,
        )
    reason_codes = _row_reason_codes(
        bridge_authority_score=bridge_authority_score,
        dual_claim_floor_score=dual_claim_floor_score,
        claim_gap_ratio=claim_gap_ratio,
        contradiction_pressure_score=row.contradiction_pressure_score,
        unresolved_authority_gap_score=row.unresolved_authority_gap_score,
        config=config,
    )
    expected_values = (
        ("scrapling_claim_score", row.scrapling_claim_score, scrapling_claim_score),
        ("authority_claim_score", row.authority_claim_score, authority_claim_score),
        ("claim_gap_ratio", row.claim_gap_ratio, claim_gap_ratio),
        ("dual_claim_floor_score", row.dual_claim_floor_score, dual_claim_floor_score),
        ("bridge_authority_score", row.bridge_authority_score, bridge_authority_score),
    )
    for field_name, actual, expected in expected_values:
        if actual != expected:
            raise ValueError(f"{field_name} must match public bridge evidence")
    if row.reason_codes != reason_codes:
        raise ValueError("row reason_codes must match public bridge evidence and config")
    if row.status != _status_from_reasons(reason_codes):
        raise ValueError("row status must match public bridge evidence and config")


def _status_count(
    rows: tuple[ResearchSourceScraplingAuthorityClaimBridgeRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.status == status))


def _average_probability(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _normalize_probability(
            "average_probability",
            sum(values, ZERO) / _decimal_from_int(len(values)),
        )


def _max_probability(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_probability("max_probability", max(values))


def _require_ordered_floor(label: str, watch_value: Decimal, pass_value: Decimal) -> None:
    if watch_value > pass_value:
        raise ValueError(f"{label} watch threshold must not exceed pass threshold")


def _require_ordered_ceiling(label: str, pass_value: Decimal, watch_value: Decimal) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{label} pass threshold must not exceed watch threshold")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSourceScraplingAuthorityClaimBridgeRow, ...]:
    if isinstance(rows, (str, bytes, dict)):
        raise ValueError("rows must be a tuple of authority claim bridge rows")
    normalized: list[ResearchSourceScraplingAuthorityClaimBridgeRow] = []
    for row in rows:  # type: ignore[union-attr]
        _require_exact_type(row, ResearchSourceScraplingAuthorityClaimBridgeRow, "row")
        normalized.append(
            ResearchSourceScraplingAuthorityClaimBridgeRow(
                **_constructor_values(row),
            ),
        )
    return tuple(normalized)


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes, dict)):
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount] = []
    for item in counts:  # type: ignore[union-attr]
        _require_exact_type(
            item,
            ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount,
            "reason_code_count",
        )
        normalized.append(
            ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount(
                **_constructor_values(item),
            ),
        )
    return tuple(normalized)


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    for reason_code in normalized:
        _normalize_reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _normalize_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_status(field_name: str, value: object) -> None:
    _require_public_identifier(field_name, value)
    if value not in RESEARCH_SOURCE_SCRAPLING_AUTHORITY_CLAIM_BRIDGE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a safe public identifier")
    _reject_unsafe_public_string(field_name, value, key=False)


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if raw_value != raw_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize(raw_value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw_value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < ZERO or raw_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(raw_value)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _quantize(_require_decimal(field_name, value))


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _decimal_from_int(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _validate_report_digest(report: ResearchSourceScraplingAuthorityClaimBridgeReport) -> None:
    _require_exact_type(report, ResearchSourceScraplingAuthorityClaimBridgeReport, "report")
    _require_hard_flags("report", report)
    expected_digest = research_source_scrapling_authority_claim_bridge_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_public_payload_digest(payload: Mapping[str, object]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    values = dict(payload)
    values.pop("derived_validation_digest", None)
    expected_digest = _report_digest_from_values(values)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest must match payload")


def _report_values_without_digest(
    report: ResearchSourceScraplingAuthorityClaimBridgeReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest_payload",
        payload,
        allow_json_containers=True,
    )
    canonical_payload = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _copy_json_object(value: Mapping[str, object]) -> dict[str, Any]:
    copied = _json_ready(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _require_exact_payload_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if tuple(value) != expected_keys:
        raise ValueError(f"{label} must use exact schema")


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
    if parsed.as_tuple().exponent != -6 or str(parsed) != value:
        raise ValueError(f"{field_name} must be a canonical six-place Decimal string")
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


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (tuple, list)):
        if not allow_json_containers and isinstance(value, list):
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value, key=False)


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"{path}.{key} contains unsafe public key text")


def _reject_unsafe_public_string(label: str, value: str, *, key: bool) -> None:
    fragments = UNSAFE_PUBLIC_KEY_FRAGMENTS if key else UNSAFE_PUBLIC_VALUE_FRAGMENTS
    lowered = value.lower()
    if any(fragment in lowered for fragment in fragments):
        raise ValueError(f"{label} contains unsafe public text")


def _validate_status_values_in_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "status":
                _require_status("status", item)
            _validate_status_values_in_payload(item)
    elif isinstance(value, list):
        for item in value:
            _validate_status_values_in_payload(item)
