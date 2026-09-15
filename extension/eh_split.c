#include "eh_split.h"
#include "eh_hash.h"
#include "eh_bucket.h"
#include <string.h>

void bucket_split(Directory *dir, int idx)
{
    Bucket *old_b = dir->slots[idx];
    int old_ld = old_b->local_depth;
    int new_ld = old_ld + 1;
    Bucket *new_b = bucket_create(new_ld);

    Entry temp[BUCKET_CAPACITY];
    int temp_count = old_b->count;
    int i, s;

    memcpy(temp, old_b->entries, sizeof(Entry) * temp_count);

    old_b->local_depth = new_ld;
    old_b->count = 0;

    // Redistribuir las entradas segun el bit adicional del hash
    // (el bit en la posicion old_ld, que antes no se usaba para indexar)
    for (i = 0; i < temp_count; i++)
    {
        uint32_t h = hash_function(temp[i].key);
        int bit = (h >> old_ld) & 1;
        if (bit)
            bucket_insert_raw(new_b, temp[i].key, temp[i].tid);
        else
            bucket_insert_raw(old_b, temp[i].key, temp[i].tid);
    }

    // Actualizar los slots del directorio: los que compartian old_b
    // y tienen el bit nuevo en 1 ahora apuntan a new_b
    for (s = 0; s < dir->num_slots; s++)
    {
        if (dir->slots[s] == old_b)
        {
            int bit = (s >> old_ld) & 1;
            if (bit)
                dir->slots[s] = new_b;
        }
    }
}
