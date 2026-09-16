#include "postgres.h"
#include "eh_directory.h"
#include "eh_bucket.h"
#include <stdlib.h>

Directory *directory_create(int initial_global_depth) {
    bucket_reset_id_counter();

    Directory *dir = malloc(sizeof(Directory));
    dir->global_depth = initial_global_depth;
    dir->num_slots = 1 << initial_global_depth;
    dir->slots = malloc(sizeof(Bucket*) * dir->num_slots);

    // Semana 3: todos los slots apuntan al mismo bucket inicial, vacio.
    // El primer split real de este bucket compartido se implementa
    // en la Semana 5 junto con la logica de insercion.
    Bucket *initial = bucket_create(initial_global_depth);
        for (int i = 0; i < dir->num_slots; i++) {
            dir->slots[i] = initial;
        }
    return dir;
}

void directory_free(Directory *dir) {
    // Nota: no libera los buckets aqui porque varios slots pueden
    // compartir el mismo puntero. La liberacion de buckets unicos
    // se resuelve en la Semana 5 cuando ya existan multiples buckets.
    free(dir->slots);
    free(dir);
}

int directory_index(Directory *dir, uint32_t hash) {
    return hash & ((1u << dir->global_depth) - 1);
}

void directory_double(Directory *dir) {
    int old_slots = dir->num_slots;
    dir->global_depth++;
        if (dir->global_depth >= 20)
            {
                elog(ERROR, "directory_double: ABORTADO en global_depth=%d — bug de duplicacion descontrolada detectado", dir->global_depth);
            }
    dir->num_slots = old_slots * 2;
    dir->slots = realloc(dir->slots, dir->num_slots * sizeof(Bucket*));
    for (int i = 0; i < old_slots; i++) {
        dir->slots[old_slots + i] = dir->slots[i];
    }
}

void directory_free_all(Directory *dir) {
    if (dir == NULL) return;
    bool *freed = calloc(dir->num_slots, sizeof(bool));
    for (int i = 0; i < dir->num_slots; i++) {
        if (!freed[i]) {
            Bucket *b = dir->slots[i];
            for (int j = i; j < dir->num_slots; j++) {
                if (dir->slots[j] == b) freed[j] = true;
            }
            free(b);
        }
    }
    free(freed);
    free(dir->slots);
    free(dir);
}
