#ifndef EH_INSERT_CORE_H
#define EH_INSERT_CORE_H

#include "eh_types.h"

// Retorna: 1 = insertado, 0 = duplicado (no se inserta), -1 = error (overflow de splits)
int eh_directory_insert(Directory *dir, int32_t key, int64_t tid);

#endif
