create table if not exists public.paper_probability_selection_summary_history_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    source_report_count integer not null,
    latest_generated_at timestamptz,
    latest_age_seconds integer,
    latest_queue_count integer not null,
    latest_selected_count integer not null,
    latest_selected_share numeric(12, 6) not null,
    average_selected_share numeric(12, 6) not null,
    history_status text not null,
    recommended_next_step text not null,
    reason_codes jsonb not null,
    payload jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (source_report_count >= 0),
    check (latest_age_seconds is null or latest_age_seconds >= 0),
    check (latest_queue_count >= 0),
    check (latest_selected_count >= 0),
    check (latest_selected_count <= latest_queue_count),
    check (latest_selected_share >= 0 and latest_selected_share <= 1),
    check (average_selected_share >= 0 and average_selected_share <= 1),
    check (history_status in ('ready', 'watch', 'blocked')),
    check (
        recommended_next_step in (
            'collect_more_history',
            'refresh_selection_summary',
            'review_probability_selection',
            'proceed_to_paper_allocation'
        )
    ),
    check (jsonb_typeof(reason_codes) = 'array'),
    check (jsonb_typeof(payload) = 'object'),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true),
    check (payload ? 'paper_only' and payload -> 'paper_only' = 'true'::jsonb),
    check (payload ? 'report_only' and payload -> 'report_only' = 'true'::jsonb),
    check (payload ? 'readonly' and payload -> 'readonly' = 'true'::jsonb),
    check (payload ? 'generated_at' and jsonb_typeof(payload -> 'generated_at') = 'string' and (payload ->> 'generated_at')::timestamptz = generated_at),
    check (payload ? 'config_version' and jsonb_typeof(payload -> 'config_version') = 'string' and payload ->> 'config_version' = config_version),
    check (payload ? 'source_report_count' and (payload ->> 'source_report_count')::integer = source_report_count),
    check (payload ? 'latest_queue_count' and (payload ->> 'latest_queue_count')::integer = latest_queue_count),
    check (payload ? 'latest_selected_count' and (payload ->> 'latest_selected_count')::integer = latest_selected_count),
    check (payload ? 'history_status' and jsonb_typeof(payload -> 'history_status') = 'string' and payload ->> 'history_status' = history_status),
    check (payload ? 'recommended_next_step' and jsonb_typeof(payload -> 'recommended_next_step') = 'string' and payload ->> 'recommended_next_step' = recommended_next_step),
    check (payload ? 'reason_codes' and jsonb_typeof(payload -> 'reason_codes') = 'array' and payload -> 'reason_codes' = reason_codes)
);

create index if not exists ppsshr_generated_order_idx
    on public.paper_probability_selection_summary_history_reports (generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists ppsshr_config_order_idx
    on public.paper_probability_selection_summary_history_reports (config_version, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists ppsshr_status_order_idx
    on public.paper_probability_selection_summary_history_reports (history_status, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists ppsshr_latest_generated_order_idx
    on public.paper_probability_selection_summary_history_reports (latest_generated_at desc, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists ppsshr_reason_codes_idx
    on public.paper_probability_selection_summary_history_reports using gin (reason_codes jsonb_path_ops);

create index if not exists ppsshr_payload_idx
    on public.paper_probability_selection_summary_history_reports using gin (payload jsonb_path_ops);
