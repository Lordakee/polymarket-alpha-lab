-- Immutable rotation cursors, not execution claims, leases or model approval.
create table research_capture.dispatch_turns (
  rotation_id text not null check (rotation_id ~ '^[A-Za-z0-9_.:-]{1,128}$'),
  turn_id text not null check (turn_id ~ '^[A-Za-z0-9_.:-]{1,128}$'),
  turn_number integer not null check (turn_number between 1 and 1000000000),
  start_slot integer not null check (start_slot between 0 and 99),
  next_slot integer not null check (next_slot between 0 and 99),
  roster_sha256 text not null check (roster_sha256 ~ '^[a-f0-9]{64}$'),
  payload text not null check (octet_length(payload) between 1 and 131072),
  payload_sha256 text not null check (payload_sha256 ~ '^[a-f0-9]{64}$'),
  reserved_at timestamptz not null check (isfinite(reserved_at)),
  paper_only boolean not null default true check (paper_only is true),
  report_only boolean not null default true check (report_only is true),
  readonly boolean not null default true check (readonly is true),
  primary key (rotation_id, turn_number),
  unique (rotation_id, turn_id),
  check (encode(sha256(convert_to(payload,'UTF8')),'hex') = payload_sha256)
);

create function research_capture.stamp_dispatch_turn() returns trigger
language plpgsql set search_path = pg_catalog as $$
declare previous research_capture.dispatch_turns%rowtype; body jsonb;
        item jsonb; key_item jsonb; observed timestamptz; n integer; cap integer;
        visited integer := 0; picked integer := 0; slot integer; total integer := 0;
        batch_ids text[] := '{}'; record_ids text[] := '{}'; stamp_count integer := 0;
        depth integer; max_depth integer := 0; key_slot integer := 0; request_body text;
begin
  perform pg_advisory_xact_lock(hashtextextended('polymarket/research_rotation/' || new.rotation_id,0));
  select * into previous from research_capture.dispatch_turns
    where rotation_id = new.rotation_id order by turn_number desc limit 1;
  body := new.payload::jsonb;
  new.reserved_at := clock_timestamp();
  if (body ->> 'schema_version' = 'research-dispatch-turn-v1') is not true
     or (body ->> 'rotation_id' = new.rotation_id) is not true
     or (body ->> 'turn_id' = new.turn_id) is not true
     or ((body ->> 'turn_number')::integer = new.turn_number) is not true
     or ((body ->> 'start_slot')::integer = new.start_slot) is not true
     or (body -> 'paper_only' = 'true'::jsonb) is not true
     or (body -> 'report_only' = 'true'::jsonb) is not true
     or (body -> 'readonly' = 'true'::jsonb) is not true
     or (jsonb_typeof(body -> 'roster') = 'array') is not true
     or (jsonb_typeof(body -> 'states') = 'array') is not true
     or (jsonb_typeof(body -> 'request_keys') = 'array') is not true
     or (jsonb_typeof(body -> 'observed_at') = 'array') is not true
     or (jsonb_array_length(body -> 'roster') between 1 and 10) is not true
     or ((body ->> 'max_workers')::integer between 1 and 8) is not true then
    raise exception 'research_rotation_payload_invalid';
  end if;
  for item in select value from jsonb_array_elements(body -> 'roster') loop
    if jsonb_typeof(item) <> 'array' or jsonb_array_length(item) <> 3
       or (item ->> 0 = any(batch_ids)) then
      raise exception 'research_rotation_roster_invalid';
    end if;
    if not exists (select 1 from research_capture.dispatch_batches b
        where b.batch_id = item ->> 0 and b.payload_sha256 = item ->> 1
          and b.request_count = (item ->> 2)::integer) then
      raise exception 'research_rotation_roster_invalid';
    end if;
    batch_ids := array_append(batch_ids,item ->> 0);
    total := total + (item ->> 2)::integer;
    max_depth := greatest(max_depth, (item ->> 2)::integer);
  end loop;
  n := jsonb_array_length(body -> 'states');
  cap := (body ->> 'max_tasks')::integer;
  if (n = total and n between 1 and 100 and cap between 1 and 100
      and new.start_slot < n and jsonb_array_length(body -> 'request_keys') = n) is not true then
    raise exception 'research_rotation_selection_invalid';
  end if;
  for item in select value from jsonb_array_elements(body -> 'states') loop
    if (item #>> '{}' in ('pending','expired','incomplete','captured')) is not true then
      raise exception 'research_rotation_state_invalid';
    end if;
  end loop;
  for key_item in select value from jsonb_array_elements(body -> 'request_keys') loop
    if (jsonb_typeof(key_item) = 'array' and jsonb_array_length(key_item) = 2
        and key_item ->> 0 ~ '^[A-Za-z0-9_.:-]{1,128}$'
        and key_item ->> 1 ~ '^[a-f0-9]{64}$') is not true
       or key_item ->> 0 = any(record_ids) then
      raise exception 'research_rotation_request_keys_invalid';
    end if;
    record_ids := array_append(record_ids,key_item ->> 0);
  end loop;
  -- Bind every interleaved slot to its original immutable batch request.
  -- This validates identity/hashes, not current execution state or approval.
  for depth in 0..max_depth-1 loop
    for item in select value from jsonb_array_elements(body -> 'roster') loop
      if depth < (item ->> 2)::integer then
        select payload::jsonb -> 'requests' ->> depth into request_body
          from research_capture.dispatch_batches where batch_id = item ->> 0;
        key_item := body -> 'request_keys' -> key_slot;
        if (key_item ->> 0 = request_body::jsonb ->> 'record_id'
            and key_item ->> 1 = encode(sha256(convert_to(request_body,'UTF8')),'hex')) is not true then
          raise exception 'research_rotation_request_binding_invalid';
        end if;
        key_slot := key_slot + 1;
      end if;
    end loop;
  end loop;
  for item in select value from jsonb_array_elements(body -> 'observed_at') loop
    observed := (item #>> '{}')::timestamptz;
    if (jsonb_typeof(item) = 'string' and isfinite(observed)
        and observed <= new.reserved_at) is not true then
      raise exception 'research_rotation_clock_invalid';
    end if;
    stamp_count := stamp_count + 1;
  end loop;
  if stamp_count <> array_length(batch_ids,1) then raise exception 'research_rotation_clock_invalid'; end if;
  while visited < n and picked < cap loop
    slot := (new.start_slot + visited) % n;
    visited := visited + 1;
    if body -> 'states' ->> slot = 'pending' then picked := picked + 1; end if;
  end loop;
  if new.next_slot <> (new.start_slot + visited) % n then
    raise exception 'research_rotation_cursor_invalid';
  end if;
  if previous.rotation_id is null then
    if new.turn_number <> 1 or new.start_slot <> 0 then
      raise exception 'research_rotation_predecessor_invalid';
    end if;
  elsif new.turn_number <> previous.turn_number + 1 or new.start_slot <> previous.next_slot
        or new.roster_sha256 <> previous.roster_sha256
        or body -> 'roster' <> previous.payload::jsonb -> 'roster'
        or body -> 'request_keys' <> previous.payload::jsonb -> 'request_keys'
        or new.reserved_at < previous.reserved_at then
    raise exception 'research_rotation_predecessor_invalid';
  end if;
  return new;
end $$;

create trigger stamp_dispatch_turn before insert on research_capture.dispatch_turns
  for each row execute function research_capture.stamp_dispatch_turn();
create trigger immutable_dispatch_turns before update or delete on research_capture.dispatch_turns
  for each row execute function research_capture.reject_mutation();
create trigger no_truncate_dispatch_turns before truncate on research_capture.dispatch_turns
  for each statement execute function research_capture.reject_mutation();
revoke all on research_capture.dispatch_turns from public;
revoke all on function research_capture.stamp_dispatch_turn() from public;
comment on table research_capture.dispatch_turns is
  'Append-only fair selection receipts. Reservation is not a claim. Replayed turns never restart models.';
