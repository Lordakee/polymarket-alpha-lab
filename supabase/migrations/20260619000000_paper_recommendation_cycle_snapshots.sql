create table if not exists public.paper_recommendation_cycle_snapshots (
  snapshot_sha256 text primary key
    check (snapshot_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  final_status text not null
    check (final_status in ('pass', 'watch', 'blocked')),
  stage_counts jsonb not null default '{}'::jsonb
    check (jsonb_typeof(stage_counts) = 'object'),
  artifact_counts jsonb not null default '{}'::jsonb
    check (jsonb_typeof(artifact_counts) = 'object'),
  reason_codes jsonb not null default '[]'::jsonb
    check (jsonb_typeof(reason_codes) = 'array'),
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

create index if not exists idx_prcs_generated_at
  on public.paper_recommendation_cycle_snapshots (generated_at desc);

create index if not exists idx_prcs_final_status_generated_at
  on public.paper_recommendation_cycle_snapshots (final_status, generated_at desc);

create index if not exists idx_prcs_reason_codes_gin
  on public.paper_recommendation_cycle_snapshots using gin (reason_codes jsonb_path_ops);

create index if not exists idx_prcs_payload_gin
  on public.paper_recommendation_cycle_snapshots using gin (payload jsonb_path_ops);
