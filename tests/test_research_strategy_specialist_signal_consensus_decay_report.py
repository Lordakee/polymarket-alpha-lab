from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Context, Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_specialist_signal_consensus_decay_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StatusSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class _InvalidOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> timedelta:
        return "invalid"  # type: ignore[return-value]

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_specialist_signal_consensus_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            "research-strategy-specialist-signal-consensus-decay-report-test-v0"
        ),
        "consensus_pass_floor": d("0.750000"),
        "consensus_watch_floor": d("0.550000"),
        "freshness_watch_floor": d("0.500000"),
        "freshness_block_floor": d("0.250000"),
        "dispersion_watch_ceiling": d("0.200000"),
        "dispersion_block_ceiling": d("0.350000"),
        "stale_signal_block_seconds": d("7200.000000"),
        "minimum_specialist_count": d("2.000000"),
    }
    values.update(overrides)
    return module.ResearchStrategySpecialistSignalConsensusDecayConfig(**values)


def signal(**overrides: object):
    module = api()
    values = {
        "signal_ref": "alpha_signal",
        "specialist_ref": "domain_a",
        "observed_at": datetime(2026, 7, 9, 11, 30, tzinfo=UTC),
        "probability_estimate": d("0.620000"),
        "confidence_score": d("0.900000"),
    }
    values.update(overrides)
    return module.ResearchStrategySpecialistSignalConsensusDecayInput(**values)


def report(*, inputs=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_specialist_signal_consensus_decay_report(
        inputs,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)


def payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(payload_values(item))
        return tuple(values)
    return (value,)


def payload_with_recomputed_digests(
    payload: dict[str, object],
) -> dict[str, object]:
    result = deepcopy(payload)
    rows = result.get("rows")
    if isinstance(rows, list):
        for row in rows:
            if type(row) is not dict:
                continue
            unsigned_row = {
                key: value
                for key, value in row.items()
                if key != "derived_validation_digest"
            }
            row["derived_validation_digest"] = hashlib.sha256(
                json.dumps(
                    unsigned_row,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8"),
            ).hexdigest()
    unsigned_report = {
        key: value
        for key, value in result.items()
        if key != "derived_validation_digest"
    }
    result["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            unsigned_report,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    return result


def test_report_scores_specialist_consensus_decay_without_actionable_outputs() -> None:
    module = api()
    summary = report(
        inputs=(
            signal(
                signal_ref="alpha_signal",
                specialist_ref="domain_a",
                observed_at=datetime(
                    2026,
                    7,
                    9,
                    7,
                    30,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                probability_estimate=d("0.620000"),
                confidence_score=d("0.900000"),
            ),
            signal(
                signal_ref="alpha_signal",
                specialist_ref="domain_b",
                observed_at=datetime(2026, 7, 9, 11, 0, tzinfo=UTC),
                probability_estimate=d("0.660000"),
                confidence_score=d("0.800000"),
            ),
            signal(
                signal_ref="alpha_signal",
                specialist_ref="domain_c",
                observed_at=datetime(2026, 7, 9, 11, 45, tzinfo=UTC),
                probability_estimate=d("0.640000"),
                confidence_score=d("0.700000"),
            ),
            signal(
                signal_ref="beta_signal",
                specialist_ref="domain_a",
                observed_at=datetime(2026, 7, 9, 10, 45, tzinfo=UTC),
                probability_estimate=d("0.450000"),
                confidence_score=d("0.650000"),
            ),
            signal(
                signal_ref="beta_signal",
                specialist_ref="domain_b",
                observed_at=datetime(2026, 7, 9, 10, 30, tzinfo=UTC),
                probability_estimate=d("0.620000"),
                confidence_score=d("0.550000"),
            ),
            signal(
                signal_ref="gamma_signal",
                specialist_ref="domain_a",
                observed_at=datetime(2026, 7, 9, 11, 45, tzinfo=UTC),
                probability_estimate=d("0.800000"),
                confidence_score=d("0.900000"),
            ),
        ),
    )

    assert is_dataclass(summary)
    assert type(summary) is module.ResearchStrategySpecialistSignalConsensusDecayReport
    assert summary.generated_at == GENERATED_AT
    assert summary.config_version == (
        "research-strategy-specialist-signal-consensus-decay-report-test-v0"
    )
    assert summary.input_signal_count == d("6.000000")
    assert summary.consensus_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_consensus_decay_score == d("0.806486")
    assert summary.max_probability_dispersion == d("0.170000")
    assert summary.min_freshness_score == d("0.312500")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "specialist_signal_consensus_decay_report_block",
        "consensus_decay_review",
        "specialist_freshness_review",
        "specialist_quorum_review",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64

    assert tuple(row.signal_ref for row in summary.rows) == (
        "gamma_signal",
        "beta_signal",
        "alpha_signal",
    )

    blocked, watched, passed = summary.rows
    assert blocked.status == "block"
    assert blocked.specialist_count == d("1.000000")
    assert blocked.consensus_probability == d("0.800000")
    assert blocked.probability_dispersion == ZERO
    assert blocked.mean_confidence_score == d("0.900000")
    assert blocked.mean_freshness_score == d("0.875000")
    assert blocked.consensus_decay_score == d("0.938750")
    assert blocked.reason_codes == ("specialist_quorum_block",)
    assert len(blocked.derived_validation_digest) == 64

    assert watched.status == "watch"
    assert watched.consensus_probability == d("0.511311")
    assert watched.probability_dispersion == d("0.170000")
    assert watched.mean_confidence_score == d("0.600000")
    assert watched.mean_freshness_score == d("0.312500")
    assert watched.consensus_decay_score == d("0.631625")
    assert watched.reason_codes == (
        "consensus_decay_watch",
        "specialist_freshness_watch",
    )

    assert passed.status == "pass"
    assert passed.consensus_probability == d("0.636741")
    assert passed.probability_dispersion == d("0.040000")
    assert passed.mean_confidence_score == d("0.800000")
    assert passed.mean_freshness_score == d("0.708333")
    assert passed.consensus_decay_score == d("0.849083")
    assert passed.reason_codes == ("specialist_signal_consensus_decay_pass",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["specialist_freshness_watch"] == (
        module.ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount(
            reason_code="specialist_freshness_watch",
            count=d("1.000000"),
            input_ratio=d("0.333333"),
        )
    )


def test_empty_report_is_pass_with_hard_flags_and_decimal_fields() -> None:
    empty = report()

    assert empty.input_signal_count == ZERO
    assert empty.consensus_row_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.mean_consensus_decay_score == ZERO
    assert empty.max_probability_dispersion == ZERO
    assert empty.min_freshness_score == ZERO
    assert empty.status == "pass"
    assert empty.reason_codes == ("specialist_signal_consensus_decay_report_clear",)
    assert empty.rows == ()
    assert empty.reason_code_counts == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(inputs=(signal(), signal(specialist_ref="domain_b"),))
    for value in (empty, populated, *populated.rows, *populated.reason_code_counts):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(("_count", "_score", "_seconds", "_dispersion")):
                assert type(item_value) is Decimal


def test_payload_is_stable_sanitized_decimal_stringed_and_digest_guarded() -> None:
    module = api()
    digest = report(inputs=(signal(), signal(specialist_ref="domain_b"),))
    first_payload = module.research_strategy_specialist_signal_consensus_decay_report_payload(
        digest,
    )
    second_payload = module.research_strategy_specialist_signal_consensus_decay_report_payload(
        report(inputs=(signal(), signal(specialist_ref="domain_b"),)),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == GENERATED_AT.isoformat()
    assert first_payload["input_signal_count"] == "2.000000"
    assert first_payload["rows"][0]["consensus_probability"] == "0.620000"
    assert first_payload["rows"][0]["consensus_decay_score"] == "0.907500"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert int(first_payload["derived_validation_digest"], 16) >= 0
    assert_no_public_numeric_values(first_payload)
    assert module.research_strategy_specialist_signal_consensus_decay_report_payload(
        first_payload,
    ) == first_payload
    json.dumps(first_payload, sort_keys=True)

    public_text = json.dumps(first_payload, sort_keys=True).lower()
    forbidden_public_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "source_url",
        "source_text",
        "://",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    )
    assert not any(fragment in public_text for fragment in forbidden_public_fragments)

    unsigned = dict(first_payload)
    supplied_digest = unsigned.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert supplied_digest == expected_digest

    tampered = dict(first_payload)
    tampered["pass_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            tampered,
        )

    downgraded = dict(first_payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            downgraded,
        )

    unsafe_payload = dict(first_payload)
    unsafe_payload["rows"] = [
        dict(first_payload["rows"][0], signal_ref="raw_market_identifier"),
    ]
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            unsafe_payload,
        )


def test_input_order_does_not_change_rows_rollups_or_digest_layers() -> None:
    module = api()
    inputs = (
        signal(
            signal_ref="beta_signal",
            specialist_ref="domain_b",
            observed_at=GENERATED_AT - timedelta(seconds=5000),
            probability_estimate=d("0.200000"),
            confidence_score=d("0.600000"),
        ),
        signal(
            signal_ref="alpha_signal",
            specialist_ref="domain_b",
            probability_estimate=d("0.700000"),
            confidence_score=d("0.800000"),
        ),
        signal(
            signal_ref="beta_signal",
            specialist_ref="domain_a",
            observed_at=GENERATED_AT - timedelta(seconds=6000),
            probability_estimate=d("0.800000"),
            confidence_score=d("0.700000"),
        ),
        signal(
            signal_ref="alpha_signal",
            specialist_ref="domain_a",
            probability_estimate=d("0.600000"),
            confidence_score=d("0.900000"),
        ),
    )

    forward = report(inputs=inputs)
    reverse = report(inputs=reversed(inputs))
    forward_payload = (
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            forward,
        )
    )
    reverse_payload = (
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            reverse,
        )
    )

    assert forward == reverse
    assert forward_payload == reverse_payload
    assert tuple(row.derived_validation_digest for row in forward.rows) == tuple(
        row.derived_validation_digest for row in reverse.rows
    )


def test_nested_row_tamper_is_not_hidden_by_resigning_only_the_report() -> None:
    module = api()
    payload = module.research_strategy_specialist_signal_consensus_decay_report_payload(
        report(inputs=(signal(), signal(specialist_ref="domain_b"),)),
    )
    tampered = deepcopy(payload)
    tampered["rows"][0]["consensus_probability"] = "0.630000"
    unsigned_report = dict(tampered)
    unsigned_report.pop("derived_validation_digest")
    tampered["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            unsigned_report,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            tampered,
        )


def test_payload_redacts_specialist_identity_and_rejects_credential_labels() -> None:
    module = api()
    specialist_refs = ("desk_delta_identifier", "desk_epsilon_identifier")
    payload = module.research_strategy_specialist_signal_consensus_decay_report_payload(
        report(
            inputs=tuple(
                signal(specialist_ref=specialist_ref)
                for specialist_ref in specialist_refs
            ),
        ),
    )
    encoded = json.dumps(payload, sort_keys=True)
    assert "specialist_ref" not in encoded
    assert all(specialist_ref not in encoded for specialist_ref in specialist_refs)

    unsafe = deepcopy(payload)
    unsafe["config_version"] = "api_key_reference"
    unsafe["config"]["config_version"] = "api_key_reference"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            payload_with_recomputed_digests(unsafe),
        )


def test_payload_rejects_fully_resigned_derived_field_forgery() -> None:
    module = api()
    payload = module.research_strategy_specialist_signal_consensus_decay_report_payload(
        report(inputs=(signal(), signal(specialist_ref="domain_b"),)),
    )

    forged_count = payload_with_recomputed_digests(
        {**payload, "pass_count": "0.000000"},
    )
    with pytest.raises(ValueError, match="pass_count must match rows"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            forged_count,
        )

    forged_status = payload_with_recomputed_digests(
        {**payload, "status": "watch"},
    )
    with pytest.raises(ValueError, match="status must match rows"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            forged_status,
        )

    forged_reasons = payload_with_recomputed_digests(
        {
            **payload,
            "reason_codes": [
                "specialist_signal_consensus_decay_report_watch",
            ],
        },
    )
    with pytest.raises(ValueError, match="reason_codes must match rows"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            forged_reasons,
        )

    forged_score = deepcopy(payload)
    forged_score["rows"][0]["consensus_decay_score"] = "0.100000"
    forged_score["mean_consensus_decay_score"] = "0.100000"
    forged_score = payload_with_recomputed_digests(forged_score)
    with pytest.raises(
        ValueError,
        match="consensus_decay_score must match row components",
    ):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            forged_score,
        )

    forged_row_status = deepcopy(payload)
    forged_row_status["rows"][0]["status"] = "watch"
    forged_row_status = payload_with_recomputed_digests(forged_row_status)
    with pytest.raises(ValueError, match="status must match reason_codes"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            forged_row_status,
        )

    forged_reason_count = deepcopy(payload)
    forged_reason_count["reason_code_counts"][0]["count"] = "2.000000"
    forged_reason_count = payload_with_recomputed_digests(forged_reason_count)
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            forged_reason_count,
        )


def test_resigned_payload_rederives_row_status_and_reasons_from_config() -> None:
    module = api()
    payload = module.research_strategy_specialist_signal_consensus_decay_report_payload(
        report(inputs=(signal(), signal(specialist_ref="domain_b"),)),
    )

    forged = deepcopy(payload)
    forged["rows"][0]["status"] = "watch"
    forged["rows"][0]["reason_codes"] = ["consensus_decay_watch"]
    forged["pass_count"] = "0.000000"
    forged["watch_count"] = "1.000000"
    forged["status"] = "watch"
    forged["reason_codes"] = [
        "specialist_signal_consensus_decay_report_watch",
        "consensus_decay_review",
    ]
    forged["reason_code_counts"] = [
        {
            "reason_code": "consensus_decay_watch",
            "count": "1.000000",
            "input_ratio": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]

    with pytest.raises(ValueError, match="status must match config"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            payload_with_recomputed_digests(forged),
        )


def test_custom_threshold_config_round_trips_as_authoritative_payload_state() -> None:
    module = api()
    custom_config = config(
        consensus_pass_floor=d("0.950000"),
        consensus_watch_floor=d("0.800000"),
    )
    summary = report(
        inputs=(signal(), signal(specialist_ref="domain_b")),
        cfg=custom_config,
    )
    payload = module.research_strategy_specialist_signal_consensus_decay_report_payload(
        summary,
    )

    assert summary.rows[0].status == "watch"
    assert summary.rows[0].reason_codes == ("consensus_decay_watch",)
    assert payload["config"]["consensus_pass_floor"] == "0.950000"
    assert payload["config"]["consensus_watch_floor"] == "0.800000"
    assert module.research_strategy_specialist_signal_consensus_decay_report_payload(
        payload,
    ) == payload


def test_resigned_payload_rejects_impossible_row_source_summaries() -> None:
    module = api()

    stale_payload = module.research_strategy_specialist_signal_consensus_decay_report_payload(
        report(
            inputs=(
                signal(
                    observed_at=GENERATED_AT - timedelta(seconds=7200),
                ),
            ),
        ),
    )
    stale_forgery = deepcopy(stale_payload)
    stale_forgery["rows"][0]["mean_freshness_score"] = "0.500000"
    stale_forgery["rows"][0]["consensus_decay_score"] = "0.845000"
    stale_forgery["rows"][0]["reason_codes"] = ["specialist_quorum_block"]
    stale_forgery["mean_consensus_decay_score"] = "0.845000"
    stale_forgery["min_freshness_score"] = "0.500000"
    stale_forgery["reason_codes"] = [
        "specialist_signal_consensus_decay_report_block",
        "specialist_quorum_review",
    ]
    stale_forgery["reason_code_counts"] = [
        {
            "reason_code": "specialist_quorum_block",
            "count": "1.000000",
            "input_ratio": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    with pytest.raises(ValueError, match="mean_freshness_score.*observed_at"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            payload_with_recomputed_digests(stale_forgery),
        )

    singleton_payload = (
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            report(inputs=(signal(),)),
        )
    )
    dispersion_forgery = deepcopy(singleton_payload)
    dispersion_forgery["rows"][0]["probability_dispersion"] = "0.100000"
    dispersion_forgery["rows"][0]["consensus_decay_score"] = "0.862500"
    dispersion_forgery["mean_consensus_decay_score"] = "0.862500"
    dispersion_forgery["max_probability_dispersion"] = "0.100000"
    with pytest.raises(ValueError, match="probability_dispersion.*single specialist"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            payload_with_recomputed_digests(dispersion_forgery),
        )


def test_standalone_single_specialist_row_requires_zero_dispersion() -> None:
    row = report(inputs=(signal(),)).rows[0]

    with pytest.raises(ValueError, match="probability_dispersion.*single specialist"):
        replace(
            row,
            probability_dispersion=d("0.100000"),
            consensus_decay_score=d("0.862500"),
            derived_validation_digest="",
        )


def test_payload_requires_exact_report_row_and_reason_count_schemas() -> None:
    module = api()
    payload = module.research_strategy_specialist_signal_consensus_decay_report_payload(
        report(inputs=(signal(), signal(specialist_ref="domain_b"),)),
    )

    assert set(payload) == {
        "generated_at",
        "config_version",
        "config",
        "input_signal_count",
        "consensus_row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_consensus_decay_score",
        "max_probability_dispersion",
        "min_freshness_score",
        "status",
        "reason_codes",
        "rows",
        "reason_code_counts",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert set(payload["config"]) == {
        "config_version",
        "consensus_pass_floor",
        "consensus_watch_floor",
        "freshness_watch_floor",
        "freshness_block_floor",
        "dispersion_watch_ceiling",
        "dispersion_block_ceiling",
        "stale_signal_block_seconds",
        "minimum_specialist_count",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert set(payload["rows"][0]) == {
        "signal_ref",
        "observed_at",
        "specialist_count",
        "consensus_probability",
        "probability_dispersion",
        "mean_confidence_score",
        "mean_freshness_score",
        "consensus_decay_score",
        "status",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert set(payload["reason_code_counts"][0]) == {
        "reason_code",
        "count",
        "input_ratio",
        "paper_only",
        "report_only",
        "readonly",
    }

    extra_report_field = payload_with_recomputed_digests(
        {**payload, "unexpected_field": "unexpected"},
    )
    with pytest.raises(ValueError, match="report payload fields"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            extra_report_field,
        )

    missing_row_field = deepcopy(payload)
    missing_row_field["rows"][0].pop("mean_freshness_score")
    missing_row_field = payload_with_recomputed_digests(missing_row_field)
    with pytest.raises(ValueError, match="row payload fields"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            missing_row_field,
        )

    extra_reason_count_field = deepcopy(payload)
    extra_reason_count_field["reason_code_counts"][0]["unexpected_field"] = "unexpected"
    extra_reason_count_field = payload_with_recomputed_digests(extra_reason_count_field)
    with pytest.raises(ValueError, match="reason code count payload fields"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            extra_reason_count_field,
        )

    extra_config_field = deepcopy(payload)
    extra_config_field["config"]["unexpected_field"] = "unexpected"
    extra_config_field = payload_with_recomputed_digests(extra_config_field)
    with pytest.raises(ValueError, match="config payload fields"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            extra_config_field,
        )

    reordered_report = {
        key: payload[key]
        for key in reversed(tuple(payload))
    }
    reordered_report = payload_with_recomputed_digests(reordered_report)
    with pytest.raises(ValueError, match="report payload fields"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            reordered_report,
        )

    reordered_row = deepcopy(payload)
    reordered_row["rows"][0] = {
        key: reordered_row["rows"][0][key]
        for key in reversed(tuple(reordered_row["rows"][0]))
    }
    reordered_row = payload_with_recomputed_digests(reordered_row)
    with pytest.raises(ValueError, match="row payload fields"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            reordered_row,
        )

    reordered_config = deepcopy(payload)
    reordered_config["config"] = {
        key: reordered_config["config"][key]
        for key in reversed(tuple(reordered_config["config"]))
    }
    reordered_config = payload_with_recomputed_digests(reordered_config)
    with pytest.raises(ValueError, match="config payload fields"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            reordered_config,
        )


@pytest.mark.parametrize(
    "mutate",
    (
        lambda payload: payload.__setitem__(
            "input_signal_count",
            d("2.000000"),
        ),
        lambda payload: payload.__setitem__("generated_at", GENERATED_AT),
        lambda payload: payload.__setitem__("rows", tuple(payload["rows"])),
        lambda payload: payload["rows"][0].__setitem__(
            "reason_codes",
            tuple(payload["rows"][0]["reason_codes"]),
        ),
        lambda payload: payload.__setitem__(
            "config",
            type("ConfigPayloadSubclass", (dict,), {})(payload["config"]),
        ),
        lambda payload: payload["rows"].__setitem__(
            0,
            type("RowPayloadSubclass", (dict,), {})(payload["rows"][0]),
        ),
        lambda payload: payload.__setitem__(
            "reason_code_counts",
            type("ReasonCountsListSubclass", (list,), {})(
                payload["reason_code_counts"],
            ),
        ),
    ),
)
def test_mapping_payload_rejects_non_json_exact_types(mutate) -> None:
    module = api()
    payload = module.research_strategy_specialist_signal_consensus_decay_report_payload(
        report(inputs=(signal(), signal(specialist_ref="domain_b"),)),
    )
    mutate(payload)

    with pytest.raises(ValueError, match="exact JSON types"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            payload,
        )


@pytest.mark.parametrize(
    ("target", "expected_error"),
    (
        ("report", "report payload fields"),
        ("row", "row payload fields"),
        ("scalar", "exact JSON types"),
    ),
)
def test_payload_schema_is_checked_before_recursive_value_walks(
    target: str,
    expected_error: str,
) -> None:
    module = api()
    payload = module.research_strategy_specialist_signal_consensus_decay_report_payload(
        report(inputs=(signal(), signal(specialist_ref="domain_b"),)),
    )
    nested: object = "leaf"
    for _ in range(1500):
        nested = [nested]
    if target == "report":
        payload["extension"] = nested
    elif target == "row":
        payload["rows"][0]["extension"] = nested
    else:
        payload["config_version"] = nested

    with pytest.raises(ValueError, match=expected_error):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            payload,
        )


def test_raw_decimal_bounds_signed_zero_and_derived_values_are_rejected() -> None:
    module = api()
    summary = report(inputs=(signal(), signal(specialist_ref="domain_b"),))
    row = summary.rows[0]

    with pytest.raises(ValueError, match="probability_estimate must be between 0 and 1"):
        signal(probability_estimate=d("1.0000004"))
    with pytest.raises(ValueError, match="confidence_score must be between 0 and 1"):
        signal(confidence_score=d("-0.0000004"))
    with pytest.raises(ValueError, match="probability_estimate must not use signed zero"):
        signal(probability_estimate=d("-0.000000"))
    for non_finite in ("NaN", "sNaN", "Infinity", "-Infinity"):
        with pytest.raises(ValueError, match="probability_estimate must be finite"):
            signal(probability_estimate=d(non_finite))
    with pytest.raises(ValueError, match="input_signal_count must not use signed zero"):
        replace(
            report(),
            input_signal_count=d("-0.000000"),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="specialist_count must be a whole number"):
        replace(
            row,
            specialist_count=d("2.500000"),
            derived_validation_digest="",
        )
    with pytest.raises(
        ValueError,
        match="consensus_decay_score must match row components",
    ):
        replace(
            row,
            consensus_decay_score=d("0.100000"),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="pass rows must use the pass reason"):
        replace(row, reason_codes=(), derived_validation_digest="")
    with pytest.raises(ValueError, match="input_signal_count must match rows"):
        replace(
            summary,
            input_signal_count=d("3.000000"),
            derived_validation_digest="",
        )

    signed_zero_payload = deepcopy(
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            summary,
        ),
    )
    signed_zero_payload["rows"][0]["probability_dispersion"] = "-0.000000"
    signed_zero_payload["max_probability_dispersion"] = "-0.000000"
    signed_zero_payload = payload_with_recomputed_digests(signed_zero_payload)
    with pytest.raises(ValueError, match="probability_dispersion must not use signed zero"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            signed_zero_payload,
        )


def test_auto_digest_sentinel_requires_an_exact_empty_string() -> None:
    summary = report(inputs=(signal(), signal(specialist_ref="domain_b"),))

    cyclic_digest: list[object] = []
    cyclic_digest.append(cyclic_digest)
    for invalid_digest in (None, False, 0, b"", cyclic_digest):
        with pytest.raises(ValueError, match="derived_validation_digest.*sha256"):
            replace(
                summary.rows[0],
                derived_validation_digest=invalid_digest,
            )
        with pytest.raises(ValueError, match="derived_validation_digest.*sha256"):
            replace(
                summary,
                derived_validation_digest=invalid_digest,
            )


def test_frozen_exact_dataclasses_decimal_only_and_validation_guards() -> None:
    module = api()
    digest = report(inputs=(signal(), signal(specialist_ref="domain_b"),))

    assert is_dataclass(module.ResearchStrategySpecialistSignalConsensusDecayConfig)
    assert is_dataclass(module.ResearchStrategySpecialistSignalConsensusDecayInput)
    assert is_dataclass(module.ResearchStrategySpecialistSignalConsensusDecayRow)
    assert is_dataclass(
        module.ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount,
    )
    assert is_dataclass(module.ResearchStrategySpecialistSignalConsensusDecayReport)
    for dataclass_type in (
        module.ResearchStrategySpecialistSignalConsensusDecayConfig,
        module.ResearchStrategySpecialistSignalConsensusDecayInput,
        module.ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount,
        module.ResearchStrategySpecialistSignalConsensusDecayRow,
        module.ResearchStrategySpecialistSignalConsensusDecayReport,
    ):
        assert dataclass_type.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        digest.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.rows[0].consensus_decay_score = d("0.100000")  # type: ignore[misc]
    for dataclass_type in (
        module.ResearchStrategySpecialistSignalConsensusDecayConfig,
        module.ResearchStrategySpecialistSignalConsensusDecayInput,
        module.ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount,
        module.ResearchStrategySpecialistSignalConsensusDecayRow,
        module.ResearchStrategySpecialistSignalConsensusDecayReport,
    ):
        with pytest.raises(TypeError, match="may not be subclassed"):
            type("ForbiddenSubclass", (dataclass_type,), {})
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(digest, report_only=False)
    with pytest.raises(ValueError, match="probability_estimate"):
        signal(probability_estimate=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="confidence_score"):
        signal(confidence_score=_DecimalSubclass("0.800000"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 9, 11, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        signal(observed_at=datetime(2026, 7, 9, 11, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        signal(observed_at=datetime(2026, 7, 9, 11, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at.*valid timezone offset"):
        signal(observed_at=datetime(2026, 7, 9, 11, 0, tzinfo=_InvalidOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at.*valid timezone offset"):
        signal(
            observed_at=datetime(
                1,
                1,
                1,
                tzinfo=timezone(timedelta(hours=1)),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(inputs=(signal(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="unique"):
        report(inputs=(signal(), signal()))
    with pytest.raises(ValueError, match="consensus_pass_floor"):
        config(consensus_pass_floor=d("0.500000"))
    with pytest.raises(ValueError, match="consensus_pass_floor.*exceed"):
        config(consensus_pass_floor=d("0.550000"))
    with pytest.raises(ValueError, match="freshness_watch_floor.*exceed"):
        config(freshness_watch_floor=d("0.250000"))
    with pytest.raises(ValueError, match="dispersion_block_ceiling"):
        config(dispersion_block_ceiling=d("0.100000"))
    with pytest.raises(ValueError, match="unsafe"):
        signal(signal_ref="candidate_reference")
    for noncanonical_signal_ref in ("alpha\nsignal", "α_signal", "a" * 129):
        with pytest.raises(ValueError, match="signal_ref"):
            signal(signal_ref=noncanonical_signal_ref)
    with pytest.raises(ValueError, match="supported status"):
        module.ResearchStrategySpecialistSignalConsensusDecayRow(
            signal_ref="manual_signal",
            observed_at=GENERATED_AT,
            specialist_count=d("2.000000"),
            consensus_probability=d("0.500000"),
            probability_dispersion=d("0.100000"),
            mean_confidence_score=d("0.700000"),
            mean_freshness_score=d("0.700000"),
            consensus_decay_score=d("0.700000"),
            status="caution",
            reason_codes=("consensus_decay_watch",),
        )


def test_builder_revalidates_low_level_tampered_config_and_inputs() -> None:
    tampered_config = config()
    object.__setattr__(
        tampered_config,
        "stale_signal_block_seconds",
        d("NaN"),
    )
    with pytest.raises(ValueError, match="stale_signal_block_seconds must be finite"):
        report(inputs=(signal(),), cfg=tampered_config)

    tampered_decimal = signal()
    object.__setattr__(tampered_decimal, "probability_estimate", d("NaN"))
    with pytest.raises(ValueError, match="probability_estimate must be finite"):
        report(inputs=(tampered_decimal,))

    tampered_reference = signal()
    object.__setattr__(tampered_reference, "specialist_ref", "secret_token")
    with pytest.raises(ValueError, match="unsafe value in specialist_ref"):
        report(inputs=(tampered_reference,))


def test_payload_revalidates_low_level_canonical_dataclass_state() -> None:
    module = api()

    tampered_report_time = report(
        inputs=(signal(), signal(specialist_ref="domain_b")),
    )
    object.__setattr__(
        tampered_report_time,
        "generated_at",
        tampered_report_time.generated_at.astimezone(
            timezone(timedelta(hours=1)),
        ),
    )
    with pytest.raises(ValueError, match="generated_at must be canonical UTC"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            tampered_report_time,
        )

    tampered_row_time = report(
        inputs=(signal(), signal(specialist_ref="domain_b")),
    )
    object.__setattr__(
        tampered_row_time.rows[0],
        "observed_at",
        tampered_row_time.rows[0].observed_at.astimezone(
            timezone(timedelta(hours=-3)),
        ),
    )
    with pytest.raises(ValueError, match="observed_at must be canonical UTC"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            tampered_row_time,
        )

    tampered_row_reasons = report(
        inputs=(signal(), signal(specialist_ref="domain_b")),
    )
    object.__setattr__(
        tampered_row_reasons.rows[0],
        "reason_codes",
        list(tampered_row_reasons.rows[0].reason_codes),
    )
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            tampered_row_reasons,
        )


def test_boundaries_reject_low_level_noncanonical_decimal_storage() -> None:
    module = api()

    tampered_config = config()
    object.__setattr__(tampered_config, "consensus_pass_floor", d("0.75"))
    with pytest.raises(ValueError, match="consensus_pass_floor.*stored canonically"):
        report(inputs=(signal(),), cfg=tampered_config)

    tampered_input = signal()
    object.__setattr__(tampered_input, "probability_estimate", d("0.62"))
    with pytest.raises(ValueError, match="probability_estimate.*stored canonically"):
        report(inputs=(tampered_input,))

    tampered_row = report(
        inputs=(signal(), signal(specialist_ref="domain_b")),
    )
    object.__setattr__(tampered_row.rows[0], "consensus_probability", d("0.62"))
    with pytest.raises(ValueError, match="consensus_probability.*stored canonically"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            tampered_row,
        )

    tampered_report = report(
        inputs=(signal(), signal(specialist_ref="domain_b")),
    )
    object.__setattr__(tampered_report, "input_signal_count", d("2"))
    with pytest.raises(ValueError, match="input_signal_count.*stored canonically"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            tampered_report,
        )


def test_decimal_arithmetic_uses_fixed_local_context() -> None:
    module = api()
    def build_case():
        case_config = config()
        case_inputs = (
            signal(
                specialist_ref="domain_a",
                probability_estimate=d("0.613579"),
                confidence_score=d("0.987654"),
            ),
            signal(
                specialist_ref="domain_b",
                observed_at=GENERATED_AT - timedelta(seconds=2345),
                probability_estimate=d("0.698765"),
                confidence_score=d("0.876543"),
            ),
            signal(
                specialist_ref="domain_c",
                observed_at=GENERATED_AT - timedelta(seconds=4567),
                probability_estimate=d("0.576543"),
                confidence_score=d("0.765432"),
            ),
        )
        case_report = report(inputs=case_inputs, cfg=case_config)
        case_payload = (
            module.research_strategy_specialist_signal_consensus_decay_report_payload(
                case_report,
            )
        )
        validated_payload = (
            module.research_strategy_specialist_signal_consensus_decay_report_payload(
                case_payload,
            )
        )
        return case_config, case_report, validated_payload

    expected_config, expected, expected_payload = build_case()
    hostile_context = Context(
        prec=3,
        rounding=ROUND_DOWN,
        Emin=-9,
        Emax=9,
    )
    hostile_context.traps[Inexact] = True
    hostile_context.traps[Rounded] = True
    with localcontext(hostile_context) as caller_context:
        caller_context.clear_flags()
        actual_config, actual, actual_payload = build_case()
        assert not any(caller_context.flags.values())

    assert actual_config == expected_config
    assert actual == expected
    assert actual_payload == expected_payload
    assert module._quantize(d("-0.0000004")) == ZERO
    assert str(module._quantize(d("-0.0000004"))) == "0.000000"


def test_large_specialist_count_ignores_hostile_ambient_decimal_context() -> None:
    module = api()
    inputs = tuple(
        signal(specialist_ref=f"domain_{index:04d}")
        for index in range(1001)
    )
    hostile_context = Context(
        prec=3,
        rounding=ROUND_DOWN,
        Emin=-9,
        Emax=9,
    )
    hostile_context.traps[Inexact] = True
    hostile_context.traps[Rounded] = True

    with localcontext(hostile_context) as caller_context:
        caller_context.clear_flags()
        summary = report(inputs=inputs)
        payload = (
            module.research_strategy_specialist_signal_consensus_decay_report_payload(
                summary,
            )
        )
        assert not any(caller_context.flags.values())

    assert summary.input_signal_count == d("1001.000000")
    assert summary.rows[0].specialist_count == d("1001.000000")
    assert payload["input_signal_count"] == "1001.000000"
    assert payload["rows"][0]["specialist_count"] == "1001.000000"


def test_resigned_payload_rejects_noncanonical_rows_and_future_observations() -> None:
    module = api()
    payload = module.research_strategy_specialist_signal_consensus_decay_report_payload(
        report(
            inputs=(
                signal(signal_ref="alpha_signal", specialist_ref="domain_a"),
                signal(signal_ref="alpha_signal", specialist_ref="domain_b"),
                signal(signal_ref="beta_signal", specialist_ref="domain_a"),
            ),
        ),
    )
    assert len(payload["rows"]) == 2

    reordered_rows = deepcopy(payload)
    reordered_rows["rows"].reverse()
    reordered_rows = payload_with_recomputed_digests(reordered_rows)
    with pytest.raises(ValueError, match="rows must be sorted"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            reordered_rows,
        )

    future_observation = deepcopy(payload)
    future_observation["rows"][0]["observed_at"] = (
        GENERATED_AT + timedelta(microseconds=1)
    ).isoformat()
    future_observation = payload_with_recomputed_digests(future_observation)
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            future_observation,
        )


def test_resigned_payload_rejects_duplicate_signal_rows() -> None:
    module = api()
    payload = module.research_strategy_specialist_signal_consensus_decay_report_payload(
        report(inputs=(signal(), signal(specialist_ref="domain_b"),)),
    )
    duplicated = deepcopy(payload)
    duplicated["rows"] = [
        deepcopy(payload["rows"][0]),
        deepcopy(payload["rows"][0]),
    ]
    duplicated["input_signal_count"] = "4.000000"
    duplicated["consensus_row_count"] = "2.000000"
    duplicated["pass_count"] = "2.000000"
    duplicated["reason_code_counts"][0]["count"] = "2.000000"

    with pytest.raises(ValueError, match="duplicate signal_ref"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            payload_with_recomputed_digests(duplicated),
        )


def test_resigned_payload_requires_canonical_decimal_and_utc_strings() -> None:
    module = api()
    payload = module.research_strategy_specialist_signal_consensus_decay_report_payload(
        report(inputs=(signal(), signal(specialist_ref="domain_b"),)),
    )

    noncanonical_decimal = deepcopy(payload)
    noncanonical_decimal["input_signal_count"] = "2"
    noncanonical_decimal = payload_with_recomputed_digests(noncanonical_decimal)
    with pytest.raises(ValueError, match="input_signal_count.*canonical"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            noncanonical_decimal,
        )

    noncanonical_row_decimal = deepcopy(payload)
    noncanonical_row_decimal["rows"][0]["consensus_probability"] = "0.62"
    noncanonical_row_decimal = payload_with_recomputed_digests(noncanonical_row_decimal)
    with pytest.raises(ValueError, match="consensus_probability.*canonical"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            noncanonical_row_decimal,
        )

    noncanonical_datetime = deepcopy(payload)
    noncanonical_datetime["generated_at"] = "2026-07-09T08:00:00-04:00"
    noncanonical_datetime = payload_with_recomputed_digests(noncanonical_datetime)
    with pytest.raises(ValueError, match="generated_at.*canonical UTC"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            noncanonical_datetime,
        )

    noncanonical_zulu = deepcopy(payload)
    noncanonical_zulu["generated_at"] = "2026-07-09T12:00:00Z"
    noncanonical_zulu = payload_with_recomputed_digests(noncanonical_zulu)
    with pytest.raises(ValueError, match="generated_at.*canonical UTC"):
        module.research_strategy_specialist_signal_consensus_decay_report_payload(
            noncanonical_zulu,
        )


def test_public_dataclasses_are_slotted_and_statuses_are_exact_strings() -> None:
    module = api()
    summary = report(inputs=(signal(), signal(specialist_ref="domain_b"),))
    public_dataclasses = (
        module.ResearchStrategySpecialistSignalConsensusDecayConfig,
        module.ResearchStrategySpecialistSignalConsensusDecayInput,
        module.ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount,
        module.ResearchStrategySpecialistSignalConsensusDecayRow,
        module.ResearchStrategySpecialistSignalConsensusDecayReport,
    )
    instances = (
        config(),
        signal(),
        summary.reason_code_counts[0],
        summary.rows[0],
        summary,
    )
    for public_dataclass, instance in zip(public_dataclasses, instances, strict=True):
        assert getattr(public_dataclass, "__final__", False) is True
        assert hasattr(public_dataclass, "__slots__")
        assert "__dict__" not in public_dataclass.__slots__
        assert not hasattr(instance, "__dict__")

    with pytest.raises(ValueError, match="status must be a supported status"):
        replace(
            summary.rows[0],
            status=_StatusSubclass(summary.rows[0].status),
            derived_validation_digest="",
        )


def test_public_dataclass_collection_fields_require_exact_tuples() -> None:
    summary = report(inputs=(signal(), signal(specialist_ref="domain_b"),))

    with pytest.raises(ValueError, match="rows must be a tuple"):
        replace(
            summary,
            rows=list(summary.rows),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="reason_code_counts must be a tuple"):
        replace(
            summary,
            reason_code_counts=list(summary.reason_code_counts),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(
            summary.rows[0],
            reason_codes=list(summary.rows[0].reason_codes),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(
            summary,
            reason_codes=type("ReasonCodeTupleSubclass", (tuple,), {})(
                summary.reason_codes,
            ),
            derived_validation_digest="",
        )


def test_row_and_reason_count_require_row_reason_code_namespace() -> None:
    module = api()
    summary = report(inputs=(signal(), signal(specialist_ref="domain_b"),))
    report_reason = "specialist_signal_consensus_decay_report_block"

    with pytest.raises(ValueError, match="row reason code"):
        replace(
            summary.rows[0],
            status="block",
            reason_codes=(report_reason,),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="row reason code"):
        module.ResearchStrategySpecialistSignalConsensusDecayReasonCodeCount(
            reason_code=report_reason,
            count=d("1.000000"),
            input_ratio=d("1.000000"),
        )


def test_source_is_report_only_and_excludes_io_execution_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))

    forbidden_import_roots = {
        "aiohttp",
        "boto3",
        "dbm",
        "pickle",
        "pymongo",
        "redis",
        "shelve",
        "sqlite3",
        "os",
        "socket",
        "subprocess",
        "requests",
        "urllib",
        "httpx",
        "web3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "exec", "eval", "compile"}
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "connect",
                    "execute",
                    "request",
                    "send",
                    "sign",
                    "submit",
                    "cancel",
                    "commit",
                    "connect",
                    "execute",
                    "insert",
                    "mkdir",
                    "publish",
                    "save",
                    "touch",
                    "unlink",
                    "write",
                    "write_bytes",
                    "write_text",
                }

    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    assert ".total_seconds(" not in source
    forbidden_terms = (
        "private_key",
        "wallet",
        "place_order",
        "submit_order",
        "cancel_order",
        "execute_order",
        "execute_trade",
        "live_trading",
        "position_size",
        "api_key",
        "authorization",
        "database_url",
        "persist_report",
    )
    assert not any(term in source for term in forbidden_terms)
