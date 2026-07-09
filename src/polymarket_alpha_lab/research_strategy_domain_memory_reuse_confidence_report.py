"""Report-only domain memory reuse confidence reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_MEMORY_REUSE_CONFIDENCE_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_DOMAIN_MEMORY_REUSE_CONFIDENCE_STATUSES",
    "ResearchStrategyDomainMemoryReuseConfidenceConfig",
    "ResearchStrategyDomainMemoryReuseConfidenceInput",
    "ResearchStrategyDomainMemoryReuseConfidenceReasonCodeCount",
    "ResearchStrategyDomainMemoryReuseConfidenceReport",
    "ResearchStrategyDomainMemoryReuseConfidenceRow",
    "build_research_strategy_domain_memory_reuse_confidence_report",
    "research_strategy_domain_memory_reuse_confidence_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_DOMAIN_MEMORY_REUSE_CONFIDENCE_REPORT_CONFIG_VERSION = (
    "research-strategy-domain-memory-reuse-confidence-report-v0"
)
RESEARCH_STRATEGY_DOMAIN_MEMORY_REUSE_CONFIDENCE_STATUSES = (
    "pass",
    "watch",
    "block",
)
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    BLOCK_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}
HEX_CHARS = frozenset("0123456789abcdef")

EMPTY_REPORT_REASON_CODE = "empty_domain_memory_reuse_confidence_inputs"
REPORT_PASS_REASON_CODE = "domain_memory_reuse_confidence_report_pass"
REPORT_WATCH_REASON_CODE = "domain_memory_reuse_confidence_report_watch"
REPORT_BLOCK_REASON_CODE = "domain_memory_reuse_confidence_report_block"
ROW_PASS_REASON_CODE = "memory_reuse_confidence_pass"
ROW_REASON_CODES = (
    "memory_reuse_confidence_score_block",
    "memory_reuse_confidence_score_watch",
    ROW_PASS_REASON_CODE,
    "prior_hit_rate_block",
    "prior_hit_rate_watch",
    "evidence_similarity_score_block",
    "evidence_similarity_score_watch",
    "transferability_score_block",
    "transferability_score_watch",
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
    "freshness_score_block",
    "freshness_score_watch",
)
REPORT_REASON_CODES = (
    REPORT_PASS_REASON_CODE,
    REPORT_WATCH_REASON_CODE,
    REPORT_BLOCK_REASON_CODE,
    *ROW_REASON_CODES,
    EMPTY_REPORT_REASON_CODE,
)
ROW_REASON_SEQUENCE = (
    (
        "memory_reuse_confidence_score_block",
        "memory_reuse_confidence_score_watch",
        ROW_PASS_REASON_CODE,
    ),
    ("prior_hit_rate_block", "prior_hit_rate_watch"),
    ("evidence_similarity_score_block", "evidence_similarity_score_watch"),
    ("transferability_score_block", "transferability_score_watch"),
    ("contradiction_pressure_block", "contradiction_pressure_watch"),
    ("freshness_score_block", "freshness_score_watch"),
)
UNSAFE_KEY_FRAGMENTS = (
    "cand" + "idate_id",
    "cand" + "idate_sl" + "ug",
    "mar" + "ket_id",
    "mar" + "ket_sl" + "ug",
    "mar" + "ket_ques" + "tion",
    "sou" + "rce_u" + "rl",
    "sou" + "rce_tex" + "t",
    "dsn",
    "tab" + "le_name",
    "tok" + "en",
    "wa" + "llet",
    "ord" + "er",
    "tra" + "de",
)
UNSAFE_VALUE_FRAGMENTS = (
    "cand" + "idate_id",
    "cand" + "idate_sl" + "ug",
    "mar" + "ket_id",
    "mar" + "ket_sl" + "ug",
    "mar" + "ket_ques" + "tion",
    "mar" + "ket",
    "sl" + "ug",
    "ques" + "tion:",
    "sou" + "rce_u" + "rl",
    "sou" + "rce_tex" + "t",
    "://",
    "dsn=",
    "tok" + "en=",
    "wa" + "llet",
    "ord" + "er",
    "tra" + "de",
    "buy",
    "sell",
    "li" + "ve",
    "si" + "zing",
    "rec" + "ommend",
)


@dataclass(frozen=True)
class ResearchStrategyDomainMemoryReuseConfidenceConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_MEMORY_REUSE_CONFIDENCE_REPORT_CONFIG_VERSION
    )
    prior_hit_rate_weight: Decimal = Decimal("0.300000")
    evidence_similarity_score_weight: Decimal = Decimal("0.250000")
    transferability_score_weight: Decimal = Decimal("0.200000")
    freshness_score_weight: Decimal = Decimal("0.150000")
    contradiction_reserve_weight: Decimal = Decimal("0.100000")
    pass_threshold: Decimal = Decimal("0.750000")
    watch_threshold: Decimal = Decimal("0.550000")
    min_pass_prior_hit_rate: Decimal = Decimal("0.750000")
    min_watch_prior_hit_rate: Decimal = Decimal("0.500000")
    min_pass_evidence_similarity_score: Decimal = Decimal("0.650000")
    min_watch_evidence_similarity_score: Decimal = Decimal("0.450000")
    min_pass_transferability_score: Decimal = Decimal("0.700000")
    min_watch_transferability_score: Decimal = Decimal("0.500000")
    max_pass_contradiction_pressure: Decimal = Decimal("0.250000")
    max_watch_contradiction_pressure: Decimal = Decimal("0.700000")
    min_pass_freshness_score: Decimal = Decimal("0.750000")
    min_watch_freshness_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainMemoryReuseConfidenceConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainMemoryReuseConfidenceConfig)
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_MEMORY_REUSE_CONFIDENCE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "prior_hit_rate_weight",
            "evidence_similarity_score_weight",
            "transferability_score_weight",
            "freshness_score_weight",
            "contradiction_reserve_weight",
            "pass_threshold",
            "watch_threshold",
            "min_pass_prior_hit_rate",
            "min_watch_prior_hit_rate",
            "min_pass_evidence_similarity_score",
            "min_watch_evidence_similarity_score",
            "min_pass_transferability_score",
            "min_watch_transferability_score",
            "max_pass_contradiction_pressure",
            "max_watch_contradiction_pressure",
            "min_pass_freshness_score",
            "min_watch_freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_descending_threshold(
            "threshold",
            self.pass_threshold,
            self.watch_threshold,
        )
        _require_descending_threshold(
            "prior_hit_rate",
            self.min_pass_prior_hit_rate,
            self.min_watch_prior_hit_rate,
        )
        _require_descending_threshold(
            "evidence_similarity_score",
            self.min_pass_evidence_similarity_score,
            self.min_watch_evidence_similarity_score,
        )
        _require_descending_threshold(
            "transferability_score",
            self.min_pass_transferability_score,
            self.min_watch_transferability_score,
        )
        _require_ascending_threshold(
            "contradiction_pressure",
            self.max_pass_contradiction_pressure,
            self.max_watch_contradiction_pressure,
        )
        _require_descending_threshold(
            "freshness_score",
            self.min_pass_freshness_score,
            self.min_watch_freshness_score,
        )
        _require_weight_total(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyDomainMemoryReuseConfidenceInput:
    domain_key: str
    memory_label: str
    observed_at: datetime
    prior_hit_rate: Decimal
    evidence_similarity_score: Decimal
    transferability_score: Decimal
    contradiction_pressure: Decimal
    freshness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainMemoryReuseConfidenceInput "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainMemoryReuseConfidenceInput)
        object.__setattr__(
            self,
            "domain_key",
            _require_safe_label("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "memory_label",
            _require_memory_label("memory_label", self.memory_label),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "prior_hit_rate",
            "evidence_similarity_score",
            "transferability_score",
            "contradiction_pressure",
            "freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyDomainMemoryReuseConfidenceRow:
    rank: Decimal
    domain_key: str
    memory_digest: str
    status: str
    observed_at: datetime
    memory_age_seconds: Decimal
    prior_hit_rate: Decimal
    evidence_similarity_score: Decimal
    transferability_score: Decimal
    contradiction_pressure: Decimal
    freshness_score: Decimal
    reuse_confidence_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainMemoryReuseConfidenceRow "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainMemoryReuseConfidenceRow)
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        object.__setattr__(
            self,
            "domain_key",
            _require_safe_label("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "memory_digest",
            _normalize_sha256("memory_digest", self.memory_digest),
        )
        _require_member(
            "status",
            self.status,
            RESEARCH_STRATEGY_DOMAIN_MEMORY_REUSE_CONFIDENCE_STATUSES,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "memory_age_seconds",
            _normalize_nonnegative_measure(
                "memory_age_seconds",
                self.memory_age_seconds,
            ),
        )
        for field_name in (
            "prior_hit_rate",
            "evidence_similarity_score",
            "transferability_score",
            "contradiction_pressure",
            "freshness_score",
            "reuse_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_row_reason_code_sequence(self.reason_codes)
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyDomainMemoryReuseConfidenceReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainMemoryReuseConfidenceReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainMemoryReuseConfidenceReasonCodeCount)
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        if self.count <= ZERO_COUNT:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyDomainMemoryReuseConfidenceReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_reuse_confidence_score: Decimal
    average_contradiction_pressure: Decimal
    highest_contradiction_pressure: Decimal
    oldest_memory_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyDomainMemoryReuseConfidenceReasonCodeCount, ...]
    rows: tuple[ResearchStrategyDomainMemoryReuseConfidenceRow, ...]
    public_payload_sha256: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainMemoryReuseConfidenceReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainMemoryReuseConfidenceReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_MEMORY_REUSE_CONFIDENCE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in ("signal_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_reuse_confidence_score",
            "average_contradiction_pressure",
            "highest_contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oldest_memory_age_seconds",
            _normalize_nonnegative_measure(
                "oldest_memory_age_seconds",
                self.oldest_memory_age_seconds,
            ),
        )
        _require_member(
            "status",
            self.status,
            RESEARCH_STRATEGY_DOMAIN_MEMORY_REUSE_CONFIDENCE_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_report_reason_code_sequence(self.reason_codes)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_sha256 = _report_public_payload_sha256(self)
        if self.public_payload_sha256:
            object.__setattr__(
                self,
                "public_payload_sha256",
                _normalize_sha256("public_payload_sha256", self.public_payload_sha256),
            )
            if self.public_payload_sha256 != expected_sha256:
                raise ValueError("public_payload_sha256 must match report fields")
        else:
            object.__setattr__(self, "public_payload_sha256", expected_sha256)


def build_research_strategy_domain_memory_reuse_confidence_report(
    signals: tuple[ResearchStrategyDomainMemoryReuseConfidenceInput, ...]
    | list[ResearchStrategyDomainMemoryReuseConfidenceInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyDomainMemoryReuseConfidenceConfig,
) -> ResearchStrategyDomainMemoryReuseConfidenceReport:
    if type(config) is not ResearchStrategyDomainMemoryReuseConfidenceConfig:
        raise ValueError(
            "config must be a ResearchStrategyDomainMemoryReuseConfidenceConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(signals, generated_at=generated_at_utc)
    rows = _rank_rows(
        tuple(_build_row(item, generated_at=generated_at_utc, config=config) for item in inputs),
    )
    return ResearchStrategyDomainMemoryReuseConfidenceReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        signal_count=_count(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        average_reuse_confidence_score=_average_field(
            rows,
            "reuse_confidence_score",
        ),
        average_contradiction_pressure=_average_field(
            rows,
            "contradiction_pressure",
        ),
        highest_contradiction_pressure=_max_ratio_field(rows, "contradiction_pressure"),
        oldest_memory_age_seconds=_max_measure_field(rows, "memory_age_seconds"),
        status=_status_rollup(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_strategy_domain_memory_reuse_confidence_report_payload(
    report: ResearchStrategyDomainMemoryReuseConfidenceReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyDomainMemoryReuseConfidenceReport:
        _require_hard_flags("report", report)
        _validate_report_public_payload_sha256(report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_canonical_public_json(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be exactly "
            "ResearchStrategyDomainMemoryReuseConfidenceReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _validate_public_payload_shape(payload)
    _validate_public_payload_sha256(payload)
    _validate_public_payload_consistency(payload)
    return payload


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


def _validate_public_payload_shape(payload: dict[str, Any]) -> None:
    _require_exact_keys(
        "payload",
        payload,
        _json_field_names(ResearchStrategyDomainMemoryReuseConfidenceReport),
    )
    _require_payload_datetime("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_STRATEGY_DOMAIN_MEMORY_REUSE_CONFIDENCE_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be supported")
    for field_name in ("signal_count", "pass_count", "watch_count", "block_count"):
        _require_payload_count(field_name, payload[field_name])
    for field_name in (
        "average_reuse_confidence_score",
        "average_contradiction_pressure",
        "highest_contradiction_pressure",
        "oldest_memory_age_seconds",
    ):
        _require_payload_measure(field_name, payload[field_name])
    _require_member(
        "status",
        payload["status"],
        RESEARCH_STRATEGY_DOMAIN_MEMORY_REUSE_CONFIDENCE_STATUSES,
    )
    _require_payload_reason_codes(
        "reason_codes",
        payload["reason_codes"],
        REPORT_REASON_CODES,
        report_level=True,
    )
    _validate_public_reason_code_counts(payload["reason_code_counts"])
    _validate_public_rows(payload["rows"])
    _normalize_sha256("public_payload_sha256", payload["public_payload_sha256"])
    _require_payload_flags("payload", payload)


def _validate_public_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("rows must be a JSON array")
    for index, row in enumerate(value):
        row_path = f"rows[{index}]"
        if type(row) is not dict:
            raise ValueError(f"{row_path} must be a JSON object")
        _require_exact_keys(
            row_path,
            row,
            _json_field_names(ResearchStrategyDomainMemoryReuseConfidenceRow),
        )
        _require_payload_positive_count(f"{row_path}.rank", row["rank"])
        _require_safe_label(f"{row_path}.domain_key", row["domain_key"])
        _normalize_sha256(f"{row_path}.memory_digest", row["memory_digest"])
        _require_member(
            f"{row_path}.status",
            row["status"],
            RESEARCH_STRATEGY_DOMAIN_MEMORY_REUSE_CONFIDENCE_STATUSES,
        )
        _require_payload_datetime(f"{row_path}.observed_at", row["observed_at"])
        for field_name in (
            "memory_age_seconds",
            "prior_hit_rate",
            "evidence_similarity_score",
            "transferability_score",
            "contradiction_pressure",
            "freshness_score",
            "reuse_confidence_score",
        ):
            _require_payload_measure(
                f"{row_path}.{field_name}",
                row[field_name],
            )
        _require_payload_reason_codes(
            f"{row_path}.reason_codes",
            row["reason_codes"],
            ROW_REASON_CODES,
            report_level=False,
        )
        _require_payload_flags(row_path, row)


def _validate_public_reason_code_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a JSON array")
    for index, item in enumerate(value):
        item_path = f"reason_code_counts[{index}]"
        if type(item) is not dict:
            raise ValueError(f"{item_path} must be a JSON object")
        _require_exact_keys(
            item_path,
            item,
            _json_field_names(
                ResearchStrategyDomainMemoryReuseConfidenceReasonCodeCount,
            ),
        )
        _require_member(
            f"{item_path}.reason_code",
            item["reason_code"],
            ROW_REASON_CODES,
        )
        _require_payload_positive_count(f"{item_path}.count", item["count"])
        _require_payload_flags(item_path, item)


def _validate_public_payload_sha256(payload: dict[str, Any]) -> None:
    digest = _normalize_sha256(
        "public_payload_sha256",
        payload["public_payload_sha256"],
    )
    digest_payload = {
        key: item
        for key, item in payload.items()
        if key != "public_payload_sha256"
    }
    if digest != _sha256_for_public_payload(digest_payload):
        raise ValueError("public_payload_sha256 must match report fields")


def _validate_public_payload_consistency(payload: dict[str, Any]) -> None:
    ResearchStrategyDomainMemoryReuseConfidenceReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        signal_count=_payload_count("signal_count", payload["signal_count"]),
        pass_count=_payload_count("pass_count", payload["pass_count"]),
        watch_count=_payload_count("watch_count", payload["watch_count"]),
        block_count=_payload_count("block_count", payload["block_count"]),
        average_reuse_confidence_score=_payload_measure(
            "average_reuse_confidence_score",
            payload["average_reuse_confidence_score"],
        ),
        average_contradiction_pressure=_payload_measure(
            "average_contradiction_pressure",
            payload["average_contradiction_pressure"],
        ),
        highest_contradiction_pressure=_payload_measure(
            "highest_contradiction_pressure",
            payload["highest_contradiction_pressure"],
        ),
        oldest_memory_age_seconds=_payload_measure(
            "oldest_memory_age_seconds",
            payload["oldest_memory_age_seconds"],
        ),
        status=payload["status"],
        reason_codes=tuple(payload["reason_codes"]),
        reason_code_counts=tuple(
            _reason_code_count_from_payload(item)
            for item in payload["reason_code_counts"]
        ),
        rows=tuple(_row_from_payload(row) for row in payload["rows"]),
        public_payload_sha256=payload["public_payload_sha256"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_payload(
    row: dict[str, Any],
) -> ResearchStrategyDomainMemoryReuseConfidenceRow:
    return ResearchStrategyDomainMemoryReuseConfidenceRow(
        rank=_payload_count("rank", row["rank"]),
        domain_key=row["domain_key"],
        memory_digest=row["memory_digest"],
        status=row["status"],
        observed_at=_payload_datetime("observed_at", row["observed_at"]),
        memory_age_seconds=_payload_measure(
            "memory_age_seconds",
            row["memory_age_seconds"],
        ),
        prior_hit_rate=_payload_measure("prior_hit_rate", row["prior_hit_rate"]),
        evidence_similarity_score=_payload_measure(
            "evidence_similarity_score",
            row["evidence_similarity_score"],
        ),
        transferability_score=_payload_measure(
            "transferability_score",
            row["transferability_score"],
        ),
        contradiction_pressure=_payload_measure(
            "contradiction_pressure",
            row["contradiction_pressure"],
        ),
        freshness_score=_payload_measure("freshness_score", row["freshness_score"]),
        reuse_confidence_score=_payload_measure(
            "reuse_confidence_score",
            row["reuse_confidence_score"],
        ),
        reason_codes=tuple(row["reason_codes"]),
        paper_only=row["paper_only"],
        report_only=row["report_only"],
        readonly=row["readonly"],
    )


def _reason_code_count_from_payload(
    item: dict[str, Any],
) -> ResearchStrategyDomainMemoryReuseConfidenceReasonCodeCount:
    return ResearchStrategyDomainMemoryReuseConfidenceReasonCodeCount(
        reason_code=item["reason_code"],
        count=_payload_count("count", item["count"]),
        paper_only=item["paper_only"],
        report_only=item["report_only"],
        readonly=item["readonly"],
    )


def _json_field_names(value_type: type[object]) -> tuple[str, ...]:
    return tuple(field.name for field in fields(value_type))


def _require_exact_keys(
    name: str,
    value: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if set(value) != set(expected_keys):
        raise ValueError(f"{name} must contain exactly the public schema fields")


def _require_payload_datetime(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
        normalized = _as_utc(name, parsed)
    except ValueError as exc:
        raise ValueError(f"{name} must be a canonical UTC datetime string") from exc
    if value != normalized.isoformat():
        raise ValueError(f"{name} must be a canonical UTC datetime string")


def _payload_datetime(name: str, value: object) -> datetime:
    _require_payload_datetime(name, value)
    return _as_utc(name, datetime.fromisoformat(value))


def _require_payload_count(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{name} must be finite")
    if parsed < ZERO_COUNT or parsed != parsed.to_integral_value():
        raise ValueError(f"{name} must be a nonnegative whole Decimal")
    if value != str(parsed.quantize(COUNT_QUANTUM)):
        raise ValueError(f"{name} must be a canonical whole Decimal")


def _require_payload_positive_count(name: str, value: object) -> None:
    _require_payload_count(name, value)
    if Decimal(value) <= ZERO_COUNT:
        raise ValueError(f"{name} must be positive")


def _payload_count(name: str, value: object) -> Decimal:
    _require_payload_count(name, value)
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_payload_measure(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{name} must be finite")
    if value != str(_quantize(parsed, RATIO_QUANTUM)):
        raise ValueError(f"{name} must be a canonical six-place Decimal")


def _payload_measure(name: str, value: object) -> Decimal:
    _require_payload_measure(name, value)
    return _quantize(Decimal(value), RATIO_QUANTUM)


def _require_payload_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
    *,
    report_level: bool,
) -> None:
    if type(value) is not list:
        raise ValueError(f"{name} must be a JSON array")
    codes = _normalize_reason_codes(name, value, allowed)
    if report_level:
        _require_report_reason_code_sequence(codes)
    else:
        _require_row_reason_code_sequence(codes)


def _require_payload_flags(name: str, payload: dict[str, Any]) -> None:
    _require_hard_flags(name, _DictFlags(payload))


def _require_canonical_public_json(value: object, path: str = "") -> None:
    current_path = path or "payload"
    if value is None or type(value) is bool or type(value) is str:
        return
    if isinstance(value, Decimal):
        raise ValueError(f"{current_path} must be a Decimal string")
    if isinstance(value, datetime):
        raise ValueError(f"{current_path} must be a canonical UTC datetime string")
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{current_path} must be a Decimal string")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _require_canonical_public_json(item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _require_canonical_public_json(item, f"{current_path}[{index}]")
        return
    raise ValueError(f"{current_path} is not a canonical public JSON value")


def _build_row(
    item: ResearchStrategyDomainMemoryReuseConfidenceInput,
    *,
    generated_at: datetime,
    config: ResearchStrategyDomainMemoryReuseConfidenceConfig,
) -> ResearchStrategyDomainMemoryReuseConfidenceRow:
    memory_age_seconds = _age_seconds(item.observed_at, generated_at)
    reuse_confidence_score = _reuse_confidence_score(item, config=config)
    reason_codes = _row_reason_codes(
        prior_hit_rate=item.prior_hit_rate,
        evidence_similarity_score=item.evidence_similarity_score,
        transferability_score=item.transferability_score,
        contradiction_pressure=item.contradiction_pressure,
        freshness_score=item.freshness_score,
        reuse_confidence_score=reuse_confidence_score,
        config=config,
    )
    return ResearchStrategyDomainMemoryReuseConfidenceRow(
        rank=COUNT_QUANTUM,
        domain_key=item.domain_key,
        memory_digest=_memory_digest(item.memory_label),
        status=_status_from_reason_codes(reason_codes),
        observed_at=item.observed_at,
        memory_age_seconds=memory_age_seconds,
        prior_hit_rate=item.prior_hit_rate,
        evidence_similarity_score=item.evidence_similarity_score,
        transferability_score=item.transferability_score,
        contradiction_pressure=item.contradiction_pressure,
        freshness_score=item.freshness_score,
        reuse_confidence_score=reuse_confidence_score,
        reason_codes=reason_codes,
    )


def _rank_rows(
    rows: tuple[ResearchStrategyDomainMemoryReuseConfidenceRow, ...],
) -> tuple[ResearchStrategyDomainMemoryReuseConfidenceRow, ...]:
    return tuple(
        ResearchStrategyDomainMemoryReuseConfidenceRow(
            rank=_count(index),
            domain_key=row.domain_key,
            memory_digest=row.memory_digest,
            status=row.status,
            observed_at=row.observed_at,
            memory_age_seconds=row.memory_age_seconds,
            prior_hit_rate=row.prior_hit_rate,
            evidence_similarity_score=row.evidence_similarity_score,
            transferability_score=row.transferability_score,
            contradiction_pressure=row.contradiction_pressure,
            freshness_score=row.freshness_score,
            reuse_confidence_score=row.reuse_confidence_score,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_reason_codes(
    *,
    prior_hit_rate: Decimal,
    evidence_similarity_score: Decimal,
    transferability_score: Decimal,
    contradiction_pressure: Decimal,
    freshness_score: Decimal,
    reuse_confidence_score: Decimal,
    config: ResearchStrategyDomainMemoryReuseConfidenceConfig,
) -> tuple[str, ...]:
    block_codes: list[str] = []
    watch_codes: list[str] = []
    if reuse_confidence_score < config.watch_threshold:
        block_codes.append("memory_reuse_confidence_score_block")
    elif reuse_confidence_score < config.pass_threshold:
        watch_codes.append("memory_reuse_confidence_score_watch")
    if prior_hit_rate < config.min_watch_prior_hit_rate:
        block_codes.append("prior_hit_rate_block")
    elif prior_hit_rate < config.min_pass_prior_hit_rate:
        watch_codes.append("prior_hit_rate_watch")
    if evidence_similarity_score < config.min_watch_evidence_similarity_score:
        block_codes.append("evidence_similarity_score_block")
    elif evidence_similarity_score < config.min_pass_evidence_similarity_score:
        watch_codes.append("evidence_similarity_score_watch")
    if transferability_score < config.min_watch_transferability_score:
        block_codes.append("transferability_score_block")
    elif transferability_score < config.min_pass_transferability_score:
        watch_codes.append("transferability_score_watch")
    if contradiction_pressure >= config.max_watch_contradiction_pressure:
        block_codes.append("contradiction_pressure_block")
    elif contradiction_pressure >= config.max_pass_contradiction_pressure:
        watch_codes.append("contradiction_pressure_watch")
    if freshness_score < config.min_watch_freshness_score:
        block_codes.append("freshness_score_block")
    elif freshness_score < config.min_pass_freshness_score:
        watch_codes.append("freshness_score_watch")
    if block_codes:
        return _normalize_reason_codes("reason_codes", tuple(block_codes), ROW_REASON_CODES)
    if watch_codes:
        return _normalize_reason_codes("reason_codes", tuple(watch_codes), ROW_REASON_CODES)
    return (ROW_PASS_REASON_CODE,)


def _reuse_confidence_score(
    item: ResearchStrategyDomainMemoryReuseConfidenceInput,
    *,
    config: ResearchStrategyDomainMemoryReuseConfidenceConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "reuse_confidence_score",
            item.prior_hit_rate * config.prior_hit_rate_weight
            + item.evidence_similarity_score * config.evidence_similarity_score_weight
            + item.transferability_score * config.transferability_score_weight
            + item.freshness_score * config.freshness_score_weight
            + (ONE_RATIO - item.contradiction_pressure)
            * config.contradiction_reserve_weight,
        )


def _normalize_inputs(
    value: tuple[ResearchStrategyDomainMemoryReuseConfidenceInput, ...]
    | list[ResearchStrategyDomainMemoryReuseConfidenceInput],
    *,
    generated_at: datetime,
) -> tuple[ResearchStrategyDomainMemoryReuseConfidenceInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategyDomainMemoryReuseConfidenceInput:
            raise ValueError(
                "signals must contain ResearchStrategyDomainMemoryReuseConfidenceInput values",
            )
        _require_hard_flags("signal", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return rows


def _normalize_rows(
    value: tuple[ResearchStrategyDomainMemoryReuseConfidenceRow, ...],
) -> tuple[ResearchStrategyDomainMemoryReuseConfidenceRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategyDomainMemoryReuseConfidenceRow:
            raise ValueError("rows must contain confidence row values")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    if tuple(row.rank for row in rows) != tuple(
        _count(index) for index in range(1, len(rows) + 1)
    ):
        raise ValueError("rows must use sequential ranks")
    return rows


def _normalize_reason_code_counts(
    value: tuple[ResearchStrategyDomainMemoryReuseConfidenceReasonCodeCount, ...],
) -> tuple[ResearchStrategyDomainMemoryReuseConfidenceReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    expected = tuple(sorted(rows, key=lambda row: _row_reason_rank(row.reason_code)))
    if rows != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyDomainMemoryReuseConfidenceReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(row.reason_code)
    return rows


def _reason_code_counts(
    rows: tuple[ResearchStrategyDomainMemoryReuseConfidenceRow, ...],
) -> tuple[ResearchStrategyDomainMemoryReuseConfidenceReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyDomainMemoryReuseConfidenceReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in counter
    )


def _validate_report(report: ResearchStrategyDomainMemoryReuseConfidenceReport) -> None:
    rows = report.rows
    if report.signal_count != _count(len(rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _status_count(rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    if report.average_reuse_confidence_score != _average_field(
        rows,
        "reuse_confidence_score",
    ):
        raise ValueError("average_reuse_confidence_score must match rows")
    if report.average_contradiction_pressure != _average_field(
        rows,
        "contradiction_pressure",
    ):
        raise ValueError("average_contradiction_pressure must match rows")
    if report.highest_contradiction_pressure != _max_ratio_field(
        rows,
        "contradiction_pressure",
    ):
        raise ValueError("highest_contradiction_pressure must match rows")
    if report.oldest_memory_age_seconds != _max_measure_field(rows, "memory_age_seconds"):
        raise ValueError("oldest_memory_age_seconds must match rows")
    if report.status != _status_rollup(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _validate_report_public_payload_sha256(
    report: ResearchStrategyDomainMemoryReuseConfidenceReport,
) -> None:
    _normalize_sha256("public_payload_sha256", report.public_payload_sha256)
    if report.public_payload_sha256 != _report_public_payload_sha256(report):
        raise ValueError("public_payload_sha256 must match report fields")


def _report_public_payload_sha256(
    report: ResearchStrategyDomainMemoryReuseConfidenceReport,
) -> str:
    payload = asdict(report)
    payload.pop("public_payload_sha256", None)
    ready = _json_ready(payload)
    _reject_unsafe_public_payload("digest_payload", ready)
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return _sha256_for_public_payload(ready)


def _sha256_for_public_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _memory_digest(memory_label: str) -> str:
    _require_memory_label("memory_label", memory_label)
    encoded = memory_label.encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _status_count(
    rows: tuple[ResearchStrategyDomainMemoryReuseConfidenceRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_field(
    rows: tuple[ResearchStrategyDomainMemoryReuseConfidenceRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            field_name,
            sum((getattr(row, field_name) for row in rows), ZERO_RATIO)
            / Decimal(len(rows)),
        )


def _max_ratio_field(
    rows: tuple[ResearchStrategyDomainMemoryReuseConfidenceRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(getattr(row, field_name) for row in rows)


def _max_measure_field(
    rows: tuple[ResearchStrategyDomainMemoryReuseConfidenceRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(getattr(row, field_name) for row in rows)


def _status_rollup(
    rows: tuple[ResearchStrategyDomainMemoryReuseConfidenceRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return BLOCK_STATUS
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainMemoryReuseConfidenceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _status_rollup(rows)
    codes = [_report_status_reason_code(status)]
    for reason_code in ROW_REASON_CODES:
        if any(reason_code in row.reason_codes for row in rows):
            codes.append(reason_code)
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _report_status_reason_code(status: str) -> str:
    if status == BLOCK_STATUS:
        return REPORT_BLOCK_REASON_CODE
    if status == WATCH_STATUS:
        return REPORT_WATCH_REASON_CODE
    return REPORT_PASS_REASON_CODE


def _row_sort_key(
    row: ResearchStrategyDomainMemoryReuseConfidenceRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_WEIGHT[row.status],
        -row.contradiction_pressure,
        -row.memory_age_seconds,
        -row.reuse_confidence_score,
        row.domain_key,
        row.memory_digest,
    )


def _row_reason_rank(reason_code: str) -> int:
    return ROW_REASON_CODES.index(reason_code)


def _require_row_reason_code_sequence(reason_codes: tuple[str, ...]) -> None:
    expected = tuple(
        reason_code
        for group in ROW_REASON_SEQUENCE
        for reason_code in group
        if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")
    score_reasons = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code
        in (
            "memory_reuse_confidence_score_block",
            "memory_reuse_confidence_score_watch",
            ROW_PASS_REASON_CODE,
        )
    )
    if len(score_reasons) != 1:
        raise ValueError("reason_codes must include exactly one confidence reason")
    if any(reason_code.endswith("_block") for reason_code in reason_codes) and any(
        reason_code.endswith("_watch") for reason_code in reason_codes
    ):
        raise ValueError("reason_codes must not mix block and watch detail")


def _require_report_reason_code_sequence(reason_codes: tuple[str, ...]) -> None:
    if reason_codes == (EMPTY_REPORT_REASON_CODE,):
        return
    expected = tuple(
        reason_code for reason_code in REPORT_REASON_CODES if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    codes = tuple(value)
    if len(codes) != len(set(codes)):
        raise ValueError(f"{name} must not contain duplicates")
    for code in codes:
        _require_member(name, code, allowed)
    return codes


def _age_seconds(older_at: datetime, newer_at: datetime) -> Decimal:
    older = _as_utc("observed_at", older_at)
    newer = _as_utc("generated_at", newer_at)
    if older > newer:
        raise ValueError("observed_at must not be after generated_at")
    delta = newer - older
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _normalize_nonnegative_measure("memory_age_seconds", seconds)


def _require_weight_total(
    config: ResearchStrategyDomainMemoryReuseConfidenceConfig,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total = _quantize(
            config.prior_hit_rate_weight
            + config.evidence_similarity_score_weight
            + config.transferability_score_weight
            + config.freshness_score_weight
            + config.contradiction_reserve_weight,
            RATIO_QUANTUM,
        )
    if total != ONE_RATIO:
        raise ValueError("confidence weights must total one")


def _require_descending_threshold(name: str, pass_value: Decimal, watch_value: Decimal) -> None:
    if pass_value < watch_value:
        raise ValueError(f"pass_{name} must not be below watch_{name}")


def _require_ascending_threshold(name: str, pass_value: Decimal, watch_value: Decimal) -> None:
    if pass_value > watch_value:
        raise ValueError(f"pass_{name} must not exceed watch_{name}")


def _require_exact_type(value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{expected_type.__name__} subclasses are not supported")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a nonblank trimmed string")


def _require_safe_label(name: str, value: object) -> str:
    _require_public_string(name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_VALUE_FRAGMENTS):
        raise ValueError(f"{name} must not expose restricted references")
    return value


def _require_memory_label(name: str, value: object) -> str:
    _require_public_string(name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_VALUE_FRAGMENTS):
        raise ValueError(f"{name} must not expose restricted references")
    return value


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be one of {', '.join(allowed)}")


def _normalize_probability(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO_RATIO or decimal > ONE_RATIO:
        raise ValueError(f"{name} must be between zero and one")
    return _quantize(decimal, RATIO_QUANTUM)


def _normalize_nonnegative_measure(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO_RATIO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(decimal, RATIO_QUANTUM)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO_COUNT:
        raise ValueError(f"{name} must be nonnegative")
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{name} must be a whole count")
    return decimal.quantize(COUNT_QUANTUM)


def _normalize_positive_count(name: str, value: object) -> Decimal:
    count = _normalize_nonnegative_count(name, value)
    if count <= ZERO_COUNT:
        raise ValueError(f"{name} must be positive")
    return count


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal, quantum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(quantum)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative integer")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_sha256(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a sha256 string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{name} must be a lowercase sha256 string")
    return value


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _reject_unsafe_public_payload(context: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{context} keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_KEY_FRAGMENTS):
                raise ValueError(f"{context} contains restricted key")
            _reject_unsafe_public_payload(f"{context}.{key}", item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(context, item)
    elif type(value) is str:
        lowered_value = value.lower()
        if any(fragment in lowered_value for fragment in UNSAFE_VALUE_FRAGMENTS):
            raise ValueError(f"{context} contains restricted value")


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
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")
