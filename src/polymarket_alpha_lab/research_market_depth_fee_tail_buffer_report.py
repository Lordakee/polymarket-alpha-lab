from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_MARKET_DEPTH_FEE_TAIL_BUFFER_CONFIG_VERSION = (
    "research-market-depth-fee-tail-buffer-report-v1"
)
DEPTH_FEE_TAIL_BUFFER_STATUSES = ("pass", "watch", "block")

_COUNT_QUANTUM = Decimal("1")
_MONEY_QUANTUM = Decimal("0.000001")
_RATIO_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_RATIO = Decimal("0.000000")
_ONE_RATIO = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_VALIDATION_DIGEST_PREFIX = "rmdftb-v1:"
_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "candidate_count",
        "buffer_row_count",
        "pass_row_count",
        "watch_row_count",
        "block_row_count",
        "source_missing_count",
        "report_status",
        "reason_codes",
        "buffer_rows",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_KEYS = frozenset(
    (
        "redacted_candidate_ref",
        "redacted_market_ref",
        "redacted_source_ref",
        "observed_at",
        "available_depth_usd",
        "required_tail_buffer_usd",
        "depth_buffer_ratio",
        "fee_rate",
        "tail_loss_rate",
        "fee_tail_pressure",
        "depth_staleness_seconds",
        "source_row_count",
        "source_missing",
        "buffer_status",
        "priority_rank",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_UNSAFE_TEXT_FRAGMENTS = UNSAFE_SURFACE_FIELD_FRAGMENTS | frozenset(
    "".join(parts)
    for parts in (
        ("li", "ve"),
        ("trad", "e"),
        ("trad", "ing"),
        ("bro", "ker"),
        ("cl", "ient"),
        ("exec", "ute"),
        ("conn", "ect"),
        ("requ", "est"),
        ("http",),
        ("pri", "vate", "_", "key"),
        ("api", "_", "key"),
        ("sec", "ret"),
        ("to", "ken"),
        ("candidate", "_", "id"),
        ("market", "_", "id"),
        ("market", "_", "slug"),
        ("market", "_", "question"),
        ("source", "_", "url"),
        ("source", "_", "text"),
        ("d", "sn"),
        ("table", "_", "name"),
        ("siz", "ing"),
        ("recom", "mendation"),
    )
)
_UNSAFE_KEY_FRAGMENTS = _UNSAFE_TEXT_FRAGMENTS | frozenset(
    "".join(parts)
    for parts in (
        ("candidate", "_", "ref"),
        ("candidate", "_", "id"),
        ("market", "_", "ref"),
        ("market", "_", "id"),
        ("market", "_", "slug"),
        ("market", "_", "label"),
        ("market", "_", "question"),
        ("evidence", "_", "ref"),
        ("evidence", "_", "excerpt"),
        ("source", "_", "ref"),
        ("source", "_", "url"),
        ("source", "_", "text"),
        ("source", "_", "excerpt"),
        ("ques", "tion"),
    )
)


@dataclass(frozen=True)
class ResearchMarketDepthFeeTailBufferConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_DEPTH_FEE_TAIL_BUFFER_CONFIG_VERSION
    hard_minimum_depth_buffer_ratio: Decimal = Decimal("1.000000")
    minimum_depth_buffer_ratio: Decimal = Decimal("1.250000")
    fee_rate_watch_threshold: Decimal = Decimal("0.020000")
    fee_rate_block_threshold: Decimal = Decimal("0.050000")
    tail_loss_watch_threshold: Decimal = Decimal("0.150000")
    tail_loss_block_threshold: Decimal = Decimal("0.300000")
    max_depth_staleness_seconds: Decimal = Decimal("900")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthFeeTailBufferConfig:
            raise ValueError("config must be a ResearchMarketDepthFeeTailBufferConfig")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "hard_minimum_depth_buffer_ratio",
            "minimum_depth_buffer_ratio",
            "fee_rate_watch_threshold",
            "fee_rate_block_threshold",
            "tail_loss_watch_threshold",
            "tail_loss_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_depth_staleness_seconds",
            _normalize_nonnegative_count(
                "max_depth_staleness_seconds",
                self.max_depth_staleness_seconds,
            ),
        )
        if self.minimum_depth_buffer_ratio < self.hard_minimum_depth_buffer_ratio:
            raise ValueError("minimum_depth_buffer_ratio must be at least hard minimum")
        if self.fee_rate_block_threshold < self.fee_rate_watch_threshold:
            raise ValueError("fee_rate_block_threshold must be at least watch threshold")
        if self.tail_loss_block_threshold < self.tail_loss_watch_threshold:
            raise ValueError("tail_loss_block_threshold must be at least watch threshold")
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthFeeTailBufferCandidate:
    candidate_ref: str = field(repr=False)
    market_ref: str = field(repr=False)
    market_label: str = field(repr=False)
    evidence_ref: str = field(repr=False)
    evidence_excerpt: str = field(repr=False)
    observed_at: datetime
    available_depth_usd: Decimal
    required_tail_buffer_usd: Decimal
    fee_rate: Decimal
    tail_loss_rate: Decimal
    depth_staleness_seconds: Decimal
    source_row_count: Decimal = Decimal("1")
    source_missing: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthFeeTailBufferCandidate:
            raise ValueError("candidate must be a ResearchMarketDepthFeeTailBufferCandidate")
        for field_name in (
            "candidate_ref",
            "market_ref",
            "market_label",
            "evidence_ref",
            "evidence_excerpt",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("available_depth_usd", "required_tail_buffer_usd"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_money(field_name, getattr(self, field_name)),
            )
        if self.required_tail_buffer_usd == _ZERO_RATIO:
            raise ValueError("required_tail_buffer_usd must be positive")
        for field_name in ("fee_rate", "tail_loss_rate"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("depth_staleness_seconds", "source_row_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if type(self.source_missing) is not bool:
            raise ValueError("source_missing must be a bool")
        require_paper_only_flags("candidate", self)


@dataclass(frozen=True)
class ResearchMarketDepthFeeTailBufferRow:
    redacted_candidate_ref: str
    redacted_market_ref: str
    redacted_source_ref: str
    observed_at: datetime
    available_depth_usd: Decimal
    required_tail_buffer_usd: Decimal
    depth_buffer_ratio: Decimal
    fee_rate: Decimal
    tail_loss_rate: Decimal
    fee_tail_pressure: Decimal
    depth_staleness_seconds: Decimal
    source_row_count: Decimal
    source_missing: bool
    buffer_status: str
    priority_rank: Decimal
    reason_codes: tuple[str, ...]
    validation_digest: str = field(default="", init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthFeeTailBufferRow:
            raise ValueError("row must be a ResearchMarketDepthFeeTailBufferRow")
        _require_redacted_ref(
            "redacted_candidate_ref",
            self.redacted_candidate_ref,
            "<redacted-candidate-",
        )
        _require_redacted_ref(
            "redacted_market_ref",
            self.redacted_market_ref,
            "<redacted-market-",
        )
        _require_redacted_ref(
            "redacted_source_ref",
            self.redacted_source_ref,
            "<redacted-source-",
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("available_depth_usd", "required_tail_buffer_usd"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_money(field_name, getattr(self, field_name)),
            )
        if self.required_tail_buffer_usd == _ZERO_RATIO:
            raise ValueError("required_tail_buffer_usd must be positive")
        for field_name in (
            "depth_buffer_ratio",
            "fee_rate",
            "tail_loss_rate",
            "fee_tail_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_staleness_seconds",
            "source_row_count",
            "priority_rank",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if type(self.source_missing) is not bool:
            raise ValueError("source_missing must be a bool")
        _require_member("buffer_status", self.buffer_status, DEPTH_FEE_TAIL_BUFFER_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "validation_digest", _row_validation_digest(self))
        _require_row_validation_digest(self)
        require_paper_only_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketDepthFeeTailBufferReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    buffer_row_count: Decimal
    pass_row_count: Decimal
    watch_row_count: Decimal
    block_row_count: Decimal
    source_missing_count: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    buffer_rows: tuple[ResearchMarketDepthFeeTailBufferRow, ...]
    validation_digest: str = field(default="", init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthFeeTailBufferReport:
            raise ValueError("report must be a ResearchMarketDepthFeeTailBufferReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "buffer_row_count",
            "pass_row_count",
            "watch_row_count",
            "block_row_count",
            "source_missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, DEPTH_FEE_TAIL_BUFFER_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        rows = tuple(self.buffer_rows)
        for row in rows:
            if type(row) is not ResearchMarketDepthFeeTailBufferRow:
                raise ValueError("buffer_rows must contain buffer row values")
            _require_row_validation_digest(row)
            require_paper_only_flags("row", row)
        object.__setattr__(self, "buffer_rows", rows)
        _validate_report(self)
        object.__setattr__(self, "validation_digest", _report_validation_digest(self))
        _require_report_validation_digest(self)
        _reject_unsafe_public_payload("report", self)
        require_paper_only_flags("report", self)


def build_research_market_depth_fee_tail_buffer_report(
    candidates: (
        list[ResearchMarketDepthFeeTailBufferCandidate]
        | tuple[ResearchMarketDepthFeeTailBufferCandidate, ...]
    ),
    *,
    config: ResearchMarketDepthFeeTailBufferConfig,
    generated_at: datetime,
) -> ResearchMarketDepthFeeTailBufferReport:
    if type(config) is not ResearchMarketDepthFeeTailBufferConfig:
        raise ValueError("config must be a ResearchMarketDepthFeeTailBufferConfig")
    require_paper_only_flags("config", config)
    normalized_candidates = _normalize_candidates(candidates)
    candidate_refs = _redaction_map(
        tuple(candidate.candidate_ref for candidate in normalized_candidates),
        "candidate",
    )
    market_refs = _redaction_map(
        tuple(candidate.market_ref for candidate in normalized_candidates),
        "market",
    )
    evidence_refs = _redaction_map(
        tuple(candidate.evidence_ref for candidate in normalized_candidates),
        "source",
    )
    ranked_rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    candidate,
                    config=config,
                    redacted_candidate_ref=candidate_refs[candidate.candidate_ref],
                    redacted_market_ref=market_refs[candidate.market_ref],
                    redacted_source_ref=evidence_refs[candidate.evidence_ref],
                )
                for candidate in normalized_candidates
            ),
            key=_row_key,
        ),
    )
    rows = tuple(
        _row_with_priority(row, _count(index))
        for index, row in enumerate(ranked_rows, start=1)
    )
    pass_row_count = _count(sum(1 for row in rows if row.buffer_status == "pass"))
    watch_row_count = _count(sum(1 for row in rows if row.buffer_status == "watch"))
    block_row_count = _count(sum(1 for row in rows if row.buffer_status == "block"))
    source_missing_count = _count(sum(1 for row in rows if row.source_missing))
    report_status = _report_status(rows)

    return ResearchMarketDepthFeeTailBufferReport(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count(len(normalized_candidates)),
        buffer_row_count=_count(len(rows)),
        pass_row_count=pass_row_count,
        watch_row_count=watch_row_count,
        block_row_count=block_row_count,
        source_missing_count=source_missing_count,
        report_status=report_status,
        reason_codes=_report_reason_codes(
            report_status,
            source_missing_count=source_missing_count,
        ),
        buffer_rows=rows,
    )


def research_market_depth_fee_tail_buffer_report_payload(
    report: ResearchMarketDepthFeeTailBufferReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketDepthFeeTailBufferReport:
        require_paper_only_flags("report", report)
        _validate_report(report)
        _require_report_validation_digest(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        parsed_report = _report_from_public_payload(report)
        payload = _json_ready(parsed_report)
    else:
        raise ValueError("report must be a ResearchMarketDepthFeeTailBufferReport")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchMarketDepthFeeTailBufferReport:
    _require_payload_keys("report", payload, _REPORT_PAYLOAD_KEYS)
    rows_value = payload["buffer_rows"]
    if type(rows_value) not in (list, tuple):
        raise ValueError("buffer_rows payload schema must use a list")
    rows = tuple(_row_from_public_payload(row) for row in rows_value)
    parsed_report = ResearchMarketDepthFeeTailBufferReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        candidate_count=_payload_decimal("candidate_count", payload["candidate_count"]),
        buffer_row_count=_payload_decimal("buffer_row_count", payload["buffer_row_count"]),
        pass_row_count=_payload_decimal("pass_row_count", payload["pass_row_count"]),
        watch_row_count=_payload_decimal("watch_row_count", payload["watch_row_count"]),
        block_row_count=_payload_decimal("block_row_count", payload["block_row_count"]),
        source_missing_count=_payload_decimal(
            "source_missing_count",
            payload["source_missing_count"],
        ),
        report_status=_payload_string("report_status", payload["report_status"]),
        reason_codes=_payload_reason_codes(payload["reason_codes"]),
        buffer_rows=rows,
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )
    expected_digest = _payload_validation_digest(
        "validation_digest",
        payload["validation_digest"],
    )
    if parsed_report.validation_digest != expected_digest:
        raise ValueError("validation_digest mismatch: report payload may be tampered")
    return parsed_report


def _row_from_public_payload(payload: object) -> ResearchMarketDepthFeeTailBufferRow:
    if type(payload) is not dict:
        raise ValueError("row payload schema must use a plain dict")
    _require_payload_keys("row", payload, _ROW_PAYLOAD_KEYS)
    parsed_row = ResearchMarketDepthFeeTailBufferRow(
        redacted_candidate_ref=_payload_string(
            "redacted_candidate_ref",
            payload["redacted_candidate_ref"],
        ),
        redacted_market_ref=_payload_string(
            "redacted_market_ref",
            payload["redacted_market_ref"],
        ),
        redacted_source_ref=_payload_string(
            "redacted_source_ref",
            payload["redacted_source_ref"],
        ),
        observed_at=_payload_datetime("observed_at", payload["observed_at"]),
        available_depth_usd=_payload_decimal(
            "available_depth_usd",
            payload["available_depth_usd"],
        ),
        required_tail_buffer_usd=_payload_decimal(
            "required_tail_buffer_usd",
            payload["required_tail_buffer_usd"],
        ),
        depth_buffer_ratio=_payload_decimal(
            "depth_buffer_ratio",
            payload["depth_buffer_ratio"],
        ),
        fee_rate=_payload_decimal("fee_rate", payload["fee_rate"]),
        tail_loss_rate=_payload_decimal("tail_loss_rate", payload["tail_loss_rate"]),
        fee_tail_pressure=_payload_decimal(
            "fee_tail_pressure",
            payload["fee_tail_pressure"],
        ),
        depth_staleness_seconds=_payload_decimal(
            "depth_staleness_seconds",
            payload["depth_staleness_seconds"],
        ),
        source_row_count=_payload_decimal(
            "source_row_count",
            payload["source_row_count"],
        ),
        source_missing=_payload_bool("source_missing", payload["source_missing"]),
        buffer_status=_payload_string("buffer_status", payload["buffer_status"]),
        priority_rank=_payload_decimal("priority_rank", payload["priority_rank"]),
        reason_codes=_payload_reason_codes(payload["reason_codes"]),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )
    expected_digest = _payload_validation_digest(
        "validation_digest",
        payload["validation_digest"],
    )
    if parsed_row.validation_digest != expected_digest:
        raise ValueError("validation_digest mismatch: row payload may be tampered")
    return parsed_row


def _require_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    if frozenset(payload) != expected_keys:
        raise ValueError(f"{label} payload schema keys mismatch")


def _payload_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    return value


def _payload_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is Decimal:
        return value
    if type(value) is str:
        try:
            return Decimal(value)
        except Exception as exc:
            raise ValueError(f"{field_name} must be a Decimal string") from exc
    raise ValueError(f"{field_name} must be a Decimal")


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is datetime:
        return value
    if type(value) is str:
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be a datetime string") from exc
    raise ValueError(f"{field_name} must be a datetime")


def _payload_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes(value)


def _payload_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a validation_digest string")
    if not value.startswith(_VALIDATION_DIGEST_PREFIX):
        raise ValueError(f"{field_name} must use the validation_digest prefix")
    suffix = value.removeprefix(_VALIDATION_DIGEST_PREFIX)
    if len(suffix) != 64 or any(char not in "0123456789abcdef" for char in suffix):
        raise ValueError(f"{field_name} must be a sha256 validation_digest")
    return value


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


def _normalize_candidates(
    candidates: (
        list[ResearchMarketDepthFeeTailBufferCandidate]
        | tuple[ResearchMarketDepthFeeTailBufferCandidate, ...]
    ),
) -> tuple[ResearchMarketDepthFeeTailBufferCandidate, ...]:
    if type(candidates) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    normalized = tuple(candidates)
    seen_candidates: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not ResearchMarketDepthFeeTailBufferCandidate:
            raise ValueError("candidates must contain depth fee tail buffer candidate values")
        require_paper_only_flags("candidate", candidate)
        if candidate.candidate_ref in seen_candidates:
            raise ValueError("candidates must not contain duplicate candidate references")
        seen_candidates.add(candidate.candidate_ref)
    return normalized


def _row_from_candidate(
    candidate: ResearchMarketDepthFeeTailBufferCandidate,
    *,
    config: ResearchMarketDepthFeeTailBufferConfig,
    redacted_candidate_ref: str,
    redacted_market_ref: str,
    redacted_source_ref: str,
) -> ResearchMarketDepthFeeTailBufferRow:
    depth_buffer_ratio = _depth_buffer_ratio(
        candidate.available_depth_usd,
        candidate.required_tail_buffer_usd,
    )
    fee_tail_pressure = _normalize_nonnegative_ratio(
        "fee_tail_pressure",
        candidate.fee_rate + candidate.tail_loss_rate,
    )
    reason_codes = _row_reason_codes(
        candidate,
        config,
        depth_buffer_ratio=depth_buffer_ratio,
    )
    return ResearchMarketDepthFeeTailBufferRow(
        redacted_candidate_ref=redacted_candidate_ref,
        redacted_market_ref=redacted_market_ref,
        redacted_source_ref=redacted_source_ref,
        observed_at=candidate.observed_at,
        available_depth_usd=candidate.available_depth_usd,
        required_tail_buffer_usd=candidate.required_tail_buffer_usd,
        depth_buffer_ratio=depth_buffer_ratio,
        fee_rate=candidate.fee_rate,
        tail_loss_rate=candidate.tail_loss_rate,
        fee_tail_pressure=fee_tail_pressure,
        depth_staleness_seconds=candidate.depth_staleness_seconds,
        source_row_count=candidate.source_row_count,
        source_missing=candidate.source_missing,
        buffer_status=_row_status(candidate, reason_codes),
        priority_rank=_ZERO_COUNT,
        reason_codes=reason_codes,
    )


def _row_with_priority(
    row: ResearchMarketDepthFeeTailBufferRow,
    priority_rank: Decimal,
) -> ResearchMarketDepthFeeTailBufferRow:
    return ResearchMarketDepthFeeTailBufferRow(
        redacted_candidate_ref=row.redacted_candidate_ref,
        redacted_market_ref=row.redacted_market_ref,
        redacted_source_ref=row.redacted_source_ref,
        observed_at=row.observed_at,
        available_depth_usd=row.available_depth_usd,
        required_tail_buffer_usd=row.required_tail_buffer_usd,
        depth_buffer_ratio=row.depth_buffer_ratio,
        fee_rate=row.fee_rate,
        tail_loss_rate=row.tail_loss_rate,
        fee_tail_pressure=row.fee_tail_pressure,
        depth_staleness_seconds=row.depth_staleness_seconds,
        source_row_count=row.source_row_count,
        source_missing=row.source_missing,
        buffer_status=row.buffer_status,
        priority_rank=priority_rank,
        reason_codes=row.reason_codes,
    )


def _depth_buffer_ratio(available_depth_usd: Decimal, required_tail_buffer_usd: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _normalize_nonnegative_ratio(
            "depth_buffer_ratio",
            available_depth_usd / required_tail_buffer_usd,
        )


def _row_reason_codes(
    candidate: ResearchMarketDepthFeeTailBufferCandidate,
    config: ResearchMarketDepthFeeTailBufferConfig,
    *,
    depth_buffer_ratio: Decimal,
) -> tuple[str, ...]:
    if candidate.source_missing:
        return ("research_market_depth_fee_tail_buffer_source_missing",)

    reason_codes: list[str] = []
    if depth_buffer_ratio < config.hard_minimum_depth_buffer_ratio:
        reason_codes.append("depth_buffer_below_required")
    elif depth_buffer_ratio < config.minimum_depth_buffer_ratio:
        reason_codes.append("depth_buffer_watch")
    if candidate.fee_rate >= config.fee_rate_block_threshold:
        reason_codes.append("fee_rate_block")
    elif candidate.fee_rate >= config.fee_rate_watch_threshold:
        reason_codes.append("fee_rate_watch")
    if candidate.tail_loss_rate >= config.tail_loss_block_threshold:
        reason_codes.append("tail_loss_block")
    elif candidate.tail_loss_rate >= config.tail_loss_watch_threshold:
        reason_codes.append("tail_loss_watch")
    if candidate.depth_staleness_seconds > config.max_depth_staleness_seconds:
        reason_codes.append("depth_snapshot_stale")
    if not reason_codes:
        reason_codes.append("market_depth_fee_tail_buffer_clear")
    return tuple(reason_codes)


def _row_status(
    candidate: ResearchMarketDepthFeeTailBufferCandidate,
    reason_codes: tuple[str, ...],
) -> str:
    if candidate.source_missing:
        return "watch"
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if "depth_buffer_below_required" in reason_codes:
        return "block"
    if reason_codes == ("market_depth_fee_tail_buffer_clear",):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchMarketDepthFeeTailBufferRow, ...]) -> str:
    if any(row.buffer_status == "block" for row in rows):
        return "block"
    if any(row.buffer_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    report_status: str,
    *,
    source_missing_count: Decimal,
) -> tuple[str, ...]:
    if report_status == "block":
        reason_codes = ["research_market_depth_fee_tail_buffer_block"]
    elif report_status == "watch":
        reason_codes = ["research_market_depth_fee_tail_buffer_watch"]
    else:
        return ("research_market_depth_fee_tail_buffer_clear",)
    if source_missing_count > _ZERO_COUNT:
        reason_codes.append("research_market_depth_fee_tail_buffer_source_missing")
    return tuple(reason_codes)


def _row_key(row: ResearchMarketDepthFeeTailBufferRow) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        _STATUS_RANK[row.buffer_status],
        -row.fee_tail_pressure,
        row.depth_buffer_ratio,
        row.redacted_candidate_ref,
        row.redacted_market_ref,
    )


def _redaction_map(values: tuple[str, ...], label: str) -> dict[str, str]:
    return {
        value: f"<redacted-{label}-{index:03d}>"
        for index, value in enumerate(sorted(set(values)), start=1)
    }


def _validate_report(report: ResearchMarketDepthFeeTailBufferReport) -> None:
    rows = report.buffer_rows
    for row in rows:
        if type(row) is not ResearchMarketDepthFeeTailBufferRow:
            raise ValueError("buffer_rows must contain buffer row values")
        _require_row_validation_digest(row)
        require_paper_only_flags("row", row)
    if report.buffer_row_count != _count(len(rows)):
        raise ValueError("buffer_row_count must match buffer_rows")
    if report.candidate_count != report.buffer_row_count:
        raise ValueError("candidate_count must match buffer_row_count")
    if report.pass_row_count != _count(sum(1 for row in rows if row.buffer_status == "pass")):
        raise ValueError("pass_row_count must match buffer_rows")
    if report.watch_row_count != _count(sum(1 for row in rows if row.buffer_status == "watch")):
        raise ValueError("watch_row_count must match buffer_rows")
    if report.block_row_count != _count(sum(1 for row in rows if row.buffer_status == "block")):
        raise ValueError("block_row_count must match buffer_rows")
    if report.source_missing_count != _count(sum(1 for row in rows if row.source_missing)):
        raise ValueError("source_missing_count must match buffer_rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match buffer_rows")
    if report.reason_codes != _report_reason_codes(
        report.report_status,
        source_missing_count=report.source_missing_count,
    ):
        raise ValueError("reason_codes must match buffer_rows")


def _row_validation_digest(row: ResearchMarketDepthFeeTailBufferRow) -> str:
    return _validation_digest(
        (
            row.redacted_candidate_ref,
            row.redacted_market_ref,
            row.redacted_source_ref,
            row.observed_at,
            row.available_depth_usd,
            row.required_tail_buffer_usd,
            row.depth_buffer_ratio,
            row.fee_rate,
            row.tail_loss_rate,
            row.fee_tail_pressure,
            row.depth_staleness_seconds,
            row.source_row_count,
            row.source_missing,
            row.buffer_status,
            row.priority_rank,
            row.reason_codes,
            row.paper_only,
            row.report_only,
            row.readonly,
        ),
    )


def _report_validation_digest(report: ResearchMarketDepthFeeTailBufferReport) -> str:
    return _validation_digest(
        (
            report.generated_at,
            report.config_version,
            report.candidate_count,
            report.buffer_row_count,
            report.pass_row_count,
            report.watch_row_count,
            report.block_row_count,
            report.source_missing_count,
            report.report_status,
            report.reason_codes,
            tuple(row.validation_digest for row in report.buffer_rows),
            report.paper_only,
            report.report_only,
            report.readonly,
        ),
    )


def _require_row_validation_digest(row: ResearchMarketDepthFeeTailBufferRow) -> None:
    if row.validation_digest != _row_validation_digest(row):
        raise ValueError("validation_digest mismatch: row may be tampered")


def _require_report_validation_digest(report: ResearchMarketDepthFeeTailBufferReport) -> None:
    if report.validation_digest != _report_validation_digest(report):
        raise ValueError("validation_digest mismatch: report may be tampered")


def _validation_digest(parts: tuple[object, ...]) -> str:
    material = "\n".join(_digest_part(part) for part in parts)
    return _VALIDATION_DIGEST_PREFIX + hashlib.sha256(material.encode("utf-8")).hexdigest()


def _digest_part(value: object) -> str:
    if value is None:
        return "none:"
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("validation_digest values must be finite")
        return f"decimal:{value}"
    if type(value) is datetime:
        return f"datetime:{_as_utc('validation_digest datetime', value).isoformat()}"
    if type(value) is str:
        return f"str:{len(value)}:{value}"
    if type(value) is bool:
        if value:
            return "bool:true"
        return "bool:false"
    if type(value) is tuple:
        return "tuple:[" + ",".join(_digest_part(item) for item in value) + "]"
    raise ValueError("validation_digest values must be canonical")


def _json_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        if not _is_allowed_public_dataclass(value):
            raise ValueError("unsafe payload object must use plain values")
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("JSON datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        if type(value) is not dict:
            raise ValueError("unsafe payload object must use plain dict values")
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        if type(value) not in (list, tuple):
            raise ValueError("unsafe payload object must use plain sequence values")
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)):
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if not _is_allowed_public_dataclass(value):
            raise ValueError("unsafe payload object must use plain values")
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if isinstance(value, dict):
        if type(value) is not dict:
            raise ValueError("unsafe payload object must use plain dict values")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        if type(value) not in (list, tuple):
            raise ValueError("unsafe payload object must use plain sequence values")
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _is_allowed_public_dataclass(value: object) -> bool:
    return type(value) in (
        ResearchMarketDepthFeeTailBufferConfig,
        ResearchMarketDepthFeeTailBufferRow,
        ResearchMarketDepthFeeTailBufferReport,
    )


def _reject_unsafe_public_text(label: str, value: str) -> None:
    if _has_fragment(value, _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


def _reject_unsafe_public_key(label: str, value: str) -> None:
    normalized = value.lower()
    if normalized.startswith("redacted_"):
        return
    if _has_fragment(value, _UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"unsafe public key in {label}")


def _has_fragment(value: str, fragments: frozenset[str]) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in fragments)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_nonnegative_money(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_MONEY_QUANTUM)
    if quantized < Decimal("0.000000"):
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_nonnegative_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_RATIO_QUANTUM)
    if quantized < _ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _require_reason_code(value: object) -> None:
    if type(value) is not str:
        raise ValueError("reason_codes must contain strings")
    if value.strip() != value or not value:
        raise ValueError("reason_codes must contain canonical strings")
    if value != value.lower() or value[0] == "_" or value[-1] == "_":
        raise ValueError("reason_codes must be lowercase snake_case strings")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError("reason_codes must be lowercase snake_case strings")
    _reject_unsafe_public_text("reason_codes", value)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_redacted_ref(field_name: str, value: object, prefix: str) -> None:
    _require_canonical_string(field_name, value)
    if not value.startswith(prefix) or not value.endswith(">"):
        raise ValueError(f"{field_name} must be redacted")
    opaque_ref = value[len(prefix) : -1]
    if len(opaque_ref) != 3 or not opaque_ref.isdecimal():
        raise ValueError(f"{field_name} must be redacted")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_DEPTH_FEE_TAIL_BUFFER_CONFIG_VERSION",
    "DEPTH_FEE_TAIL_BUFFER_STATUSES",
    "ResearchMarketDepthFeeTailBufferConfig",
    "ResearchMarketDepthFeeTailBufferCandidate",
    "ResearchMarketDepthFeeTailBufferRow",
    "ResearchMarketDepthFeeTailBufferReport",
    "build_research_market_depth_fee_tail_buffer_report",
    "research_market_depth_fee_tail_buffer_report_payload",
)
