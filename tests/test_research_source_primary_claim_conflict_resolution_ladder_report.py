from __future__ import annotations

import ast
import importlib
import json
from hashlib import sha256
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_primary_claim_conflict_resolution_ladder_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_source_primary_claim_conflict_resolution_ladder_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = json.loads(json.dumps(payload))
    digest_values = dict(resigned)
    digest_values.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_values,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    resigned["derived_validation_digest"] = sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    return resigned


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "primary-claim-conflict-ladder-test",
        "stale_after_seconds": d("86400.000000"),
        "min_primary_count": d("2"),
        "min_independent_family_count": d("2"),
        "precedence_override_gap": d("2"),
        "min_pass_resolution_score": d("0.700000"),
        "min_watch_resolution_score": d("0.450000"),
        "stale_penalty": d("0.200000"),
        "unresolved_conflict_penalty": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchSourcePrimaryClaimConflictResolutionLadderConfig(**values)


def claim_input(**overrides: object):
    module = api()
    values = {
        "claim_ref": "candidate-alpha-raw-market-slug-question",
        "reference_ref": "https://private.example/source-text/a",
        "family_ref": "official-records",
        "claim_position": "affirmed",
        "primary": True,
        "precedence_rank": d("5"),
        "observed_at": GENERATED_AT - timedelta(minutes=15),
        "confidence_score": d("0.900000"),
        "reason_codes": (),
    }
    values.update(overrides)
    return module.ResearchSourcePrimaryClaimConflictResolutionLadderInput(**values)


def build_report(*rows: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_source_primary_claim_conflict_resolution_ladder_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_payload_has_no_forbidden_public_surface(value: object) -> None:
    forbidden_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "http",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "network",
        "database",
        "position",
        "sizing",
        "recommend",
        "buy",
        "sell",
        "live",
    )
    if type(value) is str:
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(fragment in lowered_key for fragment in forbidden_fragments)
            assert_payload_has_no_forbidden_public_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_payload_has_no_forbidden_public_surface(item)


def test_ladder_resolves_primary_claim_conflicts_without_leaking_raw_refs() -> None:
    report = build_report(
        claim_input(
            claim_ref="candidate-alpha-raw-market-slug-question",
            reference_ref="https://private.example/source-text/alpha-a",
            family_ref="official-records",
            claim_position="affirmed",
            confidence_score=d("0.920000"),
        ),
        claim_input(
            claim_ref="candidate-alpha-raw-market-slug-question",
            reference_ref="https://private.example/source-text/alpha-b",
            family_ref="venue-notices",
            claim_position="affirmed",
            confidence_score=d("0.820000"),
        ),
        claim_input(
            claim_ref="candidate-beta-raw-market-slug-question",
            reference_ref="https://private.example/source-text/beta-a",
            family_ref="official-records",
            claim_position="affirmed",
            precedence_rank=d("5"),
            confidence_score=d("0.800000"),
        ),
        claim_input(
            claim_ref="candidate-beta-raw-market-slug-question",
            reference_ref="https://private.example/source-text/beta-b",
            family_ref="venue-notices",
            claim_position="disputed",
            precedence_rank=d("2"),
            confidence_score=d("0.700000"),
        ),
        claim_input(
            claim_ref="candidate-gamma-raw-market-slug-question",
            reference_ref="https://private.example/source-text/gamma-a",
            family_ref="official-records",
            claim_position="affirmed",
            precedence_rank=d("4"),
            confidence_score=d("0.700000"),
        ),
        claim_input(
            claim_ref="candidate-gamma-raw-market-slug-question",
            reference_ref="https://private.example/source-text/gamma-b",
            family_ref="venue-notices",
            claim_position="disputed",
            precedence_rank=d("3"),
            confidence_score=d("0.720000"),
        ),
    )

    assert report.status == "block"
    assert report.claim_count == d("3")
    assert report.input_count == d("6")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.conflict_count == d("2")
    assert report.stale_count == d("0")
    assert report.average_resolution_score == d("0.610000")
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.ladder_step for row in report.rows) == (
        "unresolved_primary_conflict",
        "precedence_ladder_review",
        "primary_claim_consensus",
    )

    blocked, watched, passed = report.rows
    assert blocked.primary_count == d("2")
    assert blocked.conflicting_primary_count == d("2")
    assert blocked.precedence_gap == d("1")
    assert blocked.resolution_score == d("0.210000")
    assert blocked.reason_codes == ("unresolved_primary_conflict",)
    assert watched.precedence_gap == d("3")
    assert watched.resolution_score == d("0.750000")
    assert watched.reason_codes == ("precedence_ladder_review",)
    assert passed.family_count == d("2")
    assert passed.resolution_score == d("0.870000")
    assert passed.reason_codes == ("primary_claim_consensus_clear",)
    assert all(row.claim_digest.startswith("sha256:") for row in report.rows)

    module = api()
    payload = module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
        report,
    )
    encoded = json.dumps(payload, sort_keys=True)
    for raw_fragment in (
        "candidate-alpha-raw-market-slug-question",
        "candidate-beta-raw-market-slug-question",
        "candidate-gamma-raw-market-slug-question",
        "https://private.example/source-text",
        "official-records",
        "venue-notices",
    ):
        assert raw_fragment not in encoded
    assert_payload_has_no_forbidden_public_surface(payload)


def test_empty_input_blocks_report_only_with_decimal_zeroes() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.claim_count == d("0")
    assert report.input_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.conflict_count == d("0")
    assert report.stale_count == d("0")
    assert report.average_resolution_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("no_primary_claim_inputs",)
    assert report.reason_code_counts == (
        api().ResearchSourcePrimaryClaimConflictResolutionLadderReasonCodeCount(
            reason_code="no_primary_claim_inputs",
            count=d("1"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_deterministic_decimal_stringed_frozen_and_digest_validated() -> None:
    module = api()
    report = build_report(
        claim_input(claim_ref="candidate-delta-raw", reference_ref="source-a"),
        claim_input(
            claim_ref="candidate-delta-raw",
            reference_ref="source-b",
            family_ref="venue-notices",
            confidence_score=d("0.800000"),
        ),
    )

    payload = module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
        report,
    )
    payload_again = module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
        build_report(
            claim_input(
                claim_ref="candidate-delta-raw",
                reference_ref="source-b",
                family_ref="venue-notices",
                confidence_score=d("0.800000"),
            ),
            claim_input(claim_ref="candidate-delta-raw", reference_ref="source-a"),
        ),
    )

    assert payload == payload_again
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["claim_count"] == "1"
    assert payload["average_resolution_score"] == "0.850000"
    assert payload["rows"][0]["resolution_score"] == "0.850000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(module.research_source_primary_claim_conflict_resolution_ladder_report_digest(report)) == 64
    assert_no_float_values(payload)
    assert_payload_has_no_forbidden_public_surface(payload)

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["status"] = "watch"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]

    tampered = dict(payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
            tampered,
        )


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_input = claim_input()
    sample_report = build_report(sample_input, claim_input(reference_ref="source-b", family_ref="b"))
    sample_row = sample_report.rows[0]
    sample_reason_count = sample_report.reason_code_counts[0]

    for item in (sample_config, sample_input, sample_row, sample_reason_count, sample_report):
        assert is_dataclass(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        claim_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(claim_input(readonly=False))


def test_validation_rejects_bad_types_statuses_times_and_digest_tampering() -> None:
    module = api()

    with pytest.raises(ValueError, match="precedence_override_gap"):
        config(precedence_override_gap=d("0"))
    with pytest.raises(ValueError, match="min_pass_resolution_score"):
        config(min_pass_resolution_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="stale_penalty"):
        config(stale_penalty=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="claim_position"):
        claim_input(claim_position="yes")
    with pytest.raises(ValueError, match="primary"):
        claim_input(primary=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        claim_input(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(claim_input(), generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        build_report(claim_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="status"):
        replace(
            build_report(claim_input(), claim_input(reference_ref="source-b", family_ref="b")),
            status="blocked",
        )
    report = build_report(claim_input(), claim_input(reference_ref="source-b", family_ref="b"))
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["derived_validation_digest"] = "f" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.ResearchSourcePrimaryClaimConflictResolutionLadderReport(**values)


def test_decimal_boundaries_are_raw_checked_signed_zero_safe_and_context_independent() -> None:
    module = api()

    with pytest.raises(ValueError, match="stale_penalty"):
        config(stale_penalty=d("1.0000001"))
    with pytest.raises(ValueError, match="confidence_score"):
        claim_input(confidence_score=d("-0.0000001"))
    with pytest.raises(ValueError, match="precedence_rank"):
        claim_input(precedence_rank=d("0.5"))
    with pytest.raises(ValueError, match="min_primary_count"):
        config(min_primary_count=d("1E+100"))
    assert config(stale_penalty=d("-0")).stale_penalty.as_tuple().sign == 0

    rows = tuple(
        claim_input(
            claim_ref=f"private-claim-{index}",
            reference_ref=f"private-reference-{index}",
        )
        for index in range(100)
    )
    with localcontext(Context(prec=2)):
        report = module.build_research_source_primary_claim_conflict_resolution_ladder_report(
            rows,
            config=config(),
            generated_at=GENERATED_AT,
        )

    assert report.claim_count == d("100")

    score_config = config(
        stale_after_seconds=d("1.000000"),
        min_primary_count=d("1"),
        min_independent_family_count=d("1"),
        stale_penalty=d("0.123456"),
    )
    stale_row = claim_input(
        observed_at=GENERATED_AT - timedelta(seconds=2),
        confidence_score=d("0.876543"),
    )
    baseline = build_report(stale_row, cfg=score_config)
    with localcontext(Context(prec=2)):
        context_limited = build_report(stale_row, cfg=score_config)

    assert baseline.rows[0].resolution_score == d("0.753087")
    assert context_limited.rows[0].resolution_score == baseline.rows[0].resolution_score


def test_final_dataclasses_revalidate_object_setattr_state_at_public_boundaries() -> None:
    module = api()

    with pytest.raises(TypeError, match="final"):
        class DerivedConfig(
            module.ResearchSourcePrimaryClaimConflictResolutionLadderConfig,
        ):
            pass

    forged_config = config()
    object.__setattr__(forged_config, "stale_penalty", d("1.000001"))
    with pytest.raises(ValueError, match="stale_penalty"):
        build_report(cfg=forged_config)

    forged_input = claim_input()
    object.__setattr__(forged_input, "precedence_rank", d("0.5"))
    with pytest.raises(ValueError, match="precedence_rank"):
        build_report(forged_input)

    forged_report = build_report(
        claim_input(),
        claim_input(reference_ref="source-b", family_ref="independent-family"),
    )
    object.__setattr__(forged_report.rows[0], "primary_count", d("3"))
    with pytest.raises(ValueError, match="primary_count"):
        module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
            forged_report,
        )

    forged_reason_count = build_report()
    object.__setattr__(forged_reason_count.reason_code_counts[0], "count", d("0"))
    with pytest.raises(ValueError, match="reason_code_count"):
        module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
            forged_reason_count,
        )


def test_public_mapping_requires_canonical_schema_order_and_resigned_derivations() -> None:
    module = api()
    payload = json.loads(
        json.dumps(
            module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
                build_report(
                    claim_input(),
                    claim_input(
                        reference_ref="source-b",
                        family_ref="independent-family",
                        confidence_score=d("0.800000"),
                    ),
                ),
            ),
        ),
    )

    reordered = dict(reversed(tuple(payload.items())))
    with pytest.raises(ValueError, match="payload keys"):
        module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
            resign_payload(reordered),
        )

    extra_key = dict(payload)
    extra_key["diagnostic_note"] = "forged"
    with pytest.raises(ValueError, match="payload keys"):
        module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
            resign_payload(extra_key),
        )

    forged_count = json.loads(json.dumps(payload))
    forged_count["rows"][0]["primary_count"] = "3"
    with pytest.raises(ValueError, match="primary_count"):
        module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
            resign_payload(forged_count),
        )

    forged_score = json.loads(json.dumps(payload))
    forged_score["rows"][0]["resolution_score"] = "0.800000"
    forged_score["average_resolution_score"] = "0.800000"
    with pytest.raises(ValueError, match="resolution_score"):
        module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
            resign_payload(forged_score),
        )

    forged_status = json.loads(json.dumps(payload))
    forged_status["rows"][0]["status"] = "watch"
    with pytest.raises(ValueError, match="status"):
        module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
            resign_payload(forged_status),
        )

    forged_reason = json.loads(json.dumps(payload))
    forged_reason["rows"][0]["reason_codes"] = ["thin_primary_claim_support"]
    with pytest.raises(ValueError, match="reason_codes"):
        module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
            resign_payload(forged_reason),
        )

    forged_aggregate = json.loads(json.dumps(payload))
    forged_aggregate["claim_count"] = "2"
    with pytest.raises(ValueError, match="claim_count"):
        module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
            resign_payload(forged_aggregate),
        )

    non_string_decimal = json.loads(json.dumps(payload))
    non_string_decimal["claim_count"] = 1
    with pytest.raises(ValueError, match="non-Decimal numeric"):
        module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
            resign_payload(non_string_decimal),
        )

    ordered_payload = json.loads(
        json.dumps(
            module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
                build_report(
                    claim_input(claim_ref="private-claim-a"),
                    claim_input(
                        claim_ref="private-claim-a",
                        reference_ref="private-claim-a-source-b",
                        family_ref="family-b",
                    ),
                    claim_input(claim_ref="private-claim-b"),
                    claim_input(
                        claim_ref="private-claim-b",
                        reference_ref="private-claim-b-source-b",
                        family_ref="family-b",
                    ),
                ),
            ),
        ),
    )
    ordered_payload["rows"].reverse()
    with pytest.raises(ValueError, match="sorted deterministically"):
        module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
            resign_payload(ordered_payload),
        )


def test_equal_severity_rows_use_digest_as_a_complete_deterministic_tie_breaker() -> None:
    module = api()
    rows = tuple(
        row
        for claim_ref in (
            "private-claim-alpha",
            "private-claim-beta",
            "private-claim-gamma",
        )
        for row in (
            claim_input(
                claim_ref=claim_ref,
                reference_ref=f"{claim_ref}-reference-a",
                family_ref="family-a",
            ),
            claim_input(
                claim_ref=claim_ref,
                reference_ref=f"{claim_ref}-reference-b",
                family_ref="family-b",
            ),
        )
    )

    first = build_report(*rows)
    second = build_report(*reversed(rows))

    assert tuple(row.status for row in first.rows) == ("pass", "pass", "pass")
    assert tuple(row.claim_digest for row in first.rows) == tuple(
        sorted(row.claim_digest for row in first.rows),
    )
    assert module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
        first,
    ) == module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
        second,
    )


@pytest.mark.parametrize(
    "payload",
    (
        {"paper_only": True, "report_only": True, "readonly": True, "candidate_id": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "market_slug": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "question": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "source_url": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "source_text": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "dsn": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "table_name": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "token": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "wallet order trade"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "live sizing recommendation"},
        {"paper_only": True, "report_only": False, "readonly": True},
    ),
)
def test_public_payload_rejects_unsafe_surfaces_and_flag_downgrades(
    payload: dict[str, object],
) -> None:
    module = api()

    with pytest.raises(ValueError):
        module.research_source_primary_claim_conflict_resolution_ladder_report_payload(
            payload,
        )


def test_module_scope_has_no_db_network_wallet_order_trading_or_sizing_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "broker",
        "client",
        "clob",
        "database",
        "db",
        "http",
        "network",
        "order",
        "persist",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
        "web3",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "order",
        "persist",
        "rollback",
        "sell",
        "send",
        "sign",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
