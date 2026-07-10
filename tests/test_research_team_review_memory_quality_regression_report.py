from __future__ import annotations

import ast
from collections import Counter
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_review_memory_quality_regression_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_review_memory_quality_regression_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-review-memory-quality-regression-test",
        "max_pass_stale_memory_reuse_rate": d("0.050000"),
        "max_watch_stale_memory_reuse_rate": d("0.200000"),
        "min_pass_correction_followthrough_score": d("0.900000"),
        "min_watch_correction_followthrough_score": d("0.700000"),
        "max_pass_calibration_drop_score": d("0.020000"),
        "max_watch_calibration_drop_score": d("0.100000"),
        "min_pass_evidence_coverage_score": d("0.900000"),
        "min_watch_evidence_coverage_score": d("0.700000"),
        "min_pass_contradiction_handling_score": d("0.900000"),
        "min_watch_contradiction_handling_score": d("0.700000"),
        "max_pass_review_latency_hours": d("12.000000"),
        "max_watch_review_latency_hours": d("36.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamReviewMemoryQualityRegressionConfig(**values)


def snapshot(**overrides: object):
    module = api()
    values = {
        "team_key": "macro_review",
        "reviewed_item_count": d("20"),
        "stale_memory_reuse_count": d("0"),
        "correction_required_count": d("10"),
        "correction_completed_count": d("10"),
        "calibration_prior_score": d("0.800000"),
        "calibration_current_score": d("0.820000"),
        "evidence_required_count": d("40"),
        "evidence_confirmed_count": d("38"),
        "contradiction_flag_count": d("5"),
        "contradiction_resolved_count": d("5"),
        "mean_review_latency_hours": d("6.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamReviewMemoryQualityRegressionSnapshot(**values)


def build_report(
    *items: object,
    cfg=None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_team_review_memory_quality_regression_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, bool) or value is None:
        return
    if type(value) in (int, float):
        raise AssertionError(f"unexpected non-Decimal numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if isinstance(value, datetime):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "position",
        "recommend",
        "sizing",
        "source",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def resign_payload(payload: dict[str, Any]) -> None:
    values = dict(payload)
    values.pop("public_digest", None)
    encoded = json.dumps(
        values,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    payload["public_digest"] = hashlib.sha256(encoded).hexdigest()


def refresh_reason_code_counts(payload: dict[str, Any]) -> None:
    counter: Counter[str] = Counter(payload["reason_codes"])
    for row in payload["rows"]:
        counter.update(row["reason_codes"])
    payload["reason_code_counts"] = [
        {
            "reason_code": reason_code,
            "count": f"{counter[reason_code]:.6f}",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
        for reason_code in api()._REASON_CODE_SEQUENCE
        if counter[reason_code]
    ]


def forge_row_score(payload: dict[str, Any]) -> None:
    payload["rows"][0]["quality_regression_score"] = "0.100000"
    payload["mean_quality_regression_score"] = "0.100000"
    payload["max_quality_regression_score"] = "0.100000"


def forge_row_reasons(payload: dict[str, Any]) -> None:
    payload["rows"][0]["reason_codes"][1] = "stale_memory_reuse_watch"
    refresh_reason_code_counts(payload)


def forge_row_status(payload: dict[str, Any]) -> None:
    payload["rows"][0]["status"] = "watch"
    payload["rows"][0]["reason_codes"][0] = "review_memory_quality_regression_watch"
    payload["rows"][0]["reason_codes"][1] = "stale_memory_reuse_watch"
    payload["pass_count"] = "0.000000"
    payload["watch_count"] = "1.000000"
    payload["status"] = "watch"
    payload["reason_codes"] = [
        "review_memory_quality_regression_report_watch_rows",
    ]
    refresh_reason_code_counts(payload)


def test_public_api_declares_report_only_regression_contract() -> None:
    module = api()

    assert module.DEFAULT_RESEARCH_TEAM_REVIEW_MEMORY_QUALITY_REGRESSION_CONFIG_VERSION == (
        "research-team-review-memory-quality-regression-report-v0"
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_REVIEW_MEMORY_QUALITY_REGRESSION_CONFIG_VERSION",
        "ResearchTeamReviewMemoryQualityRegressionConfig",
        "ResearchTeamReviewMemoryQualityRegressionReasonCodeCount",
        "ResearchTeamReviewMemoryQualityRegressionReport",
        "ResearchTeamReviewMemoryQualityRegressionRow",
        "ResearchTeamReviewMemoryQualityRegressionSnapshot",
        "build_research_team_review_memory_quality_regression_report",
        "research_team_review_memory_quality_regression_report_digest",
        "research_team_review_memory_quality_regression_report_payload",
    )

    for public_type in (
        module.ResearchTeamReviewMemoryQualityRegressionConfig,
        module.ResearchTeamReviewMemoryQualityRegressionReasonCodeCount,
        module.ResearchTeamReviewMemoryQualityRegressionReport,
        module.ResearchTeamReviewMemoryQualityRegressionRow,
        module.ResearchTeamReviewMemoryQualityRegressionSnapshot,
    ):
        assert is_dataclass(public_type)
        defaults = {field.name: field.default for field in fields(public_type)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True


def test_detects_review_memory_quality_regression_across_required_dimensions() -> None:
    report = build_report(
        snapshot(team_key="macro_review"),
        snapshot(
            team_key="policy_review",
            reviewed_item_count=d("10"),
            stale_memory_reuse_count=d("1"),
            correction_required_count=d("10"),
            correction_completed_count=d("7"),
            calibration_prior_score=d("0.800000"),
            calibration_current_score=d("0.740000"),
            evidence_required_count=d("20"),
            evidence_confirmed_count=d("15"),
            contradiction_flag_count=d("4"),
            contradiction_resolved_count=d("3"),
            mean_review_latency_hours=d("20.000000"),
        ),
        snapshot(
            team_key="sports_review",
            reviewed_item_count=d("5"),
            stale_memory_reuse_count=d("2"),
            correction_required_count=d("5"),
            correction_completed_count=d("2"),
            calibration_prior_score=d("0.850000"),
            calibration_current_score=d("0.650000"),
            evidence_required_count=d("10"),
            evidence_confirmed_count=d("5"),
            contradiction_flag_count=d("3"),
            contradiction_resolved_count=d("1"),
            mean_review_latency_hours=d("72.000000"),
        ),
    )

    assert report.status == "block"
    assert report.team_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.mean_stale_memory_reuse_rate == d("0.166667")
    assert report.mean_correction_followthrough_score == d("0.700000")
    assert report.mean_calibration_drop_score == d("0.086667")
    assert report.mean_evidence_coverage_score == d("0.733333")
    assert report.mean_contradiction_handling_score == d("0.694444")
    assert report.mean_review_latency_hours == d("32.666667")
    assert report.mean_quality_regression_score == d("0.340719")
    assert report.max_quality_regression_score == d("0.716601")
    assert report.reason_codes == (
        "review_memory_quality_regression_report_block_rows",
        "review_memory_quality_regression_report_watch_rows",
    )

    assert tuple(row.team_key for row in report.rows) == (
        "macro_review",
        "policy_review",
        "sports_review",
    )
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert report.rows[0].quality_regression_score == d("0.000000")
    assert report.rows[1].stale_memory_reuse_rate == d("0.100000")
    assert report.rows[1].correction_followthrough_score == d("0.700000")
    assert report.rows[1].calibration_drop_score == d("0.060000")
    assert report.rows[1].quality_regression_score == d("0.305556")
    assert report.rows[2].contradiction_handling_score == d("0.333333")
    assert report.rows[2].quality_regression_score == d("0.716601")
    assert report.rows[2].reason_codes == (
        "review_memory_quality_regression_block",
        "stale_memory_reuse_high",
        "correction_followthrough_low",
        "calibration_trend_drop",
        "evidence_coverage_low",
        "contradiction_handling_low",
        "review_latency_slow",
    )


def test_empty_input_blocks_as_report_only_public_diagnostic() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.team_count == d("0.000000")
    assert report.block_count == d("1.000000")
    assert report.rows == ()
    assert report.reason_codes == ("review_memory_quality_regression_empty_input",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: snapshot(reviewed_item_count=20),
            "reviewed_item_count must be exactly Decimal",
        ),
        (
            lambda: snapshot(mean_review_latency_hours=_DecimalSubclass("6.000000")),
            "mean_review_latency_hours must be exactly Decimal",
        ),
        (
            lambda: snapshot(mean_review_latency_hours=d("6.0000001")),
            "mean_review_latency_hours must use six decimal places or fewer",
        ),
        (
            lambda: snapshot(stale_memory_reuse_count=d("1.500000")),
            "stale_memory_reuse_count must be a whole number",
        ),
        (
            lambda: snapshot(stale_memory_reuse_count=d("21")),
            "stale_memory_reuse_count must not exceed reviewed_item_count",
        ),
        (
            lambda: snapshot(evidence_required_count=d("0")),
            "evidence_required_count must be positive",
        ),
        (
            lambda: build_report(snapshot(), generated_at=datetime(2026, 7, 8, 12, 0)),
            "generated_at must be timezone-aware",
        ),
    ),
)
def test_strict_validation_rejects_numeric_shortcuts(
    factory: Any,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()


def test_hard_flags_are_enforced_and_public_dataclasses_are_frozen() -> None:
    module = api()
    cfg = config()
    item = snapshot()
    report = build_report(item)
    row = report.rows[0]
    count = report.reason_code_counts[0]

    for value in (cfg, item, row, count, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(value)

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchTeamReviewMemoryQualityRegressionConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_payload_and_digest_are_deterministic_decimal_stringed_and_status_limited() -> None:
    left = snapshot(team_key="policy_review")
    right = snapshot(team_key="macro_review")

    report_a = build_report(right, left)
    report_b = build_report(left, right)
    payload_a = report_a.payload
    payload_b = report_b.payload

    assert payload_a == payload_b
    assert report_a.public_digest == report_b.public_digest
    assert report_a.public_digest == payload_a["public_digest"]
    assert report_a.public_digest == api().research_team_review_memory_quality_regression_report_digest(
        report_a,
    )
    assert payload_a["team_count"] == "2.000000"
    assert payload_a["rows"][0]["quality_regression_score"] == "0.000000"
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert_no_float_or_int_values(payload_a)
    json.dumps(payload_a, sort_keys=True)
    canonical_values = dict(payload_a)
    canonical_values.pop("public_digest")
    expected_digest = hashlib.sha256(
        json.dumps(
            canonical_values,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert report_a.public_digest == expected_digest
    assert (
        api().research_team_review_memory_quality_regression_report_payload(
            dict(payload_a),
        )
        == payload_a
    )

    statuses = {report_a.status}
    statuses.update(row.status for row in report_a.rows)
    assert statuses <= {"pass", "watch", "block"}
    assert "blocked" not in statuses
    assert "ready" not in statuses


def test_report_materializes_config_thresholds_for_semantic_revalidation() -> None:
    cfg = config(
        max_pass_stale_memory_reuse_rate=d("0.040000"),
        max_watch_review_latency_hours=d("40.000000"),
    )
    report = build_report(snapshot(), cfg=cfg)
    payload = report.payload

    threshold_fields = (
        "max_pass_stale_memory_reuse_rate",
        "max_watch_stale_memory_reuse_rate",
        "min_pass_correction_followthrough_score",
        "min_watch_correction_followthrough_score",
        "max_pass_calibration_drop_score",
        "max_watch_calibration_drop_score",
        "min_pass_evidence_coverage_score",
        "min_watch_evidence_coverage_score",
        "min_pass_contradiction_handling_score",
        "min_watch_contradiction_handling_score",
        "max_pass_review_latency_hours",
        "max_watch_review_latency_hours",
    )
    for field_name in threshold_fields:
        assert getattr(report, field_name) == getattr(cfg, field_name)
        assert payload[field_name] == format(getattr(cfg, field_name), "f")


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (forge_row_score, "quality_regression_score must match row metrics"),
        (forge_row_reasons, "reason_codes must match row metrics"),
        (forge_row_status, "status must match row metrics"),
    ),
)
def test_public_payload_rejects_forged_resigned_derived_row_logic(
    mutate: Any,
    message: str,
) -> None:
    module = api()
    payload = json.loads(json.dumps(build_report(snapshot()).payload))

    mutate(payload)
    resign_payload(payload)

    with pytest.raises(ValueError, match=message):
        module.research_team_review_memory_quality_regression_report_payload(payload)


def test_public_payload_rejects_leaky_identifiers_and_execution_surface() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public value"):
        snapshot(team_key="raw_candidate_bucket")

    with pytest.raises(ValueError, match="unsafe public value"):
        snapshot(team_key="market_review")

    report = build_report(snapshot())
    payload = dict(report.payload)
    payload["market_reference"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_review_memory_quality_regression_report_payload(payload)

    row_payload = dict(report.payload)
    row_payload["rows"] = [dict(row_payload["rows"][0])]
    row_payload["rows"][0]["url_text"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_review_memory_quality_regression_report_payload(row_payload)

    assert_payload_has_no_forbidden_surface(report.payload)


def test_report_consistency_and_digest_validation_reject_tampering() -> None:
    module = api()
    report = build_report(snapshot())

    with pytest.raises(ValueError, match="pass_count must match rows"):
        replace(report, pass_count=d("0.000000"))

    with pytest.raises(ValueError, match="mean_stale_memory_reuse_rate must match rows"):
        replace(report, mean_stale_memory_reuse_rate=d("0.500000"))

    payload = dict(report.payload)
    payload["status"] = "watch"
    with pytest.raises(ValueError, match="public_digest must match payload fields"):
        module.research_team_review_memory_quality_regression_report_payload(payload)


def test_consumers_revalidate_frozen_instances_after_object_setattr_tampering() -> None:
    module = api()
    cfg = config()
    object.__setattr__(
        cfg,
        "max_pass_stale_memory_reuse_rate",
        d("0.900000"),
    )
    with pytest.raises(ValueError, match="max_pass_stale_memory_reuse_rate"):
        build_report(cfg=cfg)

    report = build_report(snapshot())
    object.__setattr__(
        report.rows[0],
        "quality_regression_score",
        d("0.100000"),
    )
    object.__setattr__(
        report,
        "mean_quality_regression_score",
        d("0.100000"),
    )
    object.__setattr__(
        report,
        "max_quality_regression_score",
        d("0.100000"),
    )
    object.__setattr__(
        report,
        "public_digest",
        module._digest_from_values(module._report_values_without_digest(report)),
    )

    with pytest.raises(ValueError, match="quality_regression_score must match row metrics"):
        _ = report.payload


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (
            lambda payload: payload.__setitem__("extra_field", "safe_value"),
            "payload fields must exactly match",
        ),
        (
            lambda payload: payload["rows"][0].__setitem__(
                "extra_field",
                "safe_value",
            ),
            "row payload fields must exactly match",
        ),
        (
            lambda payload: payload.__setitem__("team_count", "1"),
            "team_count must use canonical six-decimal string form",
        ),
        (
            lambda payload: payload.__setitem__(
                "reason_codes",
                tuple(payload["reason_codes"]),
            ),
            "reason_codes must be a list",
        ),
    ),
)
def test_public_payload_requires_exact_canonical_schema(
    mutate: Any,
    message: str,
) -> None:
    module = api()
    payload = dict(build_report(snapshot()).payload)
    payload["rows"] = [dict(row) for row in payload["rows"]]
    payload["reason_code_counts"] = [
        dict(item) for item in payload["reason_code_counts"]
    ]

    mutate(payload)
    resign_payload(payload)

    with pytest.raises(ValueError, match=message):
        module.research_team_review_memory_quality_regression_report_payload(payload)


@pytest.mark.parametrize("value", (d("NaN"), d("Infinity"), d("-Infinity")))
def test_non_finite_decimal_inputs_are_rejected_cleanly(value: Decimal) -> None:
    with pytest.raises(ValueError, match="mean_review_latency_hours must be finite"):
        snapshot(mean_review_latency_hours=value)


def test_signed_zero_is_canonicalized_and_resigned_payloads_reject_it() -> None:
    item = snapshot(
        stale_memory_reuse_count=d("-0.000000"),
        calibration_prior_score=d("-0.000000"),
        mean_review_latency_hours=d("-0.000000"),
    )
    for field_name in (
        "stale_memory_reuse_count",
        "calibration_prior_score",
        "mean_review_latency_hours",
    ):
        value = getattr(item, field_name)
        assert value == d("0.000000")
        assert not value.is_signed()

    report = build_report(item)
    assert "-0.000000" not in json.dumps(report.payload, sort_keys=True)

    payload = dict(build_report().payload)
    payload["team_count"] = "-0.000000"
    resign_payload(payload)
    with pytest.raises(ValueError, match="signed zero"):
        api().research_team_review_memory_quality_regression_report_payload(payload)


def test_report_and_digest_do_not_depend_on_ambient_decimal_context() -> None:
    cfg = config()
    item = snapshot(
        reviewed_item_count=d("123456"),
        stale_memory_reuse_count=d("1234"),
        mean_review_latency_hours=d("12.345678"),
    )
    expected = build_report(item, cfg=cfg)

    with localcontext() as context:
        context.prec = 6
        actual = build_report(item, cfg=cfg)

    assert actual == expected
    assert actual.payload == expected.payload
    assert actual.public_digest == expected.public_digest


def test_module_stays_pure_report_only_without_io_or_execution_imports() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_names: set[str] = set()
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_names.add(node.module.split(".")[0])
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    assert imported_names <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "re",
        "typing",
    }
    assert imported_names.isdisjoint(
        {
            "aiohttp",
            "boto3",
            "httpx",
            "os",
            "pathlib",
            "pickle",
            "requests",
            "shelve",
            "shutil",
            "socket",
            "sqlite3",
            "subprocess",
            "urllib",
            "psycopg",
            "psycopg2",
            "supabase",
            "sqlalchemy",
            "web3",
        },
    )
    assert call_names.isdisjoint(
        {
            "connect",
            "download",
            "request",
            "open",
            "post",
            "put",
            "delete",
            "execute",
            "executemany",
            "makedirs",
            "mkdir",
            "place_order",
            "remove",
            "send",
            "submit_order",
            "touch",
            "unlink",
            "upload",
            "write",
            "write_bytes",
            "write_text",
        },
    )
