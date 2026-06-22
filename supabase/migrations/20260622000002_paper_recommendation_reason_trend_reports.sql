create table if not exists public.paper_recommendation_reason_trend_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  source_report_count integer not null
    check (source_report_count >= 0),
  reason_trend_rows jsonb not null default '[]'::jsonb
    check (jsonb_typeof(reason_trend_rows) = 'array'),
  transition_trend_rows jsonb not null default '[]'::jsonb
    check (jsonb_typeof(transition_trend_rows) = 'array'),
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

create index if not exists idx_prrtr_generated_at
  on public.paper_recommendation_reason_trend_reports (generated_at desc);

create index if not exists idx_prrtr_config_version_generated_at
  on public.paper_recommendation_reason_trend_reports (config_version, generated_at desc);

create index if not exists idx_prrtr_reason_trend_rows_gin
  on public.paper_recommendation_reason_trend_reports using gin (reason_trend_rows jsonb_path_ops);

create index if not exists idx_prrtr_transition_trend_rows_gin
  on public.paper_recommendation_reason_trend_reports using gin (transition_trend_rows jsonb_path_ops);

create index if not exists idx_prrtr_payload_gin
  on public.paper_recommendation_reason_trend_reports using gin (payload jsonb_path_ops);
