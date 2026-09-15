# Casos edge — Semana 5 (Split y duplicación)

## Overflow (límite de splits)

`eh_directory_insert()` incluye un límite de seguridad de 32 iteraciones
del ciclo insertar→split→reintentar. Esto previene un loop infinito en
caso de un bug donde el split no lograra liberar espacio en el bucket
destino. Con claves enteras únicas y una función hash de 32 bits, este
límite es más que suficiente en la práctica: en el peor caso teórico,
solo se agotaría si existieran múltiples claves cuyo hash produce
exactamente los mismos bits en las primeras 32 posiciones, lo cual es
estadísticamente insignificante para el tamaño de dataset del proyecto
(hasta 1,000,000 de registros en la Etapa II).

Si el límite se alcanza, `eh_directory_insert()` retorna `-1` en vez de
fallar silenciosamente o colgar el proceso, y `eh_insert()` lo reporta
como `WARNING` sin interrumpir la sesión de PostgreSQL.

## Duplicados

`bucket_contains()` se verifica *antes* de intentar cualquier split, así
que insertar una clave ya existente nunca dispara una división de
bucket innecesaria — se retorna `0` (duplicado) de inmediato. Esto se
valida en el Test 2 de `test_split.c`.

## Consistencia tras múltiples splits

Un mismo bucket puede requerir varios splits consecutivos si, tras
dividirse, el sub-bucket resultante también queda lleno con las claves
redistribuidas. `eh_directory_insert()` maneja esto de forma natural
porque el `while` reintenta la inserción completa (recalculando hash e
índice) después de cada split, en lugar de asumir que un solo split
basta.

## Relación con la limitación de la Semana 4

El comportamiento "bucket lleno" documentado la semana pasada (19 de
23 claves omitidas) queda resuelto por completo en esta semana: al
insertar mediante `eh_directory_insert()`, el propio mecanismo de
split y duplicación de directorio crea automáticamente los buckets
adicionales necesarios, permitiendo insertar el dataset completo.
