from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_cohort import (
    CohortCandidate,
    candidate_from_metadata,
    select_cohort,
)


def metadata(**overrides) -> dict:
    value = {
        "condition_id": "0x1",
        "slug": "will-btc-hit-100k",
        "question": "Will BTC hit 100k?",
        "clob_token_ids": ["1", "2"],
        "outcomes": ["Yes", "No"],
        "active": True,
        "closed": False,
        "liquidity": Decimal("100"),
    }
    value.update(overrides)
    return value


def test_candidate_extraction_and_validation() -> None:
    candidate = candidate_from_metadata(metadata(), "crypto_btc")
    assert candidate.is_binary and candidate.is_active and not candidate.is_closed
    assert candidate.keyword_match and candidate.liquidity == Decimal("100")
    with pytest.raises(ValueError):
        candidate_from_metadata(metadata(), "not_a_team")
    with pytest.raises(ValueError):
        CohortCandidate("  ", "s", "q", True, True, False, True, None)


def test_filter_matrix() -> None:
    eligible = candidate_from_metadata(metadata(), "crypto_btc")
    non_binary = candidate_from_metadata(metadata(clob_token_ids=["1"]), "crypto_btc")
    wrong_outcome_count = candidate_from_metadata(metadata(outcomes=["Yes"]), "crypto_btc")
    inactive = candidate_from_metadata(metadata(active=False), "crypto_btc")
    closed = candidate_from_metadata(metadata(closed=True), "crypto_btc")
    off_keyword = candidate_from_metadata(
        metadata(slug="us-election", question="Who wins?"), "crypto_btc"
    )
    no_liquidity = candidate_from_metadata(
        metadata(condition_id="0x2", liquidity=None), "crypto_btc"
    )
    selected = select_cohort(
        [non_binary, wrong_outcome_count, inactive, closed, off_keyword, no_liquidity, eligible],
        limit=5,
    )
    assert tuple(c.condition_id for c in selected) == ("0x1", "0x2")


def test_ranking_and_limit() -> None:
    low = candidate_from_metadata(metadata(condition_id="0xb", liquidity=Decimal("10")), "crypto_btc")
    high = candidate_from_metadata(metadata(condition_id="0xc", liquidity=Decimal("900")), "crypto_btc")
    tie = candidate_from_metadata(metadata(condition_id="0xa", liquidity=Decimal("10")), "crypto_btc")
    assert tuple(c.condition_id for c in select_cohort([low, high, tie], limit=3)) == (
        "0xc",
        "0xa",
        "0xb",
    )
    assert len(select_cohort([low, high, tie], limit=2)) == 2
    with pytest.raises(ValueError):
        select_cohort([], limit=0)


def test_eth_keyword_pattern() -> None:
    eth = candidate_from_metadata(
        metadata(slug="eth-flip", question="ETH flip BTC?"), "crypto_eth"
    )
    assert eth.keyword_match
    btc_only = candidate_from_metadata(
        metadata(slug="eth-flip", question="ETH flip BTC?"), "crypto_btc"
    )
    assert btc_only.keyword_match  # BTC appears too; team scoping is per-run
    neither = candidate_from_metadata(
        metadata(slug="us-election", question="Who wins?"), "crypto_eth"
    )
    assert not neither.keyword_match
