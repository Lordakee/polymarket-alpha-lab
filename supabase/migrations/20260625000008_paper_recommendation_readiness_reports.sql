create table if not exists public.paper_recommendation_readiness_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  input_count integer not null
    check (input_count >= 0),
  row_count integer not null
    check (row_count >= 0),
  ready_count integer not null
    check (ready_count >= 0),
  watch_count integer not null
    check (watch_count >= 0),
  blocked_count integer not null
    check (blocked_count >= 0),
  top_adjusted_net_probability_edge numeric not null,
  total_cost_per_share numeric not null
    check (total_cost_per_share >= 0),
  readiness_status_counts jsonb not null default '{}'::jsonb
    check (jsonb_typeof(readiness_status_counts) = 'object'),
  payload jsonb not null
    check (jsonb_typeof(payload) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (row_count = ready_count + watch_count + blocked_count),
  check (input_count >= row_count)
);

create index if not exists idx_prrr_generated_at
  on public.paper_recommendation_readiness_reports (generated_at desc);

create index if not exists idx_prrr_config_version_generated_at
  on public.paper_recommendation_readiness_reports (config_version, generated_at desc);

create index if not exists idx_prrr_blocked_count_generated_at
  on public.paper_recommendation_readiness_reports (blocked_count, generated_at desc);

create index if not exists idx_prrr_readiness_status_counts_gin
  on public.paper_recommendation_readiness_reports using gin (readiness_status_counts jsonb_path_ops);

create index if not exists idx_prrr_payload_gin
  on public.paper_recommendation_readiness_reports using gin (payload jsonb_path_ops);
