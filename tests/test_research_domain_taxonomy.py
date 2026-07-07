from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_domain_taxonomy import (
    DEFAULT_RESEARCH_DOMAIN_TAXONOMY_CONFIG_VERSION,
    RESEARCH_DOMAIN_IDS,
    ResearchDomainClassificationInput,
    ResearchDomainClassificationReport,
    ResearchDomainClassificationRow,
    ResearchDomainTaxonomyConfig,
    build_research_domain_classification_report,
    classify_research_domain,
    research_domain_classification_payload,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def _input(
    *,
    public_event_label: str,
    public_category_hint: str = "general",
    public_tags: tuple[str, ...] = (),
) -> ResearchDomainClassificationInput:
    return ResearchDomainClassificationInput(
        public_event_label=public_event_label,
        public_category_hint=public_category_hint,
        public_tags=public_tags,
    )


def test_defaults_are_frozen_readonly_and_domain_ids_are_stable() -> None:
    config = ResearchDomainTaxonomyConfig()

    assert config.config_version == DEFAULT_RESEARCH_DOMAIN_TAXONOMY_CONFIG_VERSION
    assert RESEARCH_DOMAIN_IDS == (
        "politics",
        "macro",
        "crypto",
        "equity_index",
        "gold",
        "soccer",
        "basketball",
        "general",
    )
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("candidate", "expected_domain", "expected_status", "expected_reason"),
    (
        (
            _input(
                public_event_label="US presidential election winner",
                public_category_hint="politics.elections",
                public_tags=("president",),
            ),
            "politics",
            "pass",
            "category_hint_politics",
        ),
        (
            _input(
                public_event_label="Federal Reserve rate cut before September",
                public_category_hint="economics.macro",
                public_tags=("fed",),
            ),
            "macro",
            "pass",
            "category_hint_macro",
        ),
        (
            _input(
                public_event_label="Bitcoin above 150k before year end",
                public_category_hint="finance.crypto",
                public_tags=("btc",),
            ),
            "crypto",
            "pass",
            "category_hint_crypto",
        ),
        (
            _input(
                public_event_label="S&P 500 close above 7000",
                public_category_hint="finance.equity.indices",
                public_tags=("spx",),
            ),
            "equity_index",
            "pass",
            "category_hint_equity_index",
        ),
        (
            _input(
                public_event_label="Gold trades above 3000 this year",
                public_category_hint="commodities.gold",
                public_tags=("xau",),
            ),
            "gold",
            "pass",
            "category_hint_gold",
        ),
        (
            _input(
                public_event_label="Champions League final winner",
                public_category_hint="sports.soccer",
                public_tags=("uefa",),
            ),
            "soccer",
            "pass",
            "category_hint_soccer",
        ),
        (
            _input(
                public_event_label="NBA Finals winner",
                public_category_hint="sports.basketball",
                public_tags=("nba",),
            ),
            "basketball",
            "pass",
            "category_hint_basketball",
        ),
    ),
)
def test_routes_main_research_domains(
    candidate: ResearchDomainClassificationInput,
    expected_domain: str,
    expected_status: str,
    expected_reason: str,
) -> None:
    row = classify_research_domain(candidate, config=ResearchDomainTaxonomyConfig())

    assert row.research_domain_id == expected_domain
    assert row.public_status == expected_status
    assert expected_reason in row.reason_codes
    assert row.classification_confidence.as_tuple().exponent == -6
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


@pytest.mark.parametrize(
    ("candidate", "expected_domain", "expected_subdomain", "expected_reason"),
    (
        (
            _input(
                public_event_label="US Senate control after 2026 midterms",
                public_category_hint="politics.us.congress",
            ),
            "politics",
            "us_congress",
            "subdomain_us_congress",
        ),
        (
            _input(
                public_event_label="Fed funds rate target above 5 percent",
                public_category_hint="economics.central_banks",
            ),
            "macro",
            "rates",
            "subdomain_rates",
        ),
        (
            _input(
                public_event_label="Bitcoin ETF approval window",
                public_category_hint="finance.crypto.etf",
            ),
            "crypto",
            "btc_etf",
            "subdomain_btc_etf",
        ),
        (
            _input(
                public_event_label="Nasdaq closes above record high",
                public_category_hint="finance.equity.indices",
            ),
            "equity_index",
            "nasdaq",
            "subdomain_nasdaq",
        ),
        (
            _input(
                public_event_label="Real Madrid wins UEFA Champions League",
                public_category_hint="sports.soccer",
            ),
            "soccer",
            "club_competition",
            "subdomain_club_competition",
        ),
        (
            _input(
                public_event_label="WNBA champion this season",
                public_category_hint="sports.basketball",
            ),
            "basketball",
            "wnba",
            "subdomain_wnba",
        ),
    ),
)
def test_routes_research_subdomains(
    candidate: ResearchDomainClassificationInput,
    expected_domain: str,
    expected_subdomain: str,
    expected_reason: str,
) -> None:
    row = classify_research_domain(candidate, config=ResearchDomainTaxonomyConfig())

    assert row.research_domain_id == expected_domain
    assert row.research_subdomain_id == expected_subdomain
    assert expected_reason in row.reason_codes


@pytest.mark.parametrize(
    "candidate",
    (
        _input(
            public_event_label="Celebrity technology announcement before September",
            public_category_hint="culture",
            public_tags=("ai",),
        ),
        _input(
            public_event_label="Football final winner",
            public_category_hint="sports.football",
        ),
    ),
)
def test_unknown_or_ambiguous_candidates_are_watch(candidate: ResearchDomainClassificationInput) -> None:
    row = classify_research_domain(candidate, config=ResearchDomainTaxonomyConfig())

    assert row.research_domain_id == "general"
    assert row.research_subdomain_id == "needs_triage"
    assert row.public_status == "watch"
    assert "needs_human_triage" in row.reason_codes


def test_type_rejection_is_strict_and_decimal_only() -> None:
    with pytest.raises(ValueError, match="config_version must contain canonical strings"):
        ResearchDomainTaxonomyConfig(config_version=123)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="classification_confidence must be a Decimal"):
        ResearchDomainClassificationRow(
            public_sequence=Decimal("1"),
            public_event_label="General event label",
            research_domain_id="general",
            research_subdomain_id="needs_triage",
            public_status="watch",
            classification_confidence=0.5,  # type: ignore[arg-type]
            reason_codes=("needs_human_triage",),
            matched_public_terms=(),
        )

    with pytest.raises(ValueError, match="public_sequence must be a Decimal"):
        ResearchDomainClassificationRow(
            public_sequence=1,  # type: ignore[arg-type]
            public_event_label="General event label",
            research_domain_id="general",
            research_subdomain_id="needs_triage",
            public_status="watch",
            classification_confidence=Decimal("0.500000"),
            reason_codes=("needs_human_triage",),
            matched_public_terms=(),
        )

    with pytest.raises(ValueError, match="public_status must be pass, watch, or block"):
        ResearchDomainClassificationRow(
            public_sequence=Decimal("1"),
            public_event_label="General event label",
            research_domain_id="general",
            research_subdomain_id="needs_triage",
            public_status="ready",
            classification_confidence=Decimal("0.500000"),
            reason_codes=("needs_human_triage",),
            matched_public_terms=(),
        )


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "condition id candidate-123",
        "market slug bitcoin-above-100k",
        "question: will this happen?",
        "source ref https://example.com/story",
        "raw text from resolver",
        "postgres dsn table name",
        "auth token wallet order trade",
        "position buy recommendation",
    ),
)
def test_public_leak_rejection_blocks_unsafe_values(unsafe_value: str) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        ResearchDomainClassificationInput(
            public_event_label=unsafe_value,
            public_category_hint="general",
        )

    with pytest.raises(ValueError, match="unsafe public"):
        research_domain_classification_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "public_status": "watch",
                "public_note": unsafe_value,
            },
        )


def test_hard_flags_are_required_on_inputs_rows_reports_and_payloads() -> None:
    with pytest.raises(ValueError, match="paper_only must be True"):
        ResearchDomainTaxonomyConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        ResearchDomainClassificationInput(
            public_event_label="General event label",
            public_category_hint="general",
            report_only=False,
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        ResearchDomainClassificationReport(
            generated_at=GENERATED_AT,
            config_version=DEFAULT_RESEARCH_DOMAIN_TAXONOMY_CONFIG_VERSION,
            classification_count=Decimal("0"),
            pass_count=Decimal("0"),
            watch_count=Decimal("0"),
            block_count=Decimal("0"),
            rows=(),
            readonly=False,
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        research_domain_classification_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": False,
            },
        )


def test_report_and_payload_output_are_deterministic_and_public_safe() -> None:
    candidates = (
        _input(
            public_event_label="Bitcoin above 150k before year end",
            public_category_hint="finance.crypto",
            public_tags=("btc",),
        ),
        _input(
            public_event_label="Celebrity technology announcement before September",
            public_category_hint="culture",
            public_tags=("ai",),
        ),
    )
    config = ResearchDomainTaxonomyConfig(config_version="research-domain-taxonomy-v1")

    first = build_research_domain_classification_report(
        candidates,
        config=config,
        generated_at=GENERATED_AT,
    )
    second = build_research_domain_classification_report(
        list(candidates),
        config=config,
        generated_at=GENERATED_AT,
    )

    assert first == second
    assert first.classification_count == Decimal("2")
    assert first.pass_count == Decimal("1")
    assert first.watch_count == Decimal("1")
    assert first.block_count == Decimal("0")
    assert tuple(row.public_sequence for row in first.rows) == (Decimal("1"), Decimal("2"))
    assert tuple(row.research_domain_id for row in first.rows) == ("crypto", "general")

    payload = research_domain_classification_payload(first)

    assert payload == research_domain_classification_payload(second)
    assert payload["classification_count"] == "2"
    assert payload["rows"][0]["classification_confidence"] == "0.900000"
    assert "market_slug" not in str(payload)
    assert "question" not in str(payload)


def test_public_dataclasses_expose_no_forbidden_surface_fields() -> None:
    unsafe_fragments = (
        "raw",
        "candidate",
        "condition",
        "market",
        "slug",
        "question",
        "source",
        "ref",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    )

    for cls in (
        ResearchDomainTaxonomyConfig,
        ResearchDomainClassificationInput,
        ResearchDomainClassificationRow,
        ResearchDomainClassificationReport,
    ):
        for field in fields(cls):
            assert not any(fragment in field.name.lower() for fragment in unsafe_fragments)
