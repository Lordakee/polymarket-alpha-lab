from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Context, Decimal, ROUND_DOWN, localcontext
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
        "polymarket_alpha_lab.research_strategy_specialist_claim_edge_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def redacted_claim_ref(value: str) -> str:
    return f"claim_ref_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-strategy-specialist-claim-edge-decay-report-v0",
        "pass_edge_floor": d("0.050000"),
        "watch_edge_floor": d("0.015000"),
        "max_claim_age_hours": d("36.000000"),
        "max_evidence_refresh_age_hours": d("12.000000"),
        "claim_age_decay_cap": d("0.030000"),
        "evidence_refresh_decay_cap": d("0.020000"),
        "confidence_decay_cap": d("0.020000"),
        "source_quorum_decay_cap": d("0.020000"),
        "contradiction_decay_cap": d("0.040000"),
        "specialist_confidence_watch_floor": d("0.500000"),
        "source_quorum_watch_floor": d("0.500000"),
        "contradiction_watch_score": d("0.350000"),
        "contradiction_block_score": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchStrategySpecialistClaimEdgeDecayConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "claim_ref": "candidate-raw-alpha-market-slug-question-url-token",
        "observed_at": GENERATED_AT - timedelta(hours=6),
        "specialist_probability": d("0.650000"),
        "market_probability": d("0.560000"),
        "claim_age_hours": d("6.000000"),
        "evidence_refresh_age_hours": d("3.000000"),
        "specialist_confidence_score": d("0.900000"),
        "source_quorum_score": d("0.900000"),
        "contradiction_score": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchStrategySpecialistClaimEdgeDecayObservation(**values)


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_specialist_claim_edge_decay_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def payload_with_recomputed_digest(payload: dict[str, object]) -> dict[str, object]:
    result = dict(payload)
    payload_without_digest = {
        key: value for key, value in result.items() if key != "payload_sha256"
    }
    result["payload_sha256"] = sha256(
        json.dumps(
            payload_without_digest,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    return result


def test_report_decays_specialist_claim_edges_without_raw_public_refs() -> None:
    blocked_ref = "candidate-raw-block-market-slug-question-url-token"
    watch_ref = "candidate-raw-watch-market-slug-question-url-token"
    pass_ref = "candidate-raw-pass-market-slug-question-url-token"

    decay_report = report(
        observation(
            claim_ref=pass_ref,
            specialist_probability=d("0.650000"),
            market_probability=d("0.560000"),
            claim_age_hours=d("6.000000"),
            evidence_refresh_age_hours=d("3.000000"),
            specialist_confidence_score=d("0.900000"),
            source_quorum_score=d("0.900000"),
            contradiction_score=d("0.100000"),
        ),
        observation(
            claim_ref=watch_ref,
            observed_at=GENERATED_AT - timedelta(hours=48),
            specialist_probability=d("0.630000"),
            market_probability=d("0.550000"),
            claim_age_hours=d("48.000000"),
            evidence_refresh_age_hours=d("6.000000"),
            specialist_confidence_score=d("0.850000"),
            source_quorum_score=d("0.850000"),
            contradiction_score=d("0.100000"),
        ),
        observation(
            claim_ref=blocked_ref,
            observed_at=GENERATED_AT - timedelta(hours=18),
            specialist_probability=d("0.600000"),
            market_probability=d("0.570000"),
            claim_age_hours=d("12.000000"),
            evidence_refresh_age_hours=d("18.000000"),
            specialist_confidence_score=d("0.600000"),
            source_quorum_score=d("0.400000"),
            contradiction_score=d("0.800000"),
        ),
    )

    assert is_dataclass(decay_report)
    assert decay_report.generated_at == GENERATED_AT
    assert decay_report.source_row_count == d("3")
    assert decay_report.pass_count == d("1")
    assert decay_report.watch_count == d("1")
    assert decay_report.block_count == d("1")
    assert decay_report.surviving_edge_count == d("1")
    assert decay_report.mean_decayed_edge_probability == d("0.016667")
    assert decay_report.min_decayed_edge_probability == d("-0.052000")
    assert decay_report.status == "block"
    assert decay_report.reason_codes == (
        "claim_edge_decay_block",
        "claim_edge_decay_watch",
        "claim_age_stale_watch",
        "evidence_refresh_stale_watch",
        "source_quorum_watch",
        "contradiction_block",
    )
    assert decay_report.paper_only is True
    assert decay_report.report_only is True
    assert decay_report.readonly is True

    first, second, third = decay_report.rows
    assert first.redacted_claim_ref == redacted_claim_ref(blocked_ref)
    assert first.claim_edge_status == "block"
    assert first.raw_edge_probability == d("0.030000")
    assert first.decayed_edge_probability == d("-0.052000")
    assert first.reason_codes == (
        "claim_edge_decayed",
        "evidence_refresh_stale_watch",
        "source_quorum_watch",
        "contradiction_block",
    )
    assert second.redacted_claim_ref == redacted_claim_ref(watch_ref)
    assert second.claim_edge_status == "watch"
    assert second.decayed_edge_probability == d("0.030000")
    assert second.reason_codes == (
        "claim_edge_decayed",
        "claim_age_stale_watch",
    )
    assert third.redacted_claim_ref == redacted_claim_ref(pass_ref)
    assert third.claim_edge_status == "pass"
    assert third.decayed_edge_probability == d("0.072000")
    assert third.reason_codes == ("claim_edge_survives",)

    payload = api().research_strategy_specialist_claim_edge_decay_report_payload(
        decay_report,
    )
    public_text = repr(payload).lower()
    for raw_ref in (blocked_ref, watch_ref, pass_ref):
        assert raw_ref not in public_text
    for forbidden in ("market-slug", "question", "url", "token"):
        assert forbidden not in public_text


def test_report_serializes_deterministic_json_and_validates_sha256_digest() -> None:
    module = api()
    decay_report = report(
        observation(),
        generated_at=datetime(2026, 7, 9, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.research_strategy_specialist_claim_edge_decay_report_payload(
        decay_report,
    )
    canonical_json = module.research_strategy_specialist_claim_edge_decay_report_json(
        decay_report,
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

    assert decay_report.generated_at == GENERATED_AT
    assert json.loads(canonical_json) == payload
    assert canonical_json == (
        module.research_strategy_specialist_claim_edge_decay_report_json(decay_report)
    )
    assert payload["payload_sha256"] == expected_digest
    assert decay_report.payload_sha256 == expected_digest
    assert payload["rows"][0]["redacted_claim_ref"] == redacted_claim_ref(
        "candidate-raw-alpha-market-slug-question-url-token",
    )
    assert "Decimal(" not in repr(payload)
    assert "datetime" not in repr(payload).lower()

    tampered_payload = dict(payload)
    tampered_payload["status"] = "watch"
    with pytest.raises(ValueError, match="payload_sha256 does not match"):
        module.validate_research_strategy_specialist_claim_edge_decay_report_payload(
            tampered_payload,
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.research_strategy_specialist_claim_edge_decay_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "payload_sha256": "0" * 64,
                "mean_decayed_edge_probability": 0.1,
            },
        )


def test_report_validates_decimals_flags_time_statuses_and_frozen_outputs() -> None:
    module = api()
    decay_report = report(observation())

    with pytest.raises(FrozenInstanceError):
        decay_report.rows[0].claim_edge_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="specialist_probability must be a Decimal"):
        observation(specialist_probability=0.1)

    with pytest.raises(ValueError, match="specialist_probability"):
        observation(specialist_probability=_DecimalSubclass("0.650000"))

    with pytest.raises(ValueError, match="specialist_probability must be finite"):
        observation(specialist_probability=Decimal("NaN"))

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(observation(), generated_at="bad")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            observation(),
            generated_at=datetime(2026, 7, 9, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.ResearchStrategySpecialistClaimEdgeDecayReport(
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
            config_version="research-strategy-specialist-claim-edge-decay-report-v0",
            source_row_count=d("0"),
            pass_count=d("0"),
            watch_count=d("0"),
            block_count=d("0"),
            surviving_edge_count=d("0"),
            mean_decayed_edge_probability=d("0.000000"),
            min_decayed_edge_probability=d("0.000000"),
            status="pass",
            reason_codes=("claim_edge_decay_clear",),
            reason_code_counts=(),
            rows=(),
        )

    with pytest.raises(ValueError, match="watch_edge_floor must not exceed"):
        config(watch_edge_floor=d("0.060000"))

    with pytest.raises(ValueError, match="config must be paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="observation must be readonly"):
        observation(readonly=False)

    with pytest.raises(ValueError, match="status"):
        replace(decay_report, status="review")

    with pytest.raises(ValueError, match="source_row_count"):
        replace(decay_report, source_row_count=d("2"))

    with pytest.raises(ValueError, match="surviving_edge_count"):
        replace(decay_report, surviving_edge_count=d("0"), payload_sha256="")

    with pytest.raises(ValueError, match="payload_sha256 does not match"):
        replace(decay_report, payload_sha256="0" * 64)


def test_public_payload_rejects_raw_surfaces_and_module_has_no_live_connectors() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_strategy_specialist_claim_edge_decay_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "market_slug": "raw-market",
            },
        )

    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_strategy_specialist_claim_edge_decay_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "recommendation": "watch only",
            },
        )

    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_strategy_specialist_claim_edge_decay_report_payload(
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
        "research_strategy_specialist_claim_edge_decay_report.py",
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
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def test_public_payload_rejects_recomputed_invalid_statuses_and_raw_refs() -> None:
    module = api()
    payload = module.research_strategy_specialist_claim_edge_decay_report_payload(
        report(observation()),
    )

    invalid_status_payload = payload_with_recomputed_digest(
        {**payload, "status": "review"},
    )
    with pytest.raises(ValueError, match="status"):
        module.research_strategy_specialist_claim_edge_decay_report_payload(
            invalid_status_payload,
        )

    invalid_rows = [dict(row) for row in payload["rows"]]
    invalid_rows[0]["claim_edge_status"] = "review"
    invalid_row_status_payload = payload_with_recomputed_digest(
        {**payload, "rows": invalid_rows},
    )
    with pytest.raises(ValueError, match="claim_edge_status"):
        module.research_strategy_specialist_claim_edge_decay_report_payload(
            invalid_row_status_payload,
        )

    raw_ref_rows = [dict(row) for row in payload["rows"]]
    raw_ref_rows[0]["redacted_claim_ref"] = "alpha_123"
    raw_ref_payload = payload_with_recomputed_digest({**payload, "rows": raw_ref_rows})
    with pytest.raises(ValueError, match="redacted_claim_ref"):
        module.research_strategy_specialist_claim_edge_decay_report_payload(
            raw_ref_payload,
        )


def test_public_dataclasses_are_frozen_slotted_and_final() -> None:
    module = api()

    for cls in (
        module.ResearchStrategySpecialistClaimEdgeDecayConfig,
        module.ResearchStrategySpecialistClaimEdgeDecayObservation,
        module.ResearchStrategySpecialistClaimEdgeDecayRow,
        module.ResearchStrategySpecialistClaimEdgeDecayReport,
    ):
        assert is_dataclass(cls)
        assert getattr(cls, "__final__", False) is True
        assert hasattr(cls, "__slots__")
        assert "__dict__" not in cls.__slots__
        assert "__weakref__" not in cls.__slots__


def test_quantization_canonicalizes_negative_zero() -> None:
    module = api()

    assert module._quantize_ratio(d("-0.0000004")) == d("0.000000")
    assert str(module._quantize_ratio(d("-0.0000004"))) == "0.000000"


def test_public_payload_requires_exact_report_and_row_schema() -> None:
    module = api()
    payload = module.research_strategy_specialist_claim_edge_decay_report_payload(
        report(observation()),
    )

    missing_field = dict(payload)
    del missing_field["status"]
    with pytest.raises(ValueError, match="payload fields"):
        module.validate_research_strategy_specialist_claim_edge_decay_report_payload(
            payload_with_recomputed_digest(missing_field),
        )

    unknown_field = {**payload, "unexpected": "value"}
    with pytest.raises(ValueError, match="payload fields"):
        module.validate_research_strategy_specialist_claim_edge_decay_report_payload(
            payload_with_recomputed_digest(unknown_field),
        )

    invalid_numeric_type = {**payload, "source_row_count": 1}
    with pytest.raises(ValueError, match="Decimal string"):
        module.validate_research_strategy_specialist_claim_edge_decay_report_payload(
            payload_with_recomputed_digest(invalid_numeric_type),
        )


def test_re_signed_payload_revalidates_derived_row_and_report_values() -> None:
    module = api()
    payload = module.research_strategy_specialist_claim_edge_decay_report_payload(
        report(observation()),
    )

    invalid_row = dict(payload["rows"][0])
    invalid_row["raw_edge_probability"] = "0.080000"
    with pytest.raises(ValueError, match="raw_edge_probability"):
        module.validate_research_strategy_specialist_claim_edge_decay_report_payload(
            payload_with_recomputed_digest({
                **payload,
                "rows": [invalid_row],
            }),
        )

    with pytest.raises(ValueError, match="mean_decayed_edge_probability"):
        module.validate_research_strategy_specialist_claim_edge_decay_report_payload(
            payload_with_recomputed_digest({
                **payload,
                "mean_decayed_edge_probability": "0.071999",
            }),
        )

    invalid_order = dict(payload)
    invalid_order["rows"] = [dict(payload["rows"][0]), dict(payload["rows"][0])]
    invalid_order["source_row_count"] = "2"
    with pytest.raises(ValueError, match="rows"):
        module.validate_research_strategy_specialist_claim_edge_decay_report_payload(
            payload_with_recomputed_digest(invalid_order),
        )


def test_payload_rejects_noncanonical_wire_values_and_nested_schema_drift() -> None:
    module = api()
    payload = module.research_strategy_specialist_claim_edge_decay_report_payload(
        report(observation()),
    )

    with pytest.raises(ValueError, match="canonical Decimal encoding"):
        module.validate_research_strategy_specialist_claim_edge_decay_report_payload(
            payload_with_recomputed_digest({
                **payload,
                "source_row_count": "1.000000",
            }),
        )

    with pytest.raises(ValueError, match="canonical UTC encoding"):
        module.validate_research_strategy_specialist_claim_edge_decay_report_payload(
            payload_with_recomputed_digest({
                **payload,
                "generated_at": "2026-07-09T05:00:00-07:00",
            }),
        )

    invalid_row = {**payload["rows"][0], "extra": "field"}
    with pytest.raises(ValueError, match="row fields"):
        module.validate_research_strategy_specialist_claim_edge_decay_report_payload(
            payload_with_recomputed_digest({
                **payload,
                "rows": [invalid_row],
            }),
        )

    with pytest.raises(ValueError, match="payload must be readonly"):
        module.validate_research_strategy_specialist_claim_edge_decay_report_payload(
            payload_with_recomputed_digest({
                **payload,
                "readonly": False,
            }),
        )


def test_count_quantization_uses_fixed_context_and_canonical_zero() -> None:
    module = api()

    with localcontext(Context(prec=2, rounding=ROUND_DOWN)):
        assert module._normalize_nonnegative_count(
            "count",
            d("123.000000"),
        ) == d("123")
        assert str(module._normalize_nonnegative_count("count", d("-0"))) == "0"
