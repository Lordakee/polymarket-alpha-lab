from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_primary_signal_drift_watch_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def _api():
    return import_module(
        "polymarket_alpha_lab.research_source_primary_signal_drift_watch_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    api = _api()
    values = {
        "config_version": (
            api.DEFAULT_RESEARCH_SOURCE_PRIMARY_SIGNAL_DRIFT_WATCH_REPORT_CONFIG_VERSION
        ),
        "watch_primary_signal_drift_score": d("0.200000"),
        "block_primary_signal_drift_score": d("0.500000"),
        "watch_primary_source_age_seconds": d("3600.000000"),
        "block_primary_source_age_seconds": d("86400.000000"),
        "watch_corroboration_gap_score": d("0.300000"),
        "block_corroboration_gap_score": d("0.600000"),
        "watch_official_conflict_score": d("0.250000"),
        "block_official_conflict_score": d("0.550000"),
        "watch_evidence_revision_score": d("0.250000"),
        "block_evidence_revision_score": d("0.600000"),
        "watch_drift_pressure_score": d("0.300000"),
        "block_drift_pressure_score": d("0.650000"),
        "primary_signal_drift_weight": d("0.350000"),
        "primary_source_staleness_weight": d("0.250000"),
        "corroboration_gap_weight": d("0.150000"),
        "official_conflict_weight": d("0.150000"),
        "evidence_revision_weight": d("0.100000"),
    }
    values.update(overrides)
    return api.ResearchSourcePrimarySignalDriftWatchConfig(**values)


def _input(
    signal_bucket: str = "clear-bucket",
    *,
    primary_source_age_seconds: Decimal = d("600.000000"),
    current_primary_signal_score: Decimal = d("0.520000"),
    baseline_primary_signal_score: Decimal = d("0.500000"),
    corroboration_gap_score: Decimal = d("0.050000"),
    official_conflict_score: Decimal = d("0.050000"),
    evidence_revision_score: Decimal = d("0.050000"),
    primary_source_available: bool = True,
):
    api = _api()
    return api.ResearchSourcePrimarySignalDriftWatchInput(
        signal_bucket=signal_bucket,
        primary_source_age_seconds=primary_source_age_seconds,
        current_primary_signal_score=current_primary_signal_score,
        baseline_primary_signal_score=baseline_primary_signal_score,
        corroboration_gap_score=corroboration_gap_score,
        official_conflict_score=official_conflict_score,
        evidence_revision_score=evidence_revision_score,
        primary_source_available=primary_source_available,
    )


def _report(
    rows: tuple[object, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    api = _api()
    return api.build_research_source_primary_signal_drift_watch_report(
        rows,
        config=cfg or _config(),
        generated_at=generated_at,
    )


def test_primary_signal_drift_watch_classifies_pass_watch_and_block_rows() -> None:
    api = _api()

    report = _report(
        (
            _input(),
            _input(
                "block-bucket",
                primary_source_age_seconds=d("90000.000000"),
                current_primary_signal_score=d("0.900000"),
                baseline_primary_signal_score=d("0.200000"),
                corroboration_gap_score=d("0.750000"),
                official_conflict_score=d("0.600000"),
                evidence_revision_score=d("0.650000"),
                primary_source_available=False,
            ),
            _input(
                "watch-bucket",
                primary_source_age_seconds=d("7200.000000"),
                current_primary_signal_score=d("0.650000"),
                baseline_primary_signal_score=d("0.400000"),
                corroboration_gap_score=d("0.350000"),
                official_conflict_score=d("0.300000"),
                evidence_revision_score=d("0.200000"),
            ),
        ),
        generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert type(report) is api.ResearchSourcePrimarySignalDriftWatchReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.observed_signal_count == d("3.000000")
    assert report.pass_signal_count == d("1.000000")
    assert report.watch_signal_count == d("1.000000")
    assert report.block_signal_count == d("1.000000")
    assert report.stale_primary_source_count == d("2.000000")
    assert report.missing_primary_source_count == d("1.000000")
    assert report.max_primary_signal_drift_score == d("0.700000")
    assert report.max_primary_source_age_seconds == d("90000.000000")
    assert report.max_drift_pressure_score == d("0.762500")
    assert report.watch_ratio == d("0.666667")
    assert report.block_ratio == d("0.333333")
    assert report.status == "block"
    assert report.reason_codes == (
        "missing_primary_source_present",
        "primary_signal_drift_present",
        "primary_source_stale_present",
        "corroboration_gap_present",
        "official_conflict_present",
        "evidence_revision_present",
        "drift_pressure_present",
        "primary_signal_drift_block_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    block_row, watch_row, pass_row = report.rows
    assert block_row == api.ResearchSourcePrimarySignalDriftWatchRow(
        signal_bucket="block-bucket",
        status="block",
        current_primary_signal_score=d("0.900000"),
        baseline_primary_signal_score=d("0.200000"),
        primary_signal_drift_score=d("0.700000"),
        primary_source_age_seconds=d("90000.000000"),
        primary_source_staleness_score=d("1.000000"),
        corroboration_gap_score=d("0.750000"),
        official_conflict_score=d("0.600000"),
        evidence_revision_score=d("0.650000"),
        drift_pressure_score=d("0.762500"),
        primary_source_available=False,
        primary_source_stale=True,
        reason_codes=(
            "missing_primary_source_block",
            "primary_signal_drift_block",
            "primary_source_stale_block",
            "corroboration_gap_block",
            "official_conflict_block",
            "evidence_revision_block",
            "drift_pressure_block",
        ),
    )
    assert watch_row.signal_bucket == "watch-bucket"
    assert watch_row.status == "watch"
    assert watch_row.primary_signal_drift_score == d("0.250000")
    assert watch_row.primary_source_staleness_score == d("0.083333")
    assert watch_row.drift_pressure_score == d("0.225833")
    assert watch_row.reason_codes == (
        "primary_signal_drift_watch",
        "primary_source_stale_watch",
        "corroboration_gap_watch",
        "official_conflict_watch",
    )
    assert pass_row.signal_bucket == "clear-bucket"
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("primary_signal_drift_watch_clear",)


def test_empty_report_blocks_and_clear_report_has_valid_decimal_payload_digest() -> None:
    api = _api()

    empty = _report(())
    clear = _report((_input("clear-bucket"),))
    empty_payload = api.research_source_primary_signal_drift_watch_report_payload(empty)
    payload = api.research_source_primary_signal_drift_watch_report_payload(clear)
    repeat_payload = api.research_source_primary_signal_drift_watch_report_payload(clear)

    assert empty.observed_signal_count == ZERO
    assert empty.status == "block"
    assert empty.reason_codes == ("no_primary_signal_inputs",)
    assert empty.rows == ()
    assert empty_payload["rows"] == []
    assert empty_payload["observed_signal_count"] == "0.000000"
    assert empty_payload["status"] == "block"
    assert empty_payload["reason_codes"] == ["no_primary_signal_inputs"]
    assert api.validate_research_source_primary_signal_drift_watch_report_payload(
        empty_payload,
    )
    assert (
        api.research_source_primary_signal_drift_watch_report_payload(empty_payload)
        == empty_payload
    )
    assert clear.status == "pass"
    assert clear.reason_codes == ("primary_signal_drift_watch_clear",)
    assert payload == repeat_payload
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["observed_signal_count"] == "1.000000"
    assert payload["watch_ratio"] == "0.000000"
    assert payload["rows"][0]["signal_bucket"] == "clear-bucket"
    assert payload["rows"][0]["current_primary_signal_score"] == "0.520000"
    assert payload["rows"][0]["baseline_primary_signal_score"] == "0.500000"
    assert payload["rows"][0]["primary_signal_drift_score"] == "0.020000"
    assert payload["derived_validation_digest"] == clear.derived_validation_digest
    assert len(clear.derived_validation_digest) == 64
    assert int(clear.derived_validation_digest, 16) >= 0
    assert json.dumps(payload, sort_keys=True) == json.dumps(repeat_payload, sort_keys=True)
    assert api.validate_research_source_primary_signal_drift_watch_report_payload(payload)
    assert api.research_source_primary_signal_drift_watch_report_payload(payload) == payload
    assert not _contains_float_or_int(payload)
    assert not _has_forbidden_public_key(payload)


def test_validator_requires_exact_canonical_report_config_and_row_field_order() -> None:
    api = _api()
    payload = api.research_source_primary_signal_drift_watch_report_payload(
        _report((_input(),)),
    )

    reordered_report = dict(reversed(tuple(payload.items())))
    _resign_payload(reordered_report)
    with pytest.raises(ValueError, match="canonical field order"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            reordered_report,
        )

    reordered_config = _mutable_payload(payload)
    reordered_config["config"] = dict(
        reversed(tuple(reordered_config["config"].items())),
    )
    _resign_payload(reordered_config)
    with pytest.raises(ValueError, match="canonical field order"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            reordered_config,
        )

    reordered_row = _mutable_payload(payload)
    reordered_row["rows"][0] = dict(
        reversed(tuple(reordered_row["rows"][0].items())),
    )
    _resign_payload(reordered_row)
    with pytest.raises(ValueError, match="canonical field order"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            reordered_row,
        )


def test_payload_rejects_sensitive_keys_values_flags_and_digest_downgrades() -> None:
    api = _api()
    report = _report(
        (
            _input(
                primary_source_age_seconds=d("7200.000000"),
                current_primary_signal_score=d("0.650000"),
                baseline_primary_signal_score=d("0.400000"),
                corroboration_gap_score=d("0.350000"),
                official_conflict_score=d("0.300000"),
            ),
        ),
    )
    payload = api.research_source_primary_signal_drift_watch_report_payload(report)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            {**payload, "status": "pass"},
        )
    with pytest.raises(ValueError, match="paper_only"):
        api.research_source_primary_signal_drift_watch_report_payload(
            {**payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="Decimal-derived"):
        api.research_source_primary_signal_drift_watch_report_payload(
            {**payload, "observed_signal_count": 1},
        )
    with pytest.raises(ValueError, match="six decimal places"):
        api.research_source_primary_signal_drift_watch_report_payload(
            {**payload, "observed_signal_count": "1"},
        )
    with pytest.raises(ValueError, match="float"):
        api.research_source_primary_signal_drift_watch_report_payload(
            {**payload, "watch_ratio": 0.5},
        )
    payload_with_null = _mutable_payload(payload)
    payload_with_null["config"]["watch_primary_signal_drift_score"] = None
    _resign_payload(payload_with_null)
    with pytest.raises(ValueError, match="null"):
        api.research_source_primary_signal_drift_watch_report_payload(
            payload_with_null,
        )

    unsafe_keys = (
        "raw_" + "candidate_id",
        "market_" + "id",
        "market_" + "slug",
        "sl" + "ug",
        "ques" + "tion",
        "source_" + "url",
        "source_" + "text",
        "d" + "sn",
        "ta" + "ble_name",
        "au" + "th_token",
        "wall" + "et_address",
        "or" + "der_id",
        "tra" + "de_id",
        "api_key",
        "client_secret",
        "db_password",
        "service_credential",
        "contact_email",
    )
    for unsafe_key in unsafe_keys:
        with pytest.raises(ValueError, match="unsafe"):
            api.research_source_primary_signal_drift_watch_report_payload(
                {**payload, unsafe_key: "redacted"},
            )

    unsafe_values = (
        "candidate_id=abc",
        "will-this-event-slug-leak",
        "https://example.invalid/source",
        "source text copied from feed",
        "postgres://example",
        "token=secret",
        "wallet-address",
        "order-id",
        "trade-id",
        "position sizing note",
        "buy recommendation",
        "api_key=public-leak",
        "client_secret=public-leak",
        "password=public-leak",
        "credential=public-leak",
        "email=user@example.invalid",
        "AKIAIOSFODNN7EXAMPLE",
        "ghp_abcdefghijklmnopqrstuvwxyz1234567890",
        "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890",
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature",
        "Bearer abcdefghijklmnopqrstuvwxyz",
    )
    for unsafe_value in unsafe_values:
        bad_row = {**payload["rows"][0], "signal_bucket": unsafe_value}
        with pytest.raises(ValueError, match="unsafe|public identifier"):
            api.research_source_primary_signal_drift_watch_report_payload(
                {**payload, "rows": [bad_row]},
            )

    serialized = repr(payload).lower()
    for banned in (
        "candidate_id",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
        "token",
    ):
        assert banned not in serialized


@pytest.mark.parametrize(
    "unsafe_identifier",
    (
        "safe\x00bucket",
        "safe\tbucket",
        "safe\nbucket",
        "safe\r\nbucket",
        "api-key-public-leak",
        "contains-secret-value",
        "password-public-leak",
        "service-credential",
        "owner-email",
        "AIzaSyA123456789012345678901234567890",
        "xoxb-123456789012-123456789012-abcdefghijklmnopqrstuvwx",
        "-----BEGIN PRIVATE KEY-----",
    ),
)
def test_public_identifier_rejects_controls_and_common_credential_patterns(
    unsafe_identifier: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe|public identifier|canonical"):
        _input(signal_bucket=unsafe_identifier)


def test_dataclasses_are_frozen_strict_decimal_utc_and_module_has_no_io_ast() -> None:
    api = _api()
    report = _report((_input(),))

    public_classes = (
        api.ResearchSourcePrimarySignalDriftWatchConfig,
        api.ResearchSourcePrimarySignalDriftWatchInput,
        api.ResearchSourcePrimarySignalDriftWatchRow,
        api.ResearchSourcePrimarySignalDriftWatchReport,
    )
    assert all(is_dataclass(public_class) for public_class in public_classes)
    assert all(public_class.__dataclass_params__.frozen is True for public_class in public_classes)
    for public_class in public_classes:
        for field in fields(public_class):
            if field.name.endswith(("_count", "_score", "_ratio", "_seconds")):
                assert field.type in (Decimal, "Decimal")

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        _config(watch_primary_signal_drift_score=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="Decimal"):
        _input(current_primary_signal_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        _input(primary_source_age_seconds=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        _report((), generated_at=datetime(2026, 7, 8, 16, 0))
    with pytest.raises(ValueError, match="UTC offset"):
        _report(
            (),
            generated_at=datetime(2026, 7, 8, 16, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="signal_bucket"):
        _input(signal_bucket="event slug leak")
    with pytest.raises(ValueError, match="primary_source_available"):
        _input(primary_source_available=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="watch")
    with pytest.raises(ValueError, match="pass_signal_count"):
        replace(report, pass_signal_count=ZERO)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "aiohttp",
        "httpx",
        "io",
        "os",
        "pathlib",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }
    forbidden_call_names = {
        "Popen",
        "connect",
        "create_connection",
        "open",
        "read_bytes",
        "read_text",
        "recv",
        "request",
        "run",
        "send",
        "system",
        "urlopen",
        "write_bytes",
        "write_text",
    }
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            called_name = _ast_terminal_name(node.func)
            if called_name is not None:
                called_names.add(called_name)
    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert called_names.isdisjoint(forbidden_call_names)


def test_decimal_rules_reject_signed_zero_raw_bounds_and_hostile_context() -> None:
    api = _api()

    with pytest.raises(ValueError, match="signed zero"):
        _input(current_primary_signal_score=d("-0.000000"))
    with pytest.raises(ValueError, match="current_primary_signal_score"):
        _input(current_primary_signal_score=d("-0.0000004"))
    with pytest.raises(ValueError, match="current_primary_signal_score"):
        _input(current_primary_signal_score=d("1.0000004"))
    for value in (d("NaN"), d("Infinity"), d("-Infinity")):
        with pytest.raises(ValueError, match="finite"):
            _input(current_primary_signal_score=value)
    with pytest.raises(ValueError, match="quantizable"):
        _input(primary_source_age_seconds=d("1e1000"))

    weights = {
        "primary_signal_drift_weight": d("0.333333"),
        "primary_source_staleness_weight": d("0.333333"),
        "corroboration_gap_weight": d("0.333334"),
        "official_conflict_weight": ZERO,
        "evidence_revision_weight": ZERO,
    }
    baseline_config = _config(**weights)
    baseline = _report(
        (
            _input(
                current_primary_signal_score=d("0.987654"),
                baseline_primary_signal_score=d("0.123456"),
                corroboration_gap_score=d("0.234567"),
            ),
        ),
        cfg=baseline_config,
    )

    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        hostile_context_config = _config(**weights)
        hostile_context_report = _report(
            (
                _input(
                    current_primary_signal_score=d("0.987654"),
                    baseline_primary_signal_score=d("0.123456"),
                    corroboration_gap_score=d("0.234567"),
                ),
            ),
            cfg=hostile_context_config,
        )

    assert hostile_context_config == baseline_config
    assert (
        api.research_source_primary_signal_drift_watch_report_payload(
            hostile_context_report,
        )
        == api.research_source_primary_signal_drift_watch_report_payload(baseline)
    )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("primary_source_age_seconds", d("3599.9999996")),
        ("current_primary_signal_score", d("0.1999996")),
        ("baseline_primary_signal_score", d("0.1999996")),
        ("corroboration_gap_score", d("0.2999996")),
        ("official_conflict_score", d("0.2499996")),
        ("evidence_revision_score", d("0.2499996")),
    ),
)
def test_all_input_drivers_reject_values_changed_by_six_decimal_quantization(
    field_name: str,
    value: Decimal,
) -> None:
    with pytest.raises(ValueError, match="six decimal places"):
        _input(**{field_name: value})


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("watch_primary_signal_drift_score", d("0.1999996")),
        ("block_primary_signal_drift_score", d("0.5000004")),
        ("watch_primary_source_age_seconds", d("3599.9999996")),
        ("block_primary_source_age_seconds", d("86400.0000004")),
        ("watch_corroboration_gap_score", d("0.2999996")),
        ("block_corroboration_gap_score", d("0.6000004")),
        ("watch_official_conflict_score", d("0.2499996")),
        ("block_official_conflict_score", d("0.5500004")),
        ("watch_evidence_revision_score", d("0.2499996")),
        ("block_evidence_revision_score", d("0.6000004")),
        ("watch_drift_pressure_score", d("0.2999996")),
        ("block_drift_pressure_score", d("0.6500004")),
        ("primary_signal_drift_weight", d("0.3500004")),
        ("primary_source_staleness_weight", d("0.2500004")),
        ("corroboration_gap_weight", d("0.1500004")),
        ("official_conflict_weight", d("0.1500004")),
        ("evidence_revision_weight", d("0.1000004")),
    ),
)
def test_all_config_decimals_reject_values_changed_by_six_decimal_quantization(
    field_name: str,
    value: Decimal,
) -> None:
    with pytest.raises(ValueError, match="six decimal places"):
        _config(**{field_name: value})


@pytest.mark.parametrize(
    ("input_overrides", "expected_status", "expected_reason"),
    (
        (
            {
                "current_primary_signal_score": d("0.199999"),
                "baseline_primary_signal_score": ZERO,
            },
            "pass",
            "primary_signal_drift_watch_clear",
        ),
        (
            {
                "current_primary_signal_score": d("0.200000"),
                "baseline_primary_signal_score": ZERO,
            },
            "watch",
            "primary_signal_drift_watch",
        ),
        (
            {
                "current_primary_signal_score": d("0.499999"),
                "baseline_primary_signal_score": ZERO,
            },
            "watch",
            "primary_signal_drift_watch",
        ),
        (
            {
                "current_primary_signal_score": d("0.500000"),
                "baseline_primary_signal_score": ZERO,
            },
            "block",
            "primary_signal_drift_block",
        ),
        (
            {"primary_source_age_seconds": d("3599.999999")},
            "pass",
            "primary_signal_drift_watch_clear",
        ),
        (
            {"primary_source_age_seconds": d("3600.000000")},
            "watch",
            "primary_source_stale_watch",
        ),
        (
            {"primary_source_age_seconds": d("86399.999999")},
            "watch",
            "primary_source_stale_watch",
        ),
        (
            {"primary_source_age_seconds": d("86400.000000")},
            "block",
            "primary_source_stale_block",
        ),
        (
            {"corroboration_gap_score": d("0.299999")},
            "pass",
            "primary_signal_drift_watch_clear",
        ),
        (
            {"corroboration_gap_score": d("0.300000")},
            "watch",
            "corroboration_gap_watch",
        ),
        (
            {"corroboration_gap_score": d("0.599999")},
            "watch",
            "corroboration_gap_watch",
        ),
        (
            {"corroboration_gap_score": d("0.600000")},
            "block",
            "corroboration_gap_block",
        ),
        (
            {"official_conflict_score": d("0.249999")},
            "pass",
            "primary_signal_drift_watch_clear",
        ),
        (
            {"official_conflict_score": d("0.250000")},
            "watch",
            "official_conflict_watch",
        ),
        (
            {"official_conflict_score": d("0.549999")},
            "watch",
            "official_conflict_watch",
        ),
        (
            {"official_conflict_score": d("0.550000")},
            "block",
            "official_conflict_block",
        ),
        (
            {"evidence_revision_score": d("0.249999")},
            "pass",
            "primary_signal_drift_watch_clear",
        ),
        (
            {"evidence_revision_score": d("0.250000")},
            "watch",
            "evidence_revision_watch",
        ),
        (
            {"evidence_revision_score": d("0.599999")},
            "watch",
            "evidence_revision_watch",
        ),
        (
            {"evidence_revision_score": d("0.600000")},
            "block",
            "evidence_revision_block",
        ),
    ),
)
def test_direct_input_threshold_boundaries_are_exact(
    input_overrides: dict[str, Decimal],
    expected_status: str,
    expected_reason: str,
) -> None:
    row = _report((_input(**input_overrides),)).rows[0]

    assert row.status == expected_status
    assert expected_reason in row.reason_codes


@pytest.mark.parametrize(
    ("pressure", "expected_status", "expected_reason"),
    (
        (d("0.299999"), "pass", "primary_signal_drift_watch_clear"),
        (d("0.300000"), "watch", "drift_pressure_watch"),
        (d("0.649999"), "watch", "drift_pressure_watch"),
        (d("0.650000"), "block", "drift_pressure_block"),
    ),
)
def test_drift_pressure_threshold_boundaries_are_exact(
    pressure: Decimal,
    expected_status: str,
    expected_reason: str,
) -> None:
    cfg = _config(
        watch_primary_signal_drift_score=d("0.900000"),
        block_primary_signal_drift_score=ONE,
        watch_corroboration_gap_score=d("0.900000"),
        block_corroboration_gap_score=ONE,
        watch_official_conflict_score=d("0.900000"),
        block_official_conflict_score=ONE,
        watch_evidence_revision_score=d("0.900000"),
        block_evidence_revision_score=ONE,
        primary_signal_drift_weight=ONE,
        primary_source_staleness_weight=ZERO,
        corroboration_gap_weight=ZERO,
        official_conflict_weight=ZERO,
        evidence_revision_weight=ZERO,
    )
    row = _report(
        (
            _input(
                primary_source_age_seconds=ZERO,
                current_primary_signal_score=pressure,
                baseline_primary_signal_score=ZERO,
                corroboration_gap_score=ZERO,
                official_conflict_score=ZERO,
                evidence_revision_score=ZERO,
            ),
        ),
        cfg=cfg,
    ).rows[0]

    assert row.drift_pressure_score == pressure
    assert row.status == expected_status
    assert expected_reason in row.reason_codes


@pytest.mark.parametrize(
    ("config_overrides", "input_overrides", "rounded_pressure", "status", "reasons"),
    (
        (
            {
                "primary_signal_drift_weight": ZERO,
                "primary_source_staleness_weight": ZERO,
                "corroboration_gap_weight": d("0.350000"),
                "official_conflict_weight": ZERO,
                "evidence_revision_weight": d("0.650000"),
            },
            {
                "corroboration_gap_score": d("0.857142"),
                "official_conflict_score": ZERO,
            },
            d("0.300000"),
            "pass",
            ("primary_signal_drift_watch_clear",),
        ),
        (
            {
                "primary_signal_drift_weight": ZERO,
                "primary_source_staleness_weight": ZERO,
                "corroboration_gap_weight": d("0.600000"),
                "official_conflict_weight": d("0.400000"),
                "evidence_revision_weight": ZERO,
            },
            {
                "corroboration_gap_score": d("0.800000"),
                "official_conflict_score": d("0.424999"),
            },
            d("0.650000"),
            "watch",
            ("drift_pressure_watch",),
        ),
    ),
)
def test_rounded_pressure_never_changes_watch_or_block_semantics(
    config_overrides: dict[str, Decimal],
    input_overrides: dict[str, Decimal],
    rounded_pressure: Decimal,
    status: str,
    reasons: tuple[str, ...],
) -> None:
    cfg = _config(
        watch_primary_signal_drift_score=d("0.900000"),
        block_primary_signal_drift_score=ONE,
        watch_corroboration_gap_score=d("0.900000"),
        block_corroboration_gap_score=ONE,
        watch_official_conflict_score=d("0.900000"),
        block_official_conflict_score=ONE,
        watch_evidence_revision_score=d("0.900000"),
        block_evidence_revision_score=ONE,
        watch_primary_source_age_seconds=d("999999.000000"),
        block_primary_source_age_seconds=d("1000000.000000"),
        **config_overrides,
    )
    row = _report(
        (
            _input(
                **{
                    "primary_source_age_seconds": ZERO,
                    "current_primary_signal_score": ZERO,
                    "baseline_primary_signal_score": ZERO,
                    "corroboration_gap_score": ZERO,
                    "official_conflict_score": ZERO,
                    "evidence_revision_score": ZERO,
                    **input_overrides,
                },
            ),
        ),
        cfg=cfg,
    ).rows[0]

    assert row.drift_pressure_score == rounded_pressure
    assert row.status == status
    assert row.reason_codes == reasons


def test_public_dataclasses_are_final_exact_types() -> None:
    api = _api()

    for public_class in (
        api.ResearchSourcePrimarySignalDriftWatchConfig,
        api.ResearchSourcePrimarySignalDriftWatchInput,
        api.ResearchSourcePrimarySignalDriftWatchRow,
        api.ResearchSourcePrimarySignalDriftWatchReport,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Derived{public_class.__name__}", (public_class,), {})


def test_build_revalidates_object_setattr_mutated_config() -> None:
    config = _config()
    object.__setattr__(config, "primary_signal_drift_weight", d("0.900000"))

    with pytest.raises(ValueError, match="weights must sum to one"):
        _report((_input(),), cfg=config)


def test_build_revalidates_object_setattr_mutated_input_before_arithmetic() -> None:
    input_value = _input()
    object.__setattr__(
        input_value,
        "current_primary_signal_score",
        Decimal("NaN"),
    )

    with pytest.raises(ValueError, match="current_primary_signal_score must be finite"):
        _report((input_value,))


def test_report_revalidates_object_setattr_mutated_nested_row_before_aggregation() -> None:
    report = _report((_input(),))
    row = report.rows[0]
    object.__setattr__(row, "current_primary_signal_score", Decimal("NaN"))

    with pytest.raises(ValueError, match="current_primary_signal_score must be finite"):
        replace(report, rows=(row,), derived_validation_digest="")


def test_resigned_payload_recomputes_all_materialized_fields_and_order() -> None:
    api = _api()
    clear_payload = api.research_source_primary_signal_drift_watch_report_payload(
        _report((_input(),)),
    )

    bad_report_count = _mutable_payload(clear_payload)
    bad_report_count["observed_signal_count"] = "2.000000"
    _resign_payload(bad_report_count)
    with pytest.raises(ValueError, match="observed_signal_count"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            bad_report_count,
        )

    bad_staleness = _mutable_payload(clear_payload)
    bad_staleness["rows"][0]["primary_source_staleness_score"] = "0.006945"
    _resign_payload(bad_staleness)
    with pytest.raises(ValueError, match="primary_source_staleness_score"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            bad_staleness,
        )

    bad_pressure = _mutable_payload(clear_payload)
    bad_pressure["rows"][0]["drift_pressure_score"] = "0.028737"
    bad_pressure["max_drift_pressure_score"] = "0.028737"
    _resign_payload(bad_pressure)
    with pytest.raises(ValueError, match="drift_pressure_score"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            bad_pressure,
        )

    coherent_but_false_watch = _mutable_payload(clear_payload)
    coherent_but_false_watch["rows"][0]["status"] = "watch"
    coherent_but_false_watch["rows"][0]["reason_codes"] = [
        "primary_signal_drift_watch",
    ]
    coherent_but_false_watch["pass_signal_count"] = "0.000000"
    coherent_but_false_watch["watch_signal_count"] = "1.000000"
    coherent_but_false_watch["watch_ratio"] = "1.000000"
    coherent_but_false_watch["status"] = "watch"
    coherent_but_false_watch["reason_codes"] = [
        "primary_signal_drift_present",
    ]
    _resign_payload(coherent_but_false_watch)
    with pytest.raises(ValueError, match="status"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            coherent_but_false_watch,
        )

    coherent_but_false_drift = _mutable_payload(clear_payload)
    coherent_but_false_drift["rows"][0]["primary_signal_drift_score"] = "0.200000"
    coherent_but_false_drift["rows"][0]["drift_pressure_score"] = "0.091736"
    coherent_but_false_drift["rows"][0]["status"] = "watch"
    coherent_but_false_drift["rows"][0]["reason_codes"] = [
        "primary_signal_drift_watch",
    ]
    coherent_but_false_drift["pass_signal_count"] = "0.000000"
    coherent_but_false_drift["watch_signal_count"] = "1.000000"
    coherent_but_false_drift["max_primary_signal_drift_score"] = "0.200000"
    coherent_but_false_drift["max_drift_pressure_score"] = "0.091736"
    coherent_but_false_drift["watch_ratio"] = "1.000000"
    coherent_but_false_drift["status"] = "watch"
    coherent_but_false_drift["reason_codes"] = [
        "primary_signal_drift_present",
    ]
    _resign_payload(coherent_but_false_drift)
    with pytest.raises(ValueError, match="primary_signal_drift_score"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            coherent_but_false_drift,
        )

    signed_zero = _mutable_payload(clear_payload)
    signed_zero["watch_ratio"] = "-0.000000"
    _resign_payload(signed_zero)
    with pytest.raises(ValueError, match="signed zero"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            signed_zero,
        )

    noncanonical_timestamp = _mutable_payload(clear_payload)
    noncanonical_timestamp["generated_at"] = "2026-07-08T16:00:00Z"
    _resign_payload(noncanonical_timestamp)
    with pytest.raises(ValueError, match="generated_at"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            noncanonical_timestamp,
        )

    ordered_payload = api.research_source_primary_signal_drift_watch_report_payload(
        _report(
            (
                _input("a-clear"),
                _input(
                    "z-watch",
                    current_primary_signal_score=d("0.800000"),
                    baseline_primary_signal_score=d("0.500000"),
                ),
            ),
        ),
    )
    reordered_rows = _mutable_payload(ordered_payload)
    reordered_rows["rows"].reverse()
    _resign_payload(reordered_rows)
    with pytest.raises(ValueError, match="deterministic"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            reordered_rows,
        )

    duplicate_rows = _mutable_payload(clear_payload)
    duplicate_rows["rows"].append(dict(duplicate_rows["rows"][0]))
    duplicate_rows["observed_signal_count"] = "2.000000"
    duplicate_rows["pass_signal_count"] = "2.000000"
    _resign_payload(duplicate_rows)
    with pytest.raises(ValueError, match="unique"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            duplicate_rows,
        )


@pytest.mark.parametrize(
    ("base_kind", "changes", "expected_error"),
    (
        (
            "clear",
            {"primary_signal_drift_score": "0.030000"},
            "primary_signal_drift_score",
        ),
        (
            "clear",
            {"primary_source_staleness_score": "0.006945"},
            "primary_source_staleness_score",
        ),
        (
            "clear",
            {"primary_source_stale": True},
            "primary_source_stale",
        ),
        (
            "clear",
            {"drift_pressure_score": "0.028737"},
            "drift_pressure_score",
        ),
        (
            "clear",
            {
                "status": "watch",
                "reason_codes": ["primary_signal_drift_watch"],
            },
            "status",
        ),
        (
            "watch",
            {"reason_codes": ["corroboration_gap_watch"]},
            "reason_codes",
        ),
    ),
)
def test_resigned_payload_rejects_every_row_derived_field(
    base_kind: str,
    changes: dict[str, object],
    expected_error: str,
) -> None:
    api = _api()
    row_input = (
        _input()
        if base_kind == "clear"
        else _input(
            current_primary_signal_score=d("0.800000"),
            baseline_primary_signal_score=d("0.500000"),
        )
    )
    payload = api.research_source_primary_signal_drift_watch_report_payload(
        _report((row_input,)),
    )
    tampered = _mutable_payload(payload)
    tampered["rows"][0].update(changes)
    _resign_payload(tampered)

    with pytest.raises(ValueError, match=expected_error):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            tampered,
        )


@pytest.mark.parametrize(
    ("field_name", "tampered_value"),
    (
        ("observed_signal_count", "4.000000"),
        ("pass_signal_count", "2.000000"),
        ("watch_signal_count", "2.000000"),
        ("block_signal_count", "2.000000"),
        ("stale_primary_source_count", "1.000000"),
        ("missing_primary_source_count", "0.000000"),
        ("max_primary_signal_drift_score", "0.600000"),
        ("max_primary_source_age_seconds", "80000.000000"),
        ("max_drift_pressure_score", "0.700000"),
        ("watch_ratio", "0.500000"),
        ("block_ratio", "0.500000"),
        ("status", "watch"),
        ("reason_codes", ["primary_signal_drift_watch_clear"]),
    ),
)
def test_resigned_payload_rejects_every_report_derived_field(
    field_name: str,
    tampered_value: object,
) -> None:
    api = _api()
    payload = _mixed_payload()
    payload[field_name] = tampered_value
    _resign_payload(payload)

    with pytest.raises(ValueError, match=field_name):
        api.validate_research_source_primary_signal_drift_watch_report_payload(payload)


def test_duplicate_signal_buckets_and_reason_codes_are_rejected_after_resigning() -> None:
    api = _api()

    with pytest.raises(ValueError, match="signal_bucket values must be unique"):
        _report((_input("duplicate-bucket"), _input("duplicate-bucket")))

    payload = api.research_source_primary_signal_drift_watch_report_payload(
        _report((_input(),)),
    )
    duplicate_row_reason = _mutable_payload(payload)
    duplicate_row_reason["rows"][0]["reason_codes"].append(
        duplicate_row_reason["rows"][0]["reason_codes"][0],
    )
    _resign_payload(duplicate_row_reason)
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            duplicate_row_reason,
        )

    duplicate_report_reason = _mutable_payload(payload)
    duplicate_report_reason["reason_codes"].append(
        duplicate_report_reason["reason_codes"][0],
    )
    _resign_payload(duplicate_report_reason)
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            duplicate_report_reason,
        )


def test_payload_embeds_canonical_config_for_custom_config_recalculation() -> None:
    api = _api()
    custom_config = _config(
        primary_signal_drift_weight=d("0.333333"),
        primary_source_staleness_weight=d("0.333333"),
        corroboration_gap_weight=d("0.333334"),
        official_conflict_weight=ZERO,
        evidence_revision_weight=ZERO,
    )
    payload = api.research_source_primary_signal_drift_watch_report_payload(
        _report(
            (
                _input(
                    current_primary_signal_score=d("0.987654"),
                    baseline_primary_signal_score=d("0.123456"),
                    corroboration_gap_score=d("0.234567"),
                ),
            ),
            cfg=custom_config,
        ),
    )

    assert tuple(payload["config"]) == (
        "config_version",
        "watch_primary_signal_drift_score",
        "block_primary_signal_drift_score",
        "watch_primary_source_age_seconds",
        "block_primary_source_age_seconds",
        "watch_corroboration_gap_score",
        "block_corroboration_gap_score",
        "watch_official_conflict_score",
        "block_official_conflict_score",
        "watch_evidence_revision_score",
        "block_evidence_revision_score",
        "watch_drift_pressure_score",
        "block_drift_pressure_score",
        "primary_signal_drift_weight",
        "primary_source_staleness_weight",
        "corroboration_gap_weight",
        "official_conflict_weight",
        "evidence_revision_weight",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert payload["config"]["primary_signal_drift_weight"] == "0.333333"
    assert api.validate_research_source_primary_signal_drift_watch_report_payload(
        payload,
    )

    tampered_config = _mutable_payload(payload)
    tampered_config["config"]["primary_signal_drift_weight"] = "0.400000"
    tampered_config["config"]["primary_source_staleness_weight"] = "0.266666"
    _resign_payload(tampered_config)
    with pytest.raises(ValueError, match="drift_pressure_score"):
        api.validate_research_source_primary_signal_drift_watch_report_payload(
            tampered_config,
        )


def test_sorting_uses_complete_severity_tiebreakers_before_public_identifier() -> None:
    api = _api()
    report = _report(
        (
            _input(
                "a-corroboration-gap",
                current_primary_signal_score=d("0.700000"),
                baseline_primary_signal_score=d("0.500000"),
                corroboration_gap_score=d("0.466667"),
            ),
            _input(
                "z-primary-drift",
                current_primary_signal_score=d("0.900000"),
                baseline_primary_signal_score=d("0.500000"),
                corroboration_gap_score=ZERO,
            ),
        ),
    )

    assert report.rows[0].drift_pressure_score == report.rows[1].drift_pressure_score
    assert report.rows[0].primary_source_age_seconds == report.rows[1].primary_source_age_seconds
    assert tuple(row.signal_bucket for row in report.rows) == (
        "z-primary-drift",
        "a-corroboration-gap",
    )
    first = report.rows[0]
    assert api._row_sort_key(first) == (
        1,
        1,
        1,
        first.drift_pressure_score.copy_negate(),
        first.primary_signal_drift_score.copy_negate(),
        first.current_primary_signal_score.copy_negate(),
        first.baseline_primary_signal_score.copy_negate(),
        first.primary_source_staleness_score.copy_negate(),
        first.primary_source_age_seconds.copy_negate(),
        first.corroboration_gap_score.copy_negate(),
        first.official_conflict_score.copy_negate(),
        first.evidence_revision_score.copy_negate(),
        first.signal_bucket,
    )


@pytest.mark.parametrize(
    ("field_name", "first_value", "second_value"),
    (
        ("status", "block", "watch"),
        ("primary_source_available", False, True),
        ("primary_source_stale", True, False),
        ("drift_pressure_score", d("0.900000"), d("0.800000")),
        ("primary_signal_drift_score", d("0.900000"), d("0.800000")),
        ("current_primary_signal_score", d("0.900000"), d("0.800000")),
        ("baseline_primary_signal_score", d("0.900000"), d("0.800000")),
        ("primary_source_staleness_score", d("0.900000"), d("0.800000")),
        ("primary_source_age_seconds", d("900.000000"), d("800.000000")),
        ("corroboration_gap_score", d("0.900000"), d("0.800000")),
        ("official_conflict_score", d("0.900000"), d("0.800000")),
        ("evidence_revision_score", d("0.900000"), d("0.800000")),
        ("signal_bucket", "a-bucket", "b-bucket"),
    ),
)
def test_every_sort_tiebreak_component_is_effective(
    field_name: str,
    first_value: object,
    second_value: object,
) -> None:
    api = _api()
    first_overrides = {field_name: first_value}
    second_overrides = {field_name: second_value}
    first_bucket = str(first_overrides.pop("signal_bucket", "first-bucket"))
    second_bucket = str(second_overrides.pop("signal_bucket", "second-bucket"))
    first = _sort_row(first_bucket, **first_overrides)
    second = _sort_row(second_bucket, **second_overrides)

    ordered = tuple(sorted((second, first), key=api._row_sort_key))

    assert ordered == (first, second)


def _mutable_payload(payload: dict[str, Any]) -> dict[str, Any]:
    value = json.loads(json.dumps(payload))
    assert type(value) is dict
    return value


def _resign_payload(payload: dict[str, Any]) -> None:
    payload["derived_validation_digest"] = sha256(
        json.dumps(
            _without_digest_fields(payload),
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()


def _without_digest_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_digest_fields(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [_without_digest_fields(item) for item in value]
    return value


def _contains_float_or_int(value: object) -> bool:
    if isinstance(value, dict):
        return any(_contains_float_or_int(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float_or_int(item) for item in value)
    return type(value) in (float, int)


def _has_forbidden_public_key(value: object) -> bool:
    forbidden = (
        "raw_" + "candidate_id",
        "candidate_" + "id",
        "market_" + "id",
        "market_" + "slug",
        "sl" + "ug",
        "ques" + "tion",
        "source_" + "url",
        "source_" + "text",
        "d" + "sn",
        "ta" + "ble_name",
        "to" + "ken",
        "wall" + "et",
        "or" + "der",
        "tra" + "de",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            if any(term in str(key).lower() for term in forbidden):
                return True
            if _has_forbidden_public_key(item):
                return True
    if isinstance(value, list):
        return any(_has_forbidden_public_key(item) for item in value)
    return False


def _mixed_payload() -> dict[str, Any]:
    api = _api()
    return api.research_source_primary_signal_drift_watch_report_payload(
        _report(
            (
                _input(),
                _input(
                    "watch-bucket",
                    primary_source_age_seconds=d("7200.000000"),
                    current_primary_signal_score=d("0.650000"),
                    baseline_primary_signal_score=d("0.400000"),
                    corroboration_gap_score=d("0.350000"),
                    official_conflict_score=d("0.300000"),
                    evidence_revision_score=d("0.200000"),
                ),
                _input(
                    "block-bucket",
                    primary_source_age_seconds=d("90000.000000"),
                    current_primary_signal_score=d("0.900000"),
                    baseline_primary_signal_score=d("0.200000"),
                    corroboration_gap_score=d("0.750000"),
                    official_conflict_score=d("0.600000"),
                    evidence_revision_score=d("0.650000"),
                    primary_source_available=False,
                ),
            ),
        ),
    )


def _sort_row(signal_bucket: str, **overrides: object):
    api = _api()
    values: dict[str, object] = {
        "signal_bucket": signal_bucket,
        "status": "block",
        "current_primary_signal_score": d("0.500000"),
        "baseline_primary_signal_score": d("0.400000"),
        "primary_signal_drift_score": d("0.100000"),
        "primary_source_age_seconds": d("100.000000"),
        "primary_source_staleness_score": d("0.100000"),
        "corroboration_gap_score": d("0.100000"),
        "official_conflict_score": d("0.100000"),
        "evidence_revision_score": d("0.100000"),
        "drift_pressure_score": d("0.100000"),
        "primary_source_available": True,
        "primary_source_stale": False,
    }
    values.update(overrides)
    status = str(values["status"])
    if status == "pass":
        reason_codes = ("primary_signal_drift_watch_clear",)
    else:
        reason_codes_list: list[str] = []
        if values["primary_source_available"] is False:
            reason_codes_list.append("missing_primary_source_block")
        reason_codes_list.append(f"primary_signal_drift_{status}")
        if values["primary_source_stale"] is True:
            reason_codes_list.append(f"primary_source_stale_{status}")
        reason_codes = tuple(reason_codes_list)
    return api.ResearchSourcePrimarySignalDriftWatchRow(
        **values,
        reason_codes=reason_codes,
    )


def _ast_terminal_name(value: ast.AST) -> str | None:
    if isinstance(value, ast.Name):
        return value.id
    if isinstance(value, ast.Attribute):
        return value.attr
    return None
