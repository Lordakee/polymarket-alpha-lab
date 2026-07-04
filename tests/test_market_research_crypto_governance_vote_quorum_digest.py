from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_args, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_research_crypto_governance_vote_quorum_digest.py"
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_governance_vote_quorum_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def before(**kwargs: int) -> datetime:
    return GENERATED_AT - timedelta(**kwargs)


def after(**kwargs: int) -> datetime:
    return GENERATED_AT + timedelta(**kwargs)


def config(**overrides: object):
    module = api()
    values = {
        "min_quorum_progress_ratio": d("0.900000"),
        "low_participation_ratio": d("0.500000"),
        "near_close_seconds": d("7200.000000"),
        "min_source_count": d("2"),
    }
    values.update(overrides)
    return module.CryptoGovernanceVoteQuorumDigestConfig(**values)


def vote_input(
    proposal_id: str = "proposal-alpha",
    *,
    protocol_id: str = "compound",
    market_slug: str = "compound-proposal-alpha-quorum",
    vote_snapshot_at: datetime | None = None,
    voting_close_at: datetime | None = None,
    votes_for: str | Decimal = "560000.000000",
    votes_against: str | Decimal = "90000.000000",
    votes_abstain: str | Decimal = "10000.000000",
    quorum_required_votes: str | Decimal = "600000.000000",
    eligible_votes: str | Decimal = "1000000.000000",
    source_count: str | Decimal = "2",
    source_labels: tuple[str, ...] = ("forum", "snapshot"),
    stale_source_count: str | Decimal = "0",
    conflicting_source_count: str | Decimal = "0",
):
    module = api()
    return module.CryptoGovernanceVoteQuorumObservation(
        proposal_id=proposal_id,
        protocol_id=protocol_id,
        market_slug=market_slug,
        vote_snapshot_at=vote_snapshot_at or before(minutes=30),
        voting_close_at=voting_close_at or after(hours=8),
        votes_for=votes_for if isinstance(votes_for, Decimal) else d(votes_for),
        votes_against=(
            votes_against if isinstance(votes_against, Decimal) else d(votes_against)
        ),
        votes_abstain=(
            votes_abstain if isinstance(votes_abstain, Decimal) else d(votes_abstain)
        ),
        quorum_required_votes=(
            quorum_required_votes
            if isinstance(quorum_required_votes, Decimal)
            else d(quorum_required_votes)
        ),
        eligible_votes=(
            eligible_votes if isinstance(eligible_votes, Decimal) else d(eligible_votes)
        ),
        source_count=source_count if isinstance(source_count, Decimal) else d(source_count),
        source_labels=source_labels,
        stale_source_count=(
            stale_source_count
            if isinstance(stale_source_count, Decimal)
            else d(stale_source_count)
        ),
        conflicting_source_count=(
            conflicting_source_count
            if isinstance(conflicting_source_count, Decimal)
            else d(conflicting_source_count)
        ),
    )


def build_digest(*rows: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_market_research_crypto_governance_vote_quorum_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_quorum_digest_reduces_rows_deterministically() -> None:
    module = api()

    report = build_digest(
        vote_input(
            "proposal-pass",
            protocol_id="aave",
            market_slug="aave-proposal-pass-quorum",
            votes_for="610000.000000",
            votes_against="20000.000000",
            votes_abstain="0.000000",
            quorum_required_votes="600000.000000",
            eligible_votes="900000.000000",
            source_labels=("snapshot", "forum", "governance"),
            source_count="3",
        ),
        vote_input(
            "proposal-watch",
            protocol_id="uniswap",
            market_slug="uniswap-proposal-watch-quorum",
            votes_for="500000.000000",
            votes_against="10000.000000",
            votes_abstain="20000.000000",
            quorum_required_votes="600000.000000",
            eligible_votes="1200000.000000",
            voting_close_at=after(hours=1),
        ),
        vote_input(
            "proposal-block",
            protocol_id="maker",
            market_slug="maker-proposal-block-quorum",
            votes_for="120000.000000",
            votes_against="30000.000000",
            votes_abstain="0.000000",
            quorum_required_votes="600000.000000",
            eligible_votes="1000000.000000",
            stale_source_count="1",
            conflicting_source_count="1",
        ),
        generated_at=datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert type(report) is module.CryptoGovernanceVoteQuorumDigestReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-crypto-governance-vote-quorum-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_governance_vote_quorum_digest"
    )
    assert report.observation_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.quorum_met_count == d("1.000000")
    assert report.quorum_gap_count == d("2.000000")
    assert report.conflicting_source_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.near_close_count == d("1.000000")
    assert report.average_quorum_progress_ratio == d("0.711111")
    assert report.max_quorum_gap_ratio == d("0.750000")
    assert report.blocked_observation_ratio == d("0.333333")
    assert report.reason_codes == (
        "governance_vote_quorum_source_conflict_present",
        "governance_vote_quorum_stale_source_present",
        "governance_vote_quorum_gap_present",
        "governance_vote_quorum_near_close_present",
    )
    assert report.reason_code_counts == (
        module.CryptoGovernanceVoteQuorumReasonCodeCount(
            reason_code="governance_vote_quorum_source_conflict_present",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        module.CryptoGovernanceVoteQuorumReasonCodeCount(
            reason_code="governance_vote_quorum_stale_source_present",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        module.CryptoGovernanceVoteQuorumReasonCodeCount(
            reason_code="governance_vote_quorum_gap_present",
            count=d("2.000000"),
            observation_ratio=d("0.666667"),
        ),
        module.CryptoGovernanceVoteQuorumReasonCodeCount(
            reason_code="governance_vote_quorum_near_close_present",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.proposal_id for row in report.quorum_rows) == (
        "proposal-block",
        "proposal-watch",
        "proposal-pass",
    )
    blocked, watched, passed = report.quorum_rows
    assert blocked.quorum_status == "blocked"
    assert blocked.total_participating_votes == d("150000.000000")
    assert blocked.quorum_progress_ratio == d("0.250000")
    assert blocked.quorum_gap_votes == d("450000.000000")
    assert blocked.quorum_gap_ratio == d("0.750000")
    assert blocked.participation_ratio == d("0.150000")
    assert blocked.hours_until_close == d("8.000000")
    assert blocked.reason_codes == (
        "governance_vote_quorum_source_conflict",
        "governance_vote_quorum_stale_source",
        "governance_vote_quorum_far_below_threshold",
        "governance_vote_quorum_participation_low",
        "governance_vote_quorum_source_coverage_met",
    )
    assert watched.quorum_status == "watch"
    assert watched.near_close is True
    assert watched.reason_codes == (
        "governance_vote_quorum_below_threshold",
        "governance_vote_quorum_near_close",
        "governance_vote_quorum_participation_low",
        "governance_vote_quorum_source_fresh",
        "governance_vote_quorum_source_consensus",
        "governance_vote_quorum_source_coverage_met",
    )
    assert passed.quorum_status == "pass"
    assert passed.quorum_met is True
    assert passed.source_labels == ("forum", "governance", "snapshot")
    assert passed.reason_codes == (
        "governance_vote_quorum_met",
        "governance_vote_quorum_source_fresh",
        "governance_vote_quorum_source_consensus",
        "governance_vote_quorum_source_coverage_met",
    )


def test_empty_digest_is_report_only_and_decimal_zeroed() -> None:
    module = api()

    report = build_digest()

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_governance_vote_quorum_digest"
    )
    assert report.observation_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.quorum_met_count == d("0.000000")
    assert report.quorum_gap_count == d("0.000000")
    assert report.average_quorum_progress_ratio == d("0.000000")
    assert report.max_quorum_gap_ratio == d("0.000000")
    assert report.blocked_observation_ratio == d("0.000000")
    assert report.quorum_rows == ()
    assert report.reason_codes == ("governance_vote_quorum_digest_empty",)
    assert report.reason_code_counts == (
        module.CryptoGovernanceVoteQuorumReasonCodeCount(
            reason_code="governance_vote_quorum_digest_empty",
            count=d("1.000000"),
            observation_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_json_payload_uses_decimal_strings_utc_strings_and_redaction() -> None:
    module = api()
    report = build_digest(
        vote_input(
            "secret-token-proposal",
            protocol_id="private-credential-protocol",
            market_slug="wallet-governance-quorum",
            source_labels=("snapshot", "api-key-source"),
        ),
    )

    payload = module.market_research_crypto_governance_vote_quorum_digest_payload(report)

    json.dumps(payload, sort_keys=True)
    assert _float_paths(payload) == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["average_quorum_progress_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["quorum_rows"][0]["proposal_id"].startswith("redacted_")
    assert payload["quorum_rows"][0]["protocol_id"].startswith("redacted_")
    assert payload["quorum_rows"][0]["market_slug"].startswith("redacted_")
    assert payload["quorum_rows"][0]["source_labels"][0].startswith("redacted_")
    rendered = json.dumps(payload, sort_keys=True).lower()
    assert "secret-token-proposal" not in rendered
    assert "private-credential-protocol" not in rendered
    assert "wallet-governance-quorum" not in rendered
    assert "api-key-source" not in rendered


def test_public_dataclasses_are_frozen_decimal_only_and_validate_values() -> None:
    module = api()
    contract_classes = (
        module.CryptoGovernanceVoteQuorumDigestConfig,
        module.CryptoGovernanceVoteQuorumObservation,
        module.CryptoGovernanceVoteQuorumDigestRow,
        module.CryptoGovernanceVoteQuorumReasonCodeCount,
        module.CryptoGovernanceVoteQuorumDigestReport,
    )
    for contract_class in contract_classes:
        assert is_dataclass(contract_class)
        assert contract_class.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract_class)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        for hint in get_type_hints(contract_class).values():
            assert not _type_uses_float(hint)

    row = vote_input("proposal-frozen")
    with pytest.raises(FrozenInstanceError):
        row.proposal_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="Decimal"):
        config(min_quorum_progress_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="positive"):
        config(min_source_count=d("0.000000"))
    with pytest.raises(ValueError, match="timezone-aware"):
        vote_input("proposal-naive", vote_snapshot_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_crypto_governance_vote_quorum_digest(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="votes_for must be a Decimal"):
        vote_input("proposal-decimal-subclass", votes_for=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="must not exceed total participating"):
        vote_input("proposal-bad-abstain", votes_abstain=d("999999.000000"))
    with pytest.raises(ValueError, match="source_labels"):
        vote_input("proposal-label-mismatch", source_count=d("2"), source_labels=("only-one",))
    with pytest.raises(ValueError, match="duplicate proposal_id"):
        build_digest(vote_input("proposal-dupe"), vote_input("proposal-dupe"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(config(), paper_only=False)

    report = build_digest(vote_input("proposal-decimals"))
    for value in _decimal_public_values(report):
        assert value is None or type(value) is Decimal


def test_static_module_surface_excludes_forbidden_terms_and_io() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live_trading",
        "wallet",
        "broker",
        "order",
        "signing",
        "advice",
        "private_key",
        "api_key",
        "secret",
        "database",
        "network",
        "requests",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def _decimal_public_values(value: object) -> tuple[object, ...]:
    found: list[object] = []
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            field_value = getattr(value, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_votes")
                or field.name.endswith("_seconds")
                or field.name.endswith("_hours")
            ):
                found.append(field_value)
            found.extend(_decimal_public_values(field_value))
        return tuple(found)
    if isinstance(value, tuple):
        for item in value:
            found.extend(_decimal_public_values(item))
    return tuple(found)


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _type_uses_float(hint: Any) -> bool:
    if hint is float:
        return True
    return any(_type_uses_float(arg) for arg in get_args(hint))
