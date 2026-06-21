create table if not exists public.paper_probability_recommendation_queue_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  source_config_version text not null,
  input_count integer not null
    check (input_count >= 0),
  queue_count integer not null
    check (queue_count >= 0),
  research_review_count integer not null
    check (research_review_count >= 0),
  await_fresh_context_count integer not null
    check (await_fresh_context_count >= 0),
  skip_count integer not null
    check (skip_count >= 0),
  excluded_count integer not null
    check (excluded_count >= 0),
  reason_code_counts jsonb not null default '{}'::jsonb
    check (jsonb_typeof(reason_code_counts) = 'object'),
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

create index if not exists idx_ppqr_generated_at
  on public.paper_probability_recommendation_queue_reports (generated_at desc);

create index if not exists idx_ppqr_source_config_version_generated_at
  on public.paper_probability_recommendation_queue_reports (source_config_version, generated_at desc);

create index if not exists idx_ppqr_reason_code_counts_gin
  on public.paper_probability_recommendation_queue_reports using gin (reason_code_counts jsonb_path_ops);

create index if not exists idx_ppqr_payload_gin
  on public.paper_probability_recommendation_queue_reports using gin (payload jsonb_path_ops);
