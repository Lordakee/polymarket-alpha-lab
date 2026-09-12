"""Coinbase/Kraken closed-window checks, before model construction; no I/O."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from decimal import Context, Decimal, ROUND_CEILING, localcontext
import re

from polymarket_alpha_lab.team_research_agent_types import ResearchEvidence, aware, hard_flags, integer, strict_json
from polymarket_alpha_lab.team_research_crypto_candles import (
    REASONS as COINBASE_REASONS, CoinbaseCandleSnapshot, CryptoCandleWindow,
    _number, _rows, _scope, _seconds, _source_id, prepare_crypto_candle_evidence,
)
from polymarket_alpha_lab.team_research_intake import ResearchSourceReceipt, evidence_content_sha256
from polymarket_alpha_lab.team_research_kraken_candles import (
    KRAKEN_REASONS, KrakenCandleRejected, KrakenCandleSnapshot,
    _prepare_kraken_evidence, kraken_reference, kraken_source_id,
)

REASONS = (
    "cross_source_matched", "source_window_mismatch", "capture_skew_exceeded",
    "kraken_snapshot_from_future", "kraken_snapshot_stale", "kraken_window_unclosed",
    "close_price_divergence",
    *("coinbase:" + item for item in COINBASE_REASONS if item != "crypto_candles_prepared"),
    *("kraken:" + item for item in KRAKEN_REASONS),
)


@dataclass(frozen=True, slots=True)
class CrossSourcePolicy:
    # Operational data discrepancy tolerance, NOT a calibrated confidence rule.
    max_close_divergence_bps: Decimal = Decimal("100")
    max_capture_skew_seconds: int = 60

    def __post_init__(self) -> None:
        value = self.max_close_divergence_bps
        if (type(value) is not Decimal or not value.is_finite()
                or not Decimal("0") <= value <= Decimal("10000")
                or len(value.as_tuple().digits) > 12
                or not -6 <= value.as_tuple().exponent <= 4):
            raise ValueError("invalid bounded Decimal divergence threshold")
        integer("max_capture_skew_seconds", self.max_capture_skew_seconds, 0, 86400)


def _divergence(a: Decimal, b: Decimal) -> Decimal:
    # 10000 * |a-b| / mean(a,b). Round outward for diagnostics: a small breach
    # must not display as an acceptable equality at a six-decimal threshold.
    with localcontext(Context(prec=96)):
        return (abs(a - b) * Decimal("20000") / (a + b)).quantize(
            Decimal("0.000001"), rounding=ROUND_CEILING)


def _receipt(item: ResearchEvidence) -> ResearchSourceReceipt:
    return ResearchSourceReceipt(item.source_id, evidence_content_sha256(item), item.reference, item.observed_at)


@dataclass(frozen=True, slots=True)
class CryptoCrossSourceCheck:
    team_id: str
    condition_id: str
    window: CryptoCandleWindow
    as_of: datetime
    coinbase_fetched_at: datetime
    kraken_fetched_at: datetime
    coinbase_raw_sha256: str
    kraken_raw_sha256: str
    policy: CrossSourcePolicy
    status: str
    reason_code: str
    close_divergences_bps: tuple[Decimal, ...] = ()
    kraken_excluded_count: int = 0
    evidence: tuple[ResearchEvidence, ...] = field(default=(), repr=False)
    source_receipts: tuple[ResearchSourceReceipt, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.window) is not CryptoCandleWindow or type(self.policy) is not CrossSourcePolicy:
            raise ValueError("expected exact cross-source window and policy")
        object.__setattr__(self, "window", replace(self.window))
        object.__setattr__(self, "policy", replace(self.policy))
        _scope(self.team_id, self.condition_id, self.window)
        for name in ("as_of", "coinbase_fetched_at", "kraken_fetched_at"):
            aware(name, getattr(self, name))
        for digest in (self.coinbase_raw_sha256, self.kraken_raw_sha256):
            if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise ValueError("invalid source digest")
        hard_flags(self)
        if type(self.status) is not str or self.status not in ("matched", "blocked"):
            raise ValueError("invalid cross-source status")
        if type(self.reason_code) is not str or self.reason_code not in REASONS:
            raise ValueError("invalid cross-source reason")
        integer("kraken_excluded_count", self.kraken_excluded_count, 0, 720)
        if type(self.close_divergences_bps) is not tuple:
            raise ValueError("divergences must be an exact tuple")
        if len(self.close_divergences_bps) not in (0, self.window.expected_count):
            raise ValueError("comparisons must cover the entire requested window")
        for value in self.close_divergences_bps:
            if type(value) is not Decimal or not value.is_finite() or not 0 <= value <= 20000:
                raise ValueError("invalid close divergence")
        if type(self.evidence) is not tuple or type(self.source_receipts) is not tuple:
            raise ValueError("evidence and receipts must be tuples")
        if self.status == "blocked":
            if self.reason_code == "cross_source_matched" or self.evidence or self.source_receipts:
                raise ValueError("blocked cross-source check must suppress evidence")
            return
        if (self.reason_code != "cross_source_matched" or len(self.evidence) != 2
                or len(self.source_receipts) != 2 or not self.close_divergences_bps
                or max(self.close_divergences_bps) > self.policy.max_close_divergence_bps
                or not self.window.end <= min(self.coinbase_fetched_at, self.kraken_fetched_at)
                or max(self.coinbase_fetched_at, self.kraken_fetched_at) > self.as_of
                or abs(self.coinbase_fetched_at - self.kraken_fetched_at)
                > timedelta(seconds=self.policy.max_capture_skew_seconds)):
            raise ValueError("matched cross-source contract mismatch")
        expected = (
            (_source_id(self.window, self.coinbase_fetched_at, self.coinbase_raw_sha256),
             self.window.source_reference, "coinbase_exchange", self.coinbase_raw_sha256),
            (kraken_source_id(self.window, self.kraken_fetched_at, self.kraken_raw_sha256),
             kraken_reference(self.window), "kraken", self.kraken_raw_sha256),
        )
        source_closes = []
        for item, receipt, (source_id, reference, provider, digest) in zip(
                self.evidence, self.source_receipts, expected, strict=True):
            if type(item) is not ResearchEvidence or type(receipt) is not ResearchSourceReceipt:
                raise ValueError("expected exact evidence and receipt")
            item.__post_init__()
            receipt.__post_init__()
            if (item.team_id != self.team_id or item.condition_id != self.condition_id
                    or item.observed_at != self.window.end or item.source_id != source_id
                    or item.reference != reference or receipt != _receipt(item)):
                raise ValueError("cross-source evidence binding mismatch")
            body = strict_json(item.text)
            if (type(body) is not dict or body.get("provider") != provider
                    or body.get("raw_content_sha256") != digest
                    or body.get("product_id") != self.window.product_id
                    or body.get("window_start") != self.window.start.isoformat()
                    or body.get("window_end_exclusive") != self.window.end.isoformat()
                    or body.get("granularity_seconds") != self.window.granularity_seconds):
                raise ValueError("cross-source provider or raw-content binding mismatch")
            rows = body.get("candles")
            if type(rows) is not list or len(rows) != self.window.expected_count:
                raise ValueError("cross-source evidence coverage mismatch")
            closes = []
            for index, row in enumerate(rows):
                if (type(row) is not list or len(row) != 6 or type(row[0]) is not int
                        or row[0] != _seconds(self.window.start) + index * self.window.granularity_seconds
                        or type(row[4]) is not str or len(row[4]) > 64):
                    raise ValueError("cross-source evidence bucket mismatch")
                closes.append(_number(Decimal(row[4])))
            source_closes.append(closes)
        calculated = tuple(_divergence(a, b) for a, b in zip(*source_closes, strict=True))
        if calculated != self.close_divergences_bps:
            raise ValueError("cross-source metrics must match bound evidence")

    @property
    def max_observed_divergence_bps(self) -> Decimal | None:
        return max(self.close_divergences_bps) if self.close_divergences_bps else None


def check_crypto_cross_source(
    coinbase: CoinbaseCandleSnapshot, kraken: KrakenCandleSnapshot, *, team_id: str,
    condition_id: str, as_of: datetime, policy: CrossSourcePolicy = CrossSourcePolicy(),
    max_snapshot_age_seconds: int = 300, max_evidence_age_seconds: int = 86400,
) -> CryptoCrossSourceCheck:
    """Require two valid, identical windows and acceptable per-bucket closes.

    No averaging, source substitution, gap fill, probabilities or confidence
    adjustment. Successful checks describe data consistency, not forecast quality.
    """
    if type(coinbase) is not CoinbaseCandleSnapshot or type(kraken) is not KrakenCandleSnapshot:
        raise ValueError("expected exact Coinbase and Kraken snapshots")
    if type(policy) is not CrossSourcePolicy:
        raise ValueError("expected exact CrossSourcePolicy")
    coinbase, kraken, policy = replace(coinbase), replace(kraken), replace(policy)
    _scope(team_id, condition_id, coinbase.window)
    aware("as_of", as_of)
    integer("max_snapshot_age_seconds", max_snapshot_age_seconds, 0, 86400)
    integer("max_evidence_age_seconds", max_evidence_age_seconds, 0, 31536000)

    def report(reason: str, *, differences: tuple = (), excluded: int = 0,
               evidence: tuple = ()) -> CryptoCrossSourceCheck:
        return CryptoCrossSourceCheck(team_id, condition_id, coinbase.window, as_of,
            coinbase.fetched_at, kraken.fetched_at, coinbase.content_sha256, kraken.content_sha256,
            policy, "matched" if reason == "cross_source_matched" else "blocked", reason,
            differences, excluded, evidence, tuple(_receipt(item) for item in evidence))

    if coinbase.window != kraken.window:
        return report("source_window_mismatch")
    primary = prepare_crypto_candle_evidence(coinbase, team_id=team_id, condition_id=condition_id,
        as_of=as_of, max_snapshot_age_seconds=max_snapshot_age_seconds,
        max_evidence_age_seconds=max_evidence_age_seconds)
    if primary.status != "prepared":
        return report("coinbase:" + primary.reason_code)
    if kraken.fetched_at > as_of:
        return report("kraken_snapshot_from_future")
    if as_of - kraken.fetched_at > timedelta(seconds=max_snapshot_age_seconds):
        return report("kraken_snapshot_stale")
    if kraken.window.end > kraken.fetched_at:
        return report("kraken_window_unclosed")
    if abs(coinbase.fetched_at - kraken.fetched_at) > timedelta(seconds=policy.max_capture_skew_seconds):
        return report("capture_skew_exceeded")
    try:
        secondary, kraken_rows, excluded = _prepare_kraken_evidence(
            kraken, team_id=team_id, condition_id=condition_id)
    except KrakenCandleRejected as error:
        return report("kraken:" + str(error))
    # Reuse the existing parser only after its intake succeeds. Snapshots were
    # copied before normalization, and this path never pretends Kraken is Coinbase.
    primary_rows = tuple(sorted(row for row in _rows(coinbase.raw_json, coinbase.window.granularity_seconds)
        if _seconds(coinbase.window.start) <= row[0] < _seconds(coinbase.window.end)))
    differences = tuple(_divergence(left[4], right[4]) for left, right in zip(primary_rows, kraken_rows, strict=True))
    if max(differences) > policy.max_close_divergence_bps:
        return report("close_price_divergence", differences=differences, excluded=excluded)
    return report("cross_source_matched", differences=differences, excluded=excluded,
                  evidence=(primary.evidence, secondary))


__all__ = ("CrossSourcePolicy", "CryptoCrossSourceCheck", "check_crypto_cross_source")
