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


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_authority_claim_recovery_score_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "pass_recovery_score": d("0.700000"),
        "watch_recovery_score": d("0.400000"),
        "authority_watch_floor": d("0.600000"),
        "freshness_watch_floor": d("0.500000"),
        "contradiction_watch_ratio": d("0.250000"),
        "contradiction_block_ratio": d("0.500000"),
        "authority_weight": d("0.400000"),
        "recovery_weight": d("0.350000"),
        "freshness_weight": d("0.150000"),
        "contradiction_penalty_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityClaimRecoveryScoreConfig(**values)


def input_row(
    claim_bucket: str,
    authority_group: str,
    *,
    claim_count: Decimal = d("4.000000"),
    recovered_claim_count: Decimal = d("4.000000"),
    authoritative_corroboration_count: Decimal = d("2.000000"),
    authority_score: Decimal = d("0.900000"),
    freshness_score: Decimal = d("0.800000"),
    contradiction_count: Decimal = d("0.000000"),
) -> Any:
    module = api()
    return module.ResearchSourceAuthorityClaimRecoveryInput(
        claim_bucket=claim_bucket,
        authority_group=authority_group,
        claim_count=claim_count,
        recovered_claim_count=recovered_claim_count,
        authoritative_corroboration_count=authoritative_corroboration_count,
        authority_score=authority_score,
        freshness_score=freshness_score,
        contradiction_count=contradiction_count,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_authority_claim_recovery_score_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_empty_report_is_blocked_readonly_and_digest_verified() -> None:
    module = api()
    report = build_report()
    payload = module.research_source_authority_claim_recovery_score_report_payload(report)

    assert type(report) is module.ResearchSourceAuthorityClaimRecoveryScoreReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.bucket_count == d("0.000000")
    assert report.claim_count == d("0.000000")
    assert report.recovered_claim_count == d("0.000000")
    assert report.recovery_rows == ()
    assert report.reason_codes == ("research_source_authority_claim_recovery_no_inputs",)
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_score_report_ranks_block_watch_pass_and_stable_ties() -> None:
    report = build_report(
        input_row("sports_soccer", "official"),
        input_row(
            "macro_rates",
            "independent",
            recovered_claim_count=d("2.000000"),
            authoritative_corroboration_count=d("1.000000"),
            authority_score=d("0.700000"),
            freshness_score=d("0.500000"),
            contradiction_count=d("1.000000"),
        ),
        input_row(
            "crypto_btc",
            "independent",
            recovered_claim_count=d("2.000000"),
            authoritative_corroboration_count=d("1.000000"),
            authority_score=d("0.700000"),
            freshness_score=d("0.500000"),
            contradiction_count=d("1.000000"),
        ),
        input_row(
            "politics",
            "secondary",
            recovered_claim_count=d("0.000000"),
            authoritative_corroboration_count=d("0.000000"),
            authority_score=d("0.300000"),
            freshness_score=d("0.200000"),
            contradiction_count=d("2.000000"),
        ),
    )

    assert tuple(row.status for row in report.recovery_rows) == (
        "block",
        "watch",
        "watch",
        "pass",
    )
    assert tuple(row.claim_bucket for row in report.recovery_rows) == (
        "politics",
        "crypto_btc",
        "macro_rates",
        "sports_soccer",
    )
    assert tuple(row.recovery_ratio for row in report.recovery_rows) == (
        d("0.000000"),
        d("0.500000"),
        d("0.500000"),
        d("1.000000"),
    )
    assert tuple(row.contradiction_ratio for row in report.recovery_rows) == (
        d("0.500000"),
        d("0.250000"),
        d("0.250000"),
        d("0.000000"),
    )
    assert tuple(row.recovery_score for row in report.recovery_rows) == (
        d("0.100000"),
        d("0.505000"),
        d("0.505000"),
        d("0.830000"),
    )
    assert report.status == "block"
    assert report.bucket_count == d("4.000000")
    assert report.claim_count == d("16.000000")
    assert report.recovered_claim_count == d("8.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("2.000000")
    assert report.block_count == d("1.000000")
    assert report.average_recovery_score == d("0.485000")
    assert report.reason_codes == (
        "research_source_authority_claim_recovery_no_recovery",
        "research_source_authority_claim_recovery_low_authority",
        "research_source_authority_claim_recovery_stale_support",
        "research_source_authority_claim_recovery_contradiction_pressure",
        "research_source_authority_claim_recovery_watch",
        "research_source_authority_claim_recovery_block",
    )


def test_statuses_are_exactly_pass_watch_block() -> None:
    module = api()
    pass_report = build_report(input_row("sports_soccer", "official"))
    watch_report = build_report(
        input_row(
            "macro_rates",
            "independent",
            recovered_claim_count=d("2.000000"),
            authority_score=d("0.700000"),
            freshness_score=d("0.500000"),
            contradiction_count=d("1.000000"),
        ),
    )
    block_report = build_report(
        input_row(
            "politics",
            "secondary",
            recovered_claim_count=d("0.000000"),
            authoritative_corroboration_count=d("0.000000"),
            authority_score=d("0.300000"),
            freshness_score=d("0.200000"),
            contradiction_count=d("2.000000"),
        ),
    )

    assert module.STATUSES == ("pass", "watch", "block")
    assert pass_report.status == "pass"
    assert pass_report.recovery_rows[0].status == "pass"
    assert watch_report.status == "watch"
    assert watch_report.recovery_rows[0].status == "watch"
    assert block_report.status == "block"
    assert block_report.recovery_rows[0].status == "block"


def test_report_rejects_non_decimal_numeric_inputs() -> None:
    module = api()
    with pytest.raises(ValueError, match="pass_recovery_score must be a Decimal"):
        config(pass_recovery_score=1)
    with pytest.raises(ValueError, match="authority_weight must be a Decimal"):
        config(authority_weight=_DecimalSubclass("0.400000"))
    with pytest.raises(ValueError, match="claim_count must be a Decimal"):
        input_row(
            "politics",
            "official",
            claim_count=4,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="authority_score must be a Decimal"):
        input_row(
            "politics",
            "official",
            authority_score=0.9,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_authority_claim_recovery_score_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )


def test_payload_is_deterministic_json_ready_public_safe_and_digest_verified() -> None:
    module = api()
    rows = (
        input_row("sports_soccer", "official"),
        input_row(
            "politics",
            "secondary",
            recovered_claim_count=d("0.000000"),
            authoritative_corroboration_count=d("0.000000"),
            authority_score=d("0.300000"),
            freshness_score=d("0.200000"),
            contradiction_count=d("2.000000"),
        ),
    )

    payload = module.research_source_authority_claim_recovery_score_report_payload(
        build_report(*rows),
    )
    reversed_payload = module.research_source_authority_claim_recovery_score_report_payload(
        build_report(*reversed(rows)),
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["recovery_rows"][0]["recovery_score"] == "0.100000"
    assert payload["recovery_rows"][1]["recovery_score"] == "0.830000"
    assert json.dumps(payload, sort_keys=True)
    assert module.research_source_authority_claim_recovery_score_report_digest(
        build_report(*rows),
    ) == payload["derived_validation_digest"]

    def assert_public_safe(value: object) -> None:
        forbidden_keys = (
            "candidate_id",
            "market_id",
            "market_slug",
            "question",
            "source_id",
            "source_url",
            "source_text",
            "dsn",
            "table_name",
            "token",
            "wallet",
            "order",
            "trade",
        )
        if isinstance(value, dict):
            for key, item in value.items():
                assert not any(fragment in key.lower() for fragment in forbidden_keys)
                assert_public_safe(item)
        elif isinstance(value, list):
            for item in value:
                assert_public_safe(item)
        else:
            assert type(value) is not float
            assert type(value) is not int
            if isinstance(value, str):
                assert not value.startswith(("http://", "https://", "postgres://"))

    assert_public_safe(payload)


def test_frozen_dataclasses_and_hard_flags_are_enforced() -> None:
    report = build_report(input_row("sports_soccer", "official"))

    assert is_dataclass(config())
    assert is_dataclass(input_row("sports_soccer", "official"))
    assert is_dataclass(report)
    assert is_dataclass(report.recovery_rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.recovery_rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().authority_weight = d("0.500000")

    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(input_row("sports_soccer", "official"), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report(input_row("sports_soccer", "official"))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            recovery_rows=(
                replace(
                    report.recovery_rows[0],
                    recovery_score=d("0.700000"),
                    reason_codes=(
                        "research_source_authority_claim_recovery_pass",
                    ),
                ),
            ),
        )


def test_unsafe_public_identifiers_are_rejected_before_payload() -> None:
    for claim_bucket in (
        "candidate_id_secret",
        "market_slug_secret",
        "market_id_secret",
        "raw_question_secret",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            input_row(claim_bucket, "official")

    for authority_group in (
        "source_id_secret",
        "source_url_secret",
        "source_text_secret",
        "dsn_secret",
        "table_name_secret",
        "token_secret",
        "wallet_secret",
        "order_secret",
        "trade_secret",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            input_row("politics", authority_group)


def test_module_scope_has_no_db_network_wallet_order_or_trading_surfaces() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_AUTHORITY_CLAIM_RECOVERY_SCORE_CONFIG_VERSION",
        "STATUSES",
        "ResearchSourceAuthorityClaimRecoveryInput",
        "ResearchSourceAuthorityClaimRecoveryScoreConfig",
        "ResearchSourceAuthorityClaimRecoveryScoreReport",
        "ResearchSourceAuthorityClaimRecoveryScoreRow",
        "build_research_source_authority_claim_recovery_score_report",
        "research_source_authority_claim_recovery_score_report_digest",
        "research_source_authority_claim_recovery_score_report_payload",
    )

    unsafe_field_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_id",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    )
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in unsafe_field_fragments)

    for cls in (
        module.ResearchSourceAuthorityClaimRecoveryInput,
        module.ResearchSourceAuthorityClaimRecoveryScoreConfig,
        module.ResearchSourceAuthorityClaimRecoveryScoreReport,
        module.ResearchSourceAuthorityClaimRecoveryScoreRow,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in unsafe_field_fragments)

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
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
