from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_source_authority_claim_latency_decay_report"
)
GENERATED_AT = datetime(2026, 7, 9, 14, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "claim_latency_watch_seconds": d("1800.000000"),
        "claim_latency_block_seconds": d("7200.000000"),
        "authority_decay_watch_age_seconds": d("3600.000000"),
        "authority_decay_block_age_seconds": d("14400.000000"),
        "corroboration_pass_count": d("2.000000"),
        "corroboration_block_count": d("0.000000"),
        "contradiction_watch_threshold": d("0.300000"),
        "contradiction_block_threshold": d("0.600000"),
        "resolution_watch_seconds_remaining": d("1800.000000"),
        "resolution_block_seconds_remaining": d("600.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityClaimLatencyDecayConfig(**values)


def signal(
    authority_family: str = "official.filing",
    claim_bucket: str = "policy-update",
    *,
    source_authority_score: Decimal = d("0.900000"),
    authority_claim_latency_seconds: Decimal = d("600.000000"),
    claim_age_seconds: Decimal = d("1200.000000"),
    corroboration_count: Decimal = d("2.000000"),
    contradiction_pressure_score: Decimal = d("0.050000"),
    resolution_window_seconds: Decimal = d("7200.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceAuthorityClaimLatencyDecayInput(
        authority_family=authority_family,
        claim_bucket=claim_bucket,
        source_authority_score=source_authority_score,
        authority_claim_latency_seconds=authority_claim_latency_seconds,
        claim_age_seconds=claim_age_seconds,
        corroboration_count=corroboration_count,
        contradiction_pressure_score=contradiction_pressure_score,
        resolution_window_seconds=resolution_window_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*signals: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_authority_claim_latency_decay_report(
        signals,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def assert_no_numeric_objects(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_objects(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_numeric_objects(item)
    else:
        assert type(value) not in (Decimal, int, float)


def test_empty_report_is_pass_readonly_digest_validated_and_decimal_only() -> None:
    module = api()
    result = report()

    assert type(result) is module.ResearchSourceAuthorityClaimLatencyDecayReport
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.status == "pass"
    assert result.authority_claim_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.high_latency_count == d("0.000000")
    assert result.authority_decay_count == d("0.000000")
    assert result.corroboration_lag_count == d("0.000000")
    assert result.contradiction_pressure_count == d("0.000000")
    assert result.resolution_pressure_count == d("0.000000")
    assert result.lowest_effective_authority_score == d("0.000000")
    assert result.highest_latency_decay_score == d("0.000000")
    assert result.max_authority_claim_latency_seconds == d("0.000000")
    assert result.max_claim_age_seconds == d("0.000000")
    assert result.nearest_resolution_window_seconds == d("0.000000")
    assert result.reason_codes == (
        "research_source_authority_claim_latency_decay_empty",
    )
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64
    int(result.derived_validation_digest, 16)
    assert (
        result.derived_validation_digest
        == module.research_source_authority_claim_latency_decay_report_digest(result)
    )
    module.validate_research_source_authority_claim_latency_decay_report_digest(result)
    payload = module.research_source_authority_claim_latency_decay_report_payload(result)
    assert payload == result.payload
    assert payload["authority_claim_count"] == "0.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert_no_numeric_objects(payload)


def test_scores_latency_decay_watch_and_block_signals() -> None:
    result = report(
        signal(),
        signal(
            authority_family="wire.roundup",
            claim_bucket="regional-update",
            source_authority_score=d("0.750000"),
            authority_claim_latency_seconds=d("2400.000000"),
            claim_age_seconds=d("7200.000000"),
            corroboration_count=d("1.000000"),
            contradiction_pressure_score=d("0.350000"),
            resolution_window_seconds=d("1200.000000"),
        ),
        signal(
            authority_family="thin.summary",
            claim_bucket="late-correction",
            source_authority_score=d("0.950000"),
            authority_claim_latency_seconds=d("9000.000000"),
            claim_age_seconds=d("16000.000000"),
            corroboration_count=d("0.000000"),
            contradiction_pressure_score=d("0.700000"),
            resolution_window_seconds=d("300.000000"),
        ),
    )

    assert result.status == "block"
    assert result.authority_claim_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.high_latency_count == d("2.000000")
    assert result.authority_decay_count == d("2.000000")
    assert result.corroboration_lag_count == d("2.000000")
    assert result.contradiction_pressure_count == d("2.000000")
    assert result.resolution_pressure_count == d("2.000000")
    assert result.lowest_effective_authority_score == d("0.072833")
    assert result.highest_latency_decay_score == d("0.927167")
    assert result.max_authority_claim_latency_seconds == d("9000.000000")
    assert result.max_claim_age_seconds == d("16000.000000")
    assert result.nearest_resolution_window_seconds == d("300.000000")
    assert result.reason_codes == (
        "claim_latency_decay_block",
        "authority_decay_block",
        "corroboration_lag_block",
        "contradiction_pressure_block",
        "resolution_pressure_block",
        "claim_latency_decay_watch",
        "authority_decay_watch",
        "corroboration_lag_watch",
        "contradiction_pressure_watch",
        "resolution_pressure_watch",
    )

    assert tuple((row.authority_family, row.claim_bucket) for row in result.rows) == (
        ("thin.summary", "late-correction"),
        ("wire.roundup", "regional-update"),
        ("official.filing", "policy-update"),
    )
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")

    blocked = result.rows[0]
    assert blocked.latency_band == "blocked"
    assert blocked.authority_age_band == "expired"
    assert blocked.corroboration_band == "missing"
    assert blocked.resolution_window_band == "immediate"
    assert blocked.effective_authority_score == d("0.072833")
    assert blocked.latency_decay_score == d("0.927167")
    assert blocked.reason_codes == (
        "claim_latency_decay_block",
        "authority_decay_block",
        "corroboration_lag_block",
        "contradiction_pressure_block",
        "resolution_pressure_block",
    )

    watched = result.rows[1]
    assert watched.latency_band == "delayed"
    assert watched.authority_age_band == "stale"
    assert watched.corroboration_band == "thin"
    assert watched.resolution_window_band == "near"
    assert watched.effective_authority_score == d("0.441250")
    assert watched.latency_decay_score == d("0.558750")
    assert watched.reason_codes == (
        "claim_latency_decay_watch",
        "authority_decay_watch",
        "corroboration_lag_watch",
        "contradiction_pressure_watch",
        "resolution_pressure_watch",
    )

    passed = result.rows[2]
    assert passed.latency_band == "current"
    assert passed.authority_age_band == "fresh"
    assert passed.corroboration_band == "corroborated"
    assert passed.resolution_window_band == "open"
    assert passed.effective_authority_score == d("0.853500")
    assert passed.latency_decay_score == d("0.146500")
    assert passed.reason_codes == ("authority_claim_latency_decay_healthy",)


def test_payload_is_deterministic_public_safe_and_digest_validated() -> None:
    module = api()
    first = report(
        signal(authority_family="official.filing", claim_bucket="policy-update"),
        signal(
            authority_family="thin.summary",
            claim_bucket="late-correction",
            source_authority_score=d("0.950000"),
            authority_claim_latency_seconds=d("9000.000000"),
            claim_age_seconds=d("16000.000000"),
            corroboration_count=d("0.000000"),
            contradiction_pressure_score=d("0.700000"),
            resolution_window_seconds=d("300.000000"),
        ),
    )
    second = report(*tuple(reversed(first.rows)))

    payload_a = module.research_source_authority_claim_latency_decay_report_payload(first)
    payload_b = module.research_source_authority_claim_latency_decay_report_payload(second)
    encoded = json.dumps(payload_a, sort_keys=True, allow_nan=False)

    assert payload_a == payload_b
    assert payload_a["generated_at"] == "2026-07-09T14:00:00+00:00"
    assert payload_a["rows"][0]["authority_family"] == "thin.summary"
    assert payload_a["rows"][0]["latency_decay_score"] == "0.927167"
    assert payload_a["derived_validation_digest"] == first.derived_validation_digest
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert first.derived_validation_digest == second.derived_validation_digest
    assert_no_numeric_objects(payload_a)
    module.validate_research_source_authority_claim_latency_decay_public_payload(payload_a)
    assert module.research_source_authority_claim_latency_decay_report_payload(payload_a) == payload_a

    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "url",
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
        field.name for cls in (type(first), type(first.rows[0])) for field in fields(cls)
    }
    assert unsafe_keys.isdisjoint(public_fields)
    for forbidden in unsafe_keys | {"http://", "https://", "postgres://", "://"}:
        assert forbidden not in encoded.lower()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_source_authority_claim_latency_decay_report_payload(
            {**payload_a, "market_id": "hidden"},
        )
    with pytest.raises(ValueError, match="numeric values"):
        module.research_source_authority_claim_latency_decay_report_payload(
            {**payload_a, "authority_claim_count": 2},
        )
    tuple_numeric_payload = {**payload_a, "safe_extra": (2,)}
    tuple_numeric_payload["derived_validation_digest"] = canonical_digest(
        tuple_numeric_payload,
    )
    with pytest.raises(ValueError, match="numeric values"):
        module.validate_research_source_authority_claim_latency_decay_public_payload(
            tuple_numeric_payload,
        )
    tuple_flag_payload = {**payload_a, "safe_extra": ({"readonly": False},)}
    tuple_flag_payload["derived_validation_digest"] = canonical_digest(
        tuple_flag_payload,
    )
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_source_authority_claim_latency_decay_public_payload(
            tuple_flag_payload,
        )
    tuple_status_payload = {**payload_a, "safe_extra": ({"status": "ready"},)}
    tuple_status_payload["derived_validation_digest"] = canonical_digest(
        tuple_status_payload,
    )
    with pytest.raises(ValueError, match="status"):
        module.validate_research_source_authority_claim_latency_decay_public_payload(
            tuple_status_payload,
        )
    with pytest.raises(ValueError, match="readonly"):
        module.research_source_authority_claim_latency_decay_report_payload(
            {**payload_a, "readonly": False},
        )


def test_validation_requires_decimal_inputs_flags_statuses_and_safe_labels() -> None:
    module = api()

    with pytest.raises(ValueError, match="source_authority_score must be a Decimal"):
        signal(source_authority_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_claim_latency_seconds must be a Decimal"):
        signal(authority_claim_latency_seconds=600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_authority_score must be a Decimal"):
        signal(source_authority_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="claim_age_seconds must be nonnegative"):
        signal(claim_age_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="corroboration_count must be an integer Decimal"):
        signal(corroboration_count=d("1.500000"))
    with pytest.raises(ValueError, match="source_authority_score must be between zero and one"):
        signal(source_authority_score=d("1.000001"))
    with pytest.raises(ValueError, match="authority_family contains unsafe text"):
        signal(authority_family="market.slug")
    with pytest.raises(ValueError, match="claim_bucket contains unsafe text"):
        signal(claim_bucket="candidate-alpha")
    with pytest.raises(ValueError, match="authority_family contains unsafe text"):
        signal(authority_family="https://official.example/report")
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        signal(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        signal(readonly=False)
    with pytest.raises(ValueError, match="claim_latency_watch_seconds"):
        config(claim_latency_watch_seconds=d("7200.000000"))
    with pytest.raises(ValueError, match="corroboration_block_count"):
        config(corroboration_block_count=d("2.000000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_authority_claim_latency_decay_report(
            (),
            generated_at=datetime(2026, 7, 9, 14, 0),
        )
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_source_authority_claim_latency_decay_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    result = report(signal())
    with pytest.raises(ValueError, match="status"):
        replace(result, status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(result.rows[0], status="blocked")
    with pytest.raises(ValueError, match="latency_decay_score"):
        replace(result.rows[0], latency_decay_score=d("0.999999"))


def test_exports_frozen_dataclasses_and_status_vocabulary() -> None:
    module = api()
    result = report(signal())

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_AUTHORITY_CLAIM_LATENCY_DECAY_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_AUTHORITY_CLAIM_LATENCY_DECAY_STATUSES",
        "ResearchSourceAuthorityClaimLatencyDecayConfig",
        "ResearchSourceAuthorityClaimLatencyDecayInput",
        "ResearchSourceAuthorityClaimLatencyDecayReport",
        "ResearchSourceAuthorityClaimLatencyDecayRow",
        "build_research_source_authority_claim_latency_decay_report",
        "research_source_authority_claim_latency_decay_report_digest",
        "research_source_authority_claim_latency_decay_report_payload",
        "validate_research_source_authority_claim_latency_decay_public_payload",
        "validate_research_source_authority_claim_latency_decay_report_digest",
    )
    assert module.RESEARCH_SOURCE_AUTHORITY_CLAIM_LATENCY_DECAY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(config())
    assert is_dataclass(signal())
    assert is_dataclass(result)
    assert is_dataclass(result.rows[0])

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().claim_latency_watch_seconds = d("1.000000")


def test_module_scope_is_pure_public_safe_report_only() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/research_source_authority_claim_latency_decay_report.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source_text)
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
                "scrape",
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
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert ".timestamp(" not in source_text
    assert ".total_seconds(" not in source_text
