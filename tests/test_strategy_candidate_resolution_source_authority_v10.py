from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_candidate_resolution_source_authority_v10"
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing strategy module: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_SOURCE_AUTHORITY_V10_CONFIG_VERSION,
        "min_pass_source_hierarchy_confidence": d("0.750000"),
        "min_watch_source_hierarchy_confidence": d("0.500000"),
        "max_pass_conflicting_source_count": d("1"),
        "max_watch_conflicting_source_count": d("3"),
        "min_pass_rule_specificity": d("0.700000"),
        "min_watch_rule_specificity": d("0.450000"),
        "max_pass_adjudication_dependency": d("0.250000"),
        "max_watch_adjudication_dependency": d("0.600000"),
        "min_pass_authority_score": d("0.750000"),
        "min_watch_authority_score": d("0.550000"),
        "max_conflicting_source_count_for_score": d("5"),
    }
    values.update(overrides)
    return module.StrategyCandidateResolutionSourceAuthorityV10Config(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "candidate-secret-alpha",
        "market_slug": "alpha-official-source",
        "event_title": "Will the official agency publish the final result?",
        "official_source_available": True,
        "source_hierarchy_confidence": d("0.900000"),
        "conflicting_source_count": d("0"),
        "rule_specificity": d("0.850000"),
        "adjudication_dependency": d("0.100000"),
    }
    values.update(overrides)
    return module.StrategyCandidateResolutionSourceAuthorityV10Candidate(**values)


def report(*candidates: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_candidate_resolution_source_authority_v10(
        candidates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_scores_resolution_source_authority_and_sorts_by_weakest_authority() -> None:
    result = report(
        candidate(
            candidate_reference="pass-secret-token",
            market_slug="gamma-pass",
            official_source_available=True,
            source_hierarchy_confidence=d("0.900000"),
            conflicting_source_count=d("0"),
            rule_specificity=d("0.850000"),
            adjudication_dependency=d("0.100000"),
        ),
        candidate(
            candidate_reference="watch-candidate",
            market_slug="beta-watch",
            official_source_available=True,
            source_hierarchy_confidence=d("0.600000"),
            conflicting_source_count=d("2"),
            rule_specificity=d("0.550000"),
            adjudication_dependency=d("0.400000"),
        ),
        candidate(
            candidate_reference="block-candidate",
            market_slug="alpha-block",
            official_source_available=False,
            source_hierarchy_confidence=d("0.400000"),
            conflicting_source_count=d("5"),
            rule_specificity=d("0.300000"),
            adjudication_dependency=d("0.700000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-candidate-resolution-source-authority-v10"
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.min_authority_score == d("0.190000")
    assert result.max_authority_score == d("0.935000")
    assert result.average_authority_score == d("0.611667")
    assert result.max_conflicting_source_count == d("5")
    assert result.max_adjudication_dependency == d("0.700000")
    assert result.status == "block"
    assert result.reason_codes == (
        "official_resolution_source_missing",
        "source_hierarchy_confidence_block",
        "source_hierarchy_confidence_watch",
        "conflicting_sources_block",
        "conflicting_sources_watch",
        "resolution_rule_specificity_block",
        "resolution_rule_specificity_watch",
        "adjudication_dependency_block",
        "adjudication_dependency_watch",
        "authority_score_block",
        "authority_score_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_sha256(result.report_sha256)

    assert tuple(row.status for row in result.results) == ("block", "watch", "pass")
    blocked, watched, passed = result.results

    assert blocked.market_slug == "alpha-block"
    assert blocked.redacted_candidate_reference.startswith("candidate_ref_")
    assert blocked.official_source_available is False
    assert blocked.source_hierarchy_confidence == d("0.400000")
    assert blocked.conflicting_source_count == d("5")
    assert blocked.rule_specificity == d("0.300000")
    assert blocked.adjudication_dependency == d("0.700000")
    assert blocked.conflict_penalty == d("1.000000")
    assert blocked.authority_score == d("0.190000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "official_resolution_source_missing",
        "source_hierarchy_confidence_block",
        "conflicting_sources_block",
        "resolution_rule_specificity_block",
        "adjudication_dependency_block",
        "authority_score_block",
    )
    assert_sha256(blocked.result_sha256)

    assert watched.status == "watch"
    assert watched.conflict_penalty == d("0.400000")
    assert watched.authority_score == d("0.710000")
    assert watched.reason_codes == (
        "source_hierarchy_confidence_watch",
        "conflicting_sources_watch",
        "resolution_rule_specificity_watch",
        "adjudication_dependency_watch",
        "authority_score_watch",
    )

    assert passed.status == "pass"
    assert passed.conflict_penalty == ZERO
    assert passed.authority_score == d("0.935000")
    assert passed.reason_codes == ("resolution_source_authority_pass",)
    assert "secret" not in passed.redacted_candidate_reference
    assert "token" not in passed.redacted_candidate_reference


def test_payload_is_canonical_redacted_decimal_stringed_and_tamper_validated() -> None:
    module = api()
    result = report(
        candidate(
            candidate_reference="secret-resolution-wallet-token",
            market_slug="payload-market",
            official_source_available=True,
            source_hierarchy_confidence=d("0.800000"),
            conflicting_source_count=d("1"),
            rule_specificity=d("0.700000"),
            adjudication_dependency=d("0.250000"),
        ),
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert module.validate_strategy_candidate_resolution_source_authority_v10_report(result) is True

    payload = module.strategy_candidate_resolution_source_authority_v10_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["min_authority_score"] == "0.835000"
    assert payload["average_authority_score"] == "0.835000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["results"][0]["redacted_candidate_reference"].startswith("candidate_ref_")
    assert payload["results"][0]["authority_score"] == "0.835000"
    assert_sha256(payload["results"][0]["derived_validation_digest"])
    assert payload["results"][0]["result_sha256"] == result.results[0].result_sha256
    assert_sha256(payload["derived_validation_digest"])
    assert payload["report_sha256"] == result.report_sha256
    assert "secret" not in rendered
    assert "wallet" not in rendered
    assert "token" not in rendered
    assert_no_float_values(payload)

    with pytest.raises(ValueError, match="authority_score must match"):
        replace(result.results[0], authority_score=d("0.123456"))
    with pytest.raises(ValueError, match="result_sha256 must match"):
        replace(result.results[0], result_sha256="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result.results[0], derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="average_authority_score must match"):
        replace(result, average_authority_score=d("0.123456"))
    with pytest.raises(ValueError, match="report_sha256 must match"):
        replace(result, report_sha256="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result, derived_validation_digest="0" * 64)


def test_rejects_unsafe_public_payload_surface() -> None:
    module = api()
    result = report(candidate(candidate_reference="safe-public-reference"))
    payload = module.strategy_candidate_resolution_source_authority_v10_payload(result)

    assert module.validate_strategy_candidate_resolution_source_authority_v10_public_payload(payload) is True

    unsafe_payload = {
        **payload,
        "results": [
            {
                **payload["results"][0],
                "wallet": "must-not-be-public",
            },
        ],
    }
    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.validate_strategy_candidate_resolution_source_authority_v10_public_payload(
            unsafe_payload,
        )


def test_empty_report_is_blocked_zeroed_and_readonly() -> None:
    empty = report()

    assert empty.candidate_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.block_count == d("0")
    assert empty.min_authority_score == ZERO
    assert empty.max_authority_score == ZERO
    assert empty.average_authority_score == ZERO
    assert empty.max_conflicting_source_count == d("0")
    assert empty.max_adjudication_dependency == ZERO
    assert empty.status == "block"
    assert empty.reason_codes == ("resolution_source_authority_empty",)
    assert empty.results == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True
    assert_sha256(empty.report_sha256)

    populated = report(candidate())
    for value in (empty, *populated.results, populated):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(("_count", "_confidence", "_specificity", "_dependency", "_penalty", "_score")):
                assert type(item_value) is Decimal


def test_rejects_invalid_inputs_thresholds_duplicates_and_flags() -> None:
    module = api()
    valid_candidate = candidate()
    cfg = config()

    with pytest.raises(ValueError, match="candidates"):
        module.build_strategy_candidate_resolution_source_authority_v10(
            "not-candidates",
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="StrategyCandidateResolutionSourceAuthorityV10Candidate"):
        module.build_strategy_candidate_resolution_source_authority_v10(
            [object()],
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_candidate_resolution_source_authority_v10(
            [valid_candidate],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.build_strategy_candidate_resolution_source_authority_v10(
            [valid_candidate],
            config=cfg,
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(ValueError, match="duplicate candidate_reference"):
        report(valid_candidate, valid_candidate)
    with pytest.raises(ValueError, match="official_source_available"):
        candidate(official_source_available=1)
    with pytest.raises(ValueError, match="source_hierarchy_confidence"):
        candidate(source_hierarchy_confidence=d("1.000001"))
    with pytest.raises(ValueError, match="conflicting_source_count"):
        candidate(conflicting_source_count=d("1.5"))
    with pytest.raises(ValueError, match="adjudication_dependency"):
        candidate(adjudication_dependency=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        module.StrategyCandidateResolutionSourceAuthorityV10Candidate(
            **{
                **valid_candidate.__dict__,
                "paper_only": False,
            },
        )
    with pytest.raises(ValueError, match="min_pass_source_hierarchy_confidence"):
        config(min_pass_source_hierarchy_confidence=d("0.400000"))
    with pytest.raises(ValueError, match="max_pass_conflicting_source_count"):
        config(max_pass_conflicting_source_count=d("4"))
    with pytest.raises(ValueError, match="min_pass_rule_specificity"):
        config(min_pass_rule_specificity=d("0.400000"))
    with pytest.raises(ValueError, match="max_pass_adjudication_dependency"):
        config(max_pass_adjudication_dependency=d("0.700000"))
    with pytest.raises(ValueError, match="min_pass_authority_score"):
        config(min_pass_authority_score=d("0.400000"))


def test_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    module = api()
    row = report(candidate()).results[0]

    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]

    for klass in (
        module.StrategyCandidateResolutionSourceAuthorityV10Config,
        module.StrategyCandidateResolutionSourceAuthorityV10Candidate,
        module.StrategyCandidateResolutionSourceAuthorityV10Result,
        module.StrategyCandidateResolutionSourceAuthorityV10Report,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(ValueError, match="Decimal"):
        candidate(source_hierarchy_confidence=0.5)
    with pytest.raises(ValueError, match="exact Decimal"):
        candidate(source_hierarchy_confidence=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="datetime"):
        module.build_strategy_candidate_resolution_source_authority_v10(
            [candidate()],
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, tzinfo=UTC),
        )


def test_source_has_no_io_db_network_or_live_mutation_surface() -> None:
    module = api()
    source_path = Path(module.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    banned_import_roots = {
        "asyncio",
        "builtins.open",
        "csv",
        "http",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    assert not (set(imports) & banned_import_roots)
    lowered = source.lower()
    for term in (
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "submit_",
        "cancel_",
        "exchange",
    ):
        assert term not in lowered
