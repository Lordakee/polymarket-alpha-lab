"""Pure source adapters: raw central-data rows to normalized observations.

Adapters are deterministic and clock-free: freshness is derived entirely
from the raw row's own ``retrieval_time`` and any content timestamp the
documented payload shape carries. Unknown fields are ignored for forward
compatibility; missing required fields, type mismatches, and non-Decimal
numerics produce parse-failed observations with reason codes instead of
fabricated values.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

from .central_data_contracts import (
    FailureStatus,
    Freshness,
    NormalizedObservation,
    ObservationValueState,
    ParseState,
    SourceDefinition,
)
from .central_data_db_row import NormalizedObservationRow, RawEventRow
from .central_data_normalization import CentralDataNormalizer, NormalizationError


PARSER_VERSION = "central-data-v1"

Adapter = Callable[[SourceDefinition, RawEventRow], tuple[NormalizedObservationRow, ...]]


def _freshness(policy_seconds: int, retrieval: datetime, observation: datetime) -> Freshness:
    age = (retrieval - observation).total_seconds()
    if age < 0:
        return Freshness.UNKNOWN
    return Freshness.FRESH if age <= policy_seconds else Freshness.STALE


def _failed_observation(
    source_def: SourceDefinition,
    raw: RawEventRow,
    reason: str,
) -> NormalizedObservation:
    return CentralDataNormalizer.build_observation(
        source_def,
        raw.identity,
        observation_time=raw.retrieval_time,
        value=None,
        freshness=_freshness(
            source_def.freshness_policy_seconds,
            raw.retrieval_time,
            raw.retrieval_time,
        ),
        parse_state=ParseState.FAILED,
        value_state=ObservationValueState.NULL,
        reason_codes=(reason,),
        parser_version=PARSER_VERSION,
    )


def _row(
    source_def: SourceDefinition,
    raw: RawEventRow,
    observation: NormalizedObservation,
) -> NormalizedObservationRow:
    return NormalizedObservationRow.from_contracts(source_def, observation, raw.identity)


def _as_document(raw: RawEventRow) -> Any:
    return CentralDataNormalizer.parse_document(
        raw.raw_body.decode("utf-8"),
        raw.content_type,
    )


def _decimal(value: object) -> Decimal | None:
    if isinstance(value, Decimal):
        return value if value.is_finite() else None
    if type(value) is str:
        try:
            result = Decimal(value)
        except InvalidOperation:
            return None
        return result if result.is_finite() else None
    return None


def parse_gamma_markets(
    source_def: SourceDefinition,
    raw: RawEventRow,
) -> tuple[NormalizedObservationRow, ...]:
    """Map a Gamma ``/markets`` page to one observation per market item."""

    try:
        document = _as_document(raw)
    except (NormalizationError, UnicodeDecodeError):
        return (_row(source_def, raw, _failed_observation(source_def, raw, "json_parse_failed")),)
    if not isinstance(document, list):
        return (_row(source_def, raw, _failed_observation(source_def, raw, "type_mismatch")),)

    rows: list[NormalizedObservationRow] = []
    for item in document:
        if not isinstance(item, dict):
            rows.append(_row(source_def, raw, _failed_observation(source_def, raw, "type_mismatch")))
            continue
        required = ("conditionId", "question", "slug")
        missing = [name for name in required if name not in item or item[name] is None]
        mismatched = [
            name for name in required if name in item and type(item[name]) is not str
        ]
        if missing or mismatched:
            reason = "missing_required_field" if missing else "type_mismatch"
            rows.append(_row(source_def, raw, _failed_observation(source_def, raw, reason)))
            continue
        value: dict[str, Any] = {
            "condition_id": item["conditionId"],
            "question": item["question"],
            "slug": item["slug"],
            "active": bool(item.get("active")) if isinstance(item.get("active"), bool) else None,
            "closed": bool(item.get("closed")) if isinstance(item.get("closed"), bool) else None,
            "end_date_iso": item.get("endDate") if type(item.get("endDate")) is str else None,
        }
        reason_codes: list[str] = []
        for embedded_name, key in (
            ("outcomePrices", "outcome_prices"),
            ("outcomes", "outcomes"),
            ("clobTokenIds", "clob_token_ids"),
        ):
            encoded = item.get(embedded_name)
            decoded: Any = None
            if type(encoded) is str:
                try:
                    decoded = CentralDataNormalizer.parse_json(encoded)
                except NormalizationError:
                    decoded = None
            if decoded is None:
                reason_codes.append("embedded_json_invalid")
            else:
                value[key] = decoded
        observation = CentralDataNormalizer.build_observation(
            source_def,
            raw.identity,
            observation_time=raw.retrieval_time,
            value=value,
            freshness=_freshness(
                source_def.freshness_policy_seconds,
                raw.retrieval_time,
                raw.retrieval_time,
            ),
            reason_codes=tuple(sorted(set(reason_codes))),
            parser_version=PARSER_VERSION,
        )
        rows.append(_row(source_def, raw, observation))
    return tuple(rows)


def parse_clob_book(
    source_def: SourceDefinition,
    raw: RawEventRow,
) -> tuple[NormalizedObservationRow, ...]:
    """Map a CLOB ``/book`` snapshot to one observation with content time."""

    try:
        document = _as_document(raw)
    except (NormalizationError, UnicodeDecodeError):
        return (_row(source_def, raw, _failed_observation(source_def, raw, "json_parse_failed")),)
    if not isinstance(document, dict):
        return (_row(source_def, raw, _failed_observation(source_def, raw, "type_mismatch")),)
    required = ("market", "asset_id", "bids", "asks")
    if any(name not in document or document[name] is None for name in required):
        return (_row(source_def, raw, _failed_observation(source_def, raw, "missing_required_field")),)
    if any(type(document[name]) is not str for name in ("market", "asset_id")) or not isinstance(
        document["bids"], list
    ) or not isinstance(document["asks"], list):
        return (_row(source_def, raw, _failed_observation(source_def, raw, "type_mismatch")),)

    def _levels(items: list[Any]) -> list[dict[str, Any]] | None:
        levels: list[dict[str, Any]] = []
        for entry in items:
            if not isinstance(entry, dict):
                return None
            price = _decimal(entry.get("price"))
            size = _decimal(entry.get("size"))
            if price is None or size is None:
                return None
            levels.append({"price": price, "size": size})
        return levels

    bids = _levels(document["bids"])
    asks = _levels(document["asks"])
    if bids is None or asks is None:
        return (_row(source_def, raw, _failed_observation(source_def, raw, "type_mismatch")),)

    reason_codes: list[str] = []
    observation_time = raw.retrieval_time
    timestamp = document.get("timestamp")
    if type(timestamp) is str and timestamp.isdigit():
        epoch = int(timestamp)
        # CLOB reports milliseconds; normalize deterministically.
        if epoch > 10**12:
            epoch //= 1000
        observation_time = datetime.fromtimestamp(epoch, tz=UTC)
    elif timestamp is not None:
        reason_codes.append("invalid_content_timestamp")
    value = {
        "market": document["market"],
        "asset_id": document["asset_id"],
        "bids": bids,
        "asks": asks,
        "timestamp_epoch": timestamp if type(timestamp) is str else None,
    }
    observation = CentralDataNormalizer.build_observation(
        source_def,
        raw.identity,
        observation_time=observation_time,
        value=value,
        freshness=_freshness(
            source_def.freshness_policy_seconds,
            raw.retrieval_time,
            observation_time,
        ),
        reason_codes=tuple(sorted(set(reason_codes))),
        parser_version=PARSER_VERSION,
    )
    return (_row(source_def, raw, observation),)


def parse_kraken_ticker(
    source_def: SourceDefinition,
    raw: RawEventRow,
) -> tuple[NormalizedObservationRow, ...]:
    """Map a Kraken ``/0/public/Ticker`` response to one BTC observation."""

    try:
        document = _as_document(raw)
    except (NormalizationError, UnicodeDecodeError):
        return (_row(source_def, raw, _failed_observation(source_def, raw, "json_parse_failed")),)
    if not isinstance(document, dict):
        return (_row(source_def, raw, _failed_observation(source_def, raw, "type_mismatch")),)
    errors = document.get("error")
    if not isinstance(errors, list):
        return (_row(source_def, raw, _failed_observation(source_def, raw, "type_mismatch")),)
    if errors:
        return (_row(source_def, raw, _failed_observation(source_def, raw, "provider_error")),)
    result = document.get("result")
    if not isinstance(result, dict) or not result:
        return (_row(source_def, raw, _failed_observation(source_def, raw, "missing_required_field")),)
    pair_name, ticker = next(iter(result.items()))
    if not isinstance(ticker, dict):
        return (_row(source_def, raw, _failed_observation(source_def, raw, "type_mismatch")),)
    levels: dict[str, Decimal | None] = {}
    for key in ("c", "a", "b"):
        entry = ticker.get(key)
        if not isinstance(entry, list) or not entry:
            return (_row(source_def, raw, _failed_observation(source_def, raw, "missing_required_field")),)
        levels[key] = _decimal(entry[0])
    if any(price is None for price in levels.values()):
        return (_row(source_def, raw, _failed_observation(source_def, raw, "type_mismatch")),)
    value = {
        "pair": pair_name,
        "last_price": levels["c"],
        "ask_price": levels["a"],
        "bid_price": levels["b"],
    }
    observation = CentralDataNormalizer.build_observation(
        source_def,
        raw.identity,
        observation_time=raw.retrieval_time,
        value=value,
        freshness=_freshness(
            source_def.freshness_policy_seconds,
            raw.retrieval_time,
            raw.retrieval_time,
        ),
        parser_version=PARSER_VERSION,
    )
    return (_row(source_def, raw, observation),)


SOURCE_PARSERS: dict[str, Adapter] = {
    "polymarket_gamma_markets": parse_gamma_markets,
    "polymarket_clob_book": parse_clob_book,
    "kraken_btc_ticker": parse_kraken_ticker,
}


__all__ = (
    "SOURCE_PARSERS",
    "parse_clob_book",
    "parse_gamma_markets",
    "parse_kraken_ticker",
)
