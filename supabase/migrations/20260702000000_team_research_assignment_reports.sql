create table if not exists public.team_research_assignment_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  source_queue_config_version text not null,
  source_route_config_version text not null,
  source_memory_config_version text not null,
  assignment_status text not null
    check (assignment_status in ('ready', 'watch', 'blocked')),
  assignment_count integer not null
    check (assignment_count >= 0),
  assigned_count integer not null
    check (assigned_count >= 0),
  watch_count integer not null
    check (watch_count >= 0),
  blocked_count integer not null
    check (blocked_count >= 0),
  reason_codes_json jsonb not null default '[]'::jsonb
    check (jsonb_typeof(reason_codes_json) = 'array'),
  payload_json jsonb not null
    check (jsonb_typeof(payload_json) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (((payload_json ->> 'generated_at')::timestamptz = generated_at) is true),
  check ((payload_json ->> 'config_version' = config_version) is true),
  check ((payload_json ->> 'source_queue_config_version' = source_queue_config_version) is true),
  check ((payload_json ->> 'source_route_config_version' = source_route_config_version) is true),
  check ((payload_json ->> 'source_memory_config_version' = source_memory_config_version) is true),
  check ((payload_json ->> 'assignment_status' = assignment_status) is true),
  check (((payload_json ->> 'assignment_count')::integer = assignment_count) is true),
  check (((payload_json ->> 'assigned_count')::integer = assigned_count) is true),
  check (((payload_json ->> 'watch_count')::integer = watch_count) is true),
  check (((payload_json ->> 'blocked_count')::integer = blocked_count) is true),
  check ((payload_json -> 'reason_codes' = reason_codes_json) is true),
  check ((payload_json ->> 'paper_only' = 'true') is true),
  check ((payload_json ->> 'report_only' = 'true') is true),
  check ((payload_json ->> 'readonly' = 'true') is true),
  check (assigned_count + watch_count + blocked_count = assignment_count)
);

create index if not exists idx_trar_generated_at
  on public.team_research_assignment_reports (generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists idx_trar_assignment_status_generated_at
  on public.team_research_assignment_reports (assignment_status, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists idx_trar_config_version_generated_at
  on public.team_research_assignment_reports (config_version, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists idx_trar_reason_codes_json_gin
  on public.team_research_assignment_reports using gin (reason_codes_json jsonb_path_ops);

create index if not exists idx_trar_payload_json_gin
  on public.team_research_assignment_reports using gin (payload_json jsonb_path_ops);

alter table public.team_research_assignment_reports enable row level security;

comment on table public.team_research_assignment_reports is
  'Local Supabase/Postgres Phase 1 read-only team research assignment reports.';
