#include "postgres.h"
#include "fmgr.h"
#include "executor/spi.h"
#include <stdlib.h>
#include "eh_types.h"
#include "eh_directory.h"
#include "eh_insert_core.h"
#include "eh_persist.h"   // agregar a los includes existentes

PG_MODULE_MAGIC;

PG_FUNCTION_INFO_V1(eh_build);

Directory *g_index = NULL;

Datum
eh_build(PG_FUNCTION_ARGS)
{
    int ret;
    int64 inserted = 0;
    int64 skipped_duplicate = 0;
    int64 skipped_failed = 0;
    uint64 i;

    if (g_index != NULL)
    {
        elog(NOTICE, "eh_build: el indice ya existia, se reinicializa");
        free(g_index->slots);
        free(g_index);
        g_index = NULL;
    }

    g_index = directory_create(2);

    SPI_connect();
    ret = SPI_execute("SELECT id FROM medicamento", true, 0);

    if (ret != SPI_OK_SELECT)
        elog(ERROR, "eh_build: fallo la consulta SPI (codigo %d)", ret);

    for (i = 0; i < SPI_processed; i++)
    {
        HeapTuple tuple = SPI_tuptable->vals[i];
        TupleDesc tupdesc = SPI_tuptable->tupdesc;
        bool isnull;
        Datum id_datum = SPI_getbinval(tuple, tupdesc, 1, &isnull);
        int32 id;
        int result;

        if (isnull)
            continue;

        id = DatumGetInt32(id_datum);
        result = eh_directory_insert(g_index, id, (int64) id);

        if (result == 1)
            inserted++;
        else if (result == 0)
            skipped_duplicate++;
        else
            skipped_failed++;
    }

    SPI_finish();

    elog(NOTICE,
         "eh_build: indice construido. gd=%d, slots=%d, insertados=%lld, omitidos_duplicado=%lld, fallidos=%lld",
         g_index->global_depth, g_index->num_slots,
         (long long) inserted, (long long) skipped_duplicate, (long long) skipped_failed);

             eh_directory_save(g_index, EH_INDEX_FILE_PATH);  // persistir automaticamente tras construir
    PG_RETURN_BOOL(true);
}

/*
 * PostgreSQL llama _PG_init() automaticamente cada vez que un proceso
 * backend (una conexion) carga esta libreria por primera vez. La
 * aprovechamos para cargar el indice desde disco sin que el usuario
 * tenga que llamar eh_load() manualmente en cada conexion nueva.
 */
void
_PG_init(void)
{
    g_index = eh_directory_load(EH_INDEX_FILE_PATH);
    if (g_index != NULL)
        elog(LOG, "eh_index: indice cargado automaticamente desde disco (gd=%d, slots=%d)",
             g_index->global_depth, g_index->num_slots);
    else
        elog(LOG, "eh_index: no se encontro indice persistido, se requiere SELECT eh_build();");
}


