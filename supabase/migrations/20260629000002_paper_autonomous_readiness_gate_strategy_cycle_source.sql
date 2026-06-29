do $$
declare
    constraint_name text;
begin
    for constraint_name in
        select conname
        from pg_constraint
        where conrelid = 'public.paper_autonomous_readiness_gate_reports'::regclass
          and contype = 'c'
          and pg_get_constraintdef(oid) like '%jsonb_array_length(source_statuses_json) = 3%'
    loop
        execute format(
            'alter table public.paper_autonomous_readiness_gate_reports drop constraint if exists %I',
            constraint_name
        );
    end loop;

    for constraint_name in
        select conname
        from pg_constraint
        where conrelid = 'public.paper_autonomous_readiness_gate_reports'::regclass
          and contype = 'c'
          and pg_get_constraintdef(oid) like '%jsonb_array_length(source_config_versions_json) = 3%'
    loop
        execute format(
            'alter table public.paper_autonomous_readiness_gate_reports drop constraint if exists %I',
            constraint_name
        );
    end loop;
end $$;

alter table public.paper_autonomous_readiness_gate_reports
    add constraint pargr_source_statuses_length_check
    check (jsonb_array_length(source_statuses_json) in (3, 4));

alter table public.paper_autonomous_readiness_gate_reports
    add constraint pargr_source_config_versions_length_check
    check (jsonb_array_length(source_config_versions_json) in (3, 4));

create index if not exists pargr_four_source_status_sort_idx
    on public.paper_autonomous_readiness_gate_reports
    (
        (source_statuses_json #>> '{0,status}'),
        (source_statuses_json #>> '{1,status}'),
        (source_statuses_json #>> '{2,status}'),
        (source_statuses_json #>> '{3,status}'),
        generated_at desc,
        inserted_at desc,
        report_sha256 desc
    );
