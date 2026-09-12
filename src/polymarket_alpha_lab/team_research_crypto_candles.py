"""Pure, gap-aware BTC/ETH candle evidence intake; no I/O or persistence.

Coinbase spot candles are a single external venue's observations, not a
Polymarket settlement oracle, independent votes, or probability estimates.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
import re
from types import MappingProxyType
from urllib.parse import urlencode

from polymarket_alpha_lab.team_research_agent_types import (
    ResearchEvidence, aware, hard_flags, integer, strict_json, text,
)
from polymarket_alpha_lab.team_research_intake import (
    ResearchSourceReceipt, evidence_content_sha256,
)

PRODUCTS = MappingProxyType({"crypto_btc": "BTC-USD", "crypto_eth": "ETH-USD"})
GRANULARITIES = (60, 300, 900, 3600, 21600, 86400)
MAX_CANDLES = 48
MAX_RESPONSE_CANDLES = 300
MAX_CANDLE_BYTES = 131072
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
REASONS = (
    "crypto_candles_prepared", "candle_snapshot_from_future", "candle_snapshot_stale",
    "candle_window_unclosed", "candle_window_stale", "invalid_candle_payload",
    "duplicate_candle_bucket", "candle_window_incomplete", "candle_evidence_too_large",
)


def _seconds(value: datetime) -> int:
    delta = value.astimezone(UTC) - EPOCH
    return delta.days * 86400 + delta.seconds


@dataclass(frozen=True, slots=True)
class CryptoCandleWindow:
    product_id: str
    start: datetime
    end: datetime
    granularity_seconds: int = 3600

    def __post_init__(self) -> None:
        if type(self.product_id) is not str or self.product_id not in PRODUCTS.values():
            raise ValueError("only BTC-USD and ETH-USD candle products are supported")
        if type(self.granularity_seconds) is not int or self.granularity_seconds not in GRANULARITIES:
            raise ValueError("unsupported candle granularity")
        for name in ("start", "end"):
            value = getattr(self, name)
            aware(name, value)
            if value.microsecond or value < EPOCH or _seconds(value) % self.granularity_seconds:
                raise ValueError("candle boundaries must be UTC epoch-aligned whole seconds")
            object.__setattr__(self, name, value.astimezone(UTC))
        if not 1 <= self.expected_count <= MAX_CANDLES:
            raise ValueError("candle window must contain one to 48 complete intervals")

    @property
    def expected_count(self) -> int:
        return (_seconds(self.end) - _seconds(self.start)) // self.granularity_seconds

    @property
    def source_reference(self) -> str:
        query = urlencode({"start": self.start.isoformat(), "end": self.end.isoformat(),
                           "granularity": self.granularity_seconds})
        return f"https://api.exchange.coinbase.com/products/{self.product_id}/candles?{query}"


@dataclass(frozen=True, slots=True)
class CoinbaseCandleSnapshot:
    window: CryptoCandleWindow
    fetched_at: datetime
    raw_json: bytes = field(repr=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.window) is not CryptoCandleWindow:
            raise ValueError("expected exact candle window")
        object.__setattr__(self, "window", replace(self.window))
        aware("fetched_at", self.fetched_at)
        if type(self.raw_json) is not bytes or not 1 <= len(self.raw_json) <= MAX_CANDLE_BYTES:
            raise ValueError("invalid candle response size or type")
        hard_flags(self)

    @property
    def content_sha256(self) -> str:
        return sha256(self.raw_json).hexdigest()


def _source_id(window: CryptoCandleWindow, fetched_at: datetime, digest: str) -> str:
    binding = json.dumps([window.source_reference, fetched_at.astimezone(UTC).isoformat(), digest],
                         separators=(",", ":"), ensure_ascii=True).encode()
    return "coinbase-candles-" + sha256(binding).hexdigest()


@dataclass(frozen=True, slots=True)
class CryptoCandleIntake:
    team_id: str
    condition_id: str
    window: CryptoCandleWindow
    as_of: datetime
    fetched_at: datetime
    raw_content_sha256: str
    status: str
    reason_code: str
    accepted_count: int = 0
    excluded_count: int = 0
    missing_count: int = 0
    evidence: ResearchEvidence | None = field(default=None, repr=False)
    receipt: ResearchSourceReceipt | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.window) is not CryptoCandleWindow:
            raise ValueError("expected exact candle window")
        self.window.__post_init__()
        _scope(self.team_id, self.condition_id, self.window)
        aware("as_of", self.as_of)
        aware("fetched_at", self.fetched_at)
        hard_flags(self)
        if type(self.raw_content_sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", self.raw_content_sha256) is None:
            raise ValueError("invalid candle content digest")
        if type(self.status) is not str or self.status not in ("prepared", "blocked"):
            raise ValueError("invalid candle intake status")
        if type(self.reason_code) is not str or self.reason_code not in REASONS:
            raise ValueError("invalid candle intake reason")
        for name in ("accepted_count", "excluded_count", "missing_count"):
            integer(name, getattr(self, name), 0, MAX_RESPONSE_CANDLES)
        if self.accepted_count + self.excluded_count > MAX_RESPONSE_CANDLES or self.missing_count > self.window.expected_count:
            raise ValueError("invalid candle counts")
        if self.status == "blocked":
            if self.reason_code == "crypto_candles_prepared" or self.evidence is not None or self.receipt is not None:
                raise ValueError("blocked candles must suppress evidence and receipts")
            return
        if (self.reason_code != "crypto_candles_prepared" or self.missing_count
                or self.accepted_count != self.window.expected_count
                or not self.window.end <= self.fetched_at <= self.as_of):
            raise ValueError("prepared candle contract mismatch")
        if type(self.evidence) is not ResearchEvidence or type(self.receipt) is not ResearchSourceReceipt:
            raise ValueError("prepared candles require exact evidence and receipt")
        self.evidence.__post_init__()
        self.receipt.__post_init__()
        expected_id = _source_id(self.window, self.fetched_at, self.raw_content_sha256)
        if (self.evidence.source_id != expected_id or self.evidence.team_id != self.team_id
                or self.evidence.condition_id != self.condition_id
                or self.evidence.observed_at != self.window.end
                or self.evidence.reference != self.window.source_reference):
            raise ValueError("candle evidence scope or provenance mismatch")
        expected = ResearchSourceReceipt(expected_id, evidence_content_sha256(self.evidence),
                                         self.window.source_reference, self.window.end)
        if self.receipt != expected:
            raise ValueError("candle receipt must bind the full evidence record")


def _scope(team_id: str, condition_id: str, window: CryptoCandleWindow) -> None:
    if type(team_id) is not str or PRODUCTS.get(team_id) != window.product_id:
        raise ValueError("candle product must match the explicitly assigned crypto team")
    text("condition_id", condition_id)


def _number(value: object, *, volume: bool = False) -> Decimal:
    if type(value) not in (int, Decimal):
        raise ValueError("candle values must be JSON numbers, not strings or booleans")
    number = Decimal(value)
    if (not number.is_finite() or len(number.as_tuple().digits) > 24
            or not -12 <= number.as_tuple().exponent <= 18
            or not Decimal("0") <= number <= Decimal("1e18")
            or (not volume and number <= 0)):
        raise ValueError("invalid bounded candle number")
    return number


def _rows(raw: bytes, granularity: int) -> tuple[tuple, ...]:
    payload = strict_json(raw.decode("utf-8"))
    if type(payload) is not list or len(payload) > MAX_RESPONSE_CANDLES:
        raise ValueError("invalid candle array")
    rows = []
    for row in payload:
        if type(row) is not list or len(row) != 6:
            raise ValueError("candles require time/low/high/open/close/volume")
        stamp = row[0]
        integer("bucket time", stamp, 0, 253402300799)
        if stamp % granularity:
            raise ValueError("unaligned candle bucket")
        low, high, opening, closing = (_number(value) for value in row[1:5])
        volume = _number(row[5], volume=True)
        if not low <= min(opening, closing) <= max(opening, closing) <= high:
            raise ValueError("inconsistent candle OHLC")
        rows.append((stamp, low, high, opening, closing, volume))
    return tuple(rows)


def prepare_crypto_candle_evidence(
    snapshot: CoinbaseCandleSnapshot, *, team_id: str, condition_id: str, as_of: datetime,
    max_snapshot_age_seconds: int = 300, max_evidence_age_seconds: int = 86400,
) -> CryptoCandleIntake:
    """Normalize a complete closed window or return a packetless blocked report.

    Extra rows outside [start,end) are counted, not used. Gaps are never filled.
    observed_at is the last bucket END, not its start or the retrieval time.
    The caller owns semantic matching to the question and settlement oracle.
    """
    if type(snapshot) is not CoinbaseCandleSnapshot:
        raise ValueError("expected exact CoinbaseCandleSnapshot")
    snapshot = replace(snapshot)
    window = snapshot.window
    _scope(team_id, condition_id, window)
    aware("as_of", as_of)
    integer("max_snapshot_age_seconds", max_snapshot_age_seconds, 0, 86400)
    integer("max_evidence_age_seconds", max_evidence_age_seconds, 0, 31536000)

    def report(reason: str, *, rows: tuple = (), excluded: int = 0, missing: int = 0,
               evidence: ResearchEvidence | None = None) -> CryptoCandleIntake:
        receipt = None if evidence is None else ResearchSourceReceipt(
            evidence.source_id, evidence_content_sha256(evidence), evidence.reference, evidence.observed_at)
        return CryptoCandleIntake(team_id, condition_id, window, as_of, snapshot.fetched_at,
                                 snapshot.content_sha256, "prepared" if evidence else "blocked", reason,
                                 len(rows), excluded, missing, evidence, receipt)

    if snapshot.fetched_at > as_of:
        return report("candle_snapshot_from_future")
    if as_of - snapshot.fetched_at > timedelta(seconds=max_snapshot_age_seconds):
        return report("candle_snapshot_stale")
    if window.end > snapshot.fetched_at:
        return report("candle_window_unclosed")
    if as_of - window.end > timedelta(seconds=max_evidence_age_seconds):
        return report("candle_window_stale")
    try:
        parsed = _rows(snapshot.raw_json, window.granularity_seconds)
    except (ValueError, TypeError, UnicodeError, ArithmeticError, RecursionError):
        return report("invalid_candle_payload")
    if len({row[0] for row in parsed}) != len(parsed):
        return report("duplicate_candle_bucket")
    expected = set(range(_seconds(window.start), _seconds(window.end), window.granularity_seconds))
    selected = tuple(sorted(row for row in parsed if row[0] in expected))
    excluded = len(parsed) - len(selected)
    missing = len(expected - {row[0] for row in selected})
    if missing:
        return report("candle_window_incomplete", rows=selected, excluded=excluded, missing=missing)
    with localcontext(Context(prec=64)):
        change = ((selected[-1][4] / selected[0][3]) - Decimal("1")).quantize(Decimal("0.000001"))
    body = json.dumps({
        "provider": "coinbase_exchange", "product_id": window.product_id,
        "price_currency": "USD", "volume_currency": window.product_id.split("-")[0],
        "window_start": window.start.isoformat(), "window_end_exclusive": window.end.isoformat(),
        "granularity_seconds": window.granularity_seconds,
        "fetched_at": snapshot.fetched_at.astimezone(UTC).isoformat(),
        "raw_content_sha256": snapshot.content_sha256,
        "columns": ["bucket_start_unix", "low", "high", "open", "close", "volume"],
        "candles": [[row[0], *(format(value, "f") for value in row[1:])] for row in selected],
        "window_return_fraction": format(change, "f"),
        "limitations": "Single-venue historical spot data; not an oracle, probability, or independent source votes.",
    }, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(body) > 12000:
        return report("candle_evidence_too_large", rows=selected, excluded=excluded)
    evidence = ResearchEvidence(
        _source_id(window, snapshot.fetched_at, snapshot.content_sha256), team_id, condition_id,
        f"Coinbase {window.product_id} closed spot candles", body, window.source_reference, window.end,
    )
    return report("crypto_candles_prepared", rows=selected, excluded=excluded, evidence=evidence)


__all__ = ("CryptoCandleWindow", "CoinbaseCandleSnapshot", "CryptoCandleIntake", "prepare_crypto_candle_evidence")
