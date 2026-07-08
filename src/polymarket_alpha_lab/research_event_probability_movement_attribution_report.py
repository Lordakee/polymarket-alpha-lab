"""Pure report-only probability movement attribution reducer."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_EVENT_PROBABILITY_MOVEMENT_ATTRIBUTION_REPORT_CONFIG_VERSION = (
    "research-event-probability-movement-attribution-report"
)

Q = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_ZERO = Decimal("0.000000")
COUNT_ONE = Decimal("1.000000")

ATTRIBUTION_CATEGORIES = frozenset(
    ("fresh_evidence", "book_movement", "unresolved_noise"),
)
MOVEMENT_DIRECTIONS = frozenset(("up", "down", "flat"))
STATUSES = frozenset(("pass", "watch", "block"))
REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "report_status",
        "observation_count",
        "fresh_evidence_count",
        "book_movement_count",
        "unresolved_noise_count",
        "pass_count",
        "watch_count",
        "block_count",
        "total_movement_magnitude",
        "average_movement_magnitude",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "rank",
        "observed_at",
        "probability_before",
        "probability_after",
        "movement_magnitude",
        "movement_direction",
        "fresh_evidence_score",
        "book_movement_score",
        "unresolved_noise_score",
        "latest_fresh_evidence_age_hours",
        "book_midpoint_move",
        "attribution_category",
        "attribution_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
CATEGORY_PRIORITY = {
    "fresh_evidence": 0,
    "book_movement": 1,
    "unresolved_noise": 2,
}
REASON_PRIORITY = {
    "movement_below_materiality": 0,
    "movement_material": 1,
    "fresh_evidence_dominant": 2,
    "book_movement_dominant": 3,
    "unresolved_noise_dominant": 4,
    "book_movement_material": 5,
    "attribution_ambiguous": 6,
    "attribution_resolved": 7,
    "attribution_unresolved": 8,
    "attribution_blocked": 9,
}
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candi" + "date",
        "mark" + "et",
        "sl" + "ug",
        "ques" + "tion",
        "sou" + "rce_url",
        "sou" + "rce_text",
        "d" + "sn",
        "tab" + "le",
        "tok" + "en",
        "li" + "ve",
        "au" + "th",
        "wal" + "let",
        "or" + "der",
        "net" + "work",
        "data" + "base",
        "sign" + "ing",
        "b" + "uy",
        "se" + "ll",
        "tra" + "ding",
        "si" + "zing",
        "recom" + "mendation",
    ),
)


@dataclass(frozen=True)
class ResearchEventProbabilityMovementAttributionConfig:
    config_version: str
    material_probability_move_threshold: Decimal
    attribution_score_threshold: Decimal
    attribution_dominance_threshold: Decimal
    fresh_evidence_max_age_hours: Decimal
    book_movement_min_magnitude: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventProbabilityMovementAttributionConfig:
            raise ValueError("config must be exactly probability movement attribution config")
        _config_version(self.config_version)
        for name in (
            "material_probability_move_threshold",
            "attribution_score_threshold",
            "attribution_dominance_threshold",
            "book_movement_min_magnitude",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        object.__setattr__(
            self,
            "fresh_evidence_max_age_hours",
            _dec_positive(
                "fresh_evidence_max_age_hours",
                self.fresh_evidence_max_age_hours,
            ),
        )
        if self.attribution_dominance_threshold > self.attribution_score_threshold:
            raise ValueError(
                "attribution_dominance_threshold must not exceed "
                "attribution_score_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventProbabilityMovementAttributionObservation:
    observed_at: datetime
    probability_before: Decimal
    probability_after: Decimal
    fresh_evidence_score: Decimal
    book_movement_score: Decimal
    unresolved_noise_score: Decimal
    latest_fresh_evidence_age_hours: Decimal
    book_midpoint_move: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventProbabilityMovementAttributionObservation:
            raise ValueError(
                "observation must be exactly probability movement attribution observation",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in ("probability_before", "probability_after"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        for name in (
            "fresh_evidence_score",
            "book_movement_score",
            "unresolved_noise_score",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        object.__setattr__(
            self,
            "latest_fresh_evidence_age_hours",
            _dec_nonnegative(
                "latest_fresh_evidence_age_hours",
                self.latest_fresh_evidence_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "book_midpoint_move",
            _ratio("book_midpoint_move", self.book_midpoint_move),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventProbabilityMovementAttributionRow:
    rank: Decimal
    observed_at: datetime
    probability_before: Decimal
    probability_after: Decimal
    movement_magnitude: Decimal
    movement_direction: str
    fresh_evidence_score: Decimal
    book_movement_score: Decimal
    unresolved_noise_score: Decimal
    latest_fresh_evidence_age_hours: Decimal
    book_midpoint_move: Decimal
    attribution_category: str
    attribution_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventProbabilityMovementAttributionRow:
            raise ValueError("row must be exactly probability movement attribution row")
        object.__setattr__(self, "rank", _count_positive("rank", self.rank))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in ("probability_before", "probability_after", "movement_magnitude"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        _member("movement_direction", self.movement_direction, MOVEMENT_DIRECTIONS)
        for name in (
            "fresh_evidence_score",
            "book_movement_score",
            "unresolved_noise_score",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        object.__setattr__(
            self,
            "latest_fresh_evidence_age_hours",
            _dec_nonnegative(
                "latest_fresh_evidence_age_hours",
                self.latest_fresh_evidence_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "book_midpoint_move",
            _ratio("book_midpoint_move", self.book_midpoint_move),
        )
        _member("attribution_category", self.attribution_category, ATTRIBUTION_CATEGORIES)
        _member("attribution_status", self.attribution_status, STATUSES)
        object.__setattr__(self, "reason_codes", _reason_codes(self.reason_codes))
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventProbabilityMovementAttributionReport:
    generated_at: datetime
    config_version: str
    report_status: str
    observation_count: Decimal
    fresh_evidence_count: Decimal
    book_movement_count: Decimal
    unresolved_noise_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_movement_magnitude: Decimal
    average_movement_magnitude: Decimal
    rows: tuple[ResearchEventProbabilityMovementAttributionRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventProbabilityMovementAttributionReport:
            raise ValueError("report must be exactly probability movement attribution report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _config_version(self.config_version)
        _member("report_status", self.report_status, STATUSES)
        for name in (
            "observation_count",
            "fresh_evidence_count",
            "book_movement_count",
            "unresolved_noise_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        for name in ("total_movement_magnitude", "average_movement_magnitude"):
            object.__setattr__(self, name, _dec_nonnegative(name, getattr(self, name)))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _hex_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_digest(self)
        _report_matches(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_probability_movement_attribution_report_payload(self)


def build_research_event_probability_movement_attribution_report(
    observations: Iterable[ResearchEventProbabilityMovementAttributionObservation],
    *,
    config: ResearchEventProbabilityMovementAttributionConfig,
    generated_at: datetime,
) -> ResearchEventProbabilityMovementAttributionReport:
    if type(config) is not ResearchEventProbabilityMovementAttributionConfig:
        raise ValueError("config must be a probability movement attribution config")
    _require_hard_flags("config", config)
    stamp = _as_utc("generated_at", generated_at)
    input_rows = _normalize_observations(observations)
    for item in input_rows:
        if item.observed_at > stamp:
            raise ValueError("observed_at must not be after generated_at")
    rows = _ranked_rows(tuple(_row(item, config) for item in input_rows))
    total_magnitude = sum((row.movement_magnitude for row in rows), ZERO)
    values = {
        "generated_at": stamp,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "observation_count": _count_from_int(len(rows)),
        "fresh_evidence_count": _category_count(rows, "fresh_evidence"),
        "book_movement_count": _category_count(rows, "book_movement"),
        "unresolved_noise_count": _category_count(rows, "unresolved_noise"),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "total_movement_magnitude": _q(total_magnitude),
        "average_movement_magnitude": _average(
            tuple(row.movement_magnitude for row in rows),
        ),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventProbabilityMovementAttributionReport(
        **values,
        derived_validation_digest=_derive_digest_from_public_payload(_payload(values)),
    )


def research_event_probability_movement_attribution_report_payload(
    report: ResearchEventProbabilityMovementAttributionReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventProbabilityMovementAttributionReport:
        _require_hard_flags("report", report)
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a probability movement attribution report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_supported_payload(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _require_payload_digest(payload)
    _require_payload_report_matches(
        payload,
        tuple(_row_from_payload(row) for row in _payload_rows(payload)),
    )
    return payload


def derive_research_event_probability_movement_attribution_report_digest(
    report: ResearchEventProbabilityMovementAttributionReport | dict[str, Any],
) -> str:
    if type(report) is ResearchEventProbabilityMovementAttributionReport:
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a probability movement attribution report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_supported_payload(payload, digest_required=False)
    _require_hard_flags("payload", _DictFlags(payload))
    return _derive_digest_from_public_payload(payload)


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


def _row(
    item: ResearchEventProbabilityMovementAttributionObservation,
    config: ResearchEventProbabilityMovementAttributionConfig,
) -> ResearchEventProbabilityMovementAttributionRow:
    magnitude = _movement_magnitude(item.probability_before, item.probability_after)
    direction = _movement_direction(item.probability_before, item.probability_after)
    category, status, dominant = _attribution(item, magnitude, config)
    return ResearchEventProbabilityMovementAttributionRow(
        rank=COUNT_ONE,
        observed_at=item.observed_at,
        probability_before=item.probability_before,
        probability_after=item.probability_after,
        movement_magnitude=magnitude,
        movement_direction=direction,
        fresh_evidence_score=item.fresh_evidence_score,
        book_movement_score=item.book_movement_score,
        unresolved_noise_score=item.unresolved_noise_score,
        latest_fresh_evidence_age_hours=item.latest_fresh_evidence_age_hours,
        book_midpoint_move=item.book_midpoint_move,
        attribution_category=category,
        attribution_status=status,
        reason_codes=_reason_codes_for_attribution(category, status, dominant),
    )


def _attribution(
    item: ResearchEventProbabilityMovementAttributionObservation,
    magnitude: Decimal,
    config: ResearchEventProbabilityMovementAttributionConfig,
) -> tuple[str, str, bool]:
    if magnitude < config.material_probability_move_threshold:
        return "unresolved_noise", "block", False
    fresh_score = (
        item.fresh_evidence_score
        if item.latest_fresh_evidence_age_hours <= config.fresh_evidence_max_age_hours
        else ZERO
    )
    book_score = (
        item.book_movement_score
        if item.book_midpoint_move >= config.book_movement_min_magnitude
        else ZERO
    )
    scored = tuple(
        sorted(
            (
                (fresh_score, "fresh_evidence"),
                (book_score, "book_movement"),
                (item.unresolved_noise_score, "unresolved_noise"),
            ),
            key=lambda value: (-value[0], CATEGORY_PRIORITY[value[1]]),
        ),
    )
    top_score, category = scored[0]
    second_score = scored[1][0]
    dominant = (
        top_score >= config.attribution_score_threshold
        and _q(top_score - second_score) >= config.attribution_dominance_threshold
    )
    if not dominant:
        return "unresolved_noise", "watch", False
    if category == "unresolved_noise":
        return category, "watch", True
    return category, "pass", True


def _reason_codes_for_attribution(
    category: str,
    status: str,
    dominant: bool,
) -> tuple[str, ...]:
    if status == "block":
        return ("movement_below_materiality", "attribution_blocked")
    reasons = ["movement_material"]
    if dominant:
        reasons.append(f"{category}_dominant")
        if category == "book_movement":
            reasons.append("book_movement_material")
    else:
        reasons.append("attribution_ambiguous")
    if status == "pass":
        reasons.append("attribution_resolved")
    else:
        reasons.append("attribution_unresolved")
    return _reason_codes(tuple(reasons))


def _ranked_rows(
    rows: tuple[ResearchEventProbabilityMovementAttributionRow, ...],
) -> tuple[ResearchEventProbabilityMovementAttributionRow, ...]:
    ranked = []
    for index, row in enumerate(sorted(rows, key=_row_key), start=1):
        ranked.append(
            ResearchEventProbabilityMovementAttributionRow(
                rank=_count_from_int(index),
                observed_at=row.observed_at,
                probability_before=row.probability_before,
                probability_after=row.probability_after,
                movement_magnitude=row.movement_magnitude,
                movement_direction=row.movement_direction,
                fresh_evidence_score=row.fresh_evidence_score,
                book_movement_score=row.book_movement_score,
                unresolved_noise_score=row.unresolved_noise_score,
                latest_fresh_evidence_age_hours=row.latest_fresh_evidence_age_hours,
                book_midpoint_move=row.book_midpoint_move,
                attribution_category=row.attribution_category,
                attribution_status=row.attribution_status,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked)


def _row_key(row: ResearchEventProbabilityMovementAttributionRow) -> tuple[object, ...]:
    return (
        -row.movement_magnitude,
        CATEGORY_PRIORITY[row.attribution_category],
        row.attribution_status,
        row.observed_at,
        row.probability_before,
        row.probability_after,
        row.fresh_evidence_score,
        row.book_movement_score,
        row.unresolved_noise_score,
        row.latest_fresh_evidence_age_hours,
        row.book_midpoint_move,
    )


def _movement_magnitude(before: Decimal, after: Decimal) -> Decimal:
    return _q(abs(after - before))


def _movement_direction(before: Decimal, after: Decimal) -> str:
    if after > before:
        return "up"
    if after < before:
        return "down"
    return "flat"


def _report_status(
    rows: tuple[ResearchEventProbabilityMovementAttributionRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.attribution_status == "block" for row in rows):
        return "block"
    if any(row.attribution_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _category_count(
    rows: tuple[ResearchEventProbabilityMovementAttributionRow, ...],
    category: str,
) -> Decimal:
    return _count_from_int(sum(1 for row in rows if row.attribution_category == category))


def _status_count(
    rows: tuple[ResearchEventProbabilityMovementAttributionRow, ...],
    status: str,
) -> Decimal:
    return _count_from_int(sum(1 for row in rows if row.attribution_status == status))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _q(sum(values, ZERO) / Decimal(len(values)))


def _validate_row(row: ResearchEventProbabilityMovementAttributionRow) -> None:
    if row.movement_magnitude != _movement_magnitude(
        row.probability_before,
        row.probability_after,
    ):
        raise ValueError("movement_magnitude must match probability movement")
    if row.movement_direction != _movement_direction(
        row.probability_before,
        row.probability_after,
    ):
        raise ValueError("movement_direction must match probability movement")
    if row.attribution_status == "pass":
        if row.attribution_category == "unresolved_noise":
            raise ValueError("pass status must have a resolved attribution category")
        if "attribution_resolved" not in row.reason_codes:
            raise ValueError("pass status must include attribution_resolved")
    if row.attribution_status == "watch":
        if row.attribution_category != "unresolved_noise":
            raise ValueError("watch status must use unresolved_noise")
        if "attribution_unresolved" not in row.reason_codes:
            raise ValueError("watch status must include attribution_unresolved")
    if row.attribution_status == "block" and "attribution_blocked" not in row.reason_codes:
        raise ValueError("block status must include attribution_blocked")


def _report_matches(report: ResearchEventProbabilityMovementAttributionReport) -> None:
    rows = report.rows
    values = _report_counts_and_measures(rows)
    for name, expected in values.items():
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    expected_ranks = tuple(_count_from_int(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("row ranks must be sequential")


def _report_counts_and_measures(
    rows: tuple[ResearchEventProbabilityMovementAttributionRow, ...],
) -> dict[str, Decimal]:
    total = _q(sum((row.movement_magnitude for row in rows), ZERO))
    return {
        "observation_count": _count_from_int(len(rows)),
        "fresh_evidence_count": _category_count(rows, "fresh_evidence"),
        "book_movement_count": _category_count(rows, "book_movement"),
        "unresolved_noise_count": _category_count(rows, "unresolved_noise"),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "total_movement_magnitude": total,
        "average_movement_magnitude": _average(
            tuple(row.movement_magnitude for row in rows),
        ),
    }


def _validate_digest(report: ResearchEventProbabilityMovementAttributionReport) -> None:
    if report.derived_validation_digest != _derive_digest_from_public_payload(
        _payload(report),
    ):
        raise ValueError("derived_validation_digest must match report payload")


def _require_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _hex_digest("derived_validation_digest", digest)
    if digest != _derive_digest_from_public_payload(payload):
        raise ValueError("derived_validation_digest must match report payload")


def _derive_digest_from_public_payload(payload: dict[str, Any]) -> str:
    core = {
        key: item
        for key, item in payload.items()
        if key != "derived_validation_digest"
    }
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _payload(value: Any) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        text = value.astimezone(UTC).isoformat()
        if text.endswith("+00:00"):
            return text[:-6] + "Z"
        return text
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload(item) for item in value]
    if isinstance(value, list):
        return [_payload(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _payload(item)
            for key, item in value.items()
        }
    return value


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(_payload(value))
    if type(value) is bool or value is None or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if isinstance(value, float):
        raise ValueError("JSON numeric value must use Decimal strings")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _unsafe_text(key):
                raise ValueError("unsafe public payload key")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _unsafe_text(value):
        raise ValueError("unsafe public payload value")


def _require_supported_payload(
    payload: dict[str, Any],
    *,
    digest_required: bool = True,
) -> None:
    expected_report_fields = set(REPORT_PAYLOAD_FIELDS)
    allowed_report_fields = set(REPORT_PAYLOAD_FIELDS)
    if not digest_required:
        expected_report_fields.remove("derived_validation_digest")
    if set(payload) - allowed_report_fields:
        raise ValueError("payload field is not supported")
    if expected_report_fields - set(payload):
        raise ValueError("payload field is missing")
    _require_payload_report_values(payload, digest_required=digest_required)
    rows = _payload_rows(payload)
    for row in rows:
        if set(row) != set(ROW_PAYLOAD_FIELDS):
            raise ValueError("payload field is missing")
        _require_payload_row_values(row)
        _require_hard_flags("row payload", _DictFlags(row))


def _require_payload_report_values(
    payload: dict[str, Any],
    *,
    digest_required: bool,
) -> None:
    _payload_datetime(payload.get("generated_at"))
    if (
        payload.get("config_version")
        != DEFAULT_RESEARCH_EVENT_PROBABILITY_MOVEMENT_ATTRIBUTION_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version is not supported")
    _payload_member("report_status", payload.get("report_status"), STATUSES)
    for name in (
        "observation_count",
        "fresh_evidence_count",
        "book_movement_count",
        "unresolved_noise_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        _payload_count_decimal(name, payload.get(name))
    for name in ("total_movement_magnitude", "average_movement_magnitude"):
        _payload_nonnegative_decimal(name, payload.get(name))
    if digest_required:
        _hex_digest("derived_validation_digest", payload.get("derived_validation_digest"))


def _require_payload_row_values(row: dict[str, Any]) -> None:
    _payload_count_decimal("rank", row.get("rank"))
    _payload_datetime(row.get("observed_at"))
    for name in (
        "probability_before",
        "probability_after",
        "movement_magnitude",
        "fresh_evidence_score",
        "book_movement_score",
        "unresolved_noise_score",
        "book_midpoint_move",
    ):
        _payload_ratio_decimal(name, row.get(name))
    _payload_nonnegative_decimal(
        "latest_fresh_evidence_age_hours",
        row.get("latest_fresh_evidence_age_hours"),
    )
    _payload_member("movement_direction", row.get("movement_direction"), MOVEMENT_DIRECTIONS)
    _payload_member(
        "attribution_category",
        row.get("attribution_category"),
        ATTRIBUTION_CATEGORIES,
    )
    _payload_member("attribution_status", row.get("attribution_status"), STATUSES)
    reason_codes = row.get("reason_codes")
    if type(reason_codes) is not list:
        raise ValueError("reason_codes must be a list")
    _reason_codes(tuple(reason_codes))


def _payload_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain payload objects")
    return rows


def _row_from_payload(
    row: dict[str, Any],
) -> ResearchEventProbabilityMovementAttributionRow:
    reason_codes = row.get("reason_codes")
    if type(reason_codes) is not list:
        raise ValueError("reason_codes must be a list")
    return ResearchEventProbabilityMovementAttributionRow(
        rank=_payload_count_decimal("rank", row.get("rank")),
        observed_at=_payload_datetime(row.get("observed_at")),
        probability_before=_payload_ratio_decimal("probability_before", row.get("probability_before")),
        probability_after=_payload_ratio_decimal("probability_after", row.get("probability_after")),
        movement_magnitude=_payload_ratio_decimal("movement_magnitude", row.get("movement_magnitude")),
        movement_direction=_payload_member(
            "movement_direction",
            row.get("movement_direction"),
            MOVEMENT_DIRECTIONS,
        ),
        fresh_evidence_score=_payload_ratio_decimal(
            "fresh_evidence_score",
            row.get("fresh_evidence_score"),
        ),
        book_movement_score=_payload_ratio_decimal(
            "book_movement_score",
            row.get("book_movement_score"),
        ),
        unresolved_noise_score=_payload_ratio_decimal(
            "unresolved_noise_score",
            row.get("unresolved_noise_score"),
        ),
        latest_fresh_evidence_age_hours=_payload_nonnegative_decimal(
            "latest_fresh_evidence_age_hours",
            row.get("latest_fresh_evidence_age_hours"),
        ),
        book_midpoint_move=_payload_ratio_decimal(
            "book_midpoint_move",
            row.get("book_midpoint_move"),
        ),
        attribution_category=_payload_member(
            "attribution_category",
            row.get("attribution_category"),
            ATTRIBUTION_CATEGORIES,
        ),
        attribution_status=_payload_member(
            "attribution_status",
            row.get("attribution_status"),
            STATUSES,
        ),
        reason_codes=tuple(reason_codes),
        paper_only=row.get("paper_only"),
        report_only=row.get("report_only"),
        readonly=row.get("readonly"),
    )


def _require_payload_report_matches(
    payload: dict[str, Any],
    rows: tuple[ResearchEventProbabilityMovementAttributionRow, ...],
) -> None:
    expected = _report_counts_and_measures(rows)
    for name, value in expected.items():
        if (
            _payload_count_decimal(name, payload.get(name))
            if name.endswith("_count")
            else _payload_nonnegative_decimal(name, payload.get(name))
        ) != value:
            raise ValueError(f"{name} must match rows")
    if _payload_member("report_status", payload.get("report_status"), STATUSES) != _report_status(rows):
        raise ValueError("report_status must match rows")
    expected_ranks = tuple(_count_from_int(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("row ranks must be sequential")
    if rows != tuple(sorted(rows, key=_row_key)):
        raise ValueError("rows must use deterministic sequence")


def _normalize_observations(
    observations: Iterable[ResearchEventProbabilityMovementAttributionObservation],
) -> tuple[ResearchEventProbabilityMovementAttributionObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        rows = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchEventProbabilityMovementAttributionObservation:
            raise ValueError("observations must contain attribution observations")
        _require_hard_flags("observation", row)
    return rows


def _normalize_rows(
    rows: tuple[ResearchEventProbabilityMovementAttributionRow, ...],
) -> tuple[ResearchEventProbabilityMovementAttributionRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventProbabilityMovementAttributionRow:
            raise ValueError("rows must contain attribution row values")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or value not in REASON_PRIORITY:
            raise ValueError("reason_codes must be supported")
        if value in normalized:
            raise ValueError("reason_codes must be unique")
        normalized.append(value)
    return tuple(sorted(normalized, key=lambda value: REASON_PRIORITY[value]))


def _unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _payload_datetime(value: object) -> datetime:
    if type(value) is not str or not value.endswith("Z"):
        raise ValueError("timestamp must be a UTC string")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(UTC)
    except ValueError as exc:
        raise ValueError("timestamp must be a UTC string") from exc


def _payload_member(name: str, value: object, allowed: frozenset[str]) -> str:
    _member(name, value, allowed)
    return value


def _payload_decimal(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    try:
        return Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc


def _payload_count_decimal(name: str, value: object) -> Decimal:
    result = _count(name, _payload_decimal(name, value))
    if str(result) != value:
        raise ValueError(f"{name} must be a canonical Decimal string")
    return result


def _payload_ratio_decimal(name: str, value: object) -> Decimal:
    result = _ratio(name, _payload_decimal(name, value))
    if str(result) != value:
        raise ValueError(f"{name} must be a canonical Decimal string")
    return result


def _payload_nonnegative_decimal(name: str, value: object) -> Decimal:
    result = _dec_nonnegative(name, _payload_decimal(name, value))
    if str(result) != value:
        raise ValueError(f"{name} must be a canonical Decimal string")
    return result


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _config_version(value: str) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_EVENT_PROBABILITY_MOVEMENT_ATTRIBUTION_REPORT_CONFIG_VERSION:
        raise ValueError("config_version is not supported")


def _hex_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _member(name: str, value: object, allowed: frozenset[str]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} is not supported")


def _dec(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _q(value)


def _dec_nonnegative(name: str, value: Decimal) -> Decimal:
    result = _dec(name, value)
    if result < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return result


def _dec_positive(name: str, value: Decimal) -> Decimal:
    result = _dec(name, value)
    if result <= ZERO:
        raise ValueError(f"{name} must be positive")
    return result


def _ratio(name: str, value: Decimal) -> Decimal:
    result = _dec_nonnegative(name, value)
    if result > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return result


def _count(name: str, value: Decimal) -> Decimal:
    result = _dec(name, value)
    if result < COUNT_ZERO or result != result.to_integral_value():
        raise ValueError(f"{name} must be a nonnegative whole Decimal")
    return result


def _count_positive(name: str, value: Decimal) -> Decimal:
    result = _count(name, value)
    if result <= COUNT_ZERO:
        raise ValueError(f"{name} must be positive")
    return result


def _count_from_int(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(Q)


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} must be readonly")


def _q(value: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 64
        ctx.rounding = ROUND_HALF_EVEN
        return value.quantize(Q)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_PROBABILITY_MOVEMENT_ATTRIBUTION_REPORT_CONFIG_VERSION",
    "ResearchEventProbabilityMovementAttributionConfig",
    "ResearchEventProbabilityMovementAttributionObservation",
    "ResearchEventProbabilityMovementAttributionReport",
    "ResearchEventProbabilityMovementAttributionRow",
    "build_research_event_probability_movement_attribution_report",
    "derive_research_event_probability_movement_attribution_report_digest",
    "research_event_probability_movement_attribution_report_payload",
)
