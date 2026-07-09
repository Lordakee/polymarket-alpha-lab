"""Report-only domain claim authority memory reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_CLAIM_AUTHORITY_MEMORY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_DOMAIN_CLAIM_AUTHORITY_MEMORY_STATUSES",
    "ResearchStrategyDomainClaimAuthorityMemoryConfig",
    "ResearchStrategyDomainClaimAuthorityMemoryInput",
    "ResearchStrategyDomainClaimAuthorityMemoryReasonCodeCount",
    "ResearchStrategyDomainClaimAuthorityMemoryReport",
    "ResearchStrategyDomainClaimAuthorityMemoryRow",
    "build_research_strategy_domain_claim_authority_memory_report",
    "research_strategy_domain_claim_authority_memory_report_digest",
    "research_strategy_domain_claim_authority_memory_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_DOMAIN_CLAIM_AUTHORITY_MEMORY_REPORT_CONFIG_VERSION = (
    "research-strategy-domain-claim-authority-memory-report-v0"
)
RESEARCH_STRATEGY_DOMAIN_CLAIM_AUTHORITY_MEMORY_STATUSES = (
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

AUTHORITY_SCORE_WEIGHT = Decimal("0.250000")
MEMORY_REUSE_WEIGHT = Decimal("0.200000")
CLAIM_CONFIDENCE_WEIGHT = Decimal("0.200000")
SOURCE_QUORUM_WEIGHT = Decimal("0.150000")
MEMORY_FRESHNESS_WEIGHT = Decimal("0.100000")
CONTRADICTION_RESERVE_WEIGHT = Decimal("0.100000")

STATUS_SEQUENCE = {
    BLOCK_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}

EMPTY_REPORT_REASON_CODE = "empty_domain_claim_authority_memory_inputs"
REPORT_PASS_REASON_CODE = "domain_claim_authority_memory_report_pass"
REPORT_WATCH_REASON_CODE = "domain_claim_authority_memory_report_watch"
REPORT_BLOCK_REASON_CODE = "domain_claim_authority_memory_report_block"
ROW_PASS_REASON_CODE = "authority_memory_pass"
ROW_REASON_CODES = (
    "authority_memory_score_block",
    "authority_memory_score_watch",
    ROW_PASS_REASON_CODE,
    "authority_score_block",
    "authority_score_watch",
    "memory_reuse_block",
    "memory_reuse_watch",
    "claim_confidence_block",
    "claim_confidence_watch",
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
    "source_quorum_block",
    "source_quorum_watch",
    "memory_age_block",
    "memory_age_watch",
)
REPORT_REASON_CODES = (
    REPORT_PASS_REASON_CODE,
    REPORT_WATCH_REASON_CODE,
    REPORT_BLOCK_REASON_CODE,
    *ROW_REASON_CODES,
    EMPTY_REPORT_REASON_CODE,
)
ROW_REASON_SEQUENCE = {
    reason_code: Decimal(index)
    for index, reason_code in enumerate(ROW_REASON_CODES)
}
REPORT_REASON_SEQUENCE = {
    reason_code: Decimal(index)
    for index, reason_code in enumerate(REPORT_REASON_CODES)
}

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DIGEST_REFERENCE_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_" + "cand" + "idate",
    "cand" + "idate_id",
    "cand" + "idate_sl" + "ug",
    "mar" + "ket_id",
    "mar" + "ket_sl" + "ug",
    "mar" + "ket_ques" + "tion",
    "ques" + "tion:",
    "sou" + "rce_u" + "rl",
    "sou" + "rce_tex" + "t",
    "d" + "sn",
    "tab" + "le",
    "tok" + "en",
    "wal" + "let",
    "ord" + "er",
    "tra" + "de",
    "li" + "ve",
    "net" + "work",
    "data" + "base",
    "://" ,
)


@dataclass(frozen=True)
class ResearchStrategyDomainClaimAuthorityMemoryConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_CLAIM_AUTHORITY_MEMORY_REPORT_CONFIG_VERSION
    )
    fresh_memory_age_seconds: Decimal = Decimal("3600.000000")
    stale_memory_age_seconds: Decimal = Decimal("86400.000000")
    pass_threshold: Decimal = Decimal("0.750000")
    watch_threshold: Decimal = Decimal("0.550000")
    min_pass_authority_score: Decimal = Decimal("0.800000")
    min_watch_authority_score: Decimal = Decimal("0.550000")
    min_pass_memory_reuse_score: Decimal = Decimal("0.750000")
    min_watch_memory_reuse_score: Decimal = Decimal("0.500000")
    min_pass_claim_confidence_score: Decimal = Decimal("0.800000")
    min_watch_claim_confidence_score: Decimal = Decimal("0.550000")
    max_pass_contradiction_pressure: Decimal = Decimal("0.200000")
    max_watch_contradiction_pressure: Decimal = Decimal("0.600000")
    min_pass_source_quorum_score: Decimal = Decimal("0.750000")
    min_watch_source_quorum_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainClaimAuthorityMemoryConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainClaimAuthorityMemoryConfig)
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_CLAIM_AUTHORITY_MEMORY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in ("fresh_memory_age_seconds", "stale_memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_measure(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_threshold",
            "watch_threshold",
            "min_pass_authority_score",
            "min_watch_authority_score",
            "min_pass_memory_reuse_score",
            "min_watch_memory_reuse_score",
            "min_pass_claim_confidence_score",
            "min_watch_claim_confidence_score",
            "max_pass_contradiction_pressure",
            "max_watch_contradiction_pressure",
            "min_pass_source_quorum_score",
            "min_watch_source_quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_memory_age_seconds <= self.fresh_memory_age_seconds:
            raise ValueError(
                "stale_memory_age_seconds must exceed fresh_memory_age_seconds",
            )
        _require_descending_pair(
            "threshold",
            self.pass_threshold,
            self.watch_threshold,
        )
        _require_descending_pair(
            "authority_score",
            self.min_pass_authority_score,
            self.min_watch_authority_score,
        )
        _require_descending_pair(
            "memory_reuse_score",
            self.min_pass_memory_reuse_score,
            self.min_watch_memory_reuse_score,
        )
        _require_descending_pair(
            "claim_confidence_score",
            self.min_pass_claim_confidence_score,
            self.min_watch_claim_confidence_score,
        )
        if self.max_watch_contradiction_pressure < self.max_pass_contradiction_pressure:
            raise ValueError(
                "max_watch_contradiction_pressure must be at least "
                "max_pass_contradiction_pressure",
            )
        _require_descending_pair(
            "source_quorum_score",
            self.min_pass_source_quorum_score,
            self.min_watch_source_quorum_score,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyDomainClaimAuthorityMemoryInput:
    domain_key: str
    claim_bucket: str
    private_candidate_reference: str
    private_market_reference: str
    private_source_reference: str
    claim_observed_at: datetime
    memory_recorded_at: datetime
    authority_score: Decimal
    memory_reuse_score: Decimal
    claim_confidence_score: Decimal
    contradiction_pressure: Decimal
    source_quorum_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainClaimAuthorityMemoryInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainClaimAuthorityMemoryInput)
        for field_name in ("domain_key", "claim_bucket"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "private_candidate_reference",
            "private_market_reference",
            "private_source_reference",
        ):
            _require_private_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "claim_observed_at",
            _as_utc("claim_observed_at", self.claim_observed_at),
        )
        object.__setattr__(
            self,
            "memory_recorded_at",
            _as_utc("memory_recorded_at", self.memory_recorded_at),
        )
        for field_name in (
            "authority_score",
            "memory_reuse_score",
            "claim_confidence_score",
            "contradiction_pressure",
            "source_quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyDomainClaimAuthorityMemoryRow:
    rank: Decimal
    domain_key: str
    claim_bucket: str
    claim_digest: str
    source_digest: str
    claim_age_seconds: Decimal
    memory_age_seconds: Decimal
    memory_freshness_score: Decimal
    authority_score: Decimal
    memory_reuse_score: Decimal
    claim_confidence_score: Decimal
    contradiction_pressure: Decimal
    source_quorum_score: Decimal
    authority_memory_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainClaimAuthorityMemoryRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainClaimAuthorityMemoryRow)
        object.__setattr__(self, "rank", _require_positive_count("rank", self.rank))
        for field_name in ("domain_key", "claim_bucket"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in ("claim_digest", "source_digest"):
            _require_digest_reference(field_name, getattr(self, field_name))
        for field_name in ("claim_age_seconds", "memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_measure(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_freshness_score",
            "authority_score",
            "memory_reuse_score",
            "claim_confidence_score",
            "contradiction_pressure",
            "source_quorum_score",
            "authority_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_row_consistency(self)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_row_reason_code_sequence(self.reason_codes)
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyDomainClaimAuthorityMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainClaimAuthorityMemoryReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainClaimAuthorityMemoryReasonCodeCount)
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count("count", self.count),
        )
        if self.count <= ZERO_COUNT:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyDomainClaimAuthorityMemoryReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_authority_memory_score: Decimal
    weakest_authority_memory_score: Decimal
    highest_contradiction_pressure: Decimal
    oldest_memory_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyDomainClaimAuthorityMemoryReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyDomainClaimAuthorityMemoryRow, ...]
    public_payload_sha256: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainClaimAuthorityMemoryReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainClaimAuthorityMemoryReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_CLAIM_AUTHORITY_MEMORY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in ("signal_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_authority_memory_score",
            "weakest_authority_memory_score",
            "highest_contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oldest_memory_age_seconds",
            _require_nonnegative_measure(
                "oldest_memory_age_seconds",
                self.oldest_memory_age_seconds,
            ),
        )
        _require_status("status", self.status)
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
        _reject_unsafe_public_payload("report", self)
        expected_sha256 = _report_public_payload_sha256(self)
        if self.public_payload_sha256:
            _require_sha256("public_payload_sha256", self.public_payload_sha256)
            if self.public_payload_sha256 != expected_sha256:
                raise ValueError("public_payload_sha256 must match report fields")
        object.__setattr__(self, "public_payload_sha256", expected_sha256)


def build_research_strategy_domain_claim_authority_memory_report(
    signals: tuple[ResearchStrategyDomainClaimAuthorityMemoryInput, ...]
    | list[ResearchStrategyDomainClaimAuthorityMemoryInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyDomainClaimAuthorityMemoryConfig | None = None,
) -> ResearchStrategyDomainClaimAuthorityMemoryReport:
    if config is None:
        config = ResearchStrategyDomainClaimAuthorityMemoryConfig()
    if type(config) is not ResearchStrategyDomainClaimAuthorityMemoryConfig:
        raise ValueError(
            "config must be a ResearchStrategyDomainClaimAuthorityMemoryConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(signals)
    for item in normalized_inputs:
        if item.claim_observed_at > generated_at_utc:
            raise ValueError("claim_observed_at must not be after generated_at")
        if item.memory_recorded_at > generated_at_utc:
            raise ValueError("memory_recorded_at must not be after generated_at")
    rows = _rank_rows(
        tuple(
            _row_for_input(
                item,
                generated_at=generated_at_utc,
                config=config,
            )
            for item in normalized_inputs
        ),
    )
    return ResearchStrategyDomainClaimAuthorityMemoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        signal_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, PASS_STATUS)),
        watch_count=_count(_status_count(rows, WATCH_STATUS)),
        block_count=_count(_status_count(rows, BLOCK_STATUS)),
        average_authority_memory_score=_average_ratio(
            tuple(row.authority_memory_score for row in rows),
        ),
        weakest_authority_memory_score=min(
            (row.authority_memory_score for row in rows),
            default=ZERO_RATIO,
        ),
        highest_contradiction_pressure=max(
            (row.contradiction_pressure for row in rows),
            default=ZERO_RATIO,
        ),
        oldest_memory_age_seconds=max(
            (row.memory_age_seconds for row in rows),
            default=ZERO_RATIO,
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_strategy_domain_claim_authority_memory_report_payload(
    report: ResearchStrategyDomainClaimAuthorityMemoryReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyDomainClaimAuthorityMemoryReport:
        _require_hard_flags("report", report)
        _validate_report_public_payload_sha256(report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyDomainClaimAuthorityMemoryReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload_schema(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_sha256(payload)
    return payload


def research_strategy_domain_claim_authority_memory_report_digest(
    report: ResearchStrategyDomainClaimAuthorityMemoryReport,
) -> str:
    if type(report) is not ResearchStrategyDomainClaimAuthorityMemoryReport:
        raise ValueError(
            "report must be a ResearchStrategyDomainClaimAuthorityMemoryReport",
        )
    _require_hard_flags("report", report)
    _validate_report_public_payload_sha256(report)
    return report.public_payload_sha256


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        if "paper_only" not in self.value:
            return None
        return self.value["paper_only"]

    @property
    def report_only(self) -> object:
        if "report_only" not in self.value:
            return None
        return self.value["report_only"]

    @property
    def readonly(self) -> object:
        if "readonly" not in self.value:
            return None
        return self.value["readonly"]


REPORT_PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "signal_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_authority_memory_score",
        "weakest_authority_memory_score",
        "highest_contradiction_pressure",
        "oldest_memory_age_seconds",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "public_payload_sha256",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "rank",
        "domain_key",
        "claim_bucket",
        "claim_digest",
        "source_digest",
        "claim_age_seconds",
        "memory_age_seconds",
        "memory_freshness_score",
        "authority_score",
        "memory_reuse_score",
        "claim_confidence_score",
        "contradiction_pressure",
        "source_quorum_score",
        "authority_memory_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_CODE_COUNT_PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_payload_keys("public payload", payload, REPORT_PUBLIC_PAYLOAD_KEYS)
    report = ResearchStrategyDomainClaimAuthorityMemoryReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_str("config_version", payload["config_version"]),
        signal_count=_payload_decimal("signal_count", payload["signal_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        average_authority_memory_score=_payload_decimal(
            "average_authority_memory_score",
            payload["average_authority_memory_score"],
        ),
        weakest_authority_memory_score=_payload_decimal(
            "weakest_authority_memory_score",
            payload["weakest_authority_memory_score"],
        ),
        highest_contradiction_pressure=_payload_decimal(
            "highest_contradiction_pressure",
            payload["highest_contradiction_pressure"],
        ),
        oldest_memory_age_seconds=_payload_decimal(
            "oldest_memory_age_seconds",
            payload["oldest_memory_age_seconds"],
        ),
        status=_payload_str("status", payload["status"]),
        reason_codes=_payload_str_tuple("reason_codes", payload["reason_codes"]),
        reason_code_counts=tuple(
            _payload_reason_code_count(item)
            for item in _payload_list(
                "reason_code_counts",
                payload["reason_code_counts"],
            )
        ),
        rows=tuple(_payload_row(item) for item in _payload_list("rows", payload["rows"])),
        public_payload_sha256=_payload_str(
            "public_payload_sha256",
            payload["public_payload_sha256"],
        ),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )
    canonical_payload = _json_ready(asdict(report))
    if payload != canonical_payload:
        raise ValueError("public payload must be canonical")


def _payload_row(value: Any) -> ResearchStrategyDomainClaimAuthorityMemoryRow:
    if type(value) is not dict:
        raise ValueError("row must be a JSON object")
    _require_payload_keys("row", value, ROW_PUBLIC_PAYLOAD_KEYS)
    return ResearchStrategyDomainClaimAuthorityMemoryRow(
        rank=_payload_decimal("rank", value["rank"]),
        domain_key=_payload_str("domain_key", value["domain_key"]),
        claim_bucket=_payload_str("claim_bucket", value["claim_bucket"]),
        claim_digest=_payload_str("claim_digest", value["claim_digest"]),
        source_digest=_payload_str("source_digest", value["source_digest"]),
        claim_age_seconds=_payload_decimal(
            "claim_age_seconds",
            value["claim_age_seconds"],
        ),
        memory_age_seconds=_payload_decimal(
            "memory_age_seconds",
            value["memory_age_seconds"],
        ),
        memory_freshness_score=_payload_decimal(
            "memory_freshness_score",
            value["memory_freshness_score"],
        ),
        authority_score=_payload_decimal("authority_score", value["authority_score"]),
        memory_reuse_score=_payload_decimal(
            "memory_reuse_score",
            value["memory_reuse_score"],
        ),
        claim_confidence_score=_payload_decimal(
            "claim_confidence_score",
            value["claim_confidence_score"],
        ),
        contradiction_pressure=_payload_decimal(
            "contradiction_pressure",
            value["contradiction_pressure"],
        ),
        source_quorum_score=_payload_decimal(
            "source_quorum_score",
            value["source_quorum_score"],
        ),
        authority_memory_score=_payload_decimal(
            "authority_memory_score",
            value["authority_memory_score"],
        ),
        status=_payload_str("status", value["status"]),
        reason_codes=_payload_str_tuple("reason_codes", value["reason_codes"]),
        paper_only=_payload_bool("paper_only", value["paper_only"]),
        report_only=_payload_bool("report_only", value["report_only"]),
        readonly=_payload_bool("readonly", value["readonly"]),
    )


def _payload_reason_code_count(
    value: Any,
) -> ResearchStrategyDomainClaimAuthorityMemoryReasonCodeCount:
    if type(value) is not dict:
        raise ValueError("reason_code_count must be a JSON object")
    _require_payload_keys(
        "reason_code_count",
        value,
        REASON_CODE_COUNT_PUBLIC_PAYLOAD_KEYS,
    )
    return ResearchStrategyDomainClaimAuthorityMemoryReasonCodeCount(
        reason_code=_payload_str("reason_code", value["reason_code"]),
        count=_payload_decimal("count", value["count"]),
        paper_only=_payload_bool("paper_only", value["paper_only"]),
        report_only=_payload_bool("report_only", value["report_only"]),
        readonly=_payload_bool("readonly", value["readonly"]),
    )


def _require_payload_keys(
    field_name: str,
    payload: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    if frozenset(payload.keys()) != expected_keys:
        raise ValueError(f"{field_name} keys must match public payload schema")


def _payload_str(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_bool(field_name: str, value: Any) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _payload_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc


def _payload_datetime(field_name: str, value: Any) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc


def _payload_list(field_name: str, value: Any) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    return value


def _payload_str_tuple(field_name: str, value: Any) -> tuple[str, ...]:
    return tuple(
        _payload_str(f"{field_name} item", item)
        for item in _payload_list(field_name, value)
    )


def _row_for_input(
    item: ResearchStrategyDomainClaimAuthorityMemoryInput,
    *,
    generated_at: datetime,
    config: ResearchStrategyDomainClaimAuthorityMemoryConfig,
) -> ResearchStrategyDomainClaimAuthorityMemoryRow:
    claim_age_seconds = _age_seconds(item.claim_observed_at, generated_at)
    memory_age_seconds = _age_seconds(item.memory_recorded_at, generated_at)
    memory_freshness_score = _memory_freshness_score(memory_age_seconds, config=config)
    authority_memory_score = _authority_memory_score(
        authority_score=item.authority_score,
        memory_reuse_score=item.memory_reuse_score,
        claim_confidence_score=item.claim_confidence_score,
        contradiction_pressure=item.contradiction_pressure,
        source_quorum_score=item.source_quorum_score,
        memory_freshness_score=memory_freshness_score,
    )
    reason_codes = _row_reason_codes(
        authority_score=item.authority_score,
        memory_reuse_score=item.memory_reuse_score,
        claim_confidence_score=item.claim_confidence_score,
        contradiction_pressure=item.contradiction_pressure,
        source_quorum_score=item.source_quorum_score,
        memory_age_seconds=memory_age_seconds,
        authority_memory_score=authority_memory_score,
        config=config,
    )
    return ResearchStrategyDomainClaimAuthorityMemoryRow(
        rank=COUNT_QUANTUM,
        domain_key=item.domain_key,
        claim_bucket=item.claim_bucket,
        claim_digest=_digest_reference(
            "claim",
            item.domain_key,
            item.claim_bucket,
            item.private_candidate_reference,
            item.private_market_reference,
        ),
        source_digest=_digest_reference(
            "source",
            item.domain_key,
            item.claim_bucket,
            item.private_source_reference,
        ),
        claim_age_seconds=claim_age_seconds,
        memory_age_seconds=memory_age_seconds,
        memory_freshness_score=memory_freshness_score,
        authority_score=item.authority_score,
        memory_reuse_score=item.memory_reuse_score,
        claim_confidence_score=item.claim_confidence_score,
        contradiction_pressure=item.contradiction_pressure,
        source_quorum_score=item.source_quorum_score,
        authority_memory_score=authority_memory_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _rank_rows(
    rows: tuple[ResearchStrategyDomainClaimAuthorityMemoryRow, ...],
) -> tuple[ResearchStrategyDomainClaimAuthorityMemoryRow, ...]:
    return tuple(
        ResearchStrategyDomainClaimAuthorityMemoryRow(
            rank=_count(index),
            domain_key=row.domain_key,
            claim_bucket=row.claim_bucket,
            claim_digest=row.claim_digest,
            source_digest=row.source_digest,
            claim_age_seconds=row.claim_age_seconds,
            memory_age_seconds=row.memory_age_seconds,
            memory_freshness_score=row.memory_freshness_score,
            authority_score=row.authority_score,
            memory_reuse_score=row.memory_reuse_score,
            claim_confidence_score=row.claim_confidence_score,
            contradiction_pressure=row.contradiction_pressure,
            source_quorum_score=row.source_quorum_score,
            authority_memory_score=row.authority_memory_score,
            status=row.status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_reason_codes(
    *,
    authority_score: Decimal,
    memory_reuse_score: Decimal,
    claim_confidence_score: Decimal,
    contradiction_pressure: Decimal,
    source_quorum_score: Decimal,
    memory_age_seconds: Decimal,
    authority_memory_score: Decimal,
    config: ResearchStrategyDomainClaimAuthorityMemoryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if authority_memory_score < config.watch_threshold:
        reason_codes.append("authority_memory_score_block")
    elif authority_memory_score < config.pass_threshold:
        reason_codes.append("authority_memory_score_watch")
    if authority_score < config.min_watch_authority_score:
        reason_codes.append("authority_score_block")
    elif authority_score < config.min_pass_authority_score:
        reason_codes.append("authority_score_watch")
    if memory_reuse_score < config.min_watch_memory_reuse_score:
        reason_codes.append("memory_reuse_block")
    elif memory_reuse_score < config.min_pass_memory_reuse_score:
        reason_codes.append("memory_reuse_watch")
    if claim_confidence_score < config.min_watch_claim_confidence_score:
        reason_codes.append("claim_confidence_block")
    elif claim_confidence_score < config.min_pass_claim_confidence_score:
        reason_codes.append("claim_confidence_watch")
    if contradiction_pressure >= config.max_watch_contradiction_pressure:
        reason_codes.append("contradiction_pressure_block")
    elif contradiction_pressure >= config.max_pass_contradiction_pressure:
        reason_codes.append("contradiction_pressure_watch")
    if source_quorum_score < config.min_watch_source_quorum_score:
        reason_codes.append("source_quorum_block")
    elif source_quorum_score < config.min_pass_source_quorum_score:
        reason_codes.append("source_quorum_watch")
    if memory_age_seconds >= config.stale_memory_age_seconds:
        reason_codes.append("memory_age_block")
    elif memory_age_seconds > config.fresh_memory_age_seconds:
        reason_codes.append("memory_age_watch")
    if not reason_codes:
        return (ROW_PASS_REASON_CODE,)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _authority_memory_score(
    *,
    authority_score: Decimal,
    memory_reuse_score: Decimal,
    claim_confidence_score: Decimal,
    contradiction_pressure: Decimal,
    source_quorum_score: Decimal,
    memory_freshness_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        raw_score = (
            (authority_score * AUTHORITY_SCORE_WEIGHT)
            + (memory_reuse_score * MEMORY_REUSE_WEIGHT)
            + (claim_confidence_score * CLAIM_CONFIDENCE_WEIGHT)
            + (source_quorum_score * SOURCE_QUORUM_WEIGHT)
            + (memory_freshness_score * MEMORY_FRESHNESS_WEIGHT)
            + ((ONE_RATIO - contradiction_pressure) * CONTRADICTION_RESERVE_WEIGHT)
        )
    return _quantize_ratio(raw_score)


def _memory_freshness_score(
    memory_age_seconds: Decimal,
    *,
    config: ResearchStrategyDomainClaimAuthorityMemoryConfig,
) -> Decimal:
    if memory_age_seconds <= config.fresh_memory_age_seconds:
        return ONE_RATIO
    if memory_age_seconds >= config.stale_memory_age_seconds:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        stale_window = config.stale_memory_age_seconds - config.fresh_memory_age_seconds
        stale_progress = (memory_age_seconds - config.fresh_memory_age_seconds) / stale_window
        return _quantize_ratio(ONE_RATIO - stale_progress)


def _report_status(
    rows: tuple[ResearchStrategyDomainClaimAuthorityMemoryRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainClaimAuthorityMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _report_status(rows)
    if status == BLOCK_STATUS:
        report_code = REPORT_BLOCK_REASON_CODE
    elif status == WATCH_STATUS:
        report_code = REPORT_WATCH_REASON_CODE
    else:
        report_code = REPORT_PASS_REASON_CODE
    row_codes = {code for row in rows for code in row.reason_codes}
    return _normalize_reason_codes(
        "reason_codes",
        (report_code, *sorted(row_codes, key=_report_reason_rank)),
        REPORT_REASON_CODES,
    )


def _reason_code_counts(
    rows: tuple[ResearchStrategyDomainClaimAuthorityMemoryRow, ...],
) -> tuple[ResearchStrategyDomainClaimAuthorityMemoryReasonCodeCount, ...]:
    counts = Counter(code for row in rows for code in row.reason_codes)
    return tuple(
        ResearchStrategyDomainClaimAuthorityMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: _row_reason_rank(item[0]),
        )
    )


def _status_count(
    rows: tuple[ResearchStrategyDomainClaimAuthorityMemoryRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(sum(values, ZERO_RATIO) / Decimal(len(values)))


def _age_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("start time must not be after end time")
    delta = end - start
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            (Decimal(delta.days) * SECONDS_PER_DAY)
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    return _require_nonnegative_measure("age_seconds", seconds)


def _normalize_inputs(
    signals: tuple[ResearchStrategyDomainClaimAuthorityMemoryInput, ...]
    | list[ResearchStrategyDomainClaimAuthorityMemoryInput],
) -> tuple[ResearchStrategyDomainClaimAuthorityMemoryInput, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    for item in normalized:
        if type(item) is not ResearchStrategyDomainClaimAuthorityMemoryInput:
            raise ValueError(
                "signals must contain ResearchStrategyDomainClaimAuthorityMemoryInput",
            )
        _require_hard_flags("input", item)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyDomainClaimAuthorityMemoryRow, ...],
) -> tuple[ResearchStrategyDomainClaimAuthorityMemoryRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    expected_rank = COUNT_QUANTUM
    for row in normalized:
        if type(row) is not ResearchStrategyDomainClaimAuthorityMemoryRow:
            raise ValueError("rows must contain ResearchStrategyDomainClaimAuthorityMemoryRow")
        if row.rank != expected_rank:
            raise ValueError("rows must use contiguous Decimal ranks")
        expected_rank = _count(int(expected_rank) + 1)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return normalized


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyDomainClaimAuthorityMemoryReasonCodeCount, ...],
) -> tuple[ResearchStrategyDomainClaimAuthorityMemoryReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(counts)
    for item in normalized:
        if type(item) is not ResearchStrategyDomainClaimAuthorityMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyDomainClaimAuthorityMemoryReasonCodeCount",
            )
    if normalized != tuple(sorted(normalized, key=lambda item: _row_reason_rank(item.reason_code))):
        raise ValueError("reason_code_counts must use deterministic sequence")
    return normalized


def _validate_report(report: ResearchStrategyDomainClaimAuthorityMemoryReport) -> None:
    rows = report.rows
    if report.signal_count != _count(len(rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _count(_status_count(rows, PASS_STATUS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(rows, WATCH_STATUS)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(rows, BLOCK_STATUS)):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.average_authority_memory_score != _average_ratio(
        tuple(row.authority_memory_score for row in rows),
    ):
        raise ValueError("average_authority_memory_score must match rows")
    if report.weakest_authority_memory_score != min(
        (row.authority_memory_score for row in rows),
        default=ZERO_RATIO,
    ):
        raise ValueError("weakest_authority_memory_score must match rows")
    if report.highest_contradiction_pressure != max(
        (row.contradiction_pressure for row in rows),
        default=ZERO_RATIO,
    ):
        raise ValueError("highest_contradiction_pressure must match rows")
    if report.oldest_memory_age_seconds != max(
        (row.memory_age_seconds for row in rows),
        default=ZERO_RATIO,
    ):
        raise ValueError("oldest_memory_age_seconds must match rows")


def _validate_row_consistency(
    row: ResearchStrategyDomainClaimAuthorityMemoryRow,
) -> None:
    expected_authority_memory_score = _authority_memory_score(
        authority_score=row.authority_score,
        memory_reuse_score=row.memory_reuse_score,
        claim_confidence_score=row.claim_confidence_score,
        contradiction_pressure=row.contradiction_pressure,
        source_quorum_score=row.source_quorum_score,
        memory_freshness_score=row.memory_freshness_score,
    )
    if row.authority_memory_score != expected_authority_memory_score:
        raise ValueError("authority_memory_score must match row inputs")


def _row_sort_key(row: ResearchStrategyDomainClaimAuthorityMemoryRow) -> tuple[Any, ...]:
    return (
        STATUS_SEQUENCE[row.status],
        row.authority_memory_score,
        row.domain_key,
        row.claim_bucket,
        row.claim_digest,
        row.source_digest,
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return BLOCK_STATUS
    if any(code.endswith("_watch") for code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _require_row_reason_code_sequence(reason_codes: tuple[str, ...]) -> None:
    if tuple(sorted(reason_codes, key=_row_reason_rank)) != reason_codes:
        raise ValueError("reason_codes must use deterministic sequence")


def _require_report_reason_code_sequence(reason_codes: tuple[str, ...]) -> None:
    if tuple(sorted(reason_codes, key=_report_reason_rank)) != reason_codes:
        raise ValueError("reason_codes must use deterministic sequence")


def _row_reason_rank(reason_code: str) -> Decimal:
    return ROW_REASON_SEQUENCE[reason_code]


def _report_reason_rank(reason_code: str) -> Decimal:
    return REPORT_REASON_SEQUENCE[reason_code]


def _digest_reference(*parts: str) -> str:
    canonical = json.dumps(
        tuple(parts),
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return f"sha256:{sha256(canonical.encode('utf-8')).hexdigest()}"


def _report_public_payload_sha256(
    report: ResearchStrategyDomainClaimAuthorityMemoryReport,
) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("public_payload_sha256", None)
    return _payload_sha256(payload)


def _validate_report_public_payload_sha256(
    report: ResearchStrategyDomainClaimAuthorityMemoryReport,
) -> None:
    expected = _report_public_payload_sha256(report)
    if report.public_payload_sha256 != expected:
        raise ValueError("public_payload_sha256 must match report fields")


def _validate_payload_sha256(payload: dict[str, Any]) -> None:
    if "public_payload_sha256" not in payload:
        raise ValueError("public_payload_sha256 must be present")
    digest = payload["public_payload_sha256"]
    if type(digest) is not str:
        raise ValueError("public_payload_sha256 must be present")
    _require_sha256("public_payload_sha256", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("public_payload_sha256", None)
    if digest != _payload_sha256(unsigned_payload):
        raise ValueError("public_payload_sha256 must match payload")


def _payload_sha256(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("public numeric values must be Decimal")
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _require_exact_type(value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"value must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_private_text(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must be nonempty")


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_measure(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_measure(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_measure(field_name, value)
    if normalized <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_input_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    for reason_code in normalized:
        if type(reason_code) is not str or not REASON_CODE_RE.fullmatch(reason_code):
            raise ValueError("reason_codes must contain public reason codes")
    return tuple(sorted(set(normalized)))


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in normalized:
        _require_member(field_name, reason_code, allowed_reason_codes)
    return normalized


def _require_member(
    field_name: str,
    value: str,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_status(field_name: str, value: str) -> None:
    _require_member(field_name, value, RESEARCH_STRATEGY_DOMAIN_CLAIM_AUTHORITY_MEMORY_STATUSES)


def _require_digest_reference(field_name: str, value: str) -> None:
    if type(value) is not str or not DIGEST_REFERENCE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest reference")


def _require_sha256(field_name: str, value: str) -> None:
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_descending_pair(field_name: str, high_value: Decimal, low_value: Decimal) -> None:
    if high_value < low_value:
        raise ValueError(f"{field_name} pass value must be at least watch value")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _reject_unsafe_public_payload(field_name: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(field_name, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is str:
                _reject_unsafe_public_string(f"{field_name} key", key)
            _reject_unsafe_public_payload(field_name, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(field_name, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(field_name, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public reference")
