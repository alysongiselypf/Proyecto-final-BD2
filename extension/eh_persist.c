#include "eh_persist.h"
#include <stdio.h>
#include <stdlib.h>

#define EH_MAGIC 0x45484632u  // "EHF2" - version 2 del formato (agrega campo 'id' al bucket)
/*
 * Guardado (Fiorella). Varios slots del directorio pueden compartir
 * el mismo bucket (punteros repetidos), asi que primero se identifica
 * la lista de buckets UNICOS antes de escribir, para no duplicar
 * datos en disco.
 */
bool eh_directory_save(Directory *dir, const char *path)
{
    FILE *f;
    int *slot_bucket_id;      // el ID real del bucket (no compactado)
    int i;
    uint32_t magic = EH_MAGIC;

    // Estructura temporal: mapa de id_real -> puntero, usando un arreglo
    // dimensionado al mayor id visto, para evitar busqueda O(n) por slot.
    int max_id = -1;
    for (i = 0; i < dir->num_slots; i++) {
        if (dir->slots[i]->id > max_id)
            max_id = dir->slots[i]->id;
    }

    Bucket **by_id = calloc(max_id + 1, sizeof(Bucket*));
    bool *seen = calloc(max_id + 1, sizeof(bool));
    int num_unique = 0;

    slot_bucket_id = malloc(sizeof(int) * dir->num_slots);

    for (i = 0; i < dir->num_slots; i++) {
        Bucket *b = dir->slots[i];
        slot_bucket_id[i] = b->id;
        if (!seen[b->id]) {
            seen[b->id] = true;
            by_id[b->id] = b;
            num_unique++;
        }
    }

    f = fopen(path, "wb");
    if (f == NULL) {
        free(slot_bucket_id); free(by_id); free(seen);
        return false;
    }

    fwrite(&magic, sizeof(uint32_t), 1, f);
    fwrite(&dir->global_depth, sizeof(int), 1, f);
    fwrite(&dir->num_slots, sizeof(int), 1, f);
    fwrite(slot_bucket_id, sizeof(int), dir->num_slots, f);
    fwrite(&num_unique, sizeof(int), 1, f);

    // Escribir cada bucket unico junto con su ID real, para poder
    // reconstruir la relacion slot -> bucket al cargar.
    for (i = 0; i <= max_id; i++) {
        if (!seen[i]) continue;
        Bucket *b = by_id[i];
        fwrite(&b->id, sizeof(int), 1, f);
        fwrite(&b->local_depth, sizeof(int), 1, f);
        fwrite(&b->count, sizeof(int), 1, f);
        fwrite(b->entries, sizeof(Entry), b->count, f);
    }

    fclose(f);
    free(slot_bucket_id);
    free(by_id);
    free(seen);
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
    int num_unique;
    int i;
    int max_id = -1;

    f = fopen(path, "rb");
    if (f == NULL)
        return NULL;

    if (fread(&magic, sizeof(uint32_t), 1, f) != 1 || magic != EH_MAGIC) {
        fclose(f);
        return NULL;
    }

    dir = malloc(sizeof(Directory));
    fread(&dir->global_depth, sizeof(int), 1, f);
    fread(&dir->num_slots, sizeof(int), 1, f);

    slot_bucket_id = malloc(sizeof(int) * dir->num_slots);
    fread(slot_bucket_id, sizeof(int), dir->num_slots, f);

    fread(&num_unique, sizeof(int), 1, f);

    for (i = 0; i < dir->num_slots; i++)
        if (slot_bucket_id[i] > max_id) max_id = slot_bucket_id[i];

    Bucket **by_id = calloc(max_id + 1, sizeof(Bucket*));

    for (i = 0; i < num_unique; i++) {
        int stored_id;
        Bucket *b = malloc(sizeof(Bucket));
        fread(&stored_id, sizeof(int), 1, f);
        b->id = stored_id;
        fread(&b->local_depth, sizeof(int), 1, f);
        fread(&b->count, sizeof(int), 1, f);
        fread(b->entries, sizeof(Entry), b->count, f);
        by_id[stored_id] = b;
    }

    dir->slots = malloc(sizeof(Bucket*) * dir->num_slots);
    for (i = 0; i < dir->num_slots; i++)
        dir->slots[i] = by_id[slot_bucket_id[i]];

    free(slot_bucket_id);
    free(by_id);
    fclose(f);
    return dir;
}
