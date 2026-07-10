"""Pure report-only claim memory authority floor report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json
import re


DEFAULT_RESEARCH_SOURCE_CLAIM_MEMORY_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION = (
    "research-source-claim-memory-authority-floor-report-v0"
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PRIVATE_DIGEST_PREFIX = "sha256:"
STATUSES = ("pass", "watch", "block")
PASS_REASON = "authority_floor_pass"
WATCH_REASON = "authority_floor_watch"
BLOCK_REASON = "authority_floor_block"
STALE_REASON = "authority_memory_stale"
CONTRADICTION_WATCH_REASON = "contradiction_risk_watch"
CONTRADICTION_BLOCK_REASON = "contradiction_risk_block"
EMPTY_REASON = "no_claim_memory_authority_inputs"

PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate_id",
    "candidate-private",
    "candidate_private",
    "market-private",
    "market_private",
    "market_slug",
    "market_question",
    "will alpha resolve",
    "://",
    "www.",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "order=",
    "live feed",
    "source url",
    "source text",
    "private_candidate_reference",
    "private_market_reference",
    "private_source_reference",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CLAIM_MEMORY_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION",
    "ResearchSourceClaimMemoryAuthorityFloorConfig",
    "ResearchSourceClaimMemoryAuthorityFloorInput",
    "ResearchSourceClaimMemoryAuthorityFloorReport",
    "ResearchSourceClaimMemoryAuthorityFloorRow",
    "build_research_source_claim_memory_authority_floor_report",
    "research_source_claim_memory_authority_floor_report_digest",
    "research_source_claim_memory_authority_floor_report_public_payload",
    "validate_research_source_claim_memory_authority_floor_report_public_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchSourceClaimMemoryAuthorityFloorConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CLAIM_MEMORY_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION
    )
    fresh_authority_age_seconds: Decimal = Decimal("3600.000000")
    stale_authority_age_seconds: Decimal = Decimal("86400.000000")
    pass_authority_floor_score: Decimal = Decimal("0.800000")
    watch_authority_floor_score: Decimal = Decimal("0.550000")
    watch_contradiction_risk_score: Decimal = Decimal("0.300000")
    block_contradiction_risk_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimMemoryAuthorityFloorConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in ("fresh_authority_age_seconds", "stale_authority_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_authority_floor_score",
            "watch_authority_floor_score",
            "watch_contradiction_risk_score",
            "block_contradiction_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_authority_age_seconds <= self.fresh_authority_age_seconds:
            raise ValueError(
                "stale_authority_age_seconds must exceed fresh_authority_age_seconds",
            )
        if self.pass_authority_floor_score <= self.watch_authority_floor_score:
            raise ValueError(
                "pass_authority_floor_score must exceed watch_authority_floor_score",
            )
        if self.block_contradiction_risk_score <= self.watch_contradiction_risk_score:
            raise ValueError(
                "block_contradiction_risk_score must exceed "
                "watch_contradiction_risk_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimMemoryAuthorityFloorInput(_FinalPublicDataclass):
    claim_bucket: str
    authority_bucket: str
    private_candidate_reference: str
    private_market_reference: str
    private_source_reference: str
    observed_at: datetime
    authority_updated_at: datetime
    authority_score: Decimal
    memory_confidence_score: Decimal
    evidence_coverage_score: Decimal
    contradiction_risk_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimMemoryAuthorityFloorInput, "input")
        _require_public_string("claim_bucket", self.claim_bucket)
        _require_public_string("authority_bucket", self.authority_bucket)
        for field_name in (
            "private_candidate_reference",
            "private_market_reference",
            "private_source_reference",
        ):
            _require_nonempty_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "authority_updated_at",
            _as_utc("authority_updated_at", self.authority_updated_at),
        )
        for field_name in (
            "authority_score",
            "memory_confidence_score",
            "evidence_coverage_score",
            "contradiction_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceClaimMemoryAuthorityFloorRow(_FinalPublicDataclass):
    claim_bucket: str
    authority_bucket: str
    claim_ref_digest: str
    authority_ref_digest: str
    observed_at: datetime
    authority_updated_at: datetime
    authority_age_seconds: Decimal
    authority_score: Decimal
    memory_confidence_score: Decimal
    evidence_coverage_score: Decimal
    contradiction_risk_score: Decimal
    authority_recency_score: Decimal
    authority_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimMemoryAuthorityFloorRow, "row")
        _require_public_string("claim_bucket", self.claim_bucket)
        _require_public_string("authority_bucket", self.authority_bucket)
        for field_name in ("claim_ref_digest", "authority_ref_digest"):
            _require_private_digest(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "authority_updated_at",
            _as_utc("authority_updated_at", self.authority_updated_at),
        )
        object.__setattr__(
            self,
            "authority_age_seconds",
            _require_nonnegative_decimal(
                "authority_age_seconds",
                self.authority_age_seconds,
            ),
        )
        for field_name in (
            "authority_score",
            "memory_confidence_score",
            "evidence_coverage_score",
            "contradiction_risk_score",
            "authority_recency_score",
            "authority_floor_score",
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
        expected_floor_score = _min_ratio(
            (
                self.authority_score,
                self.memory_confidence_score,
                self.evidence_coverage_score,
                self.authority_recency_score,
            ),
        )
        if self.authority_floor_score != expected_floor_score:
            raise ValueError("authority_floor_score must match row scores")
        _require_status_reason_code(self.status, self.reason_codes)
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload(_row_public_payload(self))


@dataclass(frozen=True)
class ResearchSourceClaimMemoryAuthorityFloorReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    fresh_authority_age_seconds: Decimal
    stale_authority_age_seconds: Decimal
    pass_authority_floor_score: Decimal
    watch_authority_floor_score: Decimal
    watch_contradiction_risk_score: Decimal
    block_contradiction_risk_score: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_authority_count: Decimal
    low_authority_floor_count: Decimal
    contradiction_risk_count: Decimal
    average_authority_floor_score: Decimal
    max_authority_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceClaimMemoryAuthorityFloorRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimMemoryAuthorityFloorReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        config = ResearchSourceClaimMemoryAuthorityFloorConfig(
            config_version=self.config_version,
            fresh_authority_age_seconds=self.fresh_authority_age_seconds,
            stale_authority_age_seconds=self.stale_authority_age_seconds,
            pass_authority_floor_score=self.pass_authority_floor_score,
            watch_authority_floor_score=self.watch_authority_floor_score,
            watch_contradiction_risk_score=self.watch_contradiction_risk_score,
            block_contradiction_risk_score=self.block_contradiction_risk_score,
            paper_only=self.paper_only,
            report_only=self.report_only,
            readonly=self.readonly,
        )
        for field_name in (
            "fresh_authority_age_seconds",
            "stale_authority_age_seconds",
            "pass_authority_floor_score",
            "watch_authority_floor_score",
            "watch_contradiction_risk_score",
            "block_contradiction_risk_score",
        ):
            object.__setattr__(self, field_name, getattr(config, field_name))
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_authority_count",
            "low_authority_floor_count",
            "contradiction_risk_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_authority_floor_score",
            "max_authority_floor_score",
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
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_counts(self, config=config)
        _require_hard_flags("report", self)
        expected_digest = research_source_claim_memory_authority_floor_report_digest(
            _report_public_payload(self, include_digest=False),
        )
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _reject_unsafe_public_payload(_report_public_payload(self, include_digest=True))


def build_research_source_claim_memory_authority_floor_report(
    rows: tuple[ResearchSourceClaimMemoryAuthorityFloorInput, ...],
    *,
    config: ResearchSourceClaimMemoryAuthorityFloorConfig,
    generated_at: datetime,
) -> ResearchSourceClaimMemoryAuthorityFloorReport:
    config = _revalidate_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(rows)
    report_rows = tuple(
        sorted(
            (
                _build_row(row, config=config, generated_at=generated_at_utc)
                for row in inputs
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(report_rows)
    return ResearchSourceClaimMemoryAuthorityFloorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        fresh_authority_age_seconds=config.fresh_authority_age_seconds,
        stale_authority_age_seconds=config.stale_authority_age_seconds,
        pass_authority_floor_score=config.pass_authority_floor_score,
        watch_authority_floor_score=config.watch_authority_floor_score,
        watch_contradiction_risk_score=config.watch_contradiction_risk_score,
        block_contradiction_risk_score=config.block_contradiction_risk_score,
        row_count=_count(len(report_rows)),
        pass_count=_status_count(report_rows, "pass"),
        watch_count=_status_count(report_rows, "watch"),
        block_count=_status_count(report_rows, "block"),
        stale_authority_count=_count(
            sum(1 for row in report_rows if STALE_REASON in row.reason_codes),
        ),
        low_authority_floor_count=_count(
            sum(
                1
                for row in report_rows
                if row.authority_floor_score < config.pass_authority_floor_score
            ),
        ),
        contradiction_risk_count=_count(
            sum(
                1
                for row in report_rows
                if row.contradiction_risk_score
                >= config.watch_contradiction_risk_score
            ),
        ),
        average_authority_floor_score=_average(
            tuple(row.authority_floor_score for row in report_rows),
        ),
        max_authority_floor_score=_max_ratio(
            tuple(row.authority_floor_score for row in report_rows),
        ),
        status=_rollup_status(tuple(row.status for row in report_rows)),
        reason_codes=reason_codes,
        rows=report_rows,
    )


def research_source_claim_memory_authority_floor_report_public_payload(
    report: ResearchSourceClaimMemoryAuthorityFloorReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is dict:
        validate_research_source_claim_memory_authority_floor_report_public_payload(
            report,
        )
        return report
    if type(report) is not ResearchSourceClaimMemoryAuthorityFloorReport:
        raise ValueError("report must be a ResearchSourceClaimMemoryAuthorityFloorReport")
    expected_digest = research_source_claim_memory_authority_floor_report_digest(
        _report_public_payload(report, include_digest=False),
    )
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report payload")
    payload = _report_public_payload(report, include_digest=True)
    validate_research_source_claim_memory_authority_floor_report_public_payload(
        payload,
    )
    return payload


def validate_research_source_claim_memory_authority_floor_report_public_payload(
    payload: dict[str, object],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(payload)
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest("derived_validation_digest", digest)
    digest_material = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    expected_digest = research_source_claim_memory_authority_floor_report_digest(
        digest_material,
    )
    if digest != expected_digest:
        raise ValueError("derived_validation_digest must match public payload")
    _validate_public_payload_schema(payload)
    return True


def research_source_claim_memory_authority_floor_report_digest(
    payload: dict[str, object],
) -> str:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_canonical_public_json_value(payload)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_public_payload_schema(payload: dict[str, object]) -> None:
    expected_keys = {
        "generated_at",
        "config_version",
        "fresh_authority_age_seconds",
        "stale_authority_age_seconds",
        "pass_authority_floor_score",
        "watch_authority_floor_score",
        "watch_contradiction_risk_score",
        "block_contradiction_risk_score",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "stale_authority_count",
        "low_authority_floor_count",
        "contradiction_risk_count",
        "average_authority_floor_score",
        "max_authority_floor_score",
        "status",
        "reason_codes",
        "rows",
        "paper_only",
        "report_only",
        "readonly",
        "derived_validation_digest",
    }
    if set(payload) != expected_keys:
        raise ValueError("public payload schema keys must match report schema")
    generated_at = _require_datetime_payload("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    _require_public_true_flag("paper_only", payload["paper_only"])
    _require_public_true_flag("report_only", payload["report_only"])
    _require_public_true_flag("readonly", payload["readonly"])
    config = ResearchSourceClaimMemoryAuthorityFloorConfig(
        config_version=payload["config_version"],
        fresh_authority_age_seconds=_require_positive_decimal_payload(
            "fresh_authority_age_seconds",
            payload["fresh_authority_age_seconds"],
        ),
        stale_authority_age_seconds=_require_positive_decimal_payload(
            "stale_authority_age_seconds",
            payload["stale_authority_age_seconds"],
        ),
        pass_authority_floor_score=_require_ratio_decimal_payload(
            "pass_authority_floor_score",
            payload["pass_authority_floor_score"],
        ),
        watch_authority_floor_score=_require_ratio_decimal_payload(
            "watch_authority_floor_score",
            payload["watch_authority_floor_score"],
        ),
        watch_contradiction_risk_score=_require_ratio_decimal_payload(
            "watch_contradiction_risk_score",
            payload["watch_contradiction_risk_score"],
        ),
        block_contradiction_risk_score=_require_ratio_decimal_payload(
            "block_contradiction_risk_score",
            payload["block_contradiction_risk_score"],
        ),
    )
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    row_payloads = [_validate_public_row_payload(row) for row in rows_value]
    _require_unique_row_identities(
        tuple(
            (
                row["claim_ref_digest"],
                row["authority_ref_digest"],
            )
            for row in row_payloads
        ),
    )
    row_sort_keys = tuple(_public_row_sort_key(row) for row in row_payloads)
    if row_sort_keys != tuple(sorted(row_sort_keys)):
        raise ValueError("rows must be in canonical order")
    for row in row_payloads:
        _validate_public_row_consistency(
            row,
            config=config,
            generated_at=generated_at,
        )
    for field_name in (
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "stale_authority_count",
        "low_authority_floor_count",
        "contradiction_risk_count",
    ):
        _require_decimal_payload(field_name, payload[field_name])
    for field_name in (
        "average_authority_floor_score",
        "max_authority_floor_score",
    ):
        _require_ratio_decimal_payload(field_name, payload[field_name])
    _require_status("status", payload["status"])
    reason_codes = _require_reason_code_list("reason_codes", payload["reason_codes"])
    statuses = tuple(row["status"] for row in row_payloads)
    if payload["status"] != _rollup_status(statuses):
        raise ValueError("status must match public rows")
    if payload["row_count"] != _decimal_payload(_count(len(row_payloads))):
        raise ValueError("row_count must match public rows")
    for status in STATUSES:
        expected_count = _count(sum(1 for row in row_payloads if row["status"] == status))
        if payload[f"{status}_count"] != _decimal_payload(expected_count):
            raise ValueError(f"{status}_count must match public rows")
    stale_count = _count(
        sum(
            1
            for row in row_payloads
            if row["authority_age_seconds"] >= config.stale_authority_age_seconds
        ),
    )
    if payload["stale_authority_count"] != _decimal_payload(stale_count):
        raise ValueError("stale_authority_count must match public rows")
    low_authority_floor_count = _count(
        sum(
            1
            for row in row_payloads
            if row["authority_floor_score"] < config.pass_authority_floor_score
        ),
    )
    if payload["low_authority_floor_count"] != _decimal_payload(
        low_authority_floor_count,
    ):
        raise ValueError("low_authority_floor_count must match public rows")
    contradiction_count = _count(
        sum(
            1
            for row in row_payloads
            if row["contradiction_risk_score"]
            >= config.watch_contradiction_risk_score
        ),
    )
    if payload["contradiction_risk_count"] != _decimal_payload(contradiction_count):
        raise ValueError("contradiction_risk_count must match public rows")
    floor_scores = tuple(row["authority_floor_score"] for row in row_payloads)
    if payload["average_authority_floor_score"] != _decimal_payload(_average(floor_scores)):
        raise ValueError("average_authority_floor_score must match public rows")
    if payload["max_authority_floor_score"] != _decimal_payload(_max_ratio(floor_scores)):
        raise ValueError("max_authority_floor_score must match public rows")
    if reason_codes != _public_report_reason_codes(row_payloads):
        raise ValueError("reason_codes must match public rows")


def _validate_public_row_payload(row: object) -> dict[str, object]:
    if type(row) is not dict:
        raise ValueError("rows must contain public row objects")
    expected_keys = {
        "claim_bucket",
        "authority_bucket",
        "claim_ref_digest",
        "authority_ref_digest",
        "observed_at",
        "authority_updated_at",
        "authority_age_seconds",
        "authority_score",
        "memory_confidence_score",
        "evidence_coverage_score",
        "contradiction_risk_score",
        "authority_recency_score",
        "authority_floor_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    }
    if set(row) != expected_keys:
        raise ValueError("public row schema keys must match row schema")
    _require_public_string("claim_bucket", row["claim_bucket"])
    _require_public_string("authority_bucket", row["authority_bucket"])
    _require_private_digest("claim_ref_digest", row["claim_ref_digest"])
    _require_private_digest("authority_ref_digest", row["authority_ref_digest"])
    observed_at = _require_datetime_payload("observed_at", row["observed_at"])
    authority_updated_at = _require_datetime_payload(
        "authority_updated_at",
        row["authority_updated_at"],
    )
    authority_age_seconds = _require_decimal_payload(
        "authority_age_seconds",
        row["authority_age_seconds"],
    )
    ratios: dict[str, Decimal] = {}
    for field_name in (
        "authority_score",
        "memory_confidence_score",
        "evidence_coverage_score",
        "contradiction_risk_score",
        "authority_recency_score",
        "authority_floor_score",
    ):
        ratios[field_name] = _require_ratio_decimal_payload(
            field_name,
            row[field_name],
        )
    _require_status("status", row["status"])
    reason_codes = _require_reason_code_list("reason_codes", row["reason_codes"])
    if row["status"] != _status_from_reason_codes(reason_codes):
        raise ValueError("status must match public row reason_codes")
    _require_public_true_flag("paper_only", row["paper_only"])
    _require_public_true_flag("report_only", row["report_only"])
    _require_public_true_flag("readonly", row["readonly"])
    return {
        "claim_bucket": row["claim_bucket"],
        "authority_bucket": row["authority_bucket"],
        "claim_ref_digest": row["claim_ref_digest"],
        "authority_ref_digest": row["authority_ref_digest"],
        "observed_at": observed_at,
        "authority_updated_at": authority_updated_at,
        "authority_age_seconds": authority_age_seconds,
        "authority_score": ratios["authority_score"],
        "memory_confidence_score": ratios["memory_confidence_score"],
        "evidence_coverage_score": ratios["evidence_coverage_score"],
        "contradiction_risk_score": ratios["contradiction_risk_score"],
        "authority_recency_score": ratios["authority_recency_score"],
        "status": row["status"],
        "reason_codes": reason_codes,
        "authority_floor_score": ratios["authority_floor_score"],
    }


def _public_row_sort_key(row: dict[str, object]) -> tuple[str, str, str]:
    return (
        {"block": "0", "watch": "1", "pass": "2"}[row["status"]],
        row["claim_bucket"],
        row["authority_bucket"],
    )


def _validate_public_row_consistency(
    row: dict[str, object],
    *,
    config: ResearchSourceClaimMemoryAuthorityFloorConfig,
    generated_at: datetime,
) -> None:
    _require_not_after_generated_at(
        "observed_at",
        row["observed_at"],
        generated_at,
    )
    _require_not_after_generated_at(
        "authority_updated_at",
        row["authority_updated_at"],
        generated_at,
    )
    expected_age_seconds = _seconds_between(
        generated_at,
        row["authority_updated_at"],
    )
    if row["authority_age_seconds"] != expected_age_seconds:
        raise ValueError("authority_age_seconds must match public row timestamps")
    expected_recency_score = _authority_recency_score(
        expected_age_seconds,
        fresh_age_seconds=config.fresh_authority_age_seconds,
        stale_age_seconds=config.stale_authority_age_seconds,
    )
    if row["authority_recency_score"] != expected_recency_score:
        raise ValueError("authority_recency_score must match public row timestamps")
    expected_floor_score = _min_ratio(
        (
            row["authority_score"],
            row["memory_confidence_score"],
            row["evidence_coverage_score"],
            row["authority_recency_score"],
        ),
    )
    if row["authority_floor_score"] != expected_floor_score:
        raise ValueError("authority_floor_score must match public row scores")
    expected_status = _row_status(
        floor_score=expected_floor_score,
        contradiction_risk_score=row["contradiction_risk_score"],
        config=config,
    )
    if row["status"] != expected_status:
        raise ValueError("status must match public row scores")
    input_reason_codes = tuple(
        code[len("input_") :]
        for code in row["reason_codes"]
        if code.startswith("input_")
    )
    expected_reason_codes = _row_reason_codes(
        status=expected_status,
        age_seconds=expected_age_seconds,
        floor_score=expected_floor_score,
        contradiction_risk_score=row["contradiction_risk_score"],
        config=config,
        input_reason_codes=input_reason_codes,
    )
    if row["reason_codes"] != expected_reason_codes:
        raise ValueError("reason_codes must match public row scores")


def _public_report_reason_codes(rows: list[dict[str, object]]) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    if any(row["status"] == "block" for row in rows):
        return tuple(
            sorted(
                {
                    code
                    for row in rows
                    if row["status"] == "block"
                    for code in row["reason_codes"]
                },
            ),
        )
    if any(row["status"] == "watch" for row in rows):
        return tuple(
            sorted(
                {
                    code
                    for row in rows
                    if row["status"] == "watch"
                    for code in row["reason_codes"]
                },
            ),
        )
    return (PASS_REASON,)


def _build_row(
    row: ResearchSourceClaimMemoryAuthorityFloorInput,
    *,
    config: ResearchSourceClaimMemoryAuthorityFloorConfig,
    generated_at: datetime,
) -> ResearchSourceClaimMemoryAuthorityFloorRow:
    _require_hard_flags("input", row)
    _require_not_after_generated_at(
        "observed_at",
        row.observed_at,
        generated_at,
    )
    _require_not_after_generated_at(
        "authority_updated_at",
        row.authority_updated_at,
        generated_at,
    )
    age_seconds = _seconds_between(generated_at, row.authority_updated_at)
    recency_score = _authority_recency_score(
        age_seconds,
        fresh_age_seconds=config.fresh_authority_age_seconds,
        stale_age_seconds=config.stale_authority_age_seconds,
    )
    floor_score = _min_ratio(
        (
            row.authority_score,
            row.memory_confidence_score,
            row.evidence_coverage_score,
            recency_score,
        ),
    )
    status = _row_status(
        floor_score=floor_score,
        contradiction_risk_score=row.contradiction_risk_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        age_seconds=age_seconds,
        floor_score=floor_score,
        contradiction_risk_score=row.contradiction_risk_score,
        config=config,
        input_reason_codes=row.reason_codes,
    )
    return ResearchSourceClaimMemoryAuthorityFloorRow(
        claim_bucket=row.claim_bucket,
        authority_bucket=row.authority_bucket,
        claim_ref_digest=_private_digest(
            "claim",
            row.claim_bucket,
            row.private_candidate_reference,
        ),
        authority_ref_digest=_private_digest(
            "authority",
            row.authority_bucket,
            row.private_market_reference,
            row.private_source_reference,
        ),
        observed_at=row.observed_at,
        authority_updated_at=row.authority_updated_at,
        authority_age_seconds=age_seconds,
        authority_score=row.authority_score,
        memory_confidence_score=row.memory_confidence_score,
        evidence_coverage_score=row.evidence_coverage_score,
        contradiction_risk_score=row.contradiction_risk_score,
        authority_recency_score=recency_score,
        authority_floor_score=floor_score,
        status=status,
        reason_codes=reason_codes,
    )


def _authority_recency_score(
    age_seconds: Decimal,
    *,
    fresh_age_seconds: Decimal,
    stale_age_seconds: Decimal,
) -> Decimal:
    if age_seconds <= fresh_age_seconds:
        return ONE
    if age_seconds >= stale_age_seconds:
        return ZERO
    recency_span = stale_age_seconds - fresh_age_seconds
    stale_span = age_seconds - fresh_age_seconds
    return _quantize_ratio(ONE - (stale_span / recency_span))


def _row_status(
    *,
    floor_score: Decimal,
    contradiction_risk_score: Decimal,
    config: ResearchSourceClaimMemoryAuthorityFloorConfig,
) -> str:
    if (
        floor_score < config.watch_authority_floor_score
        or contradiction_risk_score >= config.block_contradiction_risk_score
    ):
        return "block"
    if (
        floor_score < config.pass_authority_floor_score
        or contradiction_risk_score >= config.watch_contradiction_risk_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    age_seconds: Decimal,
    floor_score: Decimal,
    contradiction_risk_score: Decimal,
    config: ResearchSourceClaimMemoryAuthorityFloorConfig,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if status == "block":
        reason_codes.append(BLOCK_REASON)
    elif status == "watch":
        reason_codes.append(WATCH_REASON)
    else:
        reason_codes.append(PASS_REASON)
    if age_seconds >= config.stale_authority_age_seconds:
        reason_codes.append(STALE_REASON)
    if contradiction_risk_score >= config.block_contradiction_risk_score:
        reason_codes.append(CONTRADICTION_BLOCK_REASON)
    elif contradiction_risk_score >= config.watch_contradiction_risk_score:
        reason_codes.append(CONTRADICTION_WATCH_REASON)
    for code in input_reason_codes:
        reason_codes.append(f"input_{code}")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchSourceClaimMemoryAuthorityFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    if any(row.status == "block" for row in rows):
        return tuple(
            sorted({code for row in rows if row.status == "block" for code in row.reason_codes}),
        )
    if any(row.status == "watch" for row in rows):
        return tuple(
            sorted({code for row in rows if row.status == "watch" for code in row.reason_codes}),
        )
    return (PASS_REASON,)


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchSourceClaimMemoryAuthorityFloorRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _row_sort_key(row: ResearchSourceClaimMemoryAuthorityFloorRow) -> tuple[str, str, str]:
    return (
        {"block": "0", "watch": "1", "pass": "2"}[row.status],
        row.claim_bucket,
        row.authority_bucket,
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes or CONTRADICTION_BLOCK_REASON in reason_codes:
        return "block"
    if WATCH_REASON in reason_codes or CONTRADICTION_WATCH_REASON in reason_codes:
        return "watch"
    if STALE_REASON in reason_codes:
        return "block"
    return "pass"


def _report_public_payload(
    report: ResearchSourceClaimMemoryAuthorityFloorReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "fresh_authority_age_seconds": _decimal_payload(
            report.fresh_authority_age_seconds,
        ),
        "stale_authority_age_seconds": _decimal_payload(
            report.stale_authority_age_seconds,
        ),
        "pass_authority_floor_score": _decimal_payload(
            report.pass_authority_floor_score,
        ),
        "watch_authority_floor_score": _decimal_payload(
            report.watch_authority_floor_score,
        ),
        "watch_contradiction_risk_score": _decimal_payload(
            report.watch_contradiction_risk_score,
        ),
        "block_contradiction_risk_score": _decimal_payload(
            report.block_contradiction_risk_score,
        ),
        "row_count": _decimal_payload(report.row_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "stale_authority_count": _decimal_payload(report.stale_authority_count),
        "low_authority_floor_count": _decimal_payload(report.low_authority_floor_count),
        "contradiction_risk_count": _decimal_payload(report.contradiction_risk_count),
        "average_authority_floor_score": _decimal_payload(
            report.average_authority_floor_score,
        ),
        "max_authority_floor_score": _decimal_payload(
            report.max_authority_floor_score,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_public_payload(
    row: ResearchSourceClaimMemoryAuthorityFloorRow,
) -> dict[str, object]:
    return {
        "claim_bucket": row.claim_bucket,
        "authority_bucket": row.authority_bucket,
        "claim_ref_digest": row.claim_ref_digest,
        "authority_ref_digest": row.authority_ref_digest,
        "observed_at": _datetime_payload(row.observed_at),
        "authority_updated_at": _datetime_payload(row.authority_updated_at),
        "authority_age_seconds": _decimal_payload(row.authority_age_seconds),
        "authority_score": _decimal_payload(row.authority_score),
        "memory_confidence_score": _decimal_payload(row.memory_confidence_score),
        "evidence_coverage_score": _decimal_payload(row.evidence_coverage_score),
        "contradiction_risk_score": _decimal_payload(row.contradiction_risk_score),
        "authority_recency_score": _decimal_payload(row.authority_recency_score),
        "authority_floor_score": _decimal_payload(row.authority_floor_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _validate_report_counts(
    report: ResearchSourceClaimMemoryAuthorityFloorReport,
    *,
    config: ResearchSourceClaimMemoryAuthorityFloorConfig,
) -> None:
    _require_unique_row_identities(
        tuple(
            (row.claim_ref_digest, row.authority_ref_digest)
            for row in report.rows
        ),
    )
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be in canonical order")
    for row in report.rows:
        _validate_report_row_consistency(
            row,
            config=config,
            generated_at=report.generated_at,
        )
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _rollup_status(tuple(row.status for row in report.rows)):
        raise ValueError("status must match rows")
    if report.stale_authority_count != _count(
        sum(
            1
            for row in report.rows
            if row.authority_age_seconds >= config.stale_authority_age_seconds
        ),
    ):
        raise ValueError("stale_authority_count must match rows")
    if report.contradiction_risk_count != _count(
        sum(
            1
            for row in report.rows
            if row.contradiction_risk_score
            >= config.watch_contradiction_risk_score
        ),
    ):
        raise ValueError("contradiction_risk_count must match rows")
    if report.low_authority_floor_count != _count(
        sum(
            1
            for row in report.rows
            if row.authority_floor_score < config.pass_authority_floor_score
        ),
    ):
        raise ValueError("low_authority_floor_count must match rows")
    floor_scores = tuple(row.authority_floor_score for row in report.rows)
    if report.average_authority_floor_score != _average(floor_scores):
        raise ValueError("average_authority_floor_score must match rows")
    if report.max_authority_floor_score != _max_ratio(floor_scores):
        raise ValueError("max_authority_floor_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _validate_report_row_consistency(
    row: ResearchSourceClaimMemoryAuthorityFloorRow,
    *,
    config: ResearchSourceClaimMemoryAuthorityFloorConfig,
    generated_at: datetime,
) -> None:
    _require_not_after_generated_at(
        "observed_at",
        row.observed_at,
        generated_at,
    )
    _require_not_after_generated_at(
        "authority_updated_at",
        row.authority_updated_at,
        generated_at,
    )
    expected_age_seconds = _seconds_between(generated_at, row.authority_updated_at)
    if row.authority_age_seconds != expected_age_seconds:
        raise ValueError("authority_age_seconds must match row timestamps")
    expected_recency_score = _authority_recency_score(
        expected_age_seconds,
        fresh_age_seconds=config.fresh_authority_age_seconds,
        stale_age_seconds=config.stale_authority_age_seconds,
    )
    if row.authority_recency_score != expected_recency_score:
        raise ValueError("authority_recency_score must match row timestamps")
    expected_floor_score = _min_ratio(
        (
            row.authority_score,
            row.memory_confidence_score,
            row.evidence_coverage_score,
            row.authority_recency_score,
        ),
    )
    if row.authority_floor_score != expected_floor_score:
        raise ValueError("authority_floor_score must match row scores")
    expected_status = _row_status(
        floor_score=expected_floor_score,
        contradiction_risk_score=row.contradiction_risk_score,
        config=config,
    )
    if row.status != expected_status:
        raise ValueError("status must match row scores")
    input_reason_codes = tuple(
        code[len("input_") :]
        for code in row.reason_codes
        if code.startswith("input_")
    )
    expected_reason_codes = _row_reason_codes(
        status=expected_status,
        age_seconds=expected_age_seconds,
        floor_score=expected_floor_score,
        contradiction_risk_score=row.contradiction_risk_score,
        config=config,
        input_reason_codes=input_reason_codes,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row scores")


def _normalize_inputs(
    rows: tuple[ResearchSourceClaimMemoryAuthorityFloorInput, ...],
) -> tuple[ResearchSourceClaimMemoryAuthorityFloorInput, ...]:
    if not isinstance(rows, tuple):
        rows = tuple(rows)
    normalized = []
    for row in rows:
        if type(row) is not ResearchSourceClaimMemoryAuthorityFloorInput:
            raise ValueError("rows must contain ResearchSourceClaimMemoryAuthorityFloorInput")
        normalized.append(_revalidate_input(row))
    return tuple(normalized)


def _revalidate_config(
    config: ResearchSourceClaimMemoryAuthorityFloorConfig,
) -> ResearchSourceClaimMemoryAuthorityFloorConfig:
    if type(config) is not ResearchSourceClaimMemoryAuthorityFloorConfig:
        raise ValueError("config must be a ResearchSourceClaimMemoryAuthorityFloorConfig")
    return ResearchSourceClaimMemoryAuthorityFloorConfig(
        config_version=config.config_version,
        fresh_authority_age_seconds=config.fresh_authority_age_seconds,
        stale_authority_age_seconds=config.stale_authority_age_seconds,
        pass_authority_floor_score=config.pass_authority_floor_score,
        watch_authority_floor_score=config.watch_authority_floor_score,
        watch_contradiction_risk_score=config.watch_contradiction_risk_score,
        block_contradiction_risk_score=config.block_contradiction_risk_score,
        paper_only=config.paper_only,
        report_only=config.report_only,
        readonly=config.readonly,
    )


def _revalidate_input(
    row: ResearchSourceClaimMemoryAuthorityFloorInput,
) -> ResearchSourceClaimMemoryAuthorityFloorInput:
    return ResearchSourceClaimMemoryAuthorityFloorInput(
        claim_bucket=row.claim_bucket,
        authority_bucket=row.authority_bucket,
        private_candidate_reference=row.private_candidate_reference,
        private_market_reference=row.private_market_reference,
        private_source_reference=row.private_source_reference,
        observed_at=row.observed_at,
        authority_updated_at=row.authority_updated_at,
        authority_score=row.authority_score,
        memory_confidence_score=row.memory_confidence_score,
        evidence_coverage_score=row.evidence_coverage_score,
        contradiction_risk_score=row.contradiction_risk_score,
        reason_codes=row.reason_codes,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )


def _normalize_rows(
    rows: tuple[ResearchSourceClaimMemoryAuthorityFloorRow, ...],
) -> tuple[ResearchSourceClaimMemoryAuthorityFloorRow, ...]:
    if not isinstance(rows, tuple):
        rows = tuple(rows)
    for row in rows:
        if type(row) is not ResearchSourceClaimMemoryAuthorityFloorRow:
            raise ValueError("rows must contain ResearchSourceClaimMemoryAuthorityFloorRow")
    return tuple(_revalidate_row(row) for row in rows)


def _revalidate_row(
    row: ResearchSourceClaimMemoryAuthorityFloorRow,
) -> ResearchSourceClaimMemoryAuthorityFloorRow:
    return ResearchSourceClaimMemoryAuthorityFloorRow(
        claim_bucket=row.claim_bucket,
        authority_bucket=row.authority_bucket,
        claim_ref_digest=row.claim_ref_digest,
        authority_ref_digest=row.authority_ref_digest,
        observed_at=row.observed_at,
        authority_updated_at=row.authority_updated_at,
        authority_age_seconds=row.authority_age_seconds,
        authority_score=row.authority_score,
        memory_confidence_score=row.memory_confidence_score,
        evidence_coverage_score=row.evidence_coverage_score,
        contradiction_risk_score=row.contradiction_risk_score,
        authority_recency_score=row.authority_recency_score,
        authority_floor_score=row.authority_floor_score,
        status=row.status,
        reason_codes=row.reason_codes,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for code in reason_codes:
        if type(code) is not str or not REASON_CODE_RE.fullmatch(code):
            raise ValueError("reason_codes must contain canonical reason codes")
        if code not in normalized:
            normalized.append(code)
    return tuple(sorted(normalized))


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or not PUBLIC_ID_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical public identifier")
    _reject_unsafe_public_string(value)


def _require_nonempty_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_status_reason_code(
    status: str,
    reason_codes: tuple[str, ...],
) -> None:
    expected_reason = {
        "pass": PASS_REASON,
        "watch": WATCH_REASON,
        "block": BLOCK_REASON,
    }[status]
    status_reasons = (PASS_REASON, WATCH_REASON, BLOCK_REASON)
    if expected_reason not in reason_codes or any(
        reason in reason_codes
        for reason in status_reasons
        if reason != expected_reason
    ):
        raise ValueError("reason_codes must contain the status reason matching status")


def _require_unique_row_identities(
    identities: tuple[tuple[object, object], ...],
) -> None:
    if len(set(identities)) != len(identities):
        raise ValueError("rows must not contain duplicate reference identities")


def _require_not_after_generated_at(
    field_name: str,
    value: datetime,
    generated_at: datetime,
) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _require_datetime_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must include timezone")
    normalized = parsed.astimezone(UTC)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _require_decimal_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} numeric payload must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} numeric payload must be a Decimal string") from exc
    normalized = _require_nonnegative_decimal(field_name, decimal_value)
    if value != _decimal_payload(normalized):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _require_positive_decimal_payload(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal_payload(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be > 0.000000")
    return normalized


def _require_ratio_decimal_payload(field_name: str, value: object) -> Decimal:
    return _require_ratio_decimal(field_name, _require_decimal_payload(field_name, value))


def _require_reason_code_list(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized = _normalize_reason_codes(tuple(value))
    if value != list(normalized):
        raise ValueError(f"{field_name} must use canonical reason code order")
    return normalized


def _require_public_true_flag(field_name: str, value: object) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must be True")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_private_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not PRIVATE_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a redacted sha256 digest")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        normalized = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must quantize to six decimals") from exc
    if normalized == ZERO:
        return ZERO
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be > 0.000000")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return normalized


def _quantize_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _count(value: int) -> Decimal:
    return Decimal(str(value)).quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_ratio(sum(values, ZERO) / _count(len(values)))


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_ratio(max(values))


def _min_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_ratio(min(values))


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    whole_seconds = Decimal(str((delta.days * 86400) + delta.seconds))
    fractional_seconds = Decimal(str(delta.microseconds)) / Decimal("1000000")
    seconds = whole_seconds + fractional_seconds
    if seconds < ZERO:
        return ZERO
    return seconds.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_payload(value: datetime) -> str:
    return value.isoformat()


def _decimal_payload(value: Decimal) -> str:
    return str(_require_decimal("payload_decimal", value))


def _private_digest(label: str, *parts: str) -> str:
    digest_material = json.dumps(
        {"label": label, "parts": list(parts)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"{PRIVATE_DIGEST_PREFIX}{sha256(digest_material).hexdigest()}"


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{label}.{flag_name} must be True")


def _require_canonical_public_json_value(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_canonical_public_json_value(item)
        return
    if type(value) is list:
        for item in value:
            _require_canonical_public_json_value(item)
        return
    if value is None or type(value) in (str, bool):
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must use Decimal strings")
    raise ValueError("public payload must contain canonical JSON values")


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_public_payload(key)
            _reject_unsafe_public_payload(item)
        return
    if type(value) is list or type(value) is tuple:
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(value)


def _reject_unsafe_public_string(value: str) -> None:
    normalized = value.lower()
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in normalized:
            raise ValueError("public payload contains unsafe private source material")
