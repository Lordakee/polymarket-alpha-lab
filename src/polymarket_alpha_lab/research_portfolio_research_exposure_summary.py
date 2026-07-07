"""Report-only exposure summary for caller-supplied research queue items."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


__all__ = (
    "DEFAULT_RESEARCH_PORTFOLIO_RESEARCH_EXPOSURE_SUMMARY_CONFIG_VERSION",
    "ResearchPortfolioResearchExposureBucket",
    "ResearchPortfolioResearchExposureInputRow",
    "ResearchPortfolioResearchExposurePublicPayloadItem",
    "ResearchPortfolioResearchExposureReasonCodeCount",
    "ResearchPortfolioResearchExposureSummaryConfig",
    "ResearchPortfolioResearchExposureSummaryReport",
    "build_research_portfolio_research_exposure_summary",
    "research_portfolio_research_exposure_summary_payload",
)


DEFAULT_RESEARCH_PORTFOLIO_RESEARCH_EXPOSURE_SUMMARY_CONFIG_VERSION = (
    "research-portfolio-research-exposure-summary-v0"
)

_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = ("pass", "watch", "blocked")
_DIMENSIONS = (
    "domain",
    "settlement_window",
    "source_dependency",
    "model_dependency",
)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNMAPPED_SOURCE_DEPENDENCY_KEY = "unmapped_source_dependency"
_UNMAPPED_MODEL_DEPENDENCY_KEY = "unmapped_model_dependency"
_UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "net" + "work",
    "data" + "base",
    "persist",
    "mutation",
    "credential",
    "secret",
    "private",
    "b" + "uy",
    "s" + "ell",
    "tr" + "ade",
    "tr" + "ading",
    "inv" + "estment",
    "ad" + "vice",
    "pos" + "ition",
    "ord" + "er",
)
_REASON_CODE_SEQUENCE = (
    "no_research_queue_items",
    "domain_exposure_pass",
    "domain_exposure_watch",
    "domain_exposure_blocked",
    "settlement_window_exposure_pass",
    "settlement_window_exposure_watch",
    "settlement_window_exposure_blocked",
    "source_dependency_exposure_pass",
    "source_dependency_exposure_watch",
    "source_dependency_exposure_blocked",
    "model_dependency_exposure_pass",
    "model_dependency_exposure_watch",
    "model_dependency_exposure_blocked",
    "missing_source_dependency",
    "missing_model_dependency",
    "research_exposure_summary_pass",
    "research_exposure_summary_watch",
    "research_exposure_summary_blocked",
)


@dataclass(frozen=True)
class ResearchPortfolioResearchExposureSummaryConfig:
    config_version: str = (
        DEFAULT_RESEARCH_PORTFOLIO_RESEARCH_EXPOSURE_SUMMARY_CONFIG_VERSION
    )
    watch_domain_share: Decimal = Decimal("0.500000")
    block_domain_share: Decimal = Decimal("0.666667")
    watch_settlement_window_share: Decimal = Decimal("0.500000")
    block_settlement_window_share: Decimal = Decimal("0.666667")
    watch_source_dependency_share: Decimal = Decimal("0.500000")
    block_source_dependency_share: Decimal = Decimal("0.666667")
    watch_model_dependency_share: Decimal = Decimal("0.500000")
    block_model_dependency_share: Decimal = Decimal("0.666667")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPortfolioResearchExposureSummaryConfig:
            raise TypeError(
                "ResearchPortfolioResearchExposureSummaryConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPortfolioResearchExposureSummaryConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchPortfolioResearchExposureSummaryConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PORTFOLIO_RESEARCH_EXPOSURE_SUMMARY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_domain_share",
            "block_domain_share",
            "watch_settlement_window_share",
            "block_settlement_window_share",
            "watch_source_dependency_share",
            "block_source_dependency_share",
            "watch_model_dependency_share",
            "block_model_dependency_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "domain",
            self.watch_domain_share,
            self.block_domain_share,
        )
        _require_threshold_pair(
            "settlement_window",
            self.watch_settlement_window_share,
            self.block_settlement_window_share,
        )
        _require_threshold_pair(
            "source_dependency",
            self.watch_source_dependency_share,
            self.block_source_dependency_share,
        )
        _require_threshold_pair(
            "model_dependency",
            self.watch_model_dependency_share,
            self.block_model_dependency_share,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPortfolioResearchExposureInputRow:
    research_item_id: str
    domain: str
    settlement_window: str
    source_dependency_keys: tuple[str, ...]
    model_dependency_keys: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPortfolioResearchExposureInputRow:
            raise TypeError(
                "ResearchPortfolioResearchExposureInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPortfolioResearchExposureInputRow:
            raise ValueError(
                "research row must be exactly "
                "ResearchPortfolioResearchExposureInputRow",
            )
        for field_name in ("research_item_id", "domain", "settlement_window"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_dependency_keys",
            _normalize_public_identifier_tuple(
                "source_dependency_keys",
                self.source_dependency_keys,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "model_dependency_keys",
            _normalize_public_identifier_tuple(
                "model_dependency_keys",
                self.model_dependency_keys,
                allow_empty=True,
            ),
        )
        _require_hard_flags("research row", self)
        _reject_unsafe_public_payload("research row", self)


@dataclass(frozen=True)
class ResearchPortfolioResearchExposurePublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPortfolioResearchExposurePublicPayloadItem:
            raise TypeError(
                "ResearchPortfolioResearchExposurePublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPortfolioResearchExposurePublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchPortfolioResearchExposurePublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchPortfolioResearchExposureBucket:
    exposure_dimension: str
    exposure_key: str
    research_item_count: Decimal
    exposure_share: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPortfolioResearchExposureBucket:
            raise TypeError(
                "ResearchPortfolioResearchExposureBucket does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPortfolioResearchExposureBucket:
            raise ValueError(
                "bucket must be exactly ResearchPortfolioResearchExposureBucket",
            )
        _require_dimension("exposure_dimension", self.exposure_dimension)
        _require_public_identifier("exposure_key", self.exposure_key)
        object.__setattr__(
            self,
            "research_item_count",
            _require_positive_whole_decimal(
                "research_item_count",
                self.research_item_count,
            ),
        )
        object.__setattr__(
            self,
            "exposure_share",
            _require_probability_decimal("exposure_share", self.exposure_share),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("bucket", self)
        _reject_unsafe_public_payload("bucket", self)
        _validate_bucket_consistency(self)


@dataclass(frozen=True)
class ResearchPortfolioResearchExposureReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPortfolioResearchExposureReasonCodeCount:
            raise TypeError(
                "ResearchPortfolioResearchExposureReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPortfolioResearchExposureReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchPortfolioResearchExposureReasonCodeCount",
            )
        _require_public_identifier("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchPortfolioResearchExposureSummaryReport:
    generated_at: datetime
    config_version: str
    research_item_count: Decimal
    domain_count: Decimal
    settlement_window_count: Decimal
    source_dependency_count: Decimal
    model_dependency_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_domain_share: Decimal
    max_settlement_window_share: Decimal
    max_source_dependency_share: Decimal
    max_model_dependency_share: Decimal
    status: str
    rows: tuple[ResearchPortfolioResearchExposureBucket, ...]
    reason_code_counts: tuple[ResearchPortfolioResearchExposureReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchPortfolioResearchExposurePublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPortfolioResearchExposureSummaryReport:
            raise TypeError(
                "ResearchPortfolioResearchExposureSummaryReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPortfolioResearchExposureSummaryReport:
            raise ValueError(
                "report must be exactly ResearchPortfolioResearchExposureSummaryReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PORTFOLIO_RESEARCH_EXPOSURE_SUMMARY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "research_item_count",
            "domain_count",
            "settlement_window_count",
            "source_dependency_count",
            "model_dependency_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_domain_share",
            "max_settlement_window_share",
            "max_source_dependency_share",
            "max_model_dependency_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchPortfolioResearchExposureSummaryReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_portfolio_research_exposure_summary(
    research_rows: Sequence[ResearchPortfolioResearchExposureInputRow],
    *,
    generated_at: datetime,
    config: ResearchPortfolioResearchExposureSummaryConfig | None = None,
    public_payload: Sequence[ResearchPortfolioResearchExposurePublicPayloadItem] = (),
) -> ResearchPortfolioResearchExposureSummaryReport:
    """Build a local, report-only research queue exposure snapshot."""

    if config is None:
        config = ResearchPortfolioResearchExposureSummaryConfig()
    if type(config) is not ResearchPortfolioResearchExposureSummaryConfig:
        raise ValueError(
            "config must be a ResearchPortfolioResearchExposureSummaryConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_research_rows(research_rows)
    payload_items = _normalize_public_payload(public_payload)
    exposure_rows = _build_exposure_rows(normalized_rows, config)
    reason_codes = _summary_reason_codes(exposure_rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "research_item_count": _decimal_count(len(normalized_rows)),
        "domain_count": _dimension_count(exposure_rows, "domain"),
        "settlement_window_count": _dimension_count(
            exposure_rows,
            "settlement_window",
        ),
        "source_dependency_count": _dimension_count(
            exposure_rows,
            "source_dependency",
        ),
        "model_dependency_count": _dimension_count(exposure_rows, "model_dependency"),
        "pass_count": _status_count(exposure_rows, "pass"),
        "watch_count": _status_count(exposure_rows, "watch"),
        "blocked_count": _status_count(exposure_rows, "blocked"),
        "max_domain_share": _max_dimension_share(exposure_rows, "domain"),
        "max_settlement_window_share": _max_dimension_share(
            exposure_rows,
            "settlement_window",
        ),
        "max_source_dependency_share": _max_dimension_share(
            exposure_rows,
            "source_dependency",
        ),
        "max_model_dependency_share": _max_dimension_share(
            exposure_rows,
            "model_dependency",
        ),
        "status": _summary_status(exposure_rows),
        "rows": exposure_rows,
        "reason_code_counts": _reason_code_counts(exposure_rows, reason_codes),
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPortfolioResearchExposureSummaryReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_portfolio_research_exposure_summary_payload(
    report: ResearchPortfolioResearchExposureSummaryReport,
) -> dict[str, object]:
    if type(report) is not ResearchPortfolioResearchExposureSummaryReport:
        raise ValueError(
            "report must be a ResearchPortfolioResearchExposureSummaryReport",
        )
    _require_hard_flags("report", report)
    return report.payload


def _build_exposure_rows(
    research_rows: tuple[ResearchPortfolioResearchExposureInputRow, ...],
    config: ResearchPortfolioResearchExposureSummaryConfig,
) -> tuple[ResearchPortfolioResearchExposureBucket, ...]:
    if not research_rows:
        return ()
    total = _decimal_count(len(research_rows))
    buckets: list[ResearchPortfolioResearchExposureBucket] = []
    bucket_maps = (
        ("domain", _single_value_counts(research_rows, "domain")),
        (
            "settlement_window",
            _single_value_counts(research_rows, "settlement_window"),
        ),
        (
            "source_dependency",
            _multi_value_counts(
                research_rows,
                "source_dependency_keys",
                _UNMAPPED_SOURCE_DEPENDENCY_KEY,
            ),
        ),
        (
            "model_dependency",
            _multi_value_counts(
                research_rows,
                "model_dependency_keys",
                _UNMAPPED_MODEL_DEPENDENCY_KEY,
            ),
        ),
    )
    for dimension, counts in bucket_maps:
        for exposure_key, count in sorted(counts.items(), key=lambda item: item[0]):
            count_decimal = _decimal_count(count)
            share = _ratio(count_decimal / total)
            status = _bucket_status(
                dimension=dimension,
                exposure_key=exposure_key,
                exposure_share=share,
                config=config,
            )
            buckets.append(
                ResearchPortfolioResearchExposureBucket(
                    exposure_dimension=dimension,
                    exposure_key=exposure_key,
                    research_item_count=count_decimal,
                    exposure_share=share,
                    status=status,
                    reason_codes=_bucket_reason_codes(
                        dimension=dimension,
                        exposure_key=exposure_key,
                        status=status,
                    ),
                ),
            )
    return tuple(
        sorted(
            buckets,
            key=lambda row: (row.exposure_dimension, row.exposure_key),
        ),
    )


def _single_value_counts(
    research_rows: tuple[ResearchPortfolioResearchExposureInputRow, ...],
    field_name: str,
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in research_rows:
        value = getattr(row, field_name)
        if type(value) is not str:
            raise ValueError(f"{field_name} must resolve to a string")
        counts[value] += 1
    return counts


def _multi_value_counts(
    research_rows: tuple[ResearchPortfolioResearchExposureInputRow, ...],
    field_name: str,
    unmapped_key: str,
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in research_rows:
        values = getattr(row, field_name)
        if type(values) is not tuple:
            raise ValueError(f"{field_name} must resolve to a tuple")
        for value in values or (unmapped_key,):
            counts[value] += 1
    return counts


def _bucket_status(
    *,
    dimension: str,
    exposure_key: str,
    exposure_share: Decimal,
    config: ResearchPortfolioResearchExposureSummaryConfig,
) -> str:
    if (
        dimension == "source_dependency"
        and exposure_key == _UNMAPPED_SOURCE_DEPENDENCY_KEY
        or dimension == "model_dependency"
        and exposure_key == _UNMAPPED_MODEL_DEPENDENCY_KEY
    ):
        return "blocked"
    watch_share, block_share = _thresholds(config, dimension)
    if exposure_share > block_share:
        return "blocked"
    if exposure_share > watch_share:
        return "watch"
    return "pass"


def _bucket_reason_codes(
    *,
    dimension: str,
    exposure_key: str,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"{dimension}_exposure_{status}"]
    if (
        dimension == "source_dependency"
        and exposure_key == _UNMAPPED_SOURCE_DEPENDENCY_KEY
    ):
        reason_codes.append("missing_source_dependency")
    if (
        dimension == "model_dependency"
        and exposure_key == _UNMAPPED_MODEL_DEPENDENCY_KEY
    ):
        reason_codes.append("missing_model_dependency")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _thresholds(
    config: ResearchPortfolioResearchExposureSummaryConfig,
    dimension: str,
) -> tuple[Decimal, Decimal]:
    _require_dimension("dimension", dimension)
    if dimension == "domain":
        return config.watch_domain_share, config.block_domain_share
    if dimension == "settlement_window":
        return (
            config.watch_settlement_window_share,
            config.block_settlement_window_share,
        )
    if dimension == "source_dependency":
        return config.watch_source_dependency_share, config.block_source_dependency_share
    return config.watch_model_dependency_share, config.block_model_dependency_share


def _summary_reason_codes(
    rows: tuple[ResearchPortfolioResearchExposureBucket, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_research_queue_items",)
    if all(row.status == "pass" for row in rows):
        return ("research_exposure_summary_pass",)
    reason_codes = [code for row in rows for code in row.reason_codes]
    reason_codes.append(f"research_exposure_summary_{_summary_status(rows)}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _summary_status(
    rows: tuple[ResearchPortfolioResearchExposureBucket, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchPortfolioResearchExposureBucket, ...],
    status: str,
) -> Decimal:
    _require_status("status", status)
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _dimension_count(
    rows: tuple[ResearchPortfolioResearchExposureBucket, ...],
    dimension: str,
) -> Decimal:
    _require_dimension("dimension", dimension)
    return _decimal_count(sum(1 for row in rows if row.exposure_dimension == dimension))


def _max_dimension_share(
    rows: tuple[ResearchPortfolioResearchExposureBucket, ...],
    dimension: str,
) -> Decimal:
    _require_dimension("dimension", dimension)
    return max(
        (row.exposure_share for row in rows if row.exposure_dimension == dimension),
        default=_ZERO,
    )


def _reason_code_counts(
    rows: tuple[ResearchPortfolioResearchExposureBucket, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchPortfolioResearchExposureReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchPortfolioResearchExposureReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchPortfolioResearchExposureReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _normalize_research_rows(
    research_rows: Sequence[ResearchPortfolioResearchExposureInputRow],
) -> tuple[ResearchPortfolioResearchExposureInputRow, ...]:
    if isinstance(research_rows, (str, bytes)) or not isinstance(research_rows, Sequence):
        raise ValueError("research_rows must be a sequence")
    normalized: list[ResearchPortfolioResearchExposureInputRow] = []
    seen_ids: set[str] = set()
    for row in research_rows:
        if type(row) is not ResearchPortfolioResearchExposureInputRow:
            raise ValueError(
                "research_rows must contain "
                "ResearchPortfolioResearchExposureInputRow values",
            )
        _require_hard_flags("research row", row)
        if row.research_item_id in seen_ids:
            raise ValueError("research_item_id values must be unique")
        seen_ids.add(row.research_item_id)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.research_item_id))


def _normalize_rows(
    rows: tuple[ResearchPortfolioResearchExposureBucket, ...],
) -> tuple[ResearchPortfolioResearchExposureBucket, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchPortfolioResearchExposureBucket:
            raise ValueError(
                "rows must contain ResearchPortfolioResearchExposureBucket values",
            )
        _require_hard_flags("bucket", row)
    sorted_rows = tuple(
        sorted(rows, key=lambda row: (row.exposure_dimension, row.exposure_key)),
    )
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by exposure_dimension and exposure_key")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchPortfolioResearchExposureReasonCodeCount, ...],
) -> tuple[ResearchPortfolioResearchExposureReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchPortfolioResearchExposureReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchPortfolioResearchExposureReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _normalize_public_payload(
    values: Sequence[ResearchPortfolioResearchExposurePublicPayloadItem],
) -> tuple[ResearchPortfolioResearchExposurePublicPayloadItem, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchPortfolioResearchExposurePublicPayloadItem] = []
    for value in values:
        if type(value) is not ResearchPortfolioResearchExposurePublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "ResearchPortfolioResearchExposurePublicPayloadItem",
            )
        _require_hard_flags("public payload item", value)
        normalized.append(value)
    return tuple(sorted(normalized, key=lambda value: value.key))


def _normalize_public_identifier_tuple(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_identifier(field_name, value)
        if value not in normalized:
            normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(normalized))


def _validate_bucket_consistency(
    row: ResearchPortfolioResearchExposureBucket,
) -> None:
    expected_status_code = f"{row.exposure_dimension}_exposure_{row.status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("reason_codes must include the bucket status reason")
    if (
        row.exposure_dimension == "source_dependency"
        and row.exposure_key == _UNMAPPED_SOURCE_DEPENDENCY_KEY
        and "missing_source_dependency" not in row.reason_codes
    ):
        raise ValueError("missing source dependency bucket must carry its reason")
    if (
        row.exposure_dimension == "model_dependency"
        and row.exposure_key == _UNMAPPED_MODEL_DEPENDENCY_KEY
        and "missing_model_dependency" not in row.reason_codes
    ):
        raise ValueError("missing model dependency bucket must carry its reason")
    if (
        "missing_source_dependency" in row.reason_codes
        and row.exposure_dimension != "source_dependency"
    ):
        raise ValueError("missing_source_dependency must stay in source_dependency rows")
    if (
        "missing_model_dependency" in row.reason_codes
        and row.exposure_dimension != "model_dependency"
    ):
        raise ValueError("missing_model_dependency must stay in model_dependency rows")


def _validate_report_consistency(
    report: ResearchPortfolioResearchExposureSummaryReport,
) -> None:
    if report.research_item_count == _ZERO and report.rows:
        raise ValueError("rows must be empty when research_item_count is zero")
    if report.research_item_count > _ZERO:
        for row in report.rows:
            if row.research_item_count > report.research_item_count:
                raise ValueError("bucket count must not exceed research_item_count")
            if row.exposure_share != _ratio(
                row.research_item_count / report.research_item_count,
            ):
                raise ValueError("exposure_share must match bucket count share")
    if report.domain_count != _dimension_count(report.rows, "domain"):
        raise ValueError("domain_count must match rows")
    if report.settlement_window_count != _dimension_count(
        report.rows,
        "settlement_window",
    ):
        raise ValueError("settlement_window_count must match rows")
    if report.source_dependency_count != _dimension_count(
        report.rows,
        "source_dependency",
    ):
        raise ValueError("source_dependency_count must match rows")
    if report.model_dependency_count != _dimension_count(report.rows, "model_dependency"):
        raise ValueError("model_dependency_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.max_domain_share != _max_dimension_share(report.rows, "domain"):
        raise ValueError("max_domain_share must match rows")
    if report.max_settlement_window_share != _max_dimension_share(
        report.rows,
        "settlement_window",
    ):
        raise ValueError("max_settlement_window_share must match rows")
    if report.max_source_dependency_share != _max_dimension_share(
        report.rows,
        "source_dependency",
    ):
        raise ValueError("max_source_dependency_share must match rows")
    if report.max_model_dependency_share != _max_dimension_share(
        report.rows,
        "model_dependency",
    ):
        raise ValueError("max_model_dependency_share must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _require_threshold_pair(
    label: str,
    watch_share: Decimal,
    block_share: Decimal,
) -> None:
    if block_share <= watch_share:
        raise ValueError(f"{label} block share must be greater than watch share")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be nonempty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_dimension(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _DIMENSIONS:
        raise ValueError(f"{field_name} must be a supported exposure dimension")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be a supported status")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return value.quantize(_QUANTUM, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(_QUANTUM, rounding=ROUND_HALF_UP)


def _ratio(value: Decimal) -> Decimal:
    normalized = value.quantize(_QUANTUM, rounding=ROUND_HALF_UP)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _normalize_reason_codes(
    field_name: str,
    values: object,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_identifier(field_name, value)
        if value not in _REASON_CODE_SEQUENCE:
            raise ValueError(f"{field_name} contains an unsupported reason code")
        if value not in normalized:
            normalized.append(value)
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(code for code in _REASON_CODE_SEQUENCE if code in normalized)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchPortfolioResearchExposureSummaryReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")
