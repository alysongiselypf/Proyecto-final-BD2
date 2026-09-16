#include "postgres.h"
#include "eh_bucket.h"
#include <stdlib.h>
#include <string.h>

static int g_next_bucket_id = 0;  // contador global, agregar arriba de bucket_create

Bucket *bucket_create(int local_depth) {
    Bucket *b = malloc(sizeof(Bucket));
    b->id = g_next_bucket_id++;
    b->local_depth = local_depth;
    b->count = 0;
    memset(b->entries, 0, sizeof(b->entries));

    if (b->id % 50000 == 0)
        elog(LOG, "bucket_create: van %d buckets creados (local_depth=%d)", b->id, local_depth);

    return b;
}

void bucket_free(Bucket *b) {
    free(b);
}

bool bucket_is_full(Bucket *b) {
    return b->count >= BUCKET_CAPACITY;
}

bool bucket_insert_raw(Bucket *b, int32_t key, int64_t tid) {
    // Nota: esta version NO hace split todavia (eso es Semana 5,
    // cuando se conecte con directory_double / bucket_split).
    if (bucket_is_full(b)) {
        return false;
    }
    b->entries[b->count].key = key;
    b->entries[b->count].tid = tid;
    b->count++;
    return true;
}

int bucket_find(Bucket *b, int32_t key, int64_t *tid_out) {
    for (int i = 0; i < b->count; i++) {
        if (b->entries[i].key == key) {
            *tid_out = b->entries[i].tid;
            return 1;
        }
    }
    return 0;
}

bool bucket_contains(Bucket *b, int32_t key) {
    int64_t dummy;
    return bucket_find(b, key, &dummy) == 1;
}

void bucket_reset_id_counter(void) {
    g_next_bucket_id = 0;
}


