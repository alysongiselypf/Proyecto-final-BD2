#ifndef EH_BUCKET_H
#define EH_BUCKET_H

#include "eh_types.h"
#include <stdbool.h>

Bucket *bucket_create(int local_depth);
void bucket_free(Bucket *b);
bool bucket_is_full(Bucket *b);
bool bucket_insert_raw(Bucket *b, int32_t key, int64_t tid);
int bucket_find(Bucket *b, int32_t key, int64_t *tid_out);
bool bucket_contains(Bucket *b, int32_t key);
void bucket_reset_id_counter(void);

#endif
