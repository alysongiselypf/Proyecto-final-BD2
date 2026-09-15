#include "eh_persist.h"
#include <stdio.h>
#include <stdlib.h>

#define EH_MAGIC 0x45484631u  // "EHF1", identifica el formato del archivo

/*
 * Guardado (Fiorella). Varios slots del directorio pueden compartir
 * el mismo bucket (punteros repetidos), asi que primero se identifica
 * la lista de buckets UNICOS antes de escribir, para no duplicar
 * datos en disco.
 */
bool eh_directory_save(Directory *dir, const char *path)
{
    FILE *f;
    Bucket **unique;
    int *slot_bucket_id;
    int num_unique = 0;
    int i, j;
    uint32_t magic = EH_MAGIC;

    if (dir == NULL)
        return false;

    unique = malloc(sizeof(Bucket*) * dir->num_slots);
    slot_bucket_id = malloc(sizeof(int) * dir->num_slots);

    for (i = 0; i < dir->num_slots; i++) {
        int found_id = -1;
        for (j = 0; j < num_unique; j++) {
            if (unique[j] == dir->slots[i]) { found_id = j; break; }
        }
        if (found_id == -1) {
            unique[num_unique] = dir->slots[i];
            found_id = num_unique;
            num_unique++;
        }
        slot_bucket_id[i] = found_id;
    }

    f = fopen(path, "wb");
    if (f == NULL) {
        free(unique); free(slot_bucket_id);
        return false;
    }

    fwrite(&magic, sizeof(uint32_t), 1, f);
    fwrite(&dir->global_depth, sizeof(int), 1, f);
    fwrite(&dir->num_slots, sizeof(int), 1, f);
    fwrite(slot_bucket_id, sizeof(int), dir->num_slots, f);
    fwrite(&num_unique, sizeof(int), 1, f);

    for (j = 0; j < num_unique; j++) {
        Bucket *b = unique[j];
        fwrite(&b->local_depth, sizeof(int), 1, f);
        fwrite(&b->count, sizeof(int), 1, f);
        fwrite(b->entries, sizeof(Entry), b->count, f);
    }

    fclose(f);
    free(unique);
    free(slot_bucket_id);
    return true;
}

/*
 * Carga (Ruth). Reconstruye primero los buckets unicos, y luego
 * reconecta cada slot del directorio a su bucket correspondiente
 * usando los IDs guardados en el archivo.
 */
Directory *eh_directory_load(const char *path)
{
    FILE *f;
    uint32_t magic;
    Directory *dir;
    int *slot_bucket_id;
    Bucket **buckets;
    int num_unique;
    int i;

    f = fopen(path, "rb");
    if (f == NULL)
        return NULL;  // no hay indice persistido todavia (arranque en frio)

    if (fread(&magic, sizeof(uint32_t), 1, f) != 1 || magic != EH_MAGIC) {
        fclose(f);
        return NULL;  // archivo corrupto o de formato incompatible
    }

    dir = malloc(sizeof(Directory));
    fread(&dir->global_depth, sizeof(int), 1, f);
    fread(&dir->num_slots, sizeof(int), 1, f);

    slot_bucket_id = malloc(sizeof(int) * dir->num_slots);
    fread(slot_bucket_id, sizeof(int), dir->num_slots, f);

    fread(&num_unique, sizeof(int), 1, f);
    buckets = malloc(sizeof(Bucket*) * num_unique);

    for (i = 0; i < num_unique; i++) {
        Bucket *b = malloc(sizeof(Bucket));
        fread(&b->local_depth, sizeof(int), 1, f);
        fread(&b->count, sizeof(int), 1, f);
        fread(b->entries, sizeof(Entry), b->count, f);
        buckets[i] = b;
    }

    dir->slots = malloc(sizeof(Bucket*) * dir->num_slots);
    for (i = 0; i < dir->num_slots; i++)
        dir->slots[i] = buckets[slot_bucket_id[i]];

    free(slot_bucket_id);
    free(buckets);
    fclose(f);
    return dir;
}
