"""Pure paper/report candidate information-decay expected-value v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from typing import Any, Iterable


DEFAULT_STRATEGY_CANDIDATE_INFORMATION_DECAY_EXPECTED_VALUE_V2_CONFIG_VERSION = (
    "scidev-v2:2026-07-06"
)
SOURCE_TYPES = ("official", "primary", "secondary", "unverified")
ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ROW_STATUSES

QUANTUM = Decimal("0.000001")
SECOND_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SOURCE_TYPE_MULTIPLIERS = {
    "official": Decimal("1.000000"),
    "primary": Decimal("0.900000"),
    "secondary": Decimal("0.750000"),
    "unverified": Decimal("0.500000"),
}
_UNSAFE_TERM_PARTS = (
    ("li", "ve"),
    ("au", "th"),
    ("wal", "let"),
    ("or", "der"),
    ("net", "work"),
    ("data", "base"),
    ("per", "sist"),
    ("sig", "ning"),
    ("muta", "tion"),
    ("b", "uy"),
    ("se", "ll"),
    ("tra", "de"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_ROW_DIGEST_FIELDS = (
    "candidate_id",
    "base_expected_value_bps",
    "source_age_seconds",
    "source_type",
    "source_age_multiplier",
    "source_type_multiplier",
    "contradiction_count",
    "contradiction_multiplier",
    "catalyst_urgency_score",
    "catalyst_urgency_multiplier",
    "settlement_horizon_seconds",
    "settlement_horizon_multiplier",
    "combined_information_multiplier",
    "information_decay_bps",
    "adjusted_expected_value_bps",
    "adjustment_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_DIGEST_FIELDS = (
    "config_version",
    "candidate_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "max_adjusted_expected_value_bps",
    "min_combined_information_multiplier",
    "average_combined_information_multiplier",
    "report_status",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class StrategyCandidateInformationDecayExpectedValueV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_INFORMATION_DECAY_EXPECTED_VALUE_V2_CONFIG_VERSION
    )
    minimum_adjusted_expected_value_bps: Decimal = Decimal("10.000000")
    watch_adjusted_expected_value_bps: Decimal = Decimal("0.000000")
    source_age_half_life_seconds: Decimal = Decimal("3600")
    contradiction_penalty_per_count: Decimal = Decimal("0.100000")
    minimum_contradiction_multiplier: Decimal = Decimal("0.250000")
    catalyst_urgency_decay_ceiling: Decimal = Decimal("0.200000")
    settlement_horizon_half_life_seconds: Decimal = Decimal("604800")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minimum_adjusted_expected_value_bps",
            "watch_adjusted_expected_value_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_age_half_life_seconds",
            "settlement_horizon_half_life_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_penalty_per_count",
            "minimum_contradiction_multiplier",
            "catalyst_urgency_decay_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_adjusted_expected_value_bps > self.minimum_adjusted_expected_value_bps:
            raise ValueError(
                "watch_adjusted_expected_value_bps must be <= "
                "minimum_adjusted_expected_value_bps",
            )
        _require_paper_flags("information decay expected-value config", self)
        reject_strategy_candidate_information_decay_expected_value_v2_unsafe_payload(
            "information decay expected-value config",
            self,
        )


@dataclass(frozen=True)
class StrategyCandidateInformationDecayExpectedValueV2Input:
    candidate_id: str
    base_expected_value_bps: Decimal
    source_age_seconds: Decimal
    source_type: str
    contradiction_count: Decimal
    catalyst_urgency_score: Decimal
    settlement_horizon_seconds: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        object.__setattr__(
            self,
            "base_expected_value_bps",
            _normalize_decimal("base_expected_value_bps", self.base_expected_value_bps),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_seconds("source_age_seconds", self.source_age_seconds),
        )
        _require_choice("source_type", self.source_type, SOURCE_TYPES)
        object.__setattr__(
            self,
            "contradiction_count",
            _normalize_nonnegative_integral_decimal(
                "contradiction_count",
                self.contradiction_count,
            ),
        )
        object.__setattr__(
            self,
            "catalyst_urgency_score",
            _normalize_ratio("catalyst_urgency_score", self.catalyst_urgency_score),
        )
        object.__setattr__(
            self,
            "settlement_horizon_seconds",
            _normalize_nonnegative_seconds(
                "settlement_horizon_seconds",
                self.settlement_horizon_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_paper_flags("information decay expected-value input", self)
        reject_strategy_candidate_information_decay_expected_value_v2_unsafe_payload(
            "information decay expected-value input",
            self,
        )


@dataclass(frozen=True)
class StrategyCandidateInformationDecayExpectedValueV2Row:
    candidate_id: str
    base_expected_value_bps: Decimal
    source_age_seconds: Decimal
    source_type: str
    source_age_multiplier: Decimal
    source_type_multiplier: Decimal
    contradiction_count: Decimal
    contradiction_multiplier: Decimal
    catalyst_urgency_score: Decimal
    catalyst_urgency_multiplier: Decimal
    settlement_horizon_seconds: Decimal
    settlement_horizon_multiplier: Decimal
    combined_information_multiplier: Decimal
    information_decay_bps: Decimal
    adjusted_expected_value_bps: Decimal
    adjustment_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        object.__setattr__(
            self,
            "base_expected_value_bps",
            _normalize_decimal("base_expected_value_bps", self.base_expected_value_bps),
        )
        for field_name in ("source_age_seconds", "settlement_horizon_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        _require_choice("source_type", self.source_type, SOURCE_TYPES)
        object.__setattr__(
            self,
            "contradiction_count",
            _normalize_nonnegative_integral_decimal(
                "contradiction_count",
                self.contradiction_count,
            ),
        )
        for field_name in (
            "source_age_multiplier",
            "source_type_multiplier",
            "contradiction_multiplier",
            "catalyst_urgency_score",
            "catalyst_urgency_multiplier",
            "settlement_horizon_multiplier",
            "combined_information_multiplier",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("information_decay_bps", "adjusted_expected_value_bps"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("adjustment_status", self.adjustment_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_paper_flags("information decay expected-value row", self)
        reject_strategy_candidate_information_decay_expected_value_v2_unsafe_payload(
            "information decay expected-value row",
            self,
        )
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            _require_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match row fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


@dataclass(frozen=True)
class StrategyCandidateInformationDecayExpectedValueV2Report:
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_adjusted_expected_value_bps: Decimal
    min_combined_information_multiplier: Decimal
    average_combined_information_multiplier: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCandidateInformationDecayExpectedValueV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "max_adjusted_expected_value_bps",
            "min_combined_information_multiplier",
            "average_combined_information_multiplier",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_paper_flags("information decay expected-value report", self)
        reject_strategy_candidate_information_decay_expected_value_v2_unsafe_payload(
            "information decay expected-value report",
            self,
        )
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_information_decay_expected_value_v2_payload(self)


def adjust_strategy_candidate_information_decay_expected_value_v2(
    candidate_input: StrategyCandidateInformationDecayExpectedValueV2Input,
    *,
    config: StrategyCandidateInformationDecayExpectedValueV2Config | None = None,
) -> StrategyCandidateInformationDecayExpectedValueV2Row:
    if type(candidate_input) is not StrategyCandidateInformationDecayExpectedValueV2Input:
        raise ValueError(
            "candidate_input must be a "
            "StrategyCandidateInformationDecayExpectedValueV2Input",
        )
    row_config = config or StrategyCandidateInformationDecayExpectedValueV2Config()
    if type(row_config) is not StrategyCandidateInformationDecayExpectedValueV2Config:
        raise ValueError(
            "config must be a StrategyCandidateInformationDecayExpectedValueV2Config",
        )
    _require_paper_flags("information decay expected-value input", candidate_input)
    _require_paper_flags("information decay expected-value config", row_config)

    source_age_multiplier = _half_life_multiplier(
        "source_age_multiplier",
        candidate_input.source_age_seconds,
        row_config.source_age_half_life_seconds,
    )
    source_type_multiplier = SOURCE_TYPE_MULTIPLIERS[candidate_input.source_type]
    contradiction_multiplier = _contradiction_multiplier(
        candidate_input.contradiction_count,
        row_config.contradiction_penalty_per_count,
        row_config.minimum_contradiction_multiplier,
    )
    catalyst_urgency_multiplier = _catalyst_urgency_multiplier(
        candidate_input.catalyst_urgency_score,
        row_config.catalyst_urgency_decay_ceiling,
    )
    settlement_horizon_multiplier = _half_life_multiplier(
        "settlement_horizon_multiplier",
        candidate_input.settlement_horizon_seconds,
        row_config.settlement_horizon_half_life_seconds,
    )
    combined_information_multiplier = _quantize_ratio(
        "combined_information_multiplier",
        source_age_multiplier
        * source_type_multiplier
        * contradiction_multiplier
        * catalyst_urgency_multiplier
        * settlement_horizon_multiplier,
    )
    adjusted_expected_value_bps = _quantize_decimal(
        "adjusted_expected_value_bps",
        candidate_input.base_expected_value_bps * combined_information_multiplier,
    )
    information_decay_bps = _quantize_decimal(
        "information_decay_bps",
        max(
            candidate_input.base_expected_value_bps - adjusted_expected_value_bps,
            ZERO,
        ),
    )
    adjustment_status = _adjustment_status(
        adjusted_expected_value_bps,
        row_config.watch_adjusted_expected_value_bps,
        row_config.minimum_adjusted_expected_value_bps,
    )

    return StrategyCandidateInformationDecayExpectedValueV2Row(
        candidate_id=candidate_input.candidate_id,
        base_expected_value_bps=candidate_input.base_expected_value_bps,
        source_age_seconds=candidate_input.source_age_seconds,
        source_type=candidate_input.source_type,
        source_age_multiplier=source_age_multiplier,
        source_type_multiplier=source_type_multiplier,
        contradiction_count=candidate_input.contradiction_count,
        contradiction_multiplier=contradiction_multiplier,
        catalyst_urgency_score=candidate_input.catalyst_urgency_score,
        catalyst_urgency_multiplier=catalyst_urgency_multiplier,
        settlement_horizon_seconds=candidate_input.settlement_horizon_seconds,
        settlement_horizon_multiplier=settlement_horizon_multiplier,
        combined_information_multiplier=combined_information_multiplier,
        information_decay_bps=information_decay_bps,
        adjusted_expected_value_bps=adjusted_expected_value_bps,
        adjustment_status=adjustment_status,
        reason_codes=_row_reason_codes(
            candidate_input.reason_codes,
            source_type=candidate_input.source_type,
            source_age_multiplier=source_age_multiplier,
            source_type_multiplier=source_type_multiplier,
            contradiction_multiplier=contradiction_multiplier,
            catalyst_urgency_multiplier=catalyst_urgency_multiplier,
            settlement_horizon_multiplier=settlement_horizon_multiplier,
            adjusted_expected_value_bps=adjusted_expected_value_bps,
            watch_adjusted_expected_value_bps=(
                row_config.watch_adjusted_expected_value_bps
            ),
            minimum_adjusted_expected_value_bps=(
                row_config.minimum_adjusted_expected_value_bps
            ),
            adjustment_status=adjustment_status,
        ),
    )


def build_strategy_candidate_information_decay_expected_value_v2_report(
    candidates: Iterable[StrategyCandidateInformationDecayExpectedValueV2Input],
    *,
    config: StrategyCandidateInformationDecayExpectedValueV2Config | None = None,
) -> StrategyCandidateInformationDecayExpectedValueV2Report:
    report_config = config or StrategyCandidateInformationDecayExpectedValueV2Config()
    if type(report_config) is not StrategyCandidateInformationDecayExpectedValueV2Config:
        raise ValueError(
            "config must be a StrategyCandidateInformationDecayExpectedValueV2Config",
        )
    input_rows = _normalize_inputs(candidates)
    rows = tuple(
        sorted(
            (
                adjust_strategy_candidate_information_decay_expected_value_v2(
                    candidate_input,
                    config=report_config,
                )
                for candidate_input in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    candidate_count = _count(len(rows))
    pass_count = _count(sum(1 for row in rows if row.adjustment_status == "pass"))
    watch_count = _count(sum(1 for row in rows if row.adjustment_status == "watch"))
    blocked_count = _count(sum(1 for row in rows if row.adjustment_status == "blocked"))
    return StrategyCandidateInformationDecayExpectedValueV2Report(
        config_version=report_config.config_version,
        candidate_count=candidate_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        max_adjusted_expected_value_bps=_max_decimal(
            tuple(row.adjusted_expected_value_bps for row in rows),
        ),
        min_combined_information_multiplier=_min_decimal(
            tuple(row.combined_information_multiplier for row in rows),
        ),
        average_combined_information_multiplier=_average_decimal(
            tuple(row.combined_information_multiplier for row in rows),
        ),
        report_status=_report_status(tuple(row.adjustment_status for row in rows)),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_candidate_information_decay_expected_value_v2_payload(
    value: object,
) -> dict[str, Any]:
    _require_payload_flags(value)
    reject_strategy_candidate_information_decay_expected_value_v2_unsafe_payload(
        "information decay expected-value payload",
        value,
    )
    _validate_payload_digest(value)
    ready = _json_ready(value)
    if type(ready) is not dict:
        raise ValueError("payload must be a dict")
    return ready


def reject_strategy_candidate_information_decay_expected_value_v2_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for path, item in _iter_public_entries(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}: {path}")


def _half_life_multiplier(
    field_name: str,
    age_seconds: Decimal,
    half_life_seconds: Decimal,
) -> Decimal:
    return _quantize_ratio(
        field_name,
        half_life_seconds / (half_life_seconds + age_seconds),
    )


def _contradiction_multiplier(
    contradiction_count: Decimal,
    penalty_per_count: Decimal,
    minimum_multiplier: Decimal,
) -> Decimal:
    penalty = contradiction_count * penalty_per_count
    return _quantize_ratio(
        "contradiction_multiplier",
        max(ONE - penalty, minimum_multiplier),
    )


def _catalyst_urgency_multiplier(
    catalyst_urgency_score: Decimal,
    decay_ceiling: Decimal,
) -> Decimal:
    return _quantize_ratio(
        "catalyst_urgency_multiplier",
        ONE - (catalyst_urgency_score * decay_ceiling),
    )


def _adjustment_status(
    adjusted_expected_value_bps: Decimal,
    watch_adjusted_expected_value_bps: Decimal,
    minimum_adjusted_expected_value_bps: Decimal,
) -> str:
    if adjusted_expected_value_bps <= watch_adjusted_expected_value_bps:
        return "blocked"
    if adjusted_expected_value_bps < minimum_adjusted_expected_value_bps:
        return "watch"
    return "pass"


def _row_reason_codes(
    existing: tuple[str, ...],
    *,
    source_type: str,
    source_age_multiplier: Decimal,
    source_type_multiplier: Decimal,
    contradiction_multiplier: Decimal,
    catalyst_urgency_multiplier: Decimal,
    settlement_horizon_multiplier: Decimal,
    adjusted_expected_value_bps: Decimal,
    watch_adjusted_expected_value_bps: Decimal,
    minimum_adjusted_expected_value_bps: Decimal,
    adjustment_status: str,
) -> tuple[str, ...]:
    additions = [
        "information_decay_expected_value_v2",
        f"information_decay_{adjustment_status}",
    ]
    if source_age_multiplier < ONE:
        additions.append("source_age_decay_applied")
    additions.append(f"source_type_{source_type}")
    if source_type_multiplier < ONE:
        additions.append("weak_source_type_decay_applied")
    if contradiction_multiplier < ONE:
        additions.append("source_contradiction_decay_applied")
    if catalyst_urgency_multiplier < ONE:
        additions.append("catalyst_urgency_decay_applied")
    if settlement_horizon_multiplier < ONE:
        additions.append("settlement_horizon_decay_applied")
    if adjusted_expected_value_bps <= watch_adjusted_expected_value_bps:
        additions.append("adjusted_expected_value_nonpositive")
    elif adjusted_expected_value_bps < minimum_adjusted_expected_value_bps:
        additions.append("adjusted_expected_value_below_minimum")
    else:
        additions.append("adjusted_expected_value_meets_minimum")
    return _append_reason_codes(existing, tuple(additions))


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_row(row: StrategyCandidateInformationDecayExpectedValueV2Row) -> None:
    if row.source_type_multiplier != SOURCE_TYPE_MULTIPLIERS[row.source_type]:
        raise ValueError("source_type_multiplier must match source_type")
    if row.combined_information_multiplier != _quantize_ratio(
        "combined_information_multiplier",
        row.source_age_multiplier
        * row.source_type_multiplier
        * row.contradiction_multiplier
        * row.catalyst_urgency_multiplier
        * row.settlement_horizon_multiplier,
    ):
        raise ValueError("combined_information_multiplier must match components")
    expected_adjusted = _quantize_decimal(
        "adjusted_expected_value_bps",
        row.base_expected_value_bps * row.combined_information_multiplier,
    )
    if row.adjusted_expected_value_bps != expected_adjusted:
        raise ValueError("adjusted_expected_value_bps must match multiplier")
    expected_decay = _quantize_decimal(
        "information_decay_bps",
        max(row.base_expected_value_bps - row.adjusted_expected_value_bps, ZERO),
    )
    if row.information_decay_bps != expected_decay:
        raise ValueError("information_decay_bps must match adjusted value")


def _validate_report(report: StrategyCandidateInformationDecayExpectedValueV2Report) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(
        sum(1 for row in report.rows if row.adjustment_status == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(
        sum(1 for row in report.rows if row.adjustment_status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count(
        sum(1 for row in report.rows if row.adjustment_status == "blocked"),
    ):
        raise ValueError("blocked_count must match rows")
    if report.max_adjusted_expected_value_bps != _max_decimal(
        tuple(row.adjusted_expected_value_bps for row in report.rows),
    ):
        raise ValueError("max_adjusted_expected_value_bps must match rows")
    if report.min_combined_information_multiplier != _min_decimal(
        tuple(row.combined_information_multiplier for row in report.rows),
    ):
        raise ValueError("min_combined_information_multiplier must match rows")
    if report.average_combined_information_multiplier != _average_decimal(
        tuple(row.combined_information_multiplier for row in report.rows),
    ):
        raise ValueError("average_combined_information_multiplier must match rows")
    if report.report_status != _report_status(
        tuple(row.adjustment_status for row in report.rows),
    ):
        raise ValueError("report_status must match rows")


def _validate_payload_digest(value: object) -> None:
    if type(value) is StrategyCandidateInformationDecayExpectedValueV2Row:
        if value.derived_validation_digest != _row_digest(value):
            raise ValueError("derived_validation_digest tamper check failed")
    if type(value) is StrategyCandidateInformationDecayExpectedValueV2Report:
        for row in value.rows:
            _validate_payload_digest(row)
        if value.derived_validation_digest != _report_digest(value):
            raise ValueError("derived_validation_digest tamper check failed")


def _row_digest(row: StrategyCandidateInformationDecayExpectedValueV2Row) -> str:
    return "scidev-v2:" + _digest_for_fields(row, _ROW_DIGEST_FIELDS)


def _report_digest(report: StrategyCandidateInformationDecayExpectedValueV2Report) -> str:
    return "scidev-v2:" + _digest_for_fields(report, _REPORT_DIGEST_FIELDS)


def _digest_for_fields(value: object, field_names: tuple[str, ...]) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(value, field_name))}"
        for field_name in field_names
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    if type(value) is StrategyCandidateInformationDecayExpectedValueV2Row:
        return _row_digest(value)
    raise ValueError("digest value must be public scalar data")


def _require_digest(value: str) -> None:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if not value.startswith("scidev-v2:"):
        raise ValueError("derived_validation_digest must use scidev-v2 prefix")
    digest = value.removeprefix("scidev-v2:")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError("derived_validation_digest must be canonical")


def _normalize_inputs(
    candidates: Iterable[StrategyCandidateInformationDecayExpectedValueV2Input],
) -> tuple[StrategyCandidateInformationDecayExpectedValueV2Input, ...]:
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Iterable):
        raise ValueError("candidates must be an iterable")
    rows = tuple(candidates)
    for row in rows:
        if type(row) is not StrategyCandidateInformationDecayExpectedValueV2Input:
            raise ValueError(
                "candidates must contain "
                "StrategyCandidateInformationDecayExpectedValueV2Input rows",
            )
    return rows


def _normalize_rows(value: object) -> tuple[StrategyCandidateInformationDecayExpectedValueV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not StrategyCandidateInformationDecayExpectedValueV2Row:
            raise ValueError(
                "rows must contain StrategyCandidateInformationDecayExpectedValueV2Row",
            )
    return value


def _row_sort_key(
    row: StrategyCandidateInformationDecayExpectedValueV2Row,
) -> tuple[Decimal, str]:
    return (-row.adjusted_expected_value_bps, row.candidate_id)


def _report_status(statuses: tuple[str, ...]) -> str:
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyCandidateInformationDecayExpectedValueV2Row, ...],
) -> tuple[str, ...]:
    status = _report_status(tuple(row.adjustment_status for row in rows))
    reason_codes = [f"information_decay_report_{status}"]
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    return tuple(reason_codes)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_decimal("max_decimal", max(values))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_decimal("min_decimal", min(values))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_decimal("average_decimal", sum(values, ZERO) / _count(len(values)))


def _count(value: int) -> Decimal:
    return Decimal(value)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_decimal(field_name, value)
    if value != normalized:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_seconds(field_name, value)
    if value != normalized:
        raise ValueError(f"{field_name} must be whole seconds")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_seconds(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_seconds(field_name, value)
    if value != normalized:
        raise ValueError(f"{field_name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _quantize_decimal(field_name: str, value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM)
    except (InvalidOperation, ArithmeticError) as exc:
        raise ValueError(f"{field_name} must fit six decimal places") from exc


def _quantize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _quantize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return normalized


def _quantize_seconds(field_name: str, value: Decimal) -> Decimal:
    try:
        return value.quantize(SECOND_QUANTUM)
    except (InvalidOperation, ArithmeticError) as exc:
        raise ValueError(f"{field_name} must be whole seconds") from exc


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_:-")
    if any(char not in allowed for char in value):
        raise ValueError(f"{field_name} must be canonical")


def _require_choice(
    field_name: str,
    value: object,
    choices: tuple[str, ...],
) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_flags(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_flags(asdict(value))
        return
    if type(value) is dict:
        for field_name in ("paper_only", "report_only", "readonly"):
            if value.get(field_name) is not True:
                raise ValueError(f"{field_name} must be True for payload")
        for item in value.values():
            if type(item) in (dict, list, tuple) or (
                is_dataclass(item) and not isinstance(item, type)
            ):
                _require_payload_flags(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            if type(item) in (dict, list, tuple) or (
                is_dataclass(item) and not isinstance(item, type)
            ):
                _require_payload_flags(item)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is dict:
        return _json_dict_ready(value)
    if isinstance(value, dict):
        return _json_dict_ready(value)
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, int):
        raise ValueError("JSON value must use Decimal, not int")
    raise ValueError("JSON value must be public scalar data")


def _json_dict_ready(value: dict[Any, Any]) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError("payload containers must be plain dict objects")
    ready: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("payload keys must be strings")
        ready[key] = _json_ready(item)
    return ready


def _iter_public_entries(value: object) -> tuple[tuple[str, str], ...]:
    entries: list[tuple[str, str]] = []
    _collect_public_entries("$", value, entries)
    return tuple(entries)


def _collect_public_entries(
    path: str,
    value: object,
    entries: list[tuple[str, str]],
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _collect_public_entries(path, asdict(value), entries)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            item_path = f"{path}.{key}"
            entries.append((item_path, key))
            _collect_public_entries(item_path, item, entries)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _collect_public_entries(f"{path}[{index}]", item, entries)
        return
    if type(value) is str:
        entries.append((path, value))


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_INFORMATION_DECAY_EXPECTED_VALUE_V2_CONFIG_VERSION",
    "SOURCE_TYPES",
    "ROW_STATUSES",
    "REPORT_STATUSES",
    "StrategyCandidateInformationDecayExpectedValueV2Config",
    "StrategyCandidateInformationDecayExpectedValueV2Input",
    "StrategyCandidateInformationDecayExpectedValueV2Row",
    "StrategyCandidateInformationDecayExpectedValueV2Report",
    "adjust_strategy_candidate_information_decay_expected_value_v2",
    "build_strategy_candidate_information_decay_expected_value_v2_report",
    "strategy_candidate_information_decay_expected_value_v2_payload",
    "reject_strategy_candidate_information_decay_expected_value_v2_unsafe_payload",
)
