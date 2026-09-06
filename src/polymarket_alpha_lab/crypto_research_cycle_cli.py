"""Bounded CLI handlers for the crypto research-cycle commands (P1).

Command registration stays in ``cli.py``. Handlers compose the impure
pieces around the pure contracts: the single-market cycle, cohort
collection, settled-outcome import, the read-only settlement export,
and the research inventory census. Persistence follows the established
env-gated local-DSN pattern; a transient flock guards collection
overlap.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import fcntl
from pathlib import Path
import sys
import tempfile


COLLECTION_LOCK_PATH = "/tmp/pal-research-collection.lock"


class _DiscardingCentralStore:
    """No-op store used when central-data persistence is disabled."""

    def insert_raw_event(self, row):
        from polymarket_alpha_lab.central_data_store import CentralDataInsertResult

        return CentralDataInsertResult(row.raw_event_id, "not_persisted")

    def insert_normalized_observation(self, row):
        from polymarket_alpha_lab.central_data_store import CentralDataInsertResult

        return CentralDataInsertResult(row.normalized_observation_id, "not_persisted")


def _team_wiring(team_id: str) -> dict:
    from polymarket_alpha_lab.central_evidence_dispatch import (
        BTC_ITEM_REQUIREMENTS,
        ETH_ITEM_REQUIREMENTS,
    )
    from polymarket_alpha_lab.crypto_btc_evidence_adapter import adapt_btc_evidence
    from polymarket_alpha_lab.crypto_btc_team import (
        CryptoBtcTeamConfig,
        build_crypto_btc_team_forecast,
    )
    from polymarket_alpha_lab.crypto_eth_evidence_adapter import adapt_eth_evidence
    from polymarket_alpha_lab.crypto_eth_team import (
        CryptoEthTeamConfig,
        build_crypto_eth_team_forecast,
    )

    wiring = {
        "crypto_btc": {
            "spot_source": "kraken_btc_ticker",
            "spot_params": {"pair": "XBTUSD"},
            "gamma_tag_id": 235,
            "requirements": BTC_ITEM_REQUIREMENTS,
            "adapter": adapt_btc_evidence,
            "builder": build_crypto_btc_team_forecast,
            "config_factory": CryptoBtcTeamConfig,
        },
        "crypto_eth": {
            "spot_source": "kraken_eth_ticker",
            "spot_params": {"pair": "ETHUSD"},
            "gamma_tag_id": 39,
            "requirements": ETH_ITEM_REQUIREMENTS,
            "adapter": adapt_eth_evidence,
            "builder": build_crypto_eth_team_forecast,
            "config_factory": CryptoEthTeamConfig,
        },
    }
    if team_id not in wiring:
        raise ValueError(f"unsupported team {team_id!r}")
    return wiring[team_id]


def _spot_item_name(team: str) -> str:
    return {"crypto_btc": "btc_spot_price", "crypto_eth": "eth_spot_price"}[team]


def _yes_token_from_metadata(metadata_value: object) -> str | None:
    from polymarket_alpha_lab.crypto_research_cycle import yes_token_id_from_metadata

    return yes_token_id_from_metadata(metadata_value)


class _CycleBlocked(RuntimeError):
    """A market could not be attempted (infrastructure-level failure)."""


@dataclass(frozen=True)
class _CycleExecution:
    result: object
    bundle: object
    outcomes: tuple


def _resolve_persistence():
    from polymarket_alpha_lab.supabase_central_data_config import from_central_data_env
    from polymarket_alpha_lab.supabase_team_forecast_config import from_team_forecast_db_env

    central_config = from_central_data_env()
    if central_config.enabled and central_config.dsn is not None:
        from polymarket_alpha_lab.central_data_psycopg import CentralDataPsycopg

        store = CentralDataPsycopg(central_config.dsn)
    else:
        store = _DiscardingCentralStore()
    forecast_config = from_team_forecast_db_env()
    return store, central_config, forecast_config


def _execute_crypto_cycle(
    team: str,
    market: str,
    *,
    registry,
    transport,
    store,
    forecast_config,
    wiring=None,
) -> _CycleExecution:
    from polymarket_alpha_lab.central_data_acquisition import acquire_once
    from polymarket_alpha_lab.central_data_contracts import FailureStatus
    from polymarket_alpha_lab.central_data_db_row import TypedEnvelope
    from polymarket_alpha_lab.central_evidence_dispatch import build_evidence_bundle
    from polymarket_alpha_lab.crypto_research_cycle import run_crypto_research_cycle

    wiring = wiring or _team_wiring(team)
    gamma_params = {"condition_ids": market} if market.startswith("0x") else {"slug": market}
    gamma_outcome = acquire_once(
        registry.get("polymarket_gamma_markets"),
        transport=transport,
        store=store,
        params={**gamma_params, "limit": 5},
    )
    if gamma_outcome.failure_status is not FailureStatus.NONE or not gamma_outcome.normalized_rows:
        raise _CycleBlocked(
            f"gamma metadata unavailable ({gamma_outcome.failure_status.value}; "
            f"{', '.join(gamma_outcome.reason_codes) or 'no reasons'})"
        )
    metadata_row = gamma_outcome.normalized_rows[0]
    metadata_value = TypedEnvelope.decode(dict(metadata_row.typed_value))
    if not isinstance(metadata_value, dict):
        raise _CycleBlocked("gamma metadata identity unavailable")
    returned_condition = metadata_value.get("condition_id")
    returned_slug = metadata_value.get("slug")
    identity_mismatch = (
        returned_condition != market
        if market.startswith("0x")
        else returned_slug != market
    )
    if identity_mismatch:
        raise _CycleBlocked("gamma metadata identity mismatch")
    yes_token = _yes_token_from_metadata(metadata_value)

    book_outcome = (
        acquire_once(
            registry.get("polymarket_clob_book"),
            transport=transport,
            store=store,
            params={"token_id": yes_token},
        )
        if yes_token is not None
        else None
    )
    spot_outcome = acquire_once(
        registry.get(wiring["spot_source"]),
        transport=transport,
        store=store,
        params=dict(wiring["spot_params"]),
    )

    now = datetime.now(UTC)
    observations_by_source: dict[str, list] = {
        "polymarket_gamma_markets": [metadata_row],
    }
    if book_outcome is not None and book_outcome.normalized_rows:
        observations_by_source["polymarket_clob_book"] = list(book_outcome.normalized_rows)
    if spot_outcome.normalized_rows:
        observations_by_source[wiring["spot_source"]] = list(spot_outcome.normalized_rows)

    bundle = build_evidence_bundle(
        team,
        wiring["requirements"],
        observations_by_source,
        registry,
        as_of=now,
        market_reference=market,
    )
    result = run_crypto_research_cycle(
        team_id=team,
        spot_item=_spot_item_name(team),
        bundle=bundle,
        metadata_observation=metadata_row,
        book_observation=book_outcome.normalized_rows[0]
        if book_outcome is not None and book_outcome.normalized_rows
        else None,
        spot_observation=spot_outcome.normalized_rows[0]
        if spot_outcome.normalized_rows
        else None,
        as_of=now,
        generated_at=now,
        config=wiring["config_factory"](config_version=f"p1-{team}-v1"),
        adapt_evidence=wiring["adapter"],
        build_forecast=wiring["builder"],
        market_slug_hint=market,
        condition_id_hint=market,
    )

    if result.status == "ready" and forecast_config.enabled and forecast_config.dsn is not None:
        from polymarket_alpha_lab.team_forecast_psycopg import (
            insert_team_forecast_evidence_with_psycopg,
            insert_team_forecast_with_psycopg,
        )

        insert_team_forecast_with_psycopg(
            forecast_config.dsn,
            result.forecast,
            table_name=forecast_config.team_forecast_table_name,
        )
        for evidence_packet in result.evidence_packets:
            insert_team_forecast_evidence_with_psycopg(
                forecast_config.dsn,
                evidence_packet,
                forecast_id=result.forecast.forecast_id,
                config_version=result.forecast.config_version,
                generated_at=result.forecast.generated_at,
                table_name=forecast_config.team_forecast_evidence_table_name,
            )

    outcomes = tuple(
        outcome
        for outcome in (gamma_outcome, book_outcome, spot_outcome)
        if outcome is not None
    )
    return _CycleExecution(result=result, bundle=bundle, outcomes=outcomes)


def run_crypto_research_cycle_command(*, team: str, market: str) -> int:
    from polymarket_alpha_lab.btc_cycle_diagnostics import format_btc_cycle_diagnostics
    from polymarket_alpha_lab.central_data_registry import (
        build_default_source_registry,
        default_allowed_hosts,
    )
    from polymarket_alpha_lab.central_data_transport import SafeGETTransport

    if type(market) is not str or not market.strip():
        print("crypto-research-cycle failed: --market must be nonblank", file=sys.stderr)
        return 2
    try:
        wiring = _team_wiring(team)
    except ValueError:
        print(f"crypto-research-cycle failed: unsupported team {team!r}", file=sys.stderr)
        return 2

    registry = build_default_source_registry()
    transport = SafeGETTransport(
        allowed_hosts=default_allowed_hosts(),
        source_catalog=registry,
        max_attempts=2,
    )
    store, _central_config, forecast_config = _resolve_persistence()
    try:
        execution = _execute_crypto_cycle(
            team, market, registry=registry, transport=transport,
            store=store, forecast_config=forecast_config, wiring=wiring,
        )
    except _CycleBlocked as blocked:
        print(f"crypto-research-cycle blocked: {blocked}", file=sys.stderr)
        return 1
    print(execution.result.operator_packet)
    print()
    print(
        format_btc_cycle_diagnostics(execution.outcomes, execution.bundle, execution.result)
    )
    return 0 if execution.result.status == "ready" else 1


def run_btc_research_cycle_command(*, market: str) -> int:
    """Backward-compatible BTC-only entry (the M3 command)."""

    return run_crypto_research_cycle_command(team="crypto_btc", market=market)


def run_collect_research_cycles_command(*, team: str, limit: int, offset: int) -> int:
    from polymarket_alpha_lab.central_data_acquisition import acquire_once
    from polymarket_alpha_lab.central_data_contracts import FailureStatus
    from polymarket_alpha_lab.central_data_db_row import TypedEnvelope
    from polymarket_alpha_lab.central_data_registry import (
        build_default_source_registry,
        default_allowed_hosts,
    )
    from polymarket_alpha_lab.central_data_transport import SafeGETTransport
    from polymarket_alpha_lab.research_cohort import candidate_from_metadata, select_cohort

    try:
        wiring = _team_wiring(team)
    except ValueError:
        print(f"collect-research-cycles failed: unsupported team {team!r}", file=sys.stderr)
        return 2
    if type(limit) is not int or not 1 <= limit <= 100:
        print("collect-research-cycles failed: --limit must be between 1 and 100", file=sys.stderr)
        return 2
    if type(offset) is not int or offset < 0:
        print("collect-research-cycles failed: --offset must be nonnegative", file=sys.stderr)
        return 2

    lock_file = open(COLLECTION_LOCK_PATH, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file.close()
        print(
            "collect-research-cycles failed: another collection run holds the lock",
            file=sys.stderr,
        )
        return 3

    registry = build_default_source_registry()
    transport = SafeGETTransport(
        allowed_hosts=default_allowed_hosts(),
        source_catalog=registry,
        max_attempts=2,
    )
    store, central_config, forecast_config = _resolve_persistence()
    listing = acquire_once(
        registry.get("polymarket_gamma_markets"),
        transport=transport,
        store=store,
        params={
            "closed": "false",
            "tag_id": wiring["gamma_tag_id"],
            "limit": limit,
            "offset": offset,
        },
    )
    if listing.failure_status is not FailureStatus.NONE or not listing.normalized_rows:
        lock_file.close()
        print(
            "collect-research-cycles failed: gamma listing unavailable "
            f"({listing.failure_status.value})",
            file=sys.stderr,
        )
        return 1
    candidates = []
    invalid_metadata = 0
    for row in listing.normalized_rows:
        try:
            candidates.append(
                candidate_from_metadata(TypedEnvelope.decode(dict(row.typed_value)), team)
            )
        except (TypeError, ValueError):
            invalid_metadata += 1
    selected = select_cohort(candidates, limit=limit)
    print(
        f"collection team={team} page_rows={len(listing.normalized_rows)} "
        f"eligible={len(selected)} invalid_metadata={invalid_metadata} persistence="
        f"{'central' if central_config.enabled else 'discarding'}"
        + ("+forecast" if forecast_config.enabled else "")
    )
    attempted = ready = blocked = 0
    try:
        for candidate in selected:
            attempted += 1
            try:
                execution = _execute_crypto_cycle(
                    team, candidate.market_slug, registry=registry,
                    transport=transport, store=store, forecast_config=forecast_config,
                )
            except _CycleBlocked as blocked_reason:
                blocked += 1
                print(
                    f"market {candidate.condition_id} status=attempt_blocked "
                    f"reason={blocked_reason}"
                )
                continue
            if execution.result.status == "ready":
                ready += 1
            else:
                blocked += 1
            print(
                f"market {candidate.condition_id} status={execution.result.status} "
                f"cycle_id={execution.result.cycle_id} "
                f"reasons={','.join(execution.result.reason_codes) or 'none'}"
            )
    finally:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
        finally:
            lock_file.close()
    print(f"summary attempted={attempted} ready={ready} blocked={blocked}")
    return 0


def run_research_inventory_command() -> int:
    store, central_config, forecast_config = _resolve_persistence()
    lines = ["research inventory"]
    lines.append(
        f"central_data_persistence: {'enabled' if central_config.enabled else 'disabled'}"
    )
    lines.append(
        f"team_forecast_persistence: {'enabled' if forecast_config.enabled else 'disabled'}"
    )
    if isinstance(store, _DiscardingCentralStore):
        lines.append("central_rows: not_persisted(discarding_store)")
    else:
        import psycopg

        from polymarket_alpha_lab.central_data_store import (
            AUDIT_TABLE,
            NORMALIZED_TABLE,
            RAW_TABLE,
        )

        with psycopg.connect(central_config.dsn) as connection:
            with connection.cursor() as cursor:
                for label, table in (
                    ("raw", RAW_TABLE),
                    ("normalized", NORMALIZED_TABLE),
                    ("audit", AUDIT_TABLE),
                    ("settled_outcomes", "research_settlement.research_settled_outcomes"),
                ):
                    cursor.execute(f"SELECT count(*) FROM {table}")
                    lines.append(f"central_{label}: {cursor.fetchone()[0]}")
    if forecast_config.enabled and forecast_config.dsn is not None:
        import psycopg

        with psycopg.connect(forecast_config.dsn) as connection:
            with connection.cursor() as cursor:
                for label, table in (
                    ("forecasts", forecast_config.team_forecast_table_name),
                    ("evidence", forecast_config.team_forecast_evidence_table_name),
                ):
                    cursor.execute(f"SELECT count(*) FROM {table}")
                    lines.append(f"team_{label}: {cursor.fetchone()[0]}")
    else:
        lines.append("team_forecasts: disabled")
    print("\n".join(lines))
    return 0


def _load_forecast_condition_ids(forecast_config) -> list[str]:
    import psycopg

    with psycopg.connect(forecast_config.dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT condition_id FROM "
                f"{forecast_config.team_forecast_table_name}"
            )
            return [row[0] for row in cursor.fetchall()]


def _derive_outcome_for_condition(condition_id: str, *, registry, transport, store):
    from polymarket_alpha_lab.central_data_acquisition import acquire_once
    from polymarket_alpha_lab.central_data_contracts import FailureStatus
    from polymarket_alpha_lab.central_data_db_row import TypedEnvelope

    gamma = registry.get("polymarket_gamma_markets")
    outcome_fetch = acquire_once(
        gamma,
        transport=transport,
        store=store,
        params={"condition_ids": condition_id, "limit": 1},
    )
    if outcome_fetch.failure_status is not FailureStatus.NONE or not outcome_fetch.normalized_rows:
        return None
    row = outcome_fetch.normalized_rows[0]
    value = TypedEnvelope.decode(dict(row.typed_value))
    if (
        not isinstance(value, dict)
        or value.get("condition_id") != condition_id
        or value.get("closed") is not True
    ):
        return None
    prices = value.get("outcome_prices")
    tokens = value.get("clob_token_ids")
    outcomes = value.get("outcomes")
    if not isinstance(prices, list) or not isinstance(tokens, list) or not isinstance(outcomes, list):
        return None
    yes_token = _yes_token_from_metadata(value)
    if yes_token is None:
        return None
    try:
        yes_index = tokens.index(yes_token)
    except ValueError:
        return None

    def _final_price(index: int) -> Decimal | None:
        try:
            number = Decimal(str(prices[index]))
        except (ArithmeticError, ValueError):
            return None
        return number if number in (Decimal(0), Decimal(1)) else None

    yes_price = _final_price(yes_index)
    other_index = 1 - yes_index
    other_price = _final_price(other_index) if other_index < len(prices) else None
    if yes_price is None or other_price is None:
        return None
    if yes_price == Decimal(1) and other_price == Decimal(0):
        result = "yes"
    elif yes_price == Decimal(0) and other_price == Decimal(1):
        result = "no"
    else:
        return None
    return row.retrieval_time, result, row.raw_payload_sha256, list(prices)


def run_import_settled_outcomes_command(*, condition_ids: tuple[str, ...] = ()) -> int:
    from polymarket_alpha_lab.central_data_registry import (
        build_default_source_registry,
        default_allowed_hosts,
    )
    from polymarket_alpha_lab.central_data_transport import SafeGETTransport

    store, central_config, forecast_config = _resolve_persistence()
    if not forecast_config.enabled or forecast_config.dsn is None:
        print(
            "import-settled-outcomes failed: team-forecast persistence is disabled",
            file=sys.stderr,
        )
        return 2
    if isinstance(store, _DiscardingCentralStore):
        print(
            "import-settled-outcomes failed: central-data persistence is disabled",
            file=sys.stderr,
        )
        return 2
    targets = list(condition_ids) or _load_forecast_condition_ids(forecast_config)
    if not targets:
        print("import-settled-outcomes: no persisted forecast condition ids found")
        return 0

    registry = build_default_source_registry()
    transport = SafeGETTransport(
        allowed_hosts=default_allowed_hosts(),
        source_catalog=registry,
        max_attempts=2,
    )
    import psycopg
    from psycopg.types.json import Jsonb

    connection = psycopg.connect(central_config.dsn)
    imported = refused = 0
    try:
        with connection.cursor() as cursor:
            for condition_id in sorted(set(targets)):
                outcome = _derive_outcome_for_condition(
                    condition_id, registry=registry, transport=transport, store=store,
                )
                if outcome is None:
                    refused += 1
                    print(
                        f"outcome {condition_id} status=refused "
                        "reason=not_settled_or_ambiguous"
                    )
                    continue
                observed_at, result, payload_hash, snapshot = outcome
                cursor.execute(
                    "INSERT INTO research_settlement.research_settled_outcomes "
                    "(condition_id, observed_at, outcome, resolution_source, "
                    "outcome_prices_snapshot, payload_sha256) "
                    "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    (
                        condition_id,
                        observed_at,
                        result,
                        "polymarket_gamma",
                        Jsonb(snapshot),
                        payload_hash,
                    ),
                )
                if cursor.rowcount == 1:
                    imported += 1
                    status = "imported"
                else:
                    status = "already_present"
                print(f"outcome {condition_id} status={status} outcome={result}")
        connection.commit()
    finally:
        connection.close()
    print(f"summary imported={imported} refused={refused}")
    return 0


def _atomic_write_text(path: Path, document: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary:
        temporary.write(document)
        temporary.flush()
        temporary_path = Path(temporary.name)
    try:
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def run_export_settlement_samples_command(*, cutoff: str, out_path: str) -> int:
    from datetime import datetime as _datetime

    from polymarket_alpha_lab.settlement_export import (
        ForecastRowView,
        SettledOutcomeView,
        build_settlement_export,
    )

    store, central_config, forecast_config = _resolve_persistence()
    if not forecast_config.enabled or forecast_config.dsn is None:
        print(
            "export-settlement-samples failed: team-forecast persistence is disabled",
            file=sys.stderr,
        )
        return 2
    if isinstance(store, _DiscardingCentralStore):
        print(
            "export-settlement-samples failed: central-data persistence is disabled",
            file=sys.stderr,
        )
        return 2

    import psycopg

    forecast_rows: list[ForecastRowView] = []
    invalid_forecast_rows = 0
    with psycopg.connect(forecast_config.dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT forecast_id, condition_id, team_id, config_version, "
                "forecast_probability, generated_at, payload_json "
                f"FROM {forecast_config.team_forecast_table_name}"
            )
            for record in cursor.fetchall():
                payload = record[6] or {}
                observed = payload.get("market_implied_probability_observed")
                try:
                    forecast_rows.append(
                        ForecastRowView(
                            forecast_id=record[0],
                            condition_id=record[1],
                            team_id=record[2],
                            config_version=record[3],
                            forecast_p_yes=Decimal(str(record[4])),
                            market_implied_p_yes=Decimal(str(observed)),
                            generated_at=record[5],
                        )
                    )
                except (ValueError, ArithmeticError, TypeError):
                    invalid_forecast_rows += 1
    outcome_rows: list[SettledOutcomeView] = []
    with psycopg.connect(central_config.dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT condition_id, outcome, observed_at, dispute_flag "
                "FROM research_settlement.research_settled_outcomes"
            )
            for record in cursor.fetchall():
                outcome_rows.append(
                    SettledOutcomeView(
                        condition_id=record[0],
                        outcome=record[1],
                        observed_at=record[2],
                        dispute_flag=record[3],
                    )
                )

    try:
        parsed_cutoff = _datetime.fromisoformat(cutoff)
        export = build_settlement_export(
            forecast_rows,
            outcome_rows,
            as_of_evaluation_cutoff=parsed_cutoff,
            invalid_forecast_row_count=invalid_forecast_rows,
        )
    except ValueError:
        print(
            "export-settlement-samples failed: --cutoff must be an ISO8601 "
            "timezone-aware timestamp",
            file=sys.stderr,
        )
        return 2
    destination = Path(out_path)
    _atomic_write_text(destination, export.document)
    _atomic_write_text(Path(out_path + ".manifest.json"), export.manifest)
    print(
        f"export written {destination} included={export.included_count} "
        f"pending={export.pending_count} "
        f"exclusions={dict(export.exclusion_reasons) or 'none'}"
    )
    return 0


__all__ = (
    "run_btc_research_cycle_command",
    "run_collect_research_cycles_command",
    "run_crypto_research_cycle_command",
    "run_export_settlement_samples_command",
    "run_import_settled_outcomes_command",
    "run_research_inventory_command",
)
