-- P2a correction: bind lineage to immutable forecast snapshot payloads.
-- Owner: postgres, database: postgres. Idempotent after successful application.

DO $$
BEGIN
  IF current_user <> 'postgres' THEN
    RAISE EXCEPTION 'research forecast lineage identity migration must run as postgres';
  END IF;
  IF current_database() <> 'postgres' THEN
    RAISE EXCEPTION 'research forecast lineage identity migration must run in database postgres';
  END IF;
END $$;

ALTER TABLE research_settlement.research_forecast_lineage
    ADD COLUMN IF NOT EXISTS forecast_payload_sha256 text;

DO $$
DECLARE
  v_primary_key_name text;
BEGIN
  IF EXISTS (
      SELECT 1
      FROM research_settlement.research_forecast_lineage
      WHERE forecast_payload_sha256 IS NULL
  ) THEN
    RAISE EXCEPTION 'existing lineage rows require audited forecast snapshot binding';
  END IF;

  SELECT constraint_name
    INTO v_primary_key_name
    FROM information_schema.table_constraints
   WHERE table_schema = 'research_settlement'
     AND table_name = 'research_forecast_lineage'
     AND constraint_type = 'PRIMARY KEY';

  IF v_primary_key_name IS NOT NULL
     AND v_primary_key_name <> 'research_forecast_lineage_pkey' THEN
    RAISE EXCEPTION 'unexpected lineage primary key constraint';
  END IF;

  IF v_primary_key_name IS NOT NULL
     AND EXISTS (
       SELECT 1
       FROM information_schema.constraint_column_usage
       WHERE table_schema = 'research_settlement'
         AND table_name = 'research_forecast_lineage'
         AND constraint_name = v_primary_key_name
         AND column_name = 'forecast_id'
     ) THEN
    ALTER TABLE research_settlement.research_forecast_lineage
        DROP CONSTRAINT research_forecast_lineage_pkey;
  END IF;
END $$;

ALTER TABLE research_settlement.research_forecast_lineage
    ALTER COLUMN forecast_payload_sha256 SET NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (
      SELECT 1
      FROM information_schema.table_constraints tc
      JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_catalog = tc.constraint_catalog
       AND ccu.constraint_schema = tc.constraint_schema
       AND ccu.constraint_name = tc.constraint_name
      WHERE tc.table_schema = 'research_settlement'
        AND tc.table_name = 'research_forecast_lineage'
        AND tc.constraint_type = 'PRIMARY KEY'
        AND ccu.column_name = 'forecast_payload_sha256'
  ) THEN
    ALTER TABLE research_settlement.research_forecast_lineage
        ADD CONSTRAINT research_forecast_lineage_pkey
        PRIMARY KEY (forecast_payload_sha256);
  END IF;
END $$;

ALTER TABLE research_settlement.research_forecast_lineage
    DROP CONSTRAINT IF EXISTS research_forecast_lineage_forecast_payload_sha256_check;
ALTER TABLE research_settlement.research_forecast_lineage
    ADD CONSTRAINT research_forecast_lineage_forecast_payload_sha256_check
    CHECK (forecast_payload_sha256 ~ '^[a-f0-9]{64}$');

CREATE INDEX IF NOT EXISTS idx_research_forecast_lineage_forecast_id
    ON research_settlement.research_forecast_lineage (forecast_id);
