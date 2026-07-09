from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_specialist_cross_domain_memory_decay_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_cross_domain_memory_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def redacted_memory_ref(value: str) -> str:
    return f"memory_ref_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def observation(**overrides: object):
    module = api()
    values = {
        "memory_ref": (
            "candidate-raw-alpha-market-slug-question-url-token-wallet-order-trade"
        ),
        "original_domain_label": "domain.crypto",
        "target_domain_label": "domain.macro",
        "specialist_label": "cross_domain_memory",
        "observed_at": GENERATED_AT - timedelta(days=12),
        "memory_age_days": d("12.000000"),
        "reuse_count": d("20.000000"),
        "conflict_count": d("1.000000"),
        "validation_count": d("10.000000"),
        "validation_pass_count": d("9.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistCrossDomainMemoryDecayObservation(**values)


def config(**overrides: object):
    module = api()
    values = {
        "max_pass_memory_age_days": d("30.000000"),
        "max_watch_memory_age_days": d("90.000000"),
        "max_pass_conflict_ratio": d("0.100000"),
        "max_watch_conflict_ratio": d("0.250000"),
        "min_pass_validation_ratio": d("0.800000"),
        "min_watch_validation_ratio": d("0.500000"),
        "min_pass_retention_score": d("0.700000"),
        "min_watch_retention_score": d("0.400000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistCrossDomainMemoryDecayConfig(**values)


def report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_specialist_cross_domain_memory_decay_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def _walk(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    else:
        yield value


def test_report_scores_cross_domain_memory_decay_without_raw_public_refs() -> None:
    pass_ref = "candidate-pass-market-slug-question-url-token"
    watch_ref = "candidate-watch-market-slug-question-url-token"
    block_ref = "candidate-block-market-slug-question-url-token"

    decay_report = report(
        observation(memory_ref=pass_ref),
        observation(
            memory_ref=watch_ref,
            original_domain_label="domain.policy",
            target_domain_label="domain.macro",
            specialist_label="policy_memory",
            observed_at=GENERATED_AT - timedelta(days=45),
            memory_age_days=d("45.000000"),
            reuse_count=d("20.000000"),
            conflict_count=d("4.000000"),
            validation_count=d("10.000000"),
            validation_pass_count=d("6.000000"),
        ),
        observation(
            memory_ref=block_ref,
            original_domain_label="domain.sports",
            target_domain_label="domain.injuries",
            specialist_label="sports_memory",
            observed_at=GENERATED_AT - timedelta(days=120),
            memory_age_days=d("120.000000"),
            reuse_count=d("20.000000"),
            conflict_count=d("10.000000"),
            validation_count=d("8.000000"),
            validation_pass_count=d("2.000000"),
        ),
    )

    assert decay_report.status == "block"
    assert decay_report.observation_count == d("3.000000")
    assert decay_report.pass_count == d("1.000000")
    assert decay_report.watch_count == d("1.000000")
    assert decay_report.block_count == d("1.000000")
    assert decay_report.reuse_count == d("60.000000")
    assert decay_report.conflict_count == d("15.000000")
    assert decay_report.validation_count == d("28.000000")
    assert decay_report.validation_pass_count == d("17.000000")
    assert decay_report.cross_domain_pair_count == d("3.000000")
    assert decay_report.mean_memory_age_days == d("59.000000")
    assert decay_report.mean_retention_score == d("0.596296")
    assert decay_report.mean_decay_score == d("0.403704")
    assert decay_report.reason_codes == (
        "cross_domain_memory_decay_block_present",
        "cross_domain_memory_decay_watch_present",
        "memory_age_decay_present",
        "memory_conflict_decay_present",
        "memory_validation_decay_present",
    )
    assert decay_report.paper_only is True
    assert decay_report.report_only is True
    assert decay_report.readonly is True

    first, second, third = decay_report.rows
    assert first.redacted_memory_ref == redacted_memory_ref(block_ref)
    assert first.status == "block"
    assert first.memory_age_ratio == d("1.000000")
    assert first.conflict_ratio == d("0.500000")
    assert first.validation_ratio == d("0.250000")
    assert first.retention_score == d("0.250000")
    assert first.decay_score == d("0.750000")
    assert first.reason_codes == (
        "memory_age_block",
        "memory_conflict_block",
        "memory_validation_block",
        "memory_retention_block",
    )
    assert second.redacted_memory_ref == redacted_memory_ref(watch_ref)
    assert second.status == "watch"
    assert second.retention_score == d("0.633333")
    assert second.reason_codes == (
        "memory_age_watch",
        "memory_conflict_watch",
        "memory_validation_watch",
        "memory_retention_watch",
    )
    assert third.redacted_memory_ref == redacted_memory_ref(pass_ref)
    assert third.status == "pass"
    assert third.retention_score == d("0.905556")
    assert third.reason_codes == ("cross_domain_memory_retained",)

    assert tuple(summary.target_domain_label for summary in decay_report.domain_summaries) == (
        "domain.injuries",
        "domain.macro",
    )
    assert decay_report.domain_summaries[0].worst_status == "block"
    assert decay_report.domain_summaries[0].mean_decay_score == d("0.750000")
    assert decay_report.domain_summaries[1].worst_status == "watch"
    assert decay_report.domain_summaries[1].memory_count == d("2.000000")
    assert decay_report.reason_code_counts[0].reason_code == "memory_age_block"
    assert decay_report.reason_code_counts[0].count == d("1.000000")

    payload = api().research_team_specialist_cross_domain_memory_decay_report_payload(
        decay_report,
    )
    public_text = json.dumps(payload, sort_keys=True).lower()
    for raw_ref in (pass_ref, watch_ref, block_ref):
        assert raw_ref not in public_text
    for forbidden in ("market-slug", "question", "url", "token", "wallet", "order", "trade"):
        assert forbidden not in public_text


def test_empty_report_is_report_only_readonly_and_deterministic() -> None:
    decay_report = report()

    assert decay_report.status == "block"
    assert decay_report.observation_count == d("0.000000")
    assert decay_report.pass_count == d("0.000000")
    assert decay_report.watch_count == d("0.000000")
    assert decay_report.block_count == d("0.000000")
    assert decay_report.mean_memory_age_days == d("0.000000")
    assert decay_report.mean_retention_score == d("0.000000")
    assert decay_report.mean_decay_score == d("1.000000")
    assert decay_report.rows == ()
    assert decay_report.domain_summaries == ()
    assert decay_report.reason_codes == ("cross_domain_memory_decay_no_observations",)
    assert decay_report.reason_code_counts[0].reason_code == (
        "cross_domain_memory_decay_no_observations"
    )
    assert decay_report.reason_code_counts[0].row_ratio == d("0.000000")
    assert decay_report.paper_only is True
    assert decay_report.report_only is True
    assert decay_report.readonly is True


def test_payload_serializes_canonical_json_and_validates_sha256_digest() -> None:
    module = api()
    decay_report = report(
        observation(),
        generated_at=datetime(2026, 7, 9, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.research_team_specialist_cross_domain_memory_decay_report_payload(
        decay_report,
    )
    canonical_json = module.research_team_specialist_cross_domain_memory_decay_report_json(
        decay_report,
    )
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "payload_sha256"
    }
    expected_digest = sha256(
        json.dumps(
            payload_without_digest,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()

    assert decay_report.generated_at == GENERATED_AT
    assert json.loads(canonical_json) == payload
    assert canonical_json == (
        module.research_team_specialist_cross_domain_memory_decay_report_json(decay_report)
    )
    assert payload["payload_sha256"] == expected_digest
    assert decay_report.payload_sha256 == expected_digest
    assert payload["rows"][0]["redacted_memory_ref"] == redacted_memory_ref(
        "candidate-raw-alpha-market-slug-question-url-token-wallet-order-trade",
    )
    assert "Decimal(" not in repr(payload)
    assert "datetime" not in repr(payload).lower()
    assert all(type(value) is not float for value in _walk(payload))

    tampered_payload = dict(payload)
    tampered_payload["status"] = "watch"
    with pytest.raises(ValueError, match="payload_sha256 does not match"):
        module.validate_research_team_specialist_cross_domain_memory_decay_report_payload(
            tampered_payload,
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.research_team_specialist_cross_domain_memory_decay_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "payload_sha256": "0" * 64,
                "mean_decay_score": 0.1,
            },
        )


def test_validation_rejects_float_subclasses_bad_time_status_digest_and_flags() -> None:
    module = api()
    decay_report = report(observation())

    with pytest.raises(FrozenInstanceError):
        decay_report.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="memory_age_days must be a Decimal"):
        observation(memory_age_days=0.1)

    with pytest.raises(ValueError, match="memory_age_days"):
        observation(memory_age_days=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="memory_age_days must be finite"):
        observation(memory_age_days=Decimal("NaN"))

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(observation(), generated_at="bad")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 9, 12, 0))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            observation(),
            generated_at=datetime(2026, 7, 9, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.ResearchTeamSpecialistCrossDomainMemoryDecayReport(
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
            config_version=module.DEFAULT_RESEARCH_TEAM_SPECIALIST_CROSS_DOMAIN_MEMORY_DECAY_REPORT_CONFIG_VERSION,
            observation_count=d("0.000000"),
            pass_count=d("0.000000"),
            watch_count=d("0.000000"),
            block_count=d("0.000000"),
            reuse_count=d("0.000000"),
            conflict_count=d("0.000000"),
            validation_count=d("0.000000"),
            validation_pass_count=d("0.000000"),
            cross_domain_pair_count=d("0.000000"),
            mean_memory_age_days=d("0.000000"),
            mean_retention_score=d("0.000000"),
            mean_decay_score=d("1.000000"),
            status="block",
            reason_codes=("cross_domain_memory_decay_no_observations",),
            reason_code_counts=(),
            domain_summaries=(),
            rows=(),
        )

    with pytest.raises(ValueError, match="max_pass_memory_age_days must not exceed"):
        config(max_pass_memory_age_days=d("91.000000"))

    with pytest.raises(ValueError, match="config must be report_only"):
        config(report_only=False)

    with pytest.raises(ValueError, match="observation must be readonly"):
        observation(readonly=False)

    with pytest.raises(ValueError, match="status"):
        replace(decay_report, status="review")

    with pytest.raises(ValueError, match="observation_count"):
        replace(decay_report, observation_count=d("2.000000"))

    with pytest.raises(ValueError, match="payload_sha256 does not match"):
        replace(decay_report, payload_sha256="0" * 64)


def test_public_payload_rejects_unsafe_surfaces_and_module_has_no_live_connectors() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_team_specialist_cross_domain_memory_decay_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "market_slug": "raw-market",
            },
        )

    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_team_specialist_cross_domain_memory_decay_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"redacted_memory_ref": "token=secret"}],
                "payload_sha256": "0" * 64,
            },
        )

    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_import_roots = {
        "boto3",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_call_names = {
        "buy",
        "connect",
        "create_order",
        "execute",
        "get",
        "open",
        "place_order",
        "post",
        "recommend",
        "request",
        "send",
        "size_position",
        "trade",
    }
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert call_names.isdisjoint(forbidden_call_names)
