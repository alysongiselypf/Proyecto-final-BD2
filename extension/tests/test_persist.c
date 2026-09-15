#include <stdio.h>
#include <assert.h>
#include "../eh_types.h"
#include "../eh_hash.h"
#include "../eh_directory.h"
#include "../eh_bucket.h"
#include "../eh_split.h"
#include "../eh_insert_core.h"
#include "../eh_persist.h"

int main(void) {
    Directory *dir = directory_create(2);
    int32_t ids[] = {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23};
    int n = sizeof(ids) / sizeof(ids[0]);

    for (int i = 0; i < n; i++)
        eh_directory_insert(dir, ids[i], (int64_t) ids[i]);

    const char *path = "test_index.dat";

    assert(eh_directory_save(dir, path));
    printf("Test 1 OK: guardado en disco correctamente\n");

    Directory *loaded = eh_directory_load(path);
    assert(loaded != NULL);
    printf("Test 2 OK: cargado desde disco correctamente\n");

    assert(loaded->global_depth == dir->global_depth);
    assert(loaded->num_slots == dir->num_slots);
    printf("Test 3 OK: metadatos coinciden (gd=%d, slots=%d)\n",
           loaded->global_depth, loaded->num_slots);

    int all_found = 1;
    for (int i = 0; i < n; i++) {
        uint32_t h = hash_function(ids[i]);
        int idx = directory_index(loaded, h);
        Bucket *b = loaded->slots[idx];
        int64_t tid;
        if (!bucket_find(b, ids[i], &tid) || tid != ids[i]) {
            printf("  ERROR: clave %d no se recupero correctamente\n", ids[i]);
            all_found = 0;
        }
    }
    assert(all_found);
    printf("Test 4 OK: las 23 claves se recuperan correctamente tras cargar desde disco\n");

    remove(path);
    printf("\nTodos los tests de persistencia pasaron correctamente.\n");
    return 0;
}
