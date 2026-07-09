from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_NAME = (
    "polymarket_alpha_lab.research_team_specialist_consensus_staleness_report"
)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object):
    module = api()
    return module.ResearchTeamSpecialistConsensusStalenessConfig(**overrides)


def snapshot(
    team_id: str,
    *,
    consensus_observed_at: datetime = datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
    evidence_refreshed_at: datetime = datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
    dissenting_specialist_count: Decimal = d("0"),
    unresolved_escalation_count: Decimal = d("0"),
    reason_codes: tuple[str, ...] = ("specialist_consensus_snapshot",),
):
    module = api()
    return module.ResearchTeamSpecialistConsensusStalenessInput(
        team_id=team_id,
        consensus_observed_at=consensus_observed_at,
        evidence_refreshed_at=evidence_refreshed_at,
        dissenting_specialist_count=dissenting_specialist_count,
        unresolved_escalation_count=unresolved_escalation_count,
        reason_codes=reason_codes,
    )


def build_report(*snapshots, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_specialist_consensus_staleness_report(
        snapshots,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_consensus_staleness_report_aggregates_by_team_and_digest_payload() -> None:
    snapshots = (
        snapshot(
            "gamma_team",
            consensus_observed_at=datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
            evidence_refreshed_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
        ),
        snapshot(
            "alpha_team",
            consensus_observed_at=datetime(2026, 7, 5, 12, 0, tzinfo=UTC),
            evidence_refreshed_at=datetime(2026, 7, 5, 12, 0, tzinfo=UTC),
            dissenting_specialist_count=d("3"),
            unresolved_escalation_count=d("2"),
            reason_codes=("manual_escalation_pending",),
        ),
        snapshot(
            "beta_team",
            consensus_observed_at=datetime(2026, 7, 7, 6, 0, tzinfo=UTC),
            evidence_refreshed_at=datetime(2026, 7, 7, 10, 0, tzinfo=UTC),
            dissenting_specialist_count=d("1"),
            reason_codes=("freshness_recheck_due",),
        ),
        snapshot(
            "beta_team",
            consensus_observed_at=datetime(2026, 7, 7, 4, 0, tzinfo=UTC),
            evidence_refreshed_at=datetime(2026, 7, 7, 8, 0, tzinfo=UTC),
            dissenting_specialist_count=d("0"),
            unresolved_escalation_count=d("1"),
            reason_codes=("second_specialist_sample",),
        ),
    )

    report = build_report(*snapshots)
    reversed_report = build_report(*reversed(snapshots))

    assert report.status == "block"
    assert report.team_count == d("3")
    assert report.block_team_count == d("1")
    assert report.watch_team_count == d("1")
    assert report.pass_team_count == d("1")
    assert report.max_last_consensus_age_seconds == d("259200.000000")
    assert report.max_evidence_refresh_age_seconds == d("259200.000000")
    assert report.total_dissent_count == d("4")
    assert report.total_unresolved_escalation_count == d("3")

    assert tuple(row.team_id for row in report.rows) == (
        "alpha_team",
        "beta_team",
        "gamma_team",
    )
    blocked, watched, passed = report.rows
    assert blocked.manual_review_urgency == "block"
    assert blocked.last_consensus_age_seconds == d("259200.000000")
    assert blocked.evidence_refresh_age_seconds == d("259200.000000")
    assert blocked.dissent_count == d("3")
    assert blocked.unresolved_escalation_count == d("2")
    assert blocked.reason_codes == (
        "manual_escalation_pending",
        "consensus_staleness_consensus_age_block",
        "consensus_staleness_evidence_refresh_block",
        "consensus_staleness_dissent_block",
        "consensus_staleness_escalation_block",
    )

    assert watched.manual_review_urgency == "watch"
    assert watched.last_consensus_age_seconds == d("108000.000000")
    assert watched.evidence_refresh_age_seconds == d("93600.000000")
    assert watched.dissent_count == d("1")
    assert watched.unresolved_escalation_count == d("1")
    assert "consensus_staleness_evidence_refresh_watch" in watched.reason_codes
    assert passed.manual_review_urgency == "pass"
    assert passed.reason_codes == (
        "specialist_consensus_snapshot",
        "consensus_staleness_clear",
    )

    payload = api().research_team_specialist_consensus_staleness_report_payload(report)
    reversed_payload = api().research_team_specialist_consensus_staleness_report_payload(
        reversed_report,
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["dissent_count"] == "3.000000"
    assert payload["rows"][0]["last_consensus_age_seconds"] == "259200.000000"
    assert _float_paths(payload) == ()
    payload_text = json.dumps(payload, sort_keys=True)
    assert "market" not in payload_text.lower()
    assert "source" not in payload_text.lower()
    json.dumps(payload, sort_keys=True)


def test_consensus_staleness_report_validates_report_only_public_shape() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SPECIALIST_CONSENSUS_STALENESS_CONFIG_VERSION",
        "STATUSES",
        "ResearchTeamSpecialistConsensusStalenessConfig",
        "ResearchTeamSpecialistConsensusStalenessInput",
        "ResearchTeamSpecialistConsensusStalenessReport",
        "ResearchTeamSpecialistConsensusStalenessRow",
        "build_research_team_specialist_consensus_staleness_report",
        "research_team_specialist_consensus_staleness_report_digest",
        "research_team_specialist_consensus_staleness_report_payload",
    )

    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen

    report = build_report(snapshot("public_team"))
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.rows[0].paper_only is True
    assert report.rows[0].report_only is True
    assert report.rows[0].readonly is True

    with pytest.raises(FrozenInstanceError):
        report.rows[0].manual_review_urgency = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="dissenting_specialist_count must be a Decimal"):
        snapshot("float_team", dissenting_specialist_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="consensus_observed_at must be UTC-aware"):
        snapshot("naive_team", consensus_observed_at=datetime(2026, 7, 8, 10, 0))
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            snapshot("zone_team"),
            generated_at=datetime(
                2026,
                7,
                8,
                12,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="evidence_refreshed_at must not exceed"):
        build_report(
            snapshot(
                "future_evidence_team",
                evidence_refreshed_at=datetime(2026, 7, 8, 13, 0, tzinfo=UTC),
            ),
        )
    with pytest.raises(ValueError, match="dissenting_specialist_count must be integral"):
        snapshot("fractional_team", dissenting_specialist_count=d("1.5"))
    with pytest.raises(ValueError, match="consensus_age_block_seconds"):
        config(
            consensus_age_watch_seconds=d("172800.000000"),
            consensus_age_block_seconds=d("86400.000000"),
        )
    with pytest.raises(ValueError, match="unsafe public payload"):
        snapshot("unsafe_team", reason_codes=("raw_market_identifier_leak",))
    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchTeamSpecialistConsensusStalenessInput(
            team_id="bad_flags",
            consensus_observed_at=datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
            evidence_refreshed_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
            dissenting_specialist_count=d("0"),
            unresolved_escalation_count=d("0"),
            reason_codes=("specialist_consensus_snapshot",),
            paper_only=False,
        )

    empty = build_report()
    assert empty.status == "pass"
    assert empty.reason_codes == ("consensus_staleness_empty",)
    assert empty.team_count == d("0")
    assert empty.rows == ()

    payload = module.research_team_specialist_consensus_staleness_report_payload(report)
    assert module.research_team_specialist_consensus_staleness_report_digest(report) == (
        payload["derived_validation_digest"]
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_consensus_staleness_report_payload(tampered)

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "private_key",
        "wallet",
        "auth",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "recommendation",
        "sizing",
    )
    for fragment in forbidden_fragments:
        assert fragment not in lowered

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
        "http",
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


def test_consensus_staleness_report_rejects_subquantum_fractional_counts() -> None:
    with pytest.raises(ValueError, match="dissenting_specialist_count must be integral"):
        snapshot(
            "fractional_team",
            dissenting_specialist_count=d("0.0000004"),
        )
    with pytest.raises(ValueError, match="team_count must be integral"):
        replace(build_report(snapshot("public_team")), team_count=d("1.0000004"))


def test_payload_revalidates_resigned_mapping_and_nested_public_values() -> None:
    module = api()
    payload = module.research_team_specialist_consensus_staleness_report_payload(
        build_report(snapshot("public_team")),
    )

    invalid_status = dict(payload)
    invalid_status["status"] = "urgent"
    invalid_status["derived_validation_digest"] = canonical_digest(invalid_status)
    with pytest.raises(ValueError, match="status"):
        module.research_team_specialist_consensus_staleness_report_payload(
            invalid_status,
        )

    extra_field = dict(payload)
    extra_field["extra_public_field"] = "unexpected"
    extra_field["derived_validation_digest"] = canonical_digest(extra_field)
    with pytest.raises(ValueError, match="fields"):
        module.research_team_specialist_consensus_staleness_report_payload(extra_field)

    invalid_row_flags = dict(payload)
    invalid_row = dict(payload["rows"][0])
    invalid_row["readonly"] = False
    invalid_row_flags["rows"] = [invalid_row]
    invalid_row_flags["derived_validation_digest"] = canonical_digest(invalid_row_flags)
    with pytest.raises(ValueError, match="readonly"):
        module.research_team_specialist_consensus_staleness_report_payload(
            invalid_row_flags,
        )

    for unsafe_reason_code in (
        "candidate_42",
        "trade_route",
        "execution_route",
        "db_name",
        "database_name",
    ):
        unsafe_payload = dict(payload)
        unsafe_row = dict(payload["rows"][0])
        unsafe_row["reason_codes"] = [unsafe_reason_code]
        unsafe_payload["rows"] = [unsafe_row]
        unsafe_payload["derived_validation_digest"] = canonical_digest(unsafe_payload)
        with pytest.raises(ValueError, match="unsafe public payload"):
            module.research_team_specialist_consensus_staleness_report_payload(
                unsafe_payload,
            )


def _float_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if isinstance(value, float):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    return ()
