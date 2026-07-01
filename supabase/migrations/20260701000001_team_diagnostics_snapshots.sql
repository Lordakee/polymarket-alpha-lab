CREATE TABLE IF NOT EXISTS public.team_diagnostics_snapshots (
    report_sha256 text PRIMARY KEY,
    generated_at timestamptz NOT NULL,
    config_version text NOT NULL,
    source_config_version text NOT NULL,
    team_id text NULL,
    market_slug text NULL,
    forecast_id text NULL,
    forecast_row_count integer NOT NULL,
    evidence_row_count integer NOT NULL,
    outcome_row_count integer NOT NULL,
    memory_eligible_reference_count integer NOT NULL,
    calibration_status text NOT NULL,
    calibration_settled_count integer NOT NULL,
    calibration_group_count integer NOT NULL,
    event_template_status text NOT NULL,
    event_template_row_count integer NOT NULL,
    source_reliability_row_count integer NOT NULL,
    source_reliability_missing_source_evidence_count integer NOT NULL,
    evidence_quality_status text NOT NULL,
    evidence_quality_pass_count integer NOT NULL,
    evidence_quality_watch_count integer NOT NULL,
    evidence_quality_blocked_count integer NOT NULL,
    evidence_quality_average_quality_score numeric NOT NULL,
    reason_codes_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    payload_json jsonb NOT NULL,
    paper_only boolean NOT NULL DEFAULT true,
    report_only boolean NOT NULL DEFAULT true,
    readonly boolean NOT NULL DEFAULT true,
    inserted_at timestamptz NOT NULL DEFAULT now(),
    CHECK (report_sha256 ~ '^[a-f0-9]{64}$'),
    CHECK (config_version <> ''),
    CHECK (source_config_version <> ''),
    CHECK (team_id IS NULL OR team_id <> ''),
    CHECK (market_slug IS NULL OR market_slug <> ''),
    CHECK (forecast_id IS NULL OR forecast_id <> ''),
    CHECK (forecast_row_count >= 0),
    CHECK (evidence_row_count >= 0),
    CHECK (outcome_row_count >= 0),
    CHECK (memory_eligible_reference_count >= 0),
    CHECK (calibration_status <> ''),
    CHECK (calibration_settled_count >= 0),
    CHECK (calibration_group_count >= 0),
    CHECK (event_template_status <> ''),
    CHECK (event_template_row_count >= 0),
    CHECK (source_reliability_row_count >= 0),
    CHECK (source_reliability_missing_source_evidence_count >= 0),
    CHECK (evidence_quality_status IN ('evidence_quality_pass', 'evidence_quality_watch', 'evidence_quality_blocked')),
    CHECK (evidence_quality_pass_count >= 0),
    CHECK (evidence_quality_watch_count >= 0),
    CHECK (evidence_quality_blocked_count >= 0),
    CHECK (evidence_quality_average_quality_score >= 0 AND evidence_quality_average_quality_score <= 1),
    CHECK (jsonb_typeof(reason_codes_json) = 'array'),
    CHECK (jsonb_typeof(payload_json) = 'object'),
    CHECK ((payload_json ->> 'paper_only') = 'true'),
    CHECK ((payload_json ->> 'report_only') = 'true'),
    CHECK ((payload_json ->> 'readonly') = 'true'),
    CHECK (paper_only IS true),
    CHECK (report_only IS true),
    CHECK (readonly IS true)
);

CREATE INDEX IF NOT EXISTS idx_tds_generated_at
    ON public.team_diagnostics_snapshots
    (generated_at DESC, inserted_at DESC, report_sha256 DESC);

CREATE INDEX IF NOT EXISTS idx_tds_team_market_history
    ON public.team_diagnostics_snapshots
    (team_id, market_slug, generated_at DESC, inserted_at DESC, report_sha256 DESC);

CREATE INDEX IF NOT EXISTS idx_tds_forecast_history
    ON public.team_diagnostics_snapshots
    (forecast_id, generated_at DESC, inserted_at DESC, report_sha256 DESC);

CREATE INDEX IF NOT EXISTS idx_tds_config_version_history
    ON public.team_diagnostics_snapshots
    (config_version, generated_at DESC, inserted_at DESC, report_sha256 DESC);

CREATE INDEX IF NOT EXISTS idx_tds_reason_codes_gin
    ON public.team_diagnostics_snapshots USING gin
    (reason_codes_json jsonb_path_ops);

CREATE INDEX IF NOT EXISTS idx_tds_payload_gin
    ON public.team_diagnostics_snapshots USING gin
    (payload_json jsonb_path_ops);
