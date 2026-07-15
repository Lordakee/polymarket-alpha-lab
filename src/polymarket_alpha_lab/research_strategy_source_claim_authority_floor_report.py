"""Pure report-only source claim authority floor reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, final


DEFAULT_RESEARCH_STRATEGY_SOURCE_CLAIM_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION = (
    "research-strategy-source-claim-authority-floor-report-v0"
)

SOURCE_CLAIM_AUTHORITY_FLOOR_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

NO_INPUTS_REASON = "no_source_claim_authority_inputs"
PASS_REASON = "source_claim_authority_floor_pass"
WATCH_REASON = "source_claim_authority_floor_watch"
BLOCK_REASON = "source_claim_authority_floor_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    BLOCK_REASON,
    "claim_strength_block",
    "authority_score_block",
    "corroboration_score_block",
    "freshness_score_block",
    "contradiction_pressure_block",
    WATCH_REASON,
    "claim_strength_watch",
    "authority_score_watch",
    "corroboration_score_watch",
    "freshness_score_watch",
    "contradiction_pressure_watch",
    PASS_REASON,
    "claim_strength_pass",
    "authority_score_pass",
    "corroboration_score_pass",
    "freshness_score_pass",
    "contradiction_pressure_pass",
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
DECIMAL_STRING_RE = re.compile(r"^[0-9]+\.[0-9]{6}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate://",
    "candidate_ref",
    "market_id",
    "market_slug",
    "market=",
    "source_url",
    "source_text",
    "raw_text",
    "http://",
    "https://",
    "www.",
    "dsn",
    "postgres://",
    "table",
    "token",
)

TOP_LEVEL_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_authority_floor_score",
        "min_claim_strength",
        "min_authority_score",
        "min_corroboration_score",
        "min_freshness_score",
        "max_contradiction_pressure",
        "status",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "row_label",
        "public_research_bucket",
        "claim_strength",
        "authority_score",
        "corroboration_score",
        "freshness_score",
        "contradiction_pressure",
        "authority_floor_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "row_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SOURCE_CLAIM_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION",
    "SOURCE_CLAIM_AUTHORITY_FLOOR_STATUSES",
    "ResearchStrategySourceClaimAuthorityFloorConfig",
    "ResearchStrategySourceClaimAuthorityFloorInput",
    "ResearchStrategySourceClaimAuthorityFloorReasonCodeCount",
    "ResearchStrategySourceClaimAuthorityFloorReport",
    "ResearchStrategySourceClaimAuthorityFloorRow",
    "build_research_strategy_source_claim_authority_floor_report",
    "research_strategy_source_claim_authority_floor_report_digest",
    "research_strategy_source_claim_authority_floor_report_payload",
    "validate_research_strategy_source_claim_authority_floor_report_payload",
)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySourceClaimAuthorityFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_SOURCE_CLAIM_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION
    )
    min_pass_claim_strength: Decimal = Decimal("0.800000")
    min_watch_claim_strength: Decimal = Decimal("0.550000")
    min_pass_authority_score: Decimal = Decimal("0.800000")
    min_watch_authority_score: Decimal = Decimal("0.550000")
    min_pass_corroboration_score: Decimal = Decimal("0.750000")
    min_watch_corroboration_score: Decimal = Decimal("0.500000")
    min_pass_freshness_score: Decimal = Decimal("0.700000")
    min_watch_freshness_score: Decimal = Decimal("0.500000")
    max_pass_contradiction_pressure: Decimal = Decimal("0.150000")
    max_watch_contradiction_pressure: Decimal = Decimal("0.350000")
    claim_strength_weight: Decimal = Decimal("0.300000")
    authority_score_weight: Decimal = Decimal("0.300000")
    corroboration_weight: Decimal = Decimal("0.150000")
    freshness_weight: Decimal = Decimal("0.150000")
    contradiction_relief_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        if cls is not ResearchStrategySourceClaimAuthorityFloorConfig:
            raise TypeError(
                "ResearchStrategySourceClaimAuthorityFloorConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceClaimAuthorityFloorConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_CLAIM_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_claim_strength",
            "min_watch_claim_strength",
            "min_pass_authority_score",
            "min_watch_authority_score",
            "min_pass_corroboration_score",
            "min_watch_corroboration_score",
            "min_pass_freshness_score",
            "min_watch_freshness_score",
            "max_pass_contradiction_pressure",
            "max_watch_contradiction_pressure",
            "claim_strength_weight",
            "authority_score_weight",
            "corroboration_weight",
            "freshness_weight",
            "contradiction_relief_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.min_watch_claim_strength > self.min_pass_claim_strength:
            raise ValueError("claim strength watch threshold must not exceed pass threshold")
        if self.min_watch_authority_score > self.min_pass_authority_score:
            raise ValueError("authority score watch threshold must not exceed pass threshold")
        if self.min_watch_corroboration_score > self.min_pass_corroboration_score:
            raise ValueError(
                "corroboration score watch threshold must not exceed pass threshold",
            )
        if self.min_watch_freshness_score > self.min_pass_freshness_score:
            raise ValueError("freshness score watch threshold must not exceed pass threshold")
        if self.max_pass_contradiction_pressure > self.max_watch_contradiction_pressure:
            raise ValueError(
                "contradiction pressure pass threshold must not exceed watch threshold",
            )
        weight_sum = _quantize(
            self.claim_strength_weight
            + self.authority_score_weight
            + self.corroboration_weight
            + self.freshness_weight
            + self.contradiction_relief_weight,
        )
        if weight_sum != ONE:
            raise ValueError("authority floor weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySourceClaimAuthorityFloorInput:
    private_reference: str
    public_research_bucket: str
    claim_strength: Decimal
    authority_score: Decimal
    corroboration_score: Decimal
    freshness_score: Decimal
    contradiction_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        if cls is not ResearchStrategySourceClaimAuthorityFloorInput:
            raise TypeError(
                "ResearchStrategySourceClaimAuthorityFloorInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceClaimAuthorityFloorInput, "input")
        _require_private_string("private_reference", self.private_reference)
        _require_public_identifier("public_research_bucket", self.public_research_bucket)
        for field_name in (
            "claim_strength",
            "authority_score",
            "corroboration_score",
            "freshness_score",
            "contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySourceClaimAuthorityFloorRow:
    row_label: str
    public_research_bucket: str
    claim_strength: Decimal
    authority_score: Decimal
    corroboration_score: Decimal
    freshness_score: Decimal
    contradiction_pressure: Decimal
    authority_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        if cls is not ResearchStrategySourceClaimAuthorityFloorRow:
            raise TypeError(
                "ResearchStrategySourceClaimAuthorityFloorRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceClaimAuthorityFloorRow, "row")
        _require_public_identifier("row_label", self.row_label)
        if not self.row_label.startswith("redacted-source-claim-authority-floor-"):
            raise ValueError("row_label must be redacted")
        _require_public_identifier("public_research_bucket", self.public_research_bucket)
        for field_name in (
            "claim_strength",
            "authority_score",
            "corroboration_score",
            "freshness_score",
            "contradiction_pressure",
            "authority_floor_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySourceClaimAuthorityFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        if cls is not ResearchStrategySourceClaimAuthorityFloorReasonCodeCount:
            raise TypeError(
                "ResearchStrategySourceClaimAuthorityFloorReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySourceClaimAuthorityFloorReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategySourceClaimAuthorityFloorReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_authority_floor_score: Decimal | None
    min_claim_strength: Decimal
    min_authority_score: Decimal
    min_corroboration_score: Decimal
    min_freshness_score: Decimal
    max_contradiction_pressure: Decimal
    status: str
    rows: tuple[ResearchStrategySourceClaimAuthorityFloorRow, ...]
    reason_code_counts: tuple[
        ResearchStrategySourceClaimAuthorityFloorReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        if cls is not ResearchStrategySourceClaimAuthorityFloorReport:
            raise TypeError(
                "ResearchStrategySourceClaimAuthorityFloorReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceClaimAuthorityFloorReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_CLAIM_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_authority_floor_score",
            _normalize_optional_probability(
                "average_authority_floor_score",
                self.average_authority_floor_score,
            ),
        )
        for field_name in (
            "min_claim_strength",
            "min_authority_score",
            "min_corroboration_score",
            "min_freshness_score",
            "max_contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_source_claim_authority_floor_report_payload(self)


def build_research_strategy_source_claim_authority_floor_report(
    inputs: Iterable[object],
    *,
    config: ResearchStrategySourceClaimAuthorityFloorConfig,
    generated_at: datetime,
) -> ResearchStrategySourceClaimAuthorityFloorReport:
    if type(config) is not ResearchStrategySourceClaimAuthorityFloorConfig:
        raise ValueError(
            "config must be a ResearchStrategySourceClaimAuthorityFloorConfig",
        )
    _require_hard_flags("config", config)
    _revalidate_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in input_items),
            key=_row_sort_key,
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchStrategySourceClaimAuthorityFloorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_authority_floor_score=_average_row_value(rows, "authority_floor_score"),
        min_claim_strength=_minimum_row_value(rows, "claim_strength"),
        min_authority_score=_minimum_row_value(rows, "authority_score"),
        min_corroboration_score=_minimum_row_value(rows, "corroboration_score"),
        min_freshness_score=_minimum_row_value(rows, "freshness_score"),
        max_contradiction_pressure=_maximum_row_value(rows, "contradiction_pressure"),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_source_claim_authority_floor_report_payload(
    report: ResearchStrategySourceClaimAuthorityFloorReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategySourceClaimAuthorityFloorReport:
        raise ValueError(
            "report must be a ResearchStrategySourceClaimAuthorityFloorReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    _validate_payload_shape(payload)
    return payload


def research_strategy_source_claim_authority_floor_report_digest(
    report: ResearchStrategySourceClaimAuthorityFloorReport,
) -> str:
    payload = research_strategy_source_claim_authority_floor_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest("derived_validation_digest", digest)
    return digest


def validate_research_strategy_source_claim_authority_floor_report_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        return False
    try:
        _validate_public_payload(payload)
        _validate_payload_shape(payload)
        digest = payload.get("derived_validation_digest")
        if type(digest) is not str:
            return False
        unsigned = dict(payload)
        unsigned.pop("derived_validation_digest")
        encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
        return sha256(encoded.encode("utf-8")).hexdigest() == digest
    except (TypeError, ValueError):
        return False


def _row_from_input(
    item: ResearchStrategySourceClaimAuthorityFloorInput,
    *,
    config: ResearchStrategySourceClaimAuthorityFloorConfig,
) -> ResearchStrategySourceClaimAuthorityFloorRow:
    authority_floor_score = _authority_floor_score(
        claim_strength=item.claim_strength,
        authority_score=item.authority_score,
        corroboration_score=item.corroboration_score,
        freshness_score=item.freshness_score,
        contradiction_pressure=item.contradiction_pressure,
        config=config,
    )
    status = _row_status(item, config=config)
    return ResearchStrategySourceClaimAuthorityFloorRow(
        row_label=(
            "redacted-source-claim-authority-floor-"
            f"{_private_ref_digest(item.private_reference)[:16]}"
        ),
        public_research_bucket=item.public_research_bucket,
        claim_strength=item.claim_strength,
        authority_score=item.authority_score,
        corroboration_score=item.corroboration_score,
        freshness_score=item.freshness_score,
        contradiction_pressure=item.contradiction_pressure,
        authority_floor_score=authority_floor_score,
        status=status,
        reason_codes=_row_reason_codes(item, status=status, config=config),
    )


def _authority_floor_score(
    *,
    claim_strength: Decimal,
    authority_score: Decimal,
    corroboration_score: Decimal,
    freshness_score: Decimal,
    contradiction_pressure: Decimal,
    config: ResearchStrategySourceClaimAuthorityFloorConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            claim_strength * config.claim_strength_weight
            + authority_score * config.authority_score_weight
            + corroboration_score * config.corroboration_weight
            + freshness_score * config.freshness_weight
            + (ONE - contradiction_pressure) * config.contradiction_relief_weight
        )
    return _quantize(value)


def _row_status(
    item: ResearchStrategySourceClaimAuthorityFloorInput,
    *,
    config: ResearchStrategySourceClaimAuthorityFloorConfig,
) -> str:
    if (
        item.claim_strength < config.min_watch_claim_strength
        or item.authority_score < config.min_watch_authority_score
        or item.corroboration_score < config.min_watch_corroboration_score
        or item.freshness_score < config.min_watch_freshness_score
        or item.contradiction_pressure > config.max_watch_contradiction_pressure
    ):
        return "block"
    if (
        item.claim_strength < config.min_pass_claim_strength
        or item.authority_score < config.min_pass_authority_score
        or item.corroboration_score < config.min_pass_corroboration_score
        or item.freshness_score < config.min_pass_freshness_score
        or item.contradiction_pressure > config.max_pass_contradiction_pressure
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchStrategySourceClaimAuthorityFloorInput,
    *,
    status: str,
    config: ResearchStrategySourceClaimAuthorityFloorConfig,
) -> tuple[str, ...]:
    codes = {
        f"source_claim_authority_floor_{status}",
        f"claim_strength_{_minimum_status(item.claim_strength, config.min_pass_claim_strength, config.min_watch_claim_strength)}",
        f"authority_score_{_minimum_status(item.authority_score, config.min_pass_authority_score, config.min_watch_authority_score)}",
        f"corroboration_score_{_minimum_status(item.corroboration_score, config.min_pass_corroboration_score, config.min_watch_corroboration_score)}",
        f"freshness_score_{_minimum_status(item.freshness_score, config.min_pass_freshness_score, config.min_watch_freshness_score)}",
        f"contradiction_pressure_{_maximum_status(item.contradiction_pressure, config.max_pass_contradiction_pressure, config.max_watch_contradiction_pressure)}",
    }
    for code in item.reason_codes:
        codes.add(f"input_{code}")
    return tuple(sorted(codes, key=_reason_sort_key))


def _minimum_status(value: Decimal, pass_threshold: Decimal, watch_threshold: Decimal) -> str:
    if value < watch_threshold:
        return "block"
    if value < pass_threshold:
        return "watch"
    return "pass"


def _maximum_status(value: Decimal, pass_threshold: Decimal, watch_threshold: Decimal) -> str:
    if value > watch_threshold:
        return "block"
    if value > pass_threshold:
        return "watch"
    return "pass"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchStrategySourceClaimAuthorityFloorInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchStrategySourceClaimAuthorityFloorInput:
    if type(value) is ResearchStrategySourceClaimAuthorityFloorInput:
        _require_hard_flags("input", value)
        _revalidate_input(value)
        return value
    raise ValueError("inputs must contain ResearchStrategySourceClaimAuthorityFloorInput")


def _revalidate_config(config: ResearchStrategySourceClaimAuthorityFloorConfig) -> None:
    ResearchStrategySourceClaimAuthorityFloorConfig.__post_init__(config)


def _revalidate_input(item: ResearchStrategySourceClaimAuthorityFloorInput) -> None:
    ResearchStrategySourceClaimAuthorityFloorInput.__post_init__(item)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategySourceClaimAuthorityFloorRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchStrategySourceClaimAuthorityFloorRow] = []
    for row in rows:
        if type(row) is not ResearchStrategySourceClaimAuthorityFloorRow:
            raise ValueError("rows must contain ResearchStrategySourceClaimAuthorityFloorRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    sorted_rows = tuple(sorted(normalized, key=_row_sort_key))
    if tuple(normalized) != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return sorted_rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchStrategySourceClaimAuthorityFloorReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchStrategySourceClaimAuthorityFloorReasonCodeCount] = []
    for count in counts:
        if type(count) is not ResearchStrategySourceClaimAuthorityFloorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategySourceClaimAuthorityFloorReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
        normalized.append(count)
    sorted_counts = tuple(sorted(normalized, key=lambda count: _reason_sort_key(count.reason_code)))
    if tuple(normalized) != sorted_counts:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return sorted_counts


def _summary_reason_codes(
    rows: tuple[ResearchStrategySourceClaimAuthorityFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    present = {
        code
        for row in rows
        for code in row.reason_codes
        if not code.startswith("input_")
    }
    if any(row.status != "pass" for row in rows):
        present.discard(PASS_REASON)
        present = {code for code in present if not code.endswith("_pass")}
    return tuple(sorted(present, key=_reason_sort_key))


def _summary_status(rows: tuple[ResearchStrategySourceClaimAuthorityFloorRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchStrategySourceClaimAuthorityFloorRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategySourceClaimAuthorityFloorReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategySourceClaimAuthorityFloorReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter(
        code for row in rows for code in row.reason_codes if code in reason_codes
    )
    total = _decimal_count(len(rows))
    return tuple(
        ResearchStrategySourceClaimAuthorityFloorReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
            row_ratio=_ratio(_decimal_count(counter[reason_code]), total),
        )
        for reason_code in reason_codes
        if counter[reason_code] > 0
    )


def _status_count(
    rows: tuple[ResearchStrategySourceClaimAuthorityFloorRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(row: ResearchStrategySourceClaimAuthorityFloorRow) -> tuple[str, int, str]:
    return (
        row.public_research_bucket,
        SOURCE_CLAIM_AUTHORITY_FLOOR_STATUSES.index(row.status),
        row.row_label,
    )


def _average_row_value(
    rows: tuple[ResearchStrategySourceClaimAuthorityFloorRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum((getattr(row, field_name) for row in rows), ZERO) / Decimal(len(rows)))


def _minimum_row_value(
    rows: tuple[ResearchStrategySourceClaimAuthorityFloorRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _maximum_row_value(
    rows: tuple[ResearchStrategySourceClaimAuthorityFloorRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _validate_row_consistency(row: ResearchStrategySourceClaimAuthorityFloorRow) -> None:
    expected_status_codes = tuple(
        code
        for code in row.reason_codes
        if code in {PASS_REASON, WATCH_REASON, BLOCK_REASON}
    )
    if expected_status_codes != (f"source_claim_authority_floor_{row.status}",):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchStrategySourceClaimAuthorityFloorReport,
) -> None:
    rows = report.rows
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must match rows")
    expected_counts = {
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.average_authority_floor_score != _average_row_value(
        rows,
        "authority_floor_score",
    ):
        raise ValueError("average_authority_floor_score must match rows")
    if report.min_claim_strength != _minimum_row_value(rows, "claim_strength"):
        raise ValueError("min_claim_strength must match rows")
    if report.min_authority_score != _minimum_row_value(rows, "authority_score"):
        raise ValueError("min_authority_score must match rows")
    if report.min_corroboration_score != _minimum_row_value(rows, "corroboration_score"):
        raise ValueError("min_corroboration_score must match rows")
    if report.min_freshness_score != _minimum_row_value(rows, "freshness_score"):
        raise ValueError("min_freshness_score must match rows")
    if report.max_contradiction_pressure != _maximum_row_value(
        rows,
        "contradiction_pressure",
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.status != _summary_status(rows):
        raise ValueError("status must match rows")
    expected_reason_codes = _summary_reason_codes(rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, expected_reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _payload_value(value: object) -> Any:
    if is_dataclass(value):
        return {item.name: _payload_value(getattr(value, item.name)) for item in fields(value)}
    if type(value) is Decimal:
        return _format_decimal(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) in {str, bool} or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _report_digest(report: ResearchStrategySourceClaimAuthorityFloorReport) -> str:
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _validate_public_payload(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_public_payload(value: Any, *, label: str = "payload") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_public_string(f"{label} key", key)
            _validate_public_payload(item, label=key)
        return
    if isinstance(value, list):
        for item in value:
            _validate_public_payload(item, label=label)
        return
    if type(value) in {int, float, Decimal}:
        raise ValueError(f"{label} must not contain raw numeric values")
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if type(value) is bool or value is None:
        return
    raise ValueError(f"{label} contains unsupported public value")


def _validate_payload_shape(payload: dict[str, Any]) -> None:
    if frozenset(payload) != TOP_LEVEL_PAYLOAD_FIELDS:
        raise ValueError("payload has unexpected fields")
    _require_payload_flags(payload)
    _require_public_identifier("config_version", payload["config_version"])
    _require_status("status", payload["status"])
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    if type(payload["generated_at"]) is not str or not payload["generated_at"]:
        raise ValueError("generated_at must be an ISO datetime string")
    for field_name in (
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "min_claim_strength",
        "min_authority_score",
        "min_corroboration_score",
        "min_freshness_score",
        "max_contradiction_pressure",
    ):
        _require_decimal_string(field_name, payload[field_name])
    if payload["average_authority_floor_score"] is not None:
        _require_decimal_string(
            "average_authority_floor_score",
            payload["average_authority_floor_score"],
        )
    if type(payload["reason_codes"]) is not list:
        raise ValueError("reason_codes must be a list")
    for reason_code in payload["reason_codes"]:
        _require_reason_code("reason_codes", reason_code)
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for row in payload["rows"]:
        _validate_row_payload_shape(row)
    if type(payload["reason_code_counts"]) is not list:
        raise ValueError("reason_code_counts must be a list")
    for count in payload["reason_code_counts"]:
        _validate_reason_count_payload_shape(count)
    _report_from_payload(payload)


def _report_from_payload(
    payload: dict[str, Any],
) -> ResearchStrategySourceClaimAuthorityFloorReport:
    rows = tuple(
        ResearchStrategySourceClaimAuthorityFloorRow(
            row_label=row["row_label"],
            public_research_bucket=row["public_research_bucket"],
            claim_strength=Decimal(row["claim_strength"]),
            authority_score=Decimal(row["authority_score"]),
            corroboration_score=Decimal(row["corroboration_score"]),
            freshness_score=Decimal(row["freshness_score"]),
            contradiction_pressure=Decimal(row["contradiction_pressure"]),
            authority_floor_score=Decimal(row["authority_floor_score"]),
            status=row["status"],
            reason_codes=tuple(row["reason_codes"]),
            paper_only=row["paper_only"],
            report_only=row["report_only"],
            readonly=row["readonly"],
        )
        for row in payload["rows"]
    )
    reason_code_counts = tuple(
        ResearchStrategySourceClaimAuthorityFloorReasonCodeCount(
            reason_code=count["reason_code"],
            count=Decimal(count["count"]),
            row_ratio=Decimal(count["row_ratio"]),
            paper_only=count["paper_only"],
            report_only=count["report_only"],
            readonly=count["readonly"],
        )
        for count in payload["reason_code_counts"]
    )
    rebuilt = ResearchStrategySourceClaimAuthorityFloorReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        input_count=Decimal(payload["input_count"]),
        pass_count=Decimal(payload["pass_count"]),
        watch_count=Decimal(payload["watch_count"]),
        block_count=Decimal(payload["block_count"]),
        average_authority_floor_score=(
            None
            if payload["average_authority_floor_score"] is None
            else Decimal(payload["average_authority_floor_score"])
        ),
        min_claim_strength=Decimal(payload["min_claim_strength"]),
        min_authority_score=Decimal(payload["min_authority_score"]),
        min_corroboration_score=Decimal(payload["min_corroboration_score"]),
        min_freshness_score=Decimal(payload["min_freshness_score"]),
        max_contradiction_pressure=Decimal(payload["max_contradiction_pressure"]),
        status=payload["status"],
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=tuple(payload["reason_codes"]),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    if _payload_value(rebuilt) != payload:
        raise ValueError("report payload must use canonical report payload schema")
    return rebuilt


def _validate_row_payload_shape(row: object) -> None:
    if not isinstance(row, dict) or frozenset(row) != ROW_PAYLOAD_FIELDS:
        raise ValueError("row payload has unexpected fields")
    _require_payload_flags(row)
    _require_public_identifier("row_label", row["row_label"])
    if not row["row_label"].startswith("redacted-source-claim-authority-floor-"):
        raise ValueError("row_label must be redacted")
    _require_public_identifier("public_research_bucket", row["public_research_bucket"])
    _require_status("status", row["status"])
    for field_name in (
        "claim_strength",
        "authority_score",
        "corroboration_score",
        "freshness_score",
        "contradiction_pressure",
        "authority_floor_score",
    ):
        _require_decimal_string(field_name, row[field_name])
    if type(row["reason_codes"]) is not list:
        raise ValueError("row reason_codes must be a list")
    for reason_code in row["reason_codes"]:
        _require_reason_code("row reason_codes", reason_code)


def _validate_reason_count_payload_shape(count: object) -> None:
    if not isinstance(count, dict) or frozenset(count) != REASON_COUNT_PAYLOAD_FIELDS:
        raise ValueError("reason count payload has unexpected fields")
    _require_payload_flags(count)
    _require_reason_code("reason_code", count["reason_code"])
    _require_decimal_string("count", count["count"])
    _require_decimal_string("row_ratio", count["row_ratio"])


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be canonical UTC")
    return normalized


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_decimal_string(field_name: str, value: object) -> None:
    if type(value) is not str or not DECIMAL_STRING_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a Decimal string")
    parsed = Decimal(value)
    if value != _format_decimal(parsed):
        raise ValueError(f"{field_name} must be a canonical Decimal string")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    _validate_public_payload(_payload_value(value), label=label)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public content")


def _private_ref_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a nonempty string")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a reason code")
    _reject_unsafe_public_string(field_name, value)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized), key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    try:
        return (REASON_CODE_SEQUENCE.index(reason_code), reason_code)
    except ValueError:
        return (len(REASON_CODE_SEQUENCE), reason_code)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_CLAIM_AUTHORITY_FLOOR_STATUSES:
        raise ValueError(
            f"{field_name} must be one of {SOURCE_CLAIM_AUTHORITY_FLOOR_STATUSES}",
        )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    value = _validate_decimal_input(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(+value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    value = _validate_decimal_input(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _normalize_decimal(field_name, value)


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_nonnegative_amount(field_name: str, value: object) -> Decimal:
    value = _validate_decimal_input(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _normalize_decimal(field_name, value)


def _validate_decimal_input(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_signed() and value.is_zero():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_amount(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_amount(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _format_decimal(value: Decimal) -> str:
    return f"{_quantize(value):.6f}"


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
