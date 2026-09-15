#ifndef EH_PERSIST_H
#define EH_PERSIST_H

#include "eh_types.h"
#include <stdbool.h>

#define EH_INDEX_FILE_PATH "/var/lib/postgresql/eh_index.dat"

bool eh_directory_save(Directory *dir, const char *path);       // Fiorella
Directory *eh_directory_load(const char *path);                  // Ruth

#endif
