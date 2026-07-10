from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_authority_event_claim_traceability_report"
)
GENERATED_AT = datetime(2026, 7, 9, 13, 15, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_SOURCE_AUTHORITY_EVENT_CLAIM_TRACEABILITY_REPORT_CONFIG_VERSION
        ),
        "min_pass_authority_score": d("0.800000"),
        "min_watch_authority_score": d("0.600000"),
        "min_pass_trace_coverage_ratio": d("0.900000"),
        "min_watch_trace_coverage_ratio": d("0.700000"),
        "max_pass_contradiction_ratio": d("0.100000"),
        "max_watch_contradiction_ratio": d("0.300000"),
        "max_pass_unresolved_claim_ratio": d("0.050000"),
        "max_watch_unresolved_claim_ratio": d("0.200000"),
        "source_age_watch_seconds": d("3600.000000"),
        "source_age_block_seconds": d("7200.000000"),
        "max_watch_lineage_depth": d("4.000000"),
        "max_block_lineage_depth": d("7.000000"),
        "authority_weight": d("0.350000"),
        "trace_coverage_weight": d("0.350000"),
        "freshness_weight": d("0.150000"),
        "claim_consistency_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityEventClaimTraceabilityConfig(**values)


def claim_input(
    private_event_claim_key: str = "private-event-claim-pass",
    *,
    authority_tier: str = "official",
    claim_lineage_depth: Decimal = d("2.000000"),
    supporting_source_count: Decimal = d("4.000000"),
    authoritative_source_count: Decimal = d("4.000000"),
    traced_source_count: Decimal = d("4.000000"),
    stale_source_count: Decimal = d("0.000000"),
    contradictory_source_count: Decimal = d("0.000000"),
    unresolved_claim_count: Decimal = d("0.000000"),
    max_source_age_seconds: Decimal = d("600.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceAuthorityEventClaimTraceabilityInput(
        private_event_claim_key=private_event_claim_key,
        authority_tier=authority_tier,
        claim_lineage_depth=claim_lineage_depth,
        supporting_source_count=supporting_source_count,
        authoritative_source_count=authoritative_source_count,
        traced_source_count=traced_source_count,
        stale_source_count=stale_source_count,
        contradictory_source_count=contradictory_source_count,
        unresolved_claim_count=unresolved_claim_count,
        max_source_age_seconds=max_source_age_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_source_authority_event_claim_traceability_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def signed_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    signed = json.loads(json.dumps(payload, sort_keys=True))
    unsigned = dict(signed)
    unsigned.pop("derived_validation_digest", None)
    signed["derived_validation_digest"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()
    return signed


def test_report_scores_pass_watch_and_block_claim_traceability_rows() -> None:
    module = api()
    blocked_private_key = (
        "raw_candidate_id_market_id_market_slug_question_"
        "https://example.invalid/source_text_private_token_wallet_order_trade"
    )
    result = build_report(
        claim_input(
            blocked_private_key,
            authority_tier="contested",
            claim_lineage_depth=d("8.000000"),
            supporting_source_count=d("4.000000"),
            authoritative_source_count=d("1.000000"),
            traced_source_count=d("1.000000"),
            stale_source_count=d("2.000000"),
            contradictory_source_count=d("2.000000"),
            unresolved_claim_count=d("1.000000"),
            max_source_age_seconds=d("9000.000000"),
        ),
        claim_input(
            "private-event-claim-watch",
            authority_tier="secondary",
            claim_lineage_depth=d("4.000000"),
            supporting_source_count=d("5.000000"),
            authoritative_source_count=d("4.000000"),
            traced_source_count=d("4.000000"),
            stale_source_count=d("1.000000"),
            contradictory_source_count=d("1.000000"),
            unresolved_claim_count=d("0.000000"),
            max_source_age_seconds=d("4800.000000"),
        ),
        claim_input("private-event-claim-pass"),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert module.RESEARCH_SOURCE_AUTHORITY_EVENT_CLAIM_TRACEABILITY_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_AUTHORITY_EVENT_CLAIM_TRACEABILITY_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_AUTHORITY_EVENT_CLAIM_TRACEABILITY_REPORT_STATUSES",
        "ResearchSourceAuthorityEventClaimTraceabilityConfig",
        "ResearchSourceAuthorityEventClaimTraceabilityInput",
        "ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount",
        "ResearchSourceAuthorityEventClaimTraceabilityReport",
        "ResearchSourceAuthorityEventClaimTraceabilityRow",
        "build_research_source_authority_event_claim_traceability_report",
        "research_source_authority_event_claim_traceability_report_digest",
        "research_source_authority_event_claim_traceability_report_payload",
        "validate_research_source_authority_event_claim_traceability_public_payload",
        "validate_research_source_authority_event_claim_traceability_report_digest",
    )
    assert type(result) is module.ResearchSourceAuthorityEventClaimTraceabilityReport
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.input_row_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.low_authority_count == d("1.000000")
    assert result.low_trace_coverage_count == d("2.000000")
    assert result.stale_source_count == d("2.000000")
    assert result.contradictory_claim_count == d("2.000000")
    assert result.unresolved_claim_count == d("1.000000")
    assert result.deep_lineage_count == d("1.000000")
    assert result.mean_trace_coverage_ratio == d("0.683333")
    assert result.mean_claim_traceability_score == d("0.676667")
    assert result.lowest_claim_traceability_score == d("0.250000")
    assert result.highest_claim_traceability_risk_score == d("0.750000")
    assert result.oldest_source_age_seconds == d("9000.000000")
    assert result.highest_contradiction_ratio == d("0.500000")
    assert result.status == "block"
    assert result.reason_codes == (
        "research_source_authority_event_claim_traceability_report_block",
        "research_source_authority_event_claim_traceability_low_authority_exception",
        "research_source_authority_event_claim_traceability_low_trace_coverage_exception",
        "research_source_authority_event_claim_traceability_stale_source_exception",
        "research_source_authority_event_claim_traceability_contradiction_exception",
        "research_source_authority_event_claim_traceability_unresolved_claim_exception",
        "research_source_authority_event_claim_traceability_deep_lineage_exception",
    )

    blocked, watched, passed = result.rows
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    assert blocked.claim_trace_hash == hashlib.sha256(
        blocked_private_key.encode(),
    ).hexdigest()
    assert blocked.authority_score == d("0.250000")
    assert blocked.trace_coverage_ratio == d("0.250000")
    assert blocked.claim_consistency_score == d("0.500000")
    assert blocked.claim_traceability_score == d("0.250000")
    assert blocked.claim_traceability_risk_score == d("0.750000")
    assert blocked.reason_codes == (
        "research_source_authority_event_claim_traceability_low_authority_block",
        "research_source_authority_event_claim_traceability_low_trace_coverage_block",
        "research_source_authority_event_claim_traceability_stale_source_block",
        "research_source_authority_event_claim_traceability_contradiction_block",
        "research_source_authority_event_claim_traceability_unresolved_claim_block",
        "research_source_authority_event_claim_traceability_deep_lineage_block",
    )

    assert watched.authority_score == d("0.800000")
    assert watched.trace_coverage_ratio == d("0.800000")
    assert watched.freshness_score == d("0.666667")
    assert watched.contradiction_ratio == d("0.200000")
    assert watched.unresolved_claim_ratio == d("0.000000")
    assert watched.claim_traceability_score == d("0.780000")
    assert watched.claim_traceability_risk_score == d("0.220000")
    assert watched.reason_codes == (
        "research_source_authority_event_claim_traceability_low_trace_coverage_watch",
        "research_source_authority_event_claim_traceability_stale_source_watch",
        "research_source_authority_event_claim_traceability_contradiction_watch",
    )

    assert passed.claim_traceability_score == d("1.000000")
    assert passed.claim_traceability_risk_score == ZERO
    assert passed.reason_codes == (
        "research_source_authority_event_claim_traceability_clear",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_empty_report_blocks_without_event_claim_authority_inputs() -> None:
    module = api()
    result = build_report()

    assert result.status == "block"
    assert result.reason_codes == (
        "research_source_authority_event_claim_traceability_report_empty",
    )
    assert result.input_row_count == ZERO
    assert result.rows == ()
    assert result.reason_code_counts == ()
    assert result.mean_claim_traceability_score == ZERO
    assert result.lowest_claim_traceability_score == ZERO
    assert result.highest_claim_traceability_risk_score == ZERO

    payload = module.research_source_authority_event_claim_traceability_report_payload(result)
    assert payload["generated_at"] == "2026-07-09T13:15:00+00:00"
    assert payload["input_row_count"] == "0.000000"
    assert payload["status"] == "block"
    assert payload["rows"] == []
    assert_no_public_numeric_values(payload)
    json.dumps(payload, sort_keys=True, allow_nan=False)


def test_public_payload_is_deterministic_safe_decimal_stringed_and_digest_guarded() -> None:
    module = api()
    first = build_report(claim_input("private-z"), claim_input("private-a"))
    second = build_report(claim_input("private-a"), claim_input("private-z"))

    first_payload = module.research_source_authority_event_claim_traceability_report_payload(
        first,
    )
    second_payload = module.research_source_authority_event_claim_traceability_report_payload(
        second,
    )
    first_digest = module.research_source_authority_event_claim_traceability_report_digest(
        first,
    )
    second_digest = module.research_source_authority_event_claim_traceability_report_digest(
        second,
    )

    assert first_payload == second_payload
    assert first_digest == second_digest
    assert first_payload["derived_validation_digest"] == first_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert len(first_digest) == 64
    int(first_digest, 16)
    assert_no_public_numeric_values(first_payload)
    assert_payload_has_no_leaked_keys_or_values(first_payload)
    module.validate_research_source_authority_event_claim_traceability_report_digest(first)
    module.validate_research_source_authority_event_claim_traceability_public_payload(
        first_payload,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered = dict(first_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_authority_event_claim_traceability_public_payload(
            tampered,
        )


def test_public_payload_prevents_raw_identifier_source_secret_and_trading_leaks() -> None:
    module = api()
    raw_private_key = (
        "candidate-123_market_id_market_slug_question_"
        "https://example.invalid/source_url_source_text_dsn_table_token_wallet_order_trade"
    )
    result = build_report(claim_input(raw_private_key))
    payload = module.research_source_authority_event_claim_traceability_report_payload(
        result,
    )
    public_field_names = {
        field.name
        for cls in (type(result), type(result.rows[0]))
        for field in fields(cls)
    }
    unsafe_public_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
        "sizing",
        "recommendation",
    }

    assert unsafe_public_keys.isdisjoint(public_field_names)
    assert result.rows[0].claim_trace_hash == hashlib.sha256(
        raw_private_key.encode(),
    ).hexdigest()
    assert raw_private_key not in json.dumps(payload, sort_keys=True)
    assert_payload_has_no_leaked_keys_or_values(payload)

    for unsafe_payload in (
        {"candidate_id": "safe"},
        {"market_slug": "safe"},
        {"question": "safe"},
        {"safe": "https://example.invalid/source"},
        {"safe": "source_text"},
        {"safe": "wallet token"},
        {"safe": "live order trade recommendation sizing"},
        {"table_name": "public_summary"},
    ):
        with pytest.raises(ValueError, match="public payload"):
            module.validate_research_source_authority_event_claim_traceability_public_payload(
                {
                    **payload,
                    **unsafe_payload,
                    "derived_validation_digest": payload["derived_validation_digest"],
                },
            )


def test_public_payload_validation_rejects_valid_digest_schema_downgrades() -> None:
    module = api()
    payload = module.research_source_authority_event_claim_traceability_report_payload(
        build_report(claim_input("private-event-claim-pass")),
    )

    invalid_status = signed_public_payload({**payload, "status": "execute"})
    with pytest.raises(ValueError, match="status"):
        module.validate_research_source_authority_event_claim_traceability_public_payload(
            invalid_status,
        )

    missing_readonly = dict(payload)
    missing_readonly.pop("readonly")
    with pytest.raises(ValueError, match="readonly|public payload"):
        module.validate_research_source_authority_event_claim_traceability_public_payload(
            signed_public_payload(missing_readonly),
        )

    downgraded_row = signed_public_payload(payload)
    downgraded_row["rows"][0]["paper_only"] = False
    downgraded_row = signed_public_payload(downgraded_row)
    with pytest.raises(ValueError, match="paper_only"):
        module.validate_research_source_authority_event_claim_traceability_public_payload(
            downgraded_row,
        )

    decimal_payload = dict(payload)
    decimal_payload["input_row_count"] = Decimal("1.000000")
    with pytest.raises(ValueError, match="public payload"):
        module.validate_research_source_authority_event_claim_traceability_public_payload(
            decimal_payload,
        )

    uppercase_row_digest = signed_public_payload(payload)
    uppercase_row_digest["rows"][0]["claim_trace_hash"] = uppercase_row_digest["rows"][0][
        "claim_trace_hash"
    ].upper()
    uppercase_row_digest = signed_public_payload(uppercase_row_digest)
    with pytest.raises(ValueError, match="claim_trace_hash"):
        module.validate_research_source_authority_event_claim_traceability_public_payload(
            uppercase_row_digest,
        )


@pytest.mark.parametrize(
    ("count_field", "replacement_value", "expected_ratio_field"),
    (
        ("authoritative_source_count", "3.000000", "authority_score"),
        ("traced_source_count", "3.000000", "trace_coverage_ratio"),
        ("contradictory_source_count", "1.000000", "contradiction_ratio"),
        ("unresolved_claim_count", "1.000000", "unresolved_claim_ratio"),
    ),
)
def test_public_payload_rejects_resigned_count_ratio_contradictions(
    count_field: str,
    replacement_value: str,
    expected_ratio_field: str,
) -> None:
    module = api()
    payload = module.research_source_authority_event_claim_traceability_report_payload(
        build_report(claim_input("private-event-claim-pass")),
    )
    tampered = signed_public_payload(payload)
    tampered["rows"][0][count_field] = replacement_value
    tampered = signed_public_payload(tampered)

    with pytest.raises(ValueError, match=expected_ratio_field):
        module.validate_research_source_authority_event_claim_traceability_public_payload(
            tampered,
        )


def test_public_payload_rejects_resigned_freshness_and_score_drift() -> None:
    module = api()
    payload = module.research_source_authority_event_claim_traceability_report_payload(
        build_report(claim_input("private-event-claim-pass")),
    )

    forged_freshness = signed_public_payload(payload)
    forged_freshness["rows"][0]["freshness_score"] = "0.500000"
    forged_freshness = signed_public_payload(forged_freshness)
    with pytest.raises(ValueError, match="freshness_score"):
        module.validate_research_source_authority_event_claim_traceability_public_payload(
            forged_freshness,
        )

    forged_score = signed_public_payload(payload)
    forged_score["rows"][0]["claim_traceability_score"] = "0.900000"
    forged_score["rows"][0]["claim_traceability_risk_score"] = "0.100000"
    forged_score["mean_claim_traceability_score"] = "0.900000"
    forged_score["lowest_claim_traceability_score"] = "0.900000"
    forged_score["highest_claim_traceability_risk_score"] = "0.100000"
    forged_score = signed_public_payload(forged_score)
    with pytest.raises(ValueError, match="claim_traceability_score"):
        module.validate_research_source_authority_event_claim_traceability_public_payload(
            forged_score,
        )


def test_public_payload_rejects_resigned_reason_status_and_count_drift() -> None:
    module = api()
    payload = module.research_source_authority_event_claim_traceability_report_payload(
        build_report(claim_input("private-event-claim-pass")),
    )
    forged = signed_public_payload(payload)
    forged["rows"][0]["status"] = "watch"
    forged["rows"][0]["reason_codes"] = [
        "research_source_authority_event_claim_traceability_stale_source_watch",
    ]
    forged["pass_count"] = "0.000000"
    forged["watch_count"] = "1.000000"
    forged["stale_source_count"] = "1.000000"
    forged["status"] = "watch"
    forged["reason_codes"] = [
        "research_source_authority_event_claim_traceability_report_watch",
        "research_source_authority_event_claim_traceability_stale_source_exception",
    ]
    forged["reason_code_counts"] = [
        {
            "reason_code": (
                "research_source_authority_event_claim_traceability_stale_source_watch"
            ),
            "count": "1.000000",
            "input_ratio": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    forged = signed_public_payload(forged)

    with pytest.raises(ValueError, match="reason_codes"):
        module.validate_research_source_authority_event_claim_traceability_public_payload(
            forged,
        )


def test_signed_zero_inputs_are_canonicalized_for_public_round_trip() -> None:
    module = api()
    negative_zero = d("-0.000000")
    source = claim_input(
        "private-event-claim-signed-zero",
        claim_lineage_depth=negative_zero,
        supporting_source_count=negative_zero,
        authoritative_source_count=negative_zero,
        traced_source_count=negative_zero,
        stale_source_count=negative_zero,
        contradictory_source_count=negative_zero,
        unresolved_claim_count=negative_zero,
        max_source_age_seconds=negative_zero,
    )
    result = build_report(source)
    payload = module.research_source_authority_event_claim_traceability_report_payload(
        result,
    )

    assert_no_signed_zero_decimals(source)
    assert_no_signed_zero_decimals(result)
    assert "-0.000000" not in json.dumps(payload, sort_keys=True)
    module.validate_research_source_authority_event_claim_traceability_public_payload(
        payload,
    )


def test_config_version_rejects_unversioned_semantic_override() -> None:
    with pytest.raises(ValueError, match="min_pass_authority_score.*config_version"):
        config(min_pass_authority_score=d("0.850000"))

    bypassed = config()
    object.__setattr__(bypassed, "min_pass_authority_score", d("0.850000"))
    with pytest.raises(ValueError, match="min_pass_authority_score.*config_version"):
        build_report(claim_input(), cfg=bypassed)


def test_direct_report_rejects_nondeterministic_row_order() -> None:
    result = build_report(
        claim_input("private-event-claim-alpha"),
        claim_input("private-event-claim-beta"),
    )

    with pytest.raises(ValueError, match="deterministic risk sort"):
        replace(
            result,
            rows=tuple(reversed(result.rows)),
            derived_validation_digest="",
        )


def test_direct_report_requires_the_supported_config_version() -> None:
    result = build_report(claim_input("private-event-claim-pass"))

    with pytest.raises(ValueError, match="config_version"):
        replace(
            result,
            config_version="research-source-authority-event-claim-traceability-report-v999",
            derived_validation_digest="",
        )


def test_public_helpers_revalidate_frozen_report_consistency() -> None:
    module = api()
    result = build_report(claim_input("private-event-claim-pass"))
    object.__setattr__(result, "input_row_count", d("2.000000"))

    with pytest.raises(ValueError, match="input_row_count"):
        module.research_source_authority_event_claim_traceability_report_digest(
            result,
        )
    with pytest.raises(ValueError, match="input_row_count"):
        module.research_source_authority_event_claim_traceability_report_payload(
            result,
        )


def test_validation_flags_frozen_dataclasses_and_pure_report_only_surface() -> None:
    module = api()
    result = build_report(claim_input("private-event-claim-pass"))

    assert is_dataclass(config())
    assert is_dataclass(claim_input())
    assert is_dataclass(result)
    assert is_dataclass(result.rows[0])

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().authority_weight = d("0.250000")
    with pytest.raises(ValueError, match="status"):
        replace(result.rows[0], status="block")

    with pytest.raises(ValueError, match="authority_weight"):
        config(authority_weight=_DecimalSubclass("0.350000"))
    with pytest.raises(ValueError, match="supporting_source_count"):
        claim_input(supporting_source_count=4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="weights must sum"):
        config(claim_consistency_weight=d("0.100000"))
    with pytest.raises(ValueError, match="min_pass_authority_score"):
        config(min_pass_authority_score=d("0.500000"))
    with pytest.raises(ValueError, match="source_age_watch_seconds"):
        config(source_age_watch_seconds=d("7200.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        claim_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        claim_input(readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_authority_event_claim_traceability_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 9, 13, 15),
        )
    with pytest.raises(ValueError, match="traced_source_count"):
        claim_input(
            supporting_source_count=d("2.000000"),
            authoritative_source_count=d("2.000000"),
            traced_source_count=d("3.000000"),
        )
    with pytest.raises(ValueError, match="claim counts"):
        claim_input(
            supporting_source_count=d("2.000000"),
            authoritative_source_count=d("2.000000"),
            traced_source_count=d("2.000000"),
            contradictory_source_count=d("2.000000"),
            unresolved_claim_count=d("1.000000"),
        )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "submit_order",
                "place_order",
                "recommend",
                "size_position",
                "write",
                "write_text",
                "write_bytes",
                "touch",
                "mkdir",
                "makedirs",
                "unlink",
                "remove",
                "rename",
                "commit",
            }

    forbidden_import_fragments = (
        "auth",
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "supabase",
        "urllib",
        "wallet",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_public_numeric_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)
    else:
        assert type(value) is not float
        assert type(value) is not int


def assert_no_signed_zero_decimals(value: object) -> None:
    if type(value) is Decimal:
        assert not (value.is_zero() and value.is_signed())
    elif is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_no_signed_zero_decimals(getattr(value, field.name))
    elif isinstance(value, dict):
        for item in value.values():
            assert_no_signed_zero_decimals(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_signed_zero_decimals(item)


def assert_payload_has_no_leaked_keys_or_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "mysql://",
        "jdbc:",
        "candidate-",
        "candidate_id",
        "market-",
        "market_id",
        "market_slug",
        "market_question",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "token",
        "wallet",
        "order",
        "trade",
        "live_surface",
        "sizing",
        "recommendation",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(fragment in lowered_key for fragment in forbidden_fragments)
            assert_payload_has_no_leaked_keys_or_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_leaked_keys_or_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
