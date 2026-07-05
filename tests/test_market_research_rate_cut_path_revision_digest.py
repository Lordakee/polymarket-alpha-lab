from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_research_rate_cut_path_revision_digest"
GENERATED_AT = datetime(2026, 7, 3, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def test_rate_cut_path_revision_digest_public_api_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_rate_cut_path_revision_digest_reduces_rows_and_sorts_deterministically() -> None:
    digest = digest_module()

    summary = report(
        digest,
        (
            input_row(
                digest,
                "research.fed.path.sept",
                condition_id="condition_fed_sept",
                rate_path_key="fed.path.sept",
                public_path_reference="https://rates.example/fomc?token=secret-123",
                observed_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=None,
                source_count=d("1.000000"),
                expected_cuts_before=d("2.000000"),
                expected_cuts_after=d("1.250000"),
                path_probability_before=d("0.620000"),
                path_probability_after=d("0.400000"),
                path_config_version="rate-cut-path-v1",
            ),
            input_row(
                digest,
                "research.fed.path.dec",
                condition_id="condition_fed_dec",
                rate_path_key="fed.path.dec",
                public_path_reference="private-rate-cut-path-feed",
                observed_at=GENERATED_AT - timedelta(hours=2, minutes=15),
                acknowledged_at=GENERATED_AT - timedelta(minutes=70),
                source_count=d("2.000000"),
                expected_cuts_before=d("1.000000"),
                expected_cuts_after=d("1.200000"),
                path_probability_before=d("0.510000"),
                path_probability_after=d("0.540000"),
                path_config_version="rate-cut-path-v1",
            ),
            input_row(
                digest,
                "research.fed.path.june",
                condition_id="condition_fed_june",
                rate_path_key="fed.path.june",
                public_path_reference="fomc-rate-cut-calendar",
                observed_at=GENERATED_AT - timedelta(minutes=30),
                acknowledged_at=GENERATED_AT - timedelta(minutes=20),
                source_count=d("3.000000"),
                expected_cuts_before=d("0.500000"),
                expected_cuts_after=d("0.520000"),
                path_probability_before=d("0.480000"),
                path_probability_after=d("0.490000"),
                path_config_version="rate-cut-path-v0",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        digest.DEFAULT_MARKET_RESEARCH_RATE_CUT_PATH_REVISION_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_rate_cut_path_revision_digest"
    )
    assert summary.path_count == d("3.000000")
    assert summary.ready_path_count == d("1.000000")
    assert summary.watch_path_count == d("1.000000")
    assert summary.blocked_path_count == d("1.000000")
    assert summary.material_revision_count == d("1.000000")
    assert summary.stale_path_count == d("2.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_acknowledgement_count == d("1.000000")
    assert summary.slow_acknowledgement_count == d("1.000000")
    assert summary.probability_repricing_count == d("1.000000")
    assert summary.average_expected_cut_revision_abs == d("0.323333")
    assert summary.average_probability_delta_abs == d("0.086667")
    assert summary.max_signal_age_seconds == d("10800.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.rate_path_key, row.research_key) for row in summary.rows) == (
        ("fed.path.sept", "research.fed.path.sept"),
        ("fed.path.dec", "research.fed.path.dec"),
        ("fed.path.june", "research.fed.path.june"),
    )

    sept = summary.rows[0]
    assert sept.revision_status == "blocked"
    assert sept.signal_age_seconds == d("10800.000000")
    assert sept.acknowledgement_lag_seconds is None
    assert sept.expected_cut_revision_delta == d("-0.750000")
    assert sept.expected_cut_revision_abs == d("0.750000")
    assert sept.probability_delta == d("-0.220000")
    assert sept.redacted_public_path_reference == redacted(
        "https://rates.example/fomc?token=secret-123",
    )
    assert sept.reason_codes == (
        "market_research_rate_cut_path_revision_digest_material_revision",
        "market_research_rate_cut_path_revision_digest_probability_repricing",
        "market_research_rate_cut_path_revision_digest_missing_acknowledgement",
        "market_research_rate_cut_path_revision_digest_stale_path",
        "market_research_rate_cut_path_revision_digest_thin_sources",
    )

    dec = summary.rows[1]
    assert dec.revision_status == "watch"
    assert dec.signal_age_seconds == d("8100.000000")
    assert dec.acknowledgement_lag_seconds == d("3900.000000")
    assert dec.expected_cut_revision_delta == d("0.200000")
    assert dec.expected_cut_revision_abs == d("0.200000")
    assert dec.probability_delta == d("0.030000")
    assert dec.redacted_public_path_reference == redacted("private-rate-cut-path-feed")
    assert dec.reason_codes == (
        "market_research_rate_cut_path_revision_digest_slow_acknowledgement",
        "market_research_rate_cut_path_revision_digest_stale_path",
    )

    june = summary.rows[2]
    assert june.revision_status == "ready"
    assert june.signal_age_seconds == d("1800.000000")
    assert june.acknowledgement_lag_seconds == d("600.000000")
    assert june.expected_cut_revision_delta == d("0.020000")
    assert june.expected_cut_revision_abs == d("0.020000")
    assert june.probability_delta == d("0.010000")
    assert june.redacted_public_path_reference == "fomc-rate-cut-calendar"
    assert june.reason_codes == (
        "market_research_rate_cut_path_revision_digest_ready",
    )

    assert summary.reason_code_counts == (
        digest.MarketResearchRateCutPathRevisionDigestReasonCodeCount(
            reason_code="market_research_rate_cut_path_revision_digest_stale_path",
            count=d("2.000000"),
            path_ratio=d("0.666667"),
        ),
        digest.MarketResearchRateCutPathRevisionDigestReasonCodeCount(
            reason_code="market_research_rate_cut_path_revision_digest_material_revision",
            count=d("1.000000"),
            path_ratio=d("0.333333"),
        ),
        digest.MarketResearchRateCutPathRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_rate_cut_path_revision_digest_probability_repricing"
            ),
            count=d("1.000000"),
            path_ratio=d("0.333333"),
        ),
        digest.MarketResearchRateCutPathRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_rate_cut_path_revision_digest_missing_acknowledgement"
            ),
            count=d("1.000000"),
            path_ratio=d("0.333333"),
        ),
        digest.MarketResearchRateCutPathRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_rate_cut_path_revision_digest_ready"
            ),
            count=d("1.000000"),
            path_ratio=d("0.333333"),
        ),
        digest.MarketResearchRateCutPathRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_rate_cut_path_revision_digest_slow_acknowledgement"
            ),
            count=d("1.000000"),
            path_ratio=d("0.333333"),
        ),
        digest.MarketResearchRateCutPathRevisionDigestReasonCodeCount(
            reason_code="market_research_rate_cut_path_revision_digest_thin_sources",
            count=d("1.000000"),
            path_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.path_config_versions == (
        ("fed.path.dec", "rate-cut-path-v1"),
        ("fed.path.june", "rate-cut-path-v0"),
        ("fed.path.sept", "rate-cut-path-v1"),
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "rates.example",
        "https://",
        "private-rate-cut-path-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "wallet",
        "account",
        "advice",
        "network",
        "database",
        "token",
        "secret",
        "private",
    ):
        assert token not in public


def test_empty_rate_cut_path_revision_digest_is_blocked_and_report_only() -> None:
    digest = digest_module()
    summary = report(digest, ())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_rate_cut_path_revision_digest"
    )
    assert summary.path_count == ZERO
    assert summary.ready_path_count == ZERO
    assert summary.watch_path_count == ZERO
    assert summary.blocked_path_count == ZERO
    assert summary.average_expected_cut_revision_abs == ZERO
    assert summary.average_probability_delta_abs == ZERO
    assert summary.max_signal_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.path_config_versions == ()
    assert summary.reason_code_counts == (
        digest.MarketResearchRateCutPathRevisionDigestReasonCodeCount(
            reason_code="market_research_rate_cut_path_revision_digest_no_inputs",
            count=d("1.000000"),
            path_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_rate_cut_path_revision_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_rate_cut_path_revision_digest_payload_uses_decimal_strings() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))
    payload = digest.market_research_rate_cut_path_revision_digest_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["path_count"] == "1.000000"
    assert payload["average_expected_cut_revision_abs"] == "0.020000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["expected_cut_revision_abs"] == "0.020000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert_six_decimal_public_numeric_payload(payload)
    assert "'public_path_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_rate_cut_path_revision_digest_payload_revalidates_public_tree() -> None:
    digest = digest_module()

    mutated_report_flag = report(digest, (input_row(digest),))
    object.__setattr__(mutated_report_flag, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        digest.market_research_rate_cut_path_revision_digest_payload(mutated_report_flag)

    mutated_row_flag = report(digest, (input_row(digest),))
    object.__setattr__(mutated_row_flag.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        digest.market_research_rate_cut_path_revision_digest_payload(mutated_row_flag)

    mutated_numeric = report(digest, (input_row(digest),))
    object.__setattr__(mutated_numeric, "path_count", 1)
    with pytest.raises(ValueError, match="Decimal|numeric"):
        digest.market_research_rate_cut_path_revision_digest_payload(mutated_numeric)

    mutated_reference = report(digest, (input_row(digest),))
    object.__setattr__(
        mutated_reference.rows[0],
        "redacted_public_path_reference",
        "sha256:secretsecret",
    )
    with pytest.raises(ValueError, match="redacted|sha256"):
        digest.market_research_rate_cut_path_revision_digest_payload(mutated_reference)


def test_rate_cut_path_revision_digest_validates_public_contracts_and_flags() -> None:
    digest = digest_module()

    assert digest.MarketResearchRateCutPathRevisionDigestConfig.__dataclass_params__.frozen
    assert digest.MarketResearchRateCutPathRevisionDigestInputRow.__dataclass_params__.frozen
    assert digest.MarketResearchRateCutPathRevisionDigestRow.__dataclass_params__.frozen
    assert (
        digest.MarketResearchRateCutPathRevisionDigestReasonCodeCount
        .__dataclass_params__
        .frozen
    )
    assert digest.MarketResearchRateCutPathRevisionDigestReport.__dataclass_params__.frozen

    summary = report(digest, (input_row(digest),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("4.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(digest, config_version=_StringSubclass("rate-cut-path-revision-v0"))
    with pytest.raises(ValueError, match="max_path_signal_age_seconds"):
        config(digest, max_path_signal_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="material_expected_cut_revision_threshold"):
        config(digest, material_expected_cut_revision_threshold=0.25)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="research_key"):
        input_row(digest, research_key=" bad")
    with pytest.raises(ValueError, match="central_bank"):
        input_row(digest, central_bank="fed private")
    with pytest.raises(ValueError, match="observed_at"):
        input_row(digest, observed_at=datetime(2026, 7, 3, 15, 0))
    with pytest.raises(ValueError, match="observed_at"):
        input_row(
            digest,
            observed_at=datetime(2026, 7, 3, 15, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(
            digest,
            acknowledged_at=_DateTimeSubclass(2026, 7, 3, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_count"):
        input_row(digest, source_count=Decimal("1.5"))
    with pytest.raises(ValueError, match="expected_cuts_before"):
        input_row(digest, expected_cuts_before=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="expected_cuts_after"):
        input_row(digest, expected_cuts_after=Decimal("Infinity"))
    with pytest.raises(ValueError, match="path_probability_before"):
        input_row(digest, path_probability_before=d("1.000001"))
    with pytest.raises(ValueError, match="path_probability_after"):
        input_row(digest, path_probability_after=d("-0.000001"))
    with pytest.raises(ValueError, match="future"):
        report(
            digest,
            (input_row(digest, observed_at=GENERATED_AT + timedelta(seconds=1)),),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(digest), paper_only=False)
    with pytest.raises(ValueError, match="count"):
        digest.MarketResearchRateCutPathRevisionDigestReasonCodeCount(
            reason_code="market_research_rate_cut_path_revision_digest_ready",
            count=ZERO,
            path_ratio=ZERO,
        )
    with pytest.raises(ValueError, match="config"):
        digest.build_market_research_rate_cut_path_revision_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    for public_dataclass in (
        digest.MarketResearchRateCutPathRevisionDigestConfig,
        digest.MarketResearchRateCutPathRevisionDigestInputRow,
        digest.MarketResearchRateCutPathRevisionDigestRow,
        digest.MarketResearchRateCutPathRevisionDigestReasonCodeCount,
        digest.MarketResearchRateCutPathRevisionDigestReport,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Bad{public_dataclass.__name__}", (public_dataclass,), {})


def test_rate_cut_path_revision_digest_rejects_each_false_report_only_flag() -> None:
    digest = digest_module()
    ready_summary = report(digest, (input_row(digest),))
    ready_row = ready_summary.rows[0]
    reason_count = ready_summary.reason_code_counts[0]

    cases = (
        ("config paper_only", lambda: config(digest, paper_only=False)),
        ("config report_only", lambda: config(digest, report_only=False)),
        ("config readonly", lambda: config(digest, readonly=False)),
        ("input row paper_only", lambda: input_row(digest, paper_only=False)),
        ("input row report_only", lambda: input_row(digest, report_only=False)),
        ("input row readonly", lambda: input_row(digest, readonly=False)),
        ("row paper_only", lambda: replace(ready_row, paper_only=False)),
        ("row report_only", lambda: replace(ready_row, report_only=False)),
        ("row readonly", lambda: replace(ready_row, readonly=False)),
        ("reason count paper_only", lambda: replace(reason_count, paper_only=False)),
        ("reason count report_only", lambda: replace(reason_count, report_only=False)),
        ("reason count readonly", lambda: replace(reason_count, readonly=False)),
        ("report paper_only", lambda: replace(ready_summary, paper_only=False)),
        ("report report_only", lambda: replace(ready_summary, report_only=False)),
        ("report readonly", lambda: replace(ready_summary, readonly=False)),
    )

    for label, action in cases:
        flag_name = label.rsplit(" ", maxsplit=1)[1]
        with pytest.raises(ValueError, match=flag_name):
            action()


def test_rate_cut_path_revision_digest_rejects_duplicates_and_bad_consistency() -> None:
    digest = digest_module()

    with pytest.raises(ValueError, match="unique"):
        report(
            digest,
            (
                input_row(digest, rate_path_key="fed.path.duplicate"),
                input_row(
                    digest,
                    "research.fed.path.duplicate-2",
                    rate_path_key="fed.path.duplicate",
                ),
            ),
        )

    ready = report(digest, (input_row(digest),)).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_rate_cut_path_revision_digest_ready",
                "market_research_rate_cut_path_revision_digest_stale_path",
            ),
        )
    with pytest.raises(ValueError, match="revision_status"):
        replace(ready, revision_status="blocked")
    with pytest.raises(ValueError, match="expected_cut_revision_delta"):
        replace(ready, expected_cut_revision_delta=d("9.999999"))
    with pytest.raises(ValueError, match="redacted_public_path_reference"):
        replace(ready, redacted_public_path_reference="https://host?token=secret")
    with pytest.raises(ValueError, match="redacted_public_path_reference"):
        replace(ready, redacted_public_path_reference="sha256:secretsecret")

    with pytest.raises(ValueError, match="ready_path_count"):
        replace(report(digest, (input_row(digest),)), ready_path_count=ZERO)
    with pytest.raises(ValueError, match="path_config_versions"):
        replace(
            report(digest, (input_row(digest),)),
            path_config_versions=(("fed.path.other", "rate-cut-path-v0"),),
        )
    multi_reason = report(
        digest,
        (
            input_row(
                digest,
                acknowledged_at=None,
                source_count=d("1.000000"),
                expected_cuts_after=d("0.900000"),
                path_probability_after=d("0.700000"),
            ),
        ),
    )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            multi_reason.rows[0],
            reason_codes=tuple(reversed(multi_reason.rows[0].reason_codes)),
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            multi_reason,
            reason_code_counts=tuple(reversed(multi_reason.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            digest,
            (
                input_row(digest, "research.fed.path.z", rate_path_key="fed.path.z"),
                input_row(digest),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="path_config_versions"):
        replace(
            unordered,
            path_config_versions=tuple(reversed(unordered.path_config_versions)),
        )


def test_public_numeric_count_ratio_fields_are_decimals() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))

    assert_decimal_public_numeric_fields(digest.MarketResearchRateCutPathRevisionDigestConfig())
    assert_decimal_public_numeric_fields(input_row(digest))
    assert_decimal_public_numeric_fields(summary)
    assert_decimal_public_numeric_fields(summary.rows[0])
    assert_decimal_public_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/market_research_rate_cut_path_revision_digest.py",
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: set[str] = set()
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "websocket",
        "aiohttp",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "pathlib",
        "openai",
        "boto",
        "ccxt",
        "subprocess",
    )
    forbidden_call_or_attribute_names = (
        "connect",
        "execute",
        "fetch",
        "get",
        "post",
        "put",
        "delete",
        "request",
        "open",
        "read",
        "write",
        "mkdir",
        "unlink",
        "rename",
        "submit",
        "cancel",
        "order",
        "trade",
        "wallet",
        "broker",
        "account",
        "sign",
        "auth",
    )

    lowered_imports = tuple(name.lower() for name in imported_modules)
    lowered_surface = tuple(name.lower() for name in (*call_names, *attribute_names))
    assert not any(
        fragment in module_name
        for module_name in lowered_imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in lowered_surface)
    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit_order",
        "cancel_order",
        "account",
        "advice",
    ):
        assert forbidden not in source.lower()


def d(value: str) -> Decimal:
    return Decimal(value)


def redacted(value: str) -> str:
    import hashlib

    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def digest_module() -> Any:
    return importlib.import_module(MODULE_NAME)


def config(digest: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            digest.DEFAULT_MARKET_RESEARCH_RATE_CUT_PATH_REVISION_DIGEST_CONFIG_VERSION
        ),
        "max_path_signal_age_seconds": d("7200.000000"),
        "material_expected_cut_revision_threshold": d("0.250000"),
        "min_probability_repricing_abs": d("0.050000"),
        "min_source_count": d("2.000000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchRateCutPathRevisionDigestConfig(**values)


def input_row(
    digest: Any,
    research_key: str = "research.fed.path.june",
    *,
    condition_id: str = "condition_fed_june",
    rate_path_key: str = "fed.path.june",
    central_bank: str = "fed",
    policy_event_key: str = "fomc.statement",
    public_path_reference: str = "fomc-rate-cut-calendar",
    observed_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3.000000"),
    expected_cuts_before: Decimal = d("0.500000"),
    expected_cuts_after: Decimal = d("0.520000"),
    path_probability_before: Decimal = d("0.480000"),
    path_probability_after: Decimal = d("0.490000"),
    path_config_version: str = "rate-cut-path-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return digest.MarketResearchRateCutPathRevisionDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        rate_path_key=rate_path_key,
        central_bank=central_bank,
        policy_event_key=policy_event_key,
        public_path_reference=public_path_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=20)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        expected_cuts_before=expected_cuts_before,
        expected_cuts_after=expected_cuts_after,
        path_probability_before=path_probability_before,
        path_probability_after=path_probability_after,
        path_config_version=path_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    digest: Any,
    rows: tuple[object, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return digest.build_market_research_rate_cut_path_revision_digest(
        rows,
        config=cfg or config(digest),
        generated_at=generated_at,
    )


def walk_values(value: object) -> list[object]:
    if isinstance(value, dict):
        return [item for child in value.values() for item in walk_values(child)]
    if isinstance(value, list):
        return [item for child in value for item in walk_values(child)]
    return [value]


def assert_decimal_public_numeric_fields(value: object) -> None:
    assert is_dataclass(value)
    numeric_markers = (
        "age_seconds",
        "average",
        "count",
        "cuts",
        "delta",
        "lag_seconds",
        "max_",
        "min_",
        "probability",
        "ratio",
        "threshold",
    )
    for field in fields(value):
        field_value = getattr(value, field.name)
        if field.name.endswith(("codes", "counts", "versions")):
            continue
        if any(marker in field.name for marker in numeric_markers):
            if field_value is not None:
                assert type(field_value) is Decimal, field.name


def assert_six_decimal_public_numeric_payload(value: object) -> None:
    numeric_markers = (
        "age_seconds",
        "average",
        "count",
        "cuts",
        "delta",
        "lag_seconds",
        "max_",
        "min_",
        "probability",
        "ratio",
        "threshold",
    )

    def walk(item: object, path: tuple[str, ...]) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                walk(child, (*path, str(key)))
            return
        if isinstance(item, list):
            for child in item:
                walk(child, path)
            return
        if not path or item is None:
            return
        field_name = path[-1]
        if not any(marker in field_name for marker in numeric_markers):
            return
        assert type(item) is str, field_name
        integer, dot, fraction = item.partition(".")
        assert integer
        assert dot == ".", field_name
        assert len(fraction) == 6, field_name
        Decimal(item)

    walk(value, ())
