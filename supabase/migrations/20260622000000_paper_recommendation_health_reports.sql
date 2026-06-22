create table if not exists public.paper_recommendation_health_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  health_status text not null
    check (health_status in ('pass', 'watch', 'blocked')),
  row_count integer not null
    check (row_count >= 0),
  recommend_count integer not null
    check (recommend_count >= 0),
  watch_count integer not null
    check (watch_count >= 0),
  reject_count integer not null
    check (reject_count >= 0),
  average_net_probability_edge numeric not null,
  average_total_cost_per_share numeric not null
    check (average_total_cost_per_share >= 0),
  top_recommendation_score numeric not null
    check (top_recommendation_score >= 0),
  reason_code_counts jsonb not null default '[]'::jsonb
    check (jsonb_typeof(reason_code_counts) = 'array'),
  max_average_cost_per_share numeric not null
    check (max_average_cost_per_share >= 0),
  min_recommend_share numeric not null
    check (min_recommend_share >= 0 and min_recommend_share <= 1),
  payload jsonb not null
    check (jsonb_typeof(payload) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (row_count = recommend_count + watch_count + reject_count)
);

create index if not exists idx_prhr_generated_at
  on public.paper_recommendation_health_reports (generated_at desc);

create index if not exists idx_prhr_config_version_generated_at
  on public.paper_recommendation_health_reports (config_version, generated_at desc);

create index if not exists idx_prhr_health_status_generated_at
  on public.paper_recommendation_health_reports (health_status, generated_at desc);

create index if not exists idx_prhr_reason_code_counts_gin
  on public.paper_recommendation_health_reports using gin (reason_code_counts jsonb_path_ops);

create index if not exists idx_prhr_payload_gin
  on public.paper_recommendation_health_reports using gin (payload jsonb_path_ops);
