from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 3, 15, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 3, 14, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")
FORBIDDEN_SURFACE_TERMS = (
    "trading",
    "auth",
    "wallet",
    "account",
    "broker",
    "order",
    "submit",
    "cancel",
    "replace",
    "psycopg",
    "sqlite",
    "socket",
    "request",
    "urlopen",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_event_cluster_correlation_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_EVENT_CLUSTER_CORRELATION_DIGEST_CONFIG_VERSION
        ),
        "max_cluster_exposure_share": d("0.500000"),
        "max_event_correlation": d("0.700000"),
        "max_condition_correlation": d("0.800000"),
        "min_watch_cluster_size": d("2"),
    }
    values.update(overrides)
    return module.StrategyEventClusterCorrelationDigestConfig(**values)


def signal(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "candidate-alpha",
        "event_key": "event-alpha",
        "condition_id": "condition-alpha",
        "signal_key": "signal-alpha",
        "paper_exposure": d("120.000000"),
        "signal_strength": d("0.240000"),
        "event_correlation": d("0.200000"),
        "condition_correlation": d("0.150000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("caller_signal",),
    }
    values.update(overrides)
    return module.StrategyEventClusterCorrelationSignal(**values)


def digest(*signals: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_strategy_event_cluster_correlation_digest(
        signals,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def decimal_public_fields(value: object) -> tuple[str, ...]:
    return tuple(
        item.name
        for item in fields(value)
        if item.type is Decimal or "Decimal" in str(item.type)
    )


def test_digest_clusters_event_signals_and_flags_over_correlation_deterministically() -> None:
    result = digest(
        signal(
            candidate_reference="secret-wallet-token-alpha",
            event_key="fed-rate",
            condition_id="fed-condition-a",
            signal_key="macro-signal-a",
            paper_exposure=d("220.000000"),
            signal_strength=d("0.450000"),
            event_correlation=d("0.760000"),
            condition_correlation=d("0.410000"),
            observed_at=GENERATED_AT - timedelta(minutes=20),
        ),
        signal(
            candidate_reference="candidate-beta",
            event_key="fed-rate",
            condition_id="fed-condition-b",
            signal_key="macro-signal-b",
            paper_exposure=d("180.000000"),
            signal_strength=d("0.350000"),
            event_correlation=d("0.680000"),
            condition_correlation=d("0.820000"),
            observed_at=GENERATED_AT - timedelta(minutes=25),
        ),
        signal(
            candidate_reference="candidate-gamma",
            event_key="jobs-print",
            condition_id="jobs-condition-a",
            signal_key="labor-signal",
            paper_exposure=d("100.000000"),
            signal_strength=d("0.110000"),
            event_correlation=d("0.220000"),
            condition_correlation=d("0.190000"),
            observed_at=GENERATED_AT - timedelta(minutes=15),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-event-cluster-correlation-digest-v0"
    assert result.signal_count == d("3")
    assert result.cluster_count == d("2")
    assert result.blocked_count == d("1")
    assert result.watch_count == d("0")
    assert result.pass_count == d("1")
    assert result.total_paper_exposure == d("500.000000")
    assert result.max_cluster_exposure_share == d("0.800000")
    assert result.max_event_correlation == d("0.760000")
    assert result.max_condition_correlation == d("0.820000")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "cluster_exposure_share_high",
        "event_correlation_high",
        "condition_correlation_high",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.status for row in result.rows) == ("blocked", "pass")
    blocked, passing = result.rows
    assert blocked.cluster_rank == d("1")
    assert blocked.redacted_event_key.startswith("event_ref_")
    assert blocked.candidate_count == d("2")
    assert blocked.condition_count == d("2")
    assert blocked.signal_count == d("2")
    assert blocked.paper_exposure == d("400.000000")
    assert blocked.exposure_share == d("0.800000")
    assert blocked.mean_signal_strength == d("0.400000")
    assert blocked.max_event_correlation == d("0.760000")
    assert blocked.max_condition_correlation == d("0.820000")
    assert blocked.reason_codes == (
        "cluster_exposure_share_high",
        "condition_correlation_high",
        "event_cluster_overlap",
        "event_correlation_high",
    )
    assert len(set(blocked.reason_codes)) == len(blocked.reason_codes)
    assert all(value.startswith("candidate_ref_") for value in blocked.redacted_candidate_references)
    assert all(value.startswith("condition_ref_") for value in blocked.redacted_condition_ids)

    assert passing.cluster_rank == d("2")
    assert passing.candidate_count == d("1")
    assert passing.condition_count == d("1")
    assert passing.exposure_share == d("0.200000")
    assert passing.reason_codes == ("cluster_correlation_clear",)


def test_watch_cluster_empty_report_and_decimal_public_fields() -> None:
    watched = digest(
        signal(
            candidate_reference="watch-a",
            event_key="single-event",
            condition_id="watch-condition-a",
            paper_exposure=d("40.000000"),
            event_correlation=d("0.300000"),
            condition_correlation=d("0.200000"),
        ),
        signal(
            candidate_reference="watch-b",
            event_key="single-event",
            condition_id="watch-condition-a",
            paper_exposure=d("40.000000"),
            event_correlation=d("0.310000"),
            condition_correlation=d("0.250000"),
        ),
    )

    assert watched.status == "watch"
    assert watched.watch_count == d("1")
    assert watched.rows[0].status == "watch"
    assert watched.rows[0].condition_count == d("1")
    assert watched.rows[0].reason_codes == (
        "condition_cluster_overlap",
        "event_cluster_overlap",
    )

    empty = digest()
    assert empty.signal_count == d("0")
    assert empty.cluster_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.total_paper_exposure == ZERO
    assert empty.max_cluster_exposure_share == ZERO
    assert empty.max_event_correlation == ZERO
    assert empty.max_condition_correlation == ZERO
    assert empty.status == "pass"
    assert empty.reason_codes == ("event_cluster_correlation_digest_empty",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = digest(signal())
    for value in (config(), signal(), *populated.rows, populated):
        for field_name in decimal_public_fields(value):
            assert type(getattr(value, field_name)) is Decimal


def test_payload_serializes_decimal_strings_redacts_references_and_contains_no_floats() -> None:
    module = api()
    result = digest(
        signal(
            candidate_reference="secret-wallet-token-alpha",
            event_key="secret-event-alpha",
            condition_id="secret-condition-alpha",
            signal_key="secret-signal-alpha",
            observed_at=datetime(2026, 7, 3, 7, 45, tzinfo=timezone(timedelta(hours=-7))),
        ),
        generated_at=datetime(2026, 7, 3, 11, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.strategy_event_cluster_correlation_digest_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    assert payload["generated_at"] == "2026-07-03T15:00:00+00:00"
    assert payload["signal_count"] == "1"
    assert payload["cluster_count"] == "1"
    assert payload["total_paper_exposure"] == "120.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["cluster_rank"] == "1"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T14:45:00+00:00"
    assert payload["rows"][0]["redacted_event_key"].startswith("event_ref_")
    assert payload["rows"][0]["redacted_candidate_references"][0].startswith(
        "candidate_ref_",
    )
    assert_no_float_values(payload)
    for token in ("secret", "wallet", "token", "condition-alpha", "event-alpha"):
        assert token not in rendered
    assert "secret" not in repr(result)
    assert "wallet" not in repr(result)
    assert "token" not in repr(result)


def test_dataclasses_are_frozen_and_reject_float_int_subclasses_bad_time_and_flags() -> None:
    module = api()
    input_signal = signal()

    with pytest.raises(FrozenInstanceError):
        input_signal.paper_exposure = d("1.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest(input_signal).rows[0].paper_exposure = d("1.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_exposure must be a Decimal"):
        signal(paper_exposure=120)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="event_correlation must be a Decimal"):
        signal(event_correlation=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="signal_strength must be exactly Decimal"):
        signal(signal_strength=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        digest(input_signal, generated_at=_DatetimeSubclass(2026, 7, 3, 15, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 3, 14, 45))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 3, 14, 45, tzinfo=_NoneOffsetTz()))
    with pytest.raises(ValueError, match="generated_at must not precede observed_at"):
        digest(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(digest(input_signal), readonly=False)
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        signal(reason_codes=("caller_signal", "caller_signal"))
    with pytest.raises(ValueError, match="reason_codes is required"):
        signal(reason_codes=())
    with pytest.raises(ValueError, match="max_event_correlation"):
        config(max_event_correlation=d("1.000001"))
    with pytest.raises(ValueError, match="signals must be an iterable"):
        digest("not-signals")
    with pytest.raises(ValueError, match="signals must contain StrategyEvent"):
        digest(object())
    with pytest.raises(ValueError, match="config must be a StrategyEvent"):
        module.build_strategy_event_cluster_correlation_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="report must be a StrategyEvent"):
        module.strategy_event_cluster_correlation_digest_payload(object())


def test_direct_constructors_validate_consistency_sorting_and_reason_codes() -> None:
    result = digest(
        signal(
            event_key="b-event",
            condition_id="b-condition",
            candidate_reference="b-candidate",
            paper_exposure=d("100.000000"),
        ),
        signal(
            event_key="a-event",
            condition_id="a-condition",
            candidate_reference="a-candidate",
            paper_exposure=d("100.000000"),
        ),
    )
    assert tuple(row.cluster_rank for row in result.rows) == (d("1"), d("2"))

    row = result.rows[0]
    with pytest.raises(ValueError, match="exposure_share"):
        replace(row, exposure_share=d("0.900000"))
    with pytest.raises(ValueError, match="candidate_count"):
        replace(row, candidate_count=d("3"))
    with pytest.raises(ValueError, match="cluster_rank"):
        replace(row, cluster_rank=d("0"))
    with pytest.raises(ValueError, match="status"):
        replace(row, status="blocked")
    with pytest.raises(ValueError, match="signal_count"):
        replace(result, signal_count=d("3"))
    with pytest.raises(ValueError, match="rows"):
        replace(result, rows=tuple(reversed(result.rows)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=("event_cluster_overlap", "event_cluster_overlap"))


def test_module_is_pure_report_only_reducer_without_runtime_surface() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    imports: set[str] = set()
    calls: set[str] = set()
    constants: list[object] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
        elif isinstance(node, ast.Constant):
            constants.append(node.value)

    assert not imports & forbidden_import_roots
    assert not calls & {
        "open",
        "print",
        "exec",
        "eval",
        "compile",
        "connect",
        "request",
        "urlopen",
    }
    assert not any(isinstance(value, float) for value in constants)
    lowered = source.lower()
    for term in FORBIDDEN_SURFACE_TERMS:
        assert term not in lowered


def test_public_exports_are_explicit() -> None:
    module = api()
    assert set(module.__all__) == {
        "DEFAULT_STRATEGY_EVENT_CLUSTER_CORRELATION_DIGEST_CONFIG_VERSION",
        "StrategyEventClusterCorrelationDigestConfig",
        "StrategyEventClusterCorrelationDigestReport",
        "StrategyEventClusterCorrelationDigestRow",
        "StrategyEventClusterCorrelationSignal",
        "build_strategy_event_cluster_correlation_digest",
        "strategy_event_cluster_correlation_digest_payload",
    }
