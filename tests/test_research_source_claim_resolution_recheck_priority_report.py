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
    "polymarket_alpha_lab."
    "research_source_claim_resolution_recheck_priority_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_claim_resolution_recheck_priority_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


class NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    index: int,
    *,
    claim_bucket: str = "alpha-pass",
    authority_bucket: str | None = None,
    observed_at: datetime | None = None,
    resolution_authority_checked_at: datetime | None = None,
    resolution_due_at: datetime | None = None,
    authority_match_score: Decimal = d("0.950000"),
    resolution_evidence_strength: Decimal = d("0.950000"),
    source_conflict_score: Decimal = d("0.000000"),
    revision_pressure_score: Decimal = d("0.000000"),
    unresolved_dependency_count: Decimal = d("0.000000"),
    required_dependency_count: Decimal = d("2.000000"),
    reason_codes: tuple[str, ...] = (),
) -> Any:
    module = api()
    return module.ResearchSourceClaimResolutionRecheckPriorityObservation(
        claim_bucket=claim_bucket,
        authority_bucket=authority_bucket or f"authority-{index:03d}",
        private_recheck_reference=(
            f"raw_candidate_id=CAND-{index:03d}; market_id=0xMARKET{index:03d}; "
            f"market_slug=will-alpha-{index}; market_question=Will Alpha resolve?"
        ),
        private_resolution_reference=(
            "https://authority.example.test/private?"
            f"dsn=postgres://user:pass@host/db&table=resolution_table_{index}; "
            f"token=secret-{index}; wallet=0xabc; order={index}; trade={index}"
        ),
        private_evidence_reference=(
            f"source_url=https://evidence.example.test/{index}; "
            "source_text=private resolution evidence; live feed"
        ),
        observed_at=observed_at
        if observed_at is not None
        else GENERATED_AT - timedelta(minutes=30),
        resolution_authority_checked_at=resolution_authority_checked_at
        if resolution_authority_checked_at is not None
        else GENERATED_AT - timedelta(minutes=20),
        resolution_due_at=resolution_due_at,
        authority_match_score=authority_match_score,
        resolution_evidence_strength=resolution_evidence_strength,
        source_conflict_score=source_conflict_score,
        revision_pressure_score=revision_pressure_score,
        unresolved_dependency_count=unresolved_dependency_count,
        required_dependency_count=required_dependency_count,
        reason_codes=reason_codes,
    )


def report(
    observations: tuple[Any, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
) -> Any:
    module = api()
    return module.build_research_source_claim_resolution_recheck_priority_report(
        observations,
        generated_at=generated_at,
        config=config,
    )


def test_prioritizes_resolution_rechecks_without_public_private_surfaces() -> None:
    module = api()
    built = report(
        (
            observation(
                1,
                claim_bucket="alpha-pass",
                authority_bucket="authority-pass",
            ),
            observation(
                2,
                claim_bucket="beta-watch",
                authority_bucket="authority-watch",
                resolution_authority_checked_at=GENERATED_AT - timedelta(hours=12),
                resolution_due_at=GENERATED_AT + timedelta(hours=24),
                authority_match_score=d("0.650000"),
                resolution_evidence_strength=d("0.700000"),
                source_conflict_score=d("0.400000"),
                revision_pressure_score=d("0.300000"),
                unresolved_dependency_count=d("1.000000"),
                required_dependency_count=d("4.000000"),
                reason_codes=("manual_resolution_review",),
            ),
            observation(
                3,
                claim_bucket="gamma-block",
                authority_bucket="authority-block",
                resolution_authority_checked_at=GENERATED_AT - timedelta(days=4),
                resolution_due_at=GENERATED_AT - timedelta(minutes=1),
                authority_match_score=d("0.200000"),
                resolution_evidence_strength=d("0.250000"),
                source_conflict_score=d("0.850000"),
                revision_pressure_score=d("0.900000"),
                unresolved_dependency_count=d("3.000000"),
                required_dependency_count=d("3.000000"),
                reason_codes=("late_authority_refresh",),
            ),
        ),
    )

    assert is_dataclass(built)
    assert built.status == "block"
    assert built.observation_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.authority_stale_count == d("2.000000")
    assert built.authority_mismatch_count == d("2.000000")
    assert built.evidence_gap_count == d("2.000000")
    assert built.conflict_count == d("2.000000")
    assert built.revision_pressure_count == d("1.000000")
    assert built.dependency_gap_count == d("2.000000")
    assert built.deadline_pressure_count == d("2.000000")
    assert built.average_resolution_recheck_priority_score == d("0.427536")
    assert built.max_resolution_recheck_priority_score == d("0.900000")

    block_row, watch_row, pass_row = built.rows
    assert type(block_row) is module.ResearchSourceClaimResolutionRecheckPriorityRow
    assert block_row.claim_bucket == "gamma-block"
    assert block_row.status == "block"
    assert block_row.authority_age_seconds == d("345600.000000")
    assert block_row.authority_staleness_score == d("1.000000")
    assert block_row.authority_mismatch_score == d("0.800000")
    assert block_row.evidence_gap_score == d("0.750000")
    assert block_row.dependency_gap_score == d("1.000000")
    assert block_row.deadline_pressure_score == d("1.000000")
    assert block_row.resolution_recheck_priority_score == d("0.900000")
    assert block_row.reason_codes == (
        "authority_mismatch_block",
        "authority_staleness_block",
        "dependency_gap_block",
        "evidence_gap_block",
        "input_late_authority_refresh",
        "resolution_deadline_pressure_block",
        "resolution_recheck_priority_block",
        "source_conflict_block",
        "source_revision_pressure_block",
    )

    assert watch_row.claim_bucket == "beta-watch"
    assert watch_row.status == "watch"
    assert watch_row.authority_age_seconds == d("43200.000000")
    assert watch_row.authority_staleness_score == d("0.478261")
    assert watch_row.authority_mismatch_score == d("0.350000")
    assert watch_row.evidence_gap_score == d("0.300000")
    assert watch_row.dependency_gap_score == d("0.250000")
    assert watch_row.deadline_pressure_score == d("0.500000")
    assert watch_row.resolution_recheck_priority_score == d("0.368323")
    assert "input_manual_resolution_review" in watch_row.reason_codes

    assert pass_row.claim_bucket == "alpha-pass"
    assert pass_row.status == "pass"
    assert pass_row.resolution_recheck_priority_score == d("0.014286")
    assert pass_row.reason_codes == (
        "authority_mismatch_clear",
        "authority_staleness_clear",
        "dependency_gap_clear",
        "evidence_gap_clear",
        "resolution_deadline_pressure_clear",
        "resolution_recheck_priority_pass",
        "source_conflict_clear",
        "source_revision_pressure_clear",
    )

    payload = module.research_source_claim_resolution_recheck_priority_report_payload(
        built,
    )
    encoded = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "raw_candidate_id",
        "cand-001",
        "market_id",
        "market_slug",
        "market_question",
        "will alpha resolve",
        "https://authority.example.test",
        "https://evidence.example.test",
        "source_url",
        "source_text",
        "dsn=postgres",
        "resolution_table",
        "token=secret",
        "wallet=0xabc",
        "order=1",
        "trade=1",
        "live feed",
        "private_recheck_reference",
        "private_resolution_reference",
        "private_evidence_reference",
    ):
        assert forbidden not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))


def test_payload_is_deterministic_json_ready_and_digest_validated() -> None:
    module = api()
    first = report(
        (
            observation(
                2,
                claim_bucket="beta-watch",
                resolution_authority_checked_at=GENERATED_AT - timedelta(hours=8),
                source_conflict_score=d("0.400000"),
            ),
            observation(1, claim_bucket="alpha-pass"),
        ),
    )
    second = report(
        (
            observation(1, claim_bucket="alpha-pass"),
            observation(
                2,
                claim_bucket="beta-watch",
                resolution_authority_checked_at=GENERATED_AT - timedelta(hours=8),
                source_conflict_score=d("0.400000"),
            ),
        ),
    )

    payload = module.research_source_claim_resolution_recheck_priority_report_payload(
        first,
    )
    second_payload = module.research_source_claim_resolution_recheck_priority_report_payload(
        second,
    )
    unsigned_payload = dict(payload)
    digest = unsigned_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )

    assert payload == second_payload
    assert json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert module.research_source_claim_resolution_recheck_priority_report_digest(
        first,
    ) == first.derived_validation_digest
    assert digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert module.validate_research_source_claim_resolution_recheck_priority_public_payload(
        payload,
    )
    assert module.research_source_claim_resolution_recheck_priority_report_payload(
        payload,
    ) == payload

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    report_values = dict(first.__dict__)
    report_values["authority_stale_count"] = d("0.000000")
    report_values["derived_validation_digest"] = ""
    with pytest.raises(ValueError, match="authority_stale_count"):
        module.ResearchSourceClaimResolutionRecheckPriorityReport(**report_values)

    semantic_tamper_payload = dict(payload)
    semantic_tamper_payload["authority_stale_count"] = "0.000000"
    semantic_unsigned_payload = dict(semantic_tamper_payload)
    semantic_unsigned_payload.pop("derived_validation_digest")
    semantic_tamper_payload["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            semantic_unsigned_payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    with pytest.raises(ValueError, match="authority_stale_count"):
        module.research_source_claim_resolution_recheck_priority_report_payload(
            semantic_tamper_payload,
        )
    assert not module.validate_research_source_claim_resolution_recheck_priority_public_payload(
        semantic_tamper_payload,
    )

    tampered_payload = dict(payload)
    tampered_payload["average_resolution_recheck_priority_score"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_claim_resolution_recheck_priority_report_payload(
            tampered_payload,
        )
    assert not module.validate_research_source_claim_resolution_recheck_priority_public_payload(
        tampered_payload,
    )


def test_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    module = api()
    built = report((observation(1),))

    public_classes = (
        module.ResearchSourceClaimResolutionRecheckPriorityConfig,
        module.ResearchSourceClaimResolutionRecheckPriorityObservation,
        module.ResearchSourceClaimResolutionRecheckPriorityRow,
        module.ResearchSourceClaimResolutionRecheckPriorityReport,
    )
    for public_class in public_classes:
        assert is_dataclass(public_class)
        assert public_class.__dataclass_params__.frozen is True

    for instance in (module.ResearchSourceClaimResolutionRecheckPriorityConfig(), observation(1), built, *built.rows):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert not isinstance(value, float)

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadReport(module.ResearchSourceClaimResolutionRecheckPriorityReport):
            pass

    with pytest.raises(ValueError, match="authority_match_score"):
        observation(1, authority_match_score=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unresolved_dependency_count"):
        observation(1, unresolved_dependency_count=DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="whole"):
        observation(1, unresolved_dependency_count=d("1.500000"))
    with pytest.raises(ValueError, match="required_dependency_count"):
        observation(
            1,
            unresolved_dependency_count=d("3.000000"),
            required_dependency_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(module.ResearchSourceClaimResolutionRecheckPriorityConfig(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(observation(1), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report((observation(1),), generated_at=DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        observation(1, observed_at=datetime(2026, 7, 8, 11, 30))
    with pytest.raises(ValueError, match="utcoffset"):
        observation(
            1,
            observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report((observation(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="resolution_authority_checked_at"):
        report(
            (
                observation(
                    1,
                    resolution_authority_checked_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="unsafe"):
        observation(1, claim_bucket="market_slug")
    with pytest.raises(ValueError, match="unsafe"):
        unsafe_payload = dict(
            module.research_source_claim_resolution_recheck_priority_report_payload(built),
        )
        unsafe_payload["wallet_surface"] = "redacted"
        module.research_source_claim_resolution_recheck_priority_report_payload(
            unsafe_payload,
        )


def test_empty_report_and_public_api_are_report_only_safe() -> None:
    module = api()
    empty = report(())

    assert module.RESOLUTION_RECHECK_PRIORITY_STATUSES == ("pass", "watch", "block")
    assert empty.status == "pass"
    assert empty.observation_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("resolution_recheck_priority_empty",)
    assert module.validate_research_source_claim_resolution_recheck_priority_public_payload(
        empty.payload,
    )

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_CLAIM_RESOLUTION_RECHECK_PRIORITY_REPORT_CONFIG_VERSION",
        "RESOLUTION_RECHECK_PRIORITY_STATUSES",
        "ResearchSourceClaimResolutionRecheckPriorityConfig",
        "ResearchSourceClaimResolutionRecheckPriorityObservation",
        "ResearchSourceClaimResolutionRecheckPriorityReport",
        "ResearchSourceClaimResolutionRecheckPriorityRow",
        "build_research_source_claim_resolution_recheck_priority_report",
        "research_source_claim_resolution_recheck_priority_report_digest",
        "research_source_claim_resolution_recheck_priority_report_payload",
        "validate_research_source_claim_resolution_recheck_priority_public_payload",
    )

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
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "scrapling",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)

    lowered_source = MODULE_PATH.read_text(encoding="utf-8").lower()
    for forbidden_call in (
        "open(",
        "connect(",
        "request(",
        "post(",
        "get(",
        "send(",
        "submit(",
        "cancel(",
        "replace_order(",
    ):
        assert forbidden_call not in lowered_source


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
