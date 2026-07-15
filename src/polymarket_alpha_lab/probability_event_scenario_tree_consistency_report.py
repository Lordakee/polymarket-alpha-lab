"""Read-only probability event scenario-tree consistency report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
from typing import Any


__all__ = (
    "ProbabilityEventScenarioTreeConsistencyReport",
    "build_probability_event_scenario_tree_consistency_report",
    "probability_event_scenario_tree_consistency_public_payload",
    "validate_probability_event_scenario_tree_consistency_payload_digest",
)


ZERO = Decimal("0")
ONE = Decimal("1")
PROBABILITY_QUANTUM = Decimal("0.000001")


@dataclass(frozen=True)
class ProbabilityEventScenarioTreeConsistencyReport:
    scenario_count: Decimal
    covered_scenario_count: Decimal
    contradictory_scenario_count: Decimal
    base_case_probability: Decimal
    tail_case_probability: Decimal
    scenario_tree_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "scenario_count",
            _require_nonnegative_whole_decimal("scenario_count", self.scenario_count),
        )
        object.__setattr__(
            self,
            "covered_scenario_count",
            _require_nonnegative_whole_decimal(
                "covered_scenario_count",
                self.covered_scenario_count,
            ),
        )
        object.__setattr__(
            self,
            "contradictory_scenario_count",
            _require_nonnegative_whole_decimal(
                "contradictory_scenario_count",
                self.contradictory_scenario_count,
            ),
        )
        object.__setattr__(
            self,
            "base_case_probability",
            _require_probability_decimal("base_case_probability", self.base_case_probability),
        )
        object.__setattr__(
            self,
            "tail_case_probability",
            _require_probability_decimal("tail_case_probability", self.tail_case_probability),
        )
        if self.covered_scenario_count > self.scenario_count:
            raise ValueError("covered_scenario_count must not exceed scenario_count")
        if self.contradictory_scenario_count > self.scenario_count:
            raise ValueError("contradictory_scenario_count must not exceed scenario_count")
        _require_status(self.scenario_tree_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes),
        )
        _require_public_text("manual_next_step", self.manual_next_step)
        _require_hard_flags(self)
        _validate_report_consistency(self)
        expected_digest = _payload_digest_for_report(self)
        if self.payload_digest:
            _require_digest("payload_digest", self.payload_digest)
            if self.payload_digest != expected_digest:
                raise ValueError("payload_digest must match public payload")
        else:
            object.__setattr__(self, "payload_digest", expected_digest)

    @property
    def public_payload(self) -> dict[str, object]:
        payload = _public_payload_without_digest(self)
        payload["payload_digest"] = self.payload_digest
        if not validate_probability_event_scenario_tree_consistency_payload_digest(payload):
            raise ValueError("payload_digest must match public payload")
        return payload


def build_probability_event_scenario_tree_consistency_report(
    *,
    scenario_count: Decimal,
    covered_scenario_count: Decimal,
    contradictory_scenario_count: Decimal,
    base_case_probability: Decimal,
    tail_case_probability: Decimal,
) -> ProbabilityEventScenarioTreeConsistencyReport:
    scenario_count = _require_nonnegative_whole_decimal("scenario_count", scenario_count)
    covered_scenario_count = _require_nonnegative_whole_decimal(
        "covered_scenario_count",
        covered_scenario_count,
    )
    contradictory_scenario_count = _require_nonnegative_whole_decimal(
        "contradictory_scenario_count",
        contradictory_scenario_count,
    )
    base_case_probability = _require_probability_decimal(
        "base_case_probability",
        base_case_probability,
    )
    tail_case_probability = _require_probability_decimal(
        "tail_case_probability",
        tail_case_probability,
    )
    if covered_scenario_count > scenario_count:
        raise ValueError("covered_scenario_count must not exceed scenario_count")
    if contradictory_scenario_count > scenario_count:
        raise ValueError("contradictory_scenario_count must not exceed scenario_count")

    reason_codes = _derive_reason_codes(
        scenario_count=scenario_count,
        covered_scenario_count=covered_scenario_count,
        contradictory_scenario_count=contradictory_scenario_count,
        base_case_probability=base_case_probability,
        tail_case_probability=tail_case_probability,
    )
    status = _status_for_reason_codes(reason_codes)
    return ProbabilityEventScenarioTreeConsistencyReport(
        scenario_count=scenario_count,
        covered_scenario_count=covered_scenario_count,
        contradictory_scenario_count=contradictory_scenario_count,
        base_case_probability=base_case_probability,
        tail_case_probability=tail_case_probability,
        scenario_tree_status=status,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step_for_reason_codes(reason_codes),
    )


def probability_event_scenario_tree_consistency_public_payload(
    report: ProbabilityEventScenarioTreeConsistencyReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventScenarioTreeConsistencyReport:
        raise ValueError(
            "report must be a ProbabilityEventScenarioTreeConsistencyReport",
        )
    _require_hard_flags(report)
    return report.public_payload


def validate_probability_event_scenario_tree_consistency_payload_digest(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        return False
    digest = payload.get("payload_digest")
    if type(digest) is not str:
        return False
    try:
        _require_digest("payload_digest", digest)
    except ValueError:
        return False
    payload_without_digest = dict(payload)
    payload_without_digest.pop("payload_digest", None)
    return digest == _payload_digest(payload_without_digest)


def _derive_reason_codes(
    *,
    scenario_count: Decimal,
    covered_scenario_count: Decimal,
    contradictory_scenario_count: Decimal,
    base_case_probability: Decimal,
    tail_case_probability: Decimal,
) -> tuple[str, ...]:
    if scenario_count == ZERO:
        return ("scenario_tree_empty",)
    if contradictory_scenario_count > ZERO:
        return ("scenario_tree_contradictory",)
    if base_case_probability < tail_case_probability:
        return ("base_case_probability_below_tail_case_probability",)
    if covered_scenario_count < scenario_count:
        return ("scenario_tree_incomplete",)
    return ("scenario_tree_consistent",)


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes in {
        ("scenario_tree_empty",),
        ("scenario_tree_contradictory",),
        ("base_case_probability_below_tail_case_probability",),
    }:
        return "block"
    if reason_codes == ("scenario_tree_incomplete",):
        return "watch"
    if reason_codes == ("scenario_tree_consistent",):
        return "pass"
    raise ValueError("reason_codes must support scenario_tree_status")


def _manual_next_step_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("scenario_tree_empty",):
        return "Add scenario branches before using this probability event tree."
    if reason_codes == ("scenario_tree_contradictory",):
        return (
            "Resolve contradictory scenario branches before relying on this probability event tree."
        )
    if reason_codes == ("base_case_probability_below_tail_case_probability",):
        return (
            "Reconcile base and tail probabilities before relying on this probability event tree."
        )
    if reason_codes == ("scenario_tree_incomplete",):
        return (
            "Manually review missing scenario branches before using this probability event tree."
        )
    if reason_codes == ("scenario_tree_consistent",):
        return "No manual action required; keep monitoring scenario coverage."
    raise ValueError("reason_codes must support manual_next_step")


def _validate_report_consistency(
    report: ProbabilityEventScenarioTreeConsistencyReport,
) -> None:
    expected_reason_codes = _derive_reason_codes(
        scenario_count=report.scenario_count,
        covered_scenario_count=report.covered_scenario_count,
        contradictory_scenario_count=report.contradictory_scenario_count,
        base_case_probability=report.base_case_probability,
        tail_case_probability=report.tail_case_probability,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match scenario tree inputs")
    if report.scenario_tree_status != _status_for_reason_codes(expected_reason_codes):
        raise ValueError("scenario_tree_status must match reason_codes")
    if report.manual_next_step != _manual_next_step_for_reason_codes(expected_reason_codes):
        raise ValueError("manual_next_step must match reason_codes")


def _public_payload_without_digest(
    report: ProbabilityEventScenarioTreeConsistencyReport,
) -> dict[str, object]:
    _require_hard_flags(report)
    return {
        "scenario_count": _decimal_text(report.scenario_count),
        "covered_scenario_count": _decimal_text(report.covered_scenario_count),
        "contradictory_scenario_count": _decimal_text(report.contradictory_scenario_count),
        "base_case_probability": _decimal_text(report.base_case_probability),
        "tail_case_probability": _decimal_text(report.tail_case_probability),
        "scenario_tree_status": report.scenario_tree_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _payload_digest_for_report(
    report: ProbabilityEventScenarioTreeConsistencyReport,
) -> str:
    return _payload_digest(_public_payload_without_digest(report))


def _payload_digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _require_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return decimal_value


def _require_probability_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value.quantize(PROBABILITY_QUANTUM)


def _require_status(value: object) -> None:
    if value not in {"pass", "watch", "block"}:
        raise ValueError("scenario_tree_status must be pass, watch, or block")


def _require_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a non-empty tuple")
    normalized = tuple(value)
    for item in value:
        _require_public_text("reason_code", item)
    return tuple(sorted(set(normalized)))


def _require_public_text(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    if any(ch.isspace() for ch in value) and name == "reason_code":
        raise ValueError("reason_code must not contain whitespace")


def _require_hard_flags(report: ProbabilityEventScenarioTreeConsistencyReport) -> None:
    if report.paper_only is not True:
        raise ValueError("paper_only must be True")
    if report.report_only is not True:
        raise ValueError("report_only must be True")
    if report.readonly is not True:
        raise ValueError("readonly must be True")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a 64-character hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a 64-character hex digest") from exc


def _decimal_text(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(value.quantize(ONE))
    return str(value)
