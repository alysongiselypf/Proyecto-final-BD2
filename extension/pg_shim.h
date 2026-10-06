#ifndef PG_SHIM_H
#define PG_SHIM_H
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

typedef uint32_t uint32;
typedef uint16_t uint16;
typedef uint8_t  uint8;
typedef int32_t  int32;

#define palloc malloc
#define palloc0(n) calloc(1, (n))
#define repalloc realloc
#define pfree free
#define elog(level, ...) ((void)0)
#endif
