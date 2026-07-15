from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from pathlib import Path
from typing import Any
from collections import UserDict

import pytest


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_memory_signal_attribution_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(hours=2)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_memory_signal_attribution_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def memory_signal(**overrides: object):
    module = api()
    values = {
        "memory_signal_key": "memory_alpha",
        "domain_key": "macro_rates",
        "decision_count": d("10.000000"),
        "helped_decision_count": d("8.000000"),
        "hurt_decision_count": d("1.000000"),
        "historical_calibration_error_sum": d("1.000000"),
        "evidence_contribution_sum": d("8.000000"),
        "override_decision_count": d("4.000000"),
        "helpful_override_count": d("3.000000"),
        "stale_memory_age_hours_sum": d("120.000000"),
        "cross_domain_conflict_count": d("1.000000"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return module.ResearchTeamMemorySignalAttributionInput(**values)


def build_report(
    *signals: object,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
):
    module = api()
    kwargs: dict[str, object] = {"generated_at": generated_at}
    if config is not None:
        kwargs["config"] = config
    return module.build_research_team_memory_signal_attribution_report(
        signals,
        **kwargs,
    )


def sample_signals() -> tuple[object, ...]:
    return (
        memory_signal(
            memory_signal_key="memory_alpha",
            domain_key="macro_rates",
            decision_count=d("10.000000"),
            helped_decision_count=d("8.000000"),
            hurt_decision_count=d("1.000000"),
            historical_calibration_error_sum=d("1.000000"),
            evidence_contribution_sum=d("8.000000"),
            override_decision_count=d("4.000000"),
            helpful_override_count=d("3.000000"),
            stale_memory_age_hours_sum=d("120.000000"),
            cross_domain_conflict_count=d("1.000000"),
        ),
        memory_signal(
            memory_signal_key="memory_beta",
            domain_key="policy_rules",
            decision_count=d("8.000000"),
            helped_decision_count=d("4.000000"),
            hurt_decision_count=d("3.000000"),
            historical_calibration_error_sum=d("3.200000"),
            evidence_contribution_sum=d("4.000000"),
            override_decision_count=d("2.000000"),
            helpful_override_count=d("1.000000"),
            stale_memory_age_hours_sum=d("720.000000"),
            cross_domain_conflict_count=d("3.000000"),
        ),
        memory_signal(
            memory_signal_key="memory_gamma",
            domain_key="sports_soccer",
            decision_count=d("5.000000"),
            helped_decision_count=d("1.000000"),
            hurt_decision_count=d("4.000000"),
            historical_calibration_error_sum=d("4.000000"),
            evidence_contribution_sum=d("1.000000"),
            override_decision_count=d("2.000000"),
            helpful_override_count=d("0.000000"),
            stale_memory_age_hours_sum=d("1000.000000"),
            cross_domain_conflict_count=d("4.000000"),
        ),
    )


def test_memory_signal_attribution_reports_pass_watch_and_block_rows() -> None:
    module = api()

    report = build_report(*reversed(sample_signals()))

    assert is_dataclass(report)
    assert module.MEMORY_SIGNAL_ATTRIBUTION_STATUSES == ("pass", "watch", "block")
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "research-team-memory-signal-attribution-report-v0"
    )
    assert report.signal_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.helped_signal_count == d("2.000000")
    assert report.hurt_signal_count == d("1.000000")
    assert report.average_attribution_score == d("0.409464")
    assert report.average_historical_calibration_score == d("0.566667")
    assert report.average_evidence_contribution_score == d("0.500000")
    assert report.average_override_usefulness_score == d("0.416667")
    assert report.max_stale_memory_penalty == d("1.000000")
    assert report.max_cross_domain_conflict_pressure == d("0.800000")
    assert report.report_status == "block"
    assert len(report.derived_validation_digest) == 64

    blocked, watched, passed = report.rows
    assert tuple(row.domain_key for row in report.rows) == (
        "sports_soccer",
        "policy_rules",
        "macro_rates",
    )
    assert tuple(row.attribution_status for row in report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert blocked.historical_calibration_score == d("0.200000")
    assert blocked.evidence_contribution_score == d("0.200000")
    assert blocked.override_usefulness_score == d("0.000000")
    assert blocked.stale_memory_penalty == d("1.000000")
    assert blocked.cross_domain_conflict_pressure == d("0.800000")
    assert blocked.net_help_ratio == d("-0.600000")
    assert blocked.attribution_score == d("0.050000")
    assert blocked.reason_codes == (
        "memory_signal_attribution_block",
        "memory_signal_hurt",
        "historical_calibration_drag",
        "evidence_contribution_drag",
        "override_usefulness_drag",
        "stale_memory_penalty_block",
        "cross_domain_conflict_pressure_block",
    )

    assert watched.attribution_score == d("0.441964")
    assert watched.stale_memory_penalty == d("0.535714")
    assert watched.cross_domain_conflict_pressure == d("0.375000")
    assert "stale_memory_penalty_watch" in watched.reason_codes
    assert "cross_domain_conflict_pressure_watch" in watched.reason_codes

    assert passed.attribution_score == d("0.736429")
    assert passed.historical_calibration_score == d("0.900000")
    assert passed.evidence_contribution_score == d("0.800000")
    assert passed.override_usefulness_score == d("0.750000")
    assert passed.net_help_ratio == d("0.700000")
    assert passed.reason_codes == (
        "memory_signal_attribution_pass",
        "memory_signal_helped",
        "historical_calibration_support",
        "evidence_contribution_support",
        "override_usefulness_support",
    )
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_public_safe_decimal_string_json_with_valid_digest() -> None:
    module = api()
    report = build_report(*sample_signals())

    payload = module.research_team_memory_signal_attribution_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True)
    assert payload["signal_count"] == "3.000000"
    assert payload["rows"][0]["decision_count"] == "5.000000"
    assert payload["rows"][0]["memory_signal_digest"].startswith("sha256:")
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert all(character in "0123456789abcdef" for character in payload["derived_validation_digest"])

    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(digest_payload, separators=(",", ":")).encode(
            "utf-8",
        ),
    ).hexdigest()
    assert payload["derived_validation_digest"] == expected_digest

    for raw_identifier in ("memory_alpha", "memory_beta", "memory_gamma"):
        assert raw_identifier not in encoded
    for forbidden in (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    ):
        assert forbidden not in encoded.lower()
    assert_no_decimal_objects(payload)
    assert_no_float_or_int_values(payload)
    assert_no_float_or_int_values(report)


def test_empty_report_is_report_only_block_with_deterministic_digest() -> None:
    report_a = build_report()
    report_b = build_report()

    assert report_a.report_status == "block"
    assert report_a.signal_count == d("0.000000")
    assert report_a.reason_codes == (
        "memory_signal_attribution_report_block",
        "empty_memory_signals",
    )
    assert report_a.reason_code_counts[0].reason_code == (
        "memory_signal_attribution_report_block"
    )
    assert report_a.reason_code_counts[1].reason_code == "empty_memory_signals"
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert report_a.paper_only is True
    assert report_a.report_only is True
    assert report_a.readonly is True


def test_payload_validation_and_report_digest_reject_tampering() -> None:
    module = api()
    report = build_report(*sample_signals())

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = report.payload
    tampered = dict(payload)
    tampered["report_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_team_memory_signal_attribution_report_payload(tampered)

    bad_flag = dict(payload)
    bad_flag["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_team_memory_signal_attribution_report_payload(bad_flag)


def test_inputs_and_config_enforce_decimal_only_hard_flags_and_safe_public_codes() -> None:
    module = api()

    with pytest.raises(ValueError, match="Decimal"):
        memory_signal(decision_count=1)
    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchTeamMemorySignalAttributionConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        memory_signal(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(build_report(*sample_signals()), readonly=False)
    with pytest.raises(ValueError, match="unsafe public"):
        memory_signal(memory_signal_key="candidate_alpha")
    with pytest.raises(ValueError, match="unsafe public"):
        memory_signal(domain_key="market_slug")
    with pytest.raises(ValueError, match="observed_at"):
        build_report(memory_signal(observed_at=GENERATED_AT + timedelta(seconds=1)))


def test_dataclasses_are_frozen_final_and_public_surface_is_narrow() -> None:
    module = api()
    report = build_report(*sample_signals())

    with pytest.raises(FrozenInstanceError):
        report.report_status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError):

        class BadRow(module.ResearchTeamMemorySignalAttributionRow):
            pass

    forbidden = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden)
    for class_name in (
        "ResearchTeamMemorySignalAttributionConfig",
        "ResearchTeamMemorySignalAttributionInput",
        "ResearchTeamMemorySignalAttributionRow",
        "ResearchTeamMemorySignalAttributionReasonCodeCount",
        "ResearchTeamMemorySignalAttributionReport",
    ):
        cls = getattr(module, class_name)
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden)

    source = MODULE_PATH.read_text()
    for forbidden_import in (
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
        assert f"import {forbidden_import}" not in source
        assert f"from {forbidden_import}" not in source


def test_object_setattr_tampering_is_rejected_at_every_public_boundary() -> None:
    module = api()
    config = module.ResearchTeamMemorySignalAttributionConfig()
    object.__setattr__(config, "pass_attribution_score", d("0.100000"))
    with pytest.raises(ValueError, match="pass_attribution_score"):
        build_report(*sample_signals(), config=config)

    report = build_report(*sample_signals())
    object.__setattr__(report.rows[0], "attribution_score", d("0.999999"))
    with pytest.raises(ValueError, match="attribution_score"):
        module.research_team_memory_signal_attribution_report_payload(report)

    report = build_report(*sample_signals())
    object.__setattr__(
        report.config,
        "historical_calibration_weight",
        d("0.900000"),
    )
    with pytest.raises(ValueError, match="historical_calibration_weight"):
        report.payload

    report = build_report(*sample_signals())
    object.__setattr__(report, "report_status", "pass")
    with pytest.raises(ValueError, match="report_status"):
        report.payload


def test_decimal_validation_uses_exact_finite_unsigned_raw_values() -> None:
    module = api()

    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(ValueError, match="Decimal"):
        memory_signal(decision_count=DecimalSubclass("10.000000"))
    with pytest.raises(ValueError, match="finite"):
        memory_signal(decision_count=Decimal("NaN"))
    with pytest.raises(ValueError, match="finite"):
        module.ResearchTeamMemorySignalAttributionConfig(
            pass_attribution_score=Decimal("Infinity"),
        )
    with pytest.raises(ValueError, match="signed zero"):
        memory_signal(decision_count=Decimal("-0.000000"))
    with pytest.raises(ValueError, match="nonnegative"):
        memory_signal(decision_count=Decimal("-0.0000001"))
    with pytest.raises(ValueError, match="between zero and one"):
        module.ResearchTeamMemorySignalAttributionConfig(
            pass_attribution_score=Decimal("1.0000001"),
        )
    with pytest.raises(ValueError, match="nonnegative"):
        module.ResearchTeamMemorySignalAttributionConfig(
            historical_calibration_weight=Decimal("-0.0000001"),
        )
    with pytest.raises(ValueError, match="whole"):
        memory_signal(
            decision_count=d("1.500000"),
            helped_decision_count=d("1.000000"),
            hurt_decision_count=d("0.000000"),
            historical_calibration_error_sum=d("1.000000"),
            evidence_contribution_sum=d("1.000000"),
            override_decision_count=d("1.000000"),
            helpful_override_count=d("1.000000"),
            cross_domain_conflict_count=d("0.000000"),
        )
    with pytest.raises(ValueError, match="historical_calibration_error_sum"):
        memory_signal(
            decision_count=d("1.000000"),
            helped_decision_count=d("1.000000"),
            hurt_decision_count=d("0.000000"),
            historical_calibration_error_sum=Decimal("1.0000001"),
            evidence_contribution_sum=d("1.000000"),
            override_decision_count=d("1.000000"),
            helpful_override_count=d("1.000000"),
            cross_domain_conflict_count=d("0.000000"),
        )


def test_decimal_math_is_independent_of_ambient_context() -> None:
    expected = build_report(*sample_signals()).payload

    with localcontext(Context(prec=6, rounding=ROUND_DOWN)):
        constrained = build_report(*reversed(sample_signals())).payload

    assert constrained == expected


def test_report_revalidates_nested_rows_and_config_and_rederives_values() -> None:
    module = api()
    report = build_report(*sample_signals())

    bad_score_row = replace(report.rows[0], attribution_score=d("0.999999"))
    with pytest.raises(ValueError, match="attribution_score"):
        replace(report, rows=(bad_score_row, *report.rows[1:]))

    bad_status_row = replace(
        report.rows[-1],
        attribution_status="watch",
        reason_codes=(
            "memory_signal_attribution_watch",
            "memory_signal_helped",
            "historical_calibration_support",
            "evidence_contribution_support",
            "override_usefulness_support",
        ),
    )
    with pytest.raises(ValueError, match="attribution_status"):
        replace(report, rows=(*report.rows[:-1], bad_status_row))

    bad_reason_row = replace(
        report.rows[-1],
        reason_codes=(
            "memory_signal_attribution_pass",
            "memory_signal_helped",
            "historical_calibration_drag",
            "evidence_contribution_support",
            "override_usefulness_support",
        ),
    )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, rows=(*report.rows[:-1], bad_reason_row))

    changed_config = replace(
        report.config,
        historical_calibration_weight=d("0.900000"),
    )
    with pytest.raises(ValueError, match="attribution_score"):
        replace(report, config=changed_config)


def test_payload_requires_exact_canonical_schema_and_order() -> None:
    module = api()
    payload = build_report(*sample_signals()).payload

    with pytest.raises(ValueError, match="exact dict"):
        module.validate_research_team_memory_signal_attribution_report_payload(
            UserDict(payload),
        )

    reordered = dict(reversed(tuple(payload.items())))
    with pytest.raises(ValueError, match="schema order"):
        module.validate_research_team_memory_signal_attribution_report_payload(
            reordered,
        )

    extra = dict(payload)
    extra["unexpected"] = "value"
    with pytest.raises(ValueError, match="schema"):
        module.validate_research_team_memory_signal_attribution_report_payload(extra)

    missing = dict(payload)
    missing.pop("report_status")
    with pytest.raises(ValueError, match="schema"):
        module.validate_research_team_memory_signal_attribution_report_payload(missing)

    nested_reordered = deepcopy(payload)
    nested_reordered["rows"][0] = dict(
        reversed(tuple(nested_reordered["rows"][0].items())),
    )
    with pytest.raises(ValueError, match="rows\\[0\\].*schema order"):
        module.validate_research_team_memory_signal_attribution_report_payload(
            nested_reordered,
        )


@pytest.mark.parametrize(
    ("mutator", "error"),
    (
        (
            lambda payload: payload["rows"][0].__setitem__(
                "attribution_score",
                "0.999999",
            ),
            "attribution_score",
        ),
        (
            lambda payload: payload["rows"][0].__setitem__(
                "attribution_status",
                "watch",
            ),
            "attribution_status",
        ),
        (
            lambda payload: payload["rows"][0].__setitem__(
                "reason_codes",
                [
                    "memory_signal_attribution_block",
                    "memory_signal_hurt",
                ],
            ),
            "reason_codes",
        ),
        (
            lambda payload: payload.__setitem__("report_status", "pass"),
            "report_status",
        ),
        (
            lambda payload: payload.__setitem__("signal_count", "4.000000"),
            "signal_count",
        ),
        (
            lambda payload: payload.__setitem__(
                "average_attribution_score",
                "0.999999",
            ),
            "average_attribution_score",
        ),
        (
            lambda payload: payload["reason_code_counts"][0].__setitem__(
                "count",
                "99.000000",
            ),
            "reason_code_counts",
        ),
    ),
)
def test_payload_rederives_all_derived_values_even_with_valid_hash(
    mutator: Any,
    error: str,
) -> None:
    module = api()
    payload = build_report(*sample_signals()).payload
    mutator(payload)
    payload = rehash_payload(payload)

    with pytest.raises(ValueError, match=error):
        module.validate_research_team_memory_signal_attribution_report_payload(payload)


def test_payload_schema_order_hash_and_round_trip_are_canonical() -> None:
    module = api()
    report = build_report(*sample_signals())
    payload = report.payload

    assert tuple(payload) == (
        "generated_at",
        "config",
        "config_version",
        "report_status",
        "signal_count",
        "pass_count",
        "watch_count",
        "block_count",
        "helped_signal_count",
        "hurt_signal_count",
        "average_attribution_score",
        "average_historical_calibration_score",
        "average_evidence_contribution_score",
        "average_override_usefulness_score",
        "max_stale_memory_penalty",
        "max_cross_domain_conflict_pressure",
        "rows",
        "reason_codes",
        "reason_code_counts",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["config"]) == tuple(
        field.name for field in fields(module.ResearchTeamMemorySignalAttributionConfig)
    )
    assert tuple(payload["rows"][0]) == (
        "memory_signal_digest",
        "domain_key",
        "decision_count",
        "helped_decision_count",
        "hurt_decision_count",
        "historical_calibration_error_sum",
        "evidence_contribution_sum",
        "override_decision_count",
        "helpful_override_count",
        "stale_memory_age_hours_sum",
        "cross_domain_conflict_count",
        "historical_calibration_score",
        "evidence_contribution_score",
        "override_usefulness_score",
        "stale_memory_penalty",
        "cross_domain_conflict_pressure",
        "net_help_ratio",
        "attribution_score",
        "attribution_status",
        "observed_at",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["reason_code_counts"][0]) == tuple(
        field.name
        for field in fields(
            module.ResearchTeamMemorySignalAttributionReasonCodeCount,
        )
    )

    material = dict(payload)
    material.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(material, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert payload["derived_validation_digest"] == expected_digest
    assert module.research_team_memory_signal_attribution_report_payload(payload) == payload
    assert build_report(*reversed(sample_signals())).payload == payload


def test_row_sort_key_has_a_complete_deterministic_tie_break(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = api()
    fixed_digest = "sha256:" + ("a" * 64)
    monkeypatch.setattr(module, "_memory_signal_digest", lambda *_: fixed_digest)
    signals = (
        memory_signal(memory_signal_key="memory_alpha", domain_key="shared_domain"),
        memory_signal(
            memory_signal_key="memory_beta",
            domain_key="shared_domain",
            decision_count=d("10.000000"),
            helped_decision_count=d("9.000000"),
            hurt_decision_count=d("0.000000"),
            historical_calibration_error_sum=d("0.000000"),
            evidence_contribution_sum=d("9.000000"),
            override_decision_count=d("2.000000"),
            helpful_override_count=d("2.000000"),
            stale_memory_age_hours_sum=d("0.000000"),
            cross_domain_conflict_count=d("0.000000"),
            observed_at=OBSERVED_AT - timedelta(minutes=1),
        ),
    )

    report = build_report(*signals)
    assert module._row_sort_key(report.rows[0]) != module._row_sort_key(report.rows[1])
    assert tuple(sorted(reversed(report.rows), key=module._row_sort_key)) == report.rows
    assert build_report(*reversed(signals)).payload == report.payload


def test_public_api_remains_paper_report_readonly_without_execution_surfaces() -> None:
    module = api()
    forbidden_public_fragments = (
        "persist",
        "execution",
        "authentication",
        "wallet",
        "recommend",
        "ranking",
        "sizing",
    )
    assert not any(
        fragment in public_name.lower()
        for public_name in module.__all__
        for fragment in forbidden_public_fragments
    )

    report = build_report(*sample_signals())
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.config.paper_only is True
    assert report.config.report_only is True
    assert report.config.readonly is True
    assert all(
        row.paper_only is True and row.report_only is True and row.readonly is True
        for row in report.rows
    )


def rehash_payload(payload: dict[str, Any]) -> dict[str, Any]:
    rehashed = deepcopy(payload)
    material = {
        key: value
        for key, value in rehashed.items()
        if key != "derived_validation_digest"
    }
    rehashed["derived_validation_digest"] = hashlib.sha256(
        json.dumps(material, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    return rehashed


def assert_no_decimal_objects(value: Any) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_decimal_objects(child)
    if isinstance(value, list):
        for child in value:
            assert_no_decimal_objects(child)


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) in (float, int):
        raise AssertionError(f"unexpected numeric payload value: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_int_values(child)
        return
    if isinstance(value, (list, tuple)):
        for child in value:
            assert_no_float_or_int_values(child)
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_no_float_or_int_values(getattr(value, field.name))
