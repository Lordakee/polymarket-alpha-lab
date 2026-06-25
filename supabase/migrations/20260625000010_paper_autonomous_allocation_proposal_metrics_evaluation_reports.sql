create table if not exists public.paper_autonomous_allocation_proposal_metrics_evaluation_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  evaluation_status text not null
    check (evaluation_status in ('pass', 'watch', 'blocked')),
  recommended_next_step text not null,
  source_report_count integer not null
    check (source_report_count >= 0),
  latest_report_generated_at timestamptz,
  reason_code_counts jsonb not null default '{}'::jsonb
    check (jsonb_typeof(reason_code_counts) = 'object'),
  reason_codes jsonb not null default '[]'::jsonb
    check (jsonb_typeof(reason_codes) = 'array'),
  diagnostics jsonb not null
    check (jsonb_typeof(diagnostics) = 'object'),
  payload jsonb not null
    check (jsonb_typeof(payload) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now()
);

create index if not exists idx_paapmer_generated_at
  on public.paper_autonomous_allocation_proposal_metrics_evaluation_reports (generated_at desc);

create index if not exists idx_paapmer_status_generated_at
  on public.paper_autonomous_allocation_proposal_metrics_evaluation_reports (evaluation_status, generated_at desc);

create index if not exists idx_paapmer_config_generated_at
  on public.paper_autonomous_allocation_proposal_metrics_evaluation_reports (config_version, generated_at desc);

create index if not exists idx_paapmer_reason_codes_gin
  on public.paper_autonomous_allocation_proposal_metrics_evaluation_reports using gin (reason_codes jsonb_path_ops);

create index if not exists idx_paapmer_payload_gin
  on public.paper_autonomous_allocation_proposal_metrics_evaluation_reports using gin (payload jsonb_path_ops);
