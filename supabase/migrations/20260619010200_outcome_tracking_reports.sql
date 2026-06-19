create table if not exists public.outcome_tracking_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  total_markets_checked integer not null
    check (total_markets_checked >= 0),
  resolved_count integer not null
    check (resolved_count >= 0),
  pending_count integer not null
    check (pending_count >= 0),
  observation_count integer not null
    check (observation_count >= 0),
  forecast_evidence_status text
    check (forecast_evidence_status is null or forecast_evidence_status in ('incomplete_data', 'insufficient_evidence', 'blocked_by_quality', 'paper_review_ready')),
  payload jsonb not null
    check (jsonb_typeof(payload) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  inserted_at timestamptz not null default now(),
  check (resolved_count + pending_count = total_markets_checked),
  check (observation_count = resolved_count)
);

create index if not exists idx_otr_generated_at
  on public.outcome_tracking_reports (generated_at desc);

create index if not exists idx_otr_config_version_generated_at
  on public.outcome_tracking_reports (config_version, generated_at desc);

create index if not exists idx_otr_forecast_evidence_status_generated_at
  on public.outcome_tracking_reports (forecast_evidence_status, generated_at desc);

create index if not exists idx_otr_payload_gin
  on public.outcome_tracking_reports using gin (payload jsonb_path_ops);
