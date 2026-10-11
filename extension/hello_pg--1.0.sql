CREATE FUNCTION hello_pg_add(integer, integer) RETURNS integer
AS 'MODULE_PATHNAME', 'hello_pg_add'
LANGUAGE C STRICT;