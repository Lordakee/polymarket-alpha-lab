"""Pure report-only team source authority resolution floor reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_AUTHORITY_RESOLUTION_FLOOR_REPORT_CONFIG_VERSION = (
    "research-strategy-team-source-authority-resolution-floor-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
TEAM_SOURCE_AUTHORITY_RESOLUTION_FLOOR_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

NO_INPUTS_REASON = "no_team_source_authority_resolution_floor_inputs"
PASS_REASON = "team_source_authority_resolution_floor_pass"
WATCH_REASON = "team_source_authority_resolution_floor_watch"
BLOCK_REASON = "team_source_authority_resolution_floor_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    BLOCK_REASON,
    "authority_score_block",
    "resolution_alignment_score_block",
    "authority_quorum_count_block",
    "resolution_latency_block",
    "resolution_floor_score_block",
    WATCH_REASON,
    "authority_score_watch",
    "resolution_alignment_score_watch",
    "authority_quorum_count_watch",
    "resolution_latency_watch",
    PASS_REASON,
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

TOP_LEVEL_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_resolution_floor_score",
        "min_authority_score",
        "min_resolution_alignment_score",
        "min_authority_quorum_count",
        "max_resolution_latency_seconds",
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
        "item_digest",
        "public_team_bucket",
        "authority_score",
        "authority_gap_score",
        "resolution_alignment_score",
        "resolution_gap_score",
        "authority_quorum_count",
        "authority_quorum_score",
        "resolution_latency_seconds",
        "latency_score",
        "resolution_floor_score",
        "observed_at",
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
UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "candidate-id",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "market_question",
    "market-question",
    "source_url",
    "source-url",
    "source_text",
    "source-text",
    "raw_url",
    "raw-url",
    "raw_text",
    "raw-text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order_id",
    "order-id",
    "trade_id",
    "trade-id",
    "position_size",
    "position-size",
    "recommendation",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "candidate://",
    "market_id",
    "market_slug",
    "market_question",
    "source_url",
    "source_text",
    "raw text",
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
    "order_id",
    "order-id",
    "trade_id",
    "trade-id",
    "position_size",
    "position-size",
    "recommendation",
    "private_",
    "secret",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_AUTHORITY_RESOLUTION_FLOOR_REPORT_CONFIG_VERSION",
    "TEAM_SOURCE_AUTHORITY_RESOLUTION_FLOOR_STATUSES",
    "ResearchStrategyTeamSourceAuthorityResolutionFloorConfig",
    "ResearchStrategyTeamSourceAuthorityResolutionFloorInput",
    "ResearchStrategyTeamSourceAuthorityResolutionFloorReasonCodeCount",
    "ResearchStrategyTeamSourceAuthorityResolutionFloorReport",
    "ResearchStrategyTeamSourceAuthorityResolutionFloorRow",
    "build_research_strategy_team_source_authority_resolution_floor_report",
    "research_strategy_team_source_authority_resolution_floor_report_digest",
    "research_strategy_team_source_authority_resolution_floor_report_payload",
    "validate_research_strategy_team_source_authority_resolution_floor_report_payload",
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
class ResearchStrategyTeamSourceAuthorityResolutionFloorConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_AUTHORITY_RESOLUTION_FLOOR_REPORT_CONFIG_VERSION
    )
    min_pass_authority_score: Decimal = Decimal("0.800000")
    min_watch_authority_score: Decimal = Decimal("0.600000")
    min_pass_resolution_alignment_score: Decimal = Decimal("0.750000")
    min_watch_resolution_alignment_score: Decimal = Decimal("0.550000")
    min_pass_authority_quorum_count: Decimal = Decimal("2.000000")
    min_watch_authority_quorum_count: Decimal = Decimal("1.000000")
    max_pass_resolution_latency_seconds: Decimal = Decimal("86400.000000")
    max_watch_resolution_latency_seconds: Decimal = Decimal("259200.000000")
    pass_min_resolution_floor_score: Decimal = Decimal("0.800000")
    watch_min_resolution_floor_score: Decimal = Decimal("0.550000")
    authority_weight: Decimal = Decimal("0.350000")
    resolution_alignment_weight: Decimal = Decimal("0.300000")
    authority_quorum_weight: Decimal = Decimal("0.200000")
    latency_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSourceAuthorityResolutionFloorConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_AUTHORITY_RESOLUTION_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_authority_score",
            "min_watch_authority_score",
            "min_pass_resolution_alignment_score",
            "min_watch_resolution_alignment_score",
            "pass_min_resolution_floor_score",
            "watch_min_resolution_floor_score",
            "authority_weight",
            "resolution_alignment_weight",
            "authority_quorum_weight",
            "latency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_authority_quorum_count",
            "min_watch_authority_quorum_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_resolution_latency_seconds",
            "max_watch_resolution_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload(_json_ready(self), label="config")


@dataclass(frozen=True)
class ResearchStrategyTeamSourceAuthorityResolutionFloorInput(_FinalPublicDataclass):
    private_reference: str
    public_team_bucket: str
    authority_score: Decimal
    resolution_alignment_score: Decimal
    authority_quorum_count: Decimal
    resolution_latency_seconds: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSourceAuthorityResolutionFloorInput,
            "input",
        )
        object.__setattr__(
            self,
            "private_reference",
            _require_private_reference("private_reference", self.private_reference),
        )
        object.__setattr__(
            self,
            "public_team_bucket",
            _require_public_identifier("public_team_bucket", self.public_team_bucket),
        )
        _reject_unsafe_public_string("public_team_bucket", self.public_team_bucket)
        for field_name in ("authority_score", "resolution_alignment_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "authority_quorum_count",
            _require_nonnegative_whole_decimal(
                "authority_quorum_count",
                self.authority_quorum_count,
            ),
        )
        object.__setattr__(
            self,
            "resolution_latency_seconds",
            _require_nonnegative_decimal(
                "resolution_latency_seconds",
                self.resolution_latency_seconds,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyTeamSourceAuthorityResolutionFloorRow(_FinalPublicDataclass):
    item_digest: str
    public_team_bucket: str
    authority_score: Decimal
    authority_gap_score: Decimal
    resolution_alignment_score: Decimal
    resolution_gap_score: Decimal
    authority_quorum_count: Decimal
    authority_quorum_score: Decimal
    resolution_latency_seconds: Decimal
    latency_score: Decimal
    resolution_floor_score: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyTeamSourceAuthorityResolutionFloorConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: (
            ResearchStrategyTeamSourceAuthorityResolutionFloorConfig | None
        ),
    ) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSourceAuthorityResolutionFloorRow,
            "row",
        )
        object.__setattr__(
            self,
            "item_digest",
            _require_private_digest("item_digest", self.item_digest),
        )
        object.__setattr__(
            self,
            "public_team_bucket",
            _require_public_identifier("public_team_bucket", self.public_team_bucket),
        )
        _reject_unsafe_public_string("public_team_bucket", self.public_team_bucket)
        for field_name in (
            "authority_score",
            "authority_gap_score",
            "resolution_alignment_score",
            "resolution_gap_score",
            "authority_quorum_score",
            "latency_score",
            "resolution_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "authority_quorum_count",
            _require_nonnegative_whole_decimal(
                "authority_quorum_count",
                self.authority_quorum_count,
            ),
        )
        object.__setattr__(
            self,
            "resolution_latency_seconds",
            _require_nonnegative_decimal(
                "resolution_latency_seconds",
                self.resolution_latency_seconds,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, validation_config or _default_config())
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload(_json_ready(self), label="row")


@dataclass(frozen=True)
class ResearchStrategyTeamSourceAuthorityResolutionFloorReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSourceAuthorityResolutionFloorReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload(_json_ready(self), label="reason_code_count")


@dataclass(frozen=True)
class ResearchStrategyTeamSourceAuthorityResolutionFloorReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_resolution_floor_score: Decimal | None
    min_authority_score: Decimal
    min_resolution_alignment_score: Decimal
    min_authority_quorum_count: Decimal
    max_resolution_latency_seconds: Decimal
    rows: tuple[ResearchStrategyTeamSourceAuthorityResolutionFloorRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyTeamSourceAuthorityResolutionFloorReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSourceAuthorityResolutionFloorReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_AUTHORITY_RESOLUTION_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_resolution_floor_score",
            _require_optional_ratio_decimal(
                "average_resolution_floor_score",
                self.average_resolution_floor_score,
            ),
        )
        for field_name in (
            "min_authority_score",
            "min_resolution_alignment_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_authority_quorum_count",
            _require_nonnegative_whole_decimal(
                "min_authority_quorum_count",
                self.min_authority_quorum_count,
            ),
        )
        object.__setattr__(
            self,
            "max_resolution_latency_seconds",
            _require_nonnegative_decimal(
                "max_resolution_latency_seconds",
                self.max_resolution_latency_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _reject_unsafe_public_payload(_json_ready(self), label="report")

    @property
    def payload(self) -> Mapping[str, Any]:
        return research_strategy_team_source_authority_resolution_floor_report_payload(
            self,
        )


def build_research_strategy_team_source_authority_resolution_floor_report(
    inputs: Iterable[object],
    *,
    config: ResearchStrategyTeamSourceAuthorityResolutionFloorConfig,
    generated_at: datetime,
) -> ResearchStrategyTeamSourceAuthorityResolutionFloorReport:
    if type(config) is not ResearchStrategyTeamSourceAuthorityResolutionFloorConfig:
        raise ValueError(
            "config must be a ResearchStrategyTeamSourceAuthorityResolutionFloorConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    for item in input_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must be at or before generated_at")
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in input_items),
            key=_row_sort_key,
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchStrategyTeamSourceAuthorityResolutionFloorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_summary_status(rows),
        row_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, STATUS_PASS)),
        watch_count=_decimal_count(_status_count(rows, STATUS_WATCH)),
        block_count=_decimal_count(_status_count(rows, STATUS_BLOCK)),
        average_resolution_floor_score=_average_row_value(
            rows,
            "resolution_floor_score",
        ),
        min_authority_score=_minimum_row_value(rows, "authority_score"),
        min_resolution_alignment_score=_minimum_row_value(
            rows,
            "resolution_alignment_score",
        ),
        min_authority_quorum_count=_minimum_row_value(rows, "authority_quorum_count"),
        max_resolution_latency_seconds=_maximum_row_value(
            rows,
            "resolution_latency_seconds",
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=reason_codes,
    )


def research_strategy_team_source_authority_resolution_floor_report_payload(
    report: (
        ResearchStrategyTeamSourceAuthorityResolutionFloorReport | Mapping[str, Any]
    ),
) -> Mapping[str, Any]:
    if type(report) is ResearchStrategyTeamSourceAuthorityResolutionFloorReport:
        _require_hard_flags("report", report)
        if report.derived_validation_digest != _report_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _payload_value(report)
    elif isinstance(report, Mapping):
        payload = _plain_json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyTeamSourceAuthorityResolutionFloorReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload, label="payload")
    _reject_raw_public_numbers("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_schema(payload)
    _validate_payload_digest(payload)
    return _freeze_json_value(payload)


def research_strategy_team_source_authority_resolution_floor_report_digest(
    report: ResearchStrategyTeamSourceAuthorityResolutionFloorReport,
) -> str:
    if type(report) is not ResearchStrategyTeamSourceAuthorityResolutionFloorReport:
        raise ValueError(
            "report must be a ResearchStrategyTeamSourceAuthorityResolutionFloorReport",
        )
    return _report_digest(report)


def validate_research_strategy_team_source_authority_resolution_floor_report_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, Mapping):
        return False
    try:
        research_strategy_team_source_authority_resolution_floor_report_payload(payload)
    except (TypeError, ValueError):
        return False
    return True


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _default_config() -> ResearchStrategyTeamSourceAuthorityResolutionFloorConfig:
    return ResearchStrategyTeamSourceAuthorityResolutionFloorConfig()


def _validate_config(
    config: ResearchStrategyTeamSourceAuthorityResolutionFloorConfig,
) -> None:
    if config.min_pass_authority_score < config.min_watch_authority_score:
        raise ValueError("min_pass_authority_score must be at least watch threshold")
    if (
        config.min_pass_resolution_alignment_score
        < config.min_watch_resolution_alignment_score
    ):
        raise ValueError(
            "min_pass_resolution_alignment_score must be at least watch threshold",
        )
    if config.min_pass_authority_quorum_count < config.min_watch_authority_quorum_count:
        raise ValueError(
            "min_pass_authority_quorum_count must be at least watch threshold",
        )
    if (
        config.max_pass_resolution_latency_seconds
        > config.max_watch_resolution_latency_seconds
    ):
        raise ValueError(
            "max_pass_resolution_latency_seconds must not exceed watch threshold",
        )
    if config.pass_min_resolution_floor_score < config.watch_min_resolution_floor_score:
        raise ValueError(
            "pass_min_resolution_floor_score must be at least watch threshold",
        )
    weight_sum = _quantize(
        config.authority_weight
        + config.resolution_alignment_weight
        + config.authority_quorum_weight
        + config.latency_weight,
    )
    if weight_sum != ONE:
        raise ValueError("resolution floor weights must sum to one")


def _row_from_input(
    item: ResearchStrategyTeamSourceAuthorityResolutionFloorInput,
    *,
    config: ResearchStrategyTeamSourceAuthorityResolutionFloorConfig,
) -> ResearchStrategyTeamSourceAuthorityResolutionFloorRow:
    quorum_score = _authority_quorum_score(item.authority_quorum_count, config)
    latency_score = _latency_score(item.resolution_latency_seconds, config)
    floor_score = _resolution_floor_score(
        authority_score=item.authority_score,
        resolution_alignment_score=item.resolution_alignment_score,
        authority_quorum_score=quorum_score,
        latency_score=latency_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        item=item,
        floor_score=floor_score,
        config=config,
    )
    return ResearchStrategyTeamSourceAuthorityResolutionFloorRow(
        item_digest=_digest_private_reference(item.private_reference),
        public_team_bucket=item.public_team_bucket,
        authority_score=item.authority_score,
        authority_gap_score=_quantize(ONE - item.authority_score),
        resolution_alignment_score=item.resolution_alignment_score,
        resolution_gap_score=_quantize(ONE - item.resolution_alignment_score),
        authority_quorum_count=item.authority_quorum_count,
        authority_quorum_score=quorum_score,
        resolution_latency_seconds=item.resolution_latency_seconds,
        latency_score=latency_score,
        resolution_floor_score=floor_score,
        observed_at=item.observed_at,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    item: ResearchStrategyTeamSourceAuthorityResolutionFloorInput,
    floor_score: Decimal,
    config: ResearchStrategyTeamSourceAuthorityResolutionFloorConfig,
) -> tuple[str, ...]:
    condition_codes: list[str] = []
    if item.authority_score < config.min_watch_authority_score:
        condition_codes.append("authority_score_block")
    elif item.authority_score < config.min_pass_authority_score:
        condition_codes.append("authority_score_watch")

    if item.resolution_alignment_score < config.min_watch_resolution_alignment_score:
        condition_codes.append("resolution_alignment_score_block")
    elif item.resolution_alignment_score < config.min_pass_resolution_alignment_score:
        condition_codes.append("resolution_alignment_score_watch")

    if item.authority_quorum_count < config.min_watch_authority_quorum_count:
        condition_codes.append("authority_quorum_count_block")
    elif item.authority_quorum_count < config.min_pass_authority_quorum_count:
        condition_codes.append("authority_quorum_count_watch")

    if item.resolution_latency_seconds > config.max_watch_resolution_latency_seconds:
        condition_codes.append("resolution_latency_block")
    elif item.resolution_latency_seconds > config.max_pass_resolution_latency_seconds:
        condition_codes.append("resolution_latency_watch")

    if floor_score < config.watch_min_resolution_floor_score:
        condition_codes.append("resolution_floor_score_block")

    if any(code.endswith("_block") for code in condition_codes):
        status_reason = BLOCK_REASON
    elif condition_codes:
        status_reason = WATCH_REASON
    else:
        status_reason = PASS_REASON

    input_codes = tuple(f"input_{code}" for code in item.reason_codes)
    return (status_reason, *condition_codes, *input_codes)


def _validate_row(
    row: ResearchStrategyTeamSourceAuthorityResolutionFloorRow,
    config: ResearchStrategyTeamSourceAuthorityResolutionFloorConfig,
) -> None:
    if row.authority_gap_score != _quantize(ONE - row.authority_score):
        raise ValueError("authority_gap_score does not match authority_score")
    if row.resolution_gap_score != _quantize(ONE - row.resolution_alignment_score):
        raise ValueError(
            "resolution_gap_score does not match resolution_alignment_score",
        )
    if row.authority_quorum_score != _authority_quorum_score(
        row.authority_quorum_count,
        config,
    ):
        raise ValueError("authority_quorum_score does not match authority_quorum_count")
    if row.latency_score != _latency_score(row.resolution_latency_seconds, config):
        raise ValueError("latency_score does not match resolution_latency_seconds")
    expected_floor_score = _resolution_floor_score(
        authority_score=row.authority_score,
        resolution_alignment_score=row.resolution_alignment_score,
        authority_quorum_score=row.authority_quorum_score,
        latency_score=row.latency_score,
        config=config,
    )
    if row.resolution_floor_score != expected_floor_score:
        raise ValueError("resolution_floor_score does not match row inputs")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status does not match row reason codes")


def _validate_report(
    report: ResearchStrategyTeamSourceAuthorityResolutionFloorReport,
) -> None:
    rows = report.rows
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count does not match rows")
    if report.pass_count != _decimal_count(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _decimal_count(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _decimal_count(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count does not match rows")
    if report.status != _summary_status(rows):
        raise ValueError("status does not match rows")
    if report.average_resolution_floor_score != _average_row_value(
        rows,
        "resolution_floor_score",
    ):
        raise ValueError("average_resolution_floor_score does not match rows")
    if report.min_authority_score != _minimum_row_value(rows, "authority_score"):
        raise ValueError("min_authority_score does not match rows")
    if report.min_resolution_alignment_score != _minimum_row_value(
        rows,
        "resolution_alignment_score",
    ):
        raise ValueError("min_resolution_alignment_score does not match rows")
    if report.min_authority_quorum_count != _minimum_row_value(
        rows,
        "authority_quorum_count",
    ):
        raise ValueError("min_authority_quorum_count does not match rows")
    if report.max_resolution_latency_seconds != _maximum_row_value(
        rows,
        "resolution_latency_seconds",
    ):
        raise ValueError("max_resolution_latency_seconds does not match rows")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes do not match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts do not match rows")


def _authority_quorum_score(
    count: Decimal,
    config: ResearchStrategyTeamSourceAuthorityResolutionFloorConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        ratio = count / config.min_pass_authority_quorum_count
    if ratio > ONE:
        return ONE
    return _quantize(ratio)


def _latency_score(
    seconds: Decimal,
    config: ResearchStrategyTeamSourceAuthorityResolutionFloorConfig,
) -> Decimal:
    if seconds >= config.max_watch_resolution_latency_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        score = ONE - (seconds / config.max_watch_resolution_latency_seconds)
    if score < ZERO:
        return ZERO
    if score > ONE:
        return ONE
    return _quantize(score)


def _resolution_floor_score(
    *,
    authority_score: Decimal,
    resolution_alignment_score: Decimal,
    authority_quorum_score: Decimal,
    latency_score: Decimal,
    config: ResearchStrategyTeamSourceAuthorityResolutionFloorConfig,
) -> Decimal:
    return _quantize(
        authority_score * config.authority_weight
        + resolution_alignment_score * config.resolution_alignment_weight
        + authority_quorum_score * config.authority_quorum_weight
        + latency_score * config.latency_weight,
    )


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchStrategyTeamSourceAuthorityResolutionFloorInput, ...]:
    if isinstance(inputs, (str, bytes, Mapping)):
        raise ValueError("inputs must be an iterable of input rows")
    items = tuple(inputs)
    for item in items:
        if type(item) is not ResearchStrategyTeamSourceAuthorityResolutionFloorInput:
            raise ValueError(
                "inputs must contain ResearchStrategyTeamSourceAuthorityResolutionFloorInput",
            )
        _require_hard_flags("input", item)
    return items


def _normalize_rows(
    rows: tuple[ResearchStrategyTeamSourceAuthorityResolutionFloorRow, ...],
) -> tuple[ResearchStrategyTeamSourceAuthorityResolutionFloorRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyTeamSourceAuthorityResolutionFloorRow:
            raise ValueError(
                "rows must contain ResearchStrategyTeamSourceAuthorityResolutionFloorRow",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        ResearchStrategyTeamSourceAuthorityResolutionFloorReasonCodeCount,
        ...,
    ],
) -> tuple[ResearchStrategyTeamSourceAuthorityResolutionFloorReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in reason_code_counts:
        if (
            type(item)
            is not ResearchStrategyTeamSourceAuthorityResolutionFloorReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyTeamSourceAuthorityResolutionFloorReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
    return reason_code_counts


def _normalize_input_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for code in reason_codes:
        ready = _require_reason_code("reason_codes", code)
        if ready.startswith("input_"):
            raise ValueError("reason_codes must not use the input_ prefix")
        if ready not in seen:
            normalized.append(ready)
            seen.add(ready)
    return tuple(sorted(normalized))


def _normalize_row_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple or not reason_codes:
        raise ValueError("reason_codes must be a non-empty tuple")
    return tuple(_require_reason_code("reason_codes", code) for code in reason_codes)


def _normalize_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple or not reason_codes:
        raise ValueError("reason_codes must be a non-empty tuple")
    return tuple(_require_reason_code("reason_codes", code) for code in reason_codes)


def _summary_status(
    rows: tuple[ResearchStrategyTeamSourceAuthorityResolutionFloorRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return STATUS_BLOCK
    if any(code.endswith("_watch") for code in reason_codes):
        return STATUS_WATCH
    if reason_codes and reason_codes[0] == BLOCK_REASON:
        return STATUS_BLOCK
    if reason_codes and reason_codes[0] == WATCH_REASON:
        return STATUS_WATCH
    return STATUS_PASS


def _summary_reason_codes(
    rows: tuple[ResearchStrategyTeamSourceAuthorityResolutionFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    row_codes = {
        code
        for row in rows
        for code in row.reason_codes
        if not code.startswith("input_")
    }
    return tuple(code for code in REASON_CODE_SEQUENCE if code in row_codes)


def _reason_code_counts(
    rows: tuple[ResearchStrategyTeamSourceAuthorityResolutionFloorRow, ...],
) -> tuple[ResearchStrategyTeamSourceAuthorityResolutionFloorReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyTeamSourceAuthorityResolutionFloorReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    ordered_codes = tuple(code for code in REASON_CODE_SEQUENCE if code in counter)
    extra_codes = tuple(sorted(code for code in counter if code not in ordered_codes))
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchStrategyTeamSourceAuthorityResolutionFloorReasonCodeCount(
            reason_code=code,
            count=_decimal_count(counter[code]),
            row_ratio=_ratio(_decimal_count(counter[code]), row_count),
        )
        for code in (*ordered_codes, *extra_codes)
    )


def _status_count(
    rows: tuple[ResearchStrategyTeamSourceAuthorityResolutionFloorRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(
    row: ResearchStrategyTeamSourceAuthorityResolutionFloorRow,
) -> tuple[int, str, str]:
    return (STATUS_RANK[row.status], row.public_team_bucket, row.item_digest)


def _average_row_value(
    rows: tuple[ResearchStrategyTeamSourceAuthorityResolutionFloorRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(getattr(row, field_name) for row in rows) / Decimal(len(rows)))


def _minimum_row_value(
    rows: tuple[ResearchStrategyTeamSourceAuthorityResolutionFloorRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _maximum_row_value(
    rows: tuple[ResearchStrategyTeamSourceAuthorityResolutionFloorRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_optional_ratio_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() == "":
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not PRIVATE_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a private sha256 digest")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be reason codes")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in TEAM_SOURCE_AUTHORITY_RESOLUTION_FLOOR_STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _digest_private_reference(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _report_digest(
    report: ResearchStrategyTeamSourceAuthorityResolutionFloorReport,
) -> str:
    payload = _payload_value(report)
    payload.pop("derived_validation_digest", None)
    return _digest_payload(payload)


def _payload_digest(payload: Mapping[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return _digest_payload(unsigned)


def _digest_payload(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: Mapping[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    expected_digest = _payload_digest(payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _payload_value(value: object) -> dict[str, Any]:
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _json_ready(value: object) -> Any:
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal|string")
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _plain_json_ready(value: object) -> Any:
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if type(value) in (int, float) or isinstance(value, Decimal):
        raise ValueError("public payload numeric values must be Decimal|string")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _plain_json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_plain_json_ready(item) for item in value]
    raise ValueError("public payload value is not JSON serializable")


def _validate_payload_schema(payload: Mapping[str, Any]) -> None:
    _require_exact_keys("payload", payload, TOP_LEVEL_PAYLOAD_FIELDS)
    _require_status("status", payload["status"])
    _require_payload_string("generated_at", payload["generated_at"])
    _require_public_identifier("config_version", payload["config_version"])
    for field_name in (
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "min_authority_score",
        "min_resolution_alignment_score",
        "min_authority_quorum_count",
        "max_resolution_latency_seconds",
    ):
        _require_payload_string(field_name, payload[field_name])
    average = payload["average_resolution_floor_score"]
    if average is not None:
        _require_payload_string("average_resolution_floor_score", average)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        _validate_row_payload_schema(row)
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for item in reason_code_counts:
        if type(item) is not dict:
            raise ValueError("reason_code_counts must contain JSON objects")
        _validate_reason_count_payload_schema(item)
    reason_codes = payload["reason_codes"]
    if type(reason_codes) is not list:
        raise ValueError("reason_codes must be a list")
    for code in reason_codes:
        _require_reason_code("reason_codes", code)


def _validate_row_payload_schema(payload: Mapping[str, Any]) -> None:
    _require_exact_keys("row", payload, ROW_PAYLOAD_FIELDS)
    _require_private_digest("item_digest", payload["item_digest"])
    _require_public_identifier("public_team_bucket", payload["public_team_bucket"])
    for field_name in (
        "authority_score",
        "authority_gap_score",
        "resolution_alignment_score",
        "resolution_gap_score",
        "authority_quorum_count",
        "authority_quorum_score",
        "resolution_latency_seconds",
        "latency_score",
        "resolution_floor_score",
    ):
        _require_payload_string(field_name, payload[field_name])
    _require_payload_string("observed_at", payload["observed_at"])
    _require_status("status", payload["status"])
    if type(payload["reason_codes"]) is not list:
        raise ValueError("reason_codes must be a list")
    for code in payload["reason_codes"]:
        _require_reason_code("reason_codes", code)
    _require_hard_flags("row", _DictFlags(payload))


def _validate_reason_count_payload_schema(payload: Mapping[str, Any]) -> None:
    _require_exact_keys("reason_code_count", payload, REASON_COUNT_PAYLOAD_FIELDS)
    _require_reason_code("reason_code", payload["reason_code"])
    _require_payload_string("count", payload["count"])
    _require_payload_string("row_ratio", payload["row_ratio"])
    _require_hard_flags("reason_code_count", _DictFlags(payload))


def _require_exact_keys(
    label: str,
    payload: Mapping[str, Any],
    expected: frozenset[str],
) -> None:
    keys = set(payload)
    if keys != expected:
        raise ValueError(f"{label} payload fields are not supported")


def _require_payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal|string payload value")
    return value


def _reject_unsafe_public_payload(value: object, *, label: str) -> None:
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(item, label=label)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item, label=label)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


def _reject_raw_public_numbers(label: str, value: object) -> None:
    if type(value) is bool or value is None:
        return
    if isinstance(value, Decimal) or type(value) in (int, float):
        raise ValueError(f"{label} numeric values must be Decimal|string")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_raw_public_numbers(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_raw_public_numbers(label, item)


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: Mapping[str, Any]) -> None:
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


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return FrozenJsonObject(
            {key: _freeze_json_value(item) for key, item in value.items()},
        )
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value
