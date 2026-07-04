from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
SIGNALED_AT = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)
CONFIG_VERSION = "strategy-team-signal-disagreement-digest-test-v0"


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_signal_disagreement_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    team_id: str,
    *,
    condition_id: str = "condition-alpha",
    forecast_probability: Decimal = d("0.600000"),
    confidence: Decimal = d("0.800000"),
    signaled_at: datetime = SIGNALED_AT,
    source_reference: str = "internal-team-signal",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.StrategyTeamForecastSignal(
        condition_id=condition_id,
        team_id=team_id,
        forecast_probability=forecast_probability,
        confidence=confidence,
        signaled_at=signaled_at,
        source_reference=source_reference,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals, **overrides):
    digest = module()
    values = {
        "generated_at": GENERATED_AT,
        "config_version": CONFIG_VERSION,
        "signals": signals,
    }
    values.update(overrides)
    return digest.build_strategy_team_signal_disagreement_digest(**values)


def test_empty_input_returns_report_only_clear_summary() -> None:
    report = build_report()

    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.condition_count == d("0")
    assert report.signal_count == d("0")
    assert report.clear_condition_count == d("0")
    assert report.watch_condition_count == d("0")
    assert report.blocked_condition_count == d("0")
    assert report.disagreement_condition_count == d("0")
    assert report.disagreement_condition_ratio is None
    assert report.status == "clear"
    assert report.reason_codes == ("empty_team_forecast_signals",)
    assert report.rows == ()
    assert report.reason_rollups == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_aligned_team_signals_clear_with_consensus_metrics() -> None:
    report = build_report(
        signal(
            "macro",
            forecast_probability=d("0.620000"),
            confidence=d("0.750000"),
        ),
        signal(
            "news",
            forecast_probability=d("0.580000"),
            confidence=d("0.250000"),
        ),
    )

    assert report.status == "clear"
    assert report.condition_count == d("1")
    assert report.signal_count == d("2")
    assert report.clear_condition_count == d("1")
    assert report.disagreement_condition_count == d("0")
    assert report.disagreement_condition_ratio == d("0.000000")
    assert report.reason_codes == ("team_signal_disagreement_clear",)

    row = report.rows[0]
    assert row.condition_id == "condition-alpha"
    assert row.row_status == "clear"
    assert row.team_count == d("2")
    assert row.minimum_forecast_probability == d("0.580000")
    assert row.maximum_forecast_probability == d("0.620000")
    assert row.average_forecast_probability == d("0.600000")
    assert row.consensus_probability == d("0.610000")
    assert row.forecast_spread == d("0.040000")
    assert row.consensus_confidence == d("0.500000")
    assert row.minimum_confidence == d("0.250000")
    assert row.consensus_confidence_gap == d("0.250000")
    assert row.high_disagreement is False
    assert row.stale_minority_view_count == d("0")
    assert row.source_references == ("<redacted-source-reference>",)
    assert row.reason_codes == ("team_signal_disagreement_clear",)


def test_single_signal_and_zero_confidence_consensus_paths_are_clear() -> None:
    single = build_report(
        signal(
            "macro",
            forecast_probability=d("0.420000"),
            confidence=d("0.000000"),
        ),
    )

    assert single.status == "clear"
    assert single.signal_count == d("1")
    assert single.rows[0].consensus_probability == d("0.420000")
    assert single.rows[0].consensus_confidence == d("0.000000")
    assert single.rows[0].reason_codes == ("team_signal_disagreement_clear",)

    zero_confidence = build_report(
        signal(
            "macro",
            forecast_probability=d("0.200000"),
            confidence=d("0.000000"),
        ),
        signal(
            "news",
            forecast_probability=d("0.800000"),
            confidence=d("0.000000"),
        ),
        disagreement_spread_limit=d("0.900000"),
    )

    row = zero_confidence.rows[0]
    assert zero_confidence.status == "clear"
    assert row.consensus_probability == d("0.500000")
    assert row.consensus_confidence == d("0.000000")
    assert row.minimum_confidence == d("0.000000")
    assert row.consensus_confidence_gap == d("0.000000")
    assert row.reason_codes == ("team_signal_disagreement_clear",)


def test_high_disagreement_stale_minority_and_confidence_gap_are_flagged() -> None:
    stale_signal_at = datetime(2026, 6, 30, 11, 0, tzinfo=timezone.utc)
    report = build_report(
        signal(
            "macro",
            forecast_probability=d("0.740000"),
            confidence=d("0.900000"),
            source_reference="postgres://secret-token@example.invalid/team-signals",
        ),
        signal(
            "news",
            forecast_probability=d("0.450000"),
            confidence=d("0.300000"),
            signaled_at=stale_signal_at,
            source_reference="https://secret.example.invalid/research-note",
        ),
        signal(
            "model",
            forecast_probability=d("0.700000"),
            confidence=d("0.800000"),
        ),
        stale_signal_seconds=d("86400.000000"),
        disagreement_spread_limit=d("0.200000"),
        confidence_gap_limit=d("0.150000"),
    )

    assert report.status == "blocked"
    assert report.blocked_condition_count == d("1")
    assert report.disagreement_condition_count == d("1")
    assert report.disagreement_condition_ratio == d("1.000000")
    assert report.reason_codes == (
        "high_team_forecast_disagreement",
        "stale_minority_team_view",
        "consensus_confidence_gap",
    )

    row = report.rows[0]
    assert row.row_status == "blocked"
    assert row.minimum_forecast_probability == d("0.450000")
    assert row.maximum_forecast_probability == d("0.740000")
    assert row.forecast_spread == d("0.290000")
    assert row.consensus_probability == d("0.680500")
    assert row.consensus_confidence == d("0.666667")
    assert row.minimum_confidence == d("0.300000")
    assert row.consensus_confidence_gap == d("0.366667")
    assert row.high_disagreement is True
    assert row.stale_minority_view_count == d("1")
    assert row.latest_signaled_at == datetime(2026, 7, 2, 10, 0, tzinfo=UTC)
    assert row.source_references == ("<redacted-source-reference>",)
    assert row.reason_codes == (
        "high_team_forecast_disagreement",
        "stale_minority_team_view",
        "consensus_confidence_gap",
    )
    assert "secret-token" not in repr(signal("macro", source_reference="secret-token"))
    assert "secret.example" not in repr(row)


def test_stale_optimistic_minority_view_is_counted_above_consensus() -> None:
    stale_signal_at = datetime(2026, 6, 30, 11, 0, tzinfo=UTC)
    report = build_report(
        signal(
            "macro",
            forecast_probability=d("0.850000"),
            confidence=d("0.200000"),
            signaled_at=stale_signal_at,
        ),
        signal(
            "news",
            forecast_probability=d("0.300000"),
            confidence=d("0.900000"),
        ),
        signal(
            "model",
            forecast_probability=d("0.350000"),
            confidence=d("0.900000"),
        ),
        stale_signal_seconds=d("86400.000000"),
        disagreement_spread_limit=d("0.700000"),
        confidence_gap_limit=d("0.900000"),
    )

    row = report.rows[0]
    assert report.status == "watch"
    assert report.reason_codes == ("stale_minority_team_view",)
    assert row.consensus_probability == d("0.377500")
    assert row.stale_minority_view_count == d("1")
    assert row.reason_codes == ("stale_minority_team_view",)


def test_deterministic_row_sorting_and_reason_rollups() -> None:
    report = build_report(
        signal(
            "macro",
            condition_id="condition-z",
            forecast_probability=d("0.750000"),
            confidence=d("0.900000"),
        ),
        signal(
            "news",
            condition_id="condition-z",
            forecast_probability=d("0.450000"),
            confidence=d("0.200000"),
        ),
        signal(
            "macro",
            condition_id="condition-a",
            forecast_probability=d("0.620000"),
            confidence=d("0.800000"),
        ),
        signal(
            "news",
            condition_id="condition-a",
            forecast_probability=d("0.570000"),
            confidence=d("0.300000"),
        ),
        disagreement_spread_limit=d("0.200000"),
        confidence_gap_limit=d("0.250000"),
    )

    assert tuple(row.condition_id for row in report.rows) == (
        "condition-z",
        "condition-a",
    )
    assert tuple(row.row_status for row in report.rows) == ("watch", "clear")
    assert report.reason_codes == (
        "high_team_forecast_disagreement",
        "consensus_confidence_gap",
    )
    assert tuple(rollup.reason_code for rollup in report.reason_rollups) == (
        "high_team_forecast_disagreement",
        "consensus_confidence_gap",
    )
    assert tuple(rollup.condition_count for rollup in report.reason_rollups) == (
        d("1"),
        d("1"),
    )
    assert all(rollup.condition_ratio == d("0.500000") for rollup in report.reason_rollups)


def test_manual_row_and_report_invariants_are_enforced() -> None:
    report = build_report(signal("macro"))
    row = report.rows[0]

    with pytest.raises(ValueError, match="high_disagreement"):
        replace(row, high_disagreement=True)
    with pytest.raises(ValueError, match="stale_minority_view_count"):
        replace(row, stale_minority_view_count=d("1"))
    with pytest.raises(ValueError, match="signal_count"):
        replace(report, signal_count=d("2"))

    future_row = replace(row, latest_signaled_at=GENERATED_AT + timedelta(seconds=1))
    with pytest.raises(ValueError, match="latest_signaled_at"):
        replace(report, rows=(future_row,))


def test_json_payload_helper_uses_decimal_strings_iso_datetimes_and_no_floats() -> None:
    digest = module()
    report = build_report(
        signal(
            "macro",
            forecast_probability=d("0.620000"),
            confidence=d("0.750000"),
        ),
        signal(
            "news",
            forecast_probability=d("0.580000"),
            confidence=d("0.250000"),
        ),
    )

    payload = digest.strategy_team_signal_disagreement_digest_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["condition_count"] == "1"
    assert payload["rows"][0]["consensus_probability"] == "0.610000"
    assert payload["rows"][0]["latest_signaled_at"] == "2026-07-02T10:00:00+00:00"
    assert payload["rows"][0]["source_references"] == ["<redacted-source-reference>"]
    assert '"0.610000"' in encoded
    assert not any(isinstance(value, float) for value in _walk_values(payload))


def test_validation_rejects_bad_inputs_and_unsafe_flags_without_echoing_source() -> None:
    digest = module()
    secret = "token=secret-team-signal"

    with pytest.raises(ValueError, match="generated_at"):
        build_report(generated_at="2026-07-02T12:00:00Z")
    with pytest.raises(ValueError, match="config_version"):
        build_report(config_version=" ")
    with pytest.raises(ValueError, match="signals must be an iterable"):
        digest.build_strategy_team_signal_disagreement_digest(
            generated_at=GENERATED_AT,
            config_version=CONFIG_VERSION,
            signals=object(),
        )
    with pytest.raises(ValueError, match="paper_only"):
        build_report(signal("unsafe", paper_only=False))
    with pytest.raises(ValueError, match="forecast_probability"):
        signal("float-probability", forecast_probability=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="confidence"):
        signal("float-confidence", confidence=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="signaled_at"):
        signal("naive-time", signaled_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="signals must contain unique condition and team"):
        build_report(signal("macro"), signal("macro"))
    with pytest.raises(ValueError) as exc_info:
        signal("bad-source", source_reference=secret, confidence=d("-0.100000"))

    assert "confidence" in str(exc_info.value)
    assert secret not in str(exc_info.value)


def test_public_text_fields_reject_sensitive_values_without_echoing_them() -> None:
    sensitive_condition = "condition-token-secret"
    sensitive_team = "wallet-private-key-team"
    sensitive_config = "api_key=secret"

    with pytest.raises(ValueError, match="condition_id") as condition_exc:
        signal("macro", condition_id=sensitive_condition)
    with pytest.raises(ValueError, match="team_id") as team_exc:
        signal(sensitive_team)
    with pytest.raises(ValueError, match="config_version") as config_exc:
        build_report(signal("macro"), config_version=sensitive_config)

    assert sensitive_condition not in str(condition_exc.value)
    assert sensitive_team not in str(team_exc.value)
    assert sensitive_config not in str(config_exc.value)


def test_manual_reason_codes_are_closed_and_do_not_leak_sensitive_values() -> None:
    digest = module()
    report = build_report(signal("macro"))
    sensitive_reason = "wallet_private_key"

    with pytest.raises(ValueError, match="reason_code") as row_exc:
        replace(
            report.rows[0],
            row_status="watch",
            reason_codes=(sensitive_reason,),
        )
    with pytest.raises(ValueError, match="reason_code") as rollup_exc:
        digest.StrategyTeamSignalDisagreementReasonRollup(
            reason_code=sensitive_reason,
            condition_count=d("1"),
            condition_ratio=d("1.000000"),
        )

    assert sensitive_reason not in str(row_exc.value)
    assert sensitive_reason not in str(rollup_exc.value)


def test_public_dataclasses_are_frozen_and_decimal_types_are_strict() -> None:
    digest = module()

    class DecimalSubclass(Decimal):
        pass

    class StrSubclass(str):
        pass

    class DateTimeSubclass(datetime):
        pass

    assert digest.__all__ == (
        "StrategyTeamForecastSignal",
        "StrategyTeamSignalDisagreementDigestReport",
        "StrategyTeamSignalDisagreementReasonRollup",
        "StrategyTeamSignalDisagreementRow",
        "build_strategy_team_signal_disagreement_digest",
        "strategy_team_signal_disagreement_digest_payload",
    )
    for exported_name in digest.__all__:
        value = getattr(digest, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(signal("frozen"))
    with pytest.raises(FrozenInstanceError):
        report.rows[0].row_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="team_id"):
        signal(StrSubclass("macro"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(generated_at=DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="condition_count"):
        replace(report, condition_count=DecimalSubclass("1"))


def test_static_forbidden_surface_terms_are_absent() -> None:
    source = module().__loader__.get_source(module().__name__)
    assert source is not None
    lowered = source.lower()

    for forbidden in (
        "db",
        "database",
        "network",
        "request",
        "socket",
        "live",
        "trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "account",
        "advice",
        "secret",
        "token",
        "private_key",
        "api_key",
    ):
        assert forbidden not in lowered


def _walk_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_values(item)
    else:
        yield value
