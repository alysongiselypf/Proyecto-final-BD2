#include <stdio.h>
#include <assert.h>
#include "../eh_types.h"
#include "../eh_hash.h"
#include "../eh_directory.h"
#include "../eh_bucket.h"
#include "../eh_split.h"
#include "../eh_insert_core.h"

int main(void) {
    Directory *dir = directory_create(2); // gd=2, arranca con bucket compartido

    int32_t ids[] = {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23};
    int n = sizeof(ids) / sizeof(ids[0]);
    int inserted = 0, duplicates = 0, failed = 0;

    for (int i = 0; i < n; i++) {
        int r = eh_directory_insert(dir, ids[i], (int64_t) ids[i]);
        if (r == 1) inserted++;
        else if (r == 0) duplicates++;
        else failed++;
    }

    printf("Insertados: %d, duplicados: %d, fallidos: %d\n", inserted, duplicates, failed);
    printf("Profundidad global final: %d (num_slots=%d)\n", dir->global_depth, dir->num_slots);

    // Test 1: las 23 claves deben insertarse SIN quedarse en "bucket lleno"
    assert(inserted == 23);
    assert(duplicates == 0);
    assert(failed == 0);
    printf("Test 1 OK: todas las claves se insertaron; el split resolvio los buckets llenos\n");

    // Test 2: reinsertar una clave existente se detecta como duplicado
    int r = eh_directory_insert(dir, 1, 999);
    assert(r == 0);
    printf("Test 2 OK: reinsertar clave existente se detecta como duplicado\n");

    // Test 3: las 23 claves deben poder buscarse correctamente despues de los splits
    int all_found = 1;
    for (int i = 0; i < n; i++) {
        uint32_t h = hash_function(ids[i]);
        int idx = directory_index(dir, h);
        Bucket *b = dir->slots[idx];
        int64_t tid;
        if (!bucket_find(b, ids[i], &tid)) {
            printf("  ERROR: no se encontro la clave %d tras el split\n", ids[i]);
            all_found = 0;
        }
    }
    assert(all_found);
    printf("Test 3 OK: las 23 claves se encuentran correctamente despues de todos los splits\n");

    // Test 4: la profundidad global debio crecer respecto al valor inicial (2),
    // confirmando que hubo al menos una duplicacion de directorio
    assert(dir->global_depth > 2);
    printf("Test 4 OK: el directorio se duplico al menos una vez (gd final=%d > gd inicial=2)\n",
           dir->global_depth);

    printf("\nTodos los tests de split/duplicacion pasaron correctamente.\n");
    return 0;
}
