#include <stdio.h>
#include <assert.h>
#include "../eh_types.h"
#include "../eh_hash.h"
#include "../eh_directory.h"
#include "../eh_bucket.h"

int main(void) {
    Directory *dir = directory_create(2);

    // En esta version (Semana 3-4), todos los slots comparten un unico
    // bucket, asi que insertamos directo en ese bucket compartido.
    Bucket *shared = dir->slots[0];

    assert(bucket_insert_raw(shared, 1, 100));
    assert(bucket_insert_raw(shared, 2, 200));

    // Test 1: busqueda exitosa
    int64_t tid;
    int found = bucket_find(shared, 1, &tid);
    assert(found == 1);
    assert(tid == 100);
    printf("Test 1 OK: clave=1 encontrada, tid=%lld\n", (long long) tid);

    // Test 2: busqueda no exitosa (clave ausente)
    found = bucket_find(shared, 999, &tid);
    assert(found == 0);
    printf("Test 2 OK: clave=999 correctamente no encontrada\n");

    // Test 3: bucket_contains detecta duplicados
    assert(bucket_contains(shared, 2) == true);
    assert(bucket_contains(shared, 500) == false);
    printf("Test 3 OK: deteccion de duplicados funciona\n");

    // Test 4: directory_index es consistente para una misma clave
    uint32_t h = hash_function(1);
    int idx1 = directory_index(dir, h);
    int idx2 = directory_index(dir, h);
    assert(idx1 == idx2);
    printf("Test 4 OK: directory_index es determinista (idx=%d)\n", idx1);

    // Test 5: bucket lleno rechaza nuevas inserciones (edge case)
    Bucket *b2 = bucket_create(2);
    assert(bucket_insert_raw(b2, 10, 10));
    assert(bucket_insert_raw(b2, 11, 11));
    assert(bucket_insert_raw(b2, 12, 12));
    assert(bucket_insert_raw(b2, 13, 13));
    assert(bucket_insert_raw(b2, 14, 14) == false); // bucket ya lleno
    printf("Test 5 OK: bucket lleno rechaza insercion correctamente\n");

    printf("\nTodos los tests de busqueda pasaron correctamente.\n");
    return 0;
}
