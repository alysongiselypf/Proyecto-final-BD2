#include "eh_hash.h"

uint32_t hash_function(int32_t key) {
    uint32_t k = (uint32_t)key;
    return k * 2654435761u;  // constante de Knuth
}

uint32_t get_bits(uint32_t h, int n_bits) {
    if (n_bits <= 0) return 0;
    return h & ((1u << n_bits) - 1);
}
