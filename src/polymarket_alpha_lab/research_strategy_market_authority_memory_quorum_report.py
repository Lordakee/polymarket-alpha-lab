"""Pure report-only authority memory quorum research report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_MARKET_AUTHORITY_MEMORY_QUORUM_CONFIG_VERSION = (
    "research-strategy-authority-memory-quorum-report-v0"
)

AUTHORITY_MEMORY_QUORUM_STATUSES = ("pass", "watch", "block")
PASS_REASON_CODE = "authority_memory_quorum_pass"
REASON_CODES = (
    PASS_REASON_CODE,
    "missing_authority_watch",
    "missing_authority_block",
    "missing_memory_watch",
    "missing_memory_block",
    "weak_quorum_watch",
    "weak_quorum_block",
    "stale_memory_watch",
    "stale_memory_block",
    "low_authority_score_watch",
    "low_authority_score_block",
    "low_memory_score_watch",
    "low_memory_score_block",
    "authority_memory_quorum_score_watch",
    "authority_memory_quorum_score_block",
)
BLOCK_REASON_CODES = frozenset(
    (
        "missing_authority_block",
        "missing_memory_block",
        "weak_quorum_block",
        "stale_memory_block",
        "low_authority_score_block",
        "low_memory_score_block",
        "authority_memory_quorum_score_block",
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")

PUBLIC_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PAYLOAD_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
AUTH_PUBLIC_SURFACE_RE = re.compile(
    r"(?:^|[^a-z0-9])" + "au" + "th" + r"(?:[^a-z0-9]|$)",
)
UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        "://",
        "www.",
        "api_key",
        "au" + "th_key",
        "au" + "th_token",
        "author" + "ization",
        "broker",
        "candi" + "date",
        "condition_id",
        "credential",
        "data" + "base",
        "dsn",
        "exec" + "ution",
        "http",
        "li" + "ve",
        "mark" + "et_id",
        "mark" + "et_slug",
        "net" + "work",
        "or" + "der",
        "private_key",
        "question",
        "raw",
        "recomm" + "endation",
        "secret",
        "siz" + "ing",
        "sou" + "rce_text",
        "sou" + "rce_url",
        "submit",
        "table",
        "token",
        "tra" + "de",
        "trad" + "ing",
        "wall" + "et",
    ),
)
PUBLIC_SURFACE_SEPARATOR_RE = re.compile(r"[^a-z0-9]+")
UNSAFE_PUBLIC_SURFACE_SQUASHED_FRAGMENTS = frozenset(
    squashed
    for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS
    for squashed in (PUBLIC_SURFACE_SEPARATOR_RE.sub("", fragment),)
    if squashed and squashed != fragment
)
HARD_FLAG_KEYS = ("paper_only", "report_only", "readonly")
REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "total_authority_count",
        "total_memory_count",
        "total_quorum_count",
        "average_authority_memory_quorum_score",
        "minimum_authority_memory_quorum_score",
        "maximum_memory_age_seconds",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REPORT_NONNEGATIVE_DECIMAL_FIELDS = (
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "total_authority_count",
    "total_memory_count",
    "total_quorum_count",
    "maximum_memory_age_seconds",
)
REPORT_RATIO_DECIMAL_FIELDS = (
    "average_authority_memory_quorum_score",
    "minimum_authority_memory_quorum_score",
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "review_key",
        "observed_at",
        "authority_count",
        "memory_count",
        "quorum_count",
        "memory_age_seconds",
        "authority_score",
        "memory_score",
        "quorum_score",
        "authority_component_score",
        "memory_component_score",
        "quorum_component_score",
        "freshness_component_score",
        "authority_memory_quorum_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_NONNEGATIVE_DECIMAL_FIELDS = (
    "authority_count",
    "memory_count",
    "quorum_count",
    "memory_age_seconds",
)
ROW_RATIO_DECIMAL_FIELDS = (
    "authority_score",
    "memory_score",
    "quorum_score",
    "authority_component_score",
    "memory_component_score",
    "quorum_component_score",
    "freshness_component_score",
    "authority_memory_quorum_score",
)
REASON_CODE_COUNT_PAYLOAD_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

__all__ = (
    "AUTHORITY_MEMORY_QUORUM_STATUSES",
    "DEFAULT_RESEARCH_STRATEGY_MARKET_AUTHORITY_MEMORY_QUORUM_CONFIG_VERSION",
    "PASS_REASON_CODE",
    "REASON_CODES",
    "ResearchStrategyMarketAuthorityMemoryQuorumConfig",
    "ResearchStrategyMarketAuthorityMemoryQuorumObservation",
    "ResearchStrategyMarketAuthorityMemoryQuorumReasonCodeCount",
    "ResearchStrategyMarketAuthorityMemoryQuorumReport",
    "ResearchStrategyMarketAuthorityMemoryQuorumRow",
    "build_research_strategy_market_authority_memory_quorum_report",
    "research_strategy_market_authority_memory_quorum_report_digest",
    "research_strategy_market_authority_memory_quorum_report_payload",
    "validate_research_strategy_market_authority_memory_quorum_public_payload",
)


@dataclass(frozen=True)
class ResearchStrategyMarketAuthorityMemoryQuorumConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MARKET_AUTHORITY_MEMORY_QUORUM_CONFIG_VERSION
    )
    min_authority_count: Decimal = Decimal("2.000000")
    min_memory_count: Decimal = Decimal("2.000000")
    min_quorum_count: Decimal = Decimal("3.000000")
    max_memory_age_seconds: Decimal = Decimal("86400.000000")
    watch_score_floor: Decimal = Decimal("0.650000")
    block_score_floor: Decimal = Decimal("0.350000")
    authority_weight: Decimal = Decimal("0.350000")
    memory_weight: Decimal = Decimal("0.250000")
    quorum_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyMarketAuthorityMemoryQuorumConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMarketAuthorityMemoryQuorumConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_authority_count",
            "min_memory_count",
            "min_quorum_count",
            "max_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_score_floor",
            "block_score_floor",
            "authority_weight",
            "memory_weight",
            "quorum_weight",
            "freshness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.block_score_floor > self.watch_score_floor:
            raise ValueError("block_score_floor must not exceed watch_score_floor")
        _require_weight_sum(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyMarketAuthorityMemoryQuorumObservation:
    review_key: str
    observed_at: datetime
    authority_count: Decimal
    memory_count: Decimal
    quorum_count: Decimal
    memory_age_seconds: Decimal
    authority_score: Decimal
    memory_score: Decimal
    quorum_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyMarketAuthorityMemoryQuorumObservation does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMarketAuthorityMemoryQuorumObservation,
            "observation",
        )
        _require_public_string("review_key", self.review_key)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "authority_count",
            "memory_count",
            "quorum_count",
            "memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("authority_score", "memory_score", "quorum_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchStrategyMarketAuthorityMemoryQuorumReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyMarketAuthorityMemoryQuorumReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMarketAuthorityMemoryQuorumReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyMarketAuthorityMemoryQuorumRow:
    review_key: str
    observed_at: datetime
    authority_count: Decimal
    memory_count: Decimal
    quorum_count: Decimal
    memory_age_seconds: Decimal
    authority_score: Decimal
    memory_score: Decimal
    quorum_score: Decimal
    authority_component_score: Decimal
    memory_component_score: Decimal
    quorum_component_score: Decimal
    freshness_component_score: Decimal
    authority_memory_quorum_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyMarketAuthorityMemoryQuorumRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMarketAuthorityMemoryQuorumRow, "row")
        _require_public_string("review_key", self.review_key)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "authority_count",
            "memory_count",
            "quorum_count",
            "memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_score",
            "memory_score",
            "quorum_score",
            "authority_component_score",
            "memory_component_score",
            "quorum_component_score",
            "freshness_component_score",
            "authority_memory_quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchStrategyMarketAuthorityMemoryQuorumReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_authority_count: Decimal
    total_memory_count: Decimal
    total_quorum_count: Decimal
    average_authority_memory_quorum_score: Decimal
    minimum_authority_memory_quorum_score: Decimal
    maximum_memory_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyMarketAuthorityMemoryQuorumReasonCodeCount, ...]
    rows: tuple[ResearchStrategyMarketAuthorityMemoryQuorumRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyMarketAuthorityMemoryQuorumReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMarketAuthorityMemoryQuorumReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_authority_count",
            "total_memory_count",
            "total_quorum_count",
            "maximum_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_authority_memory_quorum_score",
            "minimum_authority_memory_quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
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
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report(self)
        expected_digest = research_strategy_market_authority_memory_quorum_report_digest(
            self,
        )
        if not self.derived_validation_digest:
            object.__setattr__(
                self,
                "derived_validation_digest",
                expected_digest,
            )
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = research_strategy_market_authority_memory_quorum_report_payload(self)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_strategy_market_authority_memory_quorum_report(
    observations: Iterable[ResearchStrategyMarketAuthorityMemoryQuorumObservation],
    *,
    generated_at: datetime,
    config: ResearchStrategyMarketAuthorityMemoryQuorumConfig | None = None,
) -> ResearchStrategyMarketAuthorityMemoryQuorumReport:
    cfg = config or ResearchStrategyMarketAuthorityMemoryQuorumConfig()
    _require_exact_type(cfg, ResearchStrategyMarketAuthorityMemoryQuorumConfig, "config")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")

    rows = tuple(
        sorted(
            (_row_from_observation(observation, cfg) for observation in normalized_observations),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": cfg.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "total_authority_count": _sum_decimal(row.authority_count for row in rows),
        "total_memory_count": _sum_decimal(row.memory_count for row in rows),
        "total_quorum_count": _sum_decimal(row.quorum_count for row in rows),
        "average_authority_memory_quorum_score": _average(
            (row.authority_memory_quorum_score for row in rows),
        ),
        "minimum_authority_memory_quorum_score": min(
            (row.authority_memory_quorum_score for row in rows),
            default=ZERO,
        ),
        "maximum_memory_age_seconds": max(
            (row.memory_age_seconds for row in rows),
            default=ZERO,
        ),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyMarketAuthorityMemoryQuorumReport(**values)


def research_strategy_market_authority_memory_quorum_report_payload(
    report: ResearchStrategyMarketAuthorityMemoryQuorumReport,
) -> dict[str, object]:
    _require_exact_type(report, ResearchStrategyMarketAuthorityMemoryQuorumReport, "report")
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload(
        "research_strategy_market_authority_memory_quorum_report_payload",
        payload,
        allow_json_containers=True,
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def research_strategy_market_authority_memory_quorum_report_digest(
    report: ResearchStrategyMarketAuthorityMemoryQuorumReport,
) -> str:
    _require_exact_type(report, ResearchStrategyMarketAuthorityMemoryQuorumReport, "report")
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _digest_from_values(values)


def validate_research_strategy_market_authority_memory_quorum_public_payload(
    payload: object,
) -> bool:
    try:
        if type(payload) is not dict:
            return False
        _reject_unsafe_public_payload(
            "research_strategy_market_authority_memory_quorum_public_payload",
            payload,
            allow_json_containers=True,
        )
        if not _validate_public_payload_shape(payload):
            return False
        digest = payload.get("derived_validation_digest")
        if type(digest) is not str or not DIGEST_RE.fullmatch(digest):
            return False
        without_digest = dict(payload)
        without_digest.pop("derived_validation_digest", None)
        return _digest_from_values(without_digest) == digest
    except (TypeError, ValueError):
        return False


def _validate_public_payload_shape(payload: Mapping[str, object]) -> bool:
    if set(payload) != REPORT_PAYLOAD_KEYS:
        return False
    if not _payload_hard_flags(payload):
        return False
    if not _payload_public_string("config_version", payload.get("config_version")):
        return False
    generated_at = _payload_utc_datetime_value(
        "generated_at",
        payload.get("generated_at"),
    )
    if generated_at is None:
        return False
    status = payload.get("status")
    if type(status) is not str or status not in AUTHORITY_MEMORY_QUORUM_STATUSES:
        return False

    report_decimals: dict[str, Decimal] = {}
    for field_name in REPORT_NONNEGATIVE_DECIMAL_FIELDS:
        decimal_value = _payload_decimal(field_name, payload.get(field_name))
        if decimal_value is None:
            return False
        report_decimals[field_name] = decimal_value
    for field_name in REPORT_RATIO_DECIMAL_FIELDS:
        decimal_value = _payload_decimal(
            field_name,
            payload.get(field_name),
            ratio=True,
        )
        if decimal_value is None:
            return False
        report_decimals[field_name] = decimal_value

    reason_codes = _payload_reason_codes(payload.get("reason_codes"))
    if reason_codes is None:
        return False
    reason_code_counts = _payload_reason_code_counts(
        payload.get("reason_code_counts"),
    )
    if reason_code_counts is None:
        return False
    rows = _payload_rows(payload.get("rows"), generated_at=generated_at)
    if rows is None:
        return False
    return _payload_report_consistency(
        status,
        report_decimals,
        reason_codes,
        reason_code_counts,
        rows,
    )


def _payload_hard_flags(payload: Mapping[str, object]) -> bool:
    return all(payload.get(field_name) is True for field_name in HARD_FLAG_KEYS)


def _payload_public_string(field_name: str, value: object) -> bool:
    try:
        _require_public_string(field_name, value)
    except ValueError:
        return False
    return True


def _payload_utc_datetime(field_name: str, value: object) -> bool:
    return _payload_utc_datetime_value(field_name, value) is not None


def _payload_utc_datetime_value(field_name: str, value: object) -> datetime | None:
    if type(value) is not str:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        normalized = _as_utc(field_name, parsed)
    except ValueError:
        return None
    if normalized.isoformat() != value:
        return None
    return normalized


def _payload_decimal(
    field_name: str,
    value: object,
    *,
    ratio: bool = False,
    positive: bool = False,
) -> Decimal | None:
    if type(value) is not str or not PAYLOAD_DECIMAL_RE.fullmatch(value):
        return None
    decimal_value = Decimal(value)
    try:
        if positive:
            normalized = _normalize_positive_decimal(field_name, decimal_value)
        elif ratio:
            normalized = _normalize_ratio(field_name, decimal_value)
        else:
            normalized = _normalize_nonnegative_decimal(field_name, decimal_value)
    except ValueError:
        return None
    if str(normalized) != value:
        return None
    return normalized


def _payload_reason_codes(value: object) -> tuple[str, ...] | None:
    if type(value) is not list:
        return None
    try:
        reason_codes = tuple(value)
        normalized = _normalize_reason_codes("reason_codes", reason_codes)
    except ValueError:
        return None
    if not normalized or normalized != reason_codes:
        return None
    return normalized


def _payload_reason_code_counts(
    value: object,
) -> tuple[tuple[str, Decimal], ...] | None:
    if type(value) is not list:
        return None
    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not dict or set(item) != REASON_CODE_COUNT_PAYLOAD_KEYS:
            return None
        if not _payload_hard_flags(item):
            return None
        reason_code = item.get("reason_code")
        if (
            type(reason_code) is not str
            or reason_code not in REASON_CODES
            or reason_code == PASS_REASON_CODE
            or reason_code in seen
        ):
            return None
        count = _payload_decimal("count", item.get("count"), positive=True)
        if count is None:
            return None
        seen.add(reason_code)
        normalized.append((reason_code, count))
    expected_order = tuple(
        reason_code
        for reason_code in REASON_CODES
        if reason_code != PASS_REASON_CODE and reason_code in seen
    )
    if tuple(reason_code for reason_code, _count in normalized) != expected_order:
        return None
    return tuple(normalized)


def _payload_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[dict[str, object], ...] | None:
    if type(value) is not list:
        return None
    rows: list[dict[str, object]] = []
    seen_review_keys: set[str] = set()
    for item in value:
        if type(item) is not dict or set(item) != ROW_PAYLOAD_KEYS:
            return None
        if not _payload_hard_flags(item):
            return None
        review_key = item.get("review_key")
        if not _payload_public_string("review_key", review_key):
            return None
        if review_key in seen_review_keys:
            return None
        seen_review_keys.add(review_key)
        observed_at = _payload_utc_datetime_value("observed_at", item.get("observed_at"))
        if observed_at is None or observed_at > generated_at:
            return None
        status = item.get("status")
        if type(status) is not str or status not in AUTHORITY_MEMORY_QUORUM_STATUSES:
            return None
        row: dict[str, object] = {
            "review_key": review_key,
            "observed_at": observed_at,
            "status": status,
        }
        for field_name in ROW_NONNEGATIVE_DECIMAL_FIELDS:
            decimal_value = _payload_decimal(field_name, item.get(field_name))
            if decimal_value is None:
                return None
            row[field_name] = decimal_value
        for field_name in ROW_RATIO_DECIMAL_FIELDS:
            decimal_value = _payload_decimal(
                field_name,
                item.get(field_name),
                ratio=True,
            )
            if decimal_value is None:
                return None
            row[field_name] = decimal_value
        reason_codes = _payload_reason_codes(item.get("reason_codes"))
        if reason_codes is None:
            return None
        if _status_from_reason_codes(reason_codes) != status:
            return None
        if status == "pass" and reason_codes != (PASS_REASON_CODE,):
            return None
        row["reason_codes"] = reason_codes
        rows.append(row)
    normalized_rows = tuple(rows)
    if normalized_rows != tuple(sorted(normalized_rows, key=_payload_row_sort_key)):
        return None
    return normalized_rows


def _payload_row_sort_key(row: Mapping[str, object]) -> tuple[int, Decimal, str]:
    status = row["status"]
    score = row["authority_memory_quorum_score"]
    review_key = row["review_key"]
    if (
        type(status) is not str
        or type(score) is not Decimal
        or type(review_key) is not str
    ):
        raise ValueError("payload row sort values are invalid")
    return (
        {"block": 0, "watch": 1, "pass": 2}[status],
        score,
        review_key,
    )


def _payload_report_consistency(
    status: str,
    report_decimals: Mapping[str, Decimal],
    reason_codes: tuple[str, ...],
    reason_code_counts: tuple[tuple[str, Decimal], ...],
    rows: tuple[Mapping[str, object], ...],
) -> bool:
    if report_decimals["row_count"] != _decimal_count(len(rows)):
        return False
    for row_status in AUTHORITY_MEMORY_QUORUM_STATUSES:
        count_field = f"{row_status}_count"
        if report_decimals[count_field] != _decimal_count(
            sum(1 for row in rows if row["status"] == row_status),
        ):
            return False
    if status != _payload_report_status(rows):
        return False
    for report_field, row_field in (
        ("total_authority_count", "authority_count"),
        ("total_memory_count", "memory_count"),
        ("total_quorum_count", "quorum_count"),
    ):
        row_values = tuple(row[row_field] for row in rows)
        if not all(type(value) is Decimal for value in row_values):
            return False
        if report_decimals[report_field] != _sum_decimal(row_values):
            return False
    score_values = tuple(row["authority_memory_quorum_score"] for row in rows)
    if not all(type(value) is Decimal for value in score_values):
        return False
    if report_decimals["average_authority_memory_quorum_score"] != _average(
        score_values,
    ):
        return False
    if report_decimals["minimum_authority_memory_quorum_score"] != min(
        score_values,
        default=ZERO,
    ):
        return False
    memory_age_values = tuple(row["memory_age_seconds"] for row in rows)
    if not all(type(value) is Decimal for value in memory_age_values):
        return False
    if report_decimals["maximum_memory_age_seconds"] != max(
        memory_age_values,
        default=ZERO,
    ):
        return False
    if reason_codes != _payload_report_reason_codes(rows):
        return False
    return reason_code_counts == _payload_reason_code_count_pairs(rows)


def _payload_report_status(rows: tuple[Mapping[str, object], ...]) -> str:
    if any(row["status"] == "block" for row in rows):
        return "block"
    if any(row["status"] == "watch" for row in rows):
        return "watch"
    return "pass"


def _payload_report_reason_codes(
    rows: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    reason_codes = tuple(
        reason_code
        for row in rows
        if type(row["reason_codes"]) is tuple
        for reason_code in row["reason_codes"]
        if reason_code != PASS_REASON_CODE
    )
    if not reason_codes:
        return (PASS_REASON_CODE,)
    return _normalize_reason_codes("reason_codes", reason_codes)


def _payload_reason_code_count_pairs(
    rows: tuple[Mapping[str, object], ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        row_reason_codes = row["reason_codes"]
        if type(row_reason_codes) is not tuple:
            raise ValueError("payload row reason_codes are invalid")
        counter.update(code for code in row_reason_codes if code != PASS_REASON_CODE)
    return tuple(
        (reason_code, _decimal_count(counter[reason_code]))
        for reason_code in REASON_CODES
        if reason_code != PASS_REASON_CODE and counter[reason_code] > 0
    )


def _row_from_observation(
    observation: ResearchStrategyMarketAuthorityMemoryQuorumObservation,
    config: ResearchStrategyMarketAuthorityMemoryQuorumConfig,
) -> ResearchStrategyMarketAuthorityMemoryQuorumRow:
    authority_component = _coverage_component(
        observation.authority_count,
        config.min_authority_count,
        observation.authority_score,
    )
    memory_component = _coverage_component(
        observation.memory_count,
        config.min_memory_count,
        observation.memory_score,
    )
    quorum_component = _coverage_component(
        observation.quorum_count,
        config.min_quorum_count,
        observation.quorum_score,
    )
    freshness_component = _clamp_ratio(
        ONE - _ratio_divide(observation.memory_age_seconds, config.max_memory_age_seconds),
    )
    composite_score = _clamp_ratio(
        authority_component * config.authority_weight
        + memory_component * config.memory_weight
        + quorum_component * config.quorum_weight
        + freshness_component * config.freshness_weight,
    )
    reason_codes = _row_reason_codes(
        observation,
        config,
        composite_score,
    )
    return ResearchStrategyMarketAuthorityMemoryQuorumRow(
        review_key=observation.review_key,
        observed_at=observation.observed_at,
        authority_count=observation.authority_count,
        memory_count=observation.memory_count,
        quorum_count=observation.quorum_count,
        memory_age_seconds=observation.memory_age_seconds,
        authority_score=observation.authority_score,
        memory_score=observation.memory_score,
        quorum_score=observation.quorum_score,
        authority_component_score=authority_component,
        memory_component_score=memory_component,
        quorum_component_score=quorum_component,
        freshness_component_score=freshness_component,
        authority_memory_quorum_score=composite_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _coverage_component(count: Decimal, minimum: Decimal, score: Decimal) -> Decimal:
    return min(_ratio_divide(count, minimum), score, ONE)


def _row_reason_codes(
    observation: ResearchStrategyMarketAuthorityMemoryQuorumObservation,
    config: ResearchStrategyMarketAuthorityMemoryQuorumConfig,
    composite_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.authority_count == ZERO:
        reason_codes.append("missing_authority_block")
    elif observation.authority_count < config.min_authority_count:
        reason_codes.append("missing_authority_watch")

    if observation.memory_count == ZERO:
        reason_codes.append("missing_memory_block")
    elif observation.memory_count < config.min_memory_count:
        reason_codes.append("missing_memory_watch")

    if observation.quorum_count == ZERO:
        reason_codes.append("weak_quorum_block")
    elif observation.quorum_count < config.min_quorum_count:
        reason_codes.append("weak_quorum_watch")

    if observation.memory_age_seconds > config.max_memory_age_seconds:
        reason_codes.append("stale_memory_block")
    elif observation.memory_age_seconds > config.max_memory_age_seconds * Decimal("0.500000"):
        reason_codes.append("stale_memory_watch")

    if observation.authority_score < config.block_score_floor:
        reason_codes.append("low_authority_score_block")
    elif observation.authority_score < config.watch_score_floor:
        reason_codes.append("low_authority_score_watch")

    if observation.memory_score < config.block_score_floor:
        reason_codes.append("low_memory_score_block")
    elif observation.memory_score < config.watch_score_floor:
        reason_codes.append("low_memory_score_watch")

    if composite_score < config.block_score_floor:
        reason_codes.append("authority_memory_quorum_score_block")
    elif composite_score < config.watch_score_floor:
        reason_codes.append("authority_memory_quorum_score_watch")

    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _normalize_observations(
    observations: Iterable[ResearchStrategyMarketAuthorityMemoryQuorumObservation],
) -> tuple[ResearchStrategyMarketAuthorityMemoryQuorumObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observation rows")
    normalized = tuple(observations)
    seen_review_keys: set[str] = set()
    for observation in normalized:
        _require_exact_type(
            observation,
            ResearchStrategyMarketAuthorityMemoryQuorumObservation,
            "observation",
        )
        if observation.review_key in seen_review_keys:
            raise ValueError("observation review_key values must be unique")
        seen_review_keys.add(observation.review_key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyMarketAuthorityMemoryQuorumRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(row, ResearchStrategyMarketAuthorityMemoryQuorumRow, "row")
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchStrategyMarketAuthorityMemoryQuorumReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchStrategyMarketAuthorityMemoryQuorumReasonCodeCount] = []
    seen: set[str] = set()
    for count in counts:
        _require_exact_type(
            count,
            ResearchStrategyMarketAuthorityMemoryQuorumReasonCodeCount,
            "reason_code_count",
        )
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(count.reason_code)
        normalized.append(count)
    return tuple(normalized)


def _normalize_reason_codes(field_name: str, reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)


def _reason_code_counts(
    rows: tuple[ResearchStrategyMarketAuthorityMemoryQuorumRow, ...],
) -> tuple[ResearchStrategyMarketAuthorityMemoryQuorumReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(code for code in row.reason_codes if code != PASS_REASON_CODE)
    return tuple(
        ResearchStrategyMarketAuthorityMemoryQuorumReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in REASON_CODES
        if reason_code != PASS_REASON_CODE and counter[reason_code] > 0
    )


def _report_reason_codes(
    rows: tuple[ResearchStrategyMarketAuthorityMemoryQuorumRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (PASS_REASON_CODE,)
    reason_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON_CODE
    )
    if not reason_codes:
        return (PASS_REASON_CODE,)
    return _normalize_reason_codes("reason_codes", reason_codes)


def _row_sort_key(
    row: ResearchStrategyMarketAuthorityMemoryQuorumRow,
) -> tuple[int, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.authority_memory_quorum_score,
        row.review_key,
    )


def _report_status(rows: tuple[ResearchStrategyMarketAuthorityMemoryQuorumRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchStrategyMarketAuthorityMemoryQuorumRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _validate_row(row: ResearchStrategyMarketAuthorityMemoryQuorumRow) -> None:
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON_CODE,):
        raise ValueError("pass rows must carry only the pass reason code")


def _validate_report(report: ResearchStrategyMarketAuthorityMemoryQuorumReport) -> None:
    rows = report.rows
    review_keys = tuple(row.review_key for row in rows)
    if len(set(review_keys)) != len(review_keys):
        raise ValueError("rows review_key values must be unique")
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.total_authority_count != _sum_decimal(row.authority_count for row in rows):
        raise ValueError("total_authority_count must match rows")
    if report.total_memory_count != _sum_decimal(row.memory_count for row in rows):
        raise ValueError("total_memory_count must match rows")
    if report.total_quorum_count != _sum_decimal(row.quorum_count for row in rows):
        raise ValueError("total_quorum_count must match rows")
    if report.average_authority_memory_quorum_score != _average(
        (row.authority_memory_quorum_score for row in rows),
    ):
        raise ValueError("average_authority_memory_quorum_score must match rows")
    if report.minimum_authority_memory_quorum_score != min(
        (row.authority_memory_quorum_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("minimum_authority_memory_quorum_score must match rows")
    if report.maximum_memory_age_seconds != max(
        (row.memory_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("maximum_memory_age_seconds must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize_decimal(total)


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize_decimal(_sum_decimal(items) / _decimal_count(len(items)))


def _ratio_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return _clamp_ratio(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize_decimal(value), ZERO), ONE)


def _quantize_decimal(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantized to six decimal places") from exc


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _require_weight_sum(
    config: ResearchStrategyMarketAuthorityMemoryQuorumConfig,
) -> None:
    total_weight = _quantize_decimal(
        config.authority_weight
        + config.memory_weight
        + config.quorum_weight
        + config.freshness_weight,
    )
    if total_weight != ONE:
        raise ValueError("weights must sum to one")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_NAME_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} contains unsupported reason code")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in AUTHORITY_MEMORY_QUORUM_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest_payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(_quantize_decimal(value))
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or type(value) is float:
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
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
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
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    if _has_unsafe_public_fragment(key):
        raise ValueError(f"{path}.{key} has unsafe public surface")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{path} has unsafe public surface")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    if AUTH_PUBLIC_SURFACE_RE.search(lowered):
        return True
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        return True
    squashed = PUBLIC_SURFACE_SEPARATOR_RE.sub("", lowered)
    return any(
        fragment in squashed for fragment in UNSAFE_PUBLIC_SURFACE_SQUASHED_FRAGMENTS
    )
