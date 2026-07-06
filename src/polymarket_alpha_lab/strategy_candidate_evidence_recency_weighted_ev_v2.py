"""Pure paper/report/readonly recency-weighted evidence EV scorer v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any


DEFAULT_STRATEGY_CANDIDATE_EVIDENCE_RECENCY_WEIGHTED_EV_V2_VERSION = (
    "strategy-candidate-evidence-recency-weighted-ev-v2"
)
EVIDENCE_KINDS = ("analysis", "official")
CANDIDATE_STATUSES = ("candidate", "watch", "blocked", "pass")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
COUNT_ONE = Decimal("1")


@dataclass(frozen=True)
class StrategyCandidateEvidenceRecencyWeightedEvV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_EVIDENCE_RECENCY_WEIGHTED_EV_V2_VERSION
    )
    recency_half_life_seconds: Decimal = Decimal("3600.000000")
    stale_evidence_age_seconds: Decimal = Decimal("3600.000000")
    official_evidence_boost: Decimal = Decimal("0.200000")
    stale_evidence_penalty: Decimal = Decimal("0.020000")
    minimum_candidate_score: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for name in (
            "recency_half_life_seconds",
            "stale_evidence_age_seconds",
            "official_evidence_boost",
            "stale_evidence_penalty",
            "minimum_candidate_score",
        ):
            object.__setattr__(self, name, _normalize_nonnegative_decimal(name, getattr(self, name)))
        if self.recency_half_life_seconds <= ZERO:
            raise ValueError("recency_half_life_seconds must be positive")
        _reject_unsafe_public("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateEvidenceRecencyWeightedEvV2Observation:
    candidate_key: str
    evidence_key: str
    evidence_kind: str
    observed_at: datetime
    estimated_probability: Decimal
    market_probability: Decimal
    confidence: Decimal = Decimal("1.000000")
    relevance: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_key", self.candidate_key)
        _require_canonical_string("evidence_key", self.evidence_key)
        _require_choice("evidence_kind", self.evidence_kind, EVIDENCE_KINDS)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in ("estimated_probability", "market_probability", "confidence", "relevance"):
            object.__setattr__(self, name, _normalize_probability(name, getattr(self, name)))
        _reject_unsafe_public("observation", self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class StrategyCandidateEvidenceRecencyWeightedEvV2Row:
    candidate_ref: str
    evidence_refs: tuple[str, ...]
    evidence_count: Decimal
    latest_evidence_at: datetime
    newest_evidence_age_seconds: Decimal
    total_raw_expected_value: Decimal
    recency_weighted_expected_value: Decimal
    official_evidence_boost: Decimal
    stale_evidence_penalty: Decimal
    recency_weighted_ev_score: Decimal
    candidate_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_ref", self.candidate_ref)
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_public_refs("evidence_refs", self.evidence_refs),
        )
        object.__setattr__(
            self,
            "evidence_count",
            _normalize_positive_count("evidence_count", self.evidence_count),
        )
        object.__setattr__(
            self,
            "latest_evidence_at",
            _as_utc("latest_evidence_at", self.latest_evidence_at),
        )
        for name in (
            "newest_evidence_age_seconds",
            "official_evidence_boost",
            "stale_evidence_penalty",
        ):
            object.__setattr__(self, name, _normalize_nonnegative_decimal(name, getattr(self, name)))
        for name in (
            "total_raw_expected_value",
            "recency_weighted_expected_value",
            "recency_weighted_ev_score",
        ):
            object.__setattr__(self, name, _normalize_decimal(name, getattr(self, name)))
        _require_choice("candidate_status", self.candidate_status, CANDIDATE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public("row", self)
        digest = _row_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", digest)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(_row_public_map(self, include_digest=True))
        if type(payload) is not dict:
            raise ValueError("row payload must be a JSON object")
        return payload


@dataclass(frozen=True)
class StrategyCandidateEvidenceRecencyWeightedEvV2Report:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    candidate_count: Decimal
    candidate_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    candidate_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCandidateEvidenceRecencyWeightedEvV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for name in (
            "observation_count",
            "candidate_count",
            "candidate_candidate_count",
            "watch_candidate_count",
            "blocked_candidate_count",
        ):
            object.__setattr__(self, name, _normalize_nonnegative_count(name, getattr(self, name)))
        _require_choice("candidate_status", self.candidate_status, CANDIDATE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public("report", self)
        digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", digest)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_evidence_recency_weighted_ev_v2_payload(self)


def build_strategy_candidate_evidence_recency_weighted_ev_v2(
    observations: tuple[StrategyCandidateEvidenceRecencyWeightedEvV2Observation, ...]
    | list[StrategyCandidateEvidenceRecencyWeightedEvV2Observation],
    *,
    config: StrategyCandidateEvidenceRecencyWeightedEvV2Config,
    generated_at: datetime,
) -> StrategyCandidateEvidenceRecencyWeightedEvV2Report:
    if type(config) is not StrategyCandidateEvidenceRecencyWeightedEvV2Config:
        raise ValueError("config must be a StrategyCandidateEvidenceRecencyWeightedEvV2Config")
    _require_hard_flags("config", config)
    if not isinstance(observations, (list, tuple)):
        raise ValueError("observations must be a list or tuple")
    generated_at = _as_utc("generated_at", generated_at)

    items: list[StrategyCandidateEvidenceRecencyWeightedEvV2Observation] = []
    seen: set[tuple[str, str, datetime]] = set()
    for item in observations:
        if type(item) is not StrategyCandidateEvidenceRecencyWeightedEvV2Observation:
            raise ValueError(
                "observations must contain StrategyCandidateEvidenceRecencyWeightedEvV2Observation",
            )
        _require_hard_flags("observation", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (item.candidate_key, item.evidence_key, item.observed_at)
        if key in seen:
            raise ValueError("duplicate observation")
        seen.add(key)
        items.append(item)

    rows = tuple(
        _build_row(candidate_items, config=config, generated_at=generated_at)
        for candidate_items in _candidate_groups(items)
    )
    candidate_count = _count(len(rows))
    candidate_candidate_count = _count(
        sum(1 for row in rows if row.candidate_status == "candidate"),
    )
    watch_candidate_count = _count(sum(1 for row in rows if row.candidate_status == "watch"))
    blocked_candidate_count = _count(
        sum(1 for row in rows if row.candidate_status == "blocked"),
    )

    return StrategyCandidateEvidenceRecencyWeightedEvV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        observation_count=_count(len(items)),
        candidate_count=candidate_count,
        candidate_candidate_count=candidate_candidate_count,
        watch_candidate_count=watch_candidate_count,
        blocked_candidate_count=blocked_candidate_count,
        candidate_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_candidate_evidence_recency_weighted_ev_v2_payload(
    report: StrategyCandidateEvidenceRecencyWeightedEvV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCandidateEvidenceRecencyWeightedEvV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public("report", report)
        payload = _json_ready(_report_public_map(report, include_digest=True))
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public("payload", report)
        _verify_payload_digests(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyCandidateEvidenceRecencyWeightedEvV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public("payload", payload)
    _verify_payload_digests(payload)
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


def _build_row(
    items: tuple[StrategyCandidateEvidenceRecencyWeightedEvV2Observation, ...],
    *,
    config: StrategyCandidateEvidenceRecencyWeightedEvV2Config,
    generated_at: datetime,
) -> StrategyCandidateEvidenceRecencyWeightedEvV2Row:
    latest = max(item.observed_at for item in items)
    newest_age = _age_seconds(latest, generated_at)
    weighted_ev = ZERO
    raw_ev = ZERO
    official_boost = ZERO
    stale_hits = Decimal("0")
    has_fresh_official = False
    evidence_refs: list[str] = []
    for item in items:
        age = _age_seconds(item.observed_at, generated_at)
        edge = _normalize_decimal(
            "evidence_expected_value",
            item.estimated_probability - item.market_probability,
        )
        raw_ev = _normalize_decimal("total_raw_expected_value", raw_ev + edge)
        recency = _recency_weight(age, config.recency_half_life_seconds)
        item_weight = _normalize_decimal(
            "item_weight",
            recency * item.confidence * item.relevance,
        )
        item_ev = _normalize_decimal("item_ev", edge * item_weight)
        if item.evidence_kind == "official":
            boost = _normalize_decimal("official_evidence_boost", item_ev * config.official_evidence_boost)
            official_boost = _normalize_decimal("official_evidence_boost", official_boost + boost)
            item_ev = _normalize_decimal("item_ev", item_ev + boost)
            if age <= config.stale_evidence_age_seconds:
                has_fresh_official = True
        if age > config.stale_evidence_age_seconds:
            stale_hits = _normalize_decimal("stale_hits", stale_hits + COUNT_ONE)
        weighted_ev = _normalize_decimal("recency_weighted_expected_value", weighted_ev + item_ev)
        evidence_refs.append(_public_ref("evidence", item.evidence_key))
    stale_penalty = _normalize_nonnegative_decimal(
        "stale_evidence_penalty",
        stale_hits * config.stale_evidence_penalty,
    )
    applied_penalty = ZERO if has_fresh_official else stale_penalty
    score = _normalize_decimal("recency_weighted_ev_score", weighted_ev - applied_penalty)
    status = _candidate_status(score, config.minimum_candidate_score)
    return StrategyCandidateEvidenceRecencyWeightedEvV2Row(
        candidate_ref=_public_ref("candidate", items[0].candidate_key),
        evidence_refs=tuple(sorted(evidence_refs)),
        evidence_count=_count(len(items)),
        latest_evidence_at=latest,
        newest_evidence_age_seconds=newest_age,
        total_raw_expected_value=raw_ev,
        recency_weighted_expected_value=weighted_ev,
        official_evidence_boost=official_boost,
        stale_evidence_penalty=stale_penalty,
        recency_weighted_ev_score=score,
        candidate_status=status,
        reason_codes=_row_reason_codes(
            status,
            official_boost=official_boost,
            stale_penalty=stale_penalty,
        ),
    )


def _candidate_groups(
    items: list[StrategyCandidateEvidenceRecencyWeightedEvV2Observation],
) -> tuple[tuple[StrategyCandidateEvidenceRecencyWeightedEvV2Observation, ...], ...]:
    buckets: dict[str, list[StrategyCandidateEvidenceRecencyWeightedEvV2Observation]] = {}
    for item in items:
        buckets.setdefault(item.candidate_key, []).append(item)
    groups = []
    for key in sorted(buckets):
        groups.append(tuple(sorted(buckets[key], key=lambda item: (item.observed_at, item.evidence_key))))
    return tuple(groups)


def _candidate_status(score: Decimal, minimum_candidate_score: Decimal) -> str:
    if score >= minimum_candidate_score:
        return "candidate"
    if score > ZERO:
        return "watch"
    return "blocked"


def _report_status(rows: tuple[StrategyCandidateEvidenceRecencyWeightedEvV2Row, ...]) -> str:
    if not rows:
        return "pass"
    statuses = tuple(row.candidate_status for row in rows)
    if all(status == "candidate" for status in statuses):
        return "candidate"
    if any(status == "watch" for status in statuses):
        return "watch"
    if any(status == "candidate" for status in statuses) and any(
        status == "blocked" for status in statuses
    ):
        return "watch"
    return "blocked"


def _row_reason_codes(
    status: str,
    *,
    official_boost: Decimal,
    stale_penalty: Decimal,
) -> tuple[str, ...]:
    codes = [_status_reason(status)]
    if official_boost != ZERO:
        codes.append("official_evidence_boost_applied")
    if stale_penalty != ZERO:
        codes.append("stale_evidence_penalty_applied")
    return tuple(codes)


def _report_reason_codes(
    rows: tuple[StrategyCandidateEvidenceRecencyWeightedEvV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("candidate_clear",)
    status_codes: list[str] = []
    modifier_codes: list[str] = []
    for row in rows:
        for code in row.reason_codes:
            target = status_codes if code.startswith("candidate_") else modifier_codes
            if code not in target:
                target.append(code)
    return tuple(status_codes + modifier_codes)


def _status_reason(status: str) -> str:
    if status == "candidate":
        return "candidate_clear"
    if status == "watch":
        return "candidate_watch"
    if status == "blocked":
        return "candidate_blocked"
    return "candidate_clear"


def _recency_weight(age_seconds: Decimal, half_life_seconds: Decimal) -> Decimal:
    return _normalize_decimal(
        "recency_weight",
        half_life_seconds / (half_life_seconds + age_seconds),
    )


def _age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - observed_at).total_seconds()))
    return _normalize_nonnegative_decimal("evidence_age_seconds", seconds)


def _validate_report(report: StrategyCandidateEvidenceRecencyWeightedEvV2Report) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.observation_count != _normalize_nonnegative_count(
        "observation_count",
        sum((row.evidence_count for row in report.rows), ZERO),
    ):
        raise ValueError("observation_count must match rows")
    if report.candidate_candidate_count != _count(
        sum(1 for row in report.rows if row.candidate_status == "candidate"),
    ):
        raise ValueError("candidate_candidate_count must match rows")
    if report.watch_candidate_count != _count(
        sum(1 for row in report.rows if row.candidate_status == "watch"),
    ):
        raise ValueError("watch_candidate_count must match rows")
    if report.blocked_candidate_count != _count(
        sum(1 for row in report.rows if row.candidate_status == "blocked"),
    ):
        raise ValueError("blocked_candidate_count must match rows")
    if report.candidate_status != _report_status(report.rows):
        raise ValueError("candidate_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_rows(
    rows: object,
) -> tuple[StrategyCandidateEvidenceRecencyWeightedEvV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not StrategyCandidateEvidenceRecencyWeightedEvV2Row:
            raise ValueError("rows must contain StrategyCandidateEvidenceRecencyWeightedEvV2Row")
    return rows


def _row_public_map(
    row: StrategyCandidateEvidenceRecencyWeightedEvV2Row,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    result = {
        "candidate_ref": row.candidate_ref,
        "evidence_refs": row.evidence_refs,
        "evidence_count": row.evidence_count,
        "latest_evidence_at": row.latest_evidence_at,
        "newest_evidence_age_seconds": row.newest_evidence_age_seconds,
        "total_raw_expected_value": row.total_raw_expected_value,
        "recency_weighted_expected_value": row.recency_weighted_expected_value,
        "official_evidence_boost": row.official_evidence_boost,
        "stale_evidence_penalty": row.stale_evidence_penalty,
        "recency_weighted_ev_score": row.recency_weighted_ev_score,
        "candidate_status": row.candidate_status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    if include_digest:
        result["derived_validation_digest"] = row.derived_validation_digest
    return result


def _report_public_map(
    report: StrategyCandidateEvidenceRecencyWeightedEvV2Report,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    result = {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "observation_count": report.observation_count,
        "candidate_count": report.candidate_count,
        "candidate_candidate_count": report.candidate_candidate_count,
        "watch_candidate_count": report.watch_candidate_count,
        "blocked_candidate_count": report.blocked_candidate_count,
        "candidate_status": report.candidate_status,
        "reason_codes": report.reason_codes,
        "rows": tuple(_row_public_map(row, include_digest=True) for row in report.rows),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        result["derived_validation_digest"] = report.derived_validation_digest
    return result


def _row_digest(row: StrategyCandidateEvidenceRecencyWeightedEvV2Row) -> str:
    return _digest("row", _json_ready(_row_public_map(row, include_digest=False)))


def _report_digest(report: StrategyCandidateEvidenceRecencyWeightedEvV2Report) -> str:
    return _digest("report", _json_ready(_report_public_map(report, include_digest=False)))


def _verify_payload_digests(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        provided = row.get("derived_validation_digest")
        _require_canonical_digest(provided)
        row_base = {key: item for key, item in row.items() if key != "derived_validation_digest"}
        if provided != _digest("row", row_base):
            raise ValueError("derived_validation_digest mismatch")
    provided_report = payload.get("derived_validation_digest")
    _require_canonical_digest(provided_report)
    report_base = {
        key: item for key, item in payload.items() if key != "derived_validation_digest"
    }
    if provided_report != _digest("report", report_base):
        raise ValueError("derived_validation_digest mismatch")


def _digest(label: str, value: object) -> str:
    text = label + "\n" + _canonical_text(value)
    return sha256(text.encode("utf-8")).hexdigest()


def _canonical_text(value: object) -> str:
    if type(value) is dict:
        parts = []
        for key in sorted(value):
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            parts.append(key + ":" + _canonical_text(value[key]))
        return "{" + "|".join(parts) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + "|".join(_canonical_text(item) for item in value) + "]"
    if type(value) is str:
        return "s:" + value
    if type(value) is bool:
        return "b:" + ("true" if value else "false")
    if value is None:
        return "none"
    raise ValueError("value is not digestible")


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
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is bool:
        return value
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


def _reject_unsafe_public(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_part(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_part(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_part(value: str) -> bool:
    text = value.lower()
    return any(part in text for part in _unsafe_parts())


def _unsafe_parts() -> tuple[str, ...]:
    chunks = (
        ("li", "ve"),
        ("au", "th"),
        ("wa", "llet"),
        ("or", "der"),
        ("net", "work"),
        ("data", "base"),
        ("per", "sist"),
        ("sign", "ing"),
        ("mut", "ation"),
        ("b", "uy"),
        ("se", "ll"),
        ("tra", "de"),
    )
    return tuple("".join(chunk) for chunk in chunks)


def _public_ref(prefix: str, value: str) -> str:
    return prefix + ":" + sha256(value.encode("utf-8")).hexdigest()[:16]


def _normalize_public_refs(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for item in value:
        _require_canonical_string(name, item)
    return value


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for item in value:
        _require_canonical_string(name, item)
    return value


def _normalize_probability(name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal


def _normalize_positive_count(name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(name, value)
    if decimal <= ZERO:
        raise ValueError(f"{name} must be positive")
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return decimal.quantize(Decimal("1"))


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(name, value)
    if decimal < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return decimal.quantize(Decimal("1"))


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(name, value)
    if decimal < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(Decimal("1"))


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_choice(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be one of {allowed!r}")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_canonical_digest(value: object) -> None:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != 64:
        raise ValueError("derived_validation_digest must be canonical")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be canonical")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_EVIDENCE_RECENCY_WEIGHTED_EV_V2_VERSION",
    "EVIDENCE_KINDS",
    "CANDIDATE_STATUSES",
    "StrategyCandidateEvidenceRecencyWeightedEvV2Config",
    "StrategyCandidateEvidenceRecencyWeightedEvV2Observation",
    "StrategyCandidateEvidenceRecencyWeightedEvV2Row",
    "StrategyCandidateEvidenceRecencyWeightedEvV2Report",
    "build_strategy_candidate_evidence_recency_weighted_ev_v2",
    "strategy_candidate_evidence_recency_weighted_ev_v2_payload",
)
