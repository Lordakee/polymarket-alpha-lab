from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Context, Decimal, localcontext
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_domain_edge_memory_calibration_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def item(
    *,
    domain_key: str = "tennis",
    edge_memory_ref: str = (
        "candidate_id=alpha market_slug=hidden-market question: hidden"
    ),
    observed_at: datetime = GENERATED_AT - timedelta(seconds=1800),
    historical_hit_rate: str = "0.840000",
    calibration_alignment_score: str = "0.820000",
    domain_transfer_score: str = "0.790000",
    recency_score: str = "0.880000",
    sample_support_score: str = "0.760000",
    error_rate: str = "0.080000",
):
    report_api = api()
    return report_api.ResearchStrategyDomainEdgeMemoryCalibrationInput(
        domain_key=domain_key,
        edge_memory_ref=edge_memory_ref,
        observed_at=observed_at,
        historical_hit_rate=d(historical_hit_rate),
        calibration_alignment_score=d(calibration_alignment_score),
        domain_transfer_score=d(domain_transfer_score),
        recency_score=d(recency_score),
        sample_support_score=d(sample_support_score),
        error_rate=d(error_rate),
    )


def build_report(*items, generated_at: datetime = GENERATED_AT, config=None):
    report_api = api()
    return report_api.build_research_strategy_domain_edge_memory_calibration_report(
        items,
        generated_at=generated_at,
        config=config,
    )


def test_report_calibrates_domain_edge_memory_without_raw_private_refs():
    report = build_report(
        item(),
        item(
            domain_key="macro",
            edge_memory_ref="candidate_id=beta market_id=hidden source_url=https://x",
            observed_at=GENERATED_AT - timedelta(seconds=7200),
            historical_hit_rate="0.620000",
            calibration_alignment_score="0.660000",
            domain_transfer_score="0.580000",
            recency_score="0.590000",
            sample_support_score="0.620000",
            error_rate="0.260000",
        ),
        item(
            domain_key="crypto",
            edge_memory_ref="token=secret wallet=hidden order=raw trade=raw",
            observed_at=GENERATED_AT - timedelta(seconds=30000),
            historical_hit_rate="0.420000",
            calibration_alignment_score="0.500000",
            domain_transfer_score="0.430000",
            recency_score="0.350000",
            sample_support_score="0.400000",
            error_rate="0.620000",
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "research-strategy-domain-edge-memory-calibration-report-v0"
    )
    assert report.item_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.status == "block"
    assert report.average_edge_memory_calibration_score == d("0.628333")
    assert report.average_error_rate == d("0.320000")
    assert report.oldest_memory_age_seconds == d("30000.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    blocked, watched, passing = report.rows
    assert blocked.rank == d("1")
    assert blocked.domain_key == "crypto"
    assert blocked.edge_memory_digest != "token=secret wallet=hidden order=raw trade=raw"
    assert len(blocked.edge_memory_digest) == 64
    assert blocked.edge_memory_calibration_score == d("0.423300")
    assert blocked.memory_age_seconds == d("30000.000000")
    assert blocked.reason_codes == (
        "edge_memory_calibration_score_block",
        "historical_hit_rate_block",
        "calibration_alignment_score_block",
        "domain_transfer_score_block",
        "recency_score_block",
        "sample_support_score_block",
        "error_rate_block",
    )
    assert watched.reason_codes == (
        "edge_memory_calibration_score_watch",
        "historical_hit_rate_watch",
        "calibration_alignment_score_watch",
        "domain_transfer_score_watch",
        "recency_score_watch",
        "sample_support_score_watch",
        "error_rate_watch",
    )
    assert passing.reason_codes == ("domain_edge_memory_calibration_pass",)

    payload = api().research_strategy_domain_edge_memory_calibration_report_payload(
        report,
    )
    encoded = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "candidate_id",
        "candidate_slug",
        "market_id",
        "market_slug",
        "market_question",
        "question:",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "hidden-market",
        "secret",
    ):
        assert forbidden not in encoded.lower()


def test_empty_report_blocks_at_readonly_boundary():
    report = build_report()

    assert report.item_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.status == "block"
    assert report.reason_codes == ("empty_domain_edge_memory_calibration_input",)
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_public_payload_serializes_decimal_strings_and_validates_sha256_digest():
    report_api = api()
    report = build_report(item())

    payload = report_api.research_strategy_domain_edge_memory_calibration_report_payload(
        report,
    )

    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["item_count"] == "1"
    assert payload["rows"][0]["historical_hit_rate"] == "0.840000"
    assert payload["rows"][0]["memory_age_seconds"] == "1800.000000"
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert all(type(value) is not float for value in _walk(payload))
    assert all(type(value) is not int for value in _walk(payload))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_report = replace(report)
    object.__setattr__(tampered_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_api.research_strategy_domain_edge_memory_calibration_report_payload(
            tampered_report,
        )


def test_datetimes_normalize_to_utc_and_reject_invalid_time_values():
    eastern = timezone(timedelta(hours=-4))
    report = build_report(
        item(observed_at=datetime(2026, 7, 9, 7, 0, tzinfo=eastern)),
        generated_at=GENERATED_AT,
    )

    assert report.rows[0].observed_at == datetime(2026, 7, 9, 11, 0, tzinfo=UTC)
    assert report.rows[0].memory_age_seconds == d("3600.000000")

    class DateTimeSubclass(datetime):
        pass

    class NoneOffsetTz(tzinfo):
        def utcoffset(self, dt):
            return None

        def dst(self, dt):
            return None

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        item(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_report(
            item(),
            generated_at=DateTimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        item(observed_at=datetime(2026, 7, 9, 12, 0, tzinfo=NoneOffsetTz()))
    with pytest.raises(ValueError, match="observed_at must not be after"):
        build_report(item(observed_at=GENERATED_AT + timedelta(seconds=1)))


def test_validation_rejects_floats_nonfinite_decimals_flags_and_restricted_labels():
    report_api = api()

    with pytest.raises(ValueError, match="historical_hit_rate must be a Decimal"):
        report_api.ResearchStrategyDomainEdgeMemoryCalibrationInput(
            domain_key="tennis",
            edge_memory_ref="private-ref",
            observed_at=GENERATED_AT,
            historical_hit_rate=0.5,
            calibration_alignment_score=d("0.500000"),
            domain_transfer_score=d("0.500000"),
            recency_score=d("0.500000"),
            sample_support_score=d("0.500000"),
            error_rate=d("0.100000"),
        )
    with pytest.raises(ValueError, match="historical_hit_rate must be finite"):
        item(historical_hit_rate="NaN")
    with pytest.raises(ValueError, match="readonly must be True"):
        report_api.ResearchStrategyDomainEdgeMemoryCalibrationConfig(readonly=False)
    with pytest.raises(ValueError, match="pass_threshold"):
        report_api.ResearchStrategyDomainEdgeMemoryCalibrationConfig(
            pass_threshold=d("0.500000"),
            watch_threshold=d("0.600000"),
        )
    with pytest.raises(ValueError, match="restricted references"):
        item(domain_key="market_slug_raw")
    with pytest.raises(ValueError, match="edge_memory_ref"):
        item(edge_memory_ref="")


def test_public_dataclasses_are_frozen_and_decimal_types_are_strict():
    report_api = api()

    class DecimalSubclass(Decimal):
        pass

    edge_item = item()
    with pytest.raises(FrozenInstanceError):
        edge_item.historical_hit_rate = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="sample_support_score must be a Decimal"):
        report_api.ResearchStrategyDomainEdgeMemoryCalibrationInput(
            domain_key="tennis",
            edge_memory_ref="private-ref",
            observed_at=GENERATED_AT,
            historical_hit_rate=d("0.500000"),
            calibration_alignment_score=d("0.500000"),
            domain_transfer_score=d("0.500000"),
            recency_score=d("0.500000"),
            sample_support_score=DecimalSubclass("0.500000"),
            error_rate=d("0.100000"),
        )


def test_public_report_rejects_nondeterministic_row_sequence_and_reason_codes():
    report_api = api()
    report = build_report(
        item(),
        item(
            domain_key="crypto",
            edge_memory_ref="private-raw-ref",
            observed_at=GENERATED_AT - timedelta(seconds=30000),
            historical_hit_rate="0.420000",
            calibration_alignment_score="0.500000",
            domain_transfer_score="0.430000",
            recency_score="0.350000",
            sample_support_score="0.400000",
            error_rate="0.620000",
        ),
    )

    with pytest.raises(ValueError, match="rows must use deterministic sequence"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="reason_codes must use deterministic sequence"):
        report_api.ResearchStrategyDomainEdgeMemoryCalibrationRow(
            rank=d("1"),
            domain_key="macro",
            edge_memory_digest="0" * 64,
            status="watch",
            observed_at=GENERATED_AT - timedelta(seconds=7200),
            memory_age_seconds=d("7200.000000"),
            historical_hit_rate=d("0.620000"),
            calibration_alignment_score=d("0.660000"),
            domain_transfer_score=d("0.580000"),
            recency_score=d("0.590000"),
            sample_support_score=d("0.620000"),
            error_rate=d("0.260000"),
            edge_memory_calibration_score=d("0.629800"),
            reason_codes=(
                "error_rate_watch",
                "edge_memory_calibration_score_watch",
                "historical_hit_rate_watch",
                "calibration_alignment_score_watch",
                "domain_transfer_score_watch",
                "recency_score_watch",
                "sample_support_score_watch",
            ),
        )


def test_module_scope_has_no_forbidden_execution_surfaces_or_literal_float_constants():
    source_text = Path(
        "src/polymarket_alpha_lab/research_strategy_domain_edge_memory_calibration_report.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "broker",
        "signing",
        "submit",
        "cancel",
        "database",
        "open(",
        "requests",
        "http",
        "socket",
        "scrap",
        "live",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def test_public_dataclasses_are_slotted_and_reject_subclasses():
    report_api = api()
    public_types = (
        report_api.ResearchStrategyDomainEdgeMemoryCalibrationConfig,
        report_api.ResearchStrategyDomainEdgeMemoryCalibrationInput,
        report_api.ResearchStrategyDomainEdgeMemoryCalibrationRow,
        report_api.ResearchStrategyDomainEdgeMemoryCalibrationReasonCodeCount,
        report_api.ResearchStrategyDomainEdgeMemoryCalibrationReport,
    )

    for public_type in public_types:
        assert is_dataclass(public_type)
        assert hasattr(public_type, "__slots__")
        assert "__dict__" not in public_type.__dict__

    with pytest.raises(TypeError, match="may not be subclassed"):
        class SubclassedConfig(report_api.ResearchStrategyDomainEdgeMemoryCalibrationConfig):
            pass


def test_decimal_signed_zero_is_canonical_under_a_low_global_context():
    item_value = item(
        historical_hit_rate="-0.000000",
        calibration_alignment_score="-0.000000",
        domain_transfer_score="-0.000000",
        recency_score="-0.000000",
        sample_support_score="-0.000000",
        error_rate="-0.000000",
    )

    with localcontext(Context(prec=6)):
        report = build_report(item_value)

    assert str(item_value.historical_hit_rate) == "0.000000"
    assert str(report.rows[0].historical_hit_rate) == "0.000000"
    assert str(report.rows[0].error_rate) == "0.000000"
    assert str(report.average_error_rate) == "0.000000"


def test_decimal_derivations_are_independent_of_ambient_context_precision():
    expected = build_report(
        item(
            historical_hit_rate="0.123457",
            calibration_alignment_score="0.234567",
            domain_transfer_score="0.345678",
            recency_score="0.456789",
            sample_support_score="0.567891",
            error_rate="0.678912",
        ),
    )

    with localcontext(Context(prec=4)):
        constrained = build_report(
            item(
                historical_hit_rate="0.123457",
                calibration_alignment_score="0.234567",
                domain_transfer_score="0.345678",
                recency_score="0.456789",
                sample_support_score="0.567891",
                error_rate="0.678912",
            ),
        )

    assert constrained.rows[0].edge_memory_calibration_score == d("0.301985")
    assert constrained.rows[0].edge_memory_calibration_score == (
        expected.rows[0].edge_memory_calibration_score
    )


def test_build_revalidates_tampered_config_and_input_flags():
    report_api = api()
    config = report_api.ResearchStrategyDomainEdgeMemoryCalibrationConfig()
    object.__setattr__(config, "error_reserve_weight", d("0.000000"))
    with pytest.raises(ValueError, match="weights must sum to one"):
        build_report(item(), config=config)

    input_value = item()
    object.__setattr__(input_value, "readonly", False)
    with pytest.raises(ValueError, match="readonly must be True"):
        build_report(input_value)


def test_payload_validator_rejects_exact_schema_and_canonical_value_tampering():
    report_api = api()
    payload = build_report(item()).payload

    extra_key_payload = dict(payload)
    extra_key_payload["unexpected"] = "value"
    with pytest.raises(ValueError, match="canonical report payload schema"):
        report_api._validate_payload_schema(extra_key_payload)

    nested_payload = json.loads(json.dumps(payload))
    nested_payload["rows"][0]["memory_age_seconds"] = "1800.0"
    with pytest.raises(ValueError, match="canonical report payload schema"):
        report_api._validate_payload_schema(nested_payload)

    signed_zero_payload = json.loads(json.dumps(payload))
    signed_zero_payload["average_error_rate"] = "-0.000000"
    with pytest.raises(ValueError, match="canonical report payload schema"):
        report_api._validate_payload_schema(signed_zero_payload)

    missing_flag_payload = dict(payload)
    del missing_flag_payload["readonly"]
    with pytest.raises(ValueError, match="canonical report payload schema"):
        report_api._validate_payload_schema(missing_flag_payload)


def test_payload_validator_rejects_a_re_signed_derived_tamper():
    report_api = api()
    payload = json.loads(json.dumps(build_report(item()).payload))
    payload["rows"][0]["memory_age_seconds"] = "1800.000001"
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest")
    payload["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            unsigned_payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()

    with pytest.raises(ValueError, match="oldest_memory_age_seconds must match rows"):
        report_api._validate_payload_schema(payload)


def _walk(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    else:
        yield value
