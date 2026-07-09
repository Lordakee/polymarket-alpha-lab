from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_resolution_claim_latency_decay_floor_report"
)
GENERATED_AT = datetime(2026, 7, 9, 16, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "latency_watch_seconds": d("1800.000000"),
        "latency_block_seconds": d("7200.000000"),
        "decay_watch_age_seconds": d("3600.000000"),
        "decay_block_age_seconds": d("14400.000000"),
        "floor_pass_score": d("0.800000"),
        "floor_block_score": d("0.400000"),
    }
    values.update(overrides)
    return module.ResearchSourceResolutionClaimLatencyDecayFloorConfig(**values)


def observation(
    resolution_family: str = "official.filing",
    claim_bucket: str = "policy.update",
    *,
    private_trace_ref: str = (
        "raw_candidate_id=secret|market_id=secret|market_slug=secret|"
        "question=private|source_url=https://example.invalid/path?token=secret|"
        "source_text=private text|wallet=secret|order_id=secret|trade_id=secret"
    ),
    observed_at: datetime = GENERATED_AT,
    authority_confidence_score: Decimal = d("0.950000"),
    claim_confidence_score: Decimal = d("0.900000"),
    resolution_claim_latency_seconds: Decimal = d("600.000000"),
    resolution_claim_age_seconds: Decimal = d("1200.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceResolutionClaimLatencyDecayFloorObservation(
        private_trace_ref=private_trace_ref,
        observed_at=observed_at,
        resolution_family=resolution_family,
        claim_bucket=claim_bucket,
        authority_confidence_score=authority_confidence_score,
        claim_confidence_score=claim_confidence_score,
        resolution_claim_latency_seconds=resolution_claim_latency_seconds,
        resolution_claim_age_seconds=resolution_claim_age_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_resolution_claim_latency_decay_floor_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def assert_no_numeric_objects(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_objects(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_numeric_objects(item)
    else:
        assert type(value) not in (Decimal, int, float)


def assert_payload_public_safe(payload: dict[str, Any]) -> None:
    encoded = json.dumps(payload, sort_keys=True).lower()
    forbidden = (
        "raw_candidate",
        "candidate_id",
        "candidate id",
        "market_id",
        "market id",
        "market_slug",
        "market slug",
        "question",
        "source_url",
        "source url",
        "source_text",
        "source text",
        "http://",
        "https://",
        "www.",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommend",
    )
    for fragment in forbidden:
        assert fragment not in encoded


def test_empty_report_blocks_with_flags_decimal_payload_and_digest() -> None:
    module = api()
    result = build_report()

    assert type(result) is module.ResearchSourceResolutionClaimLatencyDecayFloorReport
    assert is_dataclass(result)
    assert result.__dataclass_params__.frozen
    assert result.generated_at == GENERATED_AT
    assert result.status == "block"
    assert result.input_count == d("0.000000")
    assert result.row_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.average_resolution_claim_latency_decay_floor_score == d("0.000000")
    assert result.lowest_resolution_claim_latency_decay_floor_score == d("0.000000")
    assert result.highest_resolution_claim_latency_seconds == d("0.000000")
    assert result.highest_resolution_claim_age_seconds == d("0.000000")
    assert result.reason_codes == (
        "resolution_claim_latency_decay_floor_empty",
    )
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64
    int(result.derived_validation_digest, 16)

    payload = result.payload
    assert payload == module.research_source_resolution_claim_latency_decay_floor_report_payload(
        result,
    )
    assert payload["input_count"] == "0.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert result.derived_validation_digest == module.research_source_resolution_claim_latency_decay_floor_report_digest(
        result,
    )
    assert module.validate_research_source_resolution_claim_latency_decay_floor_report_payload(
        payload,
    )
    assert_no_numeric_objects(payload)
    assert_payload_public_safe(payload)


def test_scores_pass_watch_and_block_resolution_claim_floor_rows() -> None:
    result = build_report(
        observation(),
        observation(
            resolution_family="wire.notice",
            claim_bucket="regional.update",
            authority_confidence_score=d("0.850000"),
            claim_confidence_score=d("0.750000"),
            resolution_claim_latency_seconds=d("2400.000000"),
            resolution_claim_age_seconds=d("7200.000000"),
        ),
        observation(
            resolution_family="thin.summary",
            claim_bucket="late.correction",
            authority_confidence_score=d("0.300000"),
            claim_confidence_score=d("0.650000"),
            resolution_claim_latency_seconds=d("9000.000000"),
            resolution_claim_age_seconds=d("16000.000000"),
        ),
    )

    assert result.status == "block"
    assert result.input_count == d("3.000000")
    assert result.row_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.latency_pressure_count == d("2.000000")
    assert result.decay_pressure_count == d("2.000000")
    assert result.floor_pressure_count == d("2.000000")
    assert result.average_resolution_claim_latency_decay_floor_score == d("0.466667")
    assert result.lowest_resolution_claim_latency_decay_floor_score == d("0.000000")
    assert result.highest_resolution_claim_latency_seconds == d("9000.000000")
    assert result.highest_resolution_claim_age_seconds == d("16000.000000")
    assert result.reason_codes == (
        "resolution_claim_latency_block",
        "resolution_claim_decay_block",
        "resolution_claim_floor_block",
        "resolution_claim_latency_watch",
        "resolution_claim_decay_watch",
        "resolution_claim_floor_watch",
    )
    assert tuple((row.resolution_family, row.claim_bucket) for row in result.rows) == (
        ("thin.summary", "late.correction"),
        ("wire.notice", "regional.update"),
        ("official.filing", "policy.update"),
    )
    assert tuple(row.row_index for row in result.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")

    blocked = result.rows[0]
    assert blocked.latency_status == "block"
    assert blocked.decay_status == "block"
    assert blocked.floor_status == "block"
    assert blocked.latency_health_score == d("0.000000")
    assert blocked.decay_freshness_score == d("0.000000")
    assert blocked.resolution_claim_latency_decay_floor_score == d("0.000000")
    assert blocked.reason_codes == (
        "resolution_claim_latency_block",
        "resolution_claim_decay_block",
        "resolution_claim_floor_block",
    )

    watched = result.rows[1]
    assert watched.latency_status == "watch"
    assert watched.decay_status == "watch"
    assert watched.floor_status == "watch"
    assert watched.latency_health_score == d("0.666667")
    assert watched.decay_freshness_score == d("0.500000")
    assert watched.resolution_claim_latency_decay_floor_score == d("0.500000")
    assert watched.reason_codes == (
        "resolution_claim_latency_watch",
        "resolution_claim_decay_watch",
        "resolution_claim_floor_watch",
    )

    passed = result.rows[2]
    assert passed.latency_status == "pass"
    assert passed.decay_status == "pass"
    assert passed.floor_status == "pass"
    assert passed.latency_health_score == d("0.916667")
    assert passed.decay_freshness_score == d("0.916667")
    assert passed.resolution_claim_latency_decay_floor_score == d("0.900000")
    assert passed.reason_codes == ("resolution_claim_latency_decay_floor_pass",)


def test_payload_is_deterministic_redacted_and_tamper_detecting() -> None:
    module = api()
    first = build_report(
        observation(resolution_family="official.filing", claim_bucket="policy.update"),
        observation(
            resolution_family="thin.summary",
            claim_bucket="late.correction",
            private_trace_ref="market_id=secret|source_text=secret",
            authority_confidence_score=d("0.300000"),
            claim_confidence_score=d("0.650000"),
            resolution_claim_latency_seconds=d("9000.000000"),
            resolution_claim_age_seconds=d("16000.000000"),
        ),
    )
    second = build_report(
        observation(
            resolution_family="thin.summary",
            claim_bucket="late.correction",
            private_trace_ref="changed-private-ref-with-token",
            authority_confidence_score=d("0.300000"),
            claim_confidence_score=d("0.650000"),
            resolution_claim_latency_seconds=d("9000.000000"),
            resolution_claim_age_seconds=d("16000.000000"),
        ),
        observation(
            resolution_family="official.filing",
            claim_bucket="policy.update",
            private_trace_ref="changed-private-ref-with-wallet",
        ),
    )

    payload_a = first.payload
    payload_b = second.payload
    encoded = json.dumps(payload_a, sort_keys=True, allow_nan=False)

    assert payload_a == payload_b
    assert payload_a["generated_at"] == "2026-07-09T16:00:00+00:00"
    assert payload_a["rows"][0]["resolution_family"] == "thin.summary"
    assert payload_a["rows"][0]["resolution_claim_latency_decay_floor_score"] == "0.000000"
    assert payload_a["derived_validation_digest"] == first.derived_validation_digest
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert first.derived_validation_digest == second.derived_validation_digest
    assert_no_numeric_objects(payload_a)
    assert_payload_public_safe(payload_a)
    assert "private_trace_ref" not in encoded
    assert module.validate_research_source_resolution_claim_latency_decay_floor_report_payload(
        payload_a,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered_status = dict(payload_a)
    tampered_status["status"] = "ready"
    assert not module.validate_research_source_resolution_claim_latency_decay_floor_report_payload(
        tampered_status,
    )
    tampered_numeric = dict(payload_a)
    tampered_numeric["row_count"] = 2
    assert not module.validate_research_source_resolution_claim_latency_decay_floor_report_payload(
        tampered_numeric,
    )
    tampered_unsafe = dict(payload_a)
    tampered_unsafe["source_url"] = "https://example.invalid/private"
    assert not module.validate_research_source_resolution_claim_latency_decay_floor_report_payload(
        tampered_unsafe,
    )


def test_validation_rejects_non_decimal_unsafe_labels_flags_dates_and_config() -> None:
    module = api()

    with pytest.raises(ValueError, match="authority_confidence_score must be a Decimal"):
        observation(authority_confidence_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="claim_confidence_score must be a Decimal"):
        observation(claim_confidence_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="resolution_claim_latency_seconds must be nonnegative"):
        observation(resolution_claim_latency_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="authority_confidence_score must be between"):
        observation(authority_confidence_score=d("1.000001"))
    with pytest.raises(ValueError, match="resolution_family contains unsafe text"):
        observation(resolution_family="market.slug")
    with pytest.raises(ValueError, match="claim_bucket contains unsafe text"):
        observation(claim_bucket="candidate.alpha")
    with pytest.raises(ValueError, match="private_trace_ref must be a string"):
        observation(private_trace_ref=object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)
    with pytest.raises(ValueError, match="latency_watch_seconds"):
        config(latency_watch_seconds=d("7200.000000"))
    with pytest.raises(ValueError, match="floor_block_score"):
        config(floor_block_score=d("0.900000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_resolution_claim_latency_decay_floor_report(
            (),
            generated_at=datetime(2026, 7, 9, 16, 0),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(observation(observed_at=datetime(2026, 7, 9, 16, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_source_resolution_claim_latency_decay_floor_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unique"):
        build_report(
            observation(resolution_family="official.filing", claim_bucket="policy.update"),
            observation(resolution_family="official.filing", claim_bucket="policy.update"),
        )

    result = build_report(observation())
    with pytest.raises(ValueError, match="status"):
        replace(result.rows[0], status="ready")
    with pytest.raises(ValueError, match="resolution_claim_latency_decay_floor_score"):
        replace(result.rows[0], resolution_claim_latency_decay_floor_score=d("0.100000"))


def test_exports_frozen_dataclasses_and_status_vocabulary() -> None:
    module = api()
    result = build_report(observation())

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_RESOLUTION_CLAIM_LATENCY_DECAY_FLOOR_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_RESOLUTION_CLAIM_LATENCY_DECAY_FLOOR_STATUSES",
        "ResearchSourceResolutionClaimLatencyDecayFloorConfig",
        "ResearchSourceResolutionClaimLatencyDecayFloorObservation",
        "ResearchSourceResolutionClaimLatencyDecayFloorReasonCodeCount",
        "ResearchSourceResolutionClaimLatencyDecayFloorReport",
        "ResearchSourceResolutionClaimLatencyDecayFloorRow",
        "build_research_source_resolution_claim_latency_decay_floor_report",
        "research_source_resolution_claim_latency_decay_floor_report_digest",
        "research_source_resolution_claim_latency_decay_floor_report_payload",
        "validate_research_source_resolution_claim_latency_decay_floor_report_payload",
    )
    assert module.RESEARCH_SOURCE_RESOLUTION_CLAIM_LATENCY_DECAY_FLOOR_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    for value in (config(), observation(), result, result.rows[0], result.reason_code_counts[0]):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().latency_watch_seconds = d("1.000000")
    with pytest.raises(TypeError):

        class BadReport(module.ResearchSourceResolutionClaimLatencyDecayFloorReport):
            pass


def test_module_scope_has_no_network_database_wallet_order_or_trade_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    forbidden_calls = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "send",
        "trade",
        "order",
        "recommend",
        "size",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_calls

    forbidden_import_fragments = (
        "auth",
        "cli",
        "db",
        "http",
        "psycopg",
        "requests",
        "socket",
        "sql",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    forbidden_public_names = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
    }
    public_fields = {
        field.name
        for cls in (
            module.ResearchSourceResolutionClaimLatencyDecayFloorConfig,
            module.ResearchSourceResolutionClaimLatencyDecayFloorObservation,
            module.ResearchSourceResolutionClaimLatencyDecayFloorReasonCodeCount,
            module.ResearchSourceResolutionClaimLatencyDecayFloorReport,
            module.ResearchSourceResolutionClaimLatencyDecayFloorRow,
        )
        for field in fields(cls)
    }
    assert forbidden_public_names.isdisjoint(public_fields)
