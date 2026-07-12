"""Commit readiness report for ProbabilityEventScreen development checkpoints."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any, Mapping

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


__all__ = (
    "COMMIT_READINESS_BANDS",
    "ProbabilityEventScreenCommitReadinessInput",
    "ProbabilityEventScreenCommitReadinessReport",
    "build_probability_event_screen_commit_readiness_report",
    "probability_event_screen_commit_readiness_report_digest",
    "probability_event_screen_commit_readiness_report_to_payload",
    "validate_probability_event_screen_commit_readiness_public_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("8.000000")

COMMIT_READINESS_BANDS = ("ready", "attention", "blocked")
READY_REASON_CODE = "probability_event_screen_commit_readiness_ready"

BLOCKED_REASON_SEQUENCE = (
    "commit_focused_tests_not_ready",
    "commit_compile_not_ready",
    "commit_diff_check_not_ready",
    "commit_codegraph_sync_not_ready",
    "commit_claude_review_not_ready",
    "commit_public_payload_safety_not_ready",
    "commit_supabase_contract_not_ready",
)
ATTENTION_REASON_SEQUENCE = (
    "commit_live_execution_surface_detected",
    READY_REASON_CODE,
)

PAYLOAD_KEYS = (
    "focused_tests_ready",
    "compile_ready",
    "diff_check_ready",
    "codegraph_sync_ready",
    "claude_review_ready",
    "public_payload_safety_ready",
    "supabase_contract_ready",
    "no_live_execution_surface",
    "commit_readiness_ready",
    "commit_band",
    "blocked_reason_codes",
    "attention_reason_codes",
    "ready_ratio",
    "paper_only",
    "report_only",
    "readonly",
)

_BOOL_INPUT_FIELDS = (
    "focused_tests_ready",
    "compile_ready",
    "diff_check_ready",
    "codegraph_sync_ready",
    "claude_review_ready",
    "public_payload_safety_ready",
    "supabase_contract_ready",
    "no_live_execution_surface",
)

_BLOCKING_CHECKS = (
    ("focused_tests_ready", "commit_focused_tests_not_ready"),
    ("compile_ready", "commit_compile_not_ready"),
    ("diff_check_ready", "commit_diff_check_not_ready"),
    ("codegraph_sync_ready", "commit_codegraph_sync_not_ready"),
    ("claude_review_ready", "commit_claude_review_not_ready"),
    ("public_payload_safety_ready", "commit_public_payload_safety_not_ready"),
    ("supabase_contract_ready", "commit_supabase_contract_not_ready"),
)


class _CommitReadinessPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _CommitReadinessPublicDataclass and issubclass(
                base,
                _CommitReadinessPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ProbabilityEventScreenCommitReadinessInput(_CommitReadinessPublicDataclass):
    focused_tests_ready: bool
    compile_ready: bool
    diff_check_ready: bool
    codegraph_sync_ready: bool
    claude_review_ready: bool
    public_payload_safety_ready: bool
    supabase_contract_ready: bool
    no_live_execution_surface: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenCommitReadinessInput,
            "commit readiness input",
        )
        for field_name in _BOOL_INPUT_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("commit readiness input", self)


@dataclass(frozen=True)
class ProbabilityEventScreenCommitReadinessReport(_CommitReadinessPublicDataclass):
    focused_tests_ready: bool
    compile_ready: bool
    diff_check_ready: bool
    codegraph_sync_ready: bool
    claude_review_ready: bool
    public_payload_safety_ready: bool
    supabase_contract_ready: bool
    no_live_execution_surface: bool
    commit_readiness_ready: bool
    commit_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenCommitReadinessReport,
            "commit readiness report",
        )
        for field_name in _BOOL_INPUT_FIELDS + ("commit_readiness_ready",):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "commit_band",
            _normalize_member("commit_band", self.commit_band),
        )
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                BLOCKED_REASON_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                ATTENTION_REASON_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _normalize_ratio("ready_ratio", self.ready_ratio),
        )
        _validate_report(self)
        _require_hard_flags("commit readiness report", self)

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_screen_commit_readiness_report_to_payload(self)

    @property
    def digest(self) -> str:
        return probability_event_screen_commit_readiness_report_digest(self)


def build_probability_event_screen_commit_readiness_report(
    readiness: ProbabilityEventScreenCommitReadinessInput,
) -> ProbabilityEventScreenCommitReadinessReport:
    if type(readiness) is not ProbabilityEventScreenCommitReadinessInput:
        raise ValueError(
            "readiness must be a ProbabilityEventScreenCommitReadinessInput",
        )
    _require_hard_flags("commit readiness input", readiness)

    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _commit_readiness_findings(readiness)
    )
    commit_band = _commit_band(blocked_reason_codes, attention_reason_codes)

    return ProbabilityEventScreenCommitReadinessReport(
        focused_tests_ready=readiness.focused_tests_ready,
        compile_ready=readiness.compile_ready,
        diff_check_ready=readiness.diff_check_ready,
        codegraph_sync_ready=readiness.codegraph_sync_ready,
        claude_review_ready=readiness.claude_review_ready,
        public_payload_safety_ready=readiness.public_payload_safety_ready,
        supabase_contract_ready=readiness.supabase_contract_ready,
        no_live_execution_surface=readiness.no_live_execution_surface,
        commit_readiness_ready=commit_band == "ready",
        commit_band=commit_band,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=_ratio(_count(ready_component_count), COMPONENT_COUNT),
        paper_only=readiness.paper_only,
        report_only=readiness.report_only,
        readonly=readiness.readonly,
    )


def probability_event_screen_commit_readiness_report_to_payload(
    report: ProbabilityEventScreenCommitReadinessReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventScreenCommitReadinessReport:
        raise ValueError(
            "report must be a ProbabilityEventScreenCommitReadinessReport",
        )
    _require_hard_flags("commit readiness report", report)
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "focused_tests_ready": report.focused_tests_ready,
            "compile_ready": report.compile_ready,
            "diff_check_ready": report.diff_check_ready,
            "codegraph_sync_ready": report.codegraph_sync_ready,
            "claude_review_ready": report.claude_review_ready,
            "public_payload_safety_ready": report.public_payload_safety_ready,
            "supabase_contract_ready": report.supabase_contract_ready,
            "no_live_execution_surface": report.no_live_execution_surface,
            "commit_readiness_ready": report.commit_readiness_ready,
            "commit_band": report.commit_band,
            "blocked_reason_codes": report.blocked_reason_codes,
            "attention_reason_codes": report.attention_reason_codes,
            "ready_ratio": report.ready_ratio,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_probability_event_screen_commit_readiness_public_payload(payload)
    return payload


def probability_event_screen_commit_readiness_report_digest(
    report: ProbabilityEventScreenCommitReadinessReport,
) -> str:
    payload = probability_event_screen_commit_readiness_report_to_payload(report)
    return _digest_payload(payload)


def validate_probability_event_screen_commit_readiness_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical commit readiness schema")
    reject_unsafe_surface_fields("commit readiness public payload", payload)
    for field_name in (
        *_BOOL_INPUT_FIELDS,
        "commit_readiness_ready",
        "paper_only",
        "report_only",
        "readonly",
    ):
        _require_bool(field_name, payload[field_name])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _normalize_member("commit_band", payload["commit_band"])
    blocked_reason_codes = _normalize_payload_reason_codes(
        "blocked_reason_codes",
        payload["blocked_reason_codes"],
        BLOCKED_REASON_SEQUENCE,
    )
    attention_reason_codes = _normalize_payload_reason_codes(
        "attention_reason_codes",
        payload["attention_reason_codes"],
        ATTENTION_REASON_SEQUENCE,
    )
    ready_ratio_value = payload["ready_ratio"]
    if type(ready_ratio_value) is not str:
        raise ValueError("ready_ratio must be serialized as a string")
    ready_ratio = _normalize_ratio("ready_ratio", Decimal(ready_ratio_value))
    expected_blocked, expected_attention, ready_component_count = (
        _payload_findings(payload)
    )
    if blocked_reason_codes != expected_blocked:
        raise ValueError("blocked_reason_codes must match readiness fields")
    if attention_reason_codes != expected_attention:
        raise ValueError("attention_reason_codes must match readiness fields")
    expected_band = _commit_band(blocked_reason_codes, attention_reason_codes)
    if payload["commit_band"] != expected_band:
        raise ValueError("commit_band must match reason codes")
    if payload["commit_readiness_ready"] is not (expected_band == "ready"):
        raise ValueError("commit_readiness_ready must match commit_band")
    if ready_ratio != _ratio(_count(ready_component_count), COMPONENT_COUNT):
        raise ValueError("ready_ratio must match readiness fields")
    return payload


def _commit_readiness_findings(
    readiness: ProbabilityEventScreenCommitReadinessInput,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    blocked: list[str] = []
    ready_component_count = 0
    for field_name, reason_code in _BLOCKING_CHECKS:
        if getattr(readiness, field_name) is True:
            ready_component_count += 1
        else:
            blocked.append(reason_code)

    attention: tuple[str, ...]
    if readiness.no_live_execution_surface is True:
        ready_component_count += 1
        attention = (READY_REASON_CODE,) if not blocked else ()
    else:
        attention = ("commit_live_execution_surface_detected",)
    return tuple(blocked), attention, ready_component_count


def _payload_findings(
    payload: Mapping[str, object],
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    source = ProbabilityEventScreenCommitReadinessInput(
        focused_tests_ready=payload["focused_tests_ready"],  # type: ignore[arg-type]
        compile_ready=payload["compile_ready"],  # type: ignore[arg-type]
        diff_check_ready=payload["diff_check_ready"],  # type: ignore[arg-type]
        codegraph_sync_ready=payload["codegraph_sync_ready"],  # type: ignore[arg-type]
        claude_review_ready=payload["claude_review_ready"],  # type: ignore[arg-type]
        public_payload_safety_ready=payload["public_payload_safety_ready"],  # type: ignore[arg-type]
        supabase_contract_ready=payload["supabase_contract_ready"],  # type: ignore[arg-type]
        no_live_execution_surface=payload["no_live_execution_surface"],  # type: ignore[arg-type]
        paper_only=payload["paper_only"],  # type: ignore[arg-type]
        report_only=payload["report_only"],  # type: ignore[arg-type]
        readonly=payload["readonly"],  # type: ignore[arg-type]
    )
    return _commit_readiness_findings(source)


def _validate_report(report: ProbabilityEventScreenCommitReadinessReport) -> None:
    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _report_findings(report)
    )
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match readiness fields")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match readiness fields")
    expected_band = _commit_band(blocked_reason_codes, attention_reason_codes)
    if report.commit_band != expected_band:
        raise ValueError("commit_band must match reason codes")
    if report.commit_readiness_ready is not (expected_band == "ready"):
        raise ValueError("commit_readiness_ready must match commit_band")
    if report.ready_ratio != _ratio(_count(ready_component_count), COMPONENT_COUNT):
        raise ValueError("ready_ratio must match readiness fields")


def _report_findings(
    report: ProbabilityEventScreenCommitReadinessReport,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    source = ProbabilityEventScreenCommitReadinessInput(
        focused_tests_ready=report.focused_tests_ready,
        compile_ready=report.compile_ready,
        diff_check_ready=report.diff_check_ready,
        codegraph_sync_ready=report.codegraph_sync_ready,
        claude_review_ready=report.claude_review_ready,
        public_payload_safety_ready=report.public_payload_safety_ready,
        supabase_contract_ready=report.supabase_contract_ready,
        no_live_execution_surface=report.no_live_execution_surface,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    return _commit_readiness_findings(source)


def _commit_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes != (READY_REASON_CODE,):
        return "attention"
    return "ready"


def _normalize_member(field_name: str, value: object) -> str:
    if type(value) is not str or value not in COMMIT_READINESS_BANDS:
        raise ValueError(f"{field_name} must be a supported commit readiness band")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    supported_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return _normalize_reason_code_items(field_name, value, supported_reason_codes)


def _normalize_payload_reason_codes(
    field_name: str,
    value: object,
    supported_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is list:
        return _normalize_reason_code_items(field_name, tuple(value), supported_reason_codes)
    if type(value) is tuple:
        return _normalize_reason_code_items(field_name, value, supported_reason_codes)
    raise ValueError(f"{field_name} must be a list")


def _normalize_reason_code_items(
    field_name: str,
    reason_codes: tuple[str, ...],
    supported_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in supported_reason_codes:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    ordered = tuple(
        reason_code for reason_code in supported_reason_codes if reason_code in seen
    )
    if reason_codes != ordered:
        raise ValueError(f"{field_name} must use canonical order")
    return ordered


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _normalize_ratio("ready_ratio", numerator / denominator)


def _digest_payload(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


