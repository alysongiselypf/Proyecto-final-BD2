# Resultados comparativos

## Tiempo de búsqueda (W1 - claves existentes)

| Dataset | n | Sin índice | B-tree | Extendible Hashing |
|---|---|---|---|---|
| D1 (secuencial) | 100,000 | 0.082s | 0.084s | 7.076s |
| D1 (secuencial) | 500,000 | 0.151s | 0.099s | 11.601s |
| D1 (secuencial) | 1,000,000 | 0.197s | 0.117s | 11.564s |
| D2 (aleatorio) | 100,000 | 0.107s | 0.130s | 11.877s |
| D2 (aleatorio) | 500,000 | 0.142s | 0.108s | 11.709s |
| D2 (aleatorio) | 1,000,000 | 0.197s | 0.119s | 11.953s |

*(Ver `graficos/busqueda_w1_*.png` para la visualización)*

## Tamaño del índice en disco

| Dataset | n | B-tree | Extendible Hashing | Diferencia |
|---|---|---|---|---|
| D1/D2 | 100,000 | 2,208.0 KB | ~1,635 KB | EH ~26% más pequeño |
| D1/D2 | 500,000 | 10,992.0 KB | ~8,116 KB | EH ~26% más pequeño |
| D1/D2 | 1,000,000 | 21,960.0 KB | ~16,231 KB | EH ~26% más pequeño |

## Tiempo de construcción

| Dataset | n | B-tree | Extendible Hashing |
|---|---|---|---|
| D1 | 1,000,000 | 0.656s | 11.334s |
| D2 | 1,000,000 | 0.722s | 14.183s |

## Tiempo de inserción (W3 - 10% adicional)

| Dataset | n | Sin índice | Extendible Hashing | Overhead relativo |
|---|---|---|---|---|
| D1 | 1,000,000 | 119.451s | 130.869s | +9.6% |
| D2 | 1,000,000 | 119.547s | 127.813s | +6.9% |

## Discusión: cuándo funciona mejor o peor cada alternativa

**Extendible Hashing es superior en tamaño en disco.** En los 6
casos evaluados, la estructura implementada ocupa consistentemente
alrededor de un 26-27% menos espacio que B-tree, gracias a la
ausencia de overhead de balanceo y punteros de nodos internos. Esto
respalda uno de los argumentos teóricos centrales de Extendible
Hashing frente a estructuras basadas en árboles: menor huella de
almacenamiento para el mismo conjunto de claves.

**B-tree es superior en tiempo de construcción y en búsqueda medida
por lotes.** La brecha de tiempo de construcción (hasta 20× más
lento en EH sobre 1,000,000 de registros) se explica por la ausencia
de un modo de carga masiva optimizado en la extensión — cada
inserción durante la construcción pasa por el ciclo completo de
cálculo de hash, localización de bucket y posible split, mientras
que PostgreSQL implementa algoritmos de construcción bulk altamente
optimizados para B-tree en su núcleo.

**La comparación de tiempo de búsqueda requiere lectura cuidadosa.**
La diferencia de casi dos órdenes de magnitud entre EH (~11-12s) y
B-tree/sin-índice (~0.1-0.2s) para 10,000 consultas no refleja una
deficiencia algorítmica del hashing extensible, que teóricamente
ofrece complejidad O(1) para búsquedas por igualdad — mejor que la
complejidad O(log n) de B-tree. La causa real es metodológica: las
mediciones de B-tree y sin-índice se realizaron con una única
consulta SQL batch (`WHERE id = ANY(array)`), mientras que
`eh_search()` se invoca una vez por clave, sin equivalente batch en
el diseño actual de la extensión. Esta es una limitación de
implementación, no del algoritmo subyacente, y se documenta
explícitamente como amenaza a la validez de esta comparación
específica.

**En inserción, la comparación es más directa y favorable a
Extendible Hashing.** Al medirse ambos escenarios bajo el mismo
patrón de invocación (una operación por fila), el overhead de
mantener el índice de EH sincronizado resultó moderado (entre 7% y
10% adicional sobre la inserción directa), sugiriendo que la
estructura es viable para cargas de trabajo con inserciones
frecuentes, sin el costo prohibitivo que la comparación de búsqueda
podría sugerir a primera vista.
