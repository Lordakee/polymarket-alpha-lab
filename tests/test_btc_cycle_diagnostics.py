from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.btc_cycle_diagnostics import format_btc_cycle_diagnostics
from polymarket_alpha_lab.btc_research_cycle import BtcCycleResult
from polymarket_alpha_lab.central_data_acquisition import AcquisitionOutcome
from polymarket_alpha_lab.central_data_contracts import (
    FailureStatus,
    Freshness,
    ObservationValueState,
    ParseState,
)
from polymarket_alpha_lab.central_evidence_bundle import (
    EvidenceBundle,
    EvidenceItemAvailability,
    SelectedEvidence,
    ZeroWeightPlaceholder,
)


AS_OF = datetime(2026, 9, 6, 12, 0, 0, tzinfo=UTC)


def _selected() -> SelectedEvidence:
    return SelectedEvidence(
        observation_id="a" * 64,
        source_id="kraken_btc_ticker",
        source_family="kraken_public",
        observation_time=AS_OF - timedelta(seconds=10),
        retrieval_time=AS_OF - timedelta(seconds=5),
        payload_hash="b" * 64,
        parser_version="central-data-v1",
        parse_state=ParseState.SUCCESS,
        freshness_state=Freshness.FRESH,
        value_state=ObservationValueState.PRESENT,
    )


def _outcome(source_id: str, failure: FailureStatus, *, reasons=(), attempts=2, retry=60) -> AcquisitionOutcome:
    return AcquisitionOutcome(
        source_id=source_id,
        request_identity="c" * 64,
        raw_result=None,
        normalized_rows=(),
        failure_status=failure,
        reason_codes=tuple(reasons),
        attempts=attempts,
        retry_after_seconds=retry,
        pages_fetched=0,
    )


def _bundle_and_result():
    selected = _selected()
    bundle = EvidenceBundle(
        team_id="crypto_btc",
        market_reference="btc-market",
        as_of=AS_OF,
        items={
            "btc_spot_price": selected,
            "clob_book_depth": ZeroWeightPlaceholder(
                item_name="clob_book_depth",
                availability=EvidenceItemAvailability.STALE,
                reason_codes=("item_stale",),
            ),
        },
        reason_codes=("item_stale_reason",),
    )
    result = BtcCycleResult(
        status="blocked",
        cycle_id="d" * 64,
        condition_id="0xabc",
        market_slug="btc-market",
        reason_codes=("bundle_blocked", "book_observation_missing"),
        forecast=None,
        evidence_packets=(),
        base_probability=None,
        operator_packet="unused",
    )
    return bundle, result


def test_diagnostics_are_deterministic_structured_and_redacted() -> None:
    bundle, result = _bundle_and_result()
    outcomes = (
        _outcome("kraken_btc_ticker", FailureStatus.NONE, attempts=1, retry=None),
        _outcome("polymarket_clob_book", FailureStatus.HTTP_ERROR, reasons=("http_error_429",)),
    )
    text = format_btc_cycle_diagnostics(outcomes, bundle, result)
    assert text == format_btc_cycle_diagnostics(outcomes, bundle, result)
    assert "cycle_status: blocked" in text
    assert "bundle_status: blocked" in text
    assert "polymarket_clob_book: status=http_error attempts=2 retry_after=60s" in text
    assert "reasons=http_error_429" in text
    assert "clob_book_depth: stale reasons=item_stale" in text
    assert "btc_spot_price: ready family=kraken_public" in text
    assert "cycle_reasons: bundle_blocked, book_observation_missing" in text
    # Redaction: no URLs, no bodies, no credentials appear anywhere.
    for forbidden in ("https://", "password", "authorization", "@", "0x9143"):
        assert forbidden not in text


def test_diagnostics_reject_wrong_types() -> None:
    bundle, result = _bundle_and_result()
    with pytest.raises(ValueError):
        format_btc_cycle_diagnostics((), bundle, object())  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        format_btc_cycle_diagnostics((), object(), result)  # type: ignore[arg-type]
