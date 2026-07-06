from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, dataclass, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest


GENERATED_AT = datetime(
    2026,
    7,
    6,
    9,
    30,
    tzinfo=timezone(timedelta(hours=-4)),
)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_external_source_verification_route_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def source(
    packet_id: str = "packet-alpha",
    source_id: str = "official-alpha",
    *,
    source_kind: str = "official",
    source_status: str = "available",
    observed_value: str = "resolution-yes",
    checked_at: datetime | None = None,
    verification_score: str = "0.920000",
    corroborates_official: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchPacketExternalSourceVerificationRouteV2Source(
        packet_id=packet_id,
        source_id=source_id,
        source_kind=source_kind,
        source_status=source_status,
        observed_value=observed_value,
        checked_at=checked_at or GENERATED_AT - timedelta(minutes=15),
        verification_score=d(verification_score),
        corroborates_official=corroborates_official,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "minimum_official_source_count": d("1"),
        "minimum_corroborating_third_party_count": d("2"),
        "minimum_verification_score": d("0.700000"),
        "stale_after_seconds": d("86400"),
    }
    values.update(overrides)
    return module.ResearchPacketExternalSourceVerificationRouteV2Config(**values)


def report(*sources: object, generated_at: datetime = GENERATED_AT, **overrides: object):
    module = api()
    return module.build_research_packet_external_source_verification_route_v2(
        sources,
        config=config(**overrides),
        generated_at=generated_at,
    )


def test_routes_packets_by_external_source_verification_readiness() -> None:
    verification_report = report(
        source("packet-alpha", "official-alpha"),
        source(
            "packet-alpha",
            "third-party-alpha-a",
            source_kind="third_party",
            verification_score="0.810000",
        ),
        source(
            "packet-alpha",
            "third-party-alpha-b",
            source_kind="third_party",
            verification_score="0.780000",
        ),
        source(
            "packet-beta",
            "official-beta",
            verification_score="0.910000",
        ),
        source(
            "packet-gamma",
            "official-gamma",
            source_status="missing",
            verification_score="0.000000",
            corroborates_official=False,
        ),
    )

    assert is_dataclass(verification_report)
    assert verification_report.generated_at == datetime(2026, 7, 6, 13, 30, tzinfo=UTC)
    assert verification_report.source_row_count == d("5")
    assert verification_report.route_row_count == d("3")
    assert verification_report.verified_route_count == d("1")
    assert verification_report.review_route_count == d("1")
    assert verification_report.blocked_route_count == d("1")
    assert verification_report.report_status == "review_required"
    assert verification_report.reason_codes == (
        "external_source_verification_review_required",
        "external_source_verification_blocked",
    )
    assert verification_report.paper_only is True
    assert verification_report.report_only is True
    assert verification_report.readonly is True

    verified, review, blocked = verification_report.route_rows
    assert verified.packet_id == "packet-alpha"
    assert verified.verification_route == "official_priority"
    assert verified.route_status == "verified"
    assert verified.official_source_priority_applied is True
    assert verified.official_source_count == d("1")
    assert verified.third_party_source_count == d("2")
    assert verified.corroborating_third_party_count == d("2")
    assert verified.priority_rank == d("1")
    assert verified.reason_codes == (
        "official_source_priority",
        "third_party_corroborated",
    )

    assert review.packet_id == "packet-beta"
    assert review.verification_route == "corroboration_gap"
    assert review.route_status == "review_required"
    assert review.reason_codes == (
        "official_source_priority",
        "third_party_corroboration_gap",
    )

    assert blocked.packet_id == "packet-gamma"
    assert blocked.verification_route == "source_missing"
    assert blocked.route_status == "blocked"
    assert blocked.reason_codes == ("official_source_missing",)


def test_official_source_priority_survives_third_party_conflict() -> None:
    verification_report = report(
        source("packet-alpha", "official-alpha"),
        source(
            "packet-alpha",
            "third-party-alpha-a",
            source_kind="third_party",
            verification_score="0.810000",
        ),
        source(
            "packet-alpha",
            "third-party-alpha-b",
            source_kind="third_party",
            verification_score="0.830000",
        ),
        source(
            "packet-alpha",
            "third-party-alpha-c",
            source_kind="third_party",
            source_status="contradictory",
            verification_score="0.880000",
            corroborates_official=False,
        ),
    )

    row = verification_report.route_rows[0]
    assert row.verification_route == "official_priority"
    assert row.official_source_priority_applied is True
    assert row.route_status == "review_required"
    assert row.contradiction_source_count == d("1")
    assert row.reason_codes == (
        "official_source_priority",
        "third_party_corroborated",
        "source_contradiction_present",
    )


def test_third_party_corroboration_gap_routes_to_review() -> None:
    verification_report = report(
        source("packet-gap", "official-gap"),
        source(
            "packet-gap",
            "third-party-gap-a",
            source_kind="third_party",
            verification_score="0.810000",
        ),
        source(
            "packet-gap",
            "third-party-gap-b",
            source_kind="third_party",
            verification_score="0.830000",
            corroborates_official=False,
        ),
    )

    row = verification_report.route_rows[0]
    assert row.verification_route == "corroboration_gap"
    assert row.route_status == "review_required"
    assert row.third_party_source_count == d("2")
    assert row.corroborating_third_party_count == d("1")
    assert row.reason_codes == (
        "official_source_priority",
        "third_party_corroboration_gap",
        "source_contradiction_present",
    )


def test_payload_serializes_decimals_as_strings_and_revalidates_flags() -> None:
    module = api()
    verification_report = report(
        source("packet-alpha", "official-alpha"),
        source(
            "packet-alpha",
            "third-party-alpha-a",
            source_kind="third_party",
            verification_score="0.810000",
        ),
        source(
            "packet-alpha",
            "third-party-alpha-b",
            source_kind="third_party",
            verification_score="0.780000",
        ),
    )

    payload = module.research_packet_external_source_verification_route_v2_payload(
        verification_report,
    )

    assert payload["generated_at"] == "2026-07-06T13:30:00+00:00"
    assert payload["source_row_count"] == "3"
    assert payload["route_rows"][0]["max_verification_score"] == "0.920000"
    assert payload["route_rows"][0]["official_source_count"] == "1"
    assert payload["route_rows"][0]["derived_validation_digest"].startswith(
        "rpesvr-v2:",
    )
    assert payload["derived_validation_digest"] == (
        verification_report.derived_validation_digest
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not _contains_float(payload)
    json.dumps(payload, sort_keys=True)

    readonly_payload = module.research_packet_external_source_verification_route_v2_payload(
        {
            "source_row_count": d("1"),
            "route_rows": (
                {
                    "max_verification_score": d("0.750000"),
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            ),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    assert readonly_payload["source_row_count"] == "1"
    assert readonly_payload["route_rows"][0]["max_verification_score"] == "0.750000"

    with pytest.raises(ValueError, match="readonly"):
        module.research_packet_external_source_verification_route_v2_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )
    with pytest.raises(ValueError, match="float"):
        module.research_packet_external_source_verification_route_v2_payload(
            {"score": 0.75, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="Decimal"):
        module.research_packet_external_source_verification_route_v2_payload(
            {"count": 1, "paper_only": True, "report_only": True, "readonly": True},
        )


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    verification_source = source("packet-alpha", "official-alpha")
    verification_report = report(verification_source)
    row = verification_report.route_rows[0]

    for value in (
        config(),
        verification_source,
        row,
        verification_report,
    ):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        module.ResearchPacketExternalSourceVerificationRouteV2Source(
            packet_id="packet-alpha",
            source_id="official-alpha",
            source_kind="official",
            source_status="available",
            observed_value="resolution-yes",
            checked_at=GENERATED_AT,
            verification_score=d("0.920000"),
            corroborates_official=True,
            report_only=False,
        )
    with pytest.raises(ValueError, match="verification_score must be a Decimal"):
        module.ResearchPacketExternalSourceVerificationRouteV2Source(
            packet_id="packet-alpha",
            source_id="official-alpha",
            source_kind="official",
            source_status="available",
            observed_value="resolution-yes",
            checked_at=GENERATED_AT,
            verification_score=1,
            corroborates_official=True,
        )

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="minimum_verification_score"):
        config(minimum_verification_score=DerivedDecimal("0.700000"))

    with pytest.raises(ValueError, match="checked_at must be timezone-aware"):
        module.ResearchPacketExternalSourceVerificationRouteV2Source(
            packet_id="packet-alpha",
            source_id="official-alpha",
            source_kind="official",
            source_status="available",
            observed_value="resolution-yes",
            checked_at=datetime(2026, 7, 6, 13, 30),
            verification_score=d("0.920000"),
            corroborates_official=True,
        )

    class MissingOffsetTz(tzinfo):
        def utcoffset(self, dt):  # type: ignore[no-untyped-def]
            return None

        def dst(self, dt):  # type: ignore[no-untyped-def]
            return None

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            source("packet-alpha", "official-alpha"),
            generated_at=datetime(2026, 7, 6, 13, 30, tzinfo=MissingOffsetTz()),
        )


def test_derived_validation_digest_rejects_tampering() -> None:
    module = api()
    verification_report = report(
        source("packet-alpha", "official-alpha"),
        source(
            "packet-alpha",
            "third-party-alpha-a",
            source_kind="third_party",
            verification_score="0.810000",
        ),
        source(
            "packet-alpha",
            "third-party-alpha-b",
            source_kind="third_party",
            verification_score="0.780000",
        ),
    )
    row = verification_report.route_rows[0]

    assert row.derived_validation_digest.startswith("rpesvr-v2:")
    assert verification_report.derived_validation_digest.startswith("rpesvr-v2:")

    object.__setattr__(row, "max_verification_score", d("0.010000"))
    with pytest.raises(ValueError, match="derived_validation_digest|tamper"):
        module.research_packet_external_source_verification_route_v2_payload(
            verification_report,
        )

    count_tampered_report = report(source("packet-beta", "official-beta"))
    object.__setattr__(count_tampered_report, "route_row_count", d("0"))
    with pytest.raises(ValueError, match="derived_validation_digest|route_row_count"):
        module.research_packet_external_source_verification_route_v2_payload(
            count_tampered_report,
        )


def test_unsafe_public_keys_and_values_are_rejected() -> None:
    module = api()
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
    )

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_packet_external_source_verification_route_v2_payload(
                {
                    f"{term}_field": "redacted",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_packet_external_source_verification_route_v2_payload(
                {
                    "note": f"contains {term} surface",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )

    with pytest.raises(ValueError, match="unsafe public"):
        source(packet_id="packet-wallet")

    row = report(source("packet-alpha", "official-alpha")).route_rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=("wallet_gap",))

    class PayloadDict(dict):
        pass

    @dataclass(frozen=True)
    class ForeignPayload:
        note: str
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    for unsafe_payload in (
        {
            "nested": PayloadDict({"note": "safe"}),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "nested": ForeignPayload("safe"),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ):
        with pytest.raises(ValueError, match="unsafe payload object|plain"):
            module.research_packet_external_source_verification_route_v2_payload(
                unsafe_payload,
            )


def test_module_scope_has_no_unsafe_surfaces() -> None:
    module = api()
    source_text = inspect.getsource(module)
    tree = ast.parse(source_text)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_EXTERNAL_SOURCE_VERIFICATION_ROUTE_V2_CONFIG_VERSION",
        "SOURCE_KINDS",
        "SOURCE_STATUSES",
        "VERIFICATION_ROUTES",
        "ROUTE_STATUSES",
        "ResearchPacketExternalSourceVerificationRouteV2Config",
        "ResearchPacketExternalSourceVerificationRouteV2Source",
        "ResearchPacketExternalSourceVerificationRouteV2Row",
        "ResearchPacketExternalSourceVerificationRouteV2Report",
        "build_research_packet_external_source_verification_route_v2",
        "research_packet_external_source_verification_route_v2_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
    }
    forbidden_source_terms = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
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
        "trading",
        "broker",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
        "write_text",
        "write_bytes",
    )
    assert all(term not in source_text.lower() for term in forbidden_source_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False
