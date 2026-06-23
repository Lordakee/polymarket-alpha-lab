create table if not exists public.paper_research_packet_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  input_row_count integer not null
    check (input_row_count >= 0),
  packet_row_count integer not null
    check (packet_row_count >= 0),
  included_count integer not null
    check (included_count >= 0),
  skipped_count integer not null
    check (skipped_count >= 0),
  high_priority_count integer not null
    check (high_priority_count >= 0),
  medium_priority_count integer not null
    check (medium_priority_count >= 0),
  low_priority_count integer not null
    check (low_priority_count >= 0),
  packet_rows_json jsonb not null default '[]'::jsonb
    check (jsonb_typeof(packet_rows_json) = 'array'),
  payload_json jsonb not null
    check (jsonb_typeof(payload_json) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (input_row_count >= packet_row_count),
  check (packet_row_count = included_count + skipped_count),
  check (included_count = high_priority_count + medium_priority_count + low_priority_count),
  check (packet_row_count = jsonb_array_length(packet_rows_json)),
  check (((payload_json -> 'paper_only') = 'true'::jsonb) is true),
  check (((payload_json -> 'report_only') = 'true'::jsonb) is true),
  check (((payload_json -> 'readonly') = 'true'::jsonb) is true),
  check (payload_json ? 'generated_at'
    and jsonb_typeof(payload_json -> 'generated_at') = 'string'
    and (payload_json ->> 'generated_at')::timestamptz = generated_at),
  check (payload_json ? 'config_version'
    and jsonb_typeof(payload_json -> 'config_version') = 'string'
    and payload_json ->> 'config_version' = config_version),
  check (((payload_json -> 'packet_rows') = packet_rows_json) is true),
  check (((payload_json -> 'input_row_count') = to_jsonb(input_row_count)) is true),
  check (((payload_json -> 'packet_row_count') = to_jsonb(packet_row_count)) is true),
  check (((payload_json -> 'included_count') = to_jsonb(included_count)) is true),
  check (((payload_json -> 'skipped_count') = to_jsonb(skipped_count)) is true),
  check (((payload_json -> 'high_priority_count') = to_jsonb(high_priority_count)) is true),
  check (((payload_json -> 'medium_priority_count') = to_jsonb(medium_priority_count)) is true),
  check (((payload_json -> 'low_priority_count') = to_jsonb(low_priority_count)) is true),
  check (
    jsonb_array_length(
      jsonb_path_query_array(packet_rows_json, '$[*] ? (@.paper_only == true)')
    ) = jsonb_array_length(packet_rows_json)
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(packet_rows_json, '$[*] ? (@.report_only == true)')
    ) = jsonb_array_length(packet_rows_json)
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(packet_rows_json, '$[*] ? (@.readonly == true)')
    ) = jsonb_array_length(packet_rows_json)
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(payload_json, '$.packet_rows[*] ? (@.paper_only == true)')
    ) = packet_row_count
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(payload_json, '$.packet_rows[*] ? (@.report_only == true)')
    ) = packet_row_count
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(payload_json, '$.packet_rows[*] ? (@.readonly == true)')
    ) = packet_row_count
  ),
  check (
    not jsonb_path_exists(
      packet_rows_json,
      '$[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'
    )
  ),
  check (
    not jsonb_path_exists(
      payload_json,
      '$.packet_rows[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'
    )
  )
);

create index if not exists idx_prpr_generated_at
  on public.paper_research_packet_reports (generated_at desc);

create index if not exists idx_prpr_config_version_generated_at
  on public.paper_research_packet_reports (config_version, generated_at desc);

create index if not exists idx_prpr_counts_generated_at
  on public.paper_research_packet_reports (
    packet_row_count,
    included_count,
    skipped_count,
    generated_at desc
  );

create index if not exists idx_prpr_packet_rows_json
  on public.paper_research_packet_reports using gin (packet_rows_json jsonb_path_ops);

create index if not exists idx_prpr_payload_json
  on public.paper_research_packet_reports using gin (payload_json jsonb_path_ops);
