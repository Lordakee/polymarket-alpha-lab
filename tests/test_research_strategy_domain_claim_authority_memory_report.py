from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_domain_claim_authority_memory_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_domain_claim_authority_memory_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "fresh_memory_age_seconds": d("3600.000000"),
        "stale_memory_age_seconds": d("86400.000000"),
        "pass_threshold": d("0.750000"),
        "watch_threshold": d("0.550000"),
        "min_pass_authority_score": d("0.800000"),
        "min_watch_authority_score": d("0.550000"),
        "min_pass_memory_reuse_score": d("0.750000"),
        "min_watch_memory_reuse_score": d("0.500000"),
        "min_pass_claim_confidence_score": d("0.800000"),
        "min_watch_claim_confidence_score": d("0.550000"),
        "max_pass_contradiction_pressure": d("0.200000"),
        "max_watch_contradiction_pressure": d("0.600000"),
        "min_pass_source_quorum_score": d("0.750000"),
        "min_watch_source_quorum_score": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchStrategyDomainClaimAuthorityMemoryConfig(**values)


def claim_signal(
    index: int,
    *,
    domain_key: str = "macro",
    claim_bucket: str | None = None,
    claim_observed_at: datetime | None = None,
    memory_recorded_at: datetime | None = None,
    authority_score: Decimal = d("0.900000"),
    memory_reuse_score: Decimal = d("0.850000"),
    claim_confidence_score: Decimal = d("0.900000"),
    contradiction_pressure: Decimal = d("0.050000"),
    source_quorum_score: Decimal = d("0.900000"),
    reason_codes: tuple[str, ...] = (),
) -> Any:
    module = api()
    raw_candidate = "raw_" + "cand" + "idate_id"
    market_key = "mar" + "ket_id"
    market_slug = "mar" + "ket_sl" + "ug"
    market_question = "mar" + "ket_ques" + "tion"
    source_url = "sou" + "rce_u" + "rl"
    source_text = "sou" + "rce_tex" + "t"
    secret_token = "tok" + "en"
    private_wallet = "wal" + "let"
    private_order = "ord" + "er"
    private_trade = "tra" + "de"
    return module.ResearchStrategyDomainClaimAuthorityMemoryInput(
        domain_key=domain_key,
        claim_bucket=claim_bucket or f"claim-{index:03d}",
        private_candidate_reference=f"{raw_candidate}=CAND-{index:03d}; {secret_token}=secret",
        private_market_reference=(
            f"{market_key}=0xMARKET{index:03d}; {market_slug}=alpha-{index}; "
            f"{market_question}=Will Alpha resolve {index}?"
        ),
        private_source_reference=(
            f"{source_url}=https://authority.example.test/private/{index}; "
            f"d{'sn'}=postgres://user:pass@host/db; "
            f"tab{'le'}=claim_memory; {private_wallet}=0xabc; "
            f"{private_order}={index}; {private_trade}={index}; "
            f"li{'ve'} feed; {source_text}=private evidence"
        ),
        claim_observed_at=claim_observed_at
        if claim_observed_at is not None
        else GENERATED_AT - timedelta(hours=2),
        memory_recorded_at=memory_recorded_at
        if memory_recorded_at is not None
        else GENERATED_AT - timedelta(minutes=30),
        authority_score=authority_score,
        memory_reuse_score=memory_reuse_score,
        claim_confidence_score=claim_confidence_score,
        contradiction_pressure=contradiction_pressure,
        source_quorum_score=source_quorum_score,
        reason_codes=reason_codes,
    )


def build_report(
    rows: tuple[Any, ...],
    *,
    config: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_strategy_domain_claim_authority_memory_report(
        rows,
        generated_at=generated_at,
        config=config if config is not None else cfg(),
    )


def test_report_scores_domain_claim_authority_memory_without_public_raw_surfaces() -> None:
    module = api()
    report = build_report(
        (
            claim_signal(
                1,
                domain_key="macro",
                claim_bucket="alpha-pass",
            ),
            claim_signal(
                2,
                domain_key="sports",
                claim_bucket="beta-watch",
                memory_recorded_at=GENERATED_AT - timedelta(hours=8),
                authority_score=d("0.650000"),
                memory_reuse_score=d("0.620000"),
                claim_confidence_score=d("0.700000"),
                contradiction_pressure=d("0.300000"),
                source_quorum_score=d("0.600000"),
                reason_codes=("manual_review",),
            ),
            claim_signal(
                3,
                domain_key="crypto",
                claim_bucket="gamma-block",
                memory_recorded_at=GENERATED_AT - timedelta(days=3),
                authority_score=d("0.250000"),
                memory_reuse_score=d("0.300000"),
                claim_confidence_score=d("0.400000"),
                contradiction_pressure=d("0.800000"),
                source_quorum_score=d("0.350000"),
            ),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-strategy-domain-claim-authority-memory-report-v0"
    assert report.signal_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.status == "block"
    assert report.average_authority_memory_score == d("0.612022")
    assert report.weakest_authority_memory_score == d("0.275000")
    assert report.highest_contradiction_pressure == d("0.800000")
    assert report.oldest_memory_age_seconds == d("259200.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    block_row, watch_row, pass_row = report.rows
    assert type(block_row) is module.ResearchStrategyDomainClaimAuthorityMemoryRow
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert block_row.rank == d("1")
    assert block_row.domain_key == "crypto"
    assert block_row.claim_digest.startswith("sha256:")
    assert block_row.source_digest.startswith("sha256:")
    assert block_row.claim_digest != "gamma-block"
    assert block_row.memory_freshness_score == d("0.000000")
    assert block_row.authority_memory_score == d("0.275000")
    assert block_row.reason_codes == (
        "authority_memory_score_block",
        "authority_score_block",
        "memory_reuse_block",
        "claim_confidence_block",
        "contradiction_pressure_block",
        "source_quorum_block",
        "memory_age_block",
    )

    assert watch_row.status == "watch"
    assert watch_row.memory_age_seconds == d("28800.000000")
    assert watch_row.memory_freshness_score == d("0.695652")
    assert watch_row.authority_memory_score == d("0.656065")
    assert watch_row.reason_codes == (
        "authority_memory_score_watch",
        "authority_score_watch",
        "memory_reuse_watch",
        "claim_confidence_watch",
        "contradiction_pressure_watch",
        "source_quorum_watch",
        "memory_age_watch",
    )
    assert pass_row.status == "pass"
    assert pass_row.authority_memory_score == d("0.905000")
    assert pass_row.reason_codes == ("authority_memory_pass",)

    payload = module.research_strategy_domain_claim_authority_memory_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True).lower()
    forbidden = (
        "raw_" + "candidate",
        "cand-001",
        "market_" + "id",
        "market_" + "slug",
        "market_" + "question",
        "will alpha resolve",
        "https://authority.example.test",
        "d" + "sn=postgres",
        "claim_memory",
        "tok" + "en=secret",
        "wal" + "let=0xabc",
        "ord" + "er=1",
        "tra" + "de=1",
        "li" + "ve feed",
        "source text",
        "private_candidate_reference",
        "private_market_reference",
        "private_source_reference",
    )
    assert all(term not in encoded for term in forbidden)
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_empty_report_blocks_at_report_only_boundary() -> None:
    report = build_report(())

    assert report.signal_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.status == "block"
    assert report.reason_codes == ("empty_domain_claim_authority_memory_inputs",)
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert report.average_authority_memory_score == d("0.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_digest_is_deterministic_and_validated() -> None:
    module = api()
    first = build_report(
        (
            claim_signal(2, claim_bucket="beta-watch"),
            claim_signal(1, claim_bucket="alpha-pass"),
        ),
    )
    second = build_report(
        (
            claim_signal(1, claim_bucket="alpha-pass"),
            claim_signal(2, claim_bucket="beta-watch"),
        ),
    )

    payload = module.research_strategy_domain_claim_authority_memory_report_payload(first)
    payload_again = module.research_strategy_domain_claim_authority_memory_report_payload(
        second,
    )
    unsigned_payload = dict(payload)
    digest = unsigned_payload.pop("public_payload_sha256")
    canonical = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )

    assert payload == payload_again
    assert first.public_payload_sha256 == second.public_payload_sha256
    assert payload["public_payload_sha256"] == first.public_payload_sha256
    assert digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert len(module.research_strategy_domain_claim_authority_memory_report_digest(first)) == 64
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["rows"][0]["authority_score"] == "0.900000"

    with pytest.raises(ValueError, match="public_payload_sha256"):
        replace(first, public_payload_sha256="0" * 64)

    tampered = dict(payload)
    tampered["public_payload_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="public_payload_sha256"):
        module.research_strategy_domain_claim_authority_memory_report_payload(tampered)

    object.__setattr__(first, "public_payload_sha256", "0" * 64)
    with pytest.raises(ValueError, match="public_payload_sha256"):
        module.research_strategy_domain_claim_authority_memory_report_payload(first)


def test_payload_dict_validation_rejects_recomputed_noncanonical_public_payloads() -> None:
    module = api()
    report = build_report((claim_signal(1),))
    payload = module.research_strategy_domain_claim_authority_memory_report_payload(report)

    invalid_score = _resign_payload(
        {
            **payload,
            "average_authority_memory_score": "0.000000",
            "weakest_authority_memory_score": "0.000000",
            "rows": [
                {
                    **payload["rows"][0],
                    "authority_memory_score": "0.000000",
                },
            ],
        },
    )
    with pytest.raises(ValueError, match="authority_memory_score must match row inputs"):
        module.research_strategy_domain_claim_authority_memory_report_payload(
            invalid_score,
        )

    invalid_status = _resign_payload(
        {
            **payload,
            "status": "blocked",
        },
    )
    with pytest.raises(ValueError, match="status"):
        module.research_strategy_domain_claim_authority_memory_report_payload(
            invalid_status,
        )

    extra_private_surface = _resign_payload(
        {
            **payload,
            "private_candidate_reference": "redacted",
        },
    )
    with pytest.raises(ValueError, match="public payload"):
        module.research_strategy_domain_claim_authority_memory_report_payload(
            extra_private_surface,
        )


def test_datetimes_normalize_to_utc_and_reject_invalid_time_values() -> None:
    eastern = timezone(timedelta(hours=-4))
    report = build_report(
        (
            claim_signal(
                1,
                claim_observed_at=datetime(2026, 7, 9, 7, 0, tzinfo=eastern),
                memory_recorded_at=datetime(2026, 7, 9, 7, 30, tzinfo=eastern),
            ),
        ),
    )

    assert report.rows[0].claim_age_seconds == d("3600.000000")
    assert report.rows[0].memory_age_seconds == d("1800.000000")

    class DateTimeSubclass(datetime):
        pass

    class NoneOffsetTz(tzinfo):
        def utcoffset(self, dt):
            return None

        def dst(self, dt):
            return None

    with pytest.raises(ValueError, match="claim_observed_at must be timezone-aware"):
        claim_signal(1, claim_observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_report(
            (claim_signal(1),),
            generated_at=DateTimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="memory_recorded_at must be timezone-aware"):
        claim_signal(
            1,
            memory_recorded_at=datetime(2026, 7, 9, 12, 0, tzinfo=NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="claim_observed_at must not be after"):
        build_report(
            (claim_signal(1, claim_observed_at=GENERATED_AT + timedelta(seconds=1)),),
        )
    with pytest.raises(ValueError, match="memory_recorded_at must not be after"):
        build_report(
            (claim_signal(1, memory_recorded_at=GENERATED_AT + timedelta(seconds=1)),),
        )


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    sample_config = cfg()
    sample_input = claim_signal(1)
    sample_report = build_report((sample_input,))
    sample_row = sample_report.rows[0]
    sample_reason_count = sample_report.reason_code_counts[0]

    for item in (
        sample_config,
        sample_input,
        sample_row,
        sample_reason_count,
        sample_report,
    ):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(sample_input, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(sample_row, readonly=False)
    with pytest.raises(ValueError, match="authority_score must be a Decimal"):
        claim_signal(1, authority_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_reuse_score must be a Decimal"):
        claim_signal(1, memory_reuse_score=DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="authority_score"):
        claim_signal(1, authority_score=d("1.100000"))
    with pytest.raises(ValueError, match="threshold"):
        cfg(pass_threshold=d("0.500000"), watch_threshold=d("0.600000"))
    with pytest.raises(ValueError, match="domain_key"):
        claim_signal(1, domain_key="market_slug_raw")
    with pytest.raises(ValueError, match="reason_codes"):
        claim_signal(1, reason_codes=("Needs Review",))

    with pytest.raises(ValueError, match="status"):
        replace(sample_row, status="blocked")
    ordered_report = build_report((claim_signal(1), claim_signal(2)))
    unsorted_rows = (
        replace(ordered_report.rows[1], rank=d("1")),
        replace(ordered_report.rows[0], rank=d("2")),
    )
    with pytest.raises(ValueError, match="rows must use deterministic sequence"):
        replace(ordered_report, rows=unsorted_rows)

    assert module.RESEARCH_STRATEGY_DOMAIN_CLAIM_AUTHORITY_MEMORY_STATUSES == (
        "pass",
        "watch",
        "block",
    )


def test_public_api_is_exactly_the_report_only_surface() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_DOMAIN_CLAIM_AUTHORITY_MEMORY_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_DOMAIN_CLAIM_AUTHORITY_MEMORY_STATUSES",
        "ResearchStrategyDomainClaimAuthorityMemoryConfig",
        "ResearchStrategyDomainClaimAuthorityMemoryInput",
        "ResearchStrategyDomainClaimAuthorityMemoryReasonCodeCount",
        "ResearchStrategyDomainClaimAuthorityMemoryReport",
        "ResearchStrategyDomainClaimAuthorityMemoryRow",
        "build_research_strategy_domain_claim_authority_memory_report",
        "research_strategy_domain_claim_authority_memory_report_digest",
        "research_strategy_domain_claim_authority_memory_report_payload",
    )


def test_module_has_no_side_effect_surfaces_or_literal_float_constants() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "web3",
        "open(",
        "connect(",
        "request(",
        "post(",
        "get(",
        "send(",
        "submit(",
        "cancel(",
        "place_" + "order(",
        "position_" + "size",
        "si" + "zing",
        "rec" + "ommendation",
        "net" + "work",
        "li" + "ve trading",
    )
    assert all(term not in lowered for term in forbidden_terms)

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


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


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("public_payload_sha256", None)
    payload["public_payload_sha256"] = hashlib.sha256(
        json.dumps(
            unsigned_payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    return payload
