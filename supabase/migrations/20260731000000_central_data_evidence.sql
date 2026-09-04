-- Central data Node B: local evidence persistence schema
-- Idempotent migration for central_data_internal
-- Owner: postgres, database: postgres
-- Phase 1: paper_only=True, report_only=True, readonly=True

DO $$
BEGIN
  IF current_user <> 'postgres' THEN
    RAISE EXCEPTION 'central_data migration must run as postgres';
  END IF;
  IF current_database() <> 'postgres' THEN
    RAISE EXCEPTION 'central_data migration must run in database postgres';
  END IF;
END $$;

CREATE EXTENSION IF NOT EXISTS pg_cron;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_catalog.pg_extension WHERE extname = 'pg_cron'
  ) THEN
    RAISE EXCEPTION 'pg_cron extension required for central_data retention';
  END IF;
  IF current_setting('cron.database_name', true) IS DISTINCT FROM 'postgres' THEN
    RAISE EXCEPTION 'cron.database_name must be postgres for central_data retention';
  END IF;
END $$;

CREATE SCHEMA IF NOT EXISTS central_data_internal AUTHORIZATION postgres;

REVOKE ALL ON SCHEMA central_data_internal FROM PUBLIC;
REVOKE ALL ON SCHEMA central_data_internal FROM anon;
REVOKE ALL ON SCHEMA central_data_internal FROM authenticated;
REVOKE ALL ON SCHEMA central_data_internal FROM service_role;
GRANT USAGE ON SCHEMA central_data_internal TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA central_data_internal REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA central_data_internal REVOKE ALL ON TABLES FROM anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA central_data_internal REVOKE ALL ON TABLES FROM authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA central_data_internal REVOKE ALL ON TABLES FROM service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA central_data_internal REVOKE ALL ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA central_data_internal REVOKE ALL ON FUNCTIONS FROM anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA central_data_internal REVOKE ALL ON FUNCTIONS FROM authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA central_data_internal REVOKE ALL ON FUNCTIONS FROM service_role;

CREATE TABLE IF NOT EXISTS central_data_internal.central_data_raw_response_events (
    raw_event_id text PRIMARY KEY,
    source_id text NOT NULL,
    source_family text NOT NULL,
    endpoint_url text NOT NULL,
    official_source boolean NOT NULL,
    request_url text NOT NULL,
    final_url text NOT NULL,
    retrieval_time timestamptz NOT NULL,
    status_code integer NOT NULL,
    content_type text NOT NULL,
    safe_headers jsonb NOT NULL,
    failure_status text NOT NULL,
    raw_body bytea NOT NULL,
    body_length integer NOT NULL,
    raw_payload_sha256 text NOT NULL,
    expires_at timestamptz NOT NULL,
    paper_only boolean NOT NULL DEFAULT true,
    report_only boolean NOT NULL DEFAULT true,
    readonly boolean NOT NULL DEFAULT true,
    inserted_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CHECK (raw_event_id ~ '^[a-f0-9]{64}$'),
    CHECK (source_id <> ''),
    CHECK (source_family <> ''),
    CHECK (endpoint_url <> ''),
    CHECK (request_url <> ''),
    CHECK (final_url <> ''),
    CHECK (request_url = final_url),
    CHECK (request_url = endpoint_url),
    CHECK (status_code >= 100 AND status_code < 600),
    CHECK (content_type IN (
      'application/json', 'application/rss+xml', 'application/xml', 'text/xml'
    )),
    CHECK (jsonb_typeof(safe_headers) = 'object'),
    CHECK (failure_status IN (
      'none', 'network_error', 'resolver_error', 'connect_error', 'timeout',
      'stream_error', 'size_limit', 'redirect', 'http_error',
      'unsupported_content_type', 'unsupported_content_encoding',
      'invalid_request', 'unknown'
    )),
    CHECK (body_length = octet_length(raw_body)),
    CHECK (octet_length(raw_body) <= 2097152),
    CHECK (body_length >= 0 AND body_length <= 2097152),
    CHECK (raw_payload_sha256 ~ '^[a-f0-9]{64}$'),
    CHECK (raw_payload_sha256 = pg_catalog.encode(pg_catalog.sha256(raw_body), 'hex')),
    CHECK (expires_at - retrieval_time = interval '29 days'),
    CHECK (expires_at - retrieval_time <= interval '30 days'),
    CHECK (retrieval_time <= inserted_at),
    CHECK (paper_only IS true),
    CHECK (report_only IS true),
    CHECK (readonly IS true)
);

CREATE INDEX IF NOT EXISTS idx_central_data_raw_payload_sha256
  ON central_data_internal.central_data_raw_response_events (raw_payload_sha256);
CREATE INDEX IF NOT EXISTS idx_central_data_raw_expires_at
  ON central_data_internal.central_data_raw_response_events (expires_at, raw_event_id);
CREATE INDEX IF NOT EXISTS idx_central_data_raw_source_id
  ON central_data_internal.central_data_raw_response_events (source_id, retrieval_time DESC);

ALTER TABLE central_data_internal.central_data_raw_response_events OWNER TO postgres;
ALTER TABLE central_data_internal.central_data_raw_response_events ENABLE ROW LEVEL SECURITY;
-- No FORCE, no policies: trusted local postgres owner boundary

REVOKE ALL ON TABLE central_data_internal.central_data_raw_response_events FROM PUBLIC;
REVOKE ALL ON TABLE central_data_internal.central_data_raw_response_events FROM anon;
REVOKE ALL ON TABLE central_data_internal.central_data_raw_response_events FROM authenticated;
REVOKE ALL ON TABLE central_data_internal.central_data_raw_response_events FROM service_role;
GRANT ALL ON TABLE central_data_internal.central_data_raw_response_events TO postgres;

CREATE TABLE IF NOT EXISTS central_data_internal.central_data_normalized_observations (
    normalized_observation_id text PRIMARY KEY,
    raw_event_id text NOT NULL,
    source_id text NOT NULL,
    source_family text NOT NULL,
    endpoint_url text NOT NULL,
    official_source boolean NOT NULL,
    observation_time timestamptz NOT NULL,
    retrieval_time timestamptz NOT NULL,
    raw_payload_sha256 text NOT NULL,
    parser_version text NOT NULL,
    parse_state text NOT NULL,
    freshness_state text NOT NULL,
    failure_status text NOT NULL,
    value_state text NOT NULL,
    reason_codes jsonb NOT NULL,
    typed_value jsonb NOT NULL,
    paper_only boolean NOT NULL DEFAULT true,
    report_only boolean NOT NULL DEFAULT true,
    readonly boolean NOT NULL DEFAULT true,
    inserted_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CHECK (normalized_observation_id ~ '^[a-f0-9]{64}$'),
    CHECK (raw_event_id ~ '^[a-f0-9]{64}$'),
    CHECK (source_id <> ''),
    CHECK (source_family <> ''),
    CHECK (endpoint_url <> ''),
    CHECK (raw_payload_sha256 ~ '^[a-f0-9]{64}$'),
    CHECK (parser_version <> ''),
    CHECK (parse_state IN ('success', 'failed', 'unknown')),
    CHECK (freshness_state IN ('fresh', 'stale', 'unknown')),
    CHECK (failure_status IN (
      'none', 'network_error', 'resolver_error', 'connect_error', 'timeout',
      'stream_error', 'size_limit', 'redirect', 'http_error',
      'unsupported_content_type', 'unsupported_content_encoding',
      'invalid_request', 'unknown'
    )),
    CHECK (value_state IN ('present', 'null', 'zero', 'unknown')),
    CHECK (jsonb_typeof(reason_codes) = 'array'),
    CHECK (jsonb_typeof(typed_value) = 'object'),
    CHECK ((typed_value ->> 'type') IN ('null', 'bool', 'decimal', 'string', 'datetime', 'object', 'sequence')),
    CHECK (
      ((typed_value ->> 'type') = 'null'
       AND typed_value = '{"type":"null"}'::jsonb)
      OR ((typed_value ->> 'type') IN ('bool', 'decimal', 'string', 'datetime')
          AND typed_value ? 'value'
          AND (typed_value - 'type' - 'value') = '{}'::jsonb)
      OR ((typed_value ->> 'type') IN ('object', 'sequence')
          AND jsonb_typeof(typed_value -> 'items') = 'array'
          AND (typed_value - 'type' - 'items') = '{}'::jsonb)
    ),
    CHECK (paper_only IS true),
    CHECK (report_only IS true),
    CHECK (readonly IS true)
    -- No FK to raw events; no cascade
);

CREATE INDEX IF NOT EXISTS idx_central_data_norm_raw_event_id
  ON central_data_internal.central_data_normalized_observations (raw_event_id);
CREATE INDEX IF NOT EXISTS idx_central_data_norm_source_id
  ON central_data_internal.central_data_normalized_observations (source_id, observation_time DESC);
CREATE INDEX IF NOT EXISTS idx_central_data_norm_payload_sha
  ON central_data_internal.central_data_normalized_observations (raw_payload_sha256);

ALTER TABLE central_data_internal.central_data_normalized_observations OWNER TO postgres;
ALTER TABLE central_data_internal.central_data_normalized_observations ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE central_data_internal.central_data_normalized_observations FROM PUBLIC;
REVOKE ALL ON TABLE central_data_internal.central_data_normalized_observations FROM anon;
REVOKE ALL ON TABLE central_data_internal.central_data_normalized_observations FROM authenticated;
REVOKE ALL ON TABLE central_data_internal.central_data_normalized_observations FROM service_role;
GRANT ALL ON TABLE central_data_internal.central_data_normalized_observations TO postgres;

CREATE TABLE IF NOT EXISTS central_data_internal.central_data_raw_retention_audit (
    audit_id text PRIMARY KEY,
    audit_kind text NOT NULL,
    job_name text,
    cutoff_time timestamptz,
    run_started_at timestamptz,
    run_completed_at timestamptz,
    deleted_count integer,
    backlog_remaining boolean,
    run_status text,
    source_id text,
    source_family text,
    official_source boolean,
    raw_event_id text,
    raw_payload_sha256 text,
    original_body_length integer,
    expires_at timestamptz,
    deleted_at timestamptz,
    reason_code text,
    paper_only boolean NOT NULL DEFAULT true,
    report_only boolean NOT NULL DEFAULT true,
    readonly boolean NOT NULL DEFAULT true,
    inserted_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CHECK (audit_id ~ '^[a-f0-9]{64}$'),
    CHECK (audit_kind IN ('purge_run', 'raw_delete')),
    CHECK (source_id IS NULL OR source_id <> ''),
    CHECK (source_family IS NULL OR source_family <> ''),
    CHECK (raw_event_id IS NULL OR raw_event_id ~ '^[a-f0-9]{64}$'),
    CHECK (raw_payload_sha256 IS NULL OR raw_payload_sha256 ~ '^[a-f0-9]{64}$'),
    CHECK (original_body_length IS NULL OR original_body_length BETWEEN 0 AND 2097152),
    CHECK (
      (audit_kind = 'purge_run' AND job_name IS NOT NULL AND cutoff_time IS NOT NULL
       AND run_started_at IS NOT NULL AND run_completed_at IS NOT NULL
       AND deleted_count IS NOT NULL AND deleted_count >= 0
       AND backlog_remaining IS NOT NULL
       AND run_status IN ('ok', 'backlog')
       AND run_completed_at >= run_started_at
       AND source_id IS NULL AND source_family IS NULL AND official_source IS NULL
       AND raw_event_id IS NULL AND raw_payload_sha256 IS NULL
       AND original_body_length IS NULL AND expires_at IS NULL
       AND deleted_at IS NULL AND reason_code IS NULL)
      OR
      (audit_kind = 'raw_delete' AND source_id IS NOT NULL AND source_family IS NOT NULL
       AND official_source IS NOT NULL AND raw_event_id IS NOT NULL
       AND raw_payload_sha256 IS NOT NULL AND original_body_length IS NOT NULL
       AND expires_at IS NOT NULL AND deleted_at IS NOT NULL AND reason_code IS NOT NULL
       AND job_name IS NULL AND cutoff_time IS NULL AND run_started_at IS NULL
       AND run_completed_at IS NULL AND deleted_count IS NULL
       AND backlog_remaining IS NULL AND run_status IS NULL)
    ),
    CHECK (paper_only IS true),
    CHECK (report_only IS true),
    CHECK (readonly IS true)
    -- No FK to raw; no cascade; never stores body/URL/headers
);

CREATE INDEX IF NOT EXISTS idx_central_data_retention_audit_kind
  ON central_data_internal.central_data_raw_retention_audit (audit_kind, inserted_at DESC);
CREATE INDEX IF NOT EXISTS idx_central_data_retention_run_status
  ON central_data_internal.central_data_raw_retention_audit (run_status, run_completed_at DESC)
  WHERE audit_kind = 'purge_run';

ALTER TABLE central_data_internal.central_data_raw_retention_audit OWNER TO postgres;
ALTER TABLE central_data_internal.central_data_raw_retention_audit ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE central_data_internal.central_data_raw_retention_audit FROM PUBLIC;
REVOKE ALL ON TABLE central_data_internal.central_data_raw_retention_audit FROM anon;
REVOKE ALL ON TABLE central_data_internal.central_data_raw_retention_audit FROM authenticated;
REVOKE ALL ON TABLE central_data_internal.central_data_raw_retention_audit FROM service_role;
GRANT ALL ON TABLE central_data_internal.central_data_raw_retention_audit TO postgres;

-- Purge function: SECURITY INVOKER, fully qualified, owner-only
CREATE OR REPLACE FUNCTION central_data_internal.purge_expired_central_data_raw_response_events(
    cutoff timestamptz DEFAULT statement_timestamp(),
    batch_limit integer DEFAULT 500
)
RETURNS integer
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog
AS $$
DECLARE
    v_started timestamptz := statement_timestamp();
    v_deleted integer := 0;
    v_backlog boolean := false;
    v_run_id text;
    v_row record;
    v_delete_id text;
BEGIN
    IF current_user <> 'postgres' THEN
        RAISE EXCEPTION 'central_data purge requires postgres owner';
    END IF;
    IF cutoff IS NULL THEN
        RAISE EXCEPTION 'central_data purge cutoff is required';
    END IF;
    IF batch_limit IS NULL OR batch_limit < 1 OR batch_limit > 5000 THEN
        RAISE EXCEPTION 'central_data purge batch_limit out of bounds';
    END IF;

    FOR v_row IN
        SELECT raw_event_id, source_id, source_family, official_source,
               raw_payload_sha256, body_length, expires_at
        FROM central_data_internal.central_data_raw_response_events
        WHERE expires_at <= cutoff
        ORDER BY expires_at ASC, raw_event_id ASC
        LIMIT batch_limit
        FOR UPDATE SKIP LOCKED
    LOOP
        v_delete_id := pg_catalog.encode(
            pg_catalog.sha256(
                convert_to(
                    'raw_delete|' || v_row.raw_event_id || '|' ||
                    coalesce(v_row.raw_payload_sha256, '') || '|' ||
                    extract(epoch FROM v_row.expires_at)::text,
                    'UTF8'
                )
            ),
            'hex'
        );
        INSERT INTO central_data_internal.central_data_raw_retention_audit (
            audit_id, audit_kind, source_id, source_family, official_source,
            raw_event_id, raw_payload_sha256, original_body_length,
            expires_at, deleted_at, reason_code,
            paper_only, report_only, readonly
        ) VALUES (
            v_delete_id, 'raw_delete', v_row.source_id, v_row.source_family,
            v_row.official_source, v_row.raw_event_id, v_row.raw_payload_sha256,
            v_row.body_length, v_row.expires_at, statement_timestamp(),
            'expired_retention', true, true, true
        )
        ON CONFLICT (audit_id) DO NOTHING;

        DELETE FROM central_data_internal.central_data_raw_response_events
        WHERE raw_event_id = v_row.raw_event_id;

        v_deleted := v_deleted + 1;
    END LOOP;

    SELECT EXISTS (
        SELECT 1 FROM central_data_internal.central_data_raw_response_events
        WHERE expires_at <= cutoff
    ) INTO v_backlog;

    v_run_id := pg_catalog.encode(
        pg_catalog.sha256(
            convert_to(
                'purge_run|central_data_raw_retention_15m|' ||
                cutoff::text || '|' || v_started::text || '|' ||
                statement_timestamp()::text || '|' ||
                CASE WHEN v_backlog THEN 'backlog' ELSE 'ok' END || '|' ||
                v_deleted::text,
                'UTF8'
            )
        ),
        'hex'
    );

    INSERT INTO central_data_internal.central_data_raw_retention_audit (
        audit_id, audit_kind, job_name, cutoff_time, run_started_at,
        run_completed_at, deleted_count, backlog_remaining, run_status,
        paper_only, report_only, readonly
    ) VALUES (
        v_run_id, 'purge_run', 'central_data_raw_retention_15m', cutoff,
        v_started, statement_timestamp(), v_deleted, v_backlog,
        CASE WHEN v_backlog THEN 'backlog' ELSE 'ok' END,
        true, true, true
    )
    ON CONFLICT (audit_id) DO NOTHING;

    RETURN v_deleted;
END;
$$;

ALTER FUNCTION central_data_internal.purge_expired_central_data_raw_response_events(timestamptz, integer) OWNER TO postgres;
REVOKE ALL ON FUNCTION central_data_internal.purge_expired_central_data_raw_response_events(timestamptz, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION central_data_internal.purge_expired_central_data_raw_response_events(timestamptz, integer) FROM anon;
REVOKE ALL ON FUNCTION central_data_internal.purge_expired_central_data_raw_response_events(timestamptz, integer) FROM authenticated;
REVOKE ALL ON FUNCTION central_data_internal.purge_expired_central_data_raw_response_events(timestamptz, integer) FROM service_role;
GRANT EXECUTE ON FUNCTION central_data_internal.purge_expired_central_data_raw_response_events(timestamptz, integer) TO postgres;

-- Idempotent cron job registration via schedule_in_database
DO $$
DECLARE
    v_count integer;
BEGIN
    -- pg_cron 1.6.4 updates the uniquely named job on reapplication.
    PERFORM cron.schedule_in_database(
        'central_data_raw_retention_15m',
        '*/15 * * * *',
        'select central_data_internal.purge_expired_central_data_raw_response_events();',
        'postgres',
        'postgres'
    );

    SELECT count(*) INTO v_count
    FROM cron.job
    WHERE jobname = 'central_data_raw_retention_15m'
      AND schedule = '*/15 * * * *'
      AND command = 'select central_data_internal.purge_expired_central_data_raw_response_events();'
      AND database = 'postgres'
      AND username = 'postgres'
      AND active = true;

    IF v_count <> 1 THEN
        RAISE EXCEPTION 'central_data retention job must exist exactly once with pinned contract';
    END IF;
END $$;

-- Seed only when no recent healthy run exists; migration re-application is
-- therefore idempotent with respect to retention audit metadata.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM central_data_internal.central_data_raw_retention_audit
         WHERE audit_kind = 'purge_run'
           AND job_name = 'central_data_raw_retention_15m'
           AND run_status = 'ok'
           AND backlog_remaining IS FALSE
           AND run_completed_at >= statement_timestamp() - interval '1 hour'
    ) THEN
        PERFORM central_data_internal.purge_expired_central_data_raw_response_events();
    END IF;
END $$;
