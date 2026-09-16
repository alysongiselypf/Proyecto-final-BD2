#include "postgres.h"
#include "fmgr.h"
#include "eh_types.h"
#include "eh_persist.h"
#include <sys/stat.h>

extern Directory *g_index;  // definida en eh_build.c

PG_FUNCTION_INFO_V1(eh_save);
PG_FUNCTION_INFO_V1(eh_load);
PG_FUNCTION_INFO_V1(eh_index_size);


Datum
eh_save(PG_FUNCTION_ARGS)
{
    bool ok;
    if (g_index == NULL)
        elog(ERROR, "eh_save: el indice no ha sido construido. Ejecute SELECT eh_build(); primero.");
    ok = eh_directory_save(g_index, EH_INDEX_FILE_PATH);
    if (!ok)
        elog(WARNING, "eh_save: no se pudo escribir el archivo en %s", EH_INDEX_FILE_PATH);
    PG_RETURN_BOOL(ok);
}

Datum
eh_load(PG_FUNCTION_ARGS)
{
    Directory *loaded = eh_directory_load(EH_INDEX_FILE_PATH);
    if (loaded == NULL) {
        elog(NOTICE, "eh_load: no se encontro un indice persistido en %s", EH_INDEX_FILE_PATH);
        PG_RETURN_BOOL(false);
    }
    g_index = loaded;
    elog(NOTICE, "eh_load: indice cargado desde disco (gd=%d, slots=%d)",
         g_index->global_depth, g_index->num_slots);
    PG_RETURN_BOOL(true);
}

Datum
eh_index_size(PG_FUNCTION_ARGS)
{
    struct stat st;
    if (stat(EH_INDEX_FILE_PATH, &st) != 0)
        PG_RETURN_INT64(0);
    PG_RETURN_INT64((int64) st.st_size);
}

