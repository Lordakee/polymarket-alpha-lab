from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal, localcontext
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_team_specialist_memory_reuse_backtest_readiness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def memory_signal(
    *,
    specialist_key: str = "rates-specialist",
    memory_reference: str = "memory-alpha",
    observed_at: datetime = GENERATED_AT - timedelta(seconds=3600),
    prior_reuse_hit_rate: str = "0.900000",
    signal_similarity_score: str = "0.850000",
    backtest_sample_count: str = "30",
    backtest_success_rate: str = "0.880000",
    contradiction_pressure: str = "0.050000",
    calibration_drift_pressure: str = "0.050000",
):
    report_api = api()
    return report_api.ResearchTeamSpecialistMemoryReuseBacktestReadinessInput(
        specialist_key=specialist_key,
        memory_reference=memory_reference,
        observed_at=observed_at,
        prior_reuse_hit_rate=d(prior_reuse_hit_rate),
        signal_similarity_score=d(signal_similarity_score),
        backtest_sample_count=d(backtest_sample_count),
        backtest_success_rate=d(backtest_success_rate),
        contradiction_pressure=d(contradiction_pressure),
        calibration_drift_pressure=d(calibration_drift_pressure),
    )


def build_report(*items, generated_at: datetime = GENERATED_AT, config=None):
    report_api = api()
    return report_api.build_research_team_specialist_memory_reuse_backtest_readiness_report(
        items,
        generated_at=generated_at,
        config=(
            config
            or report_api.ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig()
        ),
    )


def test_report_scores_specialist_memory_reuse_backtest_readiness_safely():
    readiness_report = build_report(
        memory_signal(),
        memory_signal(
            specialist_key="macro-specialist",
            memory_reference="memory-beta",
            observed_at=GENERATED_AT - timedelta(seconds=9000),
            prior_reuse_hit_rate="0.640000",
            signal_similarity_score="0.650000",
            backtest_sample_count="10",
            backtest_success_rate="0.620000",
            contradiction_pressure="0.320000",
            calibration_drift_pressure="0.400000",
        ),
        memory_signal(
            specialist_key="crypto-specialist",
            memory_reference="memory-gamma",
            observed_at=GENERATED_AT - timedelta(seconds=30000),
            prior_reuse_hit_rate="0.400000",
            signal_similarity_score="0.450000",
            backtest_sample_count="0",
            backtest_success_rate="0.380000",
            contradiction_pressure="0.800000",
            calibration_drift_pressure="0.750000",
        ),
    )

    assert is_dataclass(readiness_report)
    assert readiness_report.generated_at == GENERATED_AT
    assert readiness_report.config_version == (
        "research-team-specialist-memory-reuse-backtest-readiness-report-v0"
    )
    assert readiness_report.signal_count == d("3")
    assert readiness_report.pass_count == d("1")
    assert readiness_report.watch_count == d("1")
    assert readiness_report.block_count == d("1")
    assert readiness_report.status == "block"
    assert readiness_report.average_readiness_score == d("0.608000")
    assert readiness_report.lowest_backtest_sample_count == d("0")
    assert readiness_report.highest_contradiction_pressure == d("0.800000")
    assert readiness_report.oldest_memory_age_seconds == d("30000.000000")
    assert readiness_report.paper_only is True
    assert readiness_report.report_only is True
    assert readiness_report.readonly is True

    assert tuple(row.status for row in readiness_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    blocked, watched, passing = readiness_report.rows
    assert blocked.rank == d("1")
    assert blocked.specialist_key == "crypto-specialist"
    assert blocked.memory_digest != "memory-gamma"
    assert len(blocked.memory_digest) == 64
    assert blocked.backtest_sample_depth_score == d("0.000000")
    assert blocked.memory_reuse_backtest_readiness_score == d("0.298500")
    assert blocked.memory_age_seconds == d("30000.000000")
    assert blocked.reason_codes == (
        "readiness_score_block",
        "prior_reuse_hit_rate_block",
        "signal_similarity_score_block",
        "backtest_sample_depth_block",
        "backtest_success_rate_block",
        "contradiction_pressure_block",
        "calibration_drift_pressure_block",
    )
    assert watched.memory_reuse_backtest_readiness_score == d("0.612000")
    assert watched.reason_codes == (
        "readiness_score_watch",
        "prior_reuse_hit_rate_watch",
        "signal_similarity_score_watch",
        "backtest_sample_depth_watch",
        "backtest_success_rate_watch",
        "contradiction_pressure_watch",
        "calibration_drift_pressure_watch",
    )
    assert passing.reason_codes == ("specialist_memory_reuse_backtest_ready",)


def test_empty_report_blocks_at_readonly_report_boundary():
    readiness_report = build_report()

    assert readiness_report.signal_count == d("0")
    assert readiness_report.pass_count == d("0")
    assert readiness_report.watch_count == d("0")
    assert readiness_report.block_count == d("0")
    assert readiness_report.status == "block"
    assert readiness_report.average_readiness_score == d("0.000000")
    assert readiness_report.reason_codes == (
        "empty_specialist_memory_reuse_backtest_readiness_inputs",
    )
    assert readiness_report.reason_code_counts == ()
    assert readiness_report.rows == ()
    assert readiness_report.paper_only is True
    assert readiness_report.report_only is True
    assert readiness_report.readonly is True


def test_public_payload_is_deterministic_decimal_stringed_and_digest_checked():
    report_api = api()
    items = (
        memory_signal(
            specialist_key="macro-specialist",
            memory_reference="memory-beta",
            observed_at=GENERATED_AT - timedelta(seconds=9000),
            prior_reuse_hit_rate="0.640000",
            signal_similarity_score="0.650000",
            backtest_sample_count="10",
            backtest_success_rate="0.620000",
            contradiction_pressure="0.320000",
            calibration_drift_pressure="0.400000",
        ),
        memory_signal(),
    )
    first_report = build_report(*items)
    second_report = build_report(*reversed(items))

    first_payload = (
        report_api
        .research_team_specialist_memory_reuse_backtest_readiness_report_payload(
            first_report,
        )
    )
    second_payload = (
        report_api
        .research_team_specialist_memory_reuse_backtest_readiness_report_payload(
            second_report,
        )
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_report.public_payload_sha256 == second_report.public_payload_sha256
    assert first_payload["public_payload_sha256"] == first_report.public_payload_sha256
    assert first_payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_payload["signal_count"] == "2"
    assert first_payload["rows"][0]["memory_age_seconds"] == "9000.000000"
    assert first_payload["rows"][0]["backtest_sample_count"] == "10"
    assert first_payload["rows"][0]["memory_reuse_backtest_readiness_score"] == (
        "0.612000"
    )
    assert all(type(value) is not float for value in _walk(first_payload))
    assert all(type(value) is not int for value in _walk(first_payload))
    for forbidden in (
        "candidate_id",
        "candidate id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "market_question",
        "question",
        "source_url",
        "source_text",
        "url",
        "http://",
        "https://",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "position",
        "sizing",
        "recommendation",
        "memory-alpha",
        "memory-beta",
    ):
        assert forbidden not in encoded.lower()

    with pytest.raises(ValueError, match="public_payload_sha256"):
        replace(first_report, public_payload_sha256="0" * 64)

    tampered_report = replace(first_report)
    object.__setattr__(tampered_report, "public_payload_sha256", "0" * 64)
    with pytest.raises(ValueError, match="public_payload_sha256"):
        (
            report_api
            .research_team_specialist_memory_reuse_backtest_readiness_report_payload(
                tampered_report,
            )
        )


def test_validation_rejects_bad_types_times_flags_thresholds_and_unsafe_labels():
    report_api = api()

    class DecimalSubclass(Decimal):
        pass

    class DateTimeSubclass(datetime):
        pass

    class NoneOffsetTz(tzinfo):
        def utcoffset(self, dt):
            return None

        def dst(self, dt):
            return None

    with pytest.raises(ValueError, match="prior_reuse_hit_rate must be a Decimal"):
        report_api.ResearchTeamSpecialistMemoryReuseBacktestReadinessInput(
            specialist_key="rates-specialist",
            memory_reference="memory-alpha",
            observed_at=GENERATED_AT,
            prior_reuse_hit_rate=0.5,
            signal_similarity_score=d("0.500000"),
            backtest_sample_count=d("10"),
            backtest_success_rate=d("0.500000"),
            contradiction_pressure=d("0.000000"),
            calibration_drift_pressure=d("0.000000"),
        )
    with pytest.raises(ValueError, match="prior_reuse_hit_rate must be finite"):
        memory_signal(prior_reuse_hit_rate="NaN")
    with pytest.raises(ValueError, match="backtest_sample_count must be a whole count"):
        memory_signal(backtest_sample_count=("1" * 65) + ".1")
    with pytest.raises(ValueError, match="calibration_drift_pressure must be a Decimal"):
        report_api.ResearchTeamSpecialistMemoryReuseBacktestReadinessInput(
            specialist_key="rates-specialist",
            memory_reference="memory-alpha",
            observed_at=GENERATED_AT,
            prior_reuse_hit_rate=d("0.500000"),
            signal_similarity_score=d("0.500000"),
            backtest_sample_count=d("10"),
            backtest_success_rate=d("0.500000"),
            contradiction_pressure=d("0.000000"),
            calibration_drift_pressure=DecimalSubclass("0.000000"),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        memory_signal(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        memory_signal(observed_at=datetime(2026, 7, 9, 12, 0, tzinfo=NoneOffsetTz()))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_report(
            memory_signal(),
            generated_at=DateTimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after"):
        build_report(memory_signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="specialist_key"):
        memory_signal(specialist_key="market_slug_raw")
    with pytest.raises(ValueError, match="memory_reference"):
        memory_signal(memory_reference="https://example.invalid/item")
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(memory_signal(), paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        report_api.ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig(
            readonly=False,
        )
    with pytest.raises(ValueError, match="pass_threshold"):
        report_api.ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig(
            pass_threshold=d("0.500000"),
            watch_threshold=d("0.600000"),
        )
    with pytest.raises(ValueError, match="weights must total one"):
        report_api.ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig(
            prior_reuse_hit_rate_weight=d("0.100000"),
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("specialist_key", "candidate id 123"),
        ("specialist_key", "candidate-id-123"),
        ("specialist_key", "raw candidate 123"),
        ("specialist_key", "raw-candidate-123"),
        ("specialist_key", "table name positions"),
        ("memory_reference", "candidate-id-123"),
    ),
)
def test_rejects_separator_obfuscated_restricted_public_identifiers(
    field_name: str,
    value: str,
):
    with pytest.raises(ValueError, match=field_name):
        memory_signal(**{field_name: value})


def test_default_report_is_independent_of_ambient_decimal_context():
    report_api = api()
    observed_at = GENERATED_AT - timedelta(seconds=3600, microseconds=123456)
    baseline_report = build_report(memory_signal(observed_at=observed_at))
    baseline_payload = (
        report_api
        .research_team_specialist_memory_reuse_backtest_readiness_report_payload(
            baseline_report,
        )
    )

    with localcontext() as context:
        context.prec = 3
        constrained_config = (
            report_api.ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig()
        )
        constrained_report = build_report(
            memory_signal(observed_at=observed_at),
            config=constrained_config,
        )
        constrained_payload = (
            report_api
            .research_team_specialist_memory_reuse_backtest_readiness_report_payload(
                constrained_report,
            )
        )

    assert constrained_config == (
        report_api.ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig()
    )
    assert constrained_report == baseline_report
    assert constrained_payload == baseline_payload


def test_public_dataclasses_are_frozen_and_manual_report_sequence_is_validated():
    report_api = api()
    readiness_report = build_report(memory_signal(), memory_signal(specialist_key="macro"))

    with pytest.raises(FrozenInstanceError):
        readiness_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        readiness_report.rows[0].rank = d("99")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(readiness_report.rows[0], status="ready")
    with pytest.raises(ValueError, match="rows must use deterministic sequence"):
        replace(readiness_report, rows=tuple(reversed(readiness_report.rows)))
    with pytest.raises(ValueError, match="signal_count"):
        replace(readiness_report, signal_count=d("99"))
    with pytest.raises(ValueError, match="public_payload_sha256"):
        replace(readiness_report, public_payload_sha256="0" * 64)

    assert type(readiness_report.rows[0]) is (
        report_api.ResearchTeamSpecialistMemoryReuseBacktestReadinessRow
    )


def test_owned_module_has_no_io_trading_identity_or_advice_surfaces():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_team_specialist_memory_reuse_backtest_readiness_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "candidate_id",
        "candidate id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "position",
        "sizing",
        "recommendation",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk(item))
    else:
        values.append(value)
    return tuple(values)
