create table if not exists public.paper_recommendation_consistency_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  consistency_status text not null
    check (consistency_status in ('pass', 'watch', 'blocked')),
  reason_codes jsonb not null default '[]'::jsonb
    check (jsonb_typeof(reason_codes) = 'array'),
  group_count integer not null
    check (group_count >= 0),
  pass_count integer not null
    check (pass_count >= 0),
  watch_count integer not null
    check (watch_count >= 0),
  blocked_count integer not null
    check (blocked_count >= 0),
  max_edge_spread numeric not null
    check (max_edge_spread >= 0),
  max_score_spread numeric not null
    check (max_score_spread >= 0),
  min_source_count integer not null
    check (min_source_count > 0),
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

create index if not exists idx_prcr_generated_at
  on public.paper_recommendation_consistency_reports (generated_at desc);

create index if not exists idx_prcr_config_version_generated_at
  on public.paper_recommendation_consistency_reports (config_version, generated_at desc);

create index if not exists idx_prcr_consistency_status_generated_at
  on public.paper_recommendation_consistency_reports (consistency_status, generated_at desc);

create index if not exists idx_prcr_reason_codes_gin
  on public.paper_recommendation_consistency_reports using gin (reason_codes jsonb_path_ops);

create index if not exists idx_prcr_payload_gin
  on public.paper_recommendation_consistency_reports using gin (payload jsonb_path_ops);
