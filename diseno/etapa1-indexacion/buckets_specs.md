# Diseño de Buckets — Extendible Hashing

## Propósito
Cada bucket es una página de capacidad fija que guarda pares `(clave, TID)`.

## Estructura de datos (C)

```c
#define BUCKET_CAPACITY 4   // capacidad fija b (ajustable, 4 es razonable para pruebas)

typedef struct {
    int32_t key;      // medicamento.id
    int64_t tid;       // referencia al registro en PostgreSQL (ctid o id)
} Entry;

typedef struct {
    int local_depth;              // ld ≤ gd
    int count;                    // cuántas entradas ocupadas (0..BUCKET_CAPACITY)
    Entry entries[BUCKET_CAPACITY];
} Bucket;
```

## Reglas de diseño
- `local_depth` empieza en `global_depth` inicial del directorio (2).
- Un bucket está **lleno** cuando `count == BUCKET_CAPACITY` — ahí se dispara
  el split.
- Las claves dentro de un bucket comparten los `local_depth` bits menos
  significativos de su hash (por eso terminan juntas en el mismo bucket).

## Operación clave: split de un bucket

Cuando el bucket está lleno y llega una nueva inserción:

```c
void bucket_split(Bucket *old_bucket, Bucket *new_bucket, int bit_position) {
    new_bucket->local_depth = old_bucket->local_depth + 1;
    old_bucket->local_depth += 1;
    new_bucket->count = 0;

    // redistribuir las entradas actuales según el nuevo bit
    Entry temp[BUCKET_CAPACITY];
    int temp_count = old_bucket->count;
    memcpy(temp, old_bucket->entries, sizeof(Entry) * temp_count);
    old_bucket->count = 0;

    for (int i = 0; i < temp_count; i++) {
        uint32_t h = hash_function(temp[i].key);
        if ((h >> bit_position) & 1) {
            new_bucket->entries[new_bucket->count++] = temp[i];
        } else {
            old_bucket->entries[old_bucket->count++] = temp[i];
        }
    }
}
```

## Dos casos al insertar en bucket lleno
(esto es lo que definieron en la propuesta)

1. `ld_bucket < gd_directorio` → solo se divide el bucket (split local), no
   hace falta tocar el directorio. Se actualizan los slots del directorio que
   apuntaban al bucket viejo para que la mitad ahora apunte al bucket nuevo.
2. `ld_bucket == gd_directorio` → primero se duplica el directorio
   (`directory_double`), y luego se hace el split del bucket como en el caso 1.

## Persistencia
Cada bucket se serializa como bloque de tamaño fijo:
`[local_depth][count][entry_1]...[entry_4]`
— tamaño fijo facilita calcular offsets en el archivo binario sin necesidad de
índice adicional.