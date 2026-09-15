#ifndef EH_DIRECTORY_H
#define EH_DIRECTORY_H

#include "eh_types.h"

Directory *directory_create(int initial_global_depth);
void directory_free(Directory *dir);
int directory_index(Directory *dir, uint32_t hash);
void directory_double(Directory *dir);

#endif
