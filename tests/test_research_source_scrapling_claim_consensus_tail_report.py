from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_source_scrapling_claim_consensus_tail_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_scrapling_claim_consensus_tail_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 45, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "research-source-scrapling-claim-consensus-tail-report-v1",
        "watch_consensus_score_floor": d("0.700000"),
        "block_consensus_score_floor": d("0.450000"),
        "watch_scrapling_confidence_score_floor": d("0.650000"),
        "block_scrapling_confidence_score_floor": d("0.400000"),
        "watch_tail_disagreement_score": d("0.350000"),
        "block_tail_disagreement_score": d("0.700000"),
        "watch_contradiction_score": d("0.250000"),
        "block_contradiction_score": d("0.600000"),
        "min_family_count": d("2"),
        "min_evidence_count": d("3"),
        "block_watch_signal_count": d("3"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceScraplingClaimConsensusTailConfig(**values)


def observation(
    *,
    observed_at: datetime = OBSERVED_AT,
    consensus_score: Decimal = d("0.850000"),
    scrapling_confidence_score: Decimal = d("0.800000"),
    tail_disagreement_score: Decimal = d("0.100000"),
    contradiction_score: Decimal = d("0.050000"),
    family_count: Decimal = d("3"),
    evidence_count: Decimal = d("5"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchSourceScraplingClaimConsensusTailObservation(
        observed_at=observed_at,
        consensus_score=consensus_score,
        scrapling_confidence_score=scrapling_confidence_score,
        tail_disagreement_score=tail_disagreement_score,
        contradiction_score=contradiction_score,
        family_count=family_count,
        evidence_count=evidence_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*observations: object, generated_at: datetime = GENERATED_AT, cfg: object | None = None):
    module = api()
    return module.build_research_source_scrapling_claim_consensus_tail_report(
        observations,
        generated_at=generated_at,
        config=cfg or config(),
    )


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_public_number_payload(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_public_number_payload(item_value)


def assert_no_forbidden_public_surface(value: Any) -> None:
    forbidden_key_fragments = (
        "raw",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "private",
        "auth",
        "wallet",
        "network",
        "database",
        "order",
        "buy",
        "sell",
        "trade",
        "position",
        "recommend",
        "sizing",
        "live",
    )
    forbidden_value_fragments = (
        "raw-candidate",
        "market_id",
        "market-slug",
        "question?",
        "://",
        "www.",
        "postgres://",
        "wallet",
        "order",
        "trade",
        "token",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_key_fragments:
                assert fragment not in lowered, key
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for fragment in forbidden_value_fragments:
            assert fragment not in lowered, value


def test_empty_input_returns_pass_report_only_decimal_digest() -> None:
    module = api()
    empty_report = report()

    assert is_dataclass(empty_report)
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == (
        "research-source-scrapling-claim-consensus-tail-report-v1"
    )
    assert empty_report.status == "pass"
    assert empty_report.reason_codes == ("scrapling_claim_consensus_tail_pass",)
    assert empty_report.observation_count == d("0")
    assert empty_report.pass_count == d("0")
    assert empty_report.watch_count == d("0")
    assert empty_report.block_count == d("0")
    assert empty_report.max_tail_pressure_score == d("0.000000")
    assert empty_report.min_consensus_score is None
    assert empty_report.min_scrapling_confidence_score is None
    assert empty_report.rows == ()
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True

    payload = module.research_source_scrapling_claim_consensus_tail_report_payload(
        empty_report,
    )
    digest_value = module.research_source_scrapling_claim_consensus_tail_report_digest(
        empty_report,
    )
    json.dumps(payload, sort_keys=True)
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert payload["observation_count"] == "0.000000"
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64
    assert module.validate_research_source_scrapling_claim_consensus_tail_public_payload(
        payload,
    ) is None


def test_report_scores_consensus_tail_watch_and_block() -> None:
    passed = observation(observed_at=GENERATED_AT - timedelta(minutes=3))
    watched = observation(
        observed_at=GENERATED_AT - timedelta(minutes=2),
        consensus_score=d("0.680000"),
        tail_disagreement_score=d("0.450000"),
    )
    blocked = observation(
        observed_at=GENERATED_AT - timedelta(minutes=1),
        consensus_score=d("0.300000"),
        scrapling_confidence_score=d("0.350000"),
        tail_disagreement_score=d("0.800000"),
        contradiction_score=d("0.700000"),
        family_count=d("1"),
        evidence_count=d("1"),
    )

    built = report(watched, blocked, passed)

    assert built.status == "block"
    assert built.observation_count == d("3")
    assert built.pass_count == d("1")
    assert built.watch_count == d("1")
    assert built.block_count == d("1")
    assert built.weak_consensus_count == d("2")
    assert built.weak_scrapling_confidence_count == d("1")
    assert built.tail_disagreement_count == d("2")
    assert built.contradiction_count == d("1")
    assert built.sparse_family_count == d("1")
    assert built.sparse_evidence_count == d("1")
    assert built.max_tail_pressure_score == d("0.800000")
    assert built.min_consensus_score == d("0.300000")
    assert built.min_scrapling_confidence_score == d("0.350000")
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")

    blocked_row, watched_row, passed_row = built.rows
    assert blocked_row.row_label == "redacted-claim-consensus-tail-000001"
    assert blocked_row.tail_pressure_score == d("0.800000")
    assert blocked_row.watch_signal_count == d("6")
    assert blocked_row.status == "block"
    assert blocked_row.reason_codes == (
        "low_consensus_block",
        "low_scrapling_confidence_block",
        "tail_disagreement_block",
        "contradiction_block",
        "sparse_family_watch",
        "sparse_evidence_watch",
        "scrapling_claim_consensus_tail_block",
    )

    assert watched_row.watch_signal_count == d("2")
    assert watched_row.status == "watch"
    assert watched_row.reason_codes == (
        "low_consensus_watch",
        "tail_disagreement_watch",
        "scrapling_claim_consensus_tail_watch",
    )
    assert passed_row.status == "pass"
    assert passed_row.reason_codes == ("scrapling_claim_consensus_tail_pass",)


def test_payload_is_decimal_string_sanitized_deterministic_and_digest_checked() -> None:
    module = api()
    observations = (
        observation(
            observed_at=GENERATED_AT - timedelta(minutes=2),
            consensus_score=d("0.680000"),
            tail_disagreement_score=d("0.450000"),
        ),
        observation(
            observed_at=GENERATED_AT - timedelta(minutes=1),
            consensus_score=d("0.300000"),
            scrapling_confidence_score=d("0.350000"),
            tail_disagreement_score=d("0.800000"),
            contradiction_score=d("0.700000"),
            family_count=d("1"),
            evidence_count=d("1"),
        ),
    )
    first = report(*observations)
    second = report(*reversed(observations))

    payload = first.payload
    second_payload = second.payload
    json.dumps(payload, sort_keys=True)
    assert payload == second_payload
    assert payload["rows"][0]["status"] == "block"
    assert payload["rows"][0]["consensus_score"] == "0.300000"
    assert payload["rows"][1]["tail_disagreement_score"] == "0.450000"
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert module.research_source_scrapling_claim_consensus_tail_report_digest(first) == (
        first.derived_validation_digest
    )
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered = dict(payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_scrapling_claim_consensus_tail_public_payload(
            tampered,
        )

    unsafe = dict(payload)
    unsafe["source_url"] = "https://example.invalid/raw-candidate-007"
    unsafe_without_digest = dict(unsafe)
    unsafe_without_digest.pop("derived_validation_digest")
    unsafe["derived_validation_digest"] = hashlib.sha256(
        json.dumps(unsafe_without_digest, sort_keys=True, separators=(",", ":")).encode(
            "utf-8",
        ),
    ).hexdigest()
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_research_source_scrapling_claim_consensus_tail_public_payload(
            unsafe,
        )


def test_dataclasses_are_frozen_strict_and_enforce_flags() -> None:
    module = api()
    built = report(observation())

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchSourceScraplingClaimConsensusTailConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built.rows[0], readonly=False)

    with pytest.raises(ValueError, match="consensus_score must be exactly Decimal"):
        observation(consensus_score=_DecimalSubclass("0.400000"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="tail_disagreement_score must be a Decimal"):
        observation(tail_disagreement_score=0.4)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="family_count must be a whole Decimal"):
        observation(family_count=d("1.5"))

    with pytest.raises(ValueError, match="timezone-aware"):
        observation(observed_at=datetime(2026, 7, 9, 11, 45))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(observation(), generated_at=_DatetimeSubclass(2026, 7, 9, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="utcoffset"):
        observation(observed_at=datetime(2026, 7, 9, 11, 45, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="block_consensus_score_floor"):
        config(block_consensus_score_floor=d("0.800000"))


def test_module_scope_has_no_forbidden_imports_or_payload_surfaces() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)

    for cls in (
        module.ResearchSourceScraplingClaimConsensusTailRow,
        module.ResearchSourceScraplingClaimConsensusTailReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert "raw" not in lowered
            assert "candidate" not in lowered
            assert "market_id" not in lowered
            assert "market_slug" not in lowered
            assert "slug" not in lowered
            assert "question" not in lowered
            assert "source_url" not in lowered
            assert "source_text" not in lowered
            assert "url" not in lowered
            assert "text" not in lowered
            assert "dsn" not in lowered
            assert "table" not in lowered
            assert "token" not in lowered
            assert "wallet" not in lowered
            assert "auth" not in lowered
            assert "order" not in lowered
            assert "trade" not in lowered
            assert "recommend" not in lowered
            assert "sizing" not in lowered
            assert "live" not in lowered

    expected_public = {
        "ResearchSourceScraplingClaimConsensusTailConfig",
        "ResearchSourceScraplingClaimConsensusTailObservation",
        "ResearchSourceScraplingClaimConsensusTailRow",
        "ResearchSourceScraplingClaimConsensusTailReport",
        "build_research_source_scrapling_claim_consensus_tail_report",
        "research_source_scrapling_claim_consensus_tail_report_digest",
        "research_source_scrapling_claim_consensus_tail_report_payload",
        "validate_research_source_scrapling_claim_consensus_tail_public_payload",
    }
    assert set(module.__all__) == expected_public

    public_names = set(module.__all__)
    forbidden_public_name_fragments = {
        "client",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "recommend",
        "sizing",
        "live",
    }
    for name in public_names:
        lowered = name.lower()
        assert not any(fragment in lowered for fragment in forbidden_public_name_fragments)
