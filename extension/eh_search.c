#include "postgres.h"
#include "fmgr.h"
#include "eh_types.h"
#include "eh_directory.h"
#include "eh_bucket.h"
#include "eh_hash.h"

/* Definida en eh_build.c, dentro del mismo modulo (.so) */
extern Directory *g_index;

PG_FUNCTION_INFO_V1(eh_search);

Datum
eh_search(PG_FUNCTION_ARGS)
{
    int32 key = PG_GETARG_INT32(0);
    int64 tid_out;
    uint32_t h;
    int idx;
    Bucket *b;
    int found;

    if (g_index == NULL)
        elog(ERROR, "eh_search: el indice no ha sido construido. Ejecute SELECT eh_build(); primero.");

    h = hash_function(key);
    idx = directory_index(g_index, h);
    b = g_index->slots[idx];
    found = bucket_find(b, key, &tid_out);

    if (!found)
        PG_RETURN_NULL();

    PG_RETURN_INT64(tid_out);
}
