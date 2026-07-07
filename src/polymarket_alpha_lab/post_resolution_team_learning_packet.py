"""Pure post-resolution learning packet builder for specialist teams."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from decimal import Decimal
from typing import Any, Iterable


LEARNING_STATUSES = ("pass", "watch", "block")

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_ONE = Decimal("1.000000")
METRIC_SEMANTICS = {
    "calibration_error": "abs(forecast_probability - resolved_outcome_probability)",
    "market_team_delta": "forecast_probability - market_probability",
}
CALIBRATION_WATCH_THRESHOLD = Decimal("0.100000")
CALIBRATION_BLOCK_THRESHOLD = Decimal("0.250000")
QUALITY_WATCH_FLOOR = Decimal("0.700000")
QUALITY_BLOCK_FLOOR = Decimal("0.500000")
COST_DRAG_WATCH_THRESHOLD = Decimal("0.020000")
COST_DRAG_BLOCK_THRESHOLD = Decimal("0.050000")
SAFE_LABEL_CHARACTERS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.:-",
)

UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "credential",
        "au" "th",
        "database",
        "dsn",
        "marketid",
        "private" " key",
        "private-key",
        "private",
        "private token",
        "key material",
        "token",
        "secret",
        "wa" "llet",
        "ac" "count",
        "balance",
        "buy",
        "sell",
        "recommend",
        "recommendation",
        "position sizing",
        "position-sizing",
        "position_sizing",
        "source-text",
        "source_text",
        "sourcetext",
        "trade ticket",
        "trade surface",
        "order surface",
        "order submit",
        "submit order",
        "order-submit",
        "submit-order",
        "order_submit",
        "submit_order",
        "order sign",
        "sign order",
        "order-sign",
        "sign-order",
        "order_sign",
        "sign_order",
        "exchange mutation",
        "place" " order",
        "cancel" " order",
        "replace" " order",
        "sig" "ning",
        "sl" "ug",
    ),
)
UNSAFE_FIELD_FRAGMENTS = frozenset(
    (
        "credential",
        "au" "th",
        "database",
        "dsn",
        "table",
        "marketid",
        "private" "_key",
        "private-key",
        "private",
        "private" "_token",
        "key_material",
        "secret",
        "wa" "llet",
        "ac" "count",
        "token",
        "balance",
        "buy",
        "sell",
        "recommend",
        "recommendation",
        "position_sizing",
        "source" "_text",
        "source" "text",
        "trade_ticket",
        "trade_surface",
        "order_surface",
        "order_submit",
        "submit_order",
        "order_sign",
        "sign_order",
        "order",
        "trade",
        "exchange_mutation",
        "place" "_order",
        "cancel" "_order",
        "replace" "_order",
        "sig" "ning",
        "signed" "_payload",
        "market" "_id",
        "ques" "tion",
        "source" "_ref",
        "source" "_url",
    ),
)
UNSAFE_PUBLIC_PAYLOAD_FIELD_FRAGMENTS = frozenset(
    (
        "team_id",
        "candidate_id",
        "candidate_reference",
        "resolved_at",
        "market" "_id",
        "market" "_sl" "ug",
        "sl" "ug",
        "ques" "tion",
        "source" "_ref",
        "source" "_url",
        "source" "_reference",
    ),
)
PUBLIC_PAYLOAD_FIELDS = frozenset(
    (
        "report_status",
        "row_count",
        "status_counts",
        "reason_counts",
        "hard_flag_counts",
        "next_memory_action_counts",
        "average_calibration_error",
        "average_forecast_minus_market_probability_delta",
        "average_absolute_forecast_minus_market_probability_delta",
        "average_evidence_quality_score",
        "average_resolution_quality_score",
        "average_cost_drag",
        "metric_semantics",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
PUBLIC_AVERAGE_FIELDS = frozenset(
    (
        "average_calibration_error",
        "average_forecast_minus_market_probability_delta",
        "average_absolute_forecast_minus_market_probability_delta",
        "average_evidence_quality_score",
        "average_resolution_quality_score",
        "average_cost_drag",
    ),
)
NONNEGATIVE_PUBLIC_AVERAGE_FIELDS = PUBLIC_AVERAGE_FIELDS - frozenset(
    ("average_forecast_minus_market_probability_delta",),
)
PUBLIC_HARD_FLAGS = (
    "cost_drag_above_floor",
    "evidence_quality_below_floor",
    "resolution_quality_below_floor",
    "severe_calibration_error",
)
PUBLIC_NEXT_MEMORY_ACTIONS = (
    "debias_overconfidence_memory",
    "debias_underconfidence_memory",
    "quarantine_low_quality_resolution",
    "reinforce_team_memory",
    "review_evidence_resolution_memory",
    "review_probability_memory",
    "tighten_cost_drag_memory",
)
PUBLIC_REASON_CODE_CHARACTERS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789_",
)
UNSAFE_PUBLIC_REASON_CODE_FRAGMENTS = frozenset(
    (
        "candidate",
        "au" "th",
        "database",
        "dsn",
        "table",
        "marketid",
        "market" "sl" "ug",
        "token",
        "private",
        "ac" "count",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "recommendation",
        "position_sizing",
        "position" "-sizing",
        "market" "_",
        "market" "-",
        "market" ":",
        "ques" "tion",
        "sl" "ug",
        "source" "_ref",
        "source" "-ref",
        "source" ":",
        "source" "_url",
        "source" "-url",
        "sourceurl",
        "source" "_text",
        "source" "-text",
        "source" "text",
        "source" "_reference",
        "source" "-reference",
        "team_id",
        "_url",
    ),
)


@dataclass(frozen=True)
class PostResolutionTeamLearningFact:
    team_id: str
    candidate_reference: str
    forecast_probability: Decimal
    market_probability: Decimal
    resolved_outcome_probability: Decimal
    evidence_quality_score: Decimal
    resolution_quality_score: Decimal
    cost_drag: Decimal
    reason_codes: tuple[str, ...]
    resolved_at: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PostResolutionTeamLearningFact:
            raise TypeError("PostResolutionTeamLearningFact does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PostResolutionTeamLearningFact:
            raise ValueError(
                "learning_fact must be exactly PostResolutionTeamLearningFact",
            )
        object.__setattr__(self, "team_id", _safe_label("team_id", self.team_id))
        object.__setattr__(
            self,
            "candidate_reference",
            _safe_redacted_reference(
                "candidate_reference",
                self.candidate_reference,
            ),
        )
        for field_name in (
            "forecast_probability",
            "market_probability",
            "resolved_outcome_probability",
            "evidence_quality_score",
            "resolution_quality_score",
            "cost_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal_between_zero_and_one(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _safe_reason_code_tuple("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "resolved_at",
            _safe_label("resolved_at", self.resolved_at),
        )
        _require_flags("learning_fact", self)
        _reject_unsafe_payload("learning_fact", self)


@dataclass(frozen=True)
class PostResolutionTeamLearningRow:
    team_id: str
    candidate_reference: str
    resolved_at: str
    forecast_probability: Decimal
    market_probability: Decimal
    resolved_outcome_probability: Decimal
    evidence_quality_score: Decimal
    resolution_quality_score: Decimal
    cost_drag: Decimal
    calibration_error: Decimal
    market_team_delta: Decimal
    status: str
    reason_codes: tuple[str, ...]
    hard_flags: tuple[str, ...]
    next_memory_action: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PostResolutionTeamLearningRow:
            raise TypeError("PostResolutionTeamLearningRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PostResolutionTeamLearningRow:
            raise ValueError("learning_row must be exactly PostResolutionTeamLearningRow")
        for field_name in ("team_id", "candidate_reference", "resolved_at"):
            if field_name == "candidate_reference":
                value = _safe_redacted_reference(field_name, getattr(self, field_name))
            else:
                value = _safe_label(field_name, getattr(self, field_name))
            object.__setattr__(self, field_name, value)
        for field_name in (
            "forecast_probability",
            "market_probability",
            "resolved_outcome_probability",
            "evidence_quality_score",
            "resolution_quality_score",
            "cost_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal_between_zero_and_one(field_name, getattr(self, field_name)),
            )
        for field_name in ("calibration_error", "market_team_delta"):
            object.__setattr__(
                self,
                field_name,
                _finite_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "status",
            _require_member("status", self.status, LEARNING_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _safe_reason_code_tuple("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "hard_flags",
            _safe_string_tuple("hard_flags", self.hard_flags),
        )
        object.__setattr__(
            self,
            "next_memory_action",
            _safe_label("next_memory_action", self.next_memory_action),
        )
        _require_flags("learning_row", self)
        _validate_row_consistency(self)
        _reject_unsafe_payload("learning_row", self)


@dataclass(frozen=True)
class PostResolutionTeamLearningReport:
    rows: tuple[PostResolutionTeamLearningRow, ...]
    report_status: str
    reason_counts: tuple[tuple[str, Decimal], ...]
    payload: dict[str, Any] = field(compare=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PostResolutionTeamLearningReport:
            raise TypeError(
                "PostResolutionTeamLearningReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PostResolutionTeamLearningReport:
            raise ValueError(
                "learning_report must be exactly PostResolutionTeamLearningReport",
            )
        object.__setattr__(self, "rows", _learning_row_tuple("rows", self.rows))
        object.__setattr__(
            self,
            "report_status",
            _require_member("report_status", self.report_status, LEARNING_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_counts",
            _reason_count_tuple("reason_counts", self.reason_counts),
        )
        _require_flags("learning_report", self)
        _validate_report_consistency(self)
        if self.payload != _report_payload(self):
            raise ValueError("payload must match learning report fields")
        _reject_unsafe_payload("payload", self.payload)
        _reject_public_payload_private_fields("payload", self.payload)
        _validate_public_payload_schema("payload", self.payload)


def build_post_resolution_team_learning_packet(
    facts: Iterable[PostResolutionTeamLearningFact],
) -> PostResolutionTeamLearningReport:
    rows = []
    for fact in facts:
        _require_instance("facts", fact, PostResolutionTeamLearningFact)
        rows.append(_row_from_fact(fact))

    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (row.team_id, row.candidate_reference, row.resolved_at),
        ),
    )
    report_status = _report_status(sorted_rows)
    reason_counts = _reason_counts(sorted_rows)
    return _report_from_fields(
        rows=sorted_rows,
        report_status=report_status,
        reason_counts=reason_counts,
    )


def post_resolution_team_learning_packet_payload(
    packet: PostResolutionTeamLearningReport | dict[str, Any],
) -> dict[str, Any]:
    if type(packet) is PostResolutionTeamLearningReport:
        _require_flags("packet", packet)
        _reject_unsafe_payload("packet", packet)
        payload = packet.payload
    elif type(packet) is dict:
        payload = packet
    else:
        raise ValueError("packet must be a PostResolutionTeamLearningReport")

    _require_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload("payload", payload)
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("packet payload must be a JSON object")
    _require_flags("payload", _DictFlags(ready))
    _reject_unsafe_payload("payload", ready)
    _reject_public_payload_private_fields("payload", ready)
    _validate_public_payload_schema("payload", ready)
    return ready


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


def _row_from_fact(
    fact: PostResolutionTeamLearningFact,
) -> PostResolutionTeamLearningRow:
    calibration_error = _abs_decimal(
        fact.forecast_probability - fact.resolved_outcome_probability,
    )
    market_team_delta = fact.forecast_probability - fact.market_probability
    hard_flags = _hard_flags(fact, calibration_error)
    status = _row_status(fact, calibration_error, hard_flags)
    next_memory_action = _next_memory_action(
        fact=fact,
        status=status,
        hard_flags=hard_flags,
    )
    return PostResolutionTeamLearningRow(
        team_id=fact.team_id,
        candidate_reference=fact.candidate_reference,
        resolved_at=fact.resolved_at,
        forecast_probability=fact.forecast_probability,
        market_probability=fact.market_probability,
        resolved_outcome_probability=fact.resolved_outcome_probability,
        evidence_quality_score=fact.evidence_quality_score,
        resolution_quality_score=fact.resolution_quality_score,
        cost_drag=fact.cost_drag,
        calibration_error=calibration_error,
        market_team_delta=market_team_delta,
        status=status,
        reason_codes=fact.reason_codes,
        hard_flags=hard_flags,
        next_memory_action=next_memory_action,
    )


def _report_from_fields(
    *,
    rows: tuple[PostResolutionTeamLearningRow, ...],
    report_status: str,
    reason_counts: tuple[tuple[str, Decimal], ...],
) -> PostResolutionTeamLearningReport:
    payload = _report_payload_from_parts(
        rows=rows,
        report_status=report_status,
        reason_counts=reason_counts,
    )
    return PostResolutionTeamLearningReport(
        rows=rows,
        report_status=report_status,
        reason_counts=reason_counts,
        payload=payload,
    )


def _hard_flags(
    fact: PostResolutionTeamLearningFact,
    calibration_error: Decimal,
) -> tuple[str, ...]:
    flags = []
    if calibration_error > CALIBRATION_BLOCK_THRESHOLD:
        flags.append("severe_calibration_error")
    if fact.evidence_quality_score < QUALITY_BLOCK_FLOOR:
        flags.append("evidence_quality_below_floor")
    if fact.resolution_quality_score < QUALITY_BLOCK_FLOOR:
        flags.append("resolution_quality_below_floor")
    if fact.cost_drag > COST_DRAG_BLOCK_THRESHOLD:
        flags.append("cost_drag_above_floor")
    return tuple(flags)


def _row_status(
    fact: PostResolutionTeamLearningFact,
    calibration_error: Decimal,
    hard_flags: tuple[str, ...],
) -> str:
    if hard_flags:
        return "block"
    if calibration_error > CALIBRATION_WATCH_THRESHOLD:
        return "watch"
    if fact.evidence_quality_score < QUALITY_WATCH_FLOOR:
        return "watch"
    if fact.resolution_quality_score < QUALITY_WATCH_FLOOR:
        return "watch"
    if fact.cost_drag > COST_DRAG_WATCH_THRESHOLD:
        return "watch"
    return "pass"


def _next_memory_action(
    *,
    fact: PostResolutionTeamLearningFact,
    status: str,
    hard_flags: tuple[str, ...],
) -> str:
    if (
        "evidence_quality_below_floor" in hard_flags
        or "resolution_quality_below_floor" in hard_flags
    ):
        return "quarantine_low_quality_resolution"
    if "severe_calibration_error" in hard_flags:
        if fact.forecast_probability > fact.resolved_outcome_probability:
            return "debias_overconfidence_memory"
        return "debias_underconfidence_memory"
    if "cost_drag_above_floor" in hard_flags or fact.cost_drag > COST_DRAG_WATCH_THRESHOLD:
        return "tighten_cost_drag_memory"
    if (
        fact.evidence_quality_score < QUALITY_WATCH_FLOOR
        or fact.resolution_quality_score < QUALITY_WATCH_FLOOR
    ):
        return "review_evidence_resolution_memory"
    if status == "watch":
        return "review_probability_memory"
    return "reinforce_team_memory"


def _report_status(rows: tuple[PostResolutionTeamLearningRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_counts(
    rows: tuple[PostResolutionTeamLearningRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + COUNT_ONE
    return tuple((reason_code, counts[reason_code]) for reason_code in sorted(counts))


def _status_counts(
    rows: tuple[PostResolutionTeamLearningRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts = []
    for status in LEARNING_STATUSES:
        count = ZERO
        for row in rows:
            if row.status == status:
                count += COUNT_ONE
        if count > ZERO:
            counts.append((status, count))
    return tuple(counts)


def _hard_flag_counts(
    rows: tuple[PostResolutionTeamLearningRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for hard_flag in row.hard_flags:
            counts[hard_flag] = counts.get(hard_flag, ZERO) + COUNT_ONE
    return tuple((hard_flag, counts[hard_flag]) for hard_flag in sorted(counts))


def _next_memory_action_counts(
    rows: tuple[PostResolutionTeamLearningRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        counts[row.next_memory_action] = (
            counts.get(row.next_memory_action, ZERO) + COUNT_ONE
        )
    return tuple((action, counts[action]) for action in sorted(counts))


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_ONE)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    total = ZERO
    for value in values:
        total += value
    return (total / _decimal_count(len(values))).quantize(COUNT_ONE)


def _report_payload(packet: PostResolutionTeamLearningReport) -> dict[str, Any]:
    return _report_payload_from_parts(
        rows=packet.rows,
        report_status=packet.report_status,
        reason_counts=packet.reason_counts,
    )


def _report_payload_from_parts(
    *,
    rows: tuple[PostResolutionTeamLearningRow, ...],
    report_status: str,
    reason_counts: tuple[tuple[str, Decimal], ...],
) -> dict[str, Any]:
    return {
        "report_status": report_status,
        "row_count": _json_ready(_decimal_count(len(rows))),
        "status_counts": [
            {"status": status, "count": _json_ready(count)}
            for status, count in _status_counts(rows)
        ],
        "reason_counts": [
            {"reason_code": reason_code, "count": _json_ready(count)}
            for reason_code, count in reason_counts
        ],
        "hard_flag_counts": [
            {"hard_flag": hard_flag, "count": _json_ready(count)}
            for hard_flag, count in _hard_flag_counts(rows)
        ],
        "next_memory_action_counts": [
            {"next_memory_action": action, "count": _json_ready(count)}
            for action, count in _next_memory_action_counts(rows)
        ],
        "average_calibration_error": _json_ready(
            _average_decimal(tuple(row.calibration_error for row in rows)),
        ),
        "average_forecast_minus_market_probability_delta": _json_ready(
            _average_decimal(tuple(row.market_team_delta for row in rows)),
        ),
        "average_absolute_forecast_minus_market_probability_delta": _json_ready(
            _average_decimal(tuple(_abs_decimal(row.market_team_delta) for row in rows)),
        ),
        "average_evidence_quality_score": _json_ready(
            _average_decimal(tuple(row.evidence_quality_score for row in rows)),
        ),
        "average_resolution_quality_score": _json_ready(
            _average_decimal(tuple(row.resolution_quality_score for row in rows)),
        ),
        "average_cost_drag": _json_ready(
            _average_decimal(tuple(row.cost_drag for row in rows)),
        ),
        "metric_semantics": dict(METRIC_SEMANTICS),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_row_consistency(row: PostResolutionTeamLearningRow) -> None:
    expected_calibration_error = _abs_decimal(
        row.forecast_probability - row.resolved_outcome_probability,
    )
    if row.calibration_error != expected_calibration_error:
        raise ValueError("calibration_error must match forecast and outcome")
    expected_market_team_delta = row.forecast_probability - row.market_probability
    if row.market_team_delta != expected_market_team_delta:
        raise ValueError("market_team_delta must match forecast and market")
    if row.hard_flags != _hard_flags(_fact_from_row(row), row.calibration_error):
        raise ValueError("hard_flags must match learning row metrics")
    if row.status != _row_status(_fact_from_row(row), row.calibration_error, row.hard_flags):
        raise ValueError("status must match learning row metrics")
    if row.next_memory_action != _next_memory_action(
        fact=_fact_from_row(row),
        status=row.status,
        hard_flags=row.hard_flags,
    ):
        raise ValueError("next_memory_action must match learning row metrics")


def _validate_report_consistency(packet: PostResolutionTeamLearningReport) -> None:
    expected_rows = tuple(
        sorted(
            packet.rows,
            key=lambda row: (row.team_id, row.candidate_reference, row.resolved_at),
        ),
    )
    if packet.rows != expected_rows:
        raise ValueError("rows must be sorted by team and candidate reference")
    if packet.report_status != _report_status(packet.rows):
        raise ValueError("report_status must match rows")
    if packet.reason_counts != _reason_counts(packet.rows):
        raise ValueError("reason_counts must match rows")


def _validate_public_payload_schema(label: str, payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} must be a public aggregate payload")
    if frozenset(payload) != PUBLIC_PAYLOAD_FIELDS:
        raise ValueError(f"{label} payload fields must match aggregate schema")

    report_status = _require_member(
        f"{label}.report_status",
        payload["report_status"],
        LEARNING_STATUSES,
    )
    row_count = _public_decimal_string(
        f"{label}.row_count",
        payload["row_count"],
        allow_negative=False,
    )
    if row_count != row_count.to_integral_value():
        raise ValueError(f"{label}.row_count must be a whole Decimal string")

    status_counts = _public_count_entries(
        f"{label}.status_counts",
        payload["status_counts"],
        label_key="status",
        allowed_labels=LEARNING_STATUSES,
        ordered_labels=LEARNING_STATUSES,
    )
    if _entry_count_total(status_counts) != row_count:
        raise ValueError(f"{label} status_counts must sum to row_count")
    if report_status != _public_report_status(status_counts):
        raise ValueError(f"{label}.report_status must match status_counts")

    reason_counts = _public_count_entries(
        f"{label}.reason_counts",
        payload["reason_counts"],
        label_key="reason_code",
        allowed_labels=None,
        ordered_labels=None,
    )
    hard_flag_counts = _public_count_entries(
        f"{label}.hard_flag_counts",
        payload["hard_flag_counts"],
        label_key="hard_flag",
        allowed_labels=PUBLIC_HARD_FLAGS,
        ordered_labels=PUBLIC_HARD_FLAGS,
    )
    action_counts = _public_count_entries(
        f"{label}.next_memory_action_counts",
        payload["next_memory_action_counts"],
        label_key="next_memory_action",
        allowed_labels=PUBLIC_NEXT_MEMORY_ACTIONS,
        ordered_labels=PUBLIC_NEXT_MEMORY_ACTIONS,
    )
    if _entry_count_total(action_counts) != row_count:
        raise ValueError(
            f"{label} next_memory_action_counts must sum to row_count",
        )
    status_count_map = dict(status_counts)
    block_count = status_count_map.get("block", ZERO)
    hard_flag_total = _entry_count_total(hard_flag_counts)
    if block_count == ZERO and hard_flag_total != ZERO:
        raise ValueError(f"{label}.hard_flag_counts must be empty without block rows")
    if block_count != ZERO and hard_flag_total == ZERO:
        raise ValueError(f"{label}.hard_flag_counts must describe block rows")
    _validate_public_action_counts(
        f"{label}.next_memory_action_counts",
        status_count_map,
        action_counts,
    )
    if row_count == ZERO and (reason_counts or hard_flag_counts):
        raise ValueError(f"{label} empty reports must not have aggregate counts")

    for field_name in sorted(PUBLIC_AVERAGE_FIELDS):
        decimal_value = _public_decimal_string(
            f"{label}.{field_name}",
            payload[field_name],
            allow_negative=field_name not in NONNEGATIVE_PUBLIC_AVERAGE_FIELDS,
        )
        if field_name in NONNEGATIVE_PUBLIC_AVERAGE_FIELDS:
            if decimal_value < ZERO or decimal_value > ONE:
                raise ValueError(f"{label}.{field_name} must be between 0 and 1")
        elif decimal_value < -ONE or decimal_value > ONE:
            raise ValueError(f"{label}.{field_name} must be between -1 and 1")
        if row_count == ZERO and decimal_value != ZERO:
            raise ValueError(f"{label}.{field_name} must be zero for empty reports")

    if (
        type(payload["metric_semantics"]) is not dict
        or payload["metric_semantics"] != dict(METRIC_SEMANTICS)
    ):
        raise ValueError(f"{label}.metric_semantics must match public definitions")


def _public_count_entries(
    field_name: str,
    value: object,
    *,
    label_key: str,
    allowed_labels: tuple[str, ...] | None,
    ordered_labels: tuple[str, ...] | None,
) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a public aggregate list")
    entries: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not dict or frozenset(item) != frozenset((label_key, "count")):
            raise ValueError(f"{field_name} entries must be label/count objects")
        if label_key == "reason_code":
            public_label = _safe_public_reason_code(
                f"{field_name}.{label_key}",
                item[label_key],
            )
        elif allowed_labels is None:
            public_label = _safe_label(f"{field_name}.{label_key}", item[label_key])
        else:
            public_label = _require_member(
                f"{field_name}.{label_key}",
                item[label_key],
                allowed_labels,
            )
        if public_label in seen:
            raise ValueError(f"{field_name} must not contain duplicate labels")
        seen.add(public_label)

        count = _public_decimal_string(
            f"{field_name}.count",
            item["count"],
            allow_negative=False,
        )
        if count <= ZERO or count != count.to_integral_value():
            raise ValueError(f"{field_name}.count must be a positive whole Decimal")
        entries.append((public_label, count))

    labels = tuple(label for label, _count in entries)
    if ordered_labels is None:
        if labels != tuple(sorted(labels)):
            raise ValueError(f"{field_name} must be sorted by label")
    else:
        positions = tuple(ordered_labels.index(label) for label in labels)
        if positions != tuple(sorted(positions)):
            raise ValueError(f"{field_name} must use deterministic label order")
    return tuple(entries)


def _validate_public_action_counts(
    field_name: str,
    status_count_map: dict[str, Decimal],
    action_counts: tuple[tuple[str, Decimal], ...],
) -> None:
    row_count = ZERO
    for count in status_count_map.values():
        row_count += count
    action_count_map = dict(action_counts)
    if row_count == ZERO:
        if action_count_map:
            raise ValueError(f"{field_name} must be empty for empty reports")
        return

    if status_count_map.get("pass", ZERO) == row_count:
        if action_count_map != {"reinforce_team_memory": row_count}:
            raise ValueError(f"{field_name} must match pass learning actions")
        return

    if status_count_map.get("block", ZERO) != ZERO:
        if "reinforce_team_memory" in action_count_map:
            raise ValueError(f"{field_name} contains pass-only learning actions")

    if status_count_map.get("block", ZERO) == ZERO:
        block_only_actions = (
            "debias_overconfidence_memory",
            "debias_underconfidence_memory",
            "quarantine_low_quality_resolution",
        )
        if any(action in action_count_map for action in block_only_actions):
            raise ValueError(f"{field_name} contains block-only learning actions")


def _entry_count_total(entries: tuple[tuple[str, Decimal], ...]) -> Decimal:
    total = ZERO
    for _label, count in entries:
        total += count
    return total


def _public_report_status(status_counts: tuple[tuple[str, Decimal], ...]) -> str:
    statuses = tuple(status for status, _count in status_counts)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _public_decimal_string(
    field_name: str,
    value: object,
    *,
    allow_negative: bool,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
        canonical_value = str(decimal_value.quantize(COUNT_ONE))
    except ArithmeticError as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if decimal_value == ZERO:
        canonical_value = str(ZERO)
    if value != canonical_value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    if not allow_negative and decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _safe_public_reason_code(field_name: str, value: object) -> str:
    label = _safe_label(field_name, value)
    if any(character not in PUBLIC_REASON_CODE_CHARACTERS for character in label):
        raise ValueError(f"{field_name} must use public reason-code characters")
    lowered = label.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_REASON_CODE_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public payload value")
    return label


def _fact_from_row(row: PostResolutionTeamLearningRow) -> PostResolutionTeamLearningFact:
    return PostResolutionTeamLearningFact(
        team_id=row.team_id,
        candidate_reference=row.candidate_reference,
        forecast_probability=row.forecast_probability,
        market_probability=row.market_probability,
        resolved_outcome_probability=row.resolved_outcome_probability,
        evidence_quality_score=row.evidence_quality_score,
        resolution_quality_score=row.resolution_quality_score,
        cost_drag=row.cost_drag,
        reason_codes=row.reason_codes,
        resolved_at=row.resolved_at,
    )


def _learning_row_tuple(
    field_name: str,
    value: object,
) -> tuple[PostResolutionTeamLearningRow, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    rows = []
    for item in value:
        _require_instance(field_name, item, PostResolutionTeamLearningRow)
        rows.append(item)
    return tuple(rows)


def _reason_count_tuple(
    field_name: str,
    value: object,
) -> tuple[tuple[str, Decimal], ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    seen: set[str] = set()
    counts = []
    for item in value:
        if type(item) not in (tuple, list) or len(item) != 2:
            raise ValueError(f"{field_name} entries must be reason/count pairs")
        reason_code = _safe_public_reason_code("reason_code", item[0])
        count = _whole_nonnegative_decimal("count", item[1])
        if count == ZERO:
            raise ValueError("count must be positive")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
        counts.append((reason_code, count))
    return tuple(counts)


def _require_instance(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_flags(field_name, value)
    _reject_unsafe_payload(field_name, value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    label = _safe_label(field_name, value)
    if label not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return label


def _safe_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    normalized = tuple(_safe_label(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _safe_reason_code_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    normalized = tuple(_safe_public_reason_code(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _safe_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must be a single-line canonical string")
    if "?" in value:
        raise ValueError(f"{field_name} has unsafe value")
    _reject_unsafe_text(field_name, value)
    if any(character not in SAFE_LABEL_CHARACTERS for character in value):
        raise ValueError(f"{field_name} must use public identifier characters")
    return value


def _safe_redacted_reference(field_name: str, value: object) -> str:
    label = _safe_label(field_name, value)
    if "redacted" not in label.lower():
        raise ValueError(f"{field_name} must be redacted")
    return label


def _decimal_between_zero_and_one(field_name: str, value: object) -> Decimal:
    normalized = _finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return -value
    return value


def _require_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool):
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)
        return
    if isinstance(value, Decimal):
        _finite_decimal(label, value)
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{label} must use Decimal-derived string values")
    if value is None or type(value) is bool:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            lowered = key.lower()
            if any(fragment in lowered for fragment in UNSAFE_FIELD_FRAGMENTS):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            _reject_unsafe_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_payload(label, item)
        return
    raise ValueError("value is not JSON serializable")


def _reject_public_payload_private_fields(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered = key.lower()
            if lowered == "rows" or any(
                fragment in lowered
                for fragment in UNSAFE_PUBLIC_PAYLOAD_FIELD_FRAGMENTS
            ):
                raise ValueError(f"unsafe private field in {label}: {key}")
            _reject_public_payload_private_fields(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload_private_fields(label, item)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe value")


__all__ = (
    "LEARNING_STATUSES",
    "PostResolutionTeamLearningFact",
    "PostResolutionTeamLearningReport",
    "PostResolutionTeamLearningRow",
    "build_post_resolution_team_learning_packet",
    "post_resolution_team_learning_packet_payload",
)
