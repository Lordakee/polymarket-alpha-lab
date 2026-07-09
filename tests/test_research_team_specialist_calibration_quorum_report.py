from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 10, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_team_specialist_calibration_quorum_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_team_specialist_calibration_quorum_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-specialist-calibration-quorum-report-v0",
        "min_quorum_specialist_count": d("3"),
        "min_pass_agreement_ratio": d("0.750000"),
        "min_watch_agreement_ratio": d("0.600000"),
        "max_pass_block_ratio": d("0.000000"),
        "max_watch_block_ratio": d("0.250000"),
        "min_pass_average_evidence_score": d("0.800000"),
        "min_watch_average_evidence_score": d("0.600000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistCalibrationQuorumConfig(**values)


def quorum_signal(**overrides: object):
    module = api()
    values = {
        "specialist_key": "sports_models",
        "calibration_group": "sports_calibration",
        "status": "pass",
        "evidence_score": d("0.950000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistCalibrationQuorumInput(**values)


def build_report(
    *items: object,
    cfg=None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_team_specialist_calibration_quorum_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)


def assert_public_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "raw",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "http://",
        "https://",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "buy",
        "sell",
        "recommend",
        "position",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def strip_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: strip_digest(item)
            for key, item in sorted(value.items())
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [strip_digest(item) for item in value]
    return value


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    canonical = json.dumps(
        strip_digest(payload),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload["derived_validation_digest"] = sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def assert_decimal_public_fields(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if field.name in {"paper_only", "report_only", "readonly"}:
            assert item is True
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
        if field.name.endswith(("_count", "_ratio", "_score")):
            assert type(item) is Decimal


def test_quorum_rolls_up_votes_and_blocks_when_agreement_is_too_low() -> None:
    report = build_report(
        quorum_signal(
            specialist_key="sports_models",
            calibration_group="sports_calibration",
            status="pass",
            evidence_score=d("0.950000"),
        ),
        quorum_signal(
            specialist_key="macro_models",
            calibration_group="macro_calibration",
            status="pass",
            evidence_score=d("0.850000"),
        ),
        quorum_signal(
            specialist_key="crypto_models",
            calibration_group="crypto_calibration",
            status="watch",
            evidence_score=d("0.700000"),
        ),
        quorum_signal(
            specialist_key="policy_models",
            calibration_group="policy_calibration",
            status="block",
            evidence_score=d("0.500000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-team-specialist-calibration-quorum-report-v0"
    assert report.specialist_count == d("4")
    assert report.pass_count == d("2")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.quorum_gap_count == d("0")
    assert report.agreement_ratio == d("0.500000")
    assert report.block_ratio == d("0.250000")
    assert report.average_evidence_score == d("0.750000")
    assert report.min_evidence_score == d("0.500000")
    assert report.consensus_status == "pass"
    assert report.status == "block"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked, watched, passed_low, passed_high = report.rows
    assert tuple((row.status, row.evidence_score) for row in report.rows) == (
        ("block", d("0.500000")),
        ("watch", d("0.700000")),
        ("pass", d("0.850000")),
        ("pass", d("0.950000")),
    )
    assert blocked.reason_codes == ("specialist_calibration_quorum_vote_block",)
    assert watched.reason_codes == ("specialist_calibration_quorum_vote_watch",)
    assert passed_low.reason_codes == ("specialist_calibration_quorum_vote_pass",)
    assert passed_high.reason_codes == ("specialist_calibration_quorum_vote_pass",)
    assert report.reason_codes == (
        "specialist_calibration_quorum_report_block",
        "specialist_calibration_quorum_agreement_block",
        "specialist_calibration_quorum_block_ratio_watch",
        "specialist_calibration_quorum_evidence_watch",
    )
    assert len(report.derived_validation_digest) == 64


def test_empty_and_below_quorum_reports_block() -> None:
    module = api()
    empty = build_report()

    assert empty.status == "block"
    assert empty.specialist_count == d("0")
    assert empty.quorum_gap_count == d("3")
    assert empty.rows == ()
    assert empty.reason_codes == ("specialist_calibration_quorum_no_rows",)
    assert empty.reason_code_counts == (
        module.ResearchTeamSpecialistCalibrationQuorumReasonCodeCount(
            reason_code="specialist_calibration_quorum_no_rows",
            count=d("1"),
            specialist_ratio=d("1.000000"),
        ),
    )

    thin = build_report(
        quorum_signal(specialist_key="sports_models"),
        quorum_signal(
            specialist_key="macro_models",
            calibration_group="macro_calibration",
        ),
    )
    assert thin.status == "block"
    assert thin.specialist_count == d("2")
    assert thin.quorum_gap_count == d("1")
    assert thin.reason_codes == (
        "specialist_calibration_quorum_report_block",
        "specialist_calibration_quorum_below_minimum",
    )

    strict = build_report(
        quorum_signal(specialist_key="sports_models"),
        quorum_signal(
            specialist_key="macro_models",
            calibration_group="macro_calibration",
        ),
        quorum_signal(
            specialist_key="crypto_models",
            calibration_group="crypto_calibration",
        ),
        cfg=config(min_quorum_specialist_count=d("5")),
    )
    assert strict.quorum_gap_count == d("2")
    assert strict.reason_codes == (
        "specialist_calibration_quorum_report_block",
        "specialist_calibration_quorum_below_minimum",
    )
    strict_payload = strict.public_payload
    assert (
        module.research_team_specialist_calibration_quorum_report_public_payload(
            json.loads(json.dumps(strict_payload)),
        )
        == strict_payload
    )


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    module = api()
    left = quorum_signal(
        specialist_key="sports_models",
        calibration_group="sports_calibration",
        status="pass",
        evidence_score=d("0.900000"),
    )
    right = quorum_signal(
        specialist_key="crypto_models",
        calibration_group="crypto_calibration",
        status="watch",
        evidence_score=d("0.700000"),
    )
    third = quorum_signal(
        specialist_key="macro_models",
        calibration_group="macro_calibration",
        status="pass",
        evidence_score=d("0.850000"),
    )

    report_a = build_report(right, left, third)
    report_b = build_report(third, left, right)
    payload = module.research_team_specialist_calibration_quorum_report_public_payload(
        report_a,
    )

    assert payload == module.research_team_specialist_calibration_quorum_report_public_payload(
        report_b,
    )
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert payload["specialist_count"] == "3"
    assert payload["agreement_ratio"] == "0.666667"
    assert payload["average_evidence_score"] == "0.816667"
    assert payload["rows"][0]["specialist_digest"].startswith("sha256:")
    assert payload["rows"][0]["group_digest"].startswith("sha256:")
    public_json = json.dumps(payload, sort_keys=True)
    assert "specialist_key" not in public_json
    assert "calibration_group" not in public_json
    assert "sports_models" not in public_json
    assert "sports_calibration" not in public_json
    assert "crypto_models" not in public_json
    assert payload["derived_validation_digest"] == report_a.derived_validation_digest
    assert_no_public_numeric_values(payload)
    assert_public_payload_has_no_forbidden_surface(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest does not match"):
        module.research_team_specialist_calibration_quorum_report_public_payload(
            tampered,
        )

    unsafe = dict(payload)
    unsafe["source_url"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_specialist_calibration_quorum_report_public_payload(
            unsafe,
        )

    invalid_status = dict(payload)
    invalid_status["status"] = "ready"
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        module.research_team_specialist_calibration_quorum_report_public_payload(
            resign_payload(invalid_status),
        )

    invalid_nested_status = {
        **payload,
        "rows": [{**payload["rows"][0], "status": "ready"}, *payload["rows"][1:]],
    }
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        module.research_team_specialist_calibration_quorum_report_public_payload(
            resign_payload(invalid_nested_status),
        )

    invalid_nested_flag = {
        **payload,
        "reason_code_counts": [
            {**payload["reason_code_counts"][0], "readonly": False},
            *payload["reason_code_counts"][1:],
        ],
    }
    with pytest.raises(ValueError, match="readonly must be True"):
        module.research_team_specialist_calibration_quorum_report_public_payload(
            resign_payload(invalid_nested_flag),
        )

    invalid_timestamp = dict(payload)
    invalid_timestamp["generated_at"] = GENERATED_AT.astimezone(
        timezone(timedelta(hours=-4)),
    ).isoformat()
    with pytest.raises(ValueError, match="generated_at must be a canonical UTC"):
        module.research_team_specialist_calibration_quorum_report_public_payload(
            resign_payload(invalid_timestamp),
        )


@pytest.mark.parametrize(
    ("mutation", "error_match"),
    (
        ("extra_status_prefix", "exactly one report status reason"),
        ("reordered_reasons", "canonical order"),
        ("quorum_gap", "quorum_gap_count must match reason_codes"),
        ("reordered_rows", "rows must be in canonical order"),
        ("duplicate_specialist", "specialist_digest values must be unique"),
    ),
)
def test_rejects_resigned_noncanonical_or_inconsistent_public_payloads(
    mutation: str,
    error_match: str,
) -> None:
    module = api()
    report = build_report(
        quorum_signal(
            specialist_key="sports_models",
            calibration_group="sports_calibration",
            status="pass",
            evidence_score=d("0.950000"),
        ),
        quorum_signal(
            specialist_key="macro_models",
            calibration_group="macro_calibration",
            status="pass",
            evidence_score=d("0.850000"),
        ),
        quorum_signal(
            specialist_key="crypto_models",
            calibration_group="crypto_calibration",
            status="watch",
            evidence_score=d("0.700000"),
        ),
        quorum_signal(
            specialist_key="policy_models",
            calibration_group="policy_calibration",
            status="block",
            evidence_score=d("0.500000"),
        ),
    )
    payload = json.loads(json.dumps(report.public_payload))

    if mutation == "extra_status_prefix":
        payload["reason_codes"].append("specialist_calibration_quorum_report_pass")
    elif mutation == "reordered_reasons":
        payload["reason_codes"] = [
            payload["reason_codes"][0],
            payload["reason_codes"][3],
            payload["reason_codes"][1],
            payload["reason_codes"][2],
        ]
    elif mutation == "quorum_gap":
        payload["quorum_gap_count"] = "9"
    elif mutation == "reordered_rows":
        payload["rows"].reverse()
    elif mutation == "duplicate_specialist":
        payload["rows"][1]["specialist_digest"] = payload["rows"][0][
            "specialist_digest"
        ]
    else:
        raise AssertionError(f"unsupported mutation {mutation}")

    with pytest.raises(ValueError, match=error_match):
        module.research_team_specialist_calibration_quorum_report_public_payload(
            resign_payload(payload),
        )


def test_tied_rows_use_public_digests_for_canonical_order() -> None:
    module = api()
    first = quorum_signal(
        specialist_key="sports_models",
        calibration_group="sports_calibration",
        evidence_score=d("0.900000"),
    )
    second = quorum_signal(
        specialist_key="macro_models",
        calibration_group="macro_calibration",
        evidence_score=d("0.900000"),
    )
    third = quorum_signal(
        specialist_key="crypto_models",
        calibration_group="crypto_calibration",
        evidence_score=d("0.900000"),
    )

    payload = build_report(first, second, third).public_payload
    assert payload == build_report(third, first, second).public_payload

    reordered = json.loads(json.dumps(payload))
    reordered["rows"][0], reordered["rows"][1] = (
        reordered["rows"][1],
        reordered["rows"][0],
    )
    with pytest.raises(ValueError, match="rows must be in canonical order"):
        module.research_team_specialist_calibration_quorum_report_public_payload(
            resign_payload(reordered),
        )


def test_rejects_resigned_row_reason_code_that_disagrees_with_status() -> None:
    module = api()
    payload = json.loads(
        json.dumps(
            build_report(
                quorum_signal(
                    specialist_key="sports_models",
                    calibration_group="sports_calibration",
                    status="pass",
                ),
                quorum_signal(
                    specialist_key="macro_models",
                    calibration_group="macro_calibration",
                    status="pass",
                ),
                quorum_signal(
                    specialist_key="crypto_models",
                    calibration_group="crypto_calibration",
                    status="watch",
                ),
            ).public_payload,
        ),
    )
    pass_row = next(row for row in payload["rows"] if row["status"] == "pass")
    pass_row["reason_codes"] = ["specialist_calibration_quorum_vote_watch"]
    payload["reason_code_counts"] = [
        {
            "reason_code": "specialist_calibration_quorum_vote_watch",
            "count": "2",
            "specialist_ratio": "0.666667",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "reason_code": "specialist_calibration_quorum_vote_pass",
            "count": "1",
            "specialist_ratio": "0.333333",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]

    with pytest.raises(ValueError, match="reason_codes must match status"):
        module.research_team_specialist_calibration_quorum_report_public_payload(
            resign_payload(payload),
        )


def test_normalizes_signed_zero_to_one_canonical_public_representation() -> None:
    report = build_report(
        quorum_signal(
            specialist_key="sports_models",
            evidence_score=d("-0.000000"),
        ),
        quorum_signal(
            specialist_key="macro_models",
            calibration_group="macro_calibration",
        ),
        quorum_signal(
            specialist_key="crypto_models",
            calibration_group="crypto_calibration",
        ),
    )
    zero_row = next(
        row for row in report.rows if row.specialist_key == "sports_models"
    )
    zero_payload_row = report.public_payload["rows"][0]

    assert str(zero_row.evidence_score) == "0.000000"
    assert zero_payload_row["evidence_score"] == "0.000000"
    assert (
        str(config(max_pass_block_ratio=d("-0.000000")).max_pass_block_ratio)
        == "0.000000"
    )


def test_reason_code_count_requires_positive_count() -> None:
    module = api()

    with pytest.raises(ValueError, match="count must be positive"):
        module.ResearchTeamSpecialistCalibrationQuorumReasonCodeCount(
            reason_code="specialist_calibration_quorum_vote_pass",
            count=d("0"),
            specialist_ratio=d("0.000000"),
        )


def test_validates_decimal_flags_statuses_and_frozen_dataclasses() -> None:
    module = api()
    cfg = config()
    item = quorum_signal()
    report = build_report(
        item,
        quorum_signal(
            specialist_key="macro_models",
            calibration_group="macro_calibration",
        ),
        quorum_signal(
            specialist_key="crypto_models",
            calibration_group="crypto_calibration",
        ),
    )

    for value in (cfg, item, report.rows[0], report.reason_code_counts[0], report):
        assert_decimal_public_fields(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="evidence_score must be a Decimal"):
        quorum_signal(evidence_score=0.9)
    with pytest.raises(ValueError, match="evidence_score must be a Decimal"):
        quorum_signal(evidence_score=_DecimalSubclass("0.9"))
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        quorum_signal(status="ready")
    with pytest.raises(ValueError, match="specialist_key contains unsafe public text"):
        quorum_signal(specialist_key="market_alpha")
    with pytest.raises(ValueError, match="specialist_key values must be unique"):
        build_report(item, replace(item))
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchTeamSpecialistCalibrationQuorumInput(
            specialist_key="sports_models",
            calibration_group="sports_calibration",
            status="pass",
            evidence_score=d("0.900000"),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="min_quorum_specialist_count must be integral"):
        config(min_quorum_specialist_count=d("2.5"))
    with pytest.raises(
        ValueError,
        match="min_pass_agreement_ratio must be at least min_watch_agreement_ratio",
    ):
        config(
            min_pass_agreement_ratio=d("0.500000"),
            min_watch_agreement_ratio=d("0.600000"),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.ResearchTeamSpecialistCalibrationQuorumReport(
            **{
                **report.__dict__,
                "derived_validation_digest": "0" * 64,
            },
        )
    with pytest.raises(ValueError, match="subclass is not allowed"):
        type(
            "BadConfig",
            (module.ResearchTeamSpecialistCalibrationQuorumConfig,),
            {},
        )


def test_module_static_contract_has_no_forbidden_execution_surfaces() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    imported_modules = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert imported_modules <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    assert "class Wallet" not in source
    assert "class Order" not in source
    assert "class Trade" not in source
    assert "def recommend" not in source
    assert "def size" not in source
    assert "paper_only: bool = True" in source
    assert "report_only: bool = True" in source
    assert "readonly: bool = True" in source

    forbidden_calls = {
        "__import__",
        "commit",
        "compile",
        "connect",
        "eval",
        "exec",
        "execute",
        "executemany",
        "open",
        "place_order",
        "recommend",
        "request",
        "rollback",
        "send",
        "size",
        "write",
        "write_bytes",
        "write_text",
    }
    called_names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            called_names.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            called_names.add(node.func.attr)
    assert called_names.isdisjoint(forbidden_calls)

    forbidden_definition_fragments = (
        "auth",
        "database",
        "execute",
        "execution",
        "file",
        "network",
        "order",
        "persist",
        "position",
        "recommend",
        "sizing",
        "trade",
        "trading",
        "wallet",
    )
    definition_names = {
        node.name.lower()
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert not {
        name
        for name in definition_names
        if any(fragment in name for fragment in forbidden_definition_fragments)
    }
