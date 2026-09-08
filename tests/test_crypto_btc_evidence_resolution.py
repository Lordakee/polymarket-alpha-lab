"""Red/green tests for the identity-bound BTC resolution-contract module.

Catalog verification is delegated to the pinned resolver from
``crypto_btc_evidence_catalog`` (Worker B); when absent this file installs
a faithful stub of the pinned interface and the same tests run unchanged.
"""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, dataclass
from datetime import UTC, datetime, timedelta, timezone
import inspect
from types import ModuleType, SimpleNamespace
import sys
from typing import Final, final

import pytest

@final
@dataclass(frozen=True, slots=True)
class _StubTrustedSourceRecord:
    source_id: str
    record_id: str
    record_digest: str
    source_family: str
    release_vintage: str
    catalog_version: str
    valid_from: datetime
    valid_until: datetime

class _StubCatalogError(ValueError):
    """Fail-closed error surface mirroring the pinned catalog resolver."""

_STUB_RESOLUTION_RECORD: Final = _StubTrustedSourceRecord(
    source_id="btc_resolution_rules", record_id="btc-resolution-rules-record-v0",
    record_digest="a" * 64, source_family="btc_resolution_rules",
    release_vintage="2026-07-stable", catalog_version="crypto-btc-source-catalog-v0",
    valid_from=datetime(2020, 1, 1, tzinfo=UTC),
    valid_until=datetime(2030, 1, 1, tzinfo=UTC),
)

def _stub_trusted_catalog() -> tuple[_StubTrustedSourceRecord, ...]:
    return (_STUB_RESOLUTION_RECORD,)

def _stub_resolve(
    source_id: object, record_id: object, record_digest: object,
    *, evaluated_at: object,
) -> _StubTrustedSourceRecord:
    if (
        type(source_id) is not str
        or type(record_id) is not str
        or type(record_digest) is not str
        or type(evaluated_at) is not datetime
        or evaluated_at.tzinfo is None
    ):
        raise _StubCatalogError("resolver arguments are invalid")
    for record in _stub_trusted_catalog():
        if record.source_id == source_id and record.record_id == record_id:
            if record.record_digest != record_digest:
                raise _StubCatalogError("trusted record digest mismatch")
            if evaluated_at < record.valid_from or evaluated_at > record.valid_until:
                raise _StubCatalogError("trusted record is not valid at evaluated_at")
            return record
    raise _StubCatalogError("trusted record is unknown")

def _install_stub_catalog() -> ModuleType:
    module = ModuleType("polymarket_alpha_lab.crypto_btc_evidence_catalog")
    module.CryptoBtcTrustedSourceRecord = _StubTrustedSourceRecord
    module.trusted_crypto_btc_source_catalog = _stub_trusted_catalog
    module.resolve_trusted_crypto_btc_source_record = _stub_resolve
    sys.modules[module.__name__] = module
    return module

try:
    from polymarket_alpha_lab import crypto_btc_evidence_catalog as catalog_module
except ImportError as _catalog_error:
    # Absence raises ModuleNotFoundError(name=<catalog>) or a plain ImportError
    # ("cannot import name '<catalog>' ..."). Other import failures are real.
    _absent = (
        getattr(_catalog_error, "name", None)
        == "polymarket_alpha_lab.crypto_btc_evidence_catalog"
        or str(_catalog_error).startswith(
            "cannot import name 'crypto_btc_evidence_catalog'"
        )
    )
    if not _absent:
        raise
    catalog_module = _install_stub_catalog()
    CATALOG_BACKEND_IS_STUB = True
else:
    CATALOG_BACKEND_IS_STUB = False

from polymarket_alpha_lab.crypto_btc_evidence_resolution import (  # noqa: E402
    CRYPTO_BTC_RESOLUTION_ALL_REASON_CODES, CRYPTO_BTC_RESOLUTION_BLOCKING_REASON_CODES,
    CRYPTO_BTC_RESOLUTION_CONTRACT_STATUSES, CRYPTO_BTC_RESOLUTION_CONTRACT_VERSION,
    CRYPTO_BTC_RESOLUTION_MINIMUM_QUESTION_CHARACTERS,
    CRYPTO_BTC_RESOLUTION_MINIMUM_RULES_SUMMARY_CHARACTERS,
    CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE, CRYPTO_BTC_RESOLUTION_REASON_CODES,
    CRYPTO_BTC_RESOLUTION_RULES_SOURCE_ID, CRYPTO_BTC_RESOLUTION_WATCH_REASON_CODES,
    CryptoBtcIncidentGates, CryptoBtcResolutionAssessment, CryptoBtcResolutionContract,
    check_crypto_btc_resolution_contract, crypto_btc_resolution_contract_payload,
)
import polymarket_alpha_lab.crypto_btc_evidence_resolution as resolution_module  # noqa: E402

CONDITION_ID: Final = "condition-7f3a2b9c"
MARKET_SLUG: Final = "will-btc-reach-100k-before-2027"
EVENT_TEMPLATE: Final = "btc-price-milestone-2026"
QUESTION_TEXT: Final = (
    "Will Bitcoin trade at or above 100,000 USDC before this market closes?"
)
RULES_SUMMARY: Final = (
    "This market resolves YES only if the official Polymarket resolution rules "
    "confirm the objective BTC price condition on the approved reference source."
)

_GATE_FIELDS: Final = (
    ("source_outage", "incident_source_outage"),
    ("index_dislocation", "incident_index_dislocation"),
    ("chain_reorg", "incident_chain_reorg"),
    ("resolution_rule_change", "incident_resolution_rule_change"),
    ("market_halt", "incident_market_halt"),
    ("derivatives_feed_degraded", "incident_derivatives_feed_degraded"),
)
_BLOCKING_GATE_FIELDS: Final = tuple(
    (f, c) for f, c in _GATE_FIELDS if c != "incident_derivatives_feed_degraded"
)
_RULES_WITHOUT_RESOLUTION_TERM: Final = (
    "The official Polymarket market rules documentation applies to this market "
    "outcome in full, and no other subjective judgment is permitted anywhere "
    "in the settlement of the position for all participants involved."
)
_RULES_WITHOUT_OBJECTIVE_SOURCE: Final = (
    "This market resolves YES when the internal committee decides the outcome "
    "using its own judgment about the overall trajectory and sentiment of the "
    "underlying asset over the entire evaluation window in question."
)
_RULES_WITH_AMBIGUOUS_TERM: Final = (
    "This market resolves YES when news reports and social media consensus "
    "confirm the official outcome, even if primary sources remain unclear at "
    "the time the market is scheduled to be settled and paid out."
)

def _resolution_record() -> object:
    for record in catalog_module.trusted_crypto_btc_source_catalog():
        if getattr(record, "source_id", None) == "btc_resolution_rules":
            return record
    pytest.fail("trusted catalog must expose a btc_resolution_rules record")

def _record_id() -> str:
    return _resolution_record().record_id

def _record_digest() -> str:
    return _resolution_record().record_digest

def _other_digest() -> str:
    for candidate in ("0" * 64, "1" * 64, "2" * 64):
        if candidate != _record_digest():
            return candidate
    pytest.fail("could not derive a distinct canonical digest")

def _evaluated_at() -> datetime:
    record = _resolution_record()
    valid_from, valid_until = record.valid_from, record.valid_until
    if valid_until > valid_from + timedelta(days=2):
        return valid_from + (valid_until - valid_from) / 2
    return valid_from

def _expired_evaluated_at() -> datetime:
    return _resolution_record().valid_until + timedelta(days=1)

def _close_time() -> datetime:
    return datetime(2027, 1, 1, 0, 0, 0, tzinfo=UTC)

def _contract(**overrides: object) -> CryptoBtcResolutionContract:
    fields: dict[str, object] = {
        "condition_id": CONDITION_ID, "market_slug": MARKET_SLUG,
        "event_template": EVENT_TEMPLATE, "question_text": QUESTION_TEXT,
        "rules_summary": RULES_SUMMARY, "close_time": _close_time(),
        "resolution_catalog_record_id": _record_id(),
        "resolution_catalog_record_digest": _record_digest(),
        "contract_version": CRYPTO_BTC_RESOLUTION_CONTRACT_VERSION,
    }
    fields.update(overrides)
    return CryptoBtcResolutionContract(**fields)

def _gates(**overrides: object) -> CryptoBtcIncidentGates:
    fields: dict[str, object] = {
        "source_outage": False, "index_dislocation": False, "chain_reorg": False,
        "resolution_rule_change": False, "market_halt": False,
        "derivatives_feed_degraded": False,
    }
    fields.update(overrides)
    return CryptoBtcIncidentGates(**fields)

def _assessment(**overrides: object) -> CryptoBtcResolutionAssessment:
    fields: dict[str, object] = {
        "condition_id": CONDITION_ID, "market_slug": MARKET_SLUG,
        "event_template": EVENT_TEMPLATE, "resolution_contract_status": "pass",
        "reason_codes": (CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE,),
    }
    fields.update(overrides)
    return CryptoBtcResolutionAssessment(**fields)

def _check(
    contract: CryptoBtcResolutionContract | None = None,
    *,
    gates: CryptoBtcIncidentGates | None = None,
    condition_id: str = CONDITION_ID,
    market_slug: str = MARKET_SLUG,
    event_template: str = EVENT_TEMPLATE,
    evaluated_at: datetime | None = None,
) -> CryptoBtcResolutionAssessment:
    return check_crypto_btc_resolution_contract(
        _contract() if contract is None else contract,
        condition_id=condition_id, market_slug=market_slug,
        event_template=event_template,
        incident_gates=_gates() if gates is None else gates,
        evaluated_at=_evaluated_at() if evaluated_at is None else evaluated_at,
    )

def _question_of_exact_length(length: int) -> str:
    prefix = "Will Bitcoin resolve YES "
    return prefix + "z" * (length - len(prefix)) if length > len(prefix) else "q" * length

def _rules_of_exact_length(length: int) -> str:
    prefix = "Resolves per official Polymarket rules using "
    return prefix + "z" * (length - len(prefix)) if length > len(prefix) else "r" * length

class TestCatalogBackend:
    def test_backend_resolves_the_pinned_interface(self) -> None:
        resolver = catalog_module.resolve_trusted_crypto_btc_source_record
        parameters = inspect.signature(resolver).parameters
        assert list(parameters) == [
            "source_id", "record_id", "record_digest", "evaluated_at",
        ]
        assert parameters["evaluated_at"].kind is inspect.Parameter.KEYWORD_ONLY
    def test_resolution_module_binds_the_backend_resolver(self) -> None:
        bound = resolution_module.resolve_trusted_crypto_btc_source_record
        assert bound is catalog_module.resolve_trusted_crypto_btc_source_record
    def test_backend_exposes_trusted_record_type_and_catalog(self) -> None:
        assert hasattr(catalog_module, "CryptoBtcTrustedSourceRecord")
        catalog = catalog_module.trusted_crypto_btc_source_catalog()
        assert type(catalog) is tuple
        assert any(getattr(r, "source_id", None) == "btc_resolution_rules" for r in catalog)

class TestPinnedConstants:
    def test_statuses_lengths_and_source_binding_are_pinned(self) -> None:
        assert CRYPTO_BTC_RESOLUTION_CONTRACT_STATUSES == ("pass", "watch", "blocked")
        assert CRYPTO_BTC_RESOLUTION_RULES_SOURCE_ID == "btc_resolution_rules"
        assert CRYPTO_BTC_RESOLUTION_CONTRACT_VERSION == "crypto-btc-resolution-contract-v0"
        assert CRYPTO_BTC_RESOLUTION_MINIMUM_QUESTION_CHARACTERS == 40
        assert CRYPTO_BTC_RESOLUTION_MINIMUM_RULES_SUMMARY_CHARACTERS == 80
    def test_reason_code_vocabulary_is_closed_unique_and_ordered(self) -> None:
        expected = (
            "condition_id_mismatch", "market_slug_mismatch",
            "event_template_mismatch", "question_text_too_short",
            "rules_summary_too_short", "rules_summary_not_objective",
            "missing_close_time", "resolution_catalog_record_unresolved",
            "incident_source_outage", "incident_index_dislocation",
            "incident_chain_reorg", "incident_resolution_rule_change",
            "incident_market_halt", "incident_derivatives_feed_degraded",
        )
        assert CRYPTO_BTC_RESOLUTION_REASON_CODES == expected
        assert CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE == (
            "crypto_btc_resolution_contract_passed"
        )
        assert CRYPTO_BTC_RESOLUTION_ALL_REASON_CODES == (
            CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE, *expected,
        )
        codes = list(CRYPTO_BTC_RESOLUTION_ALL_REASON_CODES)
        assert len(codes) == len(set(codes))
    def test_watch_and_blocking_partition_the_vocabulary(self) -> None:
        assert CRYPTO_BTC_RESOLUTION_WATCH_REASON_CODES == (
            "incident_derivatives_feed_degraded",
        )
        assert set(CRYPTO_BTC_RESOLUTION_BLOCKING_REASON_CODES) == set(
            CRYPTO_BTC_RESOLUTION_REASON_CODES,
        ).difference(CRYPTO_BTC_RESOLUTION_WATCH_REASON_CODES)
        assert "incident_derivatives_feed_degraded" not in (
            CRYPTO_BTC_RESOLUTION_BLOCKING_REASON_CODES
        )

class TestContractConstruction:
    def test_valid_contract_holds_exact_bound_values(self) -> None:
        contract = _contract()
        assert (contract.condition_id, contract.market_slug, contract.event_template) == (
            CONDITION_ID, MARKET_SLUG, EVENT_TEMPLATE,
        )
        assert (contract.question_text, contract.rules_summary) == (
            QUESTION_TEXT, RULES_SUMMARY,
        )
        assert contract.close_time == _close_time()
        assert contract.resolution_catalog_record_id == _record_id()
        assert contract.resolution_catalog_record_digest == _record_digest()
        assert contract.contract_version == CRYPTO_BTC_RESOLUTION_CONTRACT_VERSION
        assert (contract.paper_only, contract.report_only, contract.readonly) == (
            True, True, True,
        )

    def test_contract_is_frozen_slotted_and_final(self) -> None:
        with pytest.raises(FrozenInstanceError):
            _contract().condition_id = "condition-other"  # type: ignore[misc]
        assert not hasattr(_contract(), "__dict__")
        with pytest.raises(TypeError):
            class _Sub(CryptoBtcResolutionContract):  # noqa: F811
                pass
    def test_contract_text_is_stripped_at_construction(self) -> None:
        contract = _contract(
            question_text=f"  {QUESTION_TEXT}  ",
            rules_summary=f"\n\t{RULES_SUMMARY} \n",
        )
        assert contract.question_text == QUESTION_TEXT
        assert contract.rules_summary == RULES_SUMMARY
    def test_close_time_normalization_rules(self) -> None:
        shifted = datetime(2027, 1, 1, 5, 0, 0, tzinfo=timezone(timedelta(hours=5)))
        contract = _contract(close_time=shifted)
        assert contract.close_time == datetime(2027, 1, 1, 0, 0, 0, tzinfo=UTC)
        assert contract.close_time.utcoffset() == timedelta(0)
        with pytest.raises(ValueError, match="close_time"):
            _contract(close_time=datetime(2027, 1, 1, 0, 0, 0))
        assert _contract(close_time=None).close_time is None

    @pytest.mark.parametrize("field", [
        "condition_id", "market_slug", "event_template",
        "resolution_catalog_record_id", "contract_version",
    ])
    @pytest.mark.parametrize("value", [None, 7, "", " leading", "trailing ", "Pad"])
    def test_non_canonical_identifiers_are_rejected(
        self, field: str, value: object,
    ) -> None:
        with pytest.raises(ValueError, match=field):
            _contract(**{field: value})

    @pytest.mark.parametrize("digest", ["", "A" * 64, "0" * 63, "0" * 65, "g" * 64, 123])
    def test_non_canonical_digest_is_rejected(self, digest: object) -> None:
        with pytest.raises(ValueError, match="digest"):
            _contract(resolution_catalog_record_digest=digest)

    @pytest.mark.parametrize("field", ["question_text", "rules_summary"])
    @pytest.mark.parametrize("value", [None, 41, b"text"])
    def test_non_string_text_is_rejected(self, field: str, value: object) -> None:
        with pytest.raises(ValueError, match=field):
            _contract(**{field: value})

    @pytest.mark.parametrize("flag", ["paper_only", "report_only", "readonly"])
    def test_false_hard_flags_are_rejected(self, flag: str) -> None:
        with pytest.raises(ValueError, match=flag):
            _contract(**{flag: False})

class TestIncidentGatesConstruction:
    def test_valid_gates_hold_exact_bound_values_and_order(self) -> None:
        gates = _gates()
        assert tuple(f for f, _c in _GATE_FIELDS) == (
            "source_outage", "index_dislocation", "chain_reorg",
            "resolution_rule_change", "market_halt", "derivatives_feed_degraded",
        )
        assert all(getattr(gates, f) is False for f, _c in _GATE_FIELDS)
        assert (gates.paper_only, gates.report_only, gates.readonly) == (
            True, True, True,
        )
    def test_gates_are_frozen_slotted_and_final(self) -> None:
        with pytest.raises(FrozenInstanceError):
            _gates().source_outage = True  # type: ignore[misc]
        assert not hasattr(_gates(), "__dict__")
        with pytest.raises(TypeError):
            class _Sub(CryptoBtcIncidentGates):  # noqa: F811
                pass

    @pytest.mark.parametrize("field", [f for f, _c in _GATE_FIELDS])
    @pytest.mark.parametrize("value", [1, 0, "true", None])
    def test_non_bool_gate_values_are_rejected(
        self, field: str, value: object,
    ) -> None:
        with pytest.raises(ValueError, match=field):
            _gates(**{field: value})

    @pytest.mark.parametrize("flag", ["paper_only", "report_only", "readonly"])
    def test_false_hard_flags_are_rejected(self, flag: str) -> None:
        with pytest.raises(ValueError, match=flag):
            _gates(**{flag: False})

class TestAssessmentConstruction:
    def test_valid_assessment_holds_exact_bound_values(self) -> None:
        assessment = _assessment()
        assert (
            assessment.condition_id, assessment.market_slug, assessment.event_template
        ) == (CONDITION_ID, MARKET_SLUG, EVENT_TEMPLATE)
        assert assessment.resolution_contract_status == "pass"
        assert assessment.reason_codes == (CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE,)
        assert (
            assessment.paper_only, assessment.report_only, assessment.readonly
        ) == (True, True, True)
    def test_assessment_is_frozen_slotted_and_final(self) -> None:
        with pytest.raises(FrozenInstanceError):
            _assessment().resolution_contract_status = "blocked"  # type: ignore[misc]
        assert not hasattr(_assessment(), "__dict__")
        with pytest.raises(TypeError):
            class _Sub(CryptoBtcResolutionAssessment):  # noqa: F811
                pass

    @pytest.mark.parametrize("status", ["", "ok", "PASS", "blocked ", None, 3])
    def test_unknown_status_is_rejected(self, status: object) -> None:
        with pytest.raises(ValueError):
            _assessment(resolution_contract_status=status)

    @pytest.mark.parametrize("reason_codes", [
        (), [],
        ("not_a_reason_code",),
        (CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE,) * 2,
        ("missing_close_time", "missing_close_time"),
    ])
    def test_non_canonical_reason_codes_are_rejected(
        self, reason_codes: object,
    ) -> None:
        with pytest.raises(ValueError, match="reason_codes"):
            _assessment(
                resolution_contract_status="blocked", reason_codes=reason_codes,
            )
    def test_reason_code_order_and_status_consistency_are_enforced(self) -> None:
        with pytest.raises(ValueError, match="reason_codes"):
            _assessment(
                resolution_contract_status="blocked",
                reason_codes=(
                    "incident_derivatives_feed_degraded", "incident_market_halt",
                ),
            )
        with pytest.raises(ValueError):
            _assessment(
                resolution_contract_status="pass",
                reason_codes=(
                    CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE, "missing_close_time",
                ),
            )
        with pytest.raises(ValueError):
            _assessment(resolution_contract_status="blocked",
                        reason_codes=(CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE,))
    def test_watch_and_blocked_status_rules(self) -> None:
        watch = _assessment(
            resolution_contract_status="watch",
            reason_codes=("incident_derivatives_feed_degraded",),
        )
        assert watch.reason_codes == ("incident_derivatives_feed_degraded",)
        with pytest.raises(ValueError):
            _assessment(
                resolution_contract_status="watch",
                reason_codes=(
                    "incident_derivatives_feed_degraded", "missing_close_time",
                ),
            )
        blocked = _assessment(
            resolution_contract_status="blocked",
            reason_codes=(
                "incident_market_halt", "incident_derivatives_feed_degraded",
            ),
        )
        assert blocked.resolution_contract_status == "blocked"
        with pytest.raises(ValueError):
            _assessment(
                resolution_contract_status="blocked",
                reason_codes=("incident_derivatives_feed_degraded",),
            )

    @pytest.mark.parametrize("flag", ["paper_only", "report_only", "readonly"])
    def test_false_hard_flags_are_rejected(self, flag: str) -> None:
        with pytest.raises(ValueError, match=flag):
            _assessment(**{flag: False})

class TestCheckerSignature:
    def test_checker_and_payload_signatures_are_pinned(self) -> None:
        parameters = inspect.signature(
            check_crypto_btc_resolution_contract,
        ).parameters
        assert list(parameters) == [
            "contract", "condition_id", "market_slug", "event_template",
            "incident_gates", "evaluated_at",
        ]
        assert parameters["contract"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        for name in ("condition_id", "market_slug", "event_template",
                     "incident_gates", "evaluated_at"):
            assert parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        parameters = inspect.signature(
            crypto_btc_resolution_contract_payload,
        ).parameters
        assert list(parameters) == ["contract", "assessment"]
        for name in ("contract", "assessment"):
            assert parameters[name].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD

class TestIdentityBinding:
    def test_matching_identity_with_clean_gates_passes(self) -> None:
        assessment = _check()
        assert assessment.resolution_contract_status == "pass"
        assert assessment.reason_codes == (CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE,)
        assert assessment.condition_id == CONDITION_ID
        assert assessment.market_slug == MARKET_SLUG
        assert assessment.event_template == EVENT_TEMPLATE

    @pytest.mark.parametrize(("field", "value", "code"), [
        ("condition_id", "condition-00000001", "condition_id_mismatch"),
        ("market_slug", "will-btc-reach-200k-before-2027", "market_slug_mismatch"),
        ("event_template", "btc-price-milestone-2025", "event_template_mismatch"),
    ])
    def test_each_identity_mismatch_alone_blocks_with_exact_reason(
        self, field: str, value: str, code: str,
    ) -> None:
        assessment = _check(**{field: value})
        assert assessment.resolution_contract_status == "blocked"
        assert assessment.reason_codes == (code,)
    def test_all_identity_mismatches_are_reported_in_canonical_order(self) -> None:
        assessment = _check(condition_id="condition-00000001",
                            market_slug="will-btc-reach-200k-before-2027",
                            event_template="btc-price-milestone-2025")
        assert assessment.resolution_contract_status == "blocked"
        assert assessment.reason_codes == (
            "condition_id_mismatch", "market_slug_mismatch",
            "event_template_mismatch",
        )

    @pytest.mark.parametrize(("field", "value"), [
        ("condition_id", "not canonical"), ("market_slug", ""),
        ("event_template", " padded "),
    ])
    def test_non_canonical_checker_identity_is_rejected(
        self, field: str, value: str,
    ) -> None:
        with pytest.raises(ValueError, match=field):
            _check(**{field: value})
    def test_checker_input_datetime_rules(self) -> None:
        with pytest.raises(ValueError, match="evaluated_at"):
            _check(evaluated_at=datetime(2026, 7, 13, 12, 0, 0))
        shifted = datetime(2026, 7, 13, 7, 0, 0, tzinfo=timezone(timedelta(hours=-5)))
        assert _check(evaluated_at=shifted).resolution_contract_status == "pass"
    def test_checker_rejects_wrong_contract_and_gates_types(self) -> None:
        with pytest.raises(ValueError, match="contract"):
            check_crypto_btc_resolution_contract(
                "contract", condition_id=CONDITION_ID, market_slug=MARKET_SLUG,
                event_template=EVENT_TEMPLATE, incident_gates=_gates(),
                evaluated_at=_evaluated_at(),
            )
        with pytest.raises(ValueError, match="gates"):
            _check(gates=SimpleNamespace(source_outage=False))  # type: ignore[arg-type]

class TestContractContent:
    @pytest.mark.parametrize(("overrides", "expected"), [
        ({"question_text": _question_of_exact_length(40)}, ()),
        ({"question_text": _question_of_exact_length(39)}, ("question_text_too_short",)),
        ({"question_text": ""}, ("question_text_too_short",)),
        ({"rules_summary": _rules_of_exact_length(80)}, ()),
        ({"rules_summary": _rules_of_exact_length(79)}, ("rules_summary_too_short",)),
        ({"rules_summary": _rules_of_exact_length(20)},
         ("rules_summary_too_short", "rules_summary_not_objective")),
        ({"rules_summary": _RULES_WITHOUT_RESOLUTION_TERM},
         ("rules_summary_not_objective",)),
        ({"rules_summary": _RULES_WITHOUT_OBJECTIVE_SOURCE},
         ("rules_summary_not_objective",)),
        ({"rules_summary": _RULES_WITH_AMBIGUOUS_TERM},
         ("rules_summary_not_objective",)),
        ({"close_time": None}, ("missing_close_time",)),
        ({"question_text": "", "rules_summary": _RULES_WITHOUT_OBJECTIVE_SOURCE,
          "close_time": None},
         ("question_text_too_short", "rules_summary_not_objective",
          "missing_close_time")),
    ])
    def test_content_requirements_map_to_exact_reason_codes(
        self, overrides: dict[str, object], expected: tuple[str, ...],
    ) -> None:
        assessment = _check(contract=_contract(**overrides))
        if expected:
            assert assessment.resolution_contract_status == "blocked"
            assert assessment.reason_codes == expected
        else:
            assert assessment.resolution_contract_status == "pass"
            assert assessment.reason_codes == (
                CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE,
            )
    def test_boundary_fixture_semantics(self) -> None:
        assert len(_question_of_exact_length(40)) == 40
        assert len(_question_of_exact_length(39)) == 39
        assert len(_rules_of_exact_length(80)) == 80
        assert len(_rules_of_exact_length(79)) == 79
        assert "resolv" not in _rules_of_exact_length(20)
        assert "resolv" not in _RULES_WITHOUT_RESOLUTION_TERM.casefold()
        normalized = _RULES_WITHOUT_OBJECTIVE_SOURCE.casefold()
        assert "resolv" in normalized
        assert not any(t in normalized for t in ("official", "polymarket", "market rules"))
        ambiguous = _RULES_WITH_AMBIGUOUS_TERM.casefold()
        assert "news reports" in ambiguous and "social media" in ambiguous
    def test_objective_source_terms_are_matched_case_insensitively(self) -> None:
        rules = (
            "This market RESOLVES strictly per OFFICIAL Polymarket documentation "
            "and the deterministic price condition stated for settlement."
        )
        assessment = _check(contract=_contract(rules_summary=rules))
        assert "rules_summary_not_objective" not in assessment.reason_codes

class TestCatalogVerification:
    def test_valid_catalog_identity_passes(self) -> None:
        assessment = _check()
        assert assessment.resolution_contract_status == "pass"
        assert assessment.reason_codes == (CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE,)
    def test_unknown_record_id_is_blocked(self) -> None:
        assessment = _check(contract=_contract(
            resolution_catalog_record_id="btc-resolution-rules-record-x",
        ))
        assert assessment.resolution_contract_status == "blocked"
        assert assessment.reason_codes == ("resolution_catalog_record_unresolved",)
    def test_digest_mismatch_and_expired_record_are_blocked(self) -> None:
        assessment = _check(
            contract=_contract(resolution_catalog_record_digest=_other_digest()),
        )
        assert assessment.resolution_contract_status == "blocked"
        assert assessment.reason_codes == ("resolution_catalog_record_unresolved",)
        assessment = _check(evaluated_at=_expired_evaluated_at())
        assert assessment.resolution_contract_status == "blocked"
        assert assessment.reason_codes == ("resolution_catalog_record_unresolved",)
    def test_resolver_value_error_maps_to_blocked(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _explode(*args: object, **kwargs: object) -> object:
            raise ValueError("catalog backend fail-closed rejection")

        monkeypatch.setattr(
            resolution_module, "resolve_trusted_crypto_btc_source_record", _explode,
        )
        assessment = _check()
        assert assessment.resolution_contract_status == "blocked"
        assert assessment.reason_codes == ("resolution_catalog_record_unresolved",)
    def test_resolver_foreign_source_record_maps_to_blocked(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _foreign(*args: object, **kwargs: object) -> object:
            return SimpleNamespace(source_id="btc_spot_reference")

        monkeypatch.setattr(
            resolution_module, "resolve_trusted_crypto_btc_source_record", _foreign,
        )
        assessment = _check()
        assert assessment.resolution_contract_status == "blocked"
        assert assessment.reason_codes == ("resolution_catalog_record_unresolved",)
    def test_resolver_is_called_with_the_pinned_arguments(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        calls: list[tuple[object, dict[str, object]]] = []

        def _spy(*args: object, **kwargs: object) -> object:
            calls.append((args, kwargs))
            return catalog_module.resolve_trusted_crypto_btc_source_record(
                *args, **kwargs,
            )

        monkeypatch.setattr(
            resolution_module, "resolve_trusted_crypto_btc_source_record", _spy,
        )
        evaluated_at = _evaluated_at()
        _check(evaluated_at=evaluated_at)
        assert calls == [(
            ("btc_resolution_rules", _record_id(), _record_digest()),
            {"evaluated_at": evaluated_at},
        )]
    def test_catalog_failure_combines_with_identity_mismatch_in_order(self) -> None:
        assessment = _check(
            contract=_contract(
                resolution_catalog_record_id="btc-resolution-rules-record-x",
            ),
            condition_id="condition-00000001",
        )
        assert assessment.reason_codes == (
            "condition_id_mismatch", "resolution_catalog_record_unresolved",
        )

class TestIncidentGateAssessment:
    @pytest.mark.parametrize(("field", "code"), _BLOCKING_GATE_FIELDS)
    def test_each_blocking_gate_alone_blocks_with_exact_reason(
        self, field: str, code: str,
    ) -> None:
        assessment = _check(gates=_gates(**{field: True}))
        assert assessment.resolution_contract_status == "blocked"
        assert assessment.reason_codes == (code,)
    def test_derivatives_degradation_alone_watches(self) -> None:
        assessment = _check(gates=_gates(derivatives_feed_degraded=True))
        assert assessment.resolution_contract_status == "watch"
        assert assessment.reason_codes == ("incident_derivatives_feed_degraded",)

    @pytest.mark.parametrize(("field", "code"), _BLOCKING_GATE_FIELDS)
    def test_blocked_takes_precedence_over_watch(
        self, field: str, code: str,
    ) -> None:
        assessment = _check(
            gates=_gates(**{field: True, "derivatives_feed_degraded": True}),
        )
        assert assessment.resolution_contract_status == "blocked"
        assert assessment.reason_codes == (code, "incident_derivatives_feed_degraded")
    def test_all_gates_true_report_every_incident_in_canonical_order(self) -> None:
        assessment = _check(gates=_gates(
            source_outage=True, index_dislocation=True, chain_reorg=True,
            resolution_rule_change=True, market_halt=True,
            derivatives_feed_degraded=True,
        ))
        assert assessment.resolution_contract_status == "blocked"
        assert assessment.reason_codes == tuple(c for _f, c in _GATE_FIELDS)
    def test_every_gate_permutation_maps_deterministically(self) -> None:
        for mask in range(64):
            overrides = {
                field: bool(mask >> index & 1)
                for index, (field, _code) in enumerate(_GATE_FIELDS)
            }
            assessment = _check(gates=_gates(**overrides))
            expected_codes = tuple(c for f, c in _GATE_FIELDS if overrides[f])
            blocking = any(
                c != "incident_derivatives_feed_degraded" for c in expected_codes
            )
            expected_status = (
                "blocked" if blocking else "watch" if expected_codes else "pass"
            )
            if expected_status == "pass":
                expected_codes = (CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE,)
            assert assessment.resolution_contract_status == expected_status
            assert assessment.reason_codes == expected_codes

class TestDeterminism:
    def test_all_failures_report_the_full_canonical_code_tuple(self) -> None:
        contract = _contract(
            condition_id="condition-00000001",
            market_slug="will-btc-reach-200k-before-2027",
            event_template="btc-price-milestone-2025",
            question_text="", rules_summary="", close_time=None,
            resolution_catalog_record_id="btc-resolution-rules-record-x",
        )
        assessment = _check(contract=contract, gates=_gates(
            source_outage=True, index_dislocation=True, chain_reorg=True,
            resolution_rule_change=True, market_halt=True,
            derivatives_feed_degraded=True,
        ))
        assert assessment.resolution_contract_status == "blocked"
        assert assessment.reason_codes == CRYPTO_BTC_RESOLUTION_REASON_CODES
        assert set(assessment.reason_codes) <= set(
            CRYPTO_BTC_RESOLUTION_ALL_REASON_CODES,
        )
    def test_repeated_checks_produce_identical_assessments(self) -> None:
        contract = _contract(question_text="")
        first = _check(contract=contract, gates=_gates(market_halt=True))
        second = _check(contract=contract, gates=_gates(market_halt=True))
        assert first == second
        assert hash(first) == hash(second)

class TestPayload:
    def test_payload_returns_the_full_canonical_dict(self) -> None:
        assessment = _check()
        payload = crypto_btc_resolution_contract_payload(_contract(), assessment)
        assert payload == {
            "close_time": _close_time().isoformat(),
            "condition_id": CONDITION_ID,
            "contract_version": CRYPTO_BTC_RESOLUTION_CONTRACT_VERSION,
            "event_template": EVENT_TEMPLATE,
            "market_slug": MARKET_SLUG,
            "paper_only": True, "question_text": QUESTION_TEXT, "readonly": True,
            "reason_codes": [CRYPTO_BTC_RESOLUTION_PASS_REASON_CODE],
            "report_only": True,
            "resolution_catalog_record_digest": _record_digest(),
            "resolution_catalog_record_id": _record_id(),
            "resolution_contract_status": "pass",
            "rules_summary": RULES_SUMMARY,
        }
    def test_payload_keys_are_sorted(self) -> None:
        payload = crypto_btc_resolution_contract_payload(
            _contract(), _check(contract=_contract(close_time=None)),
        )
        assert list(payload) == sorted(payload)
    def test_payload_serializes_none_close_time(self) -> None:
        contract = _contract(close_time=None)
        payload = crypto_btc_resolution_contract_payload(
            contract, _check(contract=contract),
        )
        assert payload["close_time"] is None
        assert payload["resolution_contract_status"] == "blocked"
    def test_payload_reason_codes_are_a_defensive_copy(self) -> None:
        assessment = _check(gates=_gates(market_halt=True))
        payload = crypto_btc_resolution_contract_payload(_contract(), assessment)
        assert isinstance(payload["reason_codes"], list)
        payload["reason_codes"].append("tampered")
        assert assessment.reason_codes == ("incident_market_halt",)
    def test_payload_rejects_mismatched_contract_assessment_pairing(self) -> None:
        assessment = _check(contract=_contract(condition_id="condition-00000002"))
        with pytest.raises(ValueError, match="condition_id"):
            crypto_btc_resolution_contract_payload(_contract(), assessment)
    def test_payload_rejects_wrong_types(self) -> None:
        assessment = _check()
        with pytest.raises(ValueError):
            crypto_btc_resolution_contract_payload("contract", assessment)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            crypto_btc_resolution_contract_payload(_contract(), "assessment")  # type: ignore[arg-type]
    def test_payload_is_deterministic_across_calls(self) -> None:
        assessment = _check(gates=_gates(chain_reorg=True))
        first = crypto_btc_resolution_contract_payload(_contract(), assessment)
        second = crypto_btc_resolution_contract_payload(_contract(), assessment)
        assert first == second

class TestConstructorBypassTampering:
    def test_bypassed_contract_state_is_rejected_by_the_checker(self) -> None:
        contract = _contract()
        object.__setattr__(contract, "paper_only", False)
        with pytest.raises(ValueError, match="paper_only"):
            _check(contract=contract)
        contract = _contract()
        object.__setattr__(contract, "question_text", None)
        with pytest.raises(ValueError, match="question_text"):
            _check(contract=contract)
        contract = _contract()
        object.__setattr__(contract, "question_text", f" {QUESTION_TEXT} ")
        with pytest.raises(ValueError, match="question_text"):
            _check(contract=contract)
        contract = _contract()
        object.__setattr__(contract, "resolution_catalog_record_digest", "BAD")
        with pytest.raises(ValueError, match="digest"):
            _check(contract=contract)
    def test_bypassed_gate_state_is_rejected_by_the_checker(self) -> None:
        gates = _gates()
        object.__setattr__(gates, "source_outage", 1)
        with pytest.raises(ValueError, match="source_outage"):
            _check(gates=gates)
        gates = _gates()
        object.__setattr__(gates, "readonly", False)
        with pytest.raises(ValueError, match="readonly"):
            _check(gates=gates)
    def test_bypassed_assessment_state_is_rejected_by_the_payload(self) -> None:
        assessment = _check()
        object.__setattr__(assessment, "reason_codes", ("not_a_reason_code",))
        with pytest.raises(ValueError, match="reason_codes"):
            crypto_btc_resolution_contract_payload(_contract(), assessment)
        assessment = _check()
        object.__setattr__(assessment, "report_only", False)
        with pytest.raises(ValueError, match="report_only"):
            crypto_btc_resolution_contract_payload(_contract(), assessment)

class TestPurity:
    def test_module_source_contains_no_float_literals(self) -> None:
        tree = ast.parse(inspect.getsource(resolution_module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                assert not isinstance(node.value, float)
    def test_module_imports_stdlib_and_catalog_only(self) -> None:
        tree = ast.parse(inspect.getsource(resolution_module))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                imported.add(node.module or "")
        assert imported <= {"__future__", "dataclasses", "datetime", "re", "typing",
                           "polymarket_alpha_lab.crypto_btc_evidence_catalog"}
