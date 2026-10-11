#include <stdio.h>
#include <assert.h>
#include "../eh_hash.h"

int main(void) {
    // Test 1: determinismo (misma clave -> mismo hash siempre)
    assert(hash_function(42) == hash_function(42));

    // Test 2: caso borde clave = 0
    uint32_t h0 = hash_function(0);
    printf("hash(0) = %u\n", h0);

    // Test 3: bits extraidos nunca exceden el rango esperado (gd=2 -> max 3)
    for (int32_t id = 1; id <= 1000; id++) {
        uint32_t bits = get_bits(hash_function(id), 2);
        assert(bits <= 3);
    }

    // Test 4: distribucion sobre los 23 medicamentos reales del dataset
    printf("\nDistribucion sobre medicamento.id (1..23), gd=2:\n");
    int conteo_slot[4] = {0, 0, 0, 0};
    for (int32_t id = 1; id <= 23; id++) {
        uint32_t h = hash_function(id);
        uint32_t bits = get_bits(h, 2);
        printf("  id=%2d  hash=%10u  slot=%d\n", id, h, bits);
        conteo_slot[bits]++;
    }
    printf("\nConteo por slot: [%d, %d, %d, %d]\n",
           conteo_slot[0], conteo_slot[1], conteo_slot[2], conteo_slot[3]);

    printf("\nTodos los tests pasaron correctamente.\n");
    return 0;
}
