"""Identity-bound BTC resolution contract and incident-gate assessment.

This module owns the frozen BTC resolution-contract type, the exact incident
gates, their pure assessment, and the canonical contract payload. It is a
Phase 1 policy boundary: ``paper_only``, ``report_only``, and ``readonly``
are hard flags on every public value, and nothing here performs database,
filesystem, network, clock, randomness, or exchange operations.

The contract is identity-bound to a Polymarket condition, market slug, and
event template, and to the trusted ``btc_resolution_rules`` catalog record
through the pinned resolver from ``crypto_btc_evidence_catalog``. A missing,
expired, or digest-mismatched catalog record fails closed to blocked. Reason
codes come from a closed, unique, deterministically ordered vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import re
from typing import Final, final

from polymarket_alpha_lab.crypto_btc_evidence_catalog import (
    resolve_trusted_crypto_btc_source_record,
)

__all__ = (
    "CryptoBtcResolutionContract",
    "CryptoBtcIncidentGates",
    "CryptoBtcResolutionAssessment",
    "check_crypto_btc_resolution_contract",
    "crypto_btc_resolution_contract_payload",
)

CRYPTO_BTC_RESOLUTION_CONTRACT_VERSION: Final = "crypto-btc-resolution-contract-v0"
CRYPTO_BTC_RESOLUTION_RULES_SOURCE_ID: Final = "btc_resolution_rules"
CRYPTO_BTC_RESOLUTION_CONTRACT_STATUSES: Final = ("pass", "watch", "blocked")
CRYPTO_BTC_RESOLUTION_MINIMUM_QUESTION_CHARACTERS: Final = 40
CRYPTO_BTC_RESOLUTION_MINIMUM_RULES_SUMMARY_CHARACTERS: Final = 80
CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE: Final = "crypto_btc_resolution_contract_passed"
CRYPTO_BTC_RESOLUTION_REASON_CODES: Final = (
    "condition_id_mismatch",
    "market_slug_mismatch",
    "event_template_mismatch",
    "question_text_too_short",
    "rules_summary_too_short",
    "rules_summary_not_objective",
    "missing_close_time",
    "resolution_catalog_record_unresolved",
    "incident_source_outage",
    "incident_index_dislocation",
    "incident_chain_reorg",
    "incident_resolution_rule_change",
    "incident_market_halt",
    "incident_derivatives_feed_degraded",
)
CRYPTO_BTC_RESOLUTION_ALL_REASON_CODES: Final = (
    CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE,
    *CRYPTO_BTC_RESOLUTION_REASON_CODES,
)
CRYPTO_BTC_RESOLUTION_WATCH_REASON_CODES: Final = (
    "incident_derivatives_feed_degraded",
)
CRYPTO_BTC_RESOLUTION_BLOCKING_REASON_CODES: Final = tuple(
    code
    for code in CRYPTO_BTC_RESOLUTION_REASON_CODES
    if code not in CRYPTO_BTC_RESOLUTION_WATCH_REASON_CODES
)

_IDENTIFIER_RE: Final = re.compile(r"[a-z0-9](?:[a-z0-9._:-]*[a-z0-9])?", re.ASCII)
_DIGEST_RE: Final = re.compile(r"[0-9a-f]{64}", re.ASCII)
_HARD_FLAGS: Final = ("paper_only", "report_only", "readonly")
_PUBLIC_CLASS_NAMES: Final = (
    "CryptoBtcResolutionContract",
    "CryptoBtcIncidentGates",
    "CryptoBtcResolutionAssessment",
)
_CONTRACT_IDENTIFIER_FIELDS: Final = (
    "condition_id",
    "market_slug",
    "event_template",
    "resolution_catalog_record_id",
    "contract_version",
)
_CONTRACT_TEXT_FIELDS: Final = ("question_text", "rules_summary")
_IDENTITY_FIELDS: Final = ("condition_id", "market_slug", "event_template")
_INCIDENT_GATE_FIELDS: Final = (
    "source_outage",
    "index_dislocation",
    "chain_reorg",
    "resolution_rule_change",
    "market_halt",
    "derivatives_feed_degraded",
)
_BLOCKING_INCIDENT_REASON_CODES: Final = (
    ("source_outage", "incident_source_outage"),
    ("index_dislocation", "incident_index_dislocation"),
    ("chain_reorg", "incident_chain_reorg"),
    ("resolution_rule_change", "incident_resolution_rule_change"),
    ("market_halt", "incident_market_halt"),
)
_RULES_RESOLUTION_TERMS: Final = ("resolv",)
_RULES_OBJECTIVE_SOURCE_TERMS: Final = ("official", "polymarket", "market rules")
_RULES_AMBIGUOUS_TERMS: Final = (
    "news reports",
    "community consensus",
    "social media",
    "generally accepted",
    "tbd",
    "unclear",
    "likely",
    "probably",
)
_ALL_REASON_CODE_SET: Final = frozenset(CRYPTO_BTC_RESOLUTION_ALL_REASON_CODES)
_WATCH_REASON_CODE_SET: Final = frozenset(CRYPTO_BTC_RESOLUTION_WATCH_REASON_CODES)


class _ExactPublicDataclass:
    __slots__ = ()

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if (
            cls.__bases__ != (_ExactPublicDataclass,)
            or cls.__name__ not in _PUBLIC_CLASS_NAMES
        ):
            raise TypeError(
                "public crypto BTC resolution dataclasses do not support subclassing",
            )


def _exact_self(value: object, expected: type[object], path: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{path} must be exactly {expected.__name__}")


def _require_hard_flags(path: str, value: object) -> None:
    for name in _HARD_FLAGS:
        try:
            flag = getattr(value, name)
        except AttributeError as error:
            raise ValueError(f"{path}.{name} must be exact True") from error
        if flag is not True:
            raise ValueError(f"{path}.{name} must be exact True")


def _identifier(path: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value.encode("utf-8")) > 160
        or _IDENTIFIER_RE.fullmatch(value) is None
    ):
        raise ValueError(f"{path} must be an exact canonical identifier")
    return value


def _digest(path: str, value: object) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{path} must be an exact lowercase SHA-256 digest")
    return value


def _stripped_text(path: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{path} must be an exact string")
    return value.strip()


def _require_stripped_text(path: str, value: object) -> None:
    if type(value) is not str or value.strip() != value:
        raise ValueError(f"{path} must be an exact stripped string")


def _utc_datetime(path: str, value: object) -> datetime:
    if (
        type(value) is not datetime
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(f"{path} must be an exact aware datetime")
    return value.astimezone(UTC)


def _optional_utc_datetime(path: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _utc_datetime(path, value)


def _exact_bool(path: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{path} must be an exact bool")
    return value


def _member(path: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{path} must be one of the closed contract statuses")
    return value


def _reason_code_tuple(path: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{path} must be an exact tuple of reason codes")
    codes = list(value)
    if not codes:
        raise ValueError(f"{path} must be a nonempty tuple of reason codes")
    for code in codes:
        if type(code) is not str or code not in _ALL_REASON_CODE_SET:
            raise ValueError(f"{path} must contain known reason codes")
    if len(set(codes)) != len(codes):
        raise ValueError(f"{path} must not contain duplicate reason codes")
    expected = tuple(
        code for code in CRYPTO_BTC_RESOLUTION_ALL_REASON_CODES if code in codes
    )
    if tuple(codes) != expected:
        raise ValueError(f"{path} must follow the canonical deterministic order")
    return tuple(codes)


def _status_for_reason_codes(
    reason_codes: tuple[str, ...],
) -> str:
    if any(code not in _WATCH_REASON_CODE_SET for code in reason_codes):
        return "blocked"
    if reason_codes:
        return "watch"
    return "pass"


def _validate_status_consistency(
    status: str,
    reason_codes: tuple[str, ...],
) -> None:
    if status == "pass":
        if reason_codes != (CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE,):
            raise ValueError("pass assessments must use only the pass reason code")
        return
    if CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE in reason_codes:
        raise ValueError("non-pass assessments cannot use the pass reason code")
    if status == "watch":
        if any(code not in _WATCH_REASON_CODE_SET for code in reason_codes):
            raise ValueError("watch assessments must use only watch reason codes")
        return
    if not any(code not in _WATCH_REASON_CODE_SET for code in reason_codes):
        raise ValueError("blocked assessments require a blocking reason code")


@final
@dataclass(frozen=True, slots=True)
class CryptoBtcResolutionContract(_ExactPublicDataclass):
    condition_id: str
    market_slug: str
    event_template: str
    question_text: str
    rules_summary: str
    close_time: datetime | None
    resolution_catalog_record_id: str
    resolution_catalog_record_digest: str
    contract_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _exact_self(self, CryptoBtcResolutionContract, "contract")
        for name in _CONTRACT_IDENTIFIER_FIELDS:
            object.__setattr__(self, name, _identifier(name, getattr(self, name)))
        for name in _CONTRACT_TEXT_FIELDS:
            object.__setattr__(self, name, _stripped_text(name, getattr(self, name)))
        object.__setattr__(
            self,
            "close_time",
            _optional_utc_datetime("close_time", self.close_time),
        )
        object.__setattr__(
            self,
            "resolution_catalog_record_digest",
            _digest(
                "resolution_catalog_record_digest",
                self.resolution_catalog_record_digest,
            ),
        )
        _require_hard_flags("contract", self)


@final
@dataclass(frozen=True, slots=True)
class CryptoBtcIncidentGates(_ExactPublicDataclass):
    source_outage: bool
    index_dislocation: bool
    chain_reorg: bool
    resolution_rule_change: bool
    market_halt: bool
    derivatives_feed_degraded: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _validate_gates_state(self)


@final
@dataclass(frozen=True, slots=True)
class CryptoBtcResolutionAssessment(_ExactPublicDataclass):
    condition_id: str
    market_slug: str
    event_template: str
    resolution_contract_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _validate_assessment_state(self)


def _validate_contract_state(contract: CryptoBtcResolutionContract) -> None:
    _exact_self(contract, CryptoBtcResolutionContract, "contract")
    for name in _CONTRACT_IDENTIFIER_FIELDS:
        _identifier(name, getattr(contract, name))
    for name in _CONTRACT_TEXT_FIELDS:
        _require_stripped_text(name, getattr(contract, name))
    _optional_utc_datetime("close_time", contract.close_time)
    _digest(
        "resolution_catalog_record_digest",
        contract.resolution_catalog_record_digest,
    )
    _require_hard_flags("contract", contract)


def _validate_gates_state(gates: CryptoBtcIncidentGates) -> None:
    _exact_self(gates, CryptoBtcIncidentGates, "incident_gates")
    for name in _INCIDENT_GATE_FIELDS:
        _exact_bool(name, getattr(gates, name))
    _require_hard_flags("incident_gates", gates)


def _validate_assessment_state(assessment: CryptoBtcResolutionAssessment) -> None:
    _exact_self(assessment, CryptoBtcResolutionAssessment, "assessment")
    for name in _IDENTITY_FIELDS:
        _identifier(name, getattr(assessment, name))
    _member(
        "resolution_contract_status",
        assessment.resolution_contract_status,
        CRYPTO_BTC_RESOLUTION_CONTRACT_STATUSES,
    )
    reason_codes = _reason_code_tuple("reason_codes", assessment.reason_codes)
    _validate_status_consistency(assessment.resolution_contract_status, reason_codes)
    _require_hard_flags("assessment", assessment)


def check_crypto_btc_resolution_contract(
    contract: CryptoBtcResolutionContract,
    *,
    condition_id: str,
    market_slug: str,
    event_template: str,
    incident_gates: CryptoBtcIncidentGates,
    evaluated_at: datetime,
) -> CryptoBtcResolutionAssessment:
    """Assess a BTC resolution contract against evaluator identity and gates.

    The evaluator-supplied ``condition_id``, ``market_slug``, and
    ``event_template`` must match the contract exactly. The contract's
    ``btc_resolution_rules`` catalog identity must resolve through the pinned
    trusted-catalog resolver at ``evaluated_at``. Any blocking incident gate
    wins over the watch-level derivatives degradation; with no signals and a
    valid identity-bound contract the assessment passes.
    """
    _validate_contract_state(contract)
    checker_condition_id = _identifier("condition_id", condition_id)
    checker_market_slug = _identifier("market_slug", market_slug)
    checker_event_template = _identifier("event_template", event_template)
    _validate_gates_state(incident_gates)
    evaluation_time = _utc_datetime("evaluated_at", evaluated_at)

    reason_codes = _contract_reason_codes(
        contract,
        checker_condition_id=checker_condition_id,
        checker_market_slug=checker_market_slug,
        checker_event_template=checker_event_template,
        incident_gates=incident_gates,
        evaluation_time=evaluation_time,
    )
    status = _status_for_reason_codes(reason_codes)
    if status == "pass":
        reason_codes = (CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE,)
    return CryptoBtcResolutionAssessment(
        condition_id=contract.condition_id,
        market_slug=contract.market_slug,
        event_template=contract.event_template,
        resolution_contract_status=status,
        reason_codes=reason_codes,
    )


def crypto_btc_resolution_contract_payload(
    contract: CryptoBtcResolutionContract,
    assessment: CryptoBtcResolutionAssessment,
) -> dict[str, object]:
    """Return the canonical sorted payload for a contract and its assessment."""
    _validate_contract_state(contract)
    _validate_assessment_state(assessment)
    for name in _IDENTITY_FIELDS:
        if getattr(assessment, name) != getattr(contract, name):
            raise ValueError(
                f"assessment.{name} must match the bound contract identity",
            )
    return {
        "close_time": (
            contract.close_time.isoformat()
            if contract.close_time is not None
            else None
        ),
        "condition_id": contract.condition_id,
        "contract_version": contract.contract_version,
        "event_template": contract.event_template,
        "market_slug": contract.market_slug,
        "paper_only": contract.paper_only,
        "question_text": contract.question_text,
        "readonly": contract.readonly,
        "reason_codes": list(assessment.reason_codes),
        "report_only": contract.report_only,
        "resolution_catalog_record_digest": (
            contract.resolution_catalog_record_digest
        ),
        "resolution_catalog_record_id": contract.resolution_catalog_record_id,
        "resolution_contract_status": assessment.resolution_contract_status,
        "rules_summary": contract.rules_summary,
    }


def _contract_reason_codes(
    contract: CryptoBtcResolutionContract,
    *,
    checker_condition_id: str,
    checker_market_slug: str,
    checker_event_template: str,
    incident_gates: CryptoBtcIncidentGates,
    evaluation_time: datetime,
) -> tuple[str, ...]:
    emitted: set[str] = set()
    if contract.condition_id != checker_condition_id:
        emitted.add("condition_id_mismatch")
    if contract.market_slug != checker_market_slug:
        emitted.add("market_slug_mismatch")
    if contract.event_template != checker_event_template:
        emitted.add("event_template_mismatch")
    if (
        len(contract.question_text)
        < CRYPTO_BTC_RESOLUTION_MINIMUM_QUESTION_CHARACTERS
    ):
        emitted.add("question_text_too_short")
    if (
        len(contract.rules_summary)
        < CRYPTO_BTC_RESOLUTION_MINIMUM_RULES_SUMMARY_CHARACTERS
    ):
        emitted.add("rules_summary_too_short")
    if not _is_objective_rules_summary(contract.rules_summary):
        emitted.add("rules_summary_not_objective")
    if contract.close_time is None:
        emitted.add("missing_close_time")
    if not _resolution_catalog_record_available(contract, evaluation_time):
        emitted.add("resolution_catalog_record_unresolved")
    for gate_field, reason_code in _BLOCKING_INCIDENT_REASON_CODES:
        if getattr(incident_gates, gate_field):
            emitted.add(reason_code)
    if incident_gates.derivatives_feed_degraded:
        emitted.add("incident_derivatives_feed_degraded")
    return tuple(
        code for code in CRYPTO_BTC_RESOLUTION_REASON_CODES if code in emitted
    )


def _is_objective_rules_summary(rules_summary: str) -> bool:
    normalized = rules_summary.casefold()
    has_resolution_term = any(
        term in normalized for term in _RULES_RESOLUTION_TERMS
    )
    has_objective_source = any(
        term in normalized for term in _RULES_OBJECTIVE_SOURCE_TERMS
    )
    has_ambiguous_term = any(
        term in normalized for term in _RULES_AMBIGUOUS_TERMS
    )
    return (
        has_resolution_term
        and has_objective_source
        and not has_ambiguous_term
    )


def _resolution_catalog_record_available(
    contract: CryptoBtcResolutionContract,
    evaluation_time: datetime,
) -> bool:
    """Resolve the bound ``btc_resolution_rules`` record, failing closed.

    The pinned catalog resolver raises ``ValueError`` on every fail-closed
    path (unknown source or record, digest mismatch, family mismatch, or an
    out-of-window ``evaluated_at``); each path maps here to a blocked
    assessment. A resolved record bound to any other source also fails.
    """
    try:
        record = resolve_trusted_crypto_btc_source_record(
            CRYPTO_BTC_RESOLUTION_RULES_SOURCE_ID,
            contract.resolution_catalog_record_id,
            contract.resolution_catalog_record_digest,
            evaluated_at=evaluation_time,
        )
    except ValueError:
        return False
    return (
        getattr(record, "source_id", None)
        == CRYPTO_BTC_RESOLUTION_RULES_SOURCE_ID
    )
