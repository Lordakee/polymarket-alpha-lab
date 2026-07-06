from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
EVALUATED_AT = datetime(2026, 7, 6, 11, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    module_name = (
        "polymarket_alpha_lab."
        "strategy_candidate_source_disagreement_adjusted_ev_v2"
    )
    assert importlib.util.find_spec(module_name) is not None
    return importlib.import_module(module_name)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_CANDIDATE_SOURCE_DISAGREEMENT_ADJUSTED_EV_V2_CONFIG_VERSION
        ),
        "watch_adjusted_ev_floor": d("0.015000"),
        "pass_adjusted_ev_floor": d("0.030000"),
        "watch_source_disagreement": d("0.060000"),
        "block_source_disagreement": d("0.180000"),
        "contradiction_ev_abs_floor": d("0.010000"),
        "block_contradiction_count": d("2"),
        "disagreement_penalty_weight": d("0.250000"),
        "contradiction_penalty_weight": d("0.030000"),
        "consensus_boost_weight": d("0.012000"),
        "min_consensus_ratio": d("0.650000"),
    }
    values.update(overrides)
    return module.StrategyCandidateSourceDisagreementAdjustedEvV2Config(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "candidate-alpha",
        "market_reference": "market-alpha",
        "evaluated_at": EVALUATED_AT,
        "source_expected_values": (d("0.070000"), d("0.080000"), d("0.090000")),
        "source_confidence_scores": (d("1.000000"), d("1.000000"), d("1.000000")),
        "reason_codes": ("candidate_input",),
    }
    values.update(overrides)
    return module.StrategyCandidateSourceDisagreementAdjustedEvV2Candidate(**values)


def report(*candidates: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_strategy_candidate_source_disagreement_adjusted_ev_v2(
        candidates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def assert_public_dataclass_numeric_values_are_decimal(value: object) -> None:
    for item in fields(value):
        if item.name in {"paper_only", "report_only", "readonly"}:
            continue
        item_value = getattr(value, item.name)
        if type(item_value) in (int, float):
            raise AssertionError(f"{item.name} is not Decimal-only")
        if item.name.endswith(
            (
                "_count",
                "_ratio",
                "_score",
                "_value",
                "_ev",
                "_weight",
                "_floor",
                "_boost",
                "_penalty",
                "_disagreement",
            ),
        ):
            assert type(item_value) is Decimal
        if type(item_value) is tuple:
            for nested in item_value:
                if type(nested) in (int, float):
                    raise AssertionError(f"{item.name} contains non-Decimal numeric")


def test_scores_disagreement_adjusted_ev_with_consensus_boosts_and_penalties() -> None:
    result = report(
        candidate(
            candidate_reference="candidate-pass",
            market_reference="market-pass",
            source_expected_values=(d("0.070000"), d("0.080000"), d("0.090000")),
            source_confidence_scores=(d("1.000000"), d("1.000000"), d("1.000000")),
            reason_codes=("candidate_input", "candidate_input"),
        ),
        candidate(
            candidate_reference="candidate-watch",
            market_reference="market-watch",
            source_expected_values=(d("0.040000"), d("0.050000"), d("-0.030000")),
            source_confidence_scores=(d("1.000000"), d("1.000000"), d("1.000000")),
        ),
        candidate(
            candidate_reference="candidate-block",
            market_reference="market-block",
            source_expected_values=(d("0.120000"), d("-0.080000"), d("-0.060000")),
            source_confidence_scores=(d("1.000000"), d("1.000000"), d("1.000000")),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "strategy-candidate-source-disagreement-adjusted-ev-v2"
    )
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.average_adjusted_expected_value == d("0.003444")
    assert result.max_adjusted_expected_value == d("0.087000")
    assert result.min_adjusted_expected_value == d("-0.066667")
    assert result.max_source_disagreement == d("0.200000")
    assert result.total_contradiction_count == d("2")
    assert result.digest_status == "blocked"
    assert result.reason_codes == (
        "source_disagreement_block",
        "source_contradiction_block",
        "adjusted_ev_below_watch_floor",
        "source_disagreement_watch",
        "source_contradiction_penalty",
        "source_consensus_boost",
        "source_disagreement_adjusted_ev_pass",
    )
    assert len(result.derived_validation_digest) == 64
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    blocked, watched, passed = result.rows
    assert blocked.adjusted_expected_value == d("-0.066667")
    assert blocked.weighted_source_expected_value == d("-0.006667")
    assert blocked.source_disagreement == d("0.200000")
    assert blocked.contradiction_count == d("1")
    assert blocked.consensus_source_ratio == d("0.666667")
    assert blocked.consensus_boost == d("0.000000")
    assert blocked.disagreement_penalty == d("0.050000")
    assert blocked.contradiction_penalty == d("0.010000")
    assert blocked.reason_codes == (
        "candidate_input",
        "source_disagreement_block",
        "source_contradiction_penalty",
        "adjusted_ev_below_watch_floor",
    )

    assert passed.adjusted_expected_value == d("0.087000")
    assert passed.consensus_boost == d("0.012000")
    assert passed.disagreement_penalty == d("0.005000")
    assert passed.contradiction_penalty == ZERO
    assert passed.ev_status == "pass"
    assert passed.reason_codes == (
        "candidate_input",
        "source_consensus_boost",
        "source_disagreement_adjusted_ev_pass",
    )

    assert watched.adjusted_expected_value == d("-0.010000")
    assert watched.contradiction_count == d("1")
    assert watched.ev_status == "watch"
    assert watched.reason_codes == (
        "candidate_input",
        "source_disagreement_watch",
        "source_contradiction_penalty",
        "adjusted_ev_below_watch_floor",
    )


def test_empty_report_is_readonly_and_decimal_zeroed() -> None:
    result = report()

    assert result.candidate_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.average_adjusted_expected_value == ZERO
    assert result.max_adjusted_expected_value == ZERO
    assert result.min_adjusted_expected_value == ZERO
    assert result.max_source_disagreement == ZERO
    assert result.total_contradiction_count == d("0")
    assert result.digest_status == "pass"
    assert result.reason_codes == ("source_disagreement_adjusted_ev_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    populated = report(candidate())
    for value in (result, populated, *populated.rows):
        assert_public_dataclass_numeric_values_are_decimal(value)


def test_payload_serializes_decimals_as_strings_and_rejects_tampering() -> None:
    module = api()
    result = report(
        candidate(
            source_expected_values=(d("0.070000"), d("0.080000"), d("0.090000")),
        ),
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_candidate_source_disagreement_adjusted_ev_v2_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["rows"][0]["adjusted_expected_value"] == "0.087000"
    assert payload["rows"][0]["source_expected_values"] == [
        "0.070000",
        "0.080000",
        "0.090000",
    ]
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert result.derived_validation_digest in rendered
    assert_no_int_or_float_values(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)

    object.__setattr__(result.rows[0], "reason_codes", ("safe", "bu" + "y"))
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.strategy_candidate_source_disagreement_adjusted_ev_v2_payload(result)


def test_public_dataclasses_are_frozen_and_hard_flags_are_enforced() -> None:
    module = api()
    row = report(candidate()).rows[0]

    with pytest.raises(FrozenInstanceError):
        row.ev_status = "blocked"  # type: ignore[misc]

    for klass in (
        module.StrategyCandidateSourceDisagreementAdjustedEvV2Config,
        module.StrategyCandidateSourceDisagreementAdjustedEvV2Candidate,
        module.StrategyCandidateSourceDisagreementAdjustedEvV2Row,
        module.StrategyCandidateSourceDisagreementAdjustedEvV2Report,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report(candidate()), paper_only=False)


def test_rejects_invalid_public_numeric_types_and_inconsistent_rows() -> None:
    module = api()
    valid_candidate = candidate()
    cfg = config()

    with pytest.raises(ValueError, match="candidates"):
        module.build_strategy_candidate_source_disagreement_adjusted_ev_v2(
            "bad",
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="Candidate"):
        module.build_strategy_candidate_source_disagreement_adjusted_ev_v2(
            [object()],
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_candidate_source_disagreement_adjusted_ev_v2(
            [valid_candidate],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.build_strategy_candidate_source_disagreement_adjusted_ev_v2(
            [valid_candidate],
            config=cfg,
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        candidate(evaluated_at=datetime(2026, 7, 6, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="evaluated_at"):
        report(replace(valid_candidate, evaluated_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate candidate_reference"):
        report(valid_candidate, valid_candidate)
    with pytest.raises(ValueError, match="source_expected_values"):
        candidate(source_expected_values=(d("0.010000"),))
    with pytest.raises(ValueError, match="source_confidence_scores"):
        candidate(source_confidence_scores=(d("1.000000"), d("1.000000")))
    with pytest.raises(ValueError, match="Decimal"):
        candidate(source_expected_values=(0.1, d("0.020000")))  # type: ignore[list-item]
    with pytest.raises(ValueError, match="exact Decimal"):
        candidate(source_confidence_scores=(_DecimalSubclass("1.000000"), d("1.000000")))
    with pytest.raises(ValueError, match="datetime"):
        candidate(evaluated_at=_DatetimeSubclass(2026, 7, 6, 11, 45, tzinfo=UTC))
    with pytest.raises(ValueError, match="watch_adjusted_ev_floor"):
        config(watch_adjusted_ev_floor=d("0.040000"))
    with pytest.raises(ValueError, match="block_source_disagreement"):
        config(block_source_disagreement=d("0.050000"))
    with pytest.raises(ValueError, match="candidate_count"):
        replace(report(valid_candidate), candidate_count=d("2"))
    with pytest.raises(ValueError, match="weighted_source_expected_value"):
        replace(report(valid_candidate).rows[0], weighted_source_expected_value=d("0.100000"))


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()
    bad_terms = (
        "li" + "ve",
        "au" + "th",
        "wal" + "let",
        "ord" + "er",
        "net" + "work",
        "data" + "base",
        "per" + "sist",
        "sign" + "ing",
        "muta" + "tion",
        "b" + "uy",
        "se" + "ll",
        "tr" + "ade",
    )
    for bad in bad_terms:
        with pytest.raises(ValueError, match="unsafe public payload"):
            candidate(candidate_reference=f"candidate-{bad}")

    result = report(candidate())
    for bad in bad_terms:
        tampered = asdict(result)
        tampered[f"unsafe_{bad}"] = "safe"
        with pytest.raises(ValueError, match="unsafe public payload"):
            module.derived_validation_digest_for_strategy_candidate_source_disagreement_adjusted_ev_v2(
                tampered,
            )


def test_source_has_no_unsafe_runtime_surfaces() -> None:
    module = api()
    source_path = Path(module.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        if isinstance(node, ast.Call):
            called = node.func
            called_name = ""
            if isinstance(called, ast.Name):
                called_name = called.id
            if isinstance(called, ast.Attribute):
                called_name = called.attr
            assert called_name not in {
                "connect",
                "execute",
                "open",
                "request",
                "send",
                "write",
            }

    banned_import_roots = {
        "asyncio",
        "builtins.open",
        "csv",
        "http",
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
    for public_name in module.__all__:
        lowered = public_name.lower()
        for bad in (
            "li" + "ve",
            "au" + "th",
            "wal" + "let",
            "ord" + "er",
            "net" + "work",
            "data" + "base",
            "per" + "sist",
            "sign" + "ing",
            "muta" + "tion",
            "b" + "uy",
            "se" + "ll",
            "tr" + "ade",
        ):
            assert bad not in lowered
