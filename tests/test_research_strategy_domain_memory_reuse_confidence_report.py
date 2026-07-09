from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_domain_memory_reuse_confidence_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    *,
    domain_key: str = "tennis",
    memory_label: str = "memory-alpha",
    observed_at: datetime = GENERATED_AT - timedelta(seconds=1800),
    prior_hit_rate: str = "0.860000",
    evidence_similarity_score: str = "0.820000",
    transferability_score: str = "0.800000",
    contradiction_pressure: str = "0.050000",
    freshness_score: str = "0.900000",
):
    report_api = api()
    return report_api.ResearchStrategyDomainMemoryReuseConfidenceInput(
        domain_key=domain_key,
        memory_label=memory_label,
        observed_at=observed_at,
        prior_hit_rate=d(prior_hit_rate),
        evidence_similarity_score=d(evidence_similarity_score),
        transferability_score=d(transferability_score),
        contradiction_pressure=d(contradiction_pressure),
        freshness_score=d(freshness_score),
    )


def build_report(*items, generated_at: datetime = GENERATED_AT, config=None):
    report_api = api()
    return report_api.build_research_strategy_domain_memory_reuse_confidence_report(
        items,
        generated_at=generated_at,
        config=config or report_api.ResearchStrategyDomainMemoryReuseConfidenceConfig(),
    )


def payload_sha256(payload: dict[str, object]) -> str:
    digest_payload = {
        key: value
        for key, value in payload.items()
        if key != "public_payload_sha256"
    }
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def resign_payload(payload: dict[str, object]) -> None:
    payload["public_payload_sha256"] = payload_sha256(payload)


def test_report_aggregates_domain_memory_confidence_without_raw_identifiers():
    confidence_report = build_report(
        signal(),
        signal(
            domain_key="macro",
            memory_label="memory-beta",
            prior_hit_rate="0.640000",
            evidence_similarity_score="0.620000",
            transferability_score="0.570000",
            contradiction_pressure="0.320000",
            freshness_score="0.610000",
            observed_at=GENERATED_AT - timedelta(seconds=9000),
        ),
        signal(
            domain_key="crypto",
            memory_label="memory-gamma",
            prior_hit_rate="0.440000",
            evidence_similarity_score="0.500000",
            transferability_score="0.410000",
            contradiction_pressure="0.780000",
            freshness_score="0.350000",
            observed_at=GENERATED_AT - timedelta(seconds=30000),
        ),
    )

    assert is_dataclass(confidence_report)
    assert confidence_report.generated_at == GENERATED_AT
    assert confidence_report.config_version == (
        "research-strategy-domain-memory-reuse-confidence-report-v0"
    )
    assert confidence_report.signal_count == d("3")
    assert confidence_report.pass_count == d("1")
    assert confidence_report.watch_count == d("1")
    assert confidence_report.block_count == d("1")
    assert confidence_report.status == "block"
    assert confidence_report.average_reuse_confidence_score == d("0.629000")
    assert confidence_report.average_contradiction_pressure == d("0.383333")
    assert confidence_report.highest_contradiction_pressure == d("0.780000")
    assert confidence_report.oldest_memory_age_seconds == d("30000.000000")
    assert confidence_report.paper_only is True
    assert confidence_report.report_only is True
    assert confidence_report.readonly is True

    assert tuple(row.status for row in confidence_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    blocked, watched, passing = confidence_report.rows
    assert blocked.rank == d("1")
    assert blocked.domain_key == "crypto"
    assert blocked.memory_digest != "memory-gamma"
    assert len(blocked.memory_digest) == 64
    assert blocked.reuse_confidence_score == d("0.413500")
    assert blocked.memory_age_seconds == d("30000.000000")
    assert blocked.reason_codes == (
        "memory_reuse_confidence_score_block",
        "prior_hit_rate_block",
        "transferability_score_block",
        "contradiction_pressure_block",
        "freshness_score_block",
    )
    assert watched.reason_codes == (
        "memory_reuse_confidence_score_watch",
        "prior_hit_rate_watch",
        "evidence_similarity_score_watch",
        "transferability_score_watch",
        "contradiction_pressure_watch",
        "freshness_score_watch",
    )
    assert passing.reason_codes == ("memory_reuse_confidence_pass",)

    payload = api().research_strategy_domain_memory_reuse_confidence_report_payload(
        confidence_report,
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
        "memory-gamma",
    ):
        assert forbidden not in encoded.lower()


def test_empty_report_blocks_at_report_only_boundary():
    confidence_report = build_report()

    assert confidence_report.signal_count == d("0")
    assert confidence_report.pass_count == d("0")
    assert confidence_report.watch_count == d("0")
    assert confidence_report.block_count == d("0")
    assert confidence_report.status == "block"
    assert confidence_report.reason_codes == ("empty_domain_memory_reuse_confidence_inputs",)
    assert confidence_report.reason_code_counts == ()
    assert confidence_report.rows == ()
    assert confidence_report.paper_only is True
    assert confidence_report.report_only is True
    assert confidence_report.readonly is True


def test_public_payload_serializes_decimal_strings_and_validates_sha256_digest():
    report_api = api()
    confidence_report = build_report(signal())

    payload = report_api.research_strategy_domain_memory_reuse_confidence_report_payload(
        confidence_report,
    )

    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["signal_count"] == "1"
    assert payload["rows"][0]["prior_hit_rate"] == "0.860000"
    assert payload["rows"][0]["memory_age_seconds"] == "1800.000000"
    assert len(payload["public_payload_sha256"]) == 64
    assert payload["public_payload_sha256"] == confidence_report.public_payload_sha256
    assert payload["public_payload_sha256"] == payload_sha256(payload)
    assert all(type(value) is not float for value in _walk(payload))
    assert all(type(value) is not int for value in _walk(payload))

    with pytest.raises(ValueError, match="public_payload_sha256"):
        replace(confidence_report, public_payload_sha256="0" * 64)

    tampered_report = replace(confidence_report)
    object.__setattr__(tampered_report, "public_payload_sha256", "0" * 64)
    with pytest.raises(ValueError, match="public_payload_sha256"):
        report_api.research_strategy_domain_memory_reuse_confidence_report_payload(
            tampered_report,
        )


def test_public_payload_digest_is_deterministic_across_input_sequence():
    first = signal()
    second = signal(
        domain_key="macro",
        memory_label="memory-beta",
        prior_hit_rate="0.640000",
        evidence_similarity_score="0.620000",
        transferability_score="0.570000",
        contradiction_pressure="0.320000",
        freshness_score="0.610000",
        observed_at=GENERATED_AT - timedelta(seconds=9000),
    )

    forward_payload = api().research_strategy_domain_memory_reuse_confidence_report_payload(
        build_report(first, second),
    )
    reverse_payload = api().research_strategy_domain_memory_reuse_confidence_report_payload(
        build_report(second, first),
    )

    assert reverse_payload == forward_payload
    assert reverse_payload["public_payload_sha256"] == payload_sha256(reverse_payload)


def test_public_payload_validates_exact_canonical_dictionary_schema():
    report_api = api()
    payload = report_api.research_strategy_domain_memory_reuse_confidence_report_payload(
        build_report(signal()),
    )
    canonical_payload = json.loads(json.dumps(payload))

    assert (
        report_api.research_strategy_domain_memory_reuse_confidence_report_payload(
            canonical_payload,
        )
        == payload
    )

    extra_field_payload = json.loads(json.dumps(payload))
    extra_field_payload["unexpected"] = "value"
    with pytest.raises(ValueError, match="payload must contain exactly"):
        report_api.research_strategy_domain_memory_reuse_confidence_report_payload(
            extra_field_payload,
        )

    missing_row_field_payload = json.loads(json.dumps(payload))
    del missing_row_field_payload["rows"][0]["freshness_score"]
    with pytest.raises(ValueError, match=r"rows\[0\] must contain exactly"):
        report_api.research_strategy_domain_memory_reuse_confidence_report_payload(
            missing_row_field_payload,
        )

    decimal_object_payload = json.loads(json.dumps(payload))
    decimal_object_payload["signal_count"] = Decimal("1")
    with pytest.raises(ValueError, match="signal_count must be a Decimal string"):
        report_api.research_strategy_domain_memory_reuse_confidence_report_payload(
            decimal_object_payload,
        )

    noncanonical_count_payload = json.loads(json.dumps(payload))
    noncanonical_count_payload["signal_count"] = "1.000000"
    resign_payload(noncanonical_count_payload)
    with pytest.raises(ValueError, match="signal_count must be a canonical whole Decimal"):
        report_api.research_strategy_domain_memory_reuse_confidence_report_payload(
            noncanonical_count_payload,
        )

    inconsistent_payload = json.loads(json.dumps(payload))
    inconsistent_payload["signal_count"] = "2"
    resign_payload(inconsistent_payload)
    with pytest.raises(ValueError, match="signal_count must match rows"):
        report_api.research_strategy_domain_memory_reuse_confidence_report_payload(
            inconsistent_payload,
        )


def test_datetimes_normalize_to_utc_and_reject_invalid_time_values():
    eastern = timezone(timedelta(hours=-4))
    confidence_report = build_report(
        signal(observed_at=datetime(2026, 7, 9, 7, 0, tzinfo=eastern)),
        generated_at=GENERATED_AT,
    )

    assert confidence_report.rows[0].observed_at == datetime(
        2026,
        7,
        9,
        11,
        0,
        tzinfo=UTC,
    )
    assert confidence_report.rows[0].memory_age_seconds == d("3600.000000")

    class DateTimeSubclass(datetime):
        pass

    class NoneOffsetTz(tzinfo):
        def utcoffset(self, dt):
            return None

        def dst(self, dt):
            return None

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_report(
            signal(),
            generated_at=DateTimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 9, 12, 0, tzinfo=NoneOffsetTz()))
    with pytest.raises(ValueError, match="observed_at must not be after"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))


def test_validation_rejects_floats_nonfinite_decimals_flags_and_restricted_labels():
    report_api = api()

    with pytest.raises(ValueError, match="prior_hit_rate must be a Decimal"):
        report_api.ResearchStrategyDomainMemoryReuseConfidenceInput(
            domain_key="tennis",
            memory_label="memory-alpha",
            observed_at=GENERATED_AT,
            prior_hit_rate=0.5,
            evidence_similarity_score=d("0.500000"),
            transferability_score=d("0.500000"),
            contradiction_pressure=d("0.000000"),
            freshness_score=d("0.500000"),
        )
    with pytest.raises(ValueError, match="prior_hit_rate must be finite"):
        signal(prior_hit_rate="NaN")
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(signal(), paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        report_api.ResearchStrategyDomainMemoryReuseConfidenceConfig(readonly=False)
    with pytest.raises(ValueError, match="pass_threshold"):
        report_api.ResearchStrategyDomainMemoryReuseConfidenceConfig(
            pass_threshold=d("0.500000"),
            watch_threshold=d("0.600000"),
        )
    with pytest.raises(ValueError, match="restricted references"):
        signal(domain_key="market_slug_raw")
    with pytest.raises(ValueError, match="memory_label"):
        signal(memory_label="https://example.invalid/item")


def test_public_dataclasses_are_frozen_and_decimal_types_are_strict():
    report_api = api()

    class DecimalSubclass(Decimal):
        pass

    item = signal()
    with pytest.raises(FrozenInstanceError):
        item.prior_hit_rate = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="freshness_score must be a Decimal"):
        report_api.ResearchStrategyDomainMemoryReuseConfidenceInput(
            domain_key="tennis",
            memory_label="memory-alpha",
            observed_at=GENERATED_AT,
            prior_hit_rate=d("0.500000"),
            evidence_similarity_score=d("0.500000"),
            transferability_score=d("0.500000"),
            contradiction_pressure=d("0.000000"),
            freshness_score=DecimalSubclass("0.500000"),
        )


def test_public_dataclasses_reject_subclassing_at_class_definition():
    report_api = api()

    for public_type in (
        report_api.ResearchStrategyDomainMemoryReuseConfidenceConfig,
        report_api.ResearchStrategyDomainMemoryReuseConfidenceInput,
        report_api.ResearchStrategyDomainMemoryReuseConfidenceRow,
        report_api.ResearchStrategyDomainMemoryReuseConfidenceReasonCodeCount,
        report_api.ResearchStrategyDomainMemoryReuseConfidenceReport,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})


def test_public_report_rejects_nondeterministic_row_sequence_and_reason_codes():
    report_api = api()
    confidence_report = build_report(
        signal(),
        signal(
            domain_key="crypto",
            memory_label="memory-gamma",
            prior_hit_rate="0.440000",
            evidence_similarity_score="0.500000",
            transferability_score="0.410000",
            contradiction_pressure="0.780000",
            freshness_score="0.350000",
            observed_at=GENERATED_AT - timedelta(seconds=30000),
        ),
    )

    with pytest.raises(ValueError, match="rows must use deterministic sequence"):
        replace(confidence_report, rows=tuple(reversed(confidence_report.rows)))
    with pytest.raises(ValueError, match="reason_codes must use deterministic sequence"):
        report_api.ResearchStrategyDomainMemoryReuseConfidenceRow(
            rank=d("1"),
            domain_key="macro",
            memory_digest="0" * 64,
            status="watch",
            observed_at=GENERATED_AT - timedelta(seconds=9000),
            memory_age_seconds=d("9000.000000"),
            prior_hit_rate=d("0.640000"),
            evidence_similarity_score=d("0.620000"),
            transferability_score=d("0.570000"),
            contradiction_pressure=d("0.320000"),
            freshness_score=d("0.610000"),
            reuse_confidence_score=d("0.631000"),
            reason_codes=(
                "freshness_score_watch",
                "memory_reuse_confidence_score_watch",
                "prior_hit_rate_watch",
                "evidence_similarity_score_watch",
                "transferability_score_watch",
                "contradiction_pressure_watch",
            ),
        )


def test_module_scope_has_no_forbidden_execution_surfaces_or_literal_float_constants():
    source_text = Path(
        "src/polymarket_alpha_lab/research_strategy_domain_memory_reuse_confidence_report.py",
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


def _walk(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    else:
        yield value
