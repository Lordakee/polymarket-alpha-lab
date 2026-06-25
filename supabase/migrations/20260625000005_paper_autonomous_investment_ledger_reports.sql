create or replace function public.pailr_entries_consistent(
    entries_value jsonb,
    reason_code_counts_value jsonb,
    total_submitted_notional_value numeric,
    latest_generated_at_value timestamptz,
    latest_age_seconds_value integer,
    generated_at_value timestamptz
) returns boolean language sql immutable
as $$
    with entry_rows as (
        select item
        from jsonb_array_elements(entries_value) as entries(item)
    ),
    entry_summary as (
        select
            count(*)::integer as entry_count,
            coalesce(
                sum(
                    case
                        when item ->> 'execution_status' = 'paper_submitted'
                            then (item ->> 'execution_notional')::numeric(38, 6)
                        else 0::numeric(38, 6)
                    end
                ),
                0::numeric(38, 6)
            ) as submitted_notional,
            max((item ->> 'source_generated_at')::timestamptz) as latest_source_generated_at,
            bool_and(
                case
                    when item ->> 'execution_status' = 'paper_submitted'
                        then (item ->> 'execution_notional')::numeric(38, 6) > 0
                    when item ->> 'execution_status' in ('paper_held', 'paper_blocked')
                        then (item ->> 'execution_notional')::numeric(38, 6) = 0
                    else false
                end
            ) as entry_notionals_valid
        from entry_rows
    ),
    reason_counts as (
        select
            reason.reason_code,
            count(*)::integer as source_record_count
        from entry_rows
        cross join lateral jsonb_array_elements_text(item -> 'reason_codes') as reason(reason_code)
        group by reason.reason_code
    ),
    expected_reason_code_counts as (
        select coalesce(
            jsonb_agg(
                jsonb_build_object(
                    'reason_code', reason_code,
                    'source_record_count', source_record_count,
                    'paper_only', true,
                    'report_only', true,
                    'readonly', true
                )
                order by source_record_count desc, reason_code
            ),
            '[]'::jsonb
        ) as value
        from reason_counts
    ),
    expected_latest as (
        select
            case
                when entry_count = 0 then null
                else latest_source_generated_at
            end as latest_generated_at,
            case
                when entry_count = 0 then null
                when latest_source_generated_at > generated_at_value then null
                else ceiling(
                    extract(epoch from (generated_at_value - latest_source_generated_at))
                )::integer
            end as latest_age_seconds,
            coalesce(entry_notionals_valid, true) as entry_notionals_valid,
            submitted_notional
        from entry_summary
    )
    select
        (select entry_notionals_valid from expected_latest)
        and (select submitted_notional from expected_latest) = total_submitted_notional_value
        and (select value from expected_reason_code_counts) = reason_code_counts_value
        and (
            (
                (select latest_generated_at from expected_latest) is null
                and latest_generated_at_value is null
            )
            or (select latest_generated_at from expected_latest) = latest_generated_at_value
        )
        and (
            (
                (select latest_age_seconds from expected_latest) is null
                and latest_age_seconds_value is null
            )
            or (select latest_age_seconds from expected_latest) = latest_age_seconds_value
        );
$$;

create table if not exists public.paper_autonomous_investment_ledger_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    ledger_status text not null,
    recommended_next_step text not null,
    source_record_count integer not null,
    submitted_count integer not null,
    held_count integer not null,
    blocked_count integer not null,
    total_submitted_notional numeric(38, 6) not null,
    held_zero_notional_count integer not null,
    blocked_zero_notional_count integer not null,
    latest_generated_at timestamptz,
    latest_age_seconds integer,
    reason_code_counts jsonb not null,
    entries jsonb not null,
    reason_codes jsonb not null,
    payload jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (ledger_status in ('pass', 'watch', 'blocked')),
    check (
        recommended_next_step = case ledger_status
            when 'pass' then 'archive_paper_autonomous_investment_ledger'
            when 'watch' then 'review_paper_autonomous_investment_ledger'
            when 'blocked' then 'block_paper_autonomous_investment_ledger'
        end
    ),
    check (source_record_count >= 0),
    check (submitted_count >= 0),
    check (held_count >= 0),
    check (blocked_count >= 0),
    check (total_submitted_notional >= 0),
    check (held_zero_notional_count >= 0),
    check (blocked_zero_notional_count >= 0),
    check (latest_age_seconds is null or latest_age_seconds >= 0),
    check (source_record_count = submitted_count + held_count + blocked_count),
    check (held_zero_notional_count = held_count),
    check (blocked_zero_notional_count = blocked_count),
    check (jsonb_typeof(reason_code_counts) = 'array'),
    check (jsonb_typeof(entries) = 'array'),
    check (jsonb_typeof(reason_codes) = 'array'),
    check (jsonb_typeof(payload) = 'object'),
    check (jsonb_array_length(entries) = source_record_count),
    check (
        submitted_count = jsonb_array_length(
            jsonb_path_query_array(entries, '$[*] ? (@.execution_status == "paper_submitted")')
        )
    ),
    check (
        held_count = jsonb_array_length(
            jsonb_path_query_array(entries, '$[*] ? (@.execution_status == "paper_held")')
        )
    ),
    check (
        blocked_count = jsonb_array_length(
            jsonb_path_query_array(entries, '$[*] ? (@.execution_status == "paper_blocked")')
        )
    ),
    check (
        (source_record_count = 0 and reason_codes @> '["paper_autonomous_investment_ledger_no_source_records"]'::jsonb)
        or source_record_count > 0
    ),
    check (
        blocked_count = 0
        or reason_codes @> '["paper_autonomous_investment_ledger_blocked_records_present"]'::jsonb
    ),
    check (
        held_count = 0
        or reason_codes @> '["paper_autonomous_investment_ledger_held_records_present"]'::jsonb
    ),
    check (
        not reason_codes @> '["paper_autonomous_investment_ledger_passed"]'::jsonb
        or (source_record_count > 0 and held_count = 0 and blocked_count = 0)
    ),
    check (
        public.pailr_entries_consistent(
            entries,
            reason_code_counts,
            total_submitted_notional,
            latest_generated_at,
            latest_age_seconds,
            generated_at
        )
    ),
    check (
        (
            source_record_count = 0
            and latest_generated_at is null
            and latest_age_seconds is null
            and jsonb_array_length(reason_code_counts) = 0
        )
        or (
            source_record_count > 0
            and latest_generated_at is not null
            and latest_age_seconds is not null
            and latest_generated_at <= generated_at
        )
    ),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true),
    check (payload ? 'paper_only' and payload -> 'paper_only' = 'true'::jsonb),
    check (payload ? 'report_only' and payload -> 'report_only' = 'true'::jsonb),
    check (payload ? 'readonly' and payload -> 'readonly' = 'true'::jsonb),
    check (payload ? 'generated_at' and jsonb_typeof(payload -> 'generated_at') = 'string' and (payload ->> 'generated_at')::timestamptz = generated_at),
    check (payload ? 'config_version' and jsonb_typeof(payload -> 'config_version') = 'string' and payload ->> 'config_version' = config_version),
    check (payload ? 'ledger_status' and jsonb_typeof(payload -> 'ledger_status') = 'string' and payload ->> 'ledger_status' = ledger_status),
    check (payload ? 'recommended_next_step' and jsonb_typeof(payload -> 'recommended_next_step') = 'string' and payload ->> 'recommended_next_step' = recommended_next_step),
    check (payload ? 'source_record_count' and payload -> 'source_record_count' = to_jsonb(source_record_count)),
    check (payload ? 'submitted_count' and payload -> 'submitted_count' = to_jsonb(submitted_count)),
    check (payload ? 'held_count' and payload -> 'held_count' = to_jsonb(held_count)),
    check (payload ? 'blocked_count' and payload -> 'blocked_count' = to_jsonb(blocked_count)),
    check (payload ? 'total_submitted_notional' and jsonb_typeof(payload -> 'total_submitted_notional') = 'string' and (payload ->> 'total_submitted_notional')::numeric(38, 6) = total_submitted_notional),
    check (payload ? 'held_zero_notional_count' and payload -> 'held_zero_notional_count' = to_jsonb(held_zero_notional_count)),
    check (payload ? 'blocked_zero_notional_count' and payload -> 'blocked_zero_notional_count' = to_jsonb(blocked_zero_notional_count)),
    check (
        (
            latest_generated_at is null
            and payload ? 'latest_generated_at'
            and payload -> 'latest_generated_at' = 'null'::jsonb
        )
        or (
            latest_generated_at is not null
            and payload ? 'latest_generated_at'
            and jsonb_typeof(payload -> 'latest_generated_at') = 'string'
            and (payload ->> 'latest_generated_at')::timestamptz = latest_generated_at
        )
    ),
    check (
        (
            latest_age_seconds is null
            and payload ? 'latest_age_seconds'
            and payload -> 'latest_age_seconds' = 'null'::jsonb
        )
        or (
            latest_age_seconds is not null
            and payload ? 'latest_age_seconds'
            and payload -> 'latest_age_seconds' = to_jsonb(latest_age_seconds)
        )
    ),
    check (payload ? 'reason_code_counts' and jsonb_typeof(payload -> 'reason_code_counts') = 'array' and payload -> 'reason_code_counts' = reason_code_counts),
    check (payload ? 'entries' and jsonb_typeof(payload -> 'entries') = 'array' and payload -> 'entries' = entries),
    check (payload ? 'reason_codes' and jsonb_typeof(payload -> 'reason_codes') = 'array' and payload -> 'reason_codes' = reason_codes),
    check (
        not jsonb_path_exists(
            entries,
            '$[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'
        )
    ),
    check (
        jsonb_array_length(jsonb_path_query_array(entries, '$[*] ? (@.paper_only == true)'))
        = jsonb_array_length(entries)
    ),
    check (
        jsonb_array_length(jsonb_path_query_array(entries, '$[*] ? (@.report_only == true)'))
        = jsonb_array_length(entries)
    ),
    check (
        jsonb_array_length(jsonb_path_query_array(entries, '$[*] ? (@.readonly == true)'))
        = jsonb_array_length(entries)
    ),
    check (
        not jsonb_path_exists(
            reason_code_counts,
            '$[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'
        )
    ),
    check (
        jsonb_array_length(jsonb_path_query_array(reason_code_counts, '$[*] ? (@.paper_only == true)'))
        = jsonb_array_length(reason_code_counts)
    ),
    check (
        jsonb_array_length(jsonb_path_query_array(reason_code_counts, '$[*] ? (@.report_only == true)'))
        = jsonb_array_length(reason_code_counts)
    ),
    check (
        jsonb_array_length(jsonb_path_query_array(reason_code_counts, '$[*] ? (@.readonly == true)'))
        = jsonb_array_length(reason_code_counts)
    ),
    check (
        not jsonb_path_exists(
            payload,
            '$.entries[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'
        )
    ),
    check (
        jsonb_array_length(jsonb_path_query_array(payload, '$.entries[*] ? (@.paper_only == true)'))
        = jsonb_array_length(payload -> 'entries')
    ),
    check (
        jsonb_array_length(jsonb_path_query_array(payload, '$.entries[*] ? (@.report_only == true)'))
        = jsonb_array_length(payload -> 'entries')
    ),
    check (
        jsonb_array_length(jsonb_path_query_array(payload, '$.entries[*] ? (@.readonly == true)'))
        = jsonb_array_length(payload -> 'entries')
    ),
    check (
        not jsonb_path_exists(
            payload,
            '$.reason_code_counts[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'
        )
    ),
    check (
        jsonb_array_length(jsonb_path_query_array(payload, '$.reason_code_counts[*] ? (@.paper_only == true)'))
        = jsonb_array_length(payload -> 'reason_code_counts')
    ),
    check (
        jsonb_array_length(jsonb_path_query_array(payload, '$.reason_code_counts[*] ? (@.report_only == true)'))
        = jsonb_array_length(payload -> 'reason_code_counts')
    ),
    check (
        jsonb_array_length(jsonb_path_query_array(payload, '$.reason_code_counts[*] ? (@.readonly == true)'))
        = jsonb_array_length(payload -> 'reason_code_counts')
    )
);

create index if not exists pailr_generated_order_idx
    on public.paper_autonomous_investment_ledger_reports (generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists pailr_config_order_idx
    on public.paper_autonomous_investment_ledger_reports (config_version, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists pailr_status_order_idx
    on public.paper_autonomous_investment_ledger_reports (ledger_status, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists pailr_latest_generated_order_idx
    on public.paper_autonomous_investment_ledger_reports (latest_generated_at desc, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists pailr_reason_code_counts_idx
    on public.paper_autonomous_investment_ledger_reports using gin (reason_code_counts jsonb_path_ops);

create index if not exists pailr_entries_idx
    on public.paper_autonomous_investment_ledger_reports using gin (entries jsonb_path_ops);

create index if not exists pailr_reason_codes_idx
    on public.paper_autonomous_investment_ledger_reports using gin (reason_codes jsonb_path_ops);

create index if not exists pailr_payload_idx
    on public.paper_autonomous_investment_ledger_reports using gin (payload jsonb_path_ops);
