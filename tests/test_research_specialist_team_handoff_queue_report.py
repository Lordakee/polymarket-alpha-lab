from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_specialist_team_handoff_queue_report import (
    DEFAULT_RESEARCH_SPECIALIST_TEAM_HANDOFF_QUEUE_REPORT_CONFIG_VERSION,
    ResearchSpecialistTeamHandoffQueueConfig,
    ResearchSpecialistTeamHandoffQueueInput,
    ResearchSpecialistTeamHandoffQueueReasonCodeCount,
    ResearchSpecialistTeamHandoffQueueReport,
    ResearchSpecialistTeamHandoffQueueRow,
    build_research_specialist_team_handoff_queue_report,
    research_specialist_team_handoff_queue_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=15)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSpecialistTeamHandoffQueueConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_SPECIALIST_TEAM_HANDOFF_QUEUE_REPORT_CONFIG_VERSION
        ),
        "min_pass_confidence_score": d("0.750000"),
        "min_watch_confidence_score": d("0.550000"),
        "min_pass_evidence_score": d("0.700000"),
        "min_watch_evidence_score": d("0.500000"),
        "max_pass_urgency_score": d("0.400000"),
        "max_watch_urgency_score": d("0.700000"),
    }
    values.update(overrides)
    return ResearchSpecialistTeamHandoffQueueConfig(**values)


def handoff(
    from_domain: str = "politics",
    to_domain: str = "crypto",
    *,
    aggregate_confidence_score: Decimal = d("0.860000"),
    aggregate_evidence_score: Decimal = d("0.800000"),
    aggregate_urgency_score: Decimal = d("0.200000"),
    domain_count: Decimal = d("2.000000"),
    observed_at: datetime = OBSERVED_AT,
    reason_codes: tuple[str, ...] = ("cross_domain_signal_ready",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSpecialistTeamHandoffQueueInput:
    return ResearchSpecialistTeamHandoffQueueInput(
        from_domain=from_domain,
        to_domain=to_domain,
        aggregate_confidence_score=aggregate_confidence_score,
        aggregate_evidence_score=aggregate_evidence_score,
        aggregate_urgency_score=aggregate_urgency_score,
        domain_count=domain_count,
        observed_at=observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchSpecialistTeamHandoffQueueInput,
    cfg: ResearchSpecialistTeamHandoffQueueConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSpecialistTeamHandoffQueueReport:
    return build_research_specialist_team_handoff_queue_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def test_handoff_queue_scores_pass_watch_and_block_statuses() -> None:
    digest = report(
        handoff(
            "politics",
            "crypto",
            aggregate_confidence_score=d("0.860000"),
            aggregate_evidence_score=d("0.800000"),
            aggregate_urgency_score=d("0.200000"),
            reason_codes=("public_cross_domain_signal_ready",),
        ),
        handoff(
            "equities",
            "gold",
            aggregate_confidence_score=d("0.650000"),
            aggregate_evidence_score=d("0.620000"),
            aggregate_urgency_score=d("0.550000"),
        ),
        handoff(
            "soccer",
            "basketball",
            aggregate_confidence_score=d("0.400000"),
            aggregate_evidence_score=d("0.450000"),
            aggregate_urgency_score=d("0.850000"),
        ),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert (
        digest.config_version
        == "research-specialist-team-handoff-queue-report-v1"
    )
    assert digest.handoff_count == d("3.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.block_count == d("1.000000")
    assert digest.min_confidence_score == d("0.400000")
    assert digest.min_evidence_score == d("0.450000")
    assert digest.max_urgency_score == d("0.850000")
    assert digest.max_domain_count == d("2.000000")
    assert digest.status == "block"
    assert digest.paper_queue_action == "paper_handoff_block"
    assert digest.reason_codes == (
        "specialist_handoff_queue_block",
        "handoff_confidence_low_block",
        "handoff_evidence_low_block",
        "handoff_urgency_high_block",
        "handoff_confidence_thin_watch",
        "handoff_evidence_thin_watch",
        "handoff_urgency_elevated_watch",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True
    assert len(digest.derived_validation_digest) == 64

    blocked, watched, passed = digest.rows
    assert tuple(row.handoff_status for row in digest.rows) == ("block", "watch", "pass")
    assert blocked.from_domain == "soccer"
    assert blocked.to_domain == "basketball"
    assert blocked.reason_codes == (
        "cross_domain_signal_ready",
        "handoff_confidence_low_block",
        "handoff_evidence_low_block",
        "handoff_urgency_high_block",
    )
    assert watched.reason_codes == (
        "cross_domain_signal_ready",
        "handoff_confidence_thin_watch",
        "handoff_evidence_thin_watch",
        "handoff_urgency_elevated_watch",
    )
    assert passed.reason_codes == (
        "public_cross_domain_signal_ready",
        "handoff_queue_clear",
    )

    assert digest.reason_code_counts[0] == (
        ResearchSpecialistTeamHandoffQueueReasonCodeCount(
            reason_code="cross_domain_signal_ready",
            count=d("2.000000"),
            handoff_ratio=d("0.666667"),
        )
    )


def test_empty_queue_is_pass_with_decimal_counts_and_flags() -> None:
    digest = report()

    assert digest.handoff_count == ZERO
    assert digest.pass_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.block_count == ZERO
    assert digest.min_confidence_score == ZERO
    assert digest.min_evidence_score == ZERO
    assert digest.max_urgency_score == ZERO
    assert digest.max_domain_count == ZERO
    assert digest.status == "pass"
    assert digest.paper_queue_action == "paper_monitor_only"
    assert digest.reason_codes == ("specialist_handoff_queue_empty",)
    assert digest.reason_code_counts == ()
    assert digest.rows == ()

    populated = report(handoff())
    for value in (digest, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(("_count", "_score", "_ratio")):
                assert type(item_value) is Decimal


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    first = report(
        handoff(
            "basketball",
            "other",
            aggregate_confidence_score=d("0.600000"),
            aggregate_evidence_score=d("0.680000"),
            aggregate_urgency_score=d("0.500000"),
            observed_at=datetime(
                2026,
                7,
                8,
                4,
                30,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        handoff("politics", "crypto"),
        generated_at=datetime(
            2026,
            7,
            8,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    second = report(
        handoff("politics", "crypto"),
        handoff(
            "basketball",
            "other",
            aggregate_confidence_score=d("0.600000"),
            aggregate_evidence_score=d("0.680000"),
            aggregate_urgency_score=d("0.500000"),
            observed_at=datetime(
                2026,
                7,
                8,
                4,
                30,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            8,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )

    payload = research_specialist_team_handoff_queue_report_payload(first)
    repeat_payload = research_specialist_team_handoff_queue_report_payload(second)

    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == repeat_payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["handoff_count"] == "2.000000"
    assert payload["rows"][0]["aggregate_urgency_score"] == "0.500000"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T11:30:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_int_or_float_values(payload)
    json.dumps(payload, sort_keys=True)

    unsafe_fragments = (
        "event",
        "market",
        "source",
        "recommendation",
        "sizing",
        "order",
        "wallet",
        "auth",
    )
    assert not any(
        fragment in key.lower()
        for key in payload_keys(payload)
        for fragment in unsafe_fragments
    )

    tampered = dict(payload)
    tampered["pass_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_specialist_team_handoff_queue_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("2.000000"))


def test_public_payload_rejects_raw_identifiers_unsafe_surface_flags_and_numbers() -> None:
    payload = research_specialist_team_handoff_queue_report_payload(report(handoff()))

    for key in (
        "event_id",
        "market_slug",
        "source_reference",
        "recommendation_id",
        "position_sizing",
        "order_id",
        "wallet_address",
        "auth_header",
        "network_url",
        "database_table",
        "persist_path",
        "write_path",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            research_specialist_team_handoff_queue_report_payload(unsafe)

    for value in (
        "event id",
        "market slug",
        "source reference",
        "wallet signer",
        "auth token",
        "order route",
        "recommendation",
    ):
        unsafe = dict(payload)
        unsafe["reason_codes"] = (value,)
        with pytest.raises(ValueError, match="unsafe public"):
            research_specialist_team_handoff_queue_report_payload(unsafe)

    numeric = dict(payload)
    numeric["handoff_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        research_specialist_team_handoff_queue_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_specialist_team_handoff_queue_report_payload(downgraded)


def test_validation_rejects_bad_domains_non_decimals_duplicates_and_time_boundaries() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        handoff(aggregate_confidence_score=0.6)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        handoff(aggregate_confidence_score=_DecimalSubclass("0.600000"))

    with pytest.raises(ValueError, match="generated_at"):
        report(handoff(), generated_at=datetime(2026, 7, 8, 12, 0))

    with pytest.raises(ValueError, match="observed_at"):
        handoff(observed_at=datetime(2026, 7, 8, 11, 45))

    with pytest.raises(ValueError, match="observed_at"):
        handoff(observed_at=_DatetimeSubclass(2026, 7, 8, 11, 45, tzinfo=UTC))

    with pytest.raises(ValueError, match="future"):
        report(handoff(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="unique"):
        report(handoff(), handoff())

    with pytest.raises(ValueError, match="domain"):
        handoff("weather", "crypto")

    with pytest.raises(ValueError, match="different"):
        handoff("crypto", "crypto")

    with pytest.raises(ValueError, match="paper_only"):
        handoff(paper_only=False)

    with pytest.raises(ValueError, match="subclass"):
        ResearchSpecialistTeamHandoffQueueConfig.__new__(
            type(
                "ConfigSubclass",
                (ResearchSpecialistTeamHandoffQueueConfig,),
                {},
            ),
        )

    frozen = handoff()
    with pytest.raises(FrozenInstanceError):
        frozen.from_domain = "gold"  # type: ignore[misc]


def test_report_constructors_reject_inconsistent_materialized_fields() -> None:
    digest = report(handoff())
    row = digest.rows[0]

    with pytest.raises(ValueError, match="handoff_status"):
        ResearchSpecialistTeamHandoffQueueRow(
            **{
                **row.__dict__,
                "handoff_status": "block",
            },
        )

    with pytest.raises(ValueError, match="status"):
        ResearchSpecialistTeamHandoffQueueReport(
            **{
                **digest.__dict__,
                "status": "block",
            },
        )


def test_module_exposes_no_network_order_wallet_db_or_persistence_surface() -> None:
    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_specialist_team_handoff_queue_report.py"
    )
    tree = ast.parse(module_path.read_text())
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
