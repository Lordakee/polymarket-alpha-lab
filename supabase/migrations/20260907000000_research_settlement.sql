-- P1: auditable settled outcomes for the research forecast universe.
-- Owner: postgres, database: postgres. Idempotent migration.
-- Corrections are additive rows keyed by (condition_id, observed_at);
-- "current" is the latest observed_at per condition.

DO $$
BEGIN
  IF current_user <> 'postgres' THEN
    RAISE EXCEPTION 'research_settlement migration must run as postgres';
  END IF;
  IF current_database() <> 'postgres' THEN
    RAISE EXCEPTION 'research_settlement migration must run in database postgres';
  END IF;
END $$;

CREATE SCHEMA IF NOT EXISTS research_settlement AUTHORIZATION postgres;
REVOKE ALL ON SCHEMA research_settlement FROM PUBLIC;
REVOKE ALL ON SCHEMA research_settlement FROM anon;
REVOKE ALL ON SCHEMA research_settlement FROM authenticated;
REVOKE ALL ON SCHEMA research_settlement FROM service_role;
GRANT USAGE ON SCHEMA research_settlement TO postgres;

CREATE TABLE IF NOT EXISTS research_settlement.research_settled_outcomes (
    condition_id text NOT NULL,
    observed_at timestamptz NOT NULL,
    outcome text NOT NULL CHECK (outcome IN ('yes', 'no')),
    resolution_source text NOT NULL CHECK (resolution_source <> ''),
    outcome_prices_snapshot jsonb NOT NULL CHECK (jsonb_typeof(outcome_prices_snapshot) = 'array'),
    payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[a-f0-9]{64}$'),
    dispute_flag boolean NOT NULL DEFAULT false,
    paper_only boolean NOT NULL DEFAULT true,
    report_only boolean NOT NULL DEFAULT true,
    readonly boolean NOT NULL DEFAULT true,
    inserted_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    PRIMARY KEY (condition_id, observed_at),
    CHECK (paper_only IS true),
    CHECK (report_only IS true),
    CHECK (readonly IS true)
);

ALTER TABLE research_settlement.research_settled_outcomes OWNER TO postgres;
ALTER TABLE research_settlement.research_settled_outcomes ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE research_settlement.research_settled_outcomes FROM PUBLIC;
REVOKE ALL ON TABLE research_settlement.research_settled_outcomes FROM anon;
REVOKE ALL ON TABLE research_settlement.research_settled_outcomes FROM authenticated;
REVOKE ALL ON TABLE research_settlement.research_settled_outcomes FROM service_role;
GRANT ALL ON TABLE research_settlement.research_settled_outcomes TO postgres;
