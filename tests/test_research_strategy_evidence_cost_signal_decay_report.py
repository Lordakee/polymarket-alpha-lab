from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_UP, localcontext
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab import (
    research_strategy_evidence_cost_signal_decay_report as module,
)


class _DecimalSubclass(Decimal):
    pass


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
REPORT_SCHEMA = tuple(
    field.name
    for field in fields(module.ResearchStrategyEvidenceCostSignalDecayReport)
)
ROW_SCHEMA = tuple(
    field.name for field in fields(module.ResearchStrategyEvidenceCostSignalDecayRow)
)
REASON_CODE_COUNT_SCHEMA = tuple(
    field.name
    for field in fields(
        module.ResearchStrategyEvidenceCostSignalDecayReasonCodeCount,
    )
)


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(
    candidate_id: str = "raw-candidate-alpha",
    *,
    evidence_channel: str = "primary-analysis",
    signal_strength: Decimal = Decimal("0.900000"),
    evidence_cost: Decimal = Decimal("5.000000"),
    observed_delta: timedelta = timedelta(minutes=10),
    **overrides: object,
) -> module.ResearchStrategyEvidenceCostSignalDecayInput:
    values: dict[str, object] = {
        "candidate_id": candidate_id,
        "evidence_channel": evidence_channel,
        "signal_strength": signal_strength,
        "evidence_cost": evidence_cost,
        "observed_at": GENERATED_AT - observed_delta,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchStrategyEvidenceCostSignalDecayInput(**values)


def build_report(
    rows: list[module.ResearchStrategyEvidenceCostSignalDecayInput],
) -> module.ResearchStrategyEvidenceCostSignalDecayReport:
    return module.build_research_strategy_evidence_cost_signal_decay_report(
        rows,
        config=module.ResearchStrategyEvidenceCostSignalDecayConfig(),
        generated_at=GENERATED_AT,
    )


def walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if isinstance(value, dict):
        for key, item in value.items():
            values.extend(walk_values(key))
            values.extend(walk_values(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            values.extend(walk_values(item))
    return tuple(values)


def payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(payload_keys(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            keys.extend(payload_keys(item))
    return tuple(keys)


def mutable_payload(
    report: module.ResearchStrategyEvidenceCostSignalDecayReport,
) -> dict[str, Any]:
    return json.loads(json.dumps(report.payload, sort_keys=True))


def resign_payload(payload: dict[str, Any]) -> None:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    payload["derived_validation_digest"] = hashlib.sha256(
        encoded.encode("utf-8"),
    ).hexdigest()


def test_report_rolls_up_pass_watch_and_block_rows_with_deterministic_digest() -> None:
    pass_rows = [
        evidence("raw-candidate-pass", evidence_channel="primary-analysis"),
        evidence(
            "raw-candidate-pass",
            evidence_channel="secondary-review",
            signal_strength=d("0.850000"),
            evidence_cost=d("4.000000"),
            observed_delta=timedelta(minutes=20),
        ),
    ]
    watch_rows = [
        evidence(
            "raw-candidate-watch",
            evidence_channel="primary-analysis",
            signal_strength=d("0.560000"),
            observed_delta=timedelta(hours=1),
        ),
        evidence(
            "raw-candidate-watch",
            evidence_channel="secondary-review",
            signal_strength=d("0.520000"),
            observed_delta=timedelta(hours=2),
        ),
    ]
    block_rows = [
        evidence(
            "raw-candidate-block",
            evidence_channel="primary-analysis",
            signal_strength=d("0.950000"),
            evidence_cost=d("125.000000"),
        ),
        evidence(
            "raw-candidate-block",
            evidence_channel="secondary-review",
            signal_strength=d("0.920000"),
            evidence_cost=d("10.000000"),
        ),
    ]

    report = build_report([*watch_rows, *pass_rows, *block_rows])
    repeated = build_report([*block_rows, *watch_rows, *pass_rows])

    assert report == repeated
    assert report.status == "block"
    assert report.candidate_count == d("3.000000")
    assert report.evidence_count == d("6.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert report.reason_codes == (
        "strategy_evidence_cost_signal_decay_block",
        "strategy_evidence_cost_signal_decay_high_cost",
        "strategy_evidence_cost_signal_decay_watch",
        "strategy_evidence_cost_signal_decay_weak_signal",
        "strategy_evidence_cost_signal_decay_pass",
    )
    assert report.reason_code_counts[0].reason_code == (
        "strategy_evidence_cost_signal_decay_block"
    )
    assert len(report.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in report.derived_validation_digest
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_frozen_json_safe_decimal_only_and_hides_raw_identifiers() -> None:
    report = build_report(
        [
            evidence("raw-candidate-secret", evidence_channel="primary-analysis"),
            evidence(
                "raw-candidate-secret",
                evidence_channel="secondary-review",
                signal_strength=d("0.800000"),
            ),
        ],
    )

    payload = module.research_strategy_evidence_cost_signal_decay_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["total_evidence_cost"] == "10.000000"
    assert payload["rows"][0]["signal_hash"].startswith("sha256:")
    assert "raw-candidate-secret" not in encoded
    assert "candidate_id" not in payload_keys(payload)
    assert "market_id" not in payload_keys(payload)
    assert "market_slug" not in payload_keys(payload)
    assert "question" not in payload_keys(payload)
    assert "source_url" not in payload_keys(payload)
    assert "source_text" not in payload_keys(payload)
    assert "wallet" not in encoded
    assert "order" not in encoded
    assert "trade" not in encoded
    assert "recommendation" not in encoded
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert not any(type(value) is float for value in walk_values(payload))

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["candidate_count"] = "9.000000"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]


def test_empty_input_blocks_without_empty_status() -> None:
    report = build_report([])

    assert report.status == "block"
    assert report.candidate_count == d("0.000000")
    assert report.evidence_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "strategy_evidence_cost_signal_decay_block",
        "strategy_evidence_cost_signal_decay_empty",
    )


def test_validation_is_strict_frozen_digest_backed_and_paper_only() -> None:
    with pytest.raises(ValueError, match="signal_strength"):
        evidence(signal_strength=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="signal_strength"):
        evidence(signal_strength=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="evidence_cost"):
        evidence(evidence_cost=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(evidence(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(evidence(), readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_strategy_evidence_cost_signal_decay_report(
            [evidence()],
            config=module.ResearchStrategyEvidenceCostSignalDecayConfig(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )

    report = build_report(
        [
            evidence("raw-candidate-digest", evidence_channel="primary-analysis"),
            evidence("raw-candidate-digest", evidence_channel="secondary-review"),
            evidence("raw-candidate-second", evidence_channel="primary-analysis"),
            evidence("raw-candidate-second", evidence_channel="secondary-review"),
        ],
    )
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=tuple(reversed(report.rows)), derived_validation_digest="")


def test_decimal_rules_use_fixed_context_and_raw_bounds() -> None:
    rows = [
        evidence(
            "raw-candidate-context",
            evidence_channel="primary-analysis",
            signal_strength=d("0.999999"),
            evidence_cost=d("33.333333"),
        ),
        evidence(
            "raw-candidate-context",
            evidence_channel="secondary-review",
            signal_strength=d("0.999998"),
            evidence_cost=d("33.333334"),
        ),
        evidence(
            "raw-candidate-context",
            evidence_channel="tertiary-review",
            signal_strength=d("0.000001"),
            evidence_cost=d("33.333335"),
        ),
    ]
    baseline = build_report(rows)

    with localcontext() as ambient:
        ambient.prec = 6
        ambient.rounding = ROUND_UP
        constrained = build_report(rows)

    assert constrained == baseline

    with pytest.raises(ValueError, match="signal_strength must be between 0 and 1"):
        evidence(signal_strength=d("1.0000004"))
    with pytest.raises(ValueError, match="evidence_cost must be nonnegative"):
        evidence(evidence_cost=d("-0.0000004"))
    with pytest.raises(ValueError, match="signal_strength must not be signed zero"):
        evidence(signal_strength=d("-0.000000"))
    with pytest.raises(ValueError, match="evidence_cost must not be signed zero"):
        evidence(evidence_cost=d("-0.000000"))
    for non_finite in ("NaN", "sNaN", "Infinity", "-Infinity"):
        with pytest.raises(ValueError, match="signal_strength must be finite"):
            evidence(signal_strength=d(non_finite))
        with pytest.raises(ValueError, match="evidence_cost must be finite"):
            evidence(evidence_cost=d(non_finite))


def test_exact_decimal_boundaries_are_accepted() -> None:
    zero_signal = evidence(
        "raw-candidate-zero-boundary",
        signal_strength=d("0.000000"),
        evidence_cost=d("0.000000"),
    )
    full_signal = evidence(
        "raw-candidate-one-boundary",
        signal_strength=d("1.000000"),
        evidence_cost=d("0.000000"),
    )

    assert zero_signal.signal_strength == d("0.000000")
    assert zero_signal.evidence_cost == d("0.000000")
    assert full_signal.signal_strength == d("1.000000")
    assert full_signal.evidence_cost == d("0.000000")


def test_public_dataclasses_are_frozen_and_non_subclassable() -> None:
    public_dataclasses = (
        module.ResearchStrategyEvidenceCostSignalDecayConfig,
        module.ResearchStrategyEvidenceCostSignalDecayInput,
        module.ResearchStrategyEvidenceCostSignalDecayRow,
        module.ResearchStrategyEvidenceCostSignalDecayReasonCodeCount,
        module.ResearchStrategyEvidenceCostSignalDecayReport,
    )

    for dataclass_type in public_dataclasses:
        assert dataclass_type.__dataclass_params__.frozen is True
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Unsafe{dataclass_type.__name__}", (dataclass_type,), {})


def test_payload_schema_sha256_sorting_and_private_source_redaction_are_canonical() -> None:
    candidate_ids = (
        "private-candidate://alpha?token=alpha-secret",
        "private-candidate://beta?token=beta-secret",
        "private-candidate://gamma?token=gamma-secret",
    )
    rows = [
        evidence(
            candidate_id,
            evidence_channel="https://private-source.invalid/primary?token=hidden",
        )
        for candidate_id in candidate_ids
    ] + [
        evidence(
            candidate_id,
            evidence_channel="private-db:secondary-review",
            signal_strength=d("0.800000"),
        )
        for candidate_id in reversed(candidate_ids)
    ]

    report = build_report(rows)
    repeated = build_report(list(reversed(rows)))
    payload = report.payload
    encoded = json.dumps(payload, sort_keys=True)

    expected_hashes = tuple(
        sorted(
            f"sha256:{hashlib.sha256(candidate_id.encode('utf-8')).hexdigest()}"
            for candidate_id in candidate_ids
        ),
    )
    plaintext_order_hashes = tuple(
        f"sha256:{hashlib.sha256(candidate_id.encode('utf-8')).hexdigest()}"
        for candidate_id in sorted(candidate_ids)
    )
    assert plaintext_order_hashes != expected_hashes
    assert report == repeated
    assert tuple(row.signal_hash for row in report.rows) == expected_hashes
    assert tuple(payload) == REPORT_SCHEMA
    assert tuple(payload["rows"][0]) == ROW_SCHEMA
    assert tuple(payload["reason_code_counts"][0]) == REASON_CODE_COUNT_SCHEMA
    assert all(private_value not in encoded for private_value in candidate_ids)
    assert "private-source.invalid" not in encoded
    assert "private-db:secondary-review" not in encoded
    assert module.validate_research_strategy_evidence_cost_signal_decay_public_payload(
        payload,
    )

    unsigned_payload = mutable_payload(report)
    digest = unsigned_payload.pop("derived_validation_digest")
    canonical_json = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert digest == hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    payload_with_extra_key = mutable_payload(report)
    payload_with_extra_key["private_note"] = "redacted"
    resign_payload(payload_with_extra_key)
    with pytest.raises(ValueError, match="exact canonical schema"):
        module.validate_research_strategy_evidence_cost_signal_decay_public_payload(
            payload_with_extra_key,
        )


def test_resigned_payload_requires_full_derived_recomputation() -> None:
    config = module.ResearchStrategyEvidenceCostSignalDecayConfig(
        high_cost_watch_threshold=d("50.000000"),
        high_cost_block_threshold=d("200.000000"),
    )
    report = module.build_research_strategy_evidence_cost_signal_decay_report(
        [
            evidence(
                "raw-candidate-resigned-alpha",
                evidence_channel="primary-analysis",
                signal_strength=d("0.900000"),
                evidence_cost=d("40.000000"),
            ),
            evidence(
                "raw-candidate-resigned-alpha",
                evidence_channel="secondary-review",
                signal_strength=d("0.800000"),
                evidence_cost=d("60.000000"),
                observed_delta=timedelta(minutes=20),
            ),
            evidence(
                "raw-candidate-resigned-beta",
                evidence_channel="primary-analysis",
                signal_strength=d("0.900000"),
                evidence_cost=d("40.000000"),
            ),
            evidence(
                "raw-candidate-resigned-beta",
                evidence_channel="secondary-review",
                signal_strength=d("0.800000"),
                evidence_cost=d("60.000000"),
                observed_delta=timedelta(minutes=20),
            ),
        ],
        config=config,
        generated_at=GENERATED_AT,
    )
    assert len(report.rows) == 2
    assert module.validate_research_strategy_evidence_cost_signal_decay_public_payload(
        report.payload,
    )
    assert report.payload["high_cost_block_threshold"] == "200.000000"

    count_tamper = mutable_payload(report)
    count_tamper["candidate_count"] = "3.000000"
    resign_payload(count_tamper)
    with pytest.raises(ValueError, match="candidate_count must match rows"):
        module.validate_research_strategy_evidence_cost_signal_decay_public_payload(
            count_tamper,
        )

    age_tamper = mutable_payload(report)
    age_tamper["rows"][1]["latest_signal_age_seconds"] = "601.000000"
    resign_payload(age_tamper)
    with pytest.raises(
        ValueError,
        match="latest_signal_age_seconds must match generated_at",
    ):
        module.validate_research_strategy_evidence_cost_signal_decay_public_payload(
            age_tamper,
        )

    decay_tamper = mutable_payload(report)
    decay_tamper["rows"][1]["decayed_signal_score"] = "0.100000"
    resign_payload(decay_tamper)
    with pytest.raises(
        ValueError,
        match="decayed_signal_score must match recomputed value",
    ):
        module.validate_research_strategy_evidence_cost_signal_decay_public_payload(
            decay_tamper,
        )

    cost_tamper = mutable_payload(report)
    cost_tamper["rows"][1]["cost_efficiency_score"] = "0.100000"
    resign_payload(cost_tamper)
    with pytest.raises(
        ValueError,
        match="cost_efficiency_score must match recomputed value",
    ):
        module.validate_research_strategy_evidence_cost_signal_decay_public_payload(
            cost_tamper,
        )

    status_tamper = mutable_payload(report)
    status_tamper["rows"][1]["status"] = "pass"
    status_tamper["rows"][1]["reason_codes"] = [
        "strategy_evidence_cost_signal_decay_pass",
    ]
    resign_payload(status_tamper)
    with pytest.raises(ValueError, match="reason_codes must match recomputed value"):
        module.validate_research_strategy_evidence_cost_signal_decay_public_payload(
            status_tamper,
        )

    noncanonical_decimal = mutable_payload(report)
    noncanonical_decimal["candidate_count"] = "2.0"
    resign_payload(noncanonical_decimal)
    with pytest.raises(ValueError, match="canonical six-place Decimal"):
        module.validate_research_strategy_evidence_cost_signal_decay_public_payload(
            noncanonical_decimal,
        )


def test_module_has_no_network_db_wallet_order_or_live_trading_imports() -> None:
    module_path = Path(module.__file__)
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    banned_imports = {
        "aiohttp",
        "boto3",
        "ccxt",
        "eth_account",
        "http",
        "httpx",
        "paramiko",
        "polymarket",
        "psycopg",
        "psycopg2",
        "py_clob_client",
        "requests",
        "selenium",
        "socket",
        "sqlalchemy",
        "urllib",
        "urllib3",
        "web3",
        "websocket",
        "websockets",
    }
    assert imported_roots.isdisjoint(banned_imports)

    banned_call_or_attribute_names = {
        "buy",
        "connect",
        "execute",
        "open",
        "order",
        "read_bytes",
        "read_text",
        "sell",
        "send",
        "sign",
        "trade",
        "write_bytes",
        "write_text",
    }
    call_names: set[str] = set()
    attribute_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            attribute_names.add(node.attr)
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            call_names.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            call_names.add(node.func.attr)

    assert call_names.isdisjoint(banned_call_or_attribute_names)
    assert attribute_names.isdisjoint(banned_call_or_attribute_names)
