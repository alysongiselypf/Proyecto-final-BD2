#ifndef EH_HASH_H
#define EH_HASH_H

#include <stdint.h>

uint32_t hash_function(int32_t key);
uint32_t get_bits(uint32_t h, int n_bits);

#endif
