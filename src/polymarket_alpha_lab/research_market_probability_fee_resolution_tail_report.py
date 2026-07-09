from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from typing import Any, Iterable


STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

DECIMAL_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
FEE_NORMALIZER = Decimal("0.100000")
WATCH_TAIL_SCORE = Decimal("0.650000")
BLOCK_TAIL_SCORE = Decimal("0.900000")

_UNSAFE_PUBLIC_FIELD_FRAGMENTS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "question",
    "slug",
    "source_url",
    "source_text",
    "url",
    "dsn",
    "table_name",
    "token",
    "wallet",
    "order",
    "trade",
    "sizing",
    "recommendation",
)

_UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "mysql://",
    "sqlite://",
    "table_name",
    "token",
    "wallet",
    "order",
    "trade",
    "sizing",
    "recommendation",
)


@dataclass(frozen=True)
class MarketProbabilityFeeResolutionTailObservation:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    source_url: str
    source_text: str
    observed_at: datetime
    probability: Decimal
    fee_rate: Decimal
    resolution_uncertainty: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilityFeeResolutionTailObservation, "observation")
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "source_url",
            "source_text",
        ):
            _require_nonempty_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "probability",
            _normalize_probability("probability", self.probability),
        )
        object.__setattr__(
            self,
            "fee_rate",
            _normalize_nonnegative_decimal("fee_rate", self.fee_rate),
        )
        object.__setattr__(
            self,
            "resolution_uncertainty",
            _normalize_probability(
                "resolution_uncertainty",
                self.resolution_uncertainty,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketProbabilityFeeResolutionTailReportRow:
    research_digest: str
    observed_at: datetime
    probability: Decimal
    fee_rate: Decimal
    resolution_uncertainty: Decimal
    probability_tail_score: Decimal
    fee_tail_score: Decimal
    tail_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilityFeeResolutionTailReportRow, "row")
        _require_digest("research_digest", self.research_digest)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "probability",
            "resolution_uncertainty",
            "probability_tail_score",
            "fee_tail_score",
            "tail_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "fee_rate",
            _normalize_nonnegative_decimal("fee_rate", self.fee_rate),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketProbabilityFeeResolutionTailReport:
    generated_at: datetime
    config_version: str
    overall_status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_tail_score: Decimal
    rows: tuple[MarketProbabilityFeeResolutionTailReportRow, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilityFeeResolutionTailReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_nonempty_string("config_version", self.config_version)
        _require_status("overall_status", self.overall_status)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_tail_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        rows = _normalize_rows(self.rows)
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_digest("validation_digest", self.validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_research_market_probability_fee_resolution_tail_report(
    observations: Iterable[MarketProbabilityFeeResolutionTailObservation],
    *,
    generated_at: datetime,
    config_version: str = "research-market-probability-fee-resolution-tail-report-v1",
) -> MarketProbabilityFeeResolutionTailReport:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observations")
    rows = tuple(sorted((_row_from_observation(item) for item in observations), key=_row_sort_key))
    overall_status = _overall_status(rows)
    reason_codes = _report_reason_codes(rows, overall_status)
    pass_count = _count_status(rows, STATUS_PASS)
    watch_count = _count_status(rows, STATUS_WATCH)
    block_count = _count_status(rows, STATUS_BLOCK)
    max_tail_score = max((row.tail_score for row in rows), default=ZERO)
    report_without_digest = MarketProbabilityFeeResolutionTailReport(
        generated_at=generated_at,
        config_version=config_version,
        overall_status=overall_status,
        candidate_count=_decimal_count(rows),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_tail_score=max_tail_score,
        rows=rows,
        reason_codes=reason_codes,
        validation_digest=_empty_digest(),
    )
    unsigned_payload = _public_payload_dict(report_without_digest, include_digest=False)
    validation_digest = _validation_digest(unsigned_payload)
    return MarketProbabilityFeeResolutionTailReport(
        generated_at=report_without_digest.generated_at,
        config_version=report_without_digest.config_version,
        overall_status=report_without_digest.overall_status,
        candidate_count=report_without_digest.candidate_count,
        pass_count=report_without_digest.pass_count,
        watch_count=report_without_digest.watch_count,
        block_count=report_without_digest.block_count,
        max_tail_score=report_without_digest.max_tail_score,
        rows=report_without_digest.rows,
        reason_codes=report_without_digest.reason_codes,
        validation_digest=validation_digest,
    )


def research_market_probability_fee_resolution_tail_report_payload(
    report: MarketProbabilityFeeResolutionTailReport,
) -> "FrozenJsonObject":
    _require_exact_type(report, MarketProbabilityFeeResolutionTailReport, "report")
    _require_hard_flags(report)
    payload = _public_payload_dict(report, include_digest=True)
    _reject_public_payload_leaks("payload", payload)
    if not validate_research_market_probability_fee_resolution_tail_report_payload(payload):
        raise ValueError("validation_digest does not match report payload")
    return _freeze_json_object(payload)


def research_market_probability_fee_resolution_tail_report_payload_json(
    report: MarketProbabilityFeeResolutionTailReport,
) -> str:
    payload = research_market_probability_fee_resolution_tail_report_payload(report)
    return _canonical_json(payload)


def validate_research_market_probability_fee_resolution_tail_report_payload(
    payload: object,
) -> bool:
    try:
        if type(payload) is not dict and not isinstance(payload, FrozenJsonObject):
            return False
        _reject_public_payload_leaks("payload", payload)
        digest = payload.get("validation_digest")  # type: ignore[union-attr]
        if type(digest) is not str or not digest.startswith("sha256:"):
            return False
        unsigned = dict(payload)  # type: ignore[arg-type]
        unsigned.pop("validation_digest")
        if _validation_digest(unsigned) != digest:
            return False
        if payload.get("overall_status") not in STATUSES:  # type: ignore[union-attr]
            return False
        rows = payload.get("rows")  # type: ignore[union-attr]
        if not isinstance(rows, (list, tuple, FrozenJsonArray)):
            return False
        for row in rows:
            if type(row) is not dict and not isinstance(row, FrozenJsonObject):
                return False
            if row.get("status") not in STATUSES:
                return False
            if type(row.get("research_digest")) is not str:
                return False
        return True
    except (TypeError, ValueError):
        return False


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


class FrozenJsonArray(list[Any]):
    def __init__(self, value: Iterable[Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: Any, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: Any) -> None:
        raise TypeError("payload is immutable")

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Iterable[Any]) -> None:
        raise TypeError("payload is immutable")

    def insert(self, index: int, value: Any) -> None:
        raise TypeError("payload is immutable")

    def pop(self, index: int = -1) -> Any:
        raise TypeError("payload is immutable")

    def remove(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def reverse(self) -> None:
        raise TypeError("payload is immutable")

    def sort(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __iadd__(self, values: Iterable[Any]) -> "FrozenJsonArray":
        raise TypeError("payload is immutable")

    def __imul__(self, value: int) -> "FrozenJsonArray":
        raise TypeError("payload is immutable")


def _row_from_observation(
    observation: MarketProbabilityFeeResolutionTailObservation,
) -> MarketProbabilityFeeResolutionTailReportRow:
    _require_exact_type(
        observation,
        MarketProbabilityFeeResolutionTailObservation,
        "observation",
    )
    _require_hard_flags(observation)
    probability_tail_score = ((observation.probability - Decimal("0.500000")).copy_abs() * TWO)
    probability_tail_score = _clamp_probability(probability_tail_score)
    fee_tail_score = _clamp_probability(observation.fee_rate / FEE_NORMALIZER)
    tail_score = max(
        probability_tail_score,
        fee_tail_score,
        observation.resolution_uncertainty,
    ).quantize(DECIMAL_QUANT)
    status = _status_from_tail_score(tail_score)
    reason_codes = _row_reason_codes(
        probability_tail_score=probability_tail_score,
        fee_tail_score=fee_tail_score,
        resolution_uncertainty=observation.resolution_uncertainty,
        status=status,
    )
    return MarketProbabilityFeeResolutionTailReportRow(
        research_digest=_observation_digest(observation),
        observed_at=observation.observed_at,
        probability=observation.probability,
        fee_rate=observation.fee_rate,
        resolution_uncertainty=observation.resolution_uncertainty,
        probability_tail_score=probability_tail_score,
        fee_tail_score=fee_tail_score,
        tail_score=tail_score,
        status=status,
        reason_codes=reason_codes,
    )


def _public_payload_dict(
    report: MarketProbabilityFeeResolutionTailReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "report_type": "research_market_probability_fee_resolution_tail",
        "config_version": report.config_version,
        "generated_at": _datetime_string(report.generated_at),
        "overall_status": report.overall_status,
        "candidate_count": _decimal_string(report.candidate_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "block_count": _decimal_string(report.block_count),
        "max_tail_score": _decimal_string(report.max_tail_score),
        "reason_codes": list(report.reason_codes),
        "rows": [_public_row_dict(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["validation_digest"] = report.validation_digest
    return payload


def _public_row_dict(row: MarketProbabilityFeeResolutionTailReportRow) -> dict[str, object]:
    return {
        "research_digest": row.research_digest,
        "observed_at": _datetime_string(row.observed_at),
        "probability": _decimal_string(row.probability),
        "fee_rate": _decimal_string(row.fee_rate),
        "resolution_uncertainty": _decimal_string(row.resolution_uncertainty),
        "probability_tail_score": _decimal_string(row.probability_tail_score),
        "fee_tail_score": _decimal_string(row.fee_tail_score),
        "tail_score": _decimal_string(row.tail_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _observation_digest(observation: MarketProbabilityFeeResolutionTailObservation) -> str:
    digest_source = {
        "candidate_id": observation.candidate_id,
        "market_id": observation.market_id,
        "market_slug": observation.market_slug,
        "market_question": observation.market_question,
        "source_url": observation.source_url,
        "source_text": observation.source_text,
    }
    return _validation_digest(digest_source)


def _validation_digest(payload: dict[str, object]) -> str:
    return f"sha256:{sha256(_canonical_json(payload).encode('utf-8')).hexdigest()}"


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _reject_public_payload_leaks(path: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{path} contains non-string key")
            lowered = key.lower()
            if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FIELD_FRAGMENTS):
                raise ValueError(f"{path}.{key} contains unsafe public field")
            _reject_public_payload_leaks(f"{path}.{key}", item)
        return
    if isinstance(value, (list, tuple, FrozenJsonArray)):
        for item in value:
            _reject_public_payload_leaks(path, item)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError(f"{path} contains unsafe public text")
        return
    if isinstance(value, (Decimal, float, int)) and not isinstance(value, bool):
        raise ValueError(f"{path} contains non-public numeric value")


def _validate_report_consistency(report: MarketProbabilityFeeResolutionTailReport) -> None:
    rows = report.rows
    expected_counts = {
        STATUS_PASS: _count_status(rows, STATUS_PASS),
        STATUS_WATCH: _count_status(rows, STATUS_WATCH),
        STATUS_BLOCK: _count_status(rows, STATUS_BLOCK),
    }
    if report.candidate_count != _decimal_count(rows):
        raise ValueError("candidate_count does not match rows")
    if report.pass_count != expected_counts[STATUS_PASS]:
        raise ValueError("pass_count does not match rows")
    if report.watch_count != expected_counts[STATUS_WATCH]:
        raise ValueError("watch_count does not match rows")
    if report.block_count != expected_counts[STATUS_BLOCK]:
        raise ValueError("block_count does not match rows")
    if report.overall_status != _overall_status(rows):
        raise ValueError("overall_status does not match rows")
    expected_max = max((row.tail_score for row in rows), default=ZERO)
    if report.max_tail_score != expected_max:
        raise ValueError("max_tail_score does not match rows")


def _normalize_rows(
    rows: tuple[MarketProbabilityFeeResolutionTailReportRow, ...],
) -> tuple[MarketProbabilityFeeResolutionTailReportRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(row, MarketProbabilityFeeResolutionTailReportRow, "row")
        _require_hard_flags(row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if sorted_rows != rows:
        raise ValueError("rows must be sorted")
    digests = [row.research_digest for row in rows]
    if len(set(digests)) != len(digests):
        raise ValueError("duplicate research_digest")
    return rows


def _row_sort_key(row: MarketProbabilityFeeResolutionTailReportRow) -> tuple[str, str]:
    return (row.status, row.research_digest)


def _overall_status(rows: tuple[MarketProbabilityFeeResolutionTailReportRow, ...]) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_tail_score(tail_score: Decimal) -> str:
    if tail_score >= BLOCK_TAIL_SCORE:
        return STATUS_BLOCK
    if tail_score >= WATCH_TAIL_SCORE:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    probability_tail_score: Decimal,
    fee_tail_score: Decimal,
    resolution_uncertainty: Decimal,
    status: str,
) -> tuple[str, ...]:
    reasons = [f"status_{status}"]
    if probability_tail_score >= WATCH_TAIL_SCORE:
        reasons.append("probability_tail_watch")
    if probability_tail_score >= BLOCK_TAIL_SCORE:
        reasons.append("probability_tail_block")
    if fee_tail_score >= WATCH_TAIL_SCORE:
        reasons.append("fee_tail_watch")
    if fee_tail_score >= BLOCK_TAIL_SCORE:
        reasons.append("fee_tail_block")
    if resolution_uncertainty >= WATCH_TAIL_SCORE:
        reasons.append("resolution_uncertainty_watch")
    if resolution_uncertainty >= BLOCK_TAIL_SCORE:
        reasons.append("resolution_uncertainty_block")
    return tuple(dict.fromkeys(reasons))


def _report_reason_codes(
    rows: tuple[MarketProbabilityFeeResolutionTailReportRow, ...],
    overall_status: str,
) -> tuple[str, ...]:
    reasons = [f"overall_status_{overall_status}"]
    if not rows:
        reasons.append("empty_observation_set")
    if any(row.status == STATUS_BLOCK for row in rows):
        reasons.append("blocked_tail_observation_present")
    if any(row.status == STATUS_WATCH for row in rows):
        reasons.append("watch_tail_observation_present")
    return tuple(reasons)


def _count_status(
    rows: tuple[MarketProbabilityFeeResolutionTailReportRow, ...],
    status: str,
) -> Decimal:
    return Decimal(str(sum(Decimal("1") for row in rows if row.status == status))).quantize(
        DECIMAL_QUANT,
    )


def _decimal_count(rows: tuple[object, ...]) -> Decimal:
    return Decimal(str(sum(Decimal("1") for _row in rows))).quantize(DECIMAL_QUANT)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal = _normalize_nonnegative_decimal(field_name, value)
    if decimal > ONE:
        raise ValueError(f"{field_name} must be <= 1")
    return decimal


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be Decimal")
    try:
        decimal = value.quantize(DECIMAL_QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite Decimal") from exc
    if not decimal.is_finite():
        raise ValueError(f"{field_name} must be finite Decimal")
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value.quantize(DECIMAL_QUANT)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in value:
        _require_nonempty_string("reason_code", reason_code)
        lowered = reason_code.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FIELD_FRAGMENTS):
            raise ValueError("reason_code contains unsafe public surface")
        normalized.append(reason_code)
    return tuple(dict.fromkeys(normalized))


def _require_status(field_name: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.startswith("sha256:") or len(value) != len(_empty_digest()):
        raise ValueError(f"{field_name} must be a sha256 digest")
    hex_part = value.removeprefix("sha256:")
    if any(char not in "0123456789abcdef" for char in hex_part):
        raise ValueError(f"{field_name} must be lowercase hex")


def _empty_digest() -> str:
    return "sha256:" + ("0" * 64)


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_nonempty_string(field_name: str, value: object) -> None:
    if type(value) is not str or value.strip() == "":
        raise ValueError(f"{field_name} must be a non-empty string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_string(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _decimal_string(value: Decimal) -> str:
    return format(value.quantize(DECIMAL_QUANT), "f")
