#include "postgres.h"
#include "fmgr.h"
#include "eh_types.h"
#include "eh_insert_core.h"

extern Directory *g_index; // definida en eh_build.c

PG_FUNCTION_INFO_V1(eh_insert);

Datum
eh_insert(PG_FUNCTION_ARGS)
{
    int32 key = PG_GETARG_INT32(0);
    int result;

    if (g_index == NULL)
        elog(ERROR, "eh_insert: el indice no ha sido construido. Ejecute SELECT eh_build(); primero.");

    result = eh_directory_insert(g_index, key, (int64_t) key);

    if (result == 0)
    {
        elog(NOTICE, "eh_insert: la clave %d ya existia, no se inserto de nuevo", key);
        PG_RETURN_BOOL(false);
    }
    else if (result == -1)
    {
        elog(WARNING, "eh_insert: no se pudo insertar la clave %d (limite de splits alcanzado)", key);
        PG_RETURN_BOOL(false);
    }

    PG_RETURN_BOOL(true);
}
