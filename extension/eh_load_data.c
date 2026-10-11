#include "postgres.h"
#include "fmgr.h"
#include "executor/spi.h"
#include "eh_types.h"
#include "eh_hash.h"

PG_FUNCTION_INFO_V1(eh_count_source_rows);

/*
 * Funcion de prueba (Semana 3): se conecta a PostgreSQL via SPI,
 * lee la tabla medicamento y cuenta cuantas filas se pudieron leer,
 * calculando el hash de cada id. Esto valida que el flujo
 * SPI -> C funciona antes de conectarlo con eh_build() (Semana 4).
 */
Datum
eh_count_source_rows(PG_FUNCTION_ARGS)
{
    int ret;
    int64 processed;

    SPI_connect();

    ret = SPI_execute("SELECT id FROM medicamento", true, 0);

    if (ret != SPI_OK_SELECT)
        elog(ERROR, "eh_count_source_rows: fallo la consulta SPI (codigo %d)", ret);

    processed = SPI_processed;

    for (uint64 i = 0; i < SPI_processed; i++)
    {
        HeapTuple tuple = SPI_tuptable->vals[i];
        TupleDesc tupdesc = SPI_tuptable->tupdesc;
        bool isnull;
        Datum id_datum = SPI_getbinval(tuple, tupdesc, 1, &isnull);

        if (!isnull)
        {
            int32 id = DatumGetInt32(id_datum);
            uint32_t h = hash_function(id);
            elog(DEBUG1, "medicamento.id=%d hash=%u", id, h);
        }
    }

    SPI_finish();

    PG_RETURN_INT64(processed);
}
