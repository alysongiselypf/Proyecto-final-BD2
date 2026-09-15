#ifndef EH_TYPES_H
#define EH_TYPES_H

#include <stdint.h>

#define BUCKET_CAPACITY 4

typedef struct {
    int32_t key;   // medicamento.id
    int64_t tid;   // referencia al registro origen
} Entry;

typedef struct {
    int local_depth;
    int count;
    Entry entries[BUCKET_CAPACITY];
} Bucket;

typedef struct {
    int global_depth;
    int num_slots;
    Bucket **slots;
} Directory;

#endif
