from __future__ import annotations

import hashlib
import importlib
import json
import re
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_team_authority_confidence_router_report"
)


def module():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def item(
    claim_id: str,
    team_id: str,
    *,
    standing_score: Decimal = d("0.820000"),
    confidence_score: Decimal = d("0.780000"),
    freshness_score: Decimal = d("0.900000"),
    independence_score: Decimal = d("0.760000"),
    private_trace: str = "internal-only-note",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    router = module()
    return router.ResearchStrategyTeamConfidenceRouterInput(
        claim_id=claim_id,
        team_id=team_id,
        standing_score=standing_score,
        confidence_score=confidence_score,
        freshness_score=freshness_score,
        independence_score=independence_score,
        private_trace=private_trace,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items, **overrides):
    router = module()
    values = {
        "items": items,
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return router.build_research_strategy_team_confidence_router_report(
        **values,
    )


def test_empty_input_builds_report_only_block_summary() -> None:
    report = build_report()

    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.item_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_router_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("empty_inputs",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert re.fullmatch(r"[0-9a-f]{64}", report.validation_digest)


def test_pass_watch_and_block_routes_use_decimal_metrics_only() -> None:
    report = build_report(
        item("claim-pass", "macro"),
        item(
            "claim-watch",
            "news",
            standing_score=d("0.700000"),
            confidence_score=d("0.610000"),
        ),
        item(
            "claim-block",
            "model",
            confidence_score=d("0.190000"),
        ),
    )

    assert report.status == "block"
    assert report.item_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert tuple(row.route_status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.claim_id for row in report.rows) == (
        "claim-block",
        "claim-watch",
        "claim-pass",
    )

    blocked, watched, passed = report.rows
    assert blocked.router_score == d("0.667500")
    assert blocked.reason_codes == ("confidence_below_floor",)
    assert watched.router_score == d("0.742500")
    assert watched.reason_codes == (
        "standing_watch",
        "confidence_watch",
        "router_score_watch",
    )
    assert passed.router_score == d("0.815000")
    assert passed.reason_codes == ("router_pass",)


def test_public_payload_is_deterministic_and_digest_validated() -> None:
    router = module()
    first = build_report(
        item("claim-z", "news", confidence_score=d("0.620000")),
        item("claim-a", "macro"),
    )
    second = build_report(
        item("claim-a", "macro"),
        item("claim-z", "news", confidence_score=d("0.620000")),
    )

    assert first.payload == second.payload
    assert first.validation_digest == second.validation_digest
    assert router.verify_research_strategy_team_confidence_router_payload(
        first.payload,
    )

    tampered = dict(first.payload)
    tampered["status"] = "pass"
    assert (
        router.verify_research_strategy_team_confidence_router_payload(
            tampered,
        )
        is False
    )
    with pytest.raises(ValueError, match="validation_digest"):
        replace(first, validation_digest="0" * 64)


def test_payload_verifier_enforces_exact_schema_flags_and_canonical_values() -> None:
    router = module()
    payload = build_report(item("claim-schema", "macro")).payload

    decimal_object = dict(payload)
    decimal_object["item_count"] = d("1.000000")

    datetime_object = dict(payload)
    datetime_object["generated_at"] = GENERATED_AT

    missing_flag = _deep_copy(payload)
    missing_flag.pop("readonly")

    downgraded_row_flag = _deep_copy(payload)
    downgraded_row_flag["rows"][0]["paper_only"] = False

    extra_report_field = _deep_copy(payload)
    extra_report_field["safe_extra"] = "safe"

    extra_row_field = _deep_copy(payload)
    extra_row_field["rows"][0]["safe_extra"] = "safe"

    inconsistent_status = _deep_copy(payload)
    inconsistent_status["status"] = "watch"

    inconsistent_row = _deep_copy(payload)
    inconsistent_row["rows"][0]["route_status"] = "block"

    for invalid_payload in (
        decimal_object,
        datetime_object,
        _resign(missing_flag),
        _resign(downgraded_row_flag),
        _resign(extra_report_field),
        _resign(extra_row_field),
        _resign(inconsistent_status),
        _resign(inconsistent_row),
    ):
        assert (
            router.verify_research_strategy_team_confidence_router_payload(
                invalid_payload,
            )
            is False
        )


def test_public_payload_uses_decimal_strings_and_no_private_material() -> None:
    private = (
        "postgres://raw-candidate.raw-market.invalid/source?"
        "url=https://raw.example.invalid&text=raw-dsn-table-token"
    )
    report = build_report(item("claim-private", "macro", private_trace=private))
    encoded = json.dumps(report.payload, sort_keys=True)
    lowered = encoded.lower()

    assert report.rows[0].private_reference == "<redacted-private-trace>"
    assert report.payload["item_count"] == "1.000000"
    assert report.payload["average_router_score"] == "0.815000"
    assert report.payload["rows"][0]["router_score"] == "0.815000"
    assert not any(isinstance(value, float) for value in _walk_values(report.payload))
    assert not any(type(value) is int for value in _walk_values(report.payload))
    for fragment in (
        "raw-candidate",
        "raw-market",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "postgres",
        "raw.example",
    ):
        assert fragment not in lowered
    assert private not in repr(item("claim-safe", "macro", private_trace=private))


def test_validation_rejects_bad_inputs_without_echoing_private_values() -> None:
    router = module()
    private = "token=do-not-echo"

    with pytest.raises(ValueError, match="generated_at"):
        build_report(generated_at="2026-07-09T12:00:00Z")
    with pytest.raises(ValueError, match="items"):
        router.build_research_strategy_team_confidence_router_report(
            items=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        build_report(item("claim-flags", "macro", paper_only=False))
    with pytest.raises(ValueError, match="standing_score"):
        item("claim-float", "macro", standing_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="confidence_score"):
        item("claim-int", "macro", confidence_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="duplicate"):
        build_report(item("claim-one", "macro"), item("claim-one", "macro"))
    with pytest.raises(ValueError, match="confidence_score") as exc_info:
        item(
            "claim-private-error",
            "macro",
            confidence_score=d("-0.010000"),
            private_trace=private,
        )

    assert private not in str(exc_info.value)


def test_public_identifiers_and_reason_codes_are_closed() -> None:
    router = module()
    report = build_report(item("claim-alpha", "macro"))

    with pytest.raises(ValueError, match="claim_id"):
        item("claim://unsafe", "macro")
    with pytest.raises(ValueError, match="team_id"):
        item("claim-safe", "team?unsafe")
    with pytest.raises(ValueError, match="reason_code"):
        replace(report.rows[0], reason_codes=("unknown_reason",))
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], route_status="blocked")


def test_public_dataclasses_are_frozen_and_decimal_types_are_strict() -> None:
    router = module()

    class DecimalSubclass(Decimal):
        pass

    assert router.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_TEAM_CONFIDENCE_ROUTER_CONFIG_VERSION",
        "ResearchStrategyTeamConfidenceRouterConfig",
        "ResearchStrategyTeamConfidenceRouterInput",
        "ResearchStrategyTeamConfidenceRouterReport",
        "ResearchStrategyTeamConfidenceRouterRow",
        "build_research_strategy_team_confidence_router_report",
        "verify_research_strategy_team_confidence_router_payload",
    )
    for exported_name in router.__all__:
        value = getattr(router, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(item("claim-frozen", "macro"))
    with pytest.raises(FrozenInstanceError):
        report.rows[0].route_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="item_count"):
        replace(report, item_count=DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked")


def test_module_static_forbidden_surface_terms_are_absent() -> None:
    source = module().__loader__.get_source(module().__name__)
    assert source is not None
    lowered = source.lower()

    for forbidden in (
        "db",
        "database",
        "network",
        "wallet",
        "auth",
        "order",
        "live",
        "trading",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in lowered


def _walk_values(value):
    if isinstance(value, dict):
        for item_value in value.values():
            yield from _walk_values(item_value)
    elif isinstance(value, (list, tuple)):
        for item_value in value:
            yield from _walk_values(item_value)
    else:
        yield value


def _deep_copy(payload):
    return json.loads(json.dumps(payload))


def _resign(payload):
    unsigned = dict(payload)
    unsigned.pop("validation_digest", None)
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    unsigned["validation_digest"] = hashlib.sha256(encoded).hexdigest()
    return unsigned
