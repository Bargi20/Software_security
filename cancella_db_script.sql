-- su "schemename" ci va il nome dello schema, su supabase sta su table editor e poi lo vedi sulla colonna a sinistra in alto dove ci sono le varie tabelle
do $$ declare
    r record;
begin
    for r in (select tablename from pg_tables where schemaname = 'public') loop
        execute 'drop table if exists ' || quote_ident(r.tablename) || ' cascade';
    end loop;
end $$;