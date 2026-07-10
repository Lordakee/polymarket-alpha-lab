"""Pure report-only primary-authority disagreement SLA scoring."""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_SOURCE_PRIMARY_AUTHORITY_DISAGREEMENT_SLA_REPORT_CONFIG_VERSION = (
    "research-source-primary-authority-disagreement-sla-report-v0"
)
RESEARCH_SOURCE_PRIMARY_AUTHORITY_DISAGREEMENT_SLA_STATUSES = (
    "pass",
    "watch",
    "block",
)

EMPTY_REASON = "primary_authority_disagreement_sla_empty"
CLEAR_REASON = "primary_authority_disagreement_sla_clear"
OPEN_WATCH_REASON = "primary_authority_disagreement_open_watch"
OPEN_BLOCK_REASON = "primary_authority_disagreement_open_block"
PRIMARY_AUTHORITY_WATCH_REASON = "primary_authority_score_watch"
PRIMARY_AUTHORITY_BLOCK_REASON = "primary_authority_score_block"
COUNTER_AUTHORITY_WATCH_REASON = "counter_authority_pressure_watch"
COUNTER_AUTHORITY_BLOCK_REASON = "counter_authority_pressure_block"
INDEPENDENT_CROSSCHECK_WATCH_REASON = "independent_crosscheck_watch"
INDEPENDENT_CROSSCHECK_BLOCK_REASON = "independent_crosscheck_block"

ROW_REASON_CODES = (
    CLEAR_REASON,
    OPEN_BLOCK_REASON,
    PRIMARY_AUTHORITY_BLOCK_REASON,
    COUNTER_AUTHORITY_BLOCK_REASON,
    INDEPENDENT_CROSSCHECK_BLOCK_REASON,
    OPEN_WATCH_REASON,
    PRIMARY_AUTHORITY_WATCH_REASON,
    COUNTER_AUTHORITY_WATCH_REASON,
    INDEPENDENT_CROSSCHECK_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason for reason in REPORT_REASON_CODES if reason not in (EMPTY_REASON, CLEAR_REASON)
)

DECIMAL_CONTEXT = Context(prec=64)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FOUR = Decimal("4.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SHA256_HEX_LENGTH = 64
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "candidate-id",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "slug",
    "question",
    "source_url",
    "source-url",
    "source_text",
    "source-text",
    "raw_url",
    "raw-url",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "account",
    "balance",
    "order",
    "trade",
    "private_key",
    "authentication",
    "credential",
    "secret",
    "api_key",
    "broker",
    "execution",
    "recommend",
    "sizing",
    "notional",
    "position",
    "stake",
    "database",
    "network",
    "file_path",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "candidate-",
    "market_id",
    "market-",
    "market_slug",
    "market-slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "http://",
    "https://",
    "www.",
    "postgres://",
    "mysql://",
    "jdbc:",
    "dsn",
    "table",
    "token",
    "wallet",
    "account",
    "balance",
    "order",
    "trade",
    "private_key",
    "live",
    "authentication",
    "credential",
    "secret",
    "api_key",
    "broker",
    "execution",
    "file://",
)


@dataclass(frozen=True)
class ResearchSourcePrimaryAuthorityDisagreementSlaConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_PRIMARY_AUTHORITY_DISAGREEMENT_SLA_REPORT_CONFIG_VERSION
    )
    disagreement_watch_age_seconds: Decimal = Decimal("1800.000000")
    disagreement_block_age_seconds: Decimal = Decimal("7200.000000")
    primary_authority_watch_threshold: Decimal = Decimal("0.700000")
    primary_authority_block_threshold: Decimal = Decimal("0.400000")
    counter_authority_watch_pressure: Decimal = Decimal("0.300000")
    counter_authority_block_pressure: Decimal = Decimal("0.600000")
    minimum_independent_crosscheck_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryAuthorityDisagreementSlaConfig:
            raise TypeError(
                "ResearchSourcePrimaryAuthorityDisagreementSlaConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchSourcePrimaryAuthorityDisagreementSlaConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "disagreement_watch_age_seconds",
            "disagreement_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "primary_authority_watch_threshold",
            "primary_authority_block_threshold",
            "counter_authority_watch_pressure",
            "counter_authority_block_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_independent_crosscheck_count",
            _require_positive_whole_decimal(
                "minimum_independent_crosscheck_count",
                self.minimum_independent_crosscheck_count,
            ),
        )
        _validate_config(self)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_PRIMARY_AUTHORITY_DISAGREEMENT_SLA_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        require_paper_only_flags("config", self)
        _reject_public_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchSourcePrimaryAuthorityDisagreementSlaSignal:
    review_bucket: str
    disagreement_opened_at: datetime | None
    primary_authority_score: Decimal
    counter_authority_pressure_score: Decimal
    independent_crosscheck_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryAuthorityDisagreementSlaSignal:
            raise TypeError(
                "ResearchSourcePrimaryAuthorityDisagreementSlaSignal "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "signal",
            self,
            ResearchSourcePrimaryAuthorityDisagreementSlaSignal,
        )
        object.__setattr__(
            self,
            "review_bucket",
            _require_public_bucket("review_bucket", self.review_bucket),
        )
        object.__setattr__(
            self,
            "disagreement_opened_at",
            _optional_utc("disagreement_opened_at", self.disagreement_opened_at),
        )
        for field_name in (
            "primary_authority_score",
            "counter_authority_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "independent_crosscheck_count",
            _require_nonnegative_whole_decimal(
                "independent_crosscheck_count",
                self.independent_crosscheck_count,
            ),
        )
        require_paper_only_flags("signal", self)
        _reject_public_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchSourcePrimaryAuthorityDisagreementSlaRow:
    review_bucket: str
    disagreement_opened_at: datetime | None
    disagreement_age_seconds: Decimal
    primary_authority_score: Decimal
    counter_authority_pressure_score: Decimal
    independent_crosscheck_count: Decimal
    sla_score: Decimal
    crosscheck_score: Decimal
    resolution_readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchSourcePrimaryAuthorityDisagreementSlaConfig | None
    ] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryAuthorityDisagreementSlaRow:
            raise TypeError(
                "ResearchSourcePrimaryAuthorityDisagreementSlaRow "
                "does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchSourcePrimaryAuthorityDisagreementSlaConfig | None,
    ) -> None:
        _require_exact_type("row", self, ResearchSourcePrimaryAuthorityDisagreementSlaRow)
        normalized_validation_config = _normalize_validation_config(validation_config)
        object.__setattr__(
            self,
            "_validation_config",
            normalized_validation_config,
        )
        object.__setattr__(
            self,
            "review_bucket",
            _require_public_bucket("review_bucket", self.review_bucket),
        )
        object.__setattr__(
            self,
            "disagreement_opened_at",
            _optional_utc("disagreement_opened_at", self.disagreement_opened_at),
        )
        object.__setattr__(
            self,
            "disagreement_age_seconds",
            _require_nonnegative_decimal(
                "disagreement_age_seconds",
                self.disagreement_age_seconds,
            ),
        )
        for field_name in (
            "primary_authority_score",
            "counter_authority_pressure_score",
            "sla_score",
            "crosscheck_score",
            "resolution_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "independent_crosscheck_count",
            _require_nonnegative_whole_decimal(
                "independent_crosscheck_count",
                self.independent_crosscheck_count,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self, normalized_validation_config)
        require_paper_only_flags("row", self)
        _reject_public_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount:
            raise TypeError(
                "ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount,
        )
        if type(self.reason_code) is not str or self.reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be a known reason code")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        require_paper_only_flags("reason_code_count", self)
        _reject_public_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchSourcePrimaryAuthorityDisagreementSlaReport:
    generated_at: datetime
    config_version: str
    review_bucket_count: Decimal
    open_disagreement_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    overdue_disagreement_count: Decimal
    weak_primary_authority_count: Decimal
    counter_authority_pressure_count: Decimal
    low_independent_crosscheck_count: Decimal
    lowest_resolution_readiness_score: Decimal
    highest_disagreement_age_seconds: Decimal
    highest_counter_authority_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchSourcePrimaryAuthorityDisagreementSlaRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchSourcePrimaryAuthorityDisagreementSlaConfig | None
    ] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryAuthorityDisagreementSlaReport:
            raise TypeError(
                "ResearchSourcePrimaryAuthorityDisagreementSlaReport "
                "does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchSourcePrimaryAuthorityDisagreementSlaConfig | None,
    ) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchSourcePrimaryAuthorityDisagreementSlaReport,
        )
        normalized_validation_config = _normalize_validation_config(validation_config)
        object.__setattr__(
            self,
            "_validation_config",
            normalized_validation_config,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != normalized_validation_config.config_version:
            raise ValueError("config_version must match validation_config")
        for field_name in (
            "review_bucket_count",
            "open_disagreement_count",
            "pass_count",
            "watch_count",
            "block_count",
            "overdue_disagreement_count",
            "weak_primary_authority_count",
            "counter_authority_pressure_count",
            "low_independent_crosscheck_count",
            "highest_disagreement_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_or_scaled_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "lowest_resolution_readiness_score",
            "highest_counter_authority_pressure_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self, normalized_validation_config)
        require_paper_only_flags("report", self)
        _require_or_set_digest(self)
        _reject_public_payload(_json_ready(self))


_PUBLIC_REPORT_SCHEMA = (
    "generated_at",
    "config_version",
    "review_bucket_count",
    "open_disagreement_count",
    "pass_count",
    "watch_count",
    "block_count",
    "overdue_disagreement_count",
    "weak_primary_authority_count",
    "counter_authority_pressure_count",
    "low_independent_crosscheck_count",
    "lowest_resolution_readiness_score",
    "highest_disagreement_age_seconds",
    "highest_counter_authority_pressure_score",
    "status",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_PUBLIC_ROW_SCHEMA = (
    "review_bucket",
    "disagreement_opened_at",
    "disagreement_age_seconds",
    "primary_authority_score",
    "counter_authority_pressure_score",
    "independent_crosscheck_count",
    "sla_score",
    "crosscheck_score",
    "resolution_readiness_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_PUBLIC_REASON_CODE_COUNT_SCHEMA = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)


def build_research_source_primary_authority_disagreement_sla_report(
    signals: list[ResearchSourcePrimaryAuthorityDisagreementSlaSignal]
    | tuple[ResearchSourcePrimaryAuthorityDisagreementSlaSignal, ...],
    *,
    config: ResearchSourcePrimaryAuthorityDisagreementSlaConfig,
    generated_at: datetime,
) -> ResearchSourcePrimaryAuthorityDisagreementSlaReport:
    if type(config) is not ResearchSourcePrimaryAuthorityDisagreementSlaConfig:
        raise ValueError(
            "config must be a ResearchSourcePrimaryAuthorityDisagreementSlaConfig",
        )
    config = ResearchSourcePrimaryAuthorityDisagreementSlaConfig(**asdict(config))
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_signal(signal, config=config, generated_at=generated_at_utc)
                for signal in _normalize_signals(signals)
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchSourcePrimaryAuthorityDisagreementSlaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        review_bucket_count=_count(len(rows)),
        open_disagreement_count=_condition_count(
            rows,
            lambda row: row.disagreement_opened_at is not None,
        ),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        overdue_disagreement_count=_reason_count(rows, (OPEN_BLOCK_REASON,)),
        weak_primary_authority_count=_reason_count(
            rows,
            (PRIMARY_AUTHORITY_WATCH_REASON, PRIMARY_AUTHORITY_BLOCK_REASON),
        ),
        counter_authority_pressure_count=_reason_count(
            rows,
            (COUNTER_AUTHORITY_WATCH_REASON, COUNTER_AUTHORITY_BLOCK_REASON),
        ),
        low_independent_crosscheck_count=_reason_count(
            rows,
            (INDEPENDENT_CROSSCHECK_WATCH_REASON, INDEPENDENT_CROSSCHECK_BLOCK_REASON),
        ),
        lowest_resolution_readiness_score=min(
            (row.resolution_readiness_score for row in rows),
            default=ZERO,
        ),
        highest_disagreement_age_seconds=max(
            (row.disagreement_age_seconds for row in rows),
            default=ZERO,
        ),
        highest_counter_authority_pressure_score=max(
            (row.counter_authority_pressure_score for row in rows),
            default=ZERO,
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
        validation_config=config,
    )


def research_source_primary_authority_disagreement_sla_report_payload(
    report: ResearchSourcePrimaryAuthorityDisagreementSlaReport,
) -> "FrozenJsonObject":
    payload = _validated_report_public_payload(report, verify_stored_digest=True)
    return _freeze_json_object(payload)


def research_source_primary_authority_disagreement_sla_report_digest(
    report: ResearchSourcePrimaryAuthorityDisagreementSlaReport,
) -> str:
    payload = _validated_report_public_payload(report, verify_stored_digest=False)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_source_primary_authority_disagreement_sla_report_digest(
    report: ResearchSourcePrimaryAuthorityDisagreementSlaReport,
) -> bool:
    _validated_report_public_payload(report, verify_stored_digest=True)
    return True


def validate_research_source_primary_authority_disagreement_sla_public_payload(
    payload: dict[str, Any],
    *,
    config: ResearchSourcePrimaryAuthorityDisagreementSlaConfig | None = None,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload(payload)
    _report_from_public_payload(
        payload,
        validation_config=_normalize_validation_config(config),
    )
    return True


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def _validated_report_public_payload(
    report: ResearchSourcePrimaryAuthorityDisagreementSlaReport,
    *,
    verify_stored_digest: bool,
) -> dict[str, Any]:
    if type(report) is not ResearchSourcePrimaryAuthorityDisagreementSlaReport:
        raise ValueError(
            "report must be a ResearchSourcePrimaryAuthorityDisagreementSlaReport",
        )
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    if not verify_stored_digest:
        unsigned = dict(payload)
        unsigned.pop("derived_validation_digest", None)
        payload["derived_validation_digest"] = _canonical_digest(unsigned)
    _report_from_public_payload(
        payload,
        validation_config=_normalize_validation_config(
            getattr(report, "_validation_config", None),
        ),
    )
    return payload


def _report_from_public_payload(
    value: object,
    *,
    validation_config: ResearchSourcePrimaryAuthorityDisagreementSlaConfig,
) -> ResearchSourcePrimaryAuthorityDisagreementSlaReport:
    payload = _require_public_object_schema(
        "public payload",
        value,
        _PUBLIC_REPORT_SCHEMA,
    )
    config_version = _public_string("config_version", payload["config_version"])
    if config_version != validation_config.config_version:
        raise ValueError("config_version must be the supported config version")
    generated_at = _public_datetime("generated_at", payload["generated_at"])
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(item)
        for item in _require_public_array(
            "reason_code_counts",
            payload["reason_code_counts"],
        )
    )
    rows = tuple(
        _row_from_public_payload(
            item,
            validation_config=validation_config,
            generated_at=generated_at,
        )
        for item in _require_public_array("rows", payload["rows"])
    )
    return ResearchSourcePrimaryAuthorityDisagreementSlaReport(
        generated_at=generated_at,
        config_version=config_version,
        review_bucket_count=_public_decimal(
            "review_bucket_count",
            payload["review_bucket_count"],
        ),
        open_disagreement_count=_public_decimal(
            "open_disagreement_count",
            payload["open_disagreement_count"],
        ),
        pass_count=_public_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_decimal("watch_count", payload["watch_count"]),
        block_count=_public_decimal("block_count", payload["block_count"]),
        overdue_disagreement_count=_public_decimal(
            "overdue_disagreement_count",
            payload["overdue_disagreement_count"],
        ),
        weak_primary_authority_count=_public_decimal(
            "weak_primary_authority_count",
            payload["weak_primary_authority_count"],
        ),
        counter_authority_pressure_count=_public_decimal(
            "counter_authority_pressure_count",
            payload["counter_authority_pressure_count"],
        ),
        low_independent_crosscheck_count=_public_decimal(
            "low_independent_crosscheck_count",
            payload["low_independent_crosscheck_count"],
        ),
        lowest_resolution_readiness_score=_public_decimal(
            "lowest_resolution_readiness_score",
            payload["lowest_resolution_readiness_score"],
        ),
        highest_disagreement_age_seconds=_public_decimal(
            "highest_disagreement_age_seconds",
            payload["highest_disagreement_age_seconds"],
        ),
        highest_counter_authority_pressure_score=_public_decimal(
            "highest_counter_authority_pressure_score",
            payload["highest_counter_authority_pressure_score"],
        ),
        status=_public_string("status", payload["status"]),
        reason_codes=_public_string_tuple("reason_codes", payload["reason_codes"]),
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=_public_sha256(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_public_true_flag("paper_only", payload["paper_only"]),
        report_only=_public_true_flag("report_only", payload["report_only"]),
        readonly=_public_true_flag("readonly", payload["readonly"]),
        validation_config=validation_config,
    )


def _row_from_public_payload(
    value: object,
    *,
    validation_config: ResearchSourcePrimaryAuthorityDisagreementSlaConfig,
    generated_at: datetime,
) -> ResearchSourcePrimaryAuthorityDisagreementSlaRow:
    payload = _require_public_object_schema("row", value, _PUBLIC_ROW_SCHEMA)
    disagreement_opened_at = _public_optional_datetime(
        "disagreement_opened_at",
        payload["disagreement_opened_at"],
    )
    disagreement_age_seconds = _public_decimal(
        "disagreement_age_seconds",
        payload["disagreement_age_seconds"],
    )
    if disagreement_opened_at is not None:
        if disagreement_opened_at > generated_at:
            raise ValueError("disagreement_opened_at must not be after generated_at")
        if disagreement_age_seconds != _duration_seconds(
            disagreement_opened_at,
            generated_at,
        ):
            raise ValueError(
                "disagreement_age_seconds must match disagreement_opened_at",
            )
    return ResearchSourcePrimaryAuthorityDisagreementSlaRow(
        review_bucket=_public_string("review_bucket", payload["review_bucket"]),
        disagreement_opened_at=disagreement_opened_at,
        disagreement_age_seconds=disagreement_age_seconds,
        primary_authority_score=_public_decimal(
            "primary_authority_score",
            payload["primary_authority_score"],
        ),
        counter_authority_pressure_score=_public_decimal(
            "counter_authority_pressure_score",
            payload["counter_authority_pressure_score"],
        ),
        independent_crosscheck_count=_public_decimal(
            "independent_crosscheck_count",
            payload["independent_crosscheck_count"],
        ),
        sla_score=_public_decimal("sla_score", payload["sla_score"]),
        crosscheck_score=_public_decimal(
            "crosscheck_score",
            payload["crosscheck_score"],
        ),
        resolution_readiness_score=_public_decimal(
            "resolution_readiness_score",
            payload["resolution_readiness_score"],
        ),
        status=_public_string("status", payload["status"]),
        reason_codes=_public_string_tuple("reason_codes", payload["reason_codes"]),
        paper_only=_public_true_flag("paper_only", payload["paper_only"]),
        report_only=_public_true_flag("report_only", payload["report_only"]),
        readonly=_public_true_flag("readonly", payload["readonly"]),
        validation_config=validation_config,
    )


def _reason_code_count_from_public_payload(
    value: object,
) -> ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount:
    payload = _require_public_object_schema(
        "reason_code_count",
        value,
        _PUBLIC_REASON_CODE_COUNT_SCHEMA,
    )
    return ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount(
        reason_code=_public_string("reason_code", payload["reason_code"]),
        count=_public_decimal("count", payload["count"]),
        paper_only=_public_true_flag("paper_only", payload["paper_only"]),
        report_only=_public_true_flag("report_only", payload["report_only"]),
        readonly=_public_true_flag("readonly", payload["readonly"]),
    )


def _require_public_object_schema(
    label: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    for key in value:
        if type(key) is not str:
            raise ValueError(f"{label} keys must be strings")
    if set(value) != set(expected_fields):
        raise ValueError(f"{label} schema must use exact fields")
    return value


def _require_public_array(field_name: str, value: object) -> tuple[Any, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    return tuple(value)


def _public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _public_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    items = _require_public_array(field_name, value)
    for item in items:
        if type(item) is not str:
            raise ValueError(f"{field_name} must contain strings")
    return items


def _public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = _decimal(field_name, decimal_value)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _public_datetime(field_name: str, value: object) -> datetime:
    string_value = _public_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(string_value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != string_value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


def _public_optional_datetime(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _public_datetime(field_name, value)


def _public_true_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _public_sha256(field_name: str, value: object) -> str:
    string_value = _public_string(field_name, value)
    _require_sha256(field_name, string_value)
    return string_value


def _row_from_signal(
    signal: ResearchSourcePrimaryAuthorityDisagreementSlaSignal,
    *,
    config: ResearchSourcePrimaryAuthorityDisagreementSlaConfig,
    generated_at: datetime,
) -> ResearchSourcePrimaryAuthorityDisagreementSlaRow:
    if signal.disagreement_opened_at is not None:
        if signal.disagreement_opened_at > generated_at:
            raise ValueError("disagreement_opened_at must not be after generated_at")
        disagreement_age_seconds = _duration_seconds(
            signal.disagreement_opened_at,
            generated_at,
        )
    else:
        disagreement_age_seconds = ZERO
    sla_score = _sla_score(
        disagreement_age_seconds=disagreement_age_seconds,
        disagreement_opened=signal.disagreement_opened_at is not None,
        config=config,
    )
    crosscheck_score = _bounded_ratio(
        signal.independent_crosscheck_count,
        config.minimum_independent_crosscheck_count,
    )
    reason_codes = _row_reason_codes(
        disagreement_opened_at=signal.disagreement_opened_at,
        primary_authority_score=signal.primary_authority_score,
        counter_authority_pressure_score=signal.counter_authority_pressure_score,
        independent_crosscheck_count=signal.independent_crosscheck_count,
        disagreement_age_seconds=disagreement_age_seconds,
        config=config,
    )
    return ResearchSourcePrimaryAuthorityDisagreementSlaRow(
        review_bucket=signal.review_bucket,
        disagreement_opened_at=signal.disagreement_opened_at,
        disagreement_age_seconds=disagreement_age_seconds,
        primary_authority_score=signal.primary_authority_score,
        counter_authority_pressure_score=signal.counter_authority_pressure_score,
        independent_crosscheck_count=signal.independent_crosscheck_count,
        sla_score=sla_score,
        crosscheck_score=crosscheck_score,
        resolution_readiness_score=_resolution_readiness_score(
            primary_authority_score=signal.primary_authority_score,
            counter_authority_pressure_score=signal.counter_authority_pressure_score,
            sla_score=sla_score,
            crosscheck_score=crosscheck_score,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    disagreement_opened_at: datetime | None,
    primary_authority_score: Decimal,
    counter_authority_pressure_score: Decimal,
    independent_crosscheck_count: Decimal,
    disagreement_age_seconds: Decimal,
    config: ResearchSourcePrimaryAuthorityDisagreementSlaConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if disagreement_opened_at is not None:
        if disagreement_age_seconds >= config.disagreement_block_age_seconds:
            reasons.append(OPEN_BLOCK_REASON)
        elif disagreement_age_seconds > config.disagreement_watch_age_seconds:
            reasons.append(OPEN_WATCH_REASON)
    if primary_authority_score < config.primary_authority_block_threshold:
        reasons.append(PRIMARY_AUTHORITY_BLOCK_REASON)
    elif primary_authority_score < config.primary_authority_watch_threshold:
        reasons.append(PRIMARY_AUTHORITY_WATCH_REASON)
    if counter_authority_pressure_score >= config.counter_authority_block_pressure:
        reasons.append(COUNTER_AUTHORITY_BLOCK_REASON)
    elif counter_authority_pressure_score >= config.counter_authority_watch_pressure:
        reasons.append(COUNTER_AUTHORITY_WATCH_REASON)
    if independent_crosscheck_count == ZERO:
        reasons.append(INDEPENDENT_CROSSCHECK_BLOCK_REASON)
    elif independent_crosscheck_count < config.minimum_independent_crosscheck_count:
        reasons.append(INDEPENDENT_CROSSCHECK_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _sla_score(
    *,
    disagreement_age_seconds: Decimal,
    disagreement_opened: bool,
    config: ResearchSourcePrimaryAuthorityDisagreementSlaConfig,
) -> Decimal:
    if not disagreement_opened:
        return ONE
    if disagreement_age_seconds <= config.disagreement_watch_age_seconds:
        return ONE
    if disagreement_age_seconds >= config.disagreement_block_age_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        span = config.disagreement_block_age_seconds - config.disagreement_watch_age_seconds
        consumed = disagreement_age_seconds - config.disagreement_watch_age_seconds
        return (ONE - (consumed / span)).quantize(QUANT)


def _resolution_readiness_score(
    *,
    primary_authority_score: Decimal,
    counter_authority_pressure_score: Decimal,
    sla_score: Decimal,
    crosscheck_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        counter_support_score = ONE - counter_authority_pressure_score
        return (
            (
                primary_authority_score
                + counter_support_score
                + sla_score
                + crosscheck_score
            )
            / FOUR
        ).quantize(QUANT)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(numerator / denominator, ONE).quantize(QUANT)


def _normalize_signals(
    value: object,
) -> tuple[ResearchSourcePrimaryAuthorityDisagreementSlaSignal, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    signals = tuple(value)
    seen: set[str] = set()
    for signal in signals:
        if type(signal) is not ResearchSourcePrimaryAuthorityDisagreementSlaSignal:
            raise ValueError(
                "signals must contain "
                "ResearchSourcePrimaryAuthorityDisagreementSlaSignal",
            )
        require_paper_only_flags("signal", signal)
        _reject_public_payload(_json_ready(signal))
        if signal.review_bucket in seen:
            raise ValueError("signals must be unique by review_bucket")
        seen.add(signal.review_bucket)
    return tuple(sorted(signals, key=lambda signal: signal.review_bucket))


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourcePrimaryAuthorityDisagreementSlaRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourcePrimaryAuthorityDisagreementSlaRow:
            raise ValueError(
                "rows must contain ResearchSourcePrimaryAuthorityDisagreementSlaRow",
            )
        require_paper_only_flags("row", row)
        if row.review_bucket in seen:
            raise ValueError("rows must be unique by review_bucket")
        seen.add(row.review_bucket)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount",
            )
        require_paper_only_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique by reason_code")
        seen.add(item.reason_code)
    expected_order = tuple(reason for reason in REPORT_REASON_CODES if reason in seen)
    if tuple(item.reason_code for item in counts) != expected_order:
        raise ValueError("reason_code_counts must be deterministic")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason for reason in allowed if reason in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _row_sort_key(
    row: ResearchSourcePrimaryAuthorityDisagreementSlaRow,
) -> tuple[int, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        row.resolution_readiness_score,
        row.review_bucket,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchSourcePrimaryAuthorityDisagreementSlaRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourcePrimaryAuthorityDisagreementSlaRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason
        for reason in REPORT_TRIGGER_REASON_CODES
        if any(reason in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchSourcePrimaryAuthorityDisagreementSlaRow, ...],
) -> tuple[ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in REPORT_REASON_CODES
        if reason_code in counts
    )


def _status_count(
    rows: tuple[ResearchSourcePrimaryAuthorityDisagreementSlaRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _condition_count(
    rows: tuple[ResearchSourcePrimaryAuthorityDisagreementSlaRow, ...],
    predicate: Any,
) -> Decimal:
    return _count(sum(1 for row in rows if predicate(row)))


def _reason_count(
    rows: tuple[ResearchSourcePrimaryAuthorityDisagreementSlaRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _normalize_validation_config(
    value: object,
) -> ResearchSourcePrimaryAuthorityDisagreementSlaConfig:
    if value is None:
        return ResearchSourcePrimaryAuthorityDisagreementSlaConfig()
    if type(value) is not ResearchSourcePrimaryAuthorityDisagreementSlaConfig:
        raise ValueError(
            "validation_config must be a "
            "ResearchSourcePrimaryAuthorityDisagreementSlaConfig",
        )
    return ResearchSourcePrimaryAuthorityDisagreementSlaConfig(**asdict(value))


def _validate_config(
    config: ResearchSourcePrimaryAuthorityDisagreementSlaConfig,
) -> None:
    if config.disagreement_watch_age_seconds >= config.disagreement_block_age_seconds:
        raise ValueError(
            "disagreement_block_age_seconds must exceed "
            "disagreement_watch_age_seconds",
        )
    if config.primary_authority_block_threshold >= config.primary_authority_watch_threshold:
        raise ValueError(
            "primary_authority_watch_threshold must exceed "
            "primary_authority_block_threshold",
        )
    if config.counter_authority_watch_pressure > config.counter_authority_block_pressure:
        raise ValueError(
            "counter_authority_watch_pressure must not exceed "
            "counter_authority_block_pressure",
        )


def _validate_row(
    row: ResearchSourcePrimaryAuthorityDisagreementSlaRow,
    config: ResearchSourcePrimaryAuthorityDisagreementSlaConfig,
) -> None:
    if CLEAR_REASON in row.reason_codes and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("clear reason must be exclusive")
    for block_reason, watch_reason, label in (
        (OPEN_BLOCK_REASON, OPEN_WATCH_REASON, "open disagreement"),
        (
            PRIMARY_AUTHORITY_BLOCK_REASON,
            PRIMARY_AUTHORITY_WATCH_REASON,
            "primary authority",
        ),
        (
            COUNTER_AUTHORITY_BLOCK_REASON,
            COUNTER_AUTHORITY_WATCH_REASON,
            "counter authority",
        ),
        (
            INDEPENDENT_CROSSCHECK_BLOCK_REASON,
            INDEPENDENT_CROSSCHECK_WATCH_REASON,
            "independent crosscheck",
        ),
    ):
        if block_reason in row.reason_codes and watch_reason in row.reason_codes:
            raise ValueError(f"{label} reasons are mutually exclusive")
    if row.disagreement_opened_at is None and row.disagreement_age_seconds != ZERO:
        raise ValueError(
            "disagreement_age_seconds must be zero without an open disagreement",
        )
    if row.disagreement_opened_at is None:
        if row.sla_score != ONE:
            raise ValueError("sla_score must be one without an open disagreement")
        if any(
            reason in row.reason_codes
            for reason in (OPEN_BLOCK_REASON, OPEN_WATCH_REASON)
        ):
            raise ValueError(
                "open disagreement reasons require disagreement_opened_at",
            )
    elif row.disagreement_age_seconds == ZERO and row.sla_score != ONE:
        raise ValueError("sla_score must be one at zero disagreement age")
    if (
        row.independent_crosscheck_count == ZERO
        and row.crosscheck_score != ZERO
    ):
        raise ValueError(
            "crosscheck_score must be zero when independent_crosscheck_count is zero",
        )
    has_crosscheck_block_reason = (
        INDEPENDENT_CROSSCHECK_BLOCK_REASON in row.reason_codes
    )
    if (
        row.independent_crosscheck_count == ZERO
        and not has_crosscheck_block_reason
    ) or (
        row.independent_crosscheck_count > ZERO
        and has_crosscheck_block_reason
    ):
        raise ValueError("independent crosscheck reason_codes must match count")
    expected_sla_score = _sla_score(
        disagreement_age_seconds=row.disagreement_age_seconds,
        disagreement_opened=row.disagreement_opened_at is not None,
        config=config,
    )
    if row.sla_score != expected_sla_score:
        raise ValueError("sla_score must match disagreement age")
    expected_crosscheck_score = _bounded_ratio(
        row.independent_crosscheck_count,
        config.minimum_independent_crosscheck_count,
    )
    if row.crosscheck_score != expected_crosscheck_score:
        raise ValueError(
            "crosscheck_score must match independent_crosscheck_count",
        )
    expected_reason_codes = _row_reason_codes(
        disagreement_opened_at=row.disagreement_opened_at,
        primary_authority_score=row.primary_authority_score,
        counter_authority_pressure_score=row.counter_authority_pressure_score,
        independent_crosscheck_count=row.independent_crosscheck_count,
        disagreement_age_seconds=row.disagreement_age_seconds,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must use clear reason")
    if row.status != "pass" and row.reason_codes == (CLEAR_REASON,):
        raise ValueError("watch or block rows must not use clear reason")
    expected_readiness_score = _resolution_readiness_score(
        primary_authority_score=row.primary_authority_score,
        counter_authority_pressure_score=row.counter_authority_pressure_score,
        sla_score=row.sla_score,
        crosscheck_score=row.crosscheck_score,
    )
    if row.resolution_readiness_score != expected_readiness_score:
        raise ValueError("resolution_readiness_score must match component scores")


def _validate_report(
    report: ResearchSourcePrimaryAuthorityDisagreementSlaReport,
    config: ResearchSourcePrimaryAuthorityDisagreementSlaConfig,
) -> None:
    for row in report.rows:
        _validate_row(row, config)
        if row.disagreement_opened_at is None:
            continue
        if row.disagreement_opened_at > report.generated_at:
            raise ValueError("disagreement_opened_at must not be after generated_at")
        if row.disagreement_age_seconds != _duration_seconds(
            row.disagreement_opened_at,
            report.generated_at,
        ):
            raise ValueError(
                "disagreement_age_seconds must match disagreement_opened_at",
            )
    if report.review_bucket_count != _count(len(report.rows)):
        raise ValueError("review_bucket_count must match rows")
    expected_values = {
        "open_disagreement_count": _condition_count(
            report.rows,
            lambda row: row.disagreement_opened_at is not None,
        ),
        "pass_count": _status_count(report.rows, "pass"),
        "watch_count": _status_count(report.rows, "watch"),
        "block_count": _status_count(report.rows, "block"),
        "overdue_disagreement_count": _reason_count(report.rows, (OPEN_BLOCK_REASON,)),
        "weak_primary_authority_count": _reason_count(
            report.rows,
            (PRIMARY_AUTHORITY_WATCH_REASON, PRIMARY_AUTHORITY_BLOCK_REASON),
        ),
        "counter_authority_pressure_count": _reason_count(
            report.rows,
            (COUNTER_AUTHORITY_WATCH_REASON, COUNTER_AUTHORITY_BLOCK_REASON),
        ),
        "low_independent_crosscheck_count": _reason_count(
            report.rows,
            (INDEPENDENT_CROSSCHECK_WATCH_REASON, INDEPENDENT_CROSSCHECK_BLOCK_REASON),
        ),
        "lowest_resolution_readiness_score": min(
            (row.resolution_readiness_score for row in report.rows),
            default=ZERO,
        ),
        "highest_disagreement_age_seconds": max(
            (row.disagreement_age_seconds for row in report.rows),
            default=ZERO,
        ),
        "highest_counter_authority_pressure_score": max(
            (row.counter_authority_pressure_score for row in report.rows),
            default=ZERO,
        ),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")


def _require_or_set_digest(
    report: ResearchSourcePrimaryAuthorityDisagreementSlaReport,
) -> None:
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
    report: ResearchSourcePrimaryAuthorityDisagreementSlaReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_public_payload(payload)
    return _canonical_digest(payload)


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


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
    if isinstance(value, datetime):
        return _as_utc("JSON datetime value", value).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (float, int)):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, str):
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


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _reject_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError("public payload contains unsafe key")
            _reject_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(item)
        return
    if type(value) in (int, float):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError("public payload contains unsafe value")


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    started_at_utc = _as_utc("started_at", started_at)
    finished_at_utc = _as_utc("finished_at", finished_at)
    if finished_at_utc < started_at_utc:
        raise ValueError("duration seconds must be nonnegative")
    delta = finished_at_utc - started_at_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _quantize(seconds)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return _quantize(Decimal(value))


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    _reject_fractional_whole_decimal(field_name, value)
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    _reject_fractional_whole_decimal(field_name, value)
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_nonnegative_whole_or_scaled_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc


def _reject_fractional_whole_decimal(field_name: str, value: object) -> None:
    if (
        type(value) is Decimal
        and value.is_finite()
        and value != value.to_integral_value()
    ):
        raise ValueError(f"{field_name} must be a whole Decimal")


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_PRIMARY_AUTHORITY_DISAGREEMENT_SLA_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _require_public_bucket(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")
    if not all(char.isalnum() or char in (".", "_", "-") for char in value):
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


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_PRIMARY_AUTHORITY_DISAGREEMENT_SLA_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_PRIMARY_AUTHORITY_DISAGREEMENT_SLA_STATUSES",
    "ResearchSourcePrimaryAuthorityDisagreementSlaConfig",
    "ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount",
    "ResearchSourcePrimaryAuthorityDisagreementSlaReport",
    "ResearchSourcePrimaryAuthorityDisagreementSlaRow",
    "ResearchSourcePrimaryAuthorityDisagreementSlaSignal",
    "build_research_source_primary_authority_disagreement_sla_report",
    "research_source_primary_authority_disagreement_sla_report_digest",
    "research_source_primary_authority_disagreement_sla_report_payload",
    "validate_research_source_primary_authority_disagreement_sla_public_payload",
    "validate_research_source_primary_authority_disagreement_sla_report_digest",
)
