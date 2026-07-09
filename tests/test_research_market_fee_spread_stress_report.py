from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_market_fee_spread_stress_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_fee_spread_stress_report",
    )


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "research-market-fee-spread-stress-report-v1",
        "max_book_age_seconds": Decimal("120.000000"),
        "watch_stress_score_threshold": Decimal("0.350000"),
        "blocked_stress_score_threshold": Decimal("0.650000"),
        "high_taker_fee_bps": Decimal("50.000000"),
        "wide_spread_width_bps": Decimal("300.000000"),
        "watch_taker_fee_bps": Decimal("20.000000"),
        "watch_spread_width_bps": Decimal("100.000000"),
        "watch_depth_concentration": Decimal("0.500000"),
        "watch_settlement_uncertainty": Decimal("0.400000"),
    }
    values.update(overrides)
    return module.MarketFeeSpreadStressConfig(**values)


def observation(
    raw_candidate_id: str = "candidate-blocked",
    *,
    raw_market_reference: str = "market-123/will-this-question-resolve",
    raw_source_reference: str = "https://example.test/book?token=secret",
    book_observed_at: datetime = GENERATED_AT - timedelta(seconds=30),
    taker_fee_bps: Decimal = Decimal("40.000000"),
    spread_width_bps: Decimal = Decimal("240.000000"),
    depth_concentration: Decimal = Decimal("0.850000"),
    settlement_uncertainty: Decimal = Decimal("0.600000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketFeeSpreadStressObservation(
        raw_candidate_id=raw_candidate_id,
        raw_market_reference=raw_market_reference,
        raw_source_reference=raw_source_reference,
        book_observed_at=book_observed_at,
        taker_fee_bps=taker_fee_bps,
        spread_width_bps=spread_width_bps,
        depth_concentration=depth_concentration,
        settlement_uncertainty=settlement_uncertainty,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    observations: tuple[Any, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    cfg: object | None = None,
) -> Any:
    module = api()
    return module.build_research_market_fee_spread_stress_report(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def candidate_digest(raw_candidate_id: str) -> str:
    return hashlib.sha256(raw_candidate_id.encode("utf-8")).hexdigest()


def public_payload_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def test_builds_fee_spread_stress_report_with_status_counts_scores_and_reasons() -> None:
    built = report(
        (
            observation("candidate-pass", taker_fee_bps=Decimal("5.000000"), spread_width_bps=Decimal("30.000000"), depth_concentration=Decimal("0.200000"), settlement_uncertainty=Decimal("0.100000"), book_observed_at=GENERATED_AT - timedelta(seconds=10)),
            observation("candidate-blocked"),
            observation("candidate-stale", taker_fee_bps=Decimal("5.000000"), spread_width_bps=Decimal("30.000000"), depth_concentration=Decimal("0.200000"), settlement_uncertainty=Decimal("0.100000"), book_observed_at=GENERATED_AT - timedelta(seconds=300)),
            observation("candidate-watch", taker_fee_bps=Decimal("20.000000"), spread_width_bps=Decimal("120.000000"), depth_concentration=Decimal("0.500000"), settlement_uncertainty=Decimal("0.200000")),
        ),
    )

    assert built.generated_at == GENERATED_AT
    assert built.generated_at.tzinfo is UTC
    assert built.input_count == Decimal("4.000000")
    assert built.row_count == Decimal("4.000000")
    assert built.blocked_count == Decimal("2.000000")
    assert built.watch_count == Decimal("1.000000")
    assert built.pass_count == Decimal("1.000000")
    assert built.stale_book_count == Decimal("1.000000")
    assert built.max_stress_score == Decimal("0.660000")
    assert built.average_stress_score == Decimal("0.356667")
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    assert [(row.candidate_digest, row.mechanics_status, row.stress_score) for row in built.rows] == [
        (candidate_digest("candidate-blocked"), "block", Decimal("0.660000")),
        (candidate_digest("candidate-stale"), "block", Decimal("0.300000")),
        (candidate_digest("candidate-watch"), "watch", Decimal("0.350000")),
        (candidate_digest("candidate-pass"), "pass", Decimal("0.116667")),
    ]

    blocked = built.rows[0]
    assert blocked.book_age_seconds == Decimal("30.000000")
    assert blocked.taker_fee_pressure == Decimal("0.800000")
    assert blocked.spread_pressure == Decimal("0.800000")
    assert blocked.staleness_pressure == Decimal("0.250000")
    assert blocked.reason_codes == (
        "fee_spread_depth_concentrated",
        "fee_spread_settlement_uncertainty_elevated",
        "fee_spread_source_fresh",
        "fee_spread_spread_width_elevated",
        "fee_spread_status_block",
        "fee_spread_taker_fee_elevated",
    )

    stale = built.rows[1]
    assert stale.book_age_seconds == Decimal("300.000000")
    assert stale.staleness_pressure == Decimal("1.000000")
    assert stale.reason_codes == (
        "fee_spread_book_stale",
        "fee_spread_status_block",
    )

    counts_by_code = {item.reason_code: item.count for item in built.reason_code_counts}
    assert counts_by_code["fee_spread_source_fresh"] == Decimal("3.000000")
    assert counts_by_code["fee_spread_status_block"] == Decimal("2.000000")
    assert built.reason_code_counts == tuple(
        sorted(built.reason_code_counts, key=lambda item: (-item.count, item.reason_code)),
    )
    assert built.reason_codes == tuple(sorted(built.reason_codes))


def test_payload_is_deterministic_decimal_string_serialized_and_digest_validated() -> None:
    module = api()
    observations = (
        observation("candidate-zeta", upstream_reason_codes=("fee_vendor_public", "fee_vendor_public")),
        observation("candidate-alpha", taker_fee_bps=Decimal("5.000000"), spread_width_bps=Decimal("30.000000"), depth_concentration=Decimal("0.200000"), settlement_uncertainty=Decimal("0.100000")),
    )

    first = module.research_market_fee_spread_stress_report_payload(report(observations))
    second = module.research_market_fee_spread_stress_report_payload(
        report(tuple(reversed(observations))),
    )

    assert first == second
    assert json.dumps(first, sort_keys=True)
    assert_no_public_float_or_int(first)
    assert not any(isinstance(value, Decimal) for value in walk_values(first))
    assert first["row_count"] == "2.000000"
    assert first["paper_only"] is True
    assert first["report_only"] is True
    assert first["readonly"] is True
    assert first["rows"][0]["candidate_digest"] == candidate_digest("candidate-zeta")
    assert first["rows"][0]["reason_codes"] == sorted(first["rows"][0]["reason_codes"])

    provided_digest = first["derived_validation_digest"]
    assert provided_digest == public_payload_digest(first)
    assert module.validate_research_market_fee_spread_stress_report_payload(first) == first

    tampered = dict(first)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_fee_spread_stress_report_payload(tampered)

    numeric_payload = dict(first)
    numeric_payload["row_count"] = 2
    numeric_payload["derived_validation_digest"] = public_payload_digest(numeric_payload)
    with pytest.raises(ValueError, match="numeric"):
        module.validate_research_market_fee_spread_stress_report_payload(numeric_payload)

    nested_flag_payload = json.loads(json.dumps(first))
    nested_flag_payload["rows"][0]["readonly"] = False
    nested_flag_payload["derived_validation_digest"] = public_payload_digest(
        nested_flag_payload,
    )
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_market_fee_spread_stress_report_payload(
            nested_flag_payload,
        )


def test_public_payload_excludes_raw_candidate_market_source_and_sensitive_text() -> None:
    module = api()
    built = report(
        (
            observation(
                raw_candidate_id="candidate-blocked-private-id",
                raw_market_reference="market-id-123/will-this-market-question-resolve",
                raw_source_reference="https://example.test/source?token=secret",
            ),
        ),
    )

    payload = module.research_market_fee_spread_stress_report_payload(built)
    rendered = repr(payload).lower()

    for forbidden in (
        "candidate-blocked-private-id",
        "market-id-123",
        "will-this-market-question-resolve",
        "https://example.test",
        "source?token",
        "secret",
        "raw_candidate_id",
        "raw_market_reference",
        "raw_source_reference",
    ):
        assert forbidden not in rendered

    for unsafe_term in (
        "raw_candidate_id",
        "raw-candidate-id",
        "source_url",
        "source-url",
        "sourceUrl",
        "source_text",
        "source-text",
        "sourceText",
        "dsn",
        "table_name",
        "table-name",
        "tableName",
        "rawCandidateId",
        "market-id",
        "marketId",
        "market-slug",
        "marketSlug",
        "api-key",
        "apiKey",
        "private-key",
        "privateKey",
        "order",
    ):
        unsafe_report = replace(built)
        object.__setattr__(
            unsafe_report,
            "reason_codes",
            ("fee_spread_status_pass", unsafe_term),
        )
        object.__setattr__(unsafe_report, "derived_validation_digest", "0" * 64)
        with pytest.raises(ValueError, match="unsafe public payload"):
            module.research_market_fee_spread_stress_report_payload(unsafe_report)


def test_payload_validation_rejects_non_public_status_values() -> None:
    module = api()
    payload = module.research_market_fee_spread_stress_report_payload(
        report((observation(),)),
    )

    top_level_status_payload = json.loads(json.dumps(payload))
    top_level_status_payload["mechanics_status"] = "blocked"
    top_level_status_payload["derived_validation_digest"] = public_payload_digest(
        top_level_status_payload,
    )
    with pytest.raises(ValueError, match="mechanics_status"):
        module.validate_research_market_fee_spread_stress_report_payload(
            top_level_status_payload,
        )

    row_status_payload = json.loads(json.dumps(payload))
    row_status_payload["rows"][0]["mechanics_status"] = "clear"
    row_status_payload["derived_validation_digest"] = public_payload_digest(
        row_status_payload,
    )
    with pytest.raises(ValueError, match="mechanics_status"):
        module.validate_research_market_fee_spread_stress_report_payload(
            row_status_payload,
        )


def test_payload_validation_rejects_raw_candidate_reference_in_digest_field() -> None:
    module = api()
    payload = module.research_market_fee_spread_stress_report_payload(
        report((observation("candidate-alpha"),)),
    )

    raw_candidate_payload = json.loads(json.dumps(payload))
    raw_candidate_payload["rows"][0]["candidate_digest"] = "candidate-alpha"
    raw_candidate_payload["derived_validation_digest"] = public_payload_digest(
        raw_candidate_payload,
    )
    with pytest.raises(ValueError, match="candidate_digest"):
        module.validate_research_market_fee_spread_stress_report_payload(
            raw_candidate_payload,
        )


def test_payload_validation_rejects_noncanonical_decimal_strings() -> None:
    module = api()
    payload = module.research_market_fee_spread_stress_report_payload(
        report((observation(),)),
    )

    noncanonical_decimal_payload = json.loads(json.dumps(payload))
    noncanonical_decimal_payload["row_count"] = "1"
    noncanonical_decimal_payload["derived_validation_digest"] = public_payload_digest(
        noncanonical_decimal_payload,
    )
    with pytest.raises(ValueError, match="row_count"):
        module.validate_research_market_fee_spread_stress_report_payload(
            noncanonical_decimal_payload,
        )


def test_custom_block_threshold_can_block_below_default_threshold() -> None:
    built = report(
        (
            observation(
                "candidate-custom-block",
                taker_fee_bps=Decimal("30.000000"),
                spread_width_bps=Decimal("90.000000"),
                depth_concentration=Decimal("0.500000"),
                settlement_uncertainty=Decimal("0.500000"),
            ),
        ),
        cfg=config(
            watch_stress_score_threshold=Decimal("0.100000"),
            blocked_stress_score_threshold=Decimal("0.400000"),
        ),
    )

    assert built.mechanics_status == "block"
    assert built.rows[0].mechanics_status == "block"
    assert built.rows[0].stress_score == Decimal("0.430000")
    assert "fee_spread_status_block" in built.rows[0].reason_codes


def test_rejects_float_inputs_naive_datetimes_subclasses_future_books_and_bad_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="taker_fee_bps"):
        observation(taker_fee_bps=Decimal("NaN"))

    with pytest.raises(ValueError, match="spread_width_bps"):
        observation(spread_width_bps=_DecimalSubclass("10.000000"))

    with pytest.raises(ValueError, match="depth_concentration"):
        observation(depth_concentration=0.7)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_book_age_seconds"):
        config(max_book_age_seconds=120)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="blocked_stress_score_threshold"):
        config(blocked_stress_score_threshold=Decimal("0.300000"))

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(book_observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        observation(book_observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="book_observed_at must not be after generated_at"):
        report((observation(book_observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        report((observation(readonly=False),))

    built = report((observation(),))
    unsafe_report = replace(built)
    object.__setattr__(unsafe_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        module.research_market_fee_spread_stress_report_payload(unsafe_report)

    with pytest.raises(ValueError, match="report"):
        module.research_market_fee_spread_stress_report_payload({"bad": "value"})


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    built = report((observation(),))

    for item in (config(), observation(), built, *built.reason_code_counts, *built.rows):
        assert is_dataclass(item)

    with pytest.raises(FrozenInstanceError):
        built.row_count = Decimal("2.000000")  # type: ignore[misc]

    public_classes = (
        module.MarketFeeSpreadStressConfig,
        module.MarketFeeSpreadStressObservation,
        module.MarketFeeSpreadStressRow,
        module.MarketFeeSpreadStressReasonCodeCount,
        module.MarketFeeSpreadStressReport,
    )
    for klass in public_classes:
        assert klass.__dataclass_params__.frozen is True
        assert all(
            field.type not in (int, float)
            for field in fields(klass)
            if field.name not in {"paper_only", "report_only", "readonly"}
        )


def test_empty_report_is_report_only_readonly_and_has_valid_digest() -> None:
    module = api()
    built = report(())
    payload = module.research_market_fee_spread_stress_report_payload(built)

    assert built.input_count == Decimal("0.000000")
    assert built.row_count == Decimal("0.000000")
    assert built.reason_codes == ("fee_spread_stress_report_empty",)
    assert built.reason_code_counts == ()
    assert built.rows == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert module.validate_research_market_fee_spread_stress_report_payload(payload) == payload


def test_module_has_no_live_trading_auth_io_or_durable_surface() -> None:
    module_path = Path(__file__).resolve().parents[1] / MODULE_PATH
    tree = ast.parse(module_path.read_text())
    source = module_path.read_text().lower()

    for token in (
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "private_key",
        "api_key",
        "requests",
        "httpx",
        "urllib",
        "urlopen",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sqlite",
        "redis",
        "os.environ",
        "getenv",
        "open(",
        "read_text",
        "write_text",
        "path(",
        "connect(",
        "execute(",
    ):
        assert token not in source

    forbidden_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls

    exported = module_path.read_text().split("__all__ = (", 1)[1].split(")", 1)[0]
    assert "build_research_market_fee_spread_stress_report" in exported
    assert "research_market_fee_spread_stress_report_payload" in exported
    assert "validate_research_market_fee_spread_stress_report_payload" in exported
