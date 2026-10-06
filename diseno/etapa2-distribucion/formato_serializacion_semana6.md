# Formato de serialización binaria — Semana 6

## Ubicación del archivo
`/var/lib/postgresql/eh_index.dat`, dentro del volumen Docker `pgdata`,
por lo que sobrevive a `docker compose down` (sin `-v`) y a reinicios
del contenedor.

## Estructura del archivo (little-endian, tal como lo escribe la CPU)

| Campo | Tipo | Descripción |
|---|---|---|
| magic | uint32 | Constante `0x45484631` ("EHF1"), identifica el formato |
| global_depth | int | Profundidad global del directorio |
| num_slots | int | Cantidad de slots del directorio |
| slot_bucket_id[] | int × num_slots | A qué bucket único apunta cada slot |
| num_unique_buckets | int | Cantidad de buckets únicos (deduplicados) |
| Para cada bucket: local_depth | int | Profundidad local del bucket |
| Para cada bucket: count | int | Entradas ocupadas en el bucket |
| Para cada bucket: entries[] | Entry × count | Pares (key, tid) |

## Por qué se deduplican los buckets
Varios slots del directorio pueden apuntar al mismo bucket físico
(cuando `local_depth < global_depth`). Guardar cada bucket una sola
vez, y referenciarlo por un ID entero desde el arreglo de slots,
evita duplicar datos en disco y mantiene la relación de punteros
compartidos al reconstruir la estructura en memoria.

## Mecanismo de carga automática
Se utiliza el hook `_PG_init()` de PostgreSQL, que se ejecuta
automáticamente cada vez que un proceso backend (una conexión nueva)
carga la librería `eh_index.so` por primera vez. Esto permite que el
índice esté disponible inmediatamente en conexiones nuevas sin
requerir una llamada manual a `eh_load()`, resolviendo parcialmente
la limitación de la Semana 4 (pérdida del índice entre conexiones).

## Autoguardado
`eh_build()` ahora guarda automáticamente a disco al finalizar la
construcción. El trigger `eh_sync_trigger` también guarda a disco
tras cada inserción individual vía `INSERT INTO medicamento`. Esto
significa que, en el flujo normal de uso, el archivo en disco siempre
refleja el estado más reciente del índice sin intervención manual.
