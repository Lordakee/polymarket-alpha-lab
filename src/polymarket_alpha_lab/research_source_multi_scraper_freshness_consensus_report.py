"""Pure report-only reducer for multi-scraper freshness consensus checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import json
import re
from hashlib import sha256
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_MULTI_SCRAPER_FRESHNESS_CONSENSUS_CONFIG_VERSION = (
    "research-source-multi-scraper-freshness-consensus-report-v0"
)
RESEARCH_SOURCE_MULTI_SCRAPER_FRESHNESS_CONSENSUS_STATUSES = (
    "pass",
    "watch",
    "block",
)

PASS_REASON = "multi_scraper_freshness_consensus_pass"
REASON_CODE_SEQUENCE = (
    "fresh_scraper_quorum_watch",
    "fresh_scraper_quorum_block",
    "consensus_scraper_quorum_watch",
    "consensus_scraper_quorum_block",
    "latest_scrape_age_watch",
    "latest_scrape_age_block",
    "stale_scraper_ratio_watch",
    "stale_scraper_ratio_block",
    "consensus_agreement_watch",
    "consensus_agreement_block",
    "disagreement_pressure_watch",
    "disagreement_pressure_block",
    "parse_success_ratio_watch",
    "parse_success_ratio_block",
    PASS_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SEVEN = Decimal("7.000000")
SHA256_HEX_LENGTH = 64

_PUBLIC_BUCKET_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
_UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source_url",
    "source-url",
    "source_text",
    "source-text",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "recommendation",
    "auth_",
    "auth-",
    "authentication",
    "authorization",
    "private_key",
    "private-key",
    "secret",
    "credential",
    "password",
    "api_key",
    "api-key",
    "bearer",
)
_UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "http",
    "https",
    "postgres://",
    "mysql://",
    "jdbc:",
    "raw",
    "candidate-",
    "candidate_id",
    "market-",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source-url",
    "source_text",
    "source-text",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live_surface",
    "live-",
    "recommendation",
    "auth_",
    "auth-",
    "authentication",
    "authorization",
    "private_key",
    "private-key",
    "secret",
    "credential",
    "password",
    "api_key",
    "api-key",
    "bearer",
)
_PUBLIC_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "scraper_bucket_count",
        "pass_count",
        "watch_count",
        "block_count",
        "min_fresh_scraper_count",
        "min_consensus_scraper_count",
        "max_latest_scrape_age_seconds",
        "max_stale_scraper_ratio",
        "max_disagreement_pressure",
        "min_consensus_agreement_score",
        "min_parse_success_ratio",
        "status",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_PUBLIC_ROW_PAYLOAD_KEYS = frozenset(
    (
        "scraper_bucket",
        "scraper_family_count",
        "fresh_scraper_count",
        "consensus_scraper_count",
        "stale_scraper_count",
        "fresh_scraper_ratio",
        "stale_scraper_ratio",
        "latest_scrape_age_seconds",
        "consensus_agreement_score",
        "disagreement_pressure",
        "parse_success_ratio",
        "fresh_scraper_gap_count",
        "consensus_scraper_gap_count",
        "freshness_consensus_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


@dataclass(frozen=True)
class ResearchSourceMultiScraperFreshnessConsensusConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_MULTI_SCRAPER_FRESHNESS_CONSENSUS_CONFIG_VERSION
    )
    watch_fresh_scraper_count: Decimal = Decimal("2.000000")
    block_fresh_scraper_count: Decimal = Decimal("0.000000")
    watch_consensus_scraper_count: Decimal = Decimal("1.000000")
    block_consensus_scraper_count: Decimal = Decimal("0.000000")
    watch_latest_scrape_age_seconds: Decimal = Decimal("3600.000000")
    block_latest_scrape_age_seconds: Decimal = Decimal("14400.000000")
    watch_stale_scraper_ratio: Decimal = Decimal("0.500000")
    block_stale_scraper_ratio: Decimal = Decimal("0.850000")
    watch_consensus_agreement_score: Decimal = Decimal("0.750000")
    block_consensus_agreement_score: Decimal = Decimal("0.450000")
    watch_disagreement_pressure: Decimal = Decimal("0.250000")
    block_disagreement_pressure: Decimal = Decimal("0.650000")
    watch_parse_success_ratio: Decimal = Decimal("0.850000")
    block_parse_success_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceMultiScraperFreshnessConsensusConfig:
            raise TypeError(
                "ResearchSourceMultiScraperFreshnessConsensusConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceMultiScraperFreshnessConsensusConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceMultiScraperFreshnessConsensusConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_MULTI_SCRAPER_FRESHNESS_CONSENSUS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_fresh_scraper_count",
            "block_fresh_scraper_count",
            "watch_consensus_scraper_count",
            "block_consensus_scraper_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_latest_scrape_age_seconds",
            "block_latest_scrape_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_stale_scraper_ratio",
            "block_stale_scraper_ratio",
            "watch_consensus_agreement_score",
            "block_consensus_agreement_score",
            "watch_disagreement_pressure",
            "block_disagreement_pressure",
            "watch_parse_success_ratio",
            "block_parse_success_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_watch_before_block_low(
            "fresh_scraper_count",
            self.watch_fresh_scraper_count,
            self.block_fresh_scraper_count,
        )
        _require_watch_before_block_low(
            "consensus_scraper_count",
            self.watch_consensus_scraper_count,
            self.block_consensus_scraper_count,
        )
        _require_watch_before_block_high(
            "latest_scrape_age_seconds",
            self.watch_latest_scrape_age_seconds,
            self.block_latest_scrape_age_seconds,
        )
        _require_watch_before_block_high(
            "stale_scraper_ratio",
            self.watch_stale_scraper_ratio,
            self.block_stale_scraper_ratio,
        )
        _require_watch_before_block_low(
            "consensus_agreement_score",
            self.watch_consensus_agreement_score,
            self.block_consensus_agreement_score,
        )
        _require_watch_before_block_high(
            "disagreement_pressure",
            self.watch_disagreement_pressure,
            self.block_disagreement_pressure,
        )
        _require_watch_before_block_low(
            "parse_success_ratio",
            self.watch_parse_success_ratio,
            self.block_parse_success_ratio,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceMultiScraperFreshnessConsensusObservation:
    scraper_bucket: str
    scraper_family_count: Decimal
    fresh_scraper_count: Decimal
    consensus_scraper_count: Decimal
    latest_scraped_at: datetime | None
    consensus_agreement_score: Decimal
    disagreement_pressure: Decimal
    parse_success_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceMultiScraperFreshnessConsensusObservation:
            raise TypeError(
                "ResearchSourceMultiScraperFreshnessConsensusObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceMultiScraperFreshnessConsensusObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchSourceMultiScraperFreshnessConsensusObservation",
            )
        object.__setattr__(
            self,
            "scraper_bucket",
            _require_public_bucket("scraper_bucket", self.scraper_bucket),
        )
        object.__setattr__(
            self,
            "scraper_family_count",
            _require_positive_whole_decimal(
                "scraper_family_count",
                self.scraper_family_count,
            ),
        )
        for field_name in ("fresh_scraper_count", "consensus_scraper_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_scraper_count > self.scraper_family_count:
            raise ValueError("fresh_scraper_count must not exceed scraper_family_count")
        if self.consensus_scraper_count > self.fresh_scraper_count:
            raise ValueError("consensus_scraper_count must not exceed fresh_scraper_count")
        if self.latest_scraped_at is not None:
            object.__setattr__(
                self,
                "latest_scraped_at",
                _as_utc("latest_scraped_at", self.latest_scraped_at),
            )
        for field_name in (
            "consensus_agreement_score",
            "disagreement_pressure",
            "parse_success_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceMultiScraperFreshnessConsensusRow:
    scraper_bucket: str
    scraper_family_count: Decimal
    fresh_scraper_count: Decimal
    consensus_scraper_count: Decimal
    stale_scraper_count: Decimal
    fresh_scraper_ratio: Decimal
    stale_scraper_ratio: Decimal
    latest_scrape_age_seconds: Decimal
    consensus_agreement_score: Decimal
    disagreement_pressure: Decimal
    parse_success_ratio: Decimal
    fresh_scraper_gap_count: Decimal
    consensus_scraper_gap_count: Decimal
    freshness_consensus_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceMultiScraperFreshnessConsensusRow:
            raise TypeError(
                "ResearchSourceMultiScraperFreshnessConsensusRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceMultiScraperFreshnessConsensusRow:
            raise ValueError(
                "row must be exactly ResearchSourceMultiScraperFreshnessConsensusRow",
            )
        object.__setattr__(
            self,
            "scraper_bucket",
            _require_public_bucket("scraper_bucket", self.scraper_bucket),
        )
        for field_name in (
            "scraper_family_count",
            "fresh_scraper_count",
            "consensus_scraper_count",
            "stale_scraper_count",
            "fresh_scraper_gap_count",
            "consensus_scraper_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.scraper_family_count <= ZERO:
            raise ValueError("scraper_family_count must be positive")
        for field_name in (
            "fresh_scraper_ratio",
            "stale_scraper_ratio",
            "consensus_agreement_score",
            "disagreement_pressure",
            "parse_success_ratio",
            "freshness_consensus_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_scrape_age_seconds",
            _require_nonnegative_decimal(
                "latest_scrape_age_seconds",
                self.latest_scrape_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceMultiScraperFreshnessConsensusReport:
    generated_at: datetime
    config_version: str
    scraper_bucket_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_fresh_scraper_count: Decimal
    min_consensus_scraper_count: Decimal
    max_latest_scrape_age_seconds: Decimal
    max_stale_scraper_ratio: Decimal
    max_disagreement_pressure: Decimal
    min_consensus_agreement_score: Decimal
    min_parse_success_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceMultiScraperFreshnessConsensusRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceMultiScraperFreshnessConsensusReport:
            raise TypeError(
                "ResearchSourceMultiScraperFreshnessConsensusReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceMultiScraperFreshnessConsensusReport:
            raise ValueError(
                "report must be exactly "
                "ResearchSourceMultiScraperFreshnessConsensusReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_MULTI_SCRAPER_FRESHNESS_CONSENSUS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "scraper_bucket_count",
            "pass_count",
            "watch_count",
            "block_count",
            "min_fresh_scraper_count",
            "min_consensus_scraper_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_latest_scrape_age_seconds",
            _require_nonnegative_decimal(
                "max_latest_scrape_age_seconds",
                self.max_latest_scrape_age_seconds,
            ),
        )
        for field_name in (
            "max_stale_scraper_ratio",
            "max_disagreement_pressure",
            "min_consensus_agreement_score",
            "min_parse_success_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _require_or_set_digest(self)


def build_research_source_multi_scraper_freshness_consensus_report(
    observations: Sequence[ResearchSourceMultiScraperFreshnessConsensusObservation],
    *,
    config: ResearchSourceMultiScraperFreshnessConsensusConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceMultiScraperFreshnessConsensusReport:
    if config is None:
        config = ResearchSourceMultiScraperFreshnessConsensusConfig()
    if type(config) is not ResearchSourceMultiScraperFreshnessConsensusConfig:
        raise ValueError(
            "config must be a ResearchSourceMultiScraperFreshnessConsensusConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    if not normalized:
        raise ValueError("observations must not be empty")
    for item in normalized:
        if item.latest_scraped_at is not None:
            _reject_future_time("latest_scraped_at", item.latest_scraped_at, generated_at_utc)
    rows = tuple(
        _row_from_observation(item, config=config, generated_at=generated_at_utc)
        for item in normalized
    )
    return ResearchSourceMultiScraperFreshnessConsensusReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        scraper_bucket_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        min_fresh_scraper_count=min(
            (row.fresh_scraper_count for row in rows),
            default=ZERO,
        ),
        min_consensus_scraper_count=min(
            (row.consensus_scraper_count for row in rows),
            default=ZERO,
        ),
        max_latest_scrape_age_seconds=max(
            (row.latest_scrape_age_seconds for row in rows),
            default=ZERO,
        ),
        max_stale_scraper_ratio=max(
            (row.stale_scraper_ratio for row in rows),
            default=ZERO,
        ),
        max_disagreement_pressure=max(
            (row.disagreement_pressure for row in rows),
            default=ZERO,
        ),
        min_consensus_agreement_score=min(
            (row.consensus_agreement_score for row in rows),
            default=ONE,
        ),
        min_parse_success_ratio=min(
            (row.parse_success_ratio for row in rows),
            default=ONE,
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_multi_scraper_freshness_consensus_report_payload(
    report: ResearchSourceMultiScraperFreshnessConsensusReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceMultiScraperFreshnessConsensusReport:
        raise ValueError(
            "report must be a ResearchSourceMultiScraperFreshnessConsensusReport",
        )
    validate_research_source_multi_scraper_freshness_consensus_report_digest(report)
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_source_multi_scraper_freshness_consensus_public_payload(
        payload,
    )
    return payload


def research_source_multi_scraper_freshness_consensus_report_digest(
    report: ResearchSourceMultiScraperFreshnessConsensusReport,
) -> str:
    if type(report) is not ResearchSourceMultiScraperFreshnessConsensusReport:
        raise ValueError(
            "report must be a ResearchSourceMultiScraperFreshnessConsensusReport",
        )
    return _report_digest_from_public_payload(report)


def validate_research_source_multi_scraper_freshness_consensus_report_digest(
    report: ResearchSourceMultiScraperFreshnessConsensusReport,
) -> None:
    if type(report) is not ResearchSourceMultiScraperFreshnessConsensusReport:
        raise ValueError(
            "report must be a ResearchSourceMultiScraperFreshnessConsensusReport",
        )
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match public payload")


def validate_research_source_multi_scraper_freshness_consensus_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload(payload)
    _require_public_payload_keys(
        "report",
        payload,
        _PUBLIC_REPORT_PAYLOAD_KEYS,
    )
    _verify_public_digest(payload)
    _report_from_public_payload(payload)


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceMultiScraperFreshnessConsensusReport:
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(_row_from_public_payload(row) for row in rows_value)
    return ResearchSourceMultiScraperFreshnessConsensusReport(
        generated_at=_require_public_datetime_string(
            "generated_at",
            payload["generated_at"],
        ),
        config_version=_require_public_string(
            "config_version",
            payload["config_version"],
        ),
        scraper_bucket_count=_require_public_decimal_string(
            "scraper_bucket_count",
            payload["scraper_bucket_count"],
        ),
        pass_count=_require_public_decimal_string(
            "pass_count",
            payload["pass_count"],
        ),
        watch_count=_require_public_decimal_string(
            "watch_count",
            payload["watch_count"],
        ),
        block_count=_require_public_decimal_string(
            "block_count",
            payload["block_count"],
        ),
        min_fresh_scraper_count=_require_public_decimal_string(
            "min_fresh_scraper_count",
            payload["min_fresh_scraper_count"],
        ),
        min_consensus_scraper_count=_require_public_decimal_string(
            "min_consensus_scraper_count",
            payload["min_consensus_scraper_count"],
        ),
        max_latest_scrape_age_seconds=_require_public_decimal_string(
            "max_latest_scrape_age_seconds",
            payload["max_latest_scrape_age_seconds"],
        ),
        max_stale_scraper_ratio=_require_public_decimal_string(
            "max_stale_scraper_ratio",
            payload["max_stale_scraper_ratio"],
        ),
        max_disagreement_pressure=_require_public_decimal_string(
            "max_disagreement_pressure",
            payload["max_disagreement_pressure"],
        ),
        min_consensus_agreement_score=_require_public_decimal_string(
            "min_consensus_agreement_score",
            payload["min_consensus_agreement_score"],
        ),
        min_parse_success_ratio=_require_public_decimal_string(
            "min_parse_success_ratio",
            payload["min_parse_success_ratio"],
        ),
        status=_require_public_string("status", payload["status"]),
        reason_codes=_require_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        rows=rows,
        derived_validation_digest=_require_public_sha256(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_require_public_true("paper_only", payload["paper_only"]),
        report_only=_require_public_true("report_only", payload["report_only"]),
        readonly=_require_public_true("readonly", payload["readonly"]),
    )


def _row_from_public_payload(
    value: object,
) -> ResearchSourceMultiScraperFreshnessConsensusRow:
    _require_public_payload_keys("row", value, _PUBLIC_ROW_PAYLOAD_KEYS)
    if type(value) is not dict:
        raise ValueError("row must be a dict")
    return ResearchSourceMultiScraperFreshnessConsensusRow(
        scraper_bucket=_require_public_string(
            "scraper_bucket",
            value["scraper_bucket"],
        ),
        scraper_family_count=_require_public_decimal_string(
            "scraper_family_count",
            value["scraper_family_count"],
        ),
        fresh_scraper_count=_require_public_decimal_string(
            "fresh_scraper_count",
            value["fresh_scraper_count"],
        ),
        consensus_scraper_count=_require_public_decimal_string(
            "consensus_scraper_count",
            value["consensus_scraper_count"],
        ),
        stale_scraper_count=_require_public_decimal_string(
            "stale_scraper_count",
            value["stale_scraper_count"],
        ),
        fresh_scraper_ratio=_require_public_decimal_string(
            "fresh_scraper_ratio",
            value["fresh_scraper_ratio"],
        ),
        stale_scraper_ratio=_require_public_decimal_string(
            "stale_scraper_ratio",
            value["stale_scraper_ratio"],
        ),
        latest_scrape_age_seconds=_require_public_decimal_string(
            "latest_scrape_age_seconds",
            value["latest_scrape_age_seconds"],
        ),
        consensus_agreement_score=_require_public_decimal_string(
            "consensus_agreement_score",
            value["consensus_agreement_score"],
        ),
        disagreement_pressure=_require_public_decimal_string(
            "disagreement_pressure",
            value["disagreement_pressure"],
        ),
        parse_success_ratio=_require_public_decimal_string(
            "parse_success_ratio",
            value["parse_success_ratio"],
        ),
        fresh_scraper_gap_count=_require_public_decimal_string(
            "fresh_scraper_gap_count",
            value["fresh_scraper_gap_count"],
        ),
        consensus_scraper_gap_count=_require_public_decimal_string(
            "consensus_scraper_gap_count",
            value["consensus_scraper_gap_count"],
        ),
        freshness_consensus_score=_require_public_decimal_string(
            "freshness_consensus_score",
            value["freshness_consensus_score"],
        ),
        status=_require_public_string("status", value["status"]),
        reason_codes=_require_public_reason_codes(
            "reason_codes",
            value["reason_codes"],
        ),
        paper_only=_require_public_true("paper_only", value["paper_only"]),
        report_only=_require_public_true("report_only", value["report_only"]),
        readonly=_require_public_true("readonly", value["readonly"]),
    )


def _row_from_observation(
    observation: ResearchSourceMultiScraperFreshnessConsensusObservation,
    *,
    config: ResearchSourceMultiScraperFreshnessConsensusConfig,
    generated_at: datetime,
) -> ResearchSourceMultiScraperFreshnessConsensusRow:
    with localcontext(DECIMAL_CONTEXT):
        stale_scraper_count = (
            observation.scraper_family_count - observation.fresh_scraper_count
        ).quantize(QUANT)
    fresh_scraper_ratio = _bounded_ratio(
        observation.fresh_scraper_count,
        observation.scraper_family_count,
    )
    stale_scraper_ratio = _bounded_ratio(
        stale_scraper_count,
        observation.scraper_family_count,
    )
    latest_scrape_age_seconds = _latest_scrape_age_seconds(
        observation,
        config=config,
        generated_at=generated_at,
    )
    reason_codes = _row_reason_codes(
        fresh_scraper_count=observation.fresh_scraper_count,
        consensus_scraper_count=observation.consensus_scraper_count,
        latest_scrape_age_seconds=latest_scrape_age_seconds,
        stale_scraper_ratio=stale_scraper_ratio,
        consensus_agreement_score=observation.consensus_agreement_score,
        disagreement_pressure=observation.disagreement_pressure,
        parse_success_ratio=observation.parse_success_ratio,
        config=config,
    )
    return ResearchSourceMultiScraperFreshnessConsensusRow(
        scraper_bucket=observation.scraper_bucket,
        scraper_family_count=observation.scraper_family_count,
        fresh_scraper_count=observation.fresh_scraper_count,
        consensus_scraper_count=observation.consensus_scraper_count,
        stale_scraper_count=stale_scraper_count,
        fresh_scraper_ratio=fresh_scraper_ratio,
        stale_scraper_ratio=stale_scraper_ratio,
        latest_scrape_age_seconds=latest_scrape_age_seconds,
        consensus_agreement_score=observation.consensus_agreement_score,
        disagreement_pressure=observation.disagreement_pressure,
        parse_success_ratio=observation.parse_success_ratio,
        fresh_scraper_gap_count=_quorum_gap(
            config.watch_fresh_scraper_count,
            observation.fresh_scraper_count,
        ),
        consensus_scraper_gap_count=_quorum_gap(
            config.watch_consensus_scraper_count,
            observation.consensus_scraper_count,
        ),
        freshness_consensus_score=_freshness_consensus_score(reason_codes),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _latest_scrape_age_seconds(
    observation: ResearchSourceMultiScraperFreshnessConsensusObservation,
    *,
    config: ResearchSourceMultiScraperFreshnessConsensusConfig,
    generated_at: datetime,
) -> Decimal:
    if observation.latest_scraped_at is None:
        return config.block_latest_scrape_age_seconds
    return _elapsed_seconds(observation.latest_scraped_at, generated_at)


def _row_reason_codes(
    *,
    fresh_scraper_count: Decimal,
    consensus_scraper_count: Decimal,
    latest_scrape_age_seconds: Decimal,
    stale_scraper_ratio: Decimal,
    consensus_agreement_score: Decimal,
    disagreement_pressure: Decimal,
    parse_success_ratio: Decimal,
    config: ResearchSourceMultiScraperFreshnessConsensusConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_low_quorum_reason(
        reasons,
        prefix="fresh_scraper_quorum",
        value=fresh_scraper_count,
        watch_threshold=config.watch_fresh_scraper_count,
        block_threshold=config.block_fresh_scraper_count,
    )
    _append_low_quorum_reason(
        reasons,
        prefix="consensus_scraper_quorum",
        value=consensus_scraper_count,
        watch_threshold=config.watch_consensus_scraper_count,
        block_threshold=config.block_consensus_scraper_count,
    )
    _append_high_threshold_reason(
        reasons,
        prefix="latest_scrape_age",
        value=latest_scrape_age_seconds,
        watch_threshold=config.watch_latest_scrape_age_seconds,
        block_threshold=config.block_latest_scrape_age_seconds,
    )
    _append_high_threshold_reason(
        reasons,
        prefix="stale_scraper_ratio",
        value=stale_scraper_ratio,
        watch_threshold=config.watch_stale_scraper_ratio,
        block_threshold=config.block_stale_scraper_ratio,
    )
    _append_low_threshold_reason(
        reasons,
        prefix="consensus_agreement",
        value=consensus_agreement_score,
        watch_threshold=config.watch_consensus_agreement_score,
        block_threshold=config.block_consensus_agreement_score,
    )
    _append_high_threshold_reason(
        reasons,
        prefix="disagreement_pressure",
        value=disagreement_pressure,
        watch_threshold=config.watch_disagreement_pressure,
        block_threshold=config.block_disagreement_pressure,
    )
    _append_low_threshold_reason(
        reasons,
        prefix="parse_success_ratio",
        value=parse_success_ratio,
        watch_threshold=config.watch_parse_success_ratio,
        block_threshold=config.block_parse_success_ratio,
    )
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", reasons)


def _append_high_threshold_reason(
    reasons: list[str],
    *,
    prefix: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value >= block_threshold:
        reasons.append(f"{prefix}_block")
    elif value >= watch_threshold:
        reasons.append(f"{prefix}_watch")


def _append_low_threshold_reason(
    reasons: list[str],
    *,
    prefix: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value <= block_threshold:
        reasons.append(f"{prefix}_block")
    elif value <= watch_threshold:
        reasons.append(f"{prefix}_watch")


def _append_low_quorum_reason(
    reasons: list[str],
    *,
    prefix: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value <= block_threshold:
        reasons.append(f"{prefix}_block")
    elif value < watch_threshold:
        reasons.append(f"{prefix}_watch")


def _freshness_consensus_score(reason_codes: tuple[str, ...]) -> Decimal:
    if reason_codes == (PASS_REASON,):
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        severity_total = sum(
            (
                (
                    ONE
                    if reason_code.endswith("_block")
                    else Decimal("0.500000")
                    if reason_code.endswith("_watch")
                    else ZERO
                )
                for reason_code in reason_codes
            ),
            ZERO,
        )
        return _clamp_ratio(severity_total / SEVEN)


def _quorum_gap(required_count: Decimal, actual_count: Decimal) -> Decimal:
    if actual_count >= required_count:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (required_count - actual_count).quantize(QUANT)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchSourceMultiScraperFreshnessConsensusRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceMultiScraperFreshnessConsensusRow, ...],
) -> tuple[str, ...]:
    if all(row.status == "pass" for row in rows):
        return (PASS_REASON,)
    seen = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    }
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen),
    )


def _status_count(
    rows: tuple[ResearchSourceMultiScraperFreshnessConsensusRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _validate_row(row: ResearchSourceMultiScraperFreshnessConsensusRow) -> None:
    if row.fresh_scraper_count > row.scraper_family_count:
        raise ValueError("fresh_scraper_count must not exceed scraper_family_count")
    if row.consensus_scraper_count > row.fresh_scraper_count:
        raise ValueError("consensus_scraper_count must not exceed fresh_scraper_count")
    with localcontext(DECIMAL_CONTEXT):
        expected_stale_scraper_count = (
            row.scraper_family_count - row.fresh_scraper_count
        ).quantize(QUANT)
    if row.stale_scraper_count != expected_stale_scraper_count:
        raise ValueError("stale_scraper_count must match scraper counts")
    if row.fresh_scraper_ratio != _bounded_ratio(
        row.fresh_scraper_count,
        row.scraper_family_count,
    ):
        raise ValueError("fresh_scraper_ratio must match scraper counts")
    if row.stale_scraper_ratio != _bounded_ratio(
        row.stale_scraper_count,
        row.scraper_family_count,
    ):
        raise ValueError("stale_scraper_ratio must match scraper counts")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.freshness_consensus_score != _freshness_consensus_score(row.reason_codes):
        raise ValueError("freshness_consensus_score must match reason_codes")


def _validate_report(report: ResearchSourceMultiScraperFreshnessConsensusReport) -> None:
    if not report.rows:
        raise ValueError("rows must not be empty")
    if report.scraper_bucket_count != _count(len(report.rows)):
        raise ValueError("scraper_bucket_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.min_fresh_scraper_count != min(
        (row.fresh_scraper_count for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_fresh_scraper_count must match rows")
    if report.min_consensus_scraper_count != min(
        (row.consensus_scraper_count for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_consensus_scraper_count must match rows")
    if report.max_latest_scrape_age_seconds != max(
        (row.latest_scrape_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_latest_scrape_age_seconds must match rows")
    if report.max_stale_scraper_ratio != max(
        (row.stale_scraper_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_stale_scraper_ratio must match rows")
    if report.max_disagreement_pressure != max(
        (row.disagreement_pressure for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_disagreement_pressure must match rows")
    if report.min_consensus_agreement_score != min(
        (row.consensus_agreement_score for row in report.rows),
        default=ONE,
    ):
        raise ValueError("min_consensus_agreement_score must match rows")
    if report.min_parse_success_ratio != min(
        (row.parse_success_ratio for row in report.rows),
        default=ONE,
    ):
        raise ValueError("min_parse_success_ratio must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    buckets = tuple(row.scraper_bucket for row in report.rows)
    if len(buckets) != len(set(buckets)):
        raise ValueError("rows must be unique by scraper_bucket")
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.scraper_bucket)):
        raise ValueError("rows must be deterministic")


def _normalize_observations(
    observations: Sequence[ResearchSourceMultiScraperFreshnessConsensusObservation],
) -> tuple[ResearchSourceMultiScraperFreshnessConsensusObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchSourceMultiScraperFreshnessConsensusObservation] = []
    seen: set[str] = set()
    for item in observations:
        if type(item) is not ResearchSourceMultiScraperFreshnessConsensusObservation:
            raise ValueError(
                "observations must contain "
                "ResearchSourceMultiScraperFreshnessConsensusObservation values",
            )
        _require_hard_flags("observation", item)
        if item.scraper_bucket in seen:
            raise ValueError("observations must be unique by scraper_bucket")
        seen.add(item.scraper_bucket)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.scraper_bucket))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSourceMultiScraperFreshnessConsensusRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchSourceMultiScraperFreshnessConsensusRow:
            raise ValueError(
                "rows must contain ResearchSourceMultiScraperFreshnessConsensusRow values",
            )
        _require_hard_flags("row", row)
        if row.scraper_bucket in seen:
            raise ValueError("rows must be unique by scraper_bucket")
        seen.add(row.scraper_bucket)
    return tuple(sorted(normalized, key=lambda row: row.scraper_bucket))


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError(f"{field_name} must contain supported reason codes")
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError(f"{field_name} must be unique")
    deterministic = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in reason_codes
    )
    if reason_codes != deterministic:
        raise ValueError(f"{field_name} must be deterministic")
    return deterministic


def _require_public_payload_keys(
    label: str,
    value: object,
    expected: frozenset[str],
) -> None:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a dict")
    if frozenset(value) != expected:
        raise ValueError(f"{label} fields must match exact public schema")


def _require_public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_public_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    normalized = _require_nonnegative_decimal(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _require_public_datetime_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime string",
        ) from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _require_public_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(field_name, tuple(value))


def _require_public_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _require_public_sha256(field_name: str, value: object) -> str:
    _require_sha256(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_public_bucket(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value, key_scan=False)
    if _PUBLIC_BUCKET_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public bucket label")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_MULTI_SCRAPER_FRESHNESS_CONSENSUS_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label}.{flag_name} must be True")


def _require_watch_before_block_high(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value < watch_value:
        raise ValueError(f"block_{field_name} must be greater than or equal to watch")


def _require_watch_before_block_low(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value > watch_value:
        raise ValueError(f"block_{field_name} must be less than or equal to watch")


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc
    if normalized == ZERO:
        return ZERO
    return normalized


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(QUANT)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(numerator / denominator, ONE).quantize(QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANT, rounding=ROUND_HALF_UP)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    if normalized == ZERO:
        return ZERO
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _elapsed_seconds(started_at: datetime, ended_at: datetime) -> Decimal:
    elapsed = ended_at - started_at
    if elapsed.days < 0:
        raise ValueError("elapsed seconds must be nonnegative")
    elapsed_microseconds = (
        ((elapsed.days * 86400) + elapsed.seconds) * 1000000
    ) + elapsed.microseconds
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(elapsed_microseconds) / Decimal("1000000")).quantize(QUANT)


def _reject_future_time(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _require_or_set_digest(report: ResearchSourceMultiScraperFreshnessConsensusReport) -> None:
    if type(report.derived_validation_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _report_digest_from_public_payload(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match public payload")


def _report_digest_from_public_payload(
    report: ResearchSourceMultiScraperFreshnessConsensusReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_public_payload(payload)
    return _canonical_digest(payload)


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned):
        raise ValueError("derived_validation_digest does not match public payload")


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
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
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _reject_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_public_payload(asdict(value))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_string(
                "public payload key",
                key,
                key_scan=True,
            )
            _reject_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(item)
        return
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric public payload values must be Decimal strings")
    if type(value) is str:
        _reject_unsafe_public_string("public payload value", value, key_scan=False)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError(f"unsupported public payload value type: {type(value).__name__}")


def _reject_unsafe_public_string(
    field_name: str,
    value: str,
    *,
    key_scan: bool,
) -> None:
    lowered = value.lower()
    fragments = (
        _UNSAFE_PUBLIC_KEY_FRAGMENTS if key_scan else _UNSAFE_PUBLIC_VALUE_FRAGMENTS
    )
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} contains unsafe text")
    if any(fragment in lowered for fragment in fragments):
        raise ValueError(f"{field_name} contains unsafe text")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_MULTI_SCRAPER_FRESHNESS_CONSENSUS_CONFIG_VERSION",
    "RESEARCH_SOURCE_MULTI_SCRAPER_FRESHNESS_CONSENSUS_STATUSES",
    "ResearchSourceMultiScraperFreshnessConsensusConfig",
    "ResearchSourceMultiScraperFreshnessConsensusObservation",
    "ResearchSourceMultiScraperFreshnessConsensusReport",
    "ResearchSourceMultiScraperFreshnessConsensusRow",
    "build_research_source_multi_scraper_freshness_consensus_report",
    "research_source_multi_scraper_freshness_consensus_report_digest",
    "research_source_multi_scraper_freshness_consensus_report_payload",
    "validate_research_source_multi_scraper_freshness_consensus_public_payload",
    "validate_research_source_multi_scraper_freshness_consensus_report_digest",
)
