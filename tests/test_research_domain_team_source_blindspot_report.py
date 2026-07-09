from __future__ import annotations

import importlib
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_team_source_blindspot_report",
    )


def snapshot(
    domain_team: str = "macro",
    source_class: str = "official",
    *,
    source_count: Decimal = Decimal("2.000000"),
    latest_source_age_seconds: Decimal = Decimal("600.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchDomainTeamSourceCoverageSnapshot(
        domain_team=domain_team,
        source_class=source_class,
        source_count=source_count,
        latest_source_age_seconds=latest_source_age_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report_from(snapshots: tuple[Any, ...]) -> Any:
    module = api()
    return module.build_research_domain_team_source_blindspot_report(
        snapshots,
        generated_at=GENERATED_AT,
        config=module.ResearchDomainTeamSourceBlindspotConfig(
            required_source_classes=("official", "primary", "context"),
            watch_dominant_source_class_share=Decimal("0.600000"),
            block_dominant_source_class_share=Decimal("0.800000"),
            watch_source_age_seconds=Decimal("3600.000000"),
            block_source_age_seconds=Decimal("86400.000000"),
        ),
    )


def assert_no_public_float_or_int(value: object) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (float, int)):
        pytest.fail(f"public numeric payload must not contain float/int: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_float_or_int(item)


def walk_keys_and_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(
            item
            for key, nested in value.items()
            for item in (key, *walk_keys_and_values(nested))
        )
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_keys_and_values(nested))
    return (value,)


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    payload["derived_validation_digest"] = hashlib.sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    return payload


def test_aggregates_domain_team_source_blindspots_without_raw_identifiers() -> None:
    module = api()
    report = report_from(
        (
            snapshot("team_pass", "official", source_count=Decimal("2.000000")),
            snapshot("team_pass", "primary", source_count=Decimal("1.000000")),
            snapshot("team_pass", "context", source_count=Decimal("1.000000")),
            snapshot("team_watch", "official", source_count=Decimal("4.000000")),
            snapshot("team_watch", "primary", source_count=Decimal("1.000000")),
            snapshot("team_watch", "context", source_count=Decimal("1.000000")),
            snapshot(
                "team_block",
                "official",
                source_count=Decimal("5.000000"),
                latest_source_age_seconds=Decimal("90000.000000"),
            ),
        ),
    )

    assert report.report_status == "block"
    assert report.domain_team_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.total_source_count == Decimal("15.000000")
    assert report.total_missing_source_class_count == Decimal("2.000000")
    assert report.total_stale_source_class_count == Decimal("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    rows_by_team = {row.domain_team: row for row in report.rows}
    assert rows_by_team["team_pass"].source_blindspot_status == "pass"
    assert rows_by_team["team_watch"].source_blindspot_status == "watch"
    assert rows_by_team["team_watch"].dominant_source_class_share == Decimal("0.666667")
    assert rows_by_team["team_watch"].reason_codes == (
        "dominant_source_class_share_watch",
        "domain_team_source_blindspot_watch",
    )
    assert rows_by_team["team_block"].source_blindspot_status == "block"
    assert rows_by_team["team_block"].missing_source_class_count == Decimal("2.000000")
    assert rows_by_team["team_block"].stale_source_class_count == Decimal("1.000000")
    assert rows_by_team["team_block"].max_source_age_seconds == Decimal("90000.000000")
    assert rows_by_team["team_block"].reason_codes == (
        "dominant_source_class_share_block",
        "source_class_age_block",
        "missing_source_class_block",
        "domain_team_source_blindspot_block",
    )

    payload = module.research_domain_team_source_blindspot_report_payload(report)
    assert_no_public_float_or_int(payload)
    json.dumps(payload, sort_keys=True, separators=(",", ":"))
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert [row["domain_team"] for row in payload["rows"]] == [
        "team_block",
        "team_pass",
        "team_watch",
    ]
    unsafe_fragments = ("source_url", "source_text", "raw_source", "market_id", "market_slug")
    public_values = walk_keys_and_values(payload)
    assert not any(
        isinstance(value, str) and fragment in value.lower()
        for value in public_values
        for fragment in unsafe_fragments
    )


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()

    for cls_name in (
        "ResearchDomainTeamSourceBlindspotConfig",
        "ResearchDomainTeamSourceCoverageSnapshot",
        "ResearchDomainTeamSourceBlindspotRow",
        "ResearchDomainTeamSourceBlindspotReport",
    ):
        cls = getattr(module, cls_name)
        assert is_dataclass(cls)
        assert getattr(cls, "__dataclass_params__").frozen is True

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        snapshot(source_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="latest_source_age_seconds must be a Decimal"):
        snapshot(latest_source_age_seconds=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_research_domain_team_source_blindspot_report(
            (snapshot(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
            config=module.ResearchDomainTeamSourceBlindspotConfig(),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        snapshot(paper_only=False)

    row = report_from((snapshot(),)).rows[0]
    with pytest.raises(FrozenInstanceError):
        row.source_blindspot_status = "watch"  # type: ignore[misc]


def test_payload_is_deterministic_and_digest_validated() -> None:
    module = api()
    snapshots = (
        snapshot("team_watch", "official", source_count=Decimal("4.000000")),
        snapshot("team_watch", "primary", source_count=Decimal("1.000000")),
        snapshot("team_watch", "context", source_count=Decimal("1.000000")),
        snapshot("team_pass", "official"),
        snapshot("team_pass", "primary", source_count=Decimal("1.000000")),
        snapshot("team_pass", "context", source_count=Decimal("1.000000")),
    )
    shifted_generated_at = datetime(
        2026,
        7,
        8,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    first_report = report_from(snapshots)
    second_report = module.build_research_domain_team_source_blindspot_report(
        tuple(reversed(snapshots)),
        generated_at=shifted_generated_at,
        config=module.ResearchDomainTeamSourceBlindspotConfig(
            required_source_classes=("official", "primary", "context"),
            watch_dominant_source_class_share=Decimal("0.600000"),
            block_dominant_source_class_share=Decimal("0.800000"),
            watch_source_age_seconds=Decimal("3600.000000"),
            block_source_age_seconds=Decimal("86400.000000"),
        ),
    )

    first_payload = module.research_domain_team_source_blindspot_report_payload(first_report)
    second_payload = module.research_domain_team_source_blindspot_report_payload(second_report)
    assert first_payload == second_payload

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first_report, total_source_count=Decimal("999.000000"))

    tampered_payload = json.loads(json.dumps(first_payload))
    tampered_payload["total_source_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_domain_team_source_blindspot_report_payload(tampered_payload)


def test_payload_validation_rejects_recomputed_digest_schema_tampering() -> None:
    module = api()
    payload = module.research_domain_team_source_blindspot_report_payload(
        report_from((snapshot(),)),
    )

    row_flag_tampered = json.loads(json.dumps(payload))
    row_flag_tampered["rows"][0]["paper_only"] = False
    resign_payload(row_flag_tampered)
    with pytest.raises(ValueError, match="paper_only"):
        module.validate_research_domain_team_source_blindspot_report_payload(
            row_flag_tampered,
        )

    extra_key_tampered = json.loads(json.dumps(payload))
    extra_key_tampered["safe_extra_code"] = "safe_code"
    resign_payload(extra_key_tampered)
    with pytest.raises(ValueError, match="public report schema"):
        module.validate_research_domain_team_source_blindspot_report_payload(
            extra_key_tampered,
        )

    decimal_string_tampered = json.loads(json.dumps(payload))
    decimal_string_tampered["total_source_count"] = "2"
    resign_payload(decimal_string_tampered)
    with pytest.raises(ValueError, match="Decimal string"):
        module.validate_research_domain_team_source_blindspot_report_payload(
            decimal_string_tampered,
        )


def test_public_surface_rejects_raw_sources_market_identifiers_and_action_terms() -> None:
    module = api()

    for unsafe_value in (
        "https://example.test/source",
        "source_url",
        "source_text",
        "raw_source",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "dsn",
        "table_name",
        "token",
        "private_key",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            snapshot(domain_team=unsafe_value)

    payload = module.research_domain_team_source_blindspot_report_payload(
        report_from((snapshot(),)),
    )
    leaked_payload = json.loads(json.dumps(payload))
    leaked_payload["market_slug"] = "private-market"
    with pytest.raises(ValueError, match="unsafe public"):
        module.validate_research_domain_team_source_blindspot_report_payload(leaked_payload)

    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
        "sizing",
        "recommendation",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
        "raw_source",
    )
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls_name in (
        "ResearchDomainTeamSourceBlindspotConfig",
        "ResearchDomainTeamSourceCoverageSnapshot",
        "ResearchDomainTeamSourceBlindspotRow",
        "ResearchDomainTeamSourceBlindspotReport",
    ):
        for field in fields(getattr(module, cls_name)):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(module, forbidden_name)
