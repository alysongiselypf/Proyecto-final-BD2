#include "postgres.h"
#include "fmgr.h"
#include "commands/trigger.h"
#include "access/htup_details.h"
#include "eh_types.h"
#include "eh_insert_core.h"
#include "eh_persist.h"

extern Directory *g_index;

PG_FUNCTION_INFO_V1(eh_sync_trigger);

Datum
eh_sync_trigger(PG_FUNCTION_ARGS)
{
    TriggerData *trigdata = (TriggerData *) fcinfo->context;
    HeapTuple new_tuple;
    TupleDesc tupdesc;
    bool isnull;
    Datum id_datum;
    int32 id;

    if (!CALLED_AS_TRIGGER(fcinfo))
        elog(ERROR, "eh_sync_trigger: debe invocarse como trigger");

    if (g_index == NULL) {
        elog(WARNING, "eh_sync_trigger: indice no construido, se omite. Ejecute SELECT eh_build(); primero.");
        return PointerGetDatum(trigdata->tg_trigtuple);
    }

    new_tuple = trigdata->tg_trigtuple;
    tupdesc = trigdata->tg_relation->rd_att;

    id_datum = heap_getattr(new_tuple, 1, tupdesc, &isnull);  // columna 'id' (1ra columna)

            if (!isnull) {
        int insert_result;
        bool saved;

        id = DatumGetInt32(id_datum);

        insert_result = eh_directory_insert(g_index, id, (int64) id);

        switch (insert_result) {
            case 1:
                saved = eh_directory_save(g_index, EH_INDEX_FILE_PATH);
                if (saved)
                    elog(NOTICE, "eh_sync_trigger: medicamento id=%d sincronizado y persistido", id);
                else
                    elog(WARNING, "eh_sync_trigger: medicamento id=%d indexado en memoria, pero fallo al persistir a disco", id);
                break;
            case 0:
                elog(WARNING, "eh_sync_trigger: la clave %d ya existia en el indice, no se inserto de nuevo", id);
                break;
            case -1:
                elog(WARNING, "eh_sync_trigger: fallo al indexar medicamento id=%d (overflow de splits). El registro quedo guardado en la tabla pero NO esta en el indice.", id);
                break;
            default:
                elog(WARNING, "eh_sync_trigger: eh_directory_insert devolvio un valor inesperado (%d) para id=%d", insert_result, id);
                break;
        }
    }
 }
