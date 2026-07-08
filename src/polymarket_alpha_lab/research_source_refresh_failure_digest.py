"""Pure report-only digest for research source refresh failures."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_SOURCE_REFRESH_FAILURE_DIGEST_CONFIG_VERSION = (
    "research-source-refresh-failure-digest-v0"
)

STATUSES = ("pass", "watch", "block")
NO_INPUTS_REASON = "refresh_failure_digest_no_inputs"
PASS_REASON = "refresh_failure_digest_pass"
WATCH_FAILURE_VOLUME_REASON = "refresh_failure_digest_watch_failure_volume"
WATCH_FAILURE_AGE_REASON = "refresh_failure_digest_watch_failure_age"
WATCH_STALE_SUCCESS_REASON = "refresh_failure_digest_watch_stale_success"
BLOCK_FAILURE_AGE_REASON = "refresh_failure_digest_block_failure_age"
BLOCK_FAILURE_VOLUME_REASON = "refresh_failure_digest_block_failure_volume"
BLOCK_HARD_FAILURE_KIND_REASON = "refresh_failure_digest_block_hard_failure_kind"
BLOCK_NEVER_SUCCEEDED_REASON = "refresh_failure_digest_block_never_succeeded"
BLOCK_STALE_SUCCESS_REASON = "refresh_failure_digest_block_stale_success"
REPORT_REASON_CODE_SEQUENCE = (
    BLOCK_FAILURE_AGE_REASON,
    BLOCK_FAILURE_VOLUME_REASON,
    BLOCK_HARD_FAILURE_KIND_REASON,
    BLOCK_NEVER_SUCCEEDED_REASON,
    BLOCK_STALE_SUCCESS_REASON,
    NO_INPUTS_REASON,
    PASS_REASON,
    WATCH_FAILURE_AGE_REASON,
    WATCH_FAILURE_VOLUME_REASON,
    WATCH_STALE_SUCCESS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    BLOCK_FAILURE_AGE_REASON,
    BLOCK_FAILURE_VOLUME_REASON,
    BLOCK_HARD_FAILURE_KIND_REASON,
    BLOCK_NEVER_SUCCEEDED_REASON,
    BLOCK_STALE_SUCCESS_REASON,
    PASS_REASON,
    WATCH_FAILURE_AGE_REASON,
    WATCH_FAILURE_VOLUME_REASON,
    WATCH_STALE_SUCCESS_REASON,
)
HARD_FAILURE_KINDS = frozenset(
    (
        "schema_mismatch",
        "source_contract_changed",
        "forbidden_response",
    ),
)
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_MINUTE = Decimal("60000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("can", "didate"),
        _join_parts("candidate", "_id"),
        _join_parts("mar", "ket_id"),
        _join_parts("mar", "ket_slug"),
        _join_parts("slug"),
        _join_parts("ques", "tion"),
        _join_parts("source", "_ref"),
        _join_parts("source", "_url"),
        _join_parts("source", "_text"),
        _join_parts("http"),
        _join_parts("://"),
        _join_parts("dsn"),
        _join_parts("tab", "le"),
        _join_parts("tok", "en"),
        _join_parts("sec", "ret"),
        _join_parts("pri", "vate"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("pos", "ition"),
        _join_parts("buy"),
        _join_parts("sell"),
        _join_parts("recom", "mend"),
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("acc", "ount"),
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_REFRESH_FAILURE_DIGEST_CONFIG_VERSION",
    "ResearchSourceRefreshFailureDigestConfig",
    "ResearchSourceRefreshFailureDigestInputRow",
    "ResearchSourceRefreshFailureDigestReasonCodeCount",
    "ResearchSourceRefreshFailureDigestReport",
    "ResearchSourceRefreshFailureDigestRow",
    "build_research_source_refresh_failure_digest",
    "research_source_refresh_failure_digest_json",
)


@dataclass(frozen=True)
class ResearchSourceRefreshFailureDigestConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_REFRESH_FAILURE_DIGEST_CONFIG_VERSION
    watch_failure_count: Decimal = Decimal("2.000000")
    block_failure_count: Decimal = Decimal("4.000000")
    watch_failure_age_minutes: Decimal = Decimal("60.000000")
    block_failure_age_minutes: Decimal = Decimal("360.000000")
    stale_success_watch_minutes: Decimal = Decimal("720.000000")
    stale_success_block_minutes: Decimal = Decimal("1440.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRefreshFailureDigestConfig:
            raise TypeError(
                "ResearchSourceRefreshFailureDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRefreshFailureDigestConfig:
            raise ValueError(
                "config must be exactly ResearchSourceRefreshFailureDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_REFRESH_FAILURE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config_version")
        object.__setattr__(
            self,
            "watch_failure_count",
            _require_positive_count_decimal(
                "watch_failure_count",
                self.watch_failure_count,
            ),
        )
        object.__setattr__(
            self,
            "block_failure_count",
            _require_positive_count_decimal(
                "block_failure_count",
                self.block_failure_count,
            ),
        )
        for field_name in (
            "watch_failure_age_minutes",
            "block_failure_age_minutes",
            "stale_success_watch_minutes",
            "stale_success_block_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_failure_count <= self.watch_failure_count:
            raise ValueError("block_failure_count must exceed watch_failure_count")
        if self.block_failure_age_minutes <= self.watch_failure_age_minutes:
            raise ValueError(
                "block_failure_age_minutes must exceed watch_failure_age_minutes",
            )
        if self.stale_success_block_minutes <= self.stale_success_watch_minutes:
            raise ValueError(
                "stale_success_block_minutes must exceed stale_success_watch_minutes",
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceRefreshFailureDigestInputRow:
    source_group: str
    source_family: str
    failure_kind: str
    first_failed_at: datetime
    last_failed_at: datetime
    last_success_at: datetime | None
    failure_count: Decimal
    consecutive_failure_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRefreshFailureDigestInputRow:
            raise TypeError(
                "ResearchSourceRefreshFailureDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRefreshFailureDigestInputRow:
            raise ValueError(
                "input row must be exactly ResearchSourceRefreshFailureDigestInputRow",
            )
        _require_public_string("source_group", self.source_group)
        _require_public_string("source_family", self.source_family)
        _require_public_string("failure_kind", self.failure_kind)
        object.__setattr__(
            self,
            "first_failed_at",
            _as_utc("first_failed_at", self.first_failed_at),
        )
        object.__setattr__(
            self,
            "last_failed_at",
            _as_utc("last_failed_at", self.last_failed_at),
        )
        object.__setattr__(
            self,
            "last_success_at",
            _optional_utc("last_success_at", self.last_success_at),
        )
        object.__setattr__(
            self,
            "failure_count",
            _require_positive_count_decimal("failure_count", self.failure_count),
        )
        object.__setattr__(
            self,
            "consecutive_failure_count",
            _require_positive_count_decimal(
                "consecutive_failure_count",
                self.consecutive_failure_count,
            ),
        )
        if self.first_failed_at > self.last_failed_at:
            raise ValueError("first_failed_at must not exceed last_failed_at")
        require_paper_only_flags("input row", self)


@dataclass(frozen=True)
class ResearchSourceRefreshFailureDigestRow:
    source_group: str
    source_family: str
    failure_kind: str
    refresh_status: str
    first_failure_age_minutes: Decimal
    failure_age_minutes: Decimal
    last_success_age_minutes: Decimal | None
    failure_count: Decimal
    consecutive_failure_count: Decimal
    retry_priority_score: Decimal
    hard_failure_kind: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRefreshFailureDigestRow:
            raise TypeError(
                "ResearchSourceRefreshFailureDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRefreshFailureDigestRow:
            raise ValueError(
                "digest row must be exactly ResearchSourceRefreshFailureDigestRow",
            )
        _require_public_string("source_group", self.source_group)
        _require_public_string("source_family", self.source_family)
        _require_public_string("failure_kind", self.failure_kind)
        _require_status("refresh_status", self.refresh_status)
        for field_name in (
            "first_failure_age_minutes",
            "failure_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "last_success_age_minutes",
            _optional_nonnegative_decimal(
                "last_success_age_minutes",
                self.last_success_age_minutes,
            ),
        )
        for field_name in ("failure_count", "consecutive_failure_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "retry_priority_score",
            _require_ratio_decimal("retry_priority_score", self.retry_priority_score),
        )
        if type(self.hard_failure_kind) is not bool:
            raise ValueError("hard_failure_kind must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_digest_row(self)
        require_paper_only_flags("digest row", self)


@dataclass(frozen=True)
class ResearchSourceRefreshFailureDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    source_group_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRefreshFailureDigestReasonCodeCount:
            raise TypeError(
                "ResearchSourceRefreshFailureDigestReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRefreshFailureDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchSourceRefreshFailureDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REPORT_REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "source_group_ratio",
            _require_ratio_decimal("source_group_ratio", self.source_group_ratio),
        )
        require_paper_only_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchSourceRefreshFailureDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    source_group_count: Decimal
    pass_source_group_count: Decimal
    watch_source_group_count: Decimal
    block_source_group_count: Decimal
    hard_failure_count: Decimal
    max_retry_priority_score: Decimal
    rows: tuple[ResearchSourceRefreshFailureDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceRefreshFailureDigestReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRefreshFailureDigestReport:
            raise TypeError(
                "ResearchSourceRefreshFailureDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRefreshFailureDigestReport:
            raise ValueError(
                "digest report must be exactly ResearchSourceRefreshFailureDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SOURCE_REFRESH_FAILURE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config_version")
        _require_status("digest_status", self.digest_status)
        for field_name in (
            "source_group_count",
            "pass_source_group_count",
            "watch_source_group_count",
            "block_source_group_count",
            "hard_failure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_retry_priority_score",
            _require_ratio_decimal(
                "max_retry_priority_score",
                self.max_retry_priority_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_digest_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_digest_report(self)
        require_paper_only_flags("digest report", self)

    @property
    def digest(self) -> dict[str, object]:
        return research_source_refresh_failure_digest_json(self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchSourceRefreshFailureDigestConfig,
    ResearchSourceRefreshFailureDigestInputRow,
    ResearchSourceRefreshFailureDigestReasonCodeCount,
    ResearchSourceRefreshFailureDigestReport,
    ResearchSourceRefreshFailureDigestRow,
)


def build_research_source_refresh_failure_digest(
    input_rows: list[ResearchSourceRefreshFailureDigestInputRow]
    | tuple[ResearchSourceRefreshFailureDigestInputRow, ...],
    *,
    config: ResearchSourceRefreshFailureDigestConfig,
    generated_at: datetime,
) -> ResearchSourceRefreshFailureDigestReport:
    if type(config) is not ResearchSourceRefreshFailureDigestConfig:
        raise ValueError(
            "config must be a ResearchSourceRefreshFailureDigestConfig",
        )
    require_paper_only_flags("config", config)
    generated = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated)
    digest_rows = _digest_rows(rows, config=config, generated_at=generated)
    reason_codes = _report_reason_codes(digest_rows)
    digest_status = _report_status(digest_rows)
    source_group_count = _decimal_count(len(digest_rows))

    return ResearchSourceRefreshFailureDigestReport(
        generated_at=generated,
        config_version=config.config_version,
        digest_status=digest_status,
        source_group_count=source_group_count,
        pass_source_group_count=_status_count(digest_rows, "pass"),
        watch_source_group_count=_status_count(digest_rows, "watch"),
        block_source_group_count=_status_count(digest_rows, "block"),
        hard_failure_count=_decimal_count(
            sum(1 for row in digest_rows if row.hard_failure_kind),
        ),
        max_retry_priority_score=max(
            (row.retry_priority_score for row in digest_rows),
            default=ZERO,
        ).quantize(QUANT),
        rows=digest_rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, digest_rows),
    )


def research_source_refresh_failure_digest_json(
    report: ResearchSourceRefreshFailureDigestReport,
) -> dict[str, object]:
    if type(report) is not ResearchSourceRefreshFailureDigestReport:
        raise ValueError(
            "report must be exactly ResearchSourceRefreshFailureDigestReport",
        )
    _require_public_json_safe_value("report", report)
    json_report = _json_ready(report)
    if type(json_report) is not dict:
        raise ValueError("report JSON must be an object")
    require_paper_only_flags("report JSON", _DictFlags(json_report))
    _reject_unsafe_json_strings("report JSON", json_report)
    return json_report


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _digest_rows(
    rows: tuple[ResearchSourceRefreshFailureDigestInputRow, ...],
    *,
    config: ResearchSourceRefreshFailureDigestConfig,
    generated_at: datetime,
) -> tuple[ResearchSourceRefreshFailureDigestRow, ...]:
    digest_rows = tuple(
        _digest_row(row, config=config, generated_at=generated_at)
        for row in sorted(
            rows,
            key=lambda item: (
                item.source_group,
                item.source_family,
                item.failure_kind,
            ),
        )
    )
    seen: set[str] = set()
    for row in digest_rows:
        if row.source_group in seen:
            raise ValueError("source_group values must be unique")
        seen.add(row.source_group)
    return digest_rows


def _digest_row(
    row: ResearchSourceRefreshFailureDigestInputRow,
    *,
    config: ResearchSourceRefreshFailureDigestConfig,
    generated_at: datetime,
) -> ResearchSourceRefreshFailureDigestRow:
    first_failure_age_minutes = _minutes_between(row.first_failed_at, generated_at)
    failure_age_minutes = _minutes_between(row.last_failed_at, generated_at)
    last_success_age_minutes = (
        None
        if row.last_success_at is None
        else _minutes_between(row.last_success_at, generated_at)
    )
    hard_failure_kind = row.failure_kind in HARD_FAILURE_KINDS
    reason_codes = _row_reason_codes(
        failure_age_minutes=failure_age_minutes,
        last_success_age_minutes=last_success_age_minutes,
        consecutive_failure_count=row.consecutive_failure_count,
        hard_failure_kind=hard_failure_kind,
        config=config,
    )
    return ResearchSourceRefreshFailureDigestRow(
        source_group=row.source_group,
        source_family=row.source_family,
        failure_kind=row.failure_kind,
        refresh_status=_row_status(reason_codes),
        first_failure_age_minutes=first_failure_age_minutes,
        failure_age_minutes=failure_age_minutes,
        last_success_age_minutes=last_success_age_minutes,
        failure_count=row.failure_count,
        consecutive_failure_count=row.consecutive_failure_count,
        retry_priority_score=_retry_priority_score(
            failure_age_minutes=failure_age_minutes,
            last_success_age_minutes=last_success_age_minutes,
            consecutive_failure_count=row.consecutive_failure_count,
            hard_failure_kind=hard_failure_kind,
            config=config,
        ),
        hard_failure_kind=hard_failure_kind,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    failure_age_minutes: Decimal,
    last_success_age_minutes: Decimal | None,
    consecutive_failure_count: Decimal,
    hard_failure_kind: bool,
    config: ResearchSourceRefreshFailureDigestConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    if failure_age_minutes >= config.block_failure_age_minutes:
        block_reasons.append(BLOCK_FAILURE_AGE_REASON)
    if consecutive_failure_count >= config.block_failure_count:
        block_reasons.append(BLOCK_FAILURE_VOLUME_REASON)
    if hard_failure_kind:
        block_reasons.append(BLOCK_HARD_FAILURE_KIND_REASON)
    if last_success_age_minutes is None:
        block_reasons.append(BLOCK_NEVER_SUCCEEDED_REASON)
    elif last_success_age_minutes >= config.stale_success_block_minutes:
        block_reasons.append(BLOCK_STALE_SUCCESS_REASON)
    if block_reasons:
        return _normalize_reason_codes(
            tuple(
                reason_code
                for reason_code in ROW_REASON_CODE_SEQUENCE
                if reason_code in set(block_reasons)
            ),
            ROW_REASON_CODE_SEQUENCE,
        )

    watch_reasons: list[str] = []
    if failure_age_minutes >= config.watch_failure_age_minutes:
        watch_reasons.append(WATCH_FAILURE_AGE_REASON)
    if consecutive_failure_count >= config.watch_failure_count:
        watch_reasons.append(WATCH_FAILURE_VOLUME_REASON)
    if (
        last_success_age_minutes is not None
        and last_success_age_minutes >= config.stale_success_watch_minutes
    ):
        watch_reasons.append(WATCH_STALE_SUCCESS_REASON)
    return _normalize_reason_codes(
        tuple(
            reason_code
            for reason_code in ROW_REASON_CODE_SEQUENCE
            if reason_code in set(watch_reasons or [PASS_REASON])
        ),
        ROW_REASON_CODE_SEQUENCE,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.startswith("refresh_failure_digest_block") for reason_code in reason_codes):
        return "block"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _report_reason_codes(
    rows: tuple[ResearchSourceRefreshFailureDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(
        reason_code
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code in seen
    )


def _report_status(rows: tuple[ResearchSourceRefreshFailureDigestRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.refresh_status == "block" for row in rows):
        return "block"
    if any(row.refresh_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceRefreshFailureDigestInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchSourceRefreshFailureDigestInputRow:
            raise ValueError("input rows must contain exact input rows")
        require_paper_only_flags("input row", row)
        if row.first_failed_at > generated_at:
            raise ValueError("first_failed_at cannot be in the future")
        if row.last_failed_at > generated_at:
            raise ValueError("last_failed_at cannot be in the future")
        if row.last_success_at is not None and row.last_success_at > generated_at:
            raise ValueError("last_success_at cannot be in the future")
    return rows


def _normalize_digest_rows(
    value: object,
) -> tuple[ResearchSourceRefreshFailureDigestRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    previous_key: tuple[str, str, str] | None = None
    for row in rows:
        if type(row) is not ResearchSourceRefreshFailureDigestRow:
            raise ValueError("rows must contain exact digest rows")
        key = (row.source_group, row.source_family, row.failure_kind)
        if row.source_group in seen:
            raise ValueError("rows must be unique")
        if previous_key is not None and previous_key > key:
            raise ValueError("rows must be sorted")
        previous_key = key
        seen.add(row.source_group)
    return rows


def _normalize_reason_codes(
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes is required")
    seen: set[str] = set()
    previous: str | None = None
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code, allowed)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        if previous is not None and allowed.index(previous) > allowed.index(reason_code):
            raise ValueError("reason_codes must be sorted")
        previous = reason_code
        seen.add(reason_code)
    return reason_codes


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourceRefreshFailureDigestReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    counts = tuple(value)
    seen: set[str] = set()
    previous: str | None = None
    for count in counts:
        if type(count) is not ResearchSourceRefreshFailureDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason code counts")
        require_paper_only_flags("reason code count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        if (
            previous is not None
            and REPORT_REASON_CODE_SEQUENCE.index(previous)
            > REPORT_REASON_CODE_SEQUENCE.index(count.reason_code)
        ):
            raise ValueError("reason_code_counts must be sorted")
        previous = count.reason_code
        seen.add(count.reason_code)
    return counts


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("JSON value must be a supported public dataclass")
        ready: dict[str, object] = {}
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{field.name} must be True")
            ready[field.name] = _json_ready(item)
        return ready
    if type(value) is Decimal:
        _require_six_decimal_json_decimal("JSON Decimal value", value)
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or value is None:
        return value
    if type(value) is str:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if isinstance(value, (list, dict, set, frozenset)):
        raise ValueError("JSON value must not be a raw collection")
    raise ValueError("value is not JSON serializable")


def _require_public_json_safe_value(field_name: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a supported public dataclass")
        require_paper_only_flags(field_name, value)
        for field in fields(value):
            try:
                item = getattr(value, field.name)
            except AttributeError as exc:
                raise ValueError(
                    f"{field_name}.{field.name} must remain constructor-valid",
                ) from exc
            _require_public_json_safe_value(f"{field_name}.{field.name}", item)
        _reconstruct_public_dataclass(field_name, value)
        return
    if type(value) is Decimal:
        _require_six_decimal_json_decimal(field_name, value)
        return
    if type(value) is datetime:
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_public_json_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) is str:
        _reject_unsafe_json_strings(field_name, value)
        return
    if type(value) is bool or value is None:
        return
    if type(value) is int:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if isinstance(value, (list, dict, set, frozenset)):
        raise ValueError(f"{field_name} must not be a raw collection")
    raise ValueError(f"{field_name} must remain constructor-normalized")


def _reconstruct_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid: {exc}") from exc


def _reject_unsafe_json_strings(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} must be a supported public dataclass")
        for field in fields(value):
            _reject_unsafe_json_strings(label, getattr(value, field.name))
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError(f"{label} contains disallowed text")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
                raise ValueError(f"{label} contains disallowed text")
            _reject_unsafe_json_strings(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_json_strings(label, item)


def _validate_digest_row(row: ResearchSourceRefreshFailureDigestRow) -> None:
    if row.refresh_status != _row_status(row.reason_codes):
        raise ValueError("refresh_status must match reason_codes")
    if row.refresh_status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass status requires pass reason")
    if row.refresh_status == "block" and not any(
        reason_code.startswith("refresh_failure_digest_block")
        for reason_code in row.reason_codes
    ):
        raise ValueError("block status requires block reason")
    if row.refresh_status == "watch" and not any(
        reason_code.startswith("refresh_failure_digest_watch")
        for reason_code in row.reason_codes
    ):
        raise ValueError("watch status requires watch reason")


def _validate_digest_report(report: ResearchSourceRefreshFailureDigestReport) -> None:
    if (
        report.pass_source_group_count
        + report.watch_source_group_count
        + report.block_source_group_count
        != report.source_group_count
    ):
        raise ValueError("status counts must tie to source_group_count")
    if report.source_group_count != _decimal_count(len(report.rows)):
        raise ValueError("source_group_count must match rows")
    if report.pass_source_group_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_source_group_count must match rows")
    if report.watch_source_group_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_source_group_count must match rows")
    if report.block_source_group_count != _status_count(report.rows, "block"):
        raise ValueError("block_source_group_count must match rows")
    if report.hard_failure_count != _decimal_count(
        sum(1 for row in report.rows if row.hard_failure_kind),
    ):
        raise ValueError("hard_failure_count must match rows")
    if report.max_retry_priority_score != max(
        (row.retry_priority_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("max_retry_priority_score must match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match rows")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains disallowed text")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


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


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


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


def _optional_nonnegative_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_count_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return decimal_value


def _require_six_decimal_json_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(QUANT)
    except ArithmeticError as exc:
        raise ValueError(f"{field_name} must use six decimal places") from exc
    if normalized != value or not value.same_quantum(QUANT):
        raise ValueError(f"{field_name} must use six decimal places")


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _status_count(
    rows: tuple[ResearchSourceRefreshFailureDigestRow, ...],
    refresh_status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.refresh_status == refresh_status))


def _reason_count(
    rows: tuple[ResearchSourceRefreshFailureDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchSourceRefreshFailureDigestRow, ...],
) -> tuple[ResearchSourceRefreshFailureDigestReasonCodeCount, ...]:
    source_group_count = _decimal_count(len(rows))
    if reason_codes == (NO_INPUTS_REASON,):
        return (
            ResearchSourceRefreshFailureDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                source_group_ratio=ZERO,
            ),
        )
    return tuple(
        ResearchSourceRefreshFailureDigestReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            source_group_ratio=_ratio(_reason_count(rows, reason_code), source_group_count),
        )
        for reason_code in reason_codes
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    ratio = _ratio(numerator, denominator)
    if ratio > ONE:
        return ONE
    return ratio


def _minutes_between(start: datetime, end: datetime) -> Decimal:
    elapsed = end - start
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(elapsed.days * 86400 + elapsed.seconds) * Decimal("1000000")
            + Decimal(elapsed.microseconds)
        ).__truediv__(MICROSECONDS_PER_MINUTE).quantize(QUANT)


def _retry_priority_score(
    *,
    failure_age_minutes: Decimal,
    last_success_age_minutes: Decimal | None,
    consecutive_failure_count: Decimal,
    hard_failure_kind: bool,
    config: ResearchSourceRefreshFailureDigestConfig,
) -> Decimal:
    if hard_failure_kind or last_success_age_minutes is None:
        return ONE
    score = max(
        _capped_ratio(consecutive_failure_count, config.block_failure_count),
        _capped_ratio(failure_age_minutes, config.block_failure_age_minutes),
        _capped_ratio(last_success_age_minutes, config.stale_success_block_minutes),
    )
    return score.quantize(QUANT)
