create table if not exists public.paper_probability_selection_summary_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    source_queue_config_version text not null,
    source_cost_stress_config_version text not null,
    queue_count integer not null,
    ready_count integer not null,
    watch_count integer not null,
    blocked_count integer not null,
    missing_stress_count integer not null,
    rows jsonb not null,
    reason_codes jsonb not null,
    payload jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (queue_count >= 0),
    check (ready_count >= 0),
    check (watch_count >= 0),
    check (blocked_count >= 0),
    check (missing_stress_count >= 0),
    check (queue_count = ready_count + watch_count + blocked_count),
    check (queue_count = jsonb_array_length(rows)),
    check (jsonb_typeof(rows) = 'array'),
    check (jsonb_typeof(reason_codes) = 'array'),
    check (jsonb_typeof(payload) = 'object'),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true),
    check ((payload ->> 'paper_only') = 'true'),
    check ((payload ->> 'report_only') = 'true'),
    check ((payload ->> 'readonly') = 'true'),
    check (
        not jsonb_path_exists(
            rows,
            '$[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'
        )
    ),
    check (
        not jsonb_path_exists(
            payload,
            '$.rows[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'
        )
    )
);

create index if not exists paper_probability_selection_summary_generated_order_idx
    on public.paper_probability_selection_summary_reports (generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists paper_probability_selection_summary_config_order_idx
    on public.paper_probability_selection_summary_reports (config_version, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists paper_probability_selection_summary_queue_config_order_idx
    on public.paper_probability_selection_summary_reports (source_queue_config_version, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists paper_probability_selection_summary_cost_stress_config_order_idx
    on public.paper_probability_selection_summary_reports (source_cost_stress_config_version, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists paper_probability_selection_summary_ready_order_idx
    on public.paper_probability_selection_summary_reports (generated_at desc, inserted_at desc, report_sha256 desc)
    where ready_count > 0;

create index if not exists paper_probability_selection_summary_watch_order_idx
    on public.paper_probability_selection_summary_reports (generated_at desc, inserted_at desc, report_sha256 desc)
    where watch_count > 0;

create index if not exists paper_probability_selection_summary_blocked_order_idx
    on public.paper_probability_selection_summary_reports (generated_at desc, inserted_at desc, report_sha256 desc)
    where blocked_count > 0;

create index if not exists paper_probability_selection_summary_reason_codes_idx
    on public.paper_probability_selection_summary_reports using gin (reason_codes jsonb_path_ops);

create index if not exists paper_probability_selection_summary_rows_idx
    on public.paper_probability_selection_summary_reports using gin (rows jsonb_path_ops);

create index if not exists paper_probability_selection_summary_payload_idx
    on public.paper_probability_selection_summary_reports using gin (payload jsonb_path_ops);
