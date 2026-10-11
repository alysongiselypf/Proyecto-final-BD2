# Diseño del Directorio — Extendible Hashing

## Propósito
El directorio es un arreglo de punteros a buckets, indexado por los bits menos
significativos del valor hash de la clave.

## Estructura de datos (C)

```c
typedef struct {
    int global_depth;        // gd: número de bits usados para indexar
    int num_slots;           // = 2^global_depth
    Bucket **slots;          // arreglo de punteros a buckets, tamaño num_slots
} Directory;
```

## Reglas de diseño
- `num_slots` siempre es una potencia de 2: `2^global_depth`.
- Varias entradas del directorio pueden apuntar al **mismo bucket** (esto pasa
  cuando `local_depth` de un bucket es menor que `global_depth` del directorio).
- Ejemplo: si `gd = 2` (4 slots) y un bucket tiene `ld = 1`, ese bucket es
  apuntado por 2 slots distintos (los que comparten el bit menos significativo,
  pero difieren en el segundo bit).

## Operación clave: `directory_index(hash, gd)`

```c
int idx = hash & ((1 << gd) - 1);  // toma los gd bits menos significativos
```

## Operación clave: duplicar el directorio (cuando `ld_bucket == gd`)

```c
void directory_double(Directory *dir) {
    int old_slots = dir->num_slots;
    dir->global_depth++;
    dir->num_slots = old_slots * 2;
    dir->slots = realloc(dir->slots, dir->num_slots * sizeof(Bucket*));
    // la mitad nueva copia los mismos punteros que la mitad vieja
    for (int i = 0; i < old_slots; i++) {
        dir->slots[old_slots + i] = dir->slots[i];
    }
}
```

## Inicialización
`gd = 2` (4 slots), como se definió en la propuesta — arranca con algo de
margen antes del primer split.

## Persistencia (para la Semana 6)
El directorio se serializa a disco como:
`[global_depth][num_slots][offset_bucket_1, offset_bucket_2, ...]`
— cada slot guarda el offset en el archivo binario donde está el bucket
correspondiente, no un puntero de memoria (los punteros no sobreviven un
reinicio).