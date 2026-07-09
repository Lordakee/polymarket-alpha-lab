from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from hashlib import sha256

import pytest

from polymarket_alpha_lab.research_team_claim_source_memory_floor_report import (
    DEFAULT_RESEARCH_TEAM_CLAIM_SOURCE_MEMORY_FLOOR_REPORT_CONFIG_VERSION,
    ResearchTeamClaimSourceMemoryFloorConfig,
    ResearchTeamClaimSourceMemoryFloorObservation,
    ResearchTeamClaimSourceMemoryFloorReport,
    ResearchTeamClaimSourceMemoryFloorRow,
    build_research_team_claim_source_memory_floor_report,
    research_team_claim_source_memory_floor_public_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def _j(*parts: str) -> str:
    return "".join(parts)


def _config(**overrides: object) -> ResearchTeamClaimSourceMemoryFloorConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_TEAM_CLAIM_SOURCE_MEMORY_FLOOR_REPORT_CONFIG_VERSION
        ),
        "pass_memory_floor": d("0.700000"),
        "watch_memory_floor": d("0.400000"),
        "stale_after_seconds": d("86400.000000"),
        "min_distinct_digest_count": d("2"),
        "fresh_weight": d("0.600000"),
        "distinct_weight": d("0.400000"),
    }
    values.update(overrides)
    return ResearchTeamClaimSourceMemoryFloorConfig(**values)


def _observation(
    locator: str,
    excerpt: str,
    *,
    claim_id: str = "claim.alpha",
    team_id: str = "team.research",
    evidence_id: str = "evidence.alpha",
    observed_at: datetime | None = None,
    memory_strength: Decimal = d("0.750000"),
) -> ResearchTeamClaimSourceMemoryFloorObservation:
    return ResearchTeamClaimSourceMemoryFloorObservation(
        claim_id=claim_id,
        team_id=team_id,
        evidence_id=evidence_id,
        evidence_locator=locator,
        evidence_excerpt=excerpt,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        memory_strength=memory_strength,
    )


def test_claim_source_memory_floor_reduces_rows_and_redacts_raw_inputs() -> None:
    raw_locator = (
        "https://alpha.example/markets/abc?"
        + _j("to", "ken")
        + "=secret-value&"
        + _j("d", "sn")
        + "=postgres://hidden"
    )
    raw_excerpt = (
        "candidate alpha raw market source text in table row with secret token"
    )

    report = build_research_team_claim_source_memory_floor_report(
        (
            _observation(
                raw_locator,
                raw_excerpt,
                claim_id="claim.pass",
                evidence_id="evidence.2",
                memory_strength=d("0.900000"),
            ),
            _observation(
                "archive://second-private-locator",
                "second private excerpt",
                claim_id="claim.pass",
                evidence_id="evidence.1",
                memory_strength=d("0.800000"),
            ),
            _observation(
                "archive://stale-private-locator",
                "stale private excerpt",
                claim_id="claim.watch",
                evidence_id="evidence.3",
                observed_at=GENERATED_AT - timedelta(days=2),
                memory_strength=d("0.600000"),
            ),
            _observation(
                "archive://weak-private-locator",
                "weak private excerpt",
                claim_id="claim.block",
                evidence_id="evidence.4",
                memory_strength=d("0.100000"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(report, ResearchTeamClaimSourceMemoryFloorReport)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.claim_count == d("3")
    assert report.observation_count == d("4")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_memory_floor_score == d("0.576667")
    assert report.reason_codes == (
        "memory_floor_block",
        "memory_floor_pass",
        "memory_floor_stale",
        "memory_floor_thin_digests",
        "memory_floor_watch",
    )
    assert tuple(row.claim_id for row in report.rows) == (
        "claim.block",
        "claim.pass",
        "claim.watch",
    )

    rows = {row.claim_id: row for row in report.rows}
    assert rows["claim.pass"] == ResearchTeamClaimSourceMemoryFloorRow(
        claim_id="claim.pass",
        team_id="team.research",
        status="pass",
        observation_count=d("2"),
        fresh_observation_count=d("2"),
        stale_observation_count=d("0"),
        distinct_digest_count=d("2"),
        latest_age_seconds=d("1800.000000"),
        average_memory_strength=d("0.850000"),
        freshness_score=d("1.000000"),
        distinct_digest_score=d("1.000000"),
        memory_floor_score=d("0.910000"),
        evidence_digests=(
            "sha256:8e7a15d501376493",
            "sha256:5c8f68bb5cb5e262",
        ),
        reason_codes=("memory_floor_pass",),
    )
    assert rows["claim.watch"].status == "watch"
    assert rows["claim.watch"].reason_codes == (
        "memory_floor_stale",
        "memory_floor_thin_digests",
        "memory_floor_watch",
    )
    assert rows["claim.block"].status == "block"
    assert rows["claim.block"].reason_codes == (
        "memory_floor_block",
        "memory_floor_thin_digests",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    public = research_team_claim_source_memory_floor_public_payload(report)
    public_blob = repr(public).lower()
    for raw_fragment in (
        raw_locator,
        raw_excerpt,
        "candidate",
        "alpha.example",
        "markets/abc",
        "secret-value",
        "postgres://hidden",
        "raw market",
        "source text",
        _j("d", "sn"),
        _j("ta", "ble"),
        _j("to", "ken"),
    ):
        assert raw_fragment.lower() not in public_blob


def test_claim_source_memory_floor_public_payload_is_deterministic_and_digest_checked() -> None:
    observations = (
        _observation(
            "archive://two",
            "two excerpt",
            claim_id="claim.two",
            evidence_id="evidence.two",
            observed_at=GENERATED_AT - timedelta(seconds=1, microseconds=250000),
            memory_strength=d("0.650000"),
        ),
        _observation(
            "archive://one",
            "one excerpt",
            claim_id="claim.one",
            evidence_id="evidence.one",
            memory_strength=d("0.950000"),
        ),
    )

    first = build_research_team_claim_source_memory_floor_report(
        observations,
        config=_config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=2))),
    )
    second = build_research_team_claim_source_memory_floor_report(
        tuple(reversed(observations)),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    first_public = research_team_claim_source_memory_floor_public_payload(first)
    second_public = research_team_claim_source_memory_floor_public_payload(second)

    assert first_public == second_public
    assert first_public["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_public["claim_count"] == "2.000000"
    assert first_public["status"] == "watch"
    assert [row["claim_id"] for row in first_public["rows"]] == [
        "claim.one",
        "claim.two",
    ]
    assert first_public["rows"][1]["latest_age_seconds"] == "1.250000"
    assert first_public["paper_only"] is True
    assert first_public["report_only"] is True
    assert first_public["readonly"] is True

    public_without_digest = dict(first_public)
    digest = public_without_digest.pop("payload_sha256")
    expected_digest = sha256(
        json.dumps(
            public_without_digest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert digest == expected_digest

    tampered = first
    object.__setattr__(tampered, "payload_sha256", "0" * 64)
    with pytest.raises(ValueError, match="payload_sha256"):
        research_team_claim_source_memory_floor_public_payload(tampered)

    def walk(value: object) -> tuple[object, ...]:
        if isinstance(value, dict):
            return tuple(item for nested in value.values() for item in walk(nested))
        if isinstance(value, list):
            return tuple(item for nested in value for item in walk(nested))
        return (value,)

    assert not any(isinstance(value, Decimal) for value in walk(first_public))
    assert not any(type(value) is int for value in walk(first_public))
    assert not any(type(value) is float for value in walk(first_public))


def test_claim_source_memory_floor_validates_decimal_types_statuses_flags_and_times() -> None:
    with pytest.raises(ValueError, match="pass_memory_floor"):
        ResearchTeamClaimSourceMemoryFloorConfig(pass_memory_floor=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_memory_floor"):
        ResearchTeamClaimSourceMemoryFloorConfig(
            watch_memory_floor=_DecimalSubclass("0.400000"),
        )
    with pytest.raises(ValueError, match="min_distinct_digest_count"):
        ResearchTeamClaimSourceMemoryFloorConfig(min_distinct_digest_count=d("1.5"))
    with pytest.raises(ValueError, match="sum"):
        ResearchTeamClaimSourceMemoryFloorConfig(
            fresh_weight=d("0.500000"),
            distinct_weight=d("0.400000"),
        )
    with pytest.raises(ValueError, match="config_version"):
        ResearchTeamClaimSourceMemoryFloorConfig(config_version="wrong-version")
    with pytest.raises(ValueError, match="claim_id"):
        _observation("locator", "excerpt", claim_id=" candidate.raw ")
    for unsafe_claim_id in (
        "market_id.raw",
        "market-slug-raw",
        "question.raw",
        "source_url.raw",
        "wallet.raw",
        "order.raw",
        "trade.raw",
        "recommend.raw",
    ):
        with pytest.raises(ValueError, match="claim_id"):
            _observation("locator", "excerpt", claim_id=unsafe_claim_id)
    with pytest.raises(ValueError, match="evidence_locator"):
        _observation("", "excerpt")
    with pytest.raises(ValueError, match="team_id"):
        _observation("locator", "excerpt", team_id="team\nresearch")
    with pytest.raises(ValueError, match="evidence_excerpt"):
        _observation("locator", "")
    with pytest.raises(ValueError, match="observed_at"):
        _observation("locator", "excerpt", observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        _observation(
            "locator",
            "excerpt",
            observed_at=datetime(2026, 7, 9, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        build_research_team_claim_source_memory_floor_report(
            (
                _observation(
                    "future",
                    "future excerpt",
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="memory_strength"):
        _observation("locator", "excerpt", memory_strength=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        replace(_observation("locator", "excerpt"), paper_only=False)
    with pytest.raises(ValueError, match="observations"):
        build_research_team_claim_source_memory_floor_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_research_team_claim_source_memory_floor_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_team_claim_source_memory_floor_report(
            (),
            config=_config(),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="status"):
        ResearchTeamClaimSourceMemoryFloorRow(
            claim_id="claim.manual",
            team_id="team.research",
            status="blocked",
            observation_count=d("1"),
            fresh_observation_count=d("1"),
            stale_observation_count=d("0"),
            distinct_digest_count=d("1"),
            latest_age_seconds=d("1.000000"),
            average_memory_strength=d("0.500000"),
            freshness_score=d("1.000000"),
            distinct_digest_score=d("0.500000"),
            memory_floor_score=d("0.500000"),
            evidence_digests=("sha256:abc123abc123abcd",),
            reason_codes=("memory_floor_watch",),
        )


def test_claim_source_memory_floor_empty_report_blocks_without_inputs() -> None:
    report = build_research_team_claim_source_memory_floor_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.status == "block"
    assert report.claim_count == d("0")
    assert report.observation_count == d("0")
    assert report.average_memory_floor_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("memory_floor_no_inputs",)
    assert report.reason_code_counts[0].reason_code == "memory_floor_no_inputs"
    assert report.reason_code_counts[0].count == d("1.000000")


def test_claim_source_memory_floor_public_dataclasses_are_frozen_and_exact() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_team_claim_source_memory_floor_report",
    )
    report = build_research_team_claim_source_memory_floor_report(
        (_observation("locator", "excerpt"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    values = (
        _config(),
        _observation("input", "input excerpt"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )
    for value in values:
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False

    for public_type in (
        ResearchTeamClaimSourceMemoryFloorConfig,
        ResearchTeamClaimSourceMemoryFloorObservation,
        ResearchTeamClaimSourceMemoryFloorRow,
        module.ResearchTeamClaimSourceMemoryFloorReasonCodeCount,
        ResearchTeamClaimSourceMemoryFloorReport,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})


def test_claim_source_memory_floor_public_payload_revalidates_tampered_report() -> None:
    report = build_research_team_claim_source_memory_floor_report(
        (_observation("locator", "excerpt"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    object.__setattr__(report.rows[0], "status", "blocked")
    with pytest.raises(ValueError, match="status"):
        research_team_claim_source_memory_floor_public_payload(report)

    report = build_research_team_claim_source_memory_floor_report(
        (_observation("locator", "excerpt"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    object.__setattr__(report.rows[0], "memory_floor_score", d("0.1234567"))
    with pytest.raises(ValueError, match="six decimal"):
        research_team_claim_source_memory_floor_public_payload(report)

    with pytest.raises(ValueError, match="ResearchTeamClaimSourceMemoryFloorReport"):
        research_team_claim_source_memory_floor_public_payload(asdict(report))  # type: ignore[arg-type]

    report = build_research_team_claim_source_memory_floor_report(
        (_observation("locator", "excerpt"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    object.__setattr__(report.rows[0], "claim_id", "market_id.raw")
    with pytest.raises(ValueError, match="claim_id"):
        research_team_claim_source_memory_floor_public_payload(report)


def test_claim_source_memory_floor_scope_excludes_io_and_forbidden_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_team_claim_source_memory_floor_report",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    lowered_source = source.lower()
    for token in (
        _j("d", "b"),
        _j("net", "work"),
        _j("wal", "let"),
        _j("au", "th"),
        _j("or", "der"),
        _j("li", "ve"),
        _j("tra", "ding"),
        _j("tra", "de"),
        _j("rou", "te"),
        _j("siz", "ing"),
        _j("rec", "ommend"),
        _j("rec", "ommend", "ation"),
    ):
        assert token not in lowered_source

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        _j("d", "b"),
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
