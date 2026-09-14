-- Immutable pending inputs, not execution leases or permission to call a model.
-- Existing execution_claims remain the single at-most-once loop-start authority.
create table research_capture.dispatch_batches (
  batch_id text primary key check (length(batch_id) between 1 and 128 and batch_id ~ '^[A-Za-z0-9_.:-]+$'),
  request_count integer not null check (request_count between 1 and 100),
  enqueued_at timestamptz not null check (isfinite(enqueued_at)),
  payload text not null check (octet_length(payload) between 1 and 8388608),
  payload_sha256 text not null check (payload_sha256 ~ '^[a-f0-9]{64}$'),
  paper_only boolean not null default true check (paper_only is true),
  report_only boolean not null default true check (report_only is true),
  readonly boolean not null default true check (readonly is true),
  check (encode(sha256(convert_to(payload, 'UTF8')), 'hex') = payload_sha256),
  check ((payload::jsonb ->> 'schema_version' = 'research-dispatch-batch-v1') is true),
  check ((payload::jsonb ->> 'batch_id' = batch_id) is true),
  check ((jsonb_typeof(payload::jsonb -> 'requests') = 'array') is true),
  check ((jsonb_array_length(payload::jsonb -> 'requests') = request_count) is true),
  check ((payload::jsonb -> 'paper_only' = 'true'::jsonb) is true),
  check ((payload::jsonb -> 'report_only' = 'true'::jsonb) is true),
  check ((payload::jsonb -> 'readonly' = 'true'::jsonb) is true)
);

create function research_capture.stamp_dispatch_batch() returns trigger
language plpgsql set search_path = pg_catalog as $$
declare entry jsonb; body jsonb; raw_body text; seen_ids text[] := '{}'; seen_tasks jsonb := '[]';
        identity_key jsonb; as_of_time timestamptz; cutoff timestamptz; delay_seconds integer;
begin
  perform pg_advisory_xact_lock(hashtextextended('polymarket/research_dispatch/' || new.batch_id, 0));
  new.enqueued_at := clock_timestamp();
  for entry in select value from jsonb_array_elements(new.payload::jsonb -> 'requests') loop
    if jsonb_typeof(entry) <> 'string' then raise exception 'research_batch_request_invalid'; end if;
    raw_body := entry #>> '{}';
    if octet_length(raw_body) not between 1 and 2097152 then
      raise exception 'research_batch_request_invalid';
    end if;
    body := raw_body::jsonb;
    identity_key := jsonb_build_array(body #>> '{intake,team_id}', body ->> 'model_id',
                                     body ->> 'protocol_version', body #>> '{intake,task_id}');
    if (body ->> 'schema_version' = 'research-execution-v1') is not true
       or (body #>> '{intake,team_id}' in ('crypto_btc','crypto_eth')) is not true
       or (body ->> 'record_id' ~ '^[A-Za-z0-9_.:-]{1,128}$') is not true
       or (body -> 'paper_only' = 'true'::jsonb) is not true
       or (body -> 'report_only' = 'true'::jsonb) is not true
       or (body -> 'readonly' = 'true'::jsonb) is not true
       or body ->> 'record_id' = any(seen_ids)
       or exists (select 1 from jsonb_array_elements(seen_tasks) t(value) where t.value = identity_key) then
      raise exception 'research_batch_request_invalid';
    end if;
    seen_ids := array_append(seen_ids, body ->> 'record_id');
    seen_tasks := seen_tasks || jsonb_build_array(identity_key);
    as_of_time := (body #>> '{intake,as_of}')::timestamptz;
    cutoff := (body ->> 'forecast_cutoff_at')::timestamptz;
    delay_seconds := (body ->> 'max_start_delay_seconds')::integer;
    if (isfinite(as_of_time) and isfinite(cutoff) and delay_seconds between 1 and 3600
        and as_of_time <= new.enqueued_at and new.enqueued_at < cutoff
        and new.enqueued_at - as_of_time <= make_interval(secs => delay_seconds)) is not true then
      raise exception 'research_batch_not_startable';
    end if;
  end loop;
  return new;
end $$;

create trigger stamp_dispatch_batch before insert on research_capture.dispatch_batches
  for each row execute function research_capture.stamp_dispatch_batch();
create trigger immutable_dispatch_batches before update or delete on research_capture.dispatch_batches
  for each row execute function research_capture.reject_mutation();
create trigger no_truncate_dispatch_batches before truncate on research_capture.dispatch_batches
  for each statement execute function research_capture.reject_mutation();
revoke all on research_capture.dispatch_batches from public;
revoke all on function research_capture.stamp_dispatch_batch() from public;
comment on table research_capture.dispatch_batches is
  'Immutable local paper research inputs. Pending is not a claim; incomplete claims are never automatically reclaimed.';
