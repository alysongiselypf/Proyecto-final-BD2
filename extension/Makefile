MODULES = hello_pg
MODULE_big = eh_index
OBJS = eh_hash.o eh_bucket.o eh_directory.o eh_split.o eh_insert_core.o eh_build.o eh_search.o eh_insert.o eh_persist.o eh_persist_pg.o eh_trigger.o eh_load_data.o

EXTENSION = hello_pg eh_index
DATA = hello_pg--1.0.sql eh_index--1.0.sql

PG_CONFIG = pg_config
PGXS := $(shell $(PG_CONFIG) --pgxs)
include $(PGXS)


