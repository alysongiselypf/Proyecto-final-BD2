# Diseño e implementación

## Arquitectura general
La estructura de Extendible Hashing se implementó como una extensión
nativa de PostgreSQL en lenguaje C, compilada como biblioteca
compartida (`eh_index.so`) y registrada mediante el mecanismo estándar
de extensiones (`CREATE EXTENSION`), cumpliendo el requisito de
integración real con el DBMS establecido en la sección 5.2 de la
rúbrica — el código se ejecuta dentro del motor de PostgreSQL, no
como un programa externo que solo envía consultas.

## Componentes principales

**Directorio:** arreglo dinámico de punteros a buckets, indexado por
los bits menos significativos del hash de la clave. Soporta
duplicación (`directory_double`) cuando la profundidad local de un
bucket alcanza la profundidad global del directorio.

**Buckets:** páginas de capacidad fija (`BUCKET_CAPACITY = 64`,
ajustado durante la Semana 9 tras detectar limitaciones de
rendimiento con la capacidad inicial de 4) que almacenan pares
clave-TID. Cada bucket mantiene su propia profundidad local y un
identificador único, usado para la serialización eficiente a disco.

**Función hash:** función multiplicativa de Knuth
(`hash = clave * 2654435761 mod 2^32`), determinística y validada
mediante tests unitarios sobre distribución real del dataset.

**Persistencia:** serialización binaria del directorio y buckets a
un archivo en el volumen persistente de PostgreSQL, con
deduplicación de buckets compartidos y carga automática mediante el
hook `_PG_init()` en cada nueva conexión.

## Funciones expuestas a PostgreSQL

| Función | Propósito |
|---|---|
| `eh_build()` | Construye el índice sobre la tabla `medicamento` |
| `eh_build_table(tabla, columna)` | Construye el índice sobre cualquier tabla/columna (usada para benchmarking) |
| `eh_search(clave)` | Búsqueda por igualdad, retorna TID o NULL |
| `eh_insert(clave)` | Inserción individual con split automático |
| `eh_save()` / `eh_load()` | Persistencia manual a/desde disco |
| `eh_index_size()` | Tamaño del índice persistido, en bytes |
| `eh_sync_trigger()` | Trigger `AFTER INSERT` para sincronización automática |

## Decisiones de diseño relevantes tomadas durante la Semana 9

Durante la ejecución de las pruebas de rendimiento se identificaron y
corrigieron varios problemas de implementación no evidentes con
datasets pequeños:

1. El algoritmo de `bucket_split()` inicialmente recorría todo el
   directorio en cada split, generando un costo no lineal con
   datasets grandes. La corrección (recorrido completo pero correcto,
   verificado contra un intento previo de optimización que resultó
   incorrecto tras duplicaciones del directorio) prioriza la
   corrección sobre la velocidad teórica máxima, en línea con el
   principio de la rúbrica de valorar "una solución correcta,
   entendida y reproducible" (sección 11) por sobre una optimización
   compleja no verificada.
2. Se aumentó `BUCKET_CAPACITY` de 4 a 64, reduciendo drásticamente
   el número de buckets y operaciones de split necesarias para
   datasets grandes, sin alterar la corrección del algoritmo.
3. Se corrigieron dos problemas de gestión de memoria (fuga por
   contador de identificadores no reiniciado, y liberación incompleta
   de buckets al reconstruir el índice), verificados mediante
   monitoreo de uso de memoria del contenedor (`docker stats`)
   durante la ejecución de las pruebas.
