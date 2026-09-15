#include "eh_insert_core.h"
#include "eh_hash.h"
#include "eh_bucket.h"
#include "eh_directory.h"
#include "eh_split.h"

int eh_directory_insert(Directory *dir, int32_t key, int64_t tid)
{
    // Limite de seguridad: evita un loop infinito si un bug de split
    // dejara el bucket destino siempre lleno (edge case documentado
    // por Alyson: overflow).
    int max_iterations = 32;

    while (max_iterations-- > 0)
    {
        uint32_t h = hash_function(key);
        int idx = directory_index(dir, h);
        Bucket *b = dir->slots[idx];

        if (bucket_contains(b, key))
            return 0; // duplicado, no se inserta de nuevo

        if (!bucket_is_full(b))
        {
            bucket_insert_raw(b, key, tid);
            return 1;
        }

        // Bucket lleno: decidir si hace falta duplicar el directorio
        // antes de poder dividir el bucket.
        if (b->local_depth == dir->global_depth)
        {
            directory_double(dir);
            idx = directory_index(dir, h); // recalcular: num_slots cambio
        }

        bucket_split(dir, idx);
        // se reintenta la insercion en la siguiente vuelta del while,
        // ahora con el bucket ya dividido
    }

    return -1; // no se logro insertar tras el limite de splits
}
