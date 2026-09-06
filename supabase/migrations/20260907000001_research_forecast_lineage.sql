-- P2a: contemporaneous event lineage for persisted research forecasts.
-- Owner: postgres, database: postgres. Additive and idempotent.

DO $$
BEGIN
  IF current_user <> 'postgres' THEN
    RAISE EXCEPTION 'research forecast lineage migration must run as postgres';
  END IF;
  IF current_database() <> 'postgres' THEN
    RAISE EXCEPTION 'research forecast lineage migration must run in database postgres';
  END IF;
END $$;

CREATE SCHEMA IF NOT EXISTS research_settlement AUTHORIZATION postgres;
REVOKE ALL ON SCHEMA research_settlement FROM PUBLIC;
REVOKE ALL ON SCHEMA research_settlement FROM anon;
REVOKE ALL ON SCHEMA research_settlement FROM authenticated;
REVOKE ALL ON SCHEMA research_settlement FROM service_role;
GRANT USAGE ON SCHEMA research_settlement TO postgres;

CREATE TABLE IF NOT EXISTS research_settlement.research_forecast_lineage (
    forecast_payload_sha256 text PRIMARY KEY CHECK (
        forecast_payload_sha256 ~ '^[a-f0-9]{64}$'
    ),
    forecast_id text NOT NULL CHECK (forecast_id <> ''),
    condition_id text NOT NULL CHECK (condition_id <> ''),
    team_id text NOT NULL CHECK (team_id <> ''),
    config_version text NOT NULL CHECK (config_version <> ''),
    event_id text NULL,
    event_slug text NULL,
    market_end_at timestamptz NULL,
    event_lineage_state text NOT NULL CHECK (
        event_lineage_state IN (
            'verified', 'missing_event', 'ambiguous_events', 'malformed_event'
        )
    ),
    metadata_observed_at timestamptz NOT NULL,
    metadata_payload_sha256 text NOT NULL CHECK (
        metadata_payload_sha256 ~ '^[a-f0-9]{64}$'
    ),
    paper_only boolean NOT NULL DEFAULT true,
    report_only boolean NOT NULL DEFAULT true,
    readonly boolean NOT NULL DEFAULT true,
    inserted_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CHECK (
        (event_lineage_state = 'verified'
         AND event_id IS NOT NULL AND event_id <> ''
         AND event_slug IS NOT NULL AND event_slug <> ''
         AND market_end_at IS NOT NULL)
        OR
        (event_lineage_state <> 'verified'
         AND event_id IS NULL AND event_slug IS NULL AND market_end_at IS NULL)
    ),
    CHECK (paper_only IS true),
    CHECK (report_only IS true),
    CHECK (readonly IS true)
);

ALTER TABLE research_settlement.research_forecast_lineage OWNER TO postgres;
ALTER TABLE research_settlement.research_forecast_lineage ENABLE ROW LEVEL SECURITY;
CREATE INDEX IF NOT EXISTS idx_research_forecast_lineage_forecast_id
    ON research_settlement.research_forecast_lineage (forecast_id);
REVOKE ALL ON TABLE research_settlement.research_forecast_lineage FROM PUBLIC;
REVOKE ALL ON TABLE research_settlement.research_forecast_lineage FROM anon;
REVOKE ALL ON TABLE research_settlement.research_forecast_lineage FROM authenticated;
REVOKE ALL ON TABLE research_settlement.research_forecast_lineage FROM service_role;
GRANT ALL ON TABLE research_settlement.research_forecast_lineage TO postgres;
