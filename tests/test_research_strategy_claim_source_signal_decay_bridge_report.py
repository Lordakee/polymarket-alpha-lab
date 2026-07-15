from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal, getcontext
from hashlib import sha256
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_claim_source_signal_decay_bridge_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def redacted_ref(prefix: str, value: str) -> str:
    return f"{prefix}_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def resign_payload(payload: dict[str, object]) -> dict[str, object]:
    resigned = dict(payload)
    without_digest = {
        key: value for key, value in resigned.items() if key != "payload_sha256"
    }
    resigned["payload_sha256"] = sha256(
        json.dumps(
            without_digest,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    return resigned


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-strategy-claim-source-signal-decay-bridge-report-v0",
        "pass_bridge_signal_floor": d("0.070000"),
        "watch_bridge_signal_floor": d("0.030000"),
        "max_claim_age_hours": d("48.000000"),
        "max_source_age_hours": d("12.000000"),
        "claim_age_decay_cap": d("0.025000"),
        "source_age_decay_cap": d("0.025000"),
        "source_trust_decay_cap": d("0.020000"),
        "corroboration_decay_cap": d("0.020000"),
        "contradiction_decay_cap": d("0.050000"),
        "source_trust_watch_floor": d("0.600000"),
        "corroboration_watch_floor": d("0.500000"),
        "contradiction_watch_score": d("0.300000"),
        "contradiction_block_score": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchStrategyClaimSourceSignalDecayBridgeConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "claim_ref": "candidate-raw-alpha-market-slug-question-url-token",
        "source_ref": "https://example.test/raw-source-text?dsn=private-token",
        "claim_observed_at": GENERATED_AT - timedelta(hours=8),
        "source_observed_at": GENERATED_AT - timedelta(hours=4),
        "claim_signal_probability": d("0.130000"),
        "source_alignment_score": d("0.900000"),
        "source_trust_score": d("0.900000"),
        "corroboration_score": d("0.900000"),
        "contradiction_score": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchStrategyClaimSourceSignalDecayBridgeObservation(**values)


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_claim_source_signal_decay_bridge_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_report_bridges_claim_source_signal_decay_without_raw_public_refs() -> None:
    block_claim = "candidate-block-market-id-slug-question-token"
    block_source = "https://example.test/block-source-text?dsn=secret"
    watch_claim = "candidate-watch-market-id-slug-question-token"
    watch_source = "https://example.test/watch-source-text?dsn=secret"
    pass_claim = "candidate-pass-market-id-slug-question-token"
    pass_source = "https://example.test/pass-source-text?dsn=secret"

    bridge_report = build_report(
        observation(
            claim_ref=pass_claim,
            source_ref=pass_source,
            claim_observed_at=GENERATED_AT - timedelta(hours=8),
            source_observed_at=GENERATED_AT - timedelta(hours=4),
            claim_signal_probability=d("0.130000"),
            source_alignment_score=d("0.900000"),
            source_trust_score=d("0.900000"),
            corroboration_score=d("0.900000"),
            contradiction_score=d("0.100000"),
        ),
        observation(
            claim_ref=watch_claim,
            source_ref=watch_source,
            claim_observed_at=GENERATED_AT - timedelta(hours=60),
            source_observed_at=GENERATED_AT - timedelta(hours=6),
            claim_signal_probability=d("0.120000"),
            source_alignment_score=d("0.850000"),
            source_trust_score=d("0.850000"),
            corroboration_score=d("0.850000"),
            contradiction_score=d("0.100000"),
        ),
        observation(
            claim_ref=block_claim,
            source_ref=block_source,
            claim_observed_at=GENERATED_AT - timedelta(hours=20),
            source_observed_at=GENERATED_AT - timedelta(hours=18),
            claim_signal_probability=d("0.090000"),
            source_alignment_score=d("0.700000"),
            source_trust_score=d("0.450000"),
            corroboration_score=d("0.350000"),
            contradiction_score=d("0.800000"),
        ),
    )

    assert is_dataclass(bridge_report)
    assert bridge_report.generated_at == GENERATED_AT
    assert bridge_report.observation_count == d("3")
    assert bridge_report.pass_count == d("1")
    assert bridge_report.watch_count == d("1")
    assert bridge_report.block_count == d("1")
    assert bridge_report.surviving_bridge_count == d("1")
    assert bridge_report.mean_decayed_bridge_signal_probability == d("0.037528")
    assert bridge_report.min_decayed_bridge_signal_probability == d("-0.036417")
    assert bridge_report.status == "block"
    assert bridge_report.reason_codes == (
        "claim_source_signal_bridge_block",
        "claim_source_signal_bridge_watch",
        "claim_age_decay_watch",
        "source_age_decay_watch",
        "source_trust_watch",
        "corroboration_watch",
        "contradiction_block",
    )
    assert bridge_report.paper_only is True
    assert bridge_report.report_only is True
    assert bridge_report.readonly is True

    blocked, watched, passing = bridge_report.rows
    assert blocked.redacted_claim_ref == redacted_ref("claim_ref", block_claim)
    assert blocked.redacted_source_ref == redacted_ref("source_ref", block_source)
    assert blocked.status == "block"
    assert blocked.claim_age_hours == d("20.000000")
    assert blocked.source_age_hours == d("18.000000")
    assert blocked.decayed_bridge_signal_probability == d("-0.036417")
    assert blocked.reason_codes == (
        "claim_source_signal_decayed",
        "source_age_decay_watch",
        "source_trust_watch",
        "corroboration_watch",
        "contradiction_block",
    )
    assert watched.status == "watch"
    assert watched.decayed_bridge_signal_probability == d("0.053500")
    assert watched.reason_codes == (
        "claim_source_signal_decayed",
        "claim_age_decay_watch",
    )
    assert passing.status == "pass"
    assert passing.decayed_bridge_signal_probability == d("0.095500")
    assert passing.reason_codes == ("claim_source_signal_survives",)

    payload = api().research_strategy_claim_source_signal_decay_bridge_report_payload(
        bridge_report,
    )
    public_text = json.dumps(payload, sort_keys=True).lower()
    for raw_ref in (
        block_claim,
        block_source,
        watch_claim,
        watch_source,
        pass_claim,
        pass_source,
    ):
        assert raw_ref.lower() not in public_text
    for forbidden in (
        "candidate",
        "market-id",
        "market_id",
        "market-slug",
        "question",
        "https://",
        "source-text",
        "dsn",
        "token",
        "wallet",
        "order",
        "trade",
    ):
        assert forbidden not in public_text


def test_report_serializes_deterministic_json_and_validates_sha256_digest() -> None:
    module = api()
    bridge_report = build_report(
        observation(),
        generated_at=datetime(2026, 7, 9, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.research_strategy_claim_source_signal_decay_bridge_report_payload(
        bridge_report,
    )
    canonical_json = module.research_strategy_claim_source_signal_decay_bridge_report_json(
        bridge_report,
    )
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "payload_sha256"
    }
    expected_digest = sha256(
        json.dumps(
            payload_without_digest,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()

    assert bridge_report.generated_at == GENERATED_AT
    assert json.loads(canonical_json) == payload
    assert canonical_json == (
        module.research_strategy_claim_source_signal_decay_bridge_report_json(
            bridge_report,
        )
    )
    assert payload["payload_sha256"] == expected_digest
    assert bridge_report.payload_sha256 == expected_digest
    assert payload["rows"][0]["redacted_claim_ref"] == redacted_ref(
        "claim_ref",
        "candidate-raw-alpha-market-slug-question-url-token",
    )
    assert payload["rows"][0]["redacted_source_ref"] == redacted_ref(
        "source_ref",
        "https://example.test/raw-source-text?dsn=private-token",
    )
    assert "Decimal(" not in repr(payload)
    assert "datetime" not in repr(payload).lower()
    assert all(type(value) is not float for value in _walk_payload_values(payload))
    assert all(type(value) is not int for value in _walk_payload_values(payload))

    tampered_payload = dict(payload)
    tampered_payload["status"] = "watch"
    with pytest.raises(ValueError, match="payload_sha256 does not match"):
        module.validate_research_strategy_claim_source_signal_decay_bridge_report_payload(
            tampered_payload,
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.research_strategy_claim_source_signal_decay_bridge_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "payload_sha256": "0" * 64,
                "mean_decayed_bridge_signal_probability": 0.1,
            },
        )


def test_report_validates_decimals_flags_time_statuses_and_frozen_outputs() -> None:
    module = api()
    bridge_report = build_report(observation())

    with pytest.raises(FrozenInstanceError):
        bridge_report.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="claim_signal_probability must be a Decimal"):
        observation(claim_signal_probability=0.1)

    with pytest.raises(ValueError, match="claim_signal_probability"):
        observation(claim_signal_probability=_DecimalSubclass("0.650000"))

    with pytest.raises(ValueError, match="claim_signal_probability must be finite"):
        observation(claim_signal_probability=Decimal("NaN"))

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_report(observation(), generated_at="bad")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(
            observation(),
            generated_at=datetime(2026, 7, 9, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.ResearchStrategyClaimSourceSignalDecayBridgeReport(
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
            config_version="research-strategy-claim-source-signal-decay-bridge-report-v0",
            observation_count=d("0"),
            pass_count=d("0"),
            watch_count=d("0"),
            block_count=d("0"),
            surviving_bridge_count=d("0"),
            mean_decayed_bridge_signal_probability=d("0.000000"),
            min_decayed_bridge_signal_probability=d("0.000000"),
            status="pass",
            reason_codes=("claim_source_signal_bridge_clear",),
            reason_code_counts=(),
            rows=(),
        )

    with pytest.raises(ValueError, match="watch_bridge_signal_floor must not exceed"):
        config(watch_bridge_signal_floor=d("0.080000"))

    with pytest.raises(ValueError, match="config must be paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="observation must be readonly"):
        observation(readonly=False)

    with pytest.raises(ValueError, match="status"):
        replace(bridge_report, status="review")

    with pytest.raises(ValueError, match="observation_count"):
        replace(bridge_report, observation_count=d("2"))

    with pytest.raises(ValueError, match="payload_sha256 does not match"):
        replace(bridge_report, payload_sha256="0" * 64)

    with pytest.raises(ValueError, match="claim_observed_at must not be after"):
        build_report(observation(claim_observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="source_observed_at must not be after"):
        build_report(observation(source_observed_at=GENERATED_AT + timedelta(seconds=1)))


def test_public_payload_rejects_raw_surfaces_and_module_has_no_live_surfaces() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_strategy_claim_source_signal_decay_bridge_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "market_slug": "raw-market",
            },
        )

    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_strategy_claim_source_signal_decay_bridge_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "payload_sha256": "0" * 64,
                "summary": "https://example.test/raw-question",
            },
        )

    source = Path(
        "src/polymarket_alpha_lab/"
        "research_strategy_claim_source_signal_decay_bridge_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "wallet",
        "dsn",
        "table_name",
        "submit",
        "cancel",
        "place_order",
        "position_size",
        "recommend",
        "execute_trade",
        "network",
        "requests",
        "urllib",
        "socket",
        "auth",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def test_public_dataclasses_are_frozen_slotted_final_and_exact() -> None:
    module = api()
    public_types = (
        module.ResearchStrategyClaimSourceSignalDecayBridgeConfig,
        module.ResearchStrategyClaimSourceSignalDecayBridgeObservation,
        module.ResearchStrategyClaimSourceSignalDecayBridgeRow,
        module.ResearchStrategyClaimSourceSignalDecayBridgeReport,
    )

    for public_type in public_types:
        assert "__slots__" in public_type.__dict__
        assert public_type.__dict__.get("__final__") is True
        with pytest.raises(TypeError, match="does not support subclassing"):
            type("IllegalChild", (public_type,), {})


def test_decimal_normalization_canonicalizes_signed_zero_under_foreign_context() -> None:
    module = api()
    original_context = getcontext().copy()
    try:
        getcontext().prec = 2
        report = build_report(
            observation(
                claim_signal_probability=d("-0.000000"),
                source_alignment_score=d("-0.000000"),
                source_trust_score=d("-0.000000"),
                corroboration_score=d("-0.000000"),
                contradiction_score=d("-0.000000"),
            ),
            cfg=config(
                claim_age_decay_cap=d("-0.000000"),
                source_age_decay_cap=d("-0.000000"),
                source_trust_decay_cap=d("-0.000000"),
                corroboration_decay_cap=d("-0.000000"),
                contradiction_decay_cap=d("-0.000000"),
            ),
        )
    finally:
        getcontext().prec = original_context.prec

    assert report.min_decayed_bridge_signal_probability == d("0.000000")
    assert report.min_decayed_bridge_signal_probability.is_signed() is False
    assert all(not value.is_signed() for value in (
        report.rows[0].raw_bridge_signal_probability,
        report.rows[0].decayed_bridge_signal_probability,
        report.rows[0].claim_age_decay_probability,
        report.rows[0].source_age_decay_probability,
        report.rows[0].source_trust_decay_probability,
        report.rows[0].corroboration_decay_probability,
        report.rows[0].contradiction_decay_probability,
    ))
    assert module.research_strategy_claim_source_signal_decay_bridge_report_json(
        report,
    ).count("-0.000000") == 0


def test_decimal_derivations_are_independent_of_global_precision() -> None:
    original_context = getcontext().copy()
    try:
        getcontext().prec = 64
        high_precision = build_report(
            observation(
                claim_signal_probability=d("0.123456"),
                source_alignment_score=d("0.654321"),
            ),
        )
        getcontext().prec = 2
        low_precision = build_report(
            observation(
                claim_signal_probability=d("0.123456"),
                source_alignment_score=d("0.654321"),
            ),
        )
    finally:
        getcontext().prec = original_context.prec

    assert low_precision == high_precision
    assert low_precision.rows[0].raw_bridge_signal_probability == d("0.080780")


def test_resigned_payload_requires_exact_schema_and_canonical_scalars() -> None:
    module = api()
    payload = module.research_strategy_claim_source_signal_decay_bridge_report_payload(
        build_report(observation()),
    )

    extra_top_level = resign_payload({**payload, "unexpected": "value"})
    with pytest.raises(ValueError, match="payload keys"):
        module.validate_research_strategy_claim_source_signal_decay_bridge_report_payload(
            extra_top_level,
        )

    missing_top_level = dict(payload)
    missing_top_level.pop("rows")
    with pytest.raises(ValueError, match="payload keys"):
        module.validate_research_strategy_claim_source_signal_decay_bridge_report_payload(
            resign_payload(missing_top_level),
        )

    extra_row = dict(payload)
    extra_row["rows"] = [dict(payload["rows"][0], unexpected="value")]  # type: ignore[index]
    with pytest.raises(ValueError, match="row payload keys"):
        module.validate_research_strategy_claim_source_signal_decay_bridge_report_payload(
            resign_payload(extra_row),
        )

    noncanonical_decimal = dict(payload)
    noncanonical_decimal["observation_count"] = "1.0"
    with pytest.raises(ValueError, match="observation_count"):
        module.validate_research_strategy_claim_source_signal_decay_bridge_report_payload(
            resign_payload(noncanonical_decimal),
        )

    noncanonical_datetime = dict(payload)
    noncanonical_datetime["generated_at"] = "2026-07-09T12:00:00Z"
    with pytest.raises(ValueError, match="generated_at"):
        module.validate_research_strategy_claim_source_signal_decay_bridge_report_payload(
            resign_payload(noncanonical_datetime),
        )

    with pytest.raises(ValueError, match="exact JSON containers"):
        module.research_strategy_claim_source_signal_decay_bridge_report_payload(
            {**payload, "rows": tuple(payload["rows"])},  # type: ignore[arg-type]
        )


def test_resigned_payload_revalidates_derived_rows_and_report_aggregates() -> None:
    module = api()
    report = build_report(observation())
    payload = module.research_strategy_claim_source_signal_decay_bridge_report_payload(report)

    forged_row = dict(payload)
    forged_row["rows"] = [dict(payload["rows"][0], decayed_bridge_signal_probability="0.000000")]  # type: ignore[index]
    with pytest.raises(ValueError, match="decayed_bridge_signal_probability"):
        module.validate_research_strategy_claim_source_signal_decay_bridge_report_payload(
            resign_payload(forged_row),
        )

    forged_status = replace(
        report.rows[0],
        status="block",
        reason_codes=("claim_source_signal_decayed",),
    )
    with pytest.raises(ValueError, match="status"):
        replace(report, rows=(forged_status,))

    with pytest.raises(ValueError, match="surviving_bridge_count"):
        replace(report, surviving_bridge_count=d("0"))

    forged_config = dict(payload)
    forged_config["claim_age_decay_cap"] = "0.010000"
    with pytest.raises(ValueError, match="claim_age_decay_probability|config"):
        module.validate_research_strategy_claim_source_signal_decay_bridge_report_payload(
            resign_payload(forged_config),
        )

    forged_age = dict(payload)
    forged_age["rows"] = [dict(payload["rows"][0], claim_age_hours="9.000000")]  # type: ignore[index]
    with pytest.raises(ValueError, match="claim_age_hours"):
        module.validate_research_strategy_claim_source_signal_decay_bridge_report_payload(
            resign_payload(forged_age),
        )


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
