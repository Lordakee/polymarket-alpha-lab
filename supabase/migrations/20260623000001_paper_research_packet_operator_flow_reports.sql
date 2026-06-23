create table if not exists public.paper_research_packet_operator_flow_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  flow_status text not null
    check (flow_status in ('pass', 'watch', 'blocked')),
  packet_generated_at timestamptz not null,
  packet_config_version text not null,
  packet_persisted boolean not null,
  packet_row_count integer not null
    check (packet_row_count >= 0),
  included_count integer not null
    check (included_count >= 0),
  skipped_count integer not null
    check (skipped_count >= 0),
  quality_generated_at timestamptz not null,
  quality_config_version text not null,
  quality_status text not null
    check (quality_status in ('pass', 'watch', 'blocked')),
  quality_persisted boolean not null,
  quality_check_count integer not null
    check (quality_check_count >= 0),
  quality_pass_count integer not null
    check (quality_pass_count >= 0),
  quality_watch_count integer not null
    check (quality_watch_count >= 0),
  quality_blocked_count integer not null
    check (quality_blocked_count >= 0),
  history_generated_at timestamptz not null,
  history_config_version text not null,
  history_status text not null
    check (history_status in ('pass', 'watch', 'blocked')),
  history_source_report_count integer not null
    check (history_source_report_count >= 0),
  history_latest_quality_status text not null
    check (history_latest_quality_status in ('pass', 'watch', 'blocked')),
  reason_codes_json jsonb not null default '[]'::jsonb
    check (jsonb_typeof(reason_codes_json) = 'array'),
  reason_code_count integer not null
    check (reason_code_count >= 0),
  payload_json jsonb not null
    check (jsonb_typeof(payload_json) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (packet_row_count = included_count + skipped_count),
  check (history_source_report_count > 0),
  check (quality_check_count = quality_pass_count + quality_watch_count + quality_blocked_count),
  check (history_latest_quality_status = quality_status),
  check (packet_generated_at <= quality_generated_at),
  check (quality_generated_at <= history_generated_at),
  check (history_generated_at <= generated_at),
  check (reason_code_count = jsonb_array_length(reason_codes_json)),
  check (
    (
      quality_status = 'blocked'
      and quality_blocked_count > 0
    )
    or (
      quality_status = 'watch'
      and quality_blocked_count = 0
      and quality_watch_count > 0
    )
    or (
      quality_status = 'pass'
      and quality_blocked_count = 0
      and quality_watch_count = 0
    )
  ),
  check (
    (
      flow_status = 'blocked'
      and (
        packet_persisted is false
        or quality_persisted is false
        or quality_status = 'blocked'
        or history_status = 'blocked'
      )
    )
    or (
      flow_status = 'watch'
      and packet_persisted is true
      and quality_persisted is true
      and quality_status <> 'blocked'
      and history_status <> 'blocked'
      and (
        quality_status = 'watch'
        or history_status = 'watch'
      )
    )
    or (
      flow_status = 'pass'
      and packet_persisted is true
      and quality_persisted is true
      and quality_status = 'pass'
      and history_status = 'pass'
    )
  ),
  check (((payload_json -> 'paper_only') = 'true'::jsonb) is true),
  check (((payload_json -> 'report_only') = 'true'::jsonb) is true),
  check (((payload_json -> 'readonly') = 'true'::jsonb) is true),
  check (
    payload_json ? 'generated_at'
    and jsonb_typeof(payload_json -> 'generated_at') = 'string'
    and (payload_json ->> 'generated_at')::timestamptz = generated_at
  ),
  check (
    payload_json ? 'config_version'
    and jsonb_typeof(payload_json -> 'config_version') = 'string'
    and payload_json ->> 'config_version' = config_version
  ),
  check (
    payload_json ? 'flow_status'
    and jsonb_typeof(payload_json -> 'flow_status') = 'string'
    and payload_json ->> 'flow_status' = flow_status
  ),
  check (
    payload_json ? 'packet_generated_at'
    and jsonb_typeof(payload_json -> 'packet_generated_at') = 'string'
    and (payload_json ->> 'packet_generated_at')::timestamptz = packet_generated_at
  ),
  check (
    payload_json ? 'packet_config_version'
    and jsonb_typeof(payload_json -> 'packet_config_version') = 'string'
    and payload_json ->> 'packet_config_version' = packet_config_version
  ),
  check (((payload_json -> 'packet_persisted') = to_jsonb(packet_persisted)) is true),
  check (((payload_json -> 'packet_row_count') = to_jsonb(packet_row_count)) is true),
  check (((payload_json -> 'included_count') = to_jsonb(included_count)) is true),
  check (((payload_json -> 'skipped_count') = to_jsonb(skipped_count)) is true),
  check (
    payload_json ? 'quality_generated_at'
    and jsonb_typeof(payload_json -> 'quality_generated_at') = 'string'
    and (payload_json ->> 'quality_generated_at')::timestamptz = quality_generated_at
  ),
  check (
    payload_json ? 'quality_config_version'
    and jsonb_typeof(payload_json -> 'quality_config_version') = 'string'
    and payload_json ->> 'quality_config_version' = quality_config_version
  ),
  check (
    payload_json ? 'quality_status'
    and jsonb_typeof(payload_json -> 'quality_status') = 'string'
    and payload_json ->> 'quality_status' = quality_status
  ),
  check (((payload_json -> 'quality_persisted') = to_jsonb(quality_persisted)) is true),
  check (((payload_json -> 'quality_check_count') = to_jsonb(quality_check_count)) is true),
  check (((payload_json -> 'quality_pass_count') = to_jsonb(quality_pass_count)) is true),
  check (((payload_json -> 'quality_watch_count') = to_jsonb(quality_watch_count)) is true),
  check (((payload_json -> 'quality_blocked_count') = to_jsonb(quality_blocked_count)) is true),
  check (
    payload_json ? 'history_generated_at'
    and jsonb_typeof(payload_json -> 'history_generated_at') = 'string'
    and (payload_json ->> 'history_generated_at')::timestamptz = history_generated_at
  ),
  check (
    payload_json ? 'history_config_version'
    and jsonb_typeof(payload_json -> 'history_config_version') = 'string'
    and payload_json ->> 'history_config_version' = history_config_version
  ),
  check (
    payload_json ? 'history_status'
    and jsonb_typeof(payload_json -> 'history_status') = 'string'
    and payload_json ->> 'history_status' = history_status
  ),
  check (
    ((payload_json -> 'history_source_report_count') = to_jsonb(history_source_report_count)) is true
  ),
  check (
    payload_json ? 'history_latest_quality_status'
    and jsonb_typeof(payload_json -> 'history_latest_quality_status') = 'string'
    and payload_json ->> 'history_latest_quality_status' = history_latest_quality_status
  ),
  check (((payload_json -> 'reason_codes') = reason_codes_json) is true)
);

create index if not exists idx_prpofr_generated_at
  on public.paper_research_packet_operator_flow_reports (generated_at desc);

create index if not exists idx_prpofr_config_version_generated_at
  on public.paper_research_packet_operator_flow_reports (config_version, generated_at desc);

create index if not exists idx_prpofr_flow_status_generated_at
  on public.paper_research_packet_operator_flow_reports (flow_status, generated_at desc);

create index if not exists idx_prpofr_quality_status_generated_at
  on public.paper_research_packet_operator_flow_reports (quality_status, generated_at desc);

create index if not exists idx_prpofr_history_status_generated_at
  on public.paper_research_packet_operator_flow_reports (history_status, generated_at desc);

create index if not exists idx_prpofr_packet_generated_at
  on public.paper_research_packet_operator_flow_reports (packet_generated_at desc);

create index if not exists idx_prpofr_quality_generated_at
  on public.paper_research_packet_operator_flow_reports (quality_generated_at desc);

create index if not exists idx_prpofr_history_generated_at
  on public.paper_research_packet_operator_flow_reports (history_generated_at desc);

create index if not exists idx_prpofr_reason_codes_json
  on public.paper_research_packet_operator_flow_reports using gin (reason_codes_json jsonb_path_ops);

create index if not exists idx_prpofr_payload_json
  on public.paper_research_packet_operator_flow_reports using gin (payload_json jsonb_path_ops);
