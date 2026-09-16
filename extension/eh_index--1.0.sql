CREATE FUNCTION eh_build() RETURNS boolean
AS 'MODULE_PATHNAME', 'eh_build'
LANGUAGE C STRICT;

CREATE FUNCTION eh_search(integer) RETURNS bigint
AS 'MODULE_PATHNAME', 'eh_search'
LANGUAGE C STRICT;

CREATE FUNCTION eh_count_source_rows() RETURNS bigint
AS 'MODULE_PATHNAME', 'eh_count_source_rows'
LANGUAGE C STRICT;

CREATE FUNCTION eh_insert(integer) RETURNS boolean
AS 'MODULE_PATHNAME', 'eh_insert'
LANGUAGE C STRICT;

CREATE FUNCTION eh_save() RETURNS boolean
AS 'MODULE_PATHNAME', 'eh_save'
LANGUAGE C STRICT;

CREATE FUNCTION eh_load() RETURNS boolean
AS 'MODULE_PATHNAME', 'eh_load'
LANGUAGE C STRICT;

CREATE FUNCTION eh_sync_trigger() RETURNS trigger
AS 'MODULE_PATHNAME', 'eh_sync_trigger'
LANGUAGE C;

CREATE FUNCTION eh_build_table(text, text) RETURNS boolean
AS 'MODULE_PATHNAME', 'eh_build_table'
LANGUAGE C STRICT;

CREATE FUNCTION eh_index_size() RETURNS bigint
AS 'MODULE_PATHNAME', 'eh_index_size'
LANGUAGE C STRICT;




