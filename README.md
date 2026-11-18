# Extendible Hashing sobre PostgreSQL

**Proyecto Final de Bases de Datos II (CS272), 2026-II**  
Universidad Católica San Pablo · Ciencia de la Computación  
**Docente:** Regina Paola Ticona Herrera  
**Estructura de indexación implementada:** Extendible Hashing (hashing dinámico mediante directorio y buckets).

---

## Contenido

1. [Descripción general](#1-descripción-general)
2. [Equipo](#2-equipo)
3. [Requisitos](#3-requisitos)
4. [Instalación y verificación](#4-instalación-y-verificación)
5. [Modos de ejecución](#5-modos-de-ejecución)
6. [Guía de demostración](#6-guía-de-demostración)
7. [Fundamentos de la estructura](#7-fundamentos-de-la-estructura)
8. [Desarrollo del proyecto por semanas](#8-desarrollo-del-proyecto-por-semanas)
9. [Arquitectura e implementación](#9-arquitectura-e-implementación)
10. [Pruebas unitarias](#10-pruebas-unitarias)
11. [Evaluación experimental](#11-evaluación-experimental)
12. [Escenario distribuido](#12-escenario-distribuido)
13. [Estructura del repositorio](#13-estructura-del-repositorio)
14. [Limitaciones](#14-limitaciones)
15. [Recursos externos y uso de herramientas de IA](#15-recursos-externos-y-uso-de-herramientas-de-ia)
16. [Referencias](#16-referencias)

---

## 1. Descripción general

Este proyecto implementa **Extendible Hashing** como estructura de indexación alternativa a B-tree. La estructura se desarrolló en C y se integró en PostgreSQL 18.6 como una extensión nativa, invocable desde SQL mediante `CREATE FUNCTION ... LANGUAGE C`.

El código se ejecuta dentro del proceso del servidor y obtiene los datos de las tablas mediante SPI.

El trabajo se organiza en dos etapas:

| Etapa | Semanas | Resultado |
|---|---|---|
| I. Indexación | 1 a 5 | Estructura implementada e integrada con PostgreSQL; construcción, búsqueda, inserción y split. |
| II. Evaluación y distribución | 6 a 10 | Persistencia del índice, comparación experimental frente a B-tree y ausencia de índice, y pruebas de un escenario distribuido de tres nodos. |

El informe final se encuentra en `etapa2-evaluacion-distribucion/informe/`:

- `Informe_Final_Extendible_Hashing.docx`
- `informe_etapa2.md`

## 2. Equipo

| Integrante | Área principal |
|---|---|
| Alyson Perez Flores | Entorno, integración con PostgreSQL, persistencia y benchmark de búsqueda. |
| Rodrigo Sierra Huaracha | Núcleo de la estructura, generación y validación de datos. |
| Ruth Benique Huaman | Inserción y split, medición de inserciones y parte distribuida. |

## 3. Requisitos

| Componente | Uso |
|---|---|
| Docker Desktop (contenedores Linux) | Obligatorio. Verificar con `docker --version`. |
| Git | Obligatorio. |
| Python 3.10 o superior | Benchmarks y parte distribuida. |
| gcc | Solo para ejecutar los tests unitarios fuera de Docker. |

Instalación de dependencias de Python:

```bash
pip install -r requirements.txt
```

## 4. Instalación y verificación

### 4.1 Clonar el repositorio

```bash
git clone https://github.com/alysongiselypf/Proyecto-final-BD2.git
cd Proyecto-final-BD2
```

### 4.2 Levantar el entorno

```bash
docker compose up -d --build
```

Este comando construye la imagen de PostgreSQL 18.6, compila e instala la extensión `eh_index` y carga el esquema base con 23 registros en la tabla `medicamento`.

### 4.3 Verificación

```bash
docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "SELECT eh_build();"

docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "SELECT eh_search(1);"

docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "SELECT eh_search(9999);"
```


Resultados esperados:

| Consulta | Resultado |
|---|---|
| `eh_build()` | `t`, con `gd=5, slots=32, insertados=23, omitidos_duplicado=0, fallidos=0`. |
| `eh_search(1)` | `1`: identificador almacenado. |
| `eh_search(9999)` | `NULL`: la clave no existe. |

## 5. Modos de ejecución

El tamaño del bucket es un parámetro de compilación.

- **Capacidad 4:** modo demostración, permite observar los splits con 23 registros.
- **Capacidad 64:** modo mediciones, utilizado para los experimentos.

### 5.1 Modo demostración (buckets de 4 entradas)

Ejecutar:

```bash
docker compose up -d --build
```

Luego:

```sql
SELECT eh_build();
```

Resultado esperado:

```text
gd=5, slots=32
```

### 5.2 Modo mediciones (buckets de 64 entradas)

En PowerShell:

```powershell
$env:BUCKET_CAPACITY = 64
docker compose down -v
docker compose build
docker compose up -d --wait
```

En Bash:

```bash
export BUCKET_CAPACITY=64
docker compose down -v
docker compose build
docker compose up -d --wait
```

Con capacidad 64, `SELECT eh_build();` produce `gd=2, slots=4`.

A continuación, desde `etapa2-evaluacion-distribucion/datasets/workloads`:

```bash
pip install -r requirements.txt

python benchmark_runner.py 100000 500000 1000000

python measure_insertion.py 100000 500000 1000000
```

Los scripts realizan:

- Búsqueda, construcción y medición del tamaño del índice.
- Medición de inserciones.
- Evaluación con diferentes cantidades de claves.

**Consideraciones:**

- Los datos se generan con los scripts de `datasets/generators` y `datasets/workloads`, utilizando la semilla 272.
- Los datos se validan con `datasets/validate/check_workloads.py`.
- Los archivos CSV no se versionan.
- Los resultados se almacenan en `datasets/output/resultados_*.json`.
- Los scripts deben ejecutarse desde `datasets/workloads`, porque utilizan rutas relativas.
- Las corridas completas pueden ser prolongadas, especialmente el escenario sin índice con 1 000 000 de claves.

Para regresar al modo demostración:

```powershell
Remove-Item Env:BUCKET_CAPACITY
docker compose down -v
docker compose build
docker compose up -d --wait
```

### 5.3 Escenario distribuido

Desde `etapa2-evaluacion-distribucion/distributed`:

```bash
docker compose -f docker-compose-distributed.yml up -d --wait

python fragment_data.py rango
python run_distributed_tests.py rango

python fragment_data.py hash
python run_distributed_tests.py hash

python run_distributed_tests.py comparar
```

Para una prueba rápida con esperas reducidas, definir antes:

```bash
LATENCIA_ESCALA=0.05
REPS=1
N_OPS=100
```

## 6. Guía de demostración

Los siguientes procedimientos permiten verificar el funcionamiento de la estructura.

| Operación | Procedimiento | Resultado esperado |
|---|---|---|
| Construir índice | `SELECT eh_build();` | `t`, `gd=5`, 32 slots y 23 registros. |
| Buscar clave existente | `SELECT eh_search(1);` | `1`. |
| Buscar clave inexistente | `SELECT eh_search(9999);` | `NULL`. |
| Insertar y recuperar | `SELECT eh_insert(200);` y luego `SELECT eh_search(200);` | `t` y `200`. |
| Insertar duplicado | `SELECT eh_insert(200);` nuevamente. | `f` y aviso de clave existente. |
| Verificar persistencia | Reiniciar PostgreSQL y buscar `200`. | `200`, sin reconstruir el índice. |
| Reiniciar entorno | `docker compose down -v` y volver a levantarlo. | El índice vuelve a su estado inicial. |
| Verificar trigger | Insertar un medicamento nuevo y consultar su ID. | La clave se sincroniza y persiste. |
| Consultar tamaño | `SELECT eh_index_size();` | Tamaño del índice en bytes. |
| Modificar capacidad | Procedimiento de la sección 5.2. | La profundidad cambia de `gd=5` a `gd=2`. |
| Ejecutar tests | Sección 10. | Todas las pruebas aprobadas. |
| Contrastar B-tree | Sección 9.4. | `Seq Scan` frente a `Index Scan`. |

### Observaciones

- Después de ejecutar `docker compose down -v`, debe reconstruirse el índice con `SELECT eh_build();`.
- Si se inserta una clave que ya existe, el resultado será `f`.
- El trigger implementado cubre únicamente operaciones `INSERT`.
- Si se elimina una fila de la tabla, su clave permanece en el índice hasta reconstruirlo con `eh_build()`.

## 7. Fundamentos de la estructura

Extendible Hashing, propuesto por Fagin et al. (1979), mantiene un directorio de punteros y buckets que permiten almacenar y recuperar claves mediante una función hash.

El directorio contiene \(2^{gd}\) punteros, donde `gd` representa la profundidad global.

Cada bucket tiene una profundidad local (`ld`) y almacena pares clave-valor.

### 7.1 Organización del directorio y buckets

```text
                         DIRECTORIO (global_depth = gd)
                    2^gd punteros, indexados por los
                    gd bits menos significativos del hash

   slot 000  slot 001  slot 010  slot 011  slot 100  slot 101  slot 110  slot 111
      |          |         |         |         |         |         |         |
      v          v         v         v         v         v         v         v
   +------+   +------+  +------+  +------+  +------+  +------+  +------+  +------+
   |Bucket|   |Bucket|  |Bucket|  |Bucket|  |Bucket|  |Bucket|  |Bucket|  |Bucket|
   |  A   |   |  B   |  |  B   |  |  C   |  |  A   |  |  B   |  |  B   |  |  C   |
   | ld=3 |   | ld=2 |  | ld=2 |  | ld=3 |  | ld=3 |  | ld=2 |  | ld=2 |  | ld=3 |
   +------+   +------+  +------+  +------+  +------+  +------+  +------+  +------+
```

Varios slots pueden apuntar al mismo bucket cuando la profundidad local es menor que la profundidad global (`ld < gd`).

### 7.2 Operaciones principales

| Operación | Descripción |
|---|---|
| Búsqueda | Calcula el hash, obtiene el slot correspondiente y busca la clave dentro del bucket. |
| Inserción | Localiza el bucket e inserta la entrada si existe espacio. |
| Split local | Divide un bucket lleno y redistribuye sus entradas según el siguiente bit del hash. |
| Duplicación del directorio | Duplica el número de slots cuando `ld = gd` y posteriormente realiza el split. |

### 7.3 Casos de división

**Caso 1: `local_depth < global_depth`**

Se realiza un split local.

- El bucket se divide en dos.
- Las entradas se redistribuyen según el bit adicional del hash.
- Solo se actualizan los slots que apuntaban al bucket dividido.

**Caso 2: `local_depth == global_depth`**

Se duplica el directorio y se realiza el split.

- El directorio pasa de \(2^{gd}\) a \(2^{gd+1}\) slots.
- Los nuevos slots copian los punteros anteriores.
- Se ejecuta el split local.

### 7.4 Función hash

Se utiliza la función multiplicativa de Knuth:

```text
h(k) = k * 2654435761 mod 2^32
```

Se utilizan los bits menos significativos para determinar el slot del directorio.

Sobre los 23 registros de la tabla `medicamento`, la distribución inicial en cuatro slots fue de:

```text
5 / 6 / 6 / 6
```

### 7.5 Pseudocódigo

```text
BUSCAR(k):
    b = directorio[slot(k)]

    para cada entrada e en b:
        si e.clave == k:
            devolver e.valor

    devolver NULL


INSERTAR(k, v):
    si BUSCAR(k) != NULL:
        rechazar (duplicado)

    repetir (máximo 32 iteraciones):

        b = directorio[slot(k)]

        si b no está lleno:
            agregar (k, v) a b
            terminar

        si b.ld == gd:
            DUPLICAR_DIRECTORIO()

        SPLIT(b)

    si se agotan las iteraciones:
        reportar bucket lleno
```

### 7.6 Comparación conceptual con B-tree

| Criterio | Extendible Hashing | B-tree |
|---|---|---|
| Consultas soportadas | Solo igualdad (=) | Igualdad y rango |
| Búsqueda | O(1) promedio; peor caso O(capacidad del bucket) | O(log n) |
| Inserción | O(1) amortizado; mayor costo con splits en cadena | O(log n) |
| Crecimiento | Split y duplicación dinámica | Balanceo automático |
| Orden de claves | No mantiene orden | Mantiene orden total |
| Uso ideal | Búsquedas por clave exacta | Rangos, ordenamiento y consultas flexibles |

La principal ventaja de Extendible Hashing es el acceso directo a las claves mediante el hash.

Su principal limitación es que no mantiene un orden entre las claves, por lo que no permite resolver consultas por rango.

## 8. Desarrollo del proyecto por semanas

Esta sección documenta la evolución de la implementación durante la primera etapa del proyecto.

### Semana 1 — Propuesta inicial

Se definió Extendible Hashing como estructura de indexación y se presentó la propuesta formal.

Se incluyeron:

- Motivación de la estructura.
- Referencias bibliográficas.
- Representación mediante directorio y buckets.
- Tipo de clave: `INTEGER`, específicamente `medicamento.id`.
- Estrategia de integración con PostgreSQL mediante una extensión en C.
- Riesgos técnicos identificados.
- Plan de trabajo semanal.

**Archivo:** `Propuesta_Inicial.pdf`.

### Semana 2 — Entorno y prueba de concepto

Se configuró un proyecto Docker independiente, utilizando PostgreSQL 18.6 sobre un contenedor Linux.

Se realizó la conversión del esquema original de MariaDB a PostgreSQL:

| MariaDB | PostgreSQL |
|---|---|
| `int(11)` | `INTEGER` |
| `decimal` | `NUMERIC` |
| `enum` | `VARCHAR + CHECK` |
| `AUTO_INCREMENT` | `GENERATED ALWAYS AS IDENTITY` |

También se agregó una clave foránea que no existía originalmente:

`detalle_pedido.id_medicamento → medicamento.id`.

**Prueba de concepto en C:**

Se implementó y verificó el mecanismo de extensión:

1. Compilación dentro del contenedor.
2. Generación de la librería `.so`.
3. Registro mediante `CREATE EXTENSION`.
4. Ejecución desde SQL.

Se creó la función de prueba `hello_pg_add(a, b)`, verificando:

```sql
SELECT hello_pg_add(2,3);
```

Resultado esperado: `5`.

**Diseño de estructuras:**

Se documentaron:

- Directorio y mecanismo de duplicación.
- Buckets de capacidad fija.
- Pares clave-TID.
- Profundidad local.
- Función hash multiplicativa de Knuth.

**Incidencia resuelta:**

Se corrigió el montaje del volumen de PostgreSQL 18, que utiliza una convención diferente a versiones anteriores.

**Archivos:** `docker-compose.yml`, `database/schema_postgres.sql`, `extension/hello_pg.c`, `Makefile` y `Dockerfile`.

### Semana 3 — Construcción del índice

Se implementó el núcleo de Extendible Hashing en C.

| Archivo | Implementación |
|---|---|
| `eh_types.h` | Estructuras Directory, Bucket y Entry. |
| `eh_hash.c/.h` | Función hash. |
| `eh_bucket.c/.h` | Creación, inserción y búsqueda en buckets. |
| `eh_directory.c/.h` | Creación, indexación y duplicación del directorio. |
| `eh_load_data.c` | Lectura de datos mediante SPI. |
| `eh_build.c` | Construcción inicial del índice. |

Se realizaron pruebas unitarias de la función hash y se verificó la distribución de los 23 medicamentos.

También se comprobó la lectura correcta de las 23 filas desde PostgreSQL.

**Incidencia resuelta:**

PostgreSQL rechazó inicialmente la librería compilada por falta de `PG_MODULE_MAGIC`, macro requerida para identificar el módulo. Se agregó en `eh_build.c`.

### Semana 4 — Búsqueda

Se implementó `eh_search()`, encargada de:

1. Calcular el hash de la clave.
2. Localizar el slot del directorio.
3. Acceder al bucket correspondiente.
4. Buscar la clave y devolver su valor o `NULL`.

Se registró la función en PostgreSQL y se desarrollaron pruebas unitarias.

**Pruebas realizadas:**

- Búsqueda exitosa.
- Búsqueda no exitosa.
- Duplicados.
- Determinismo.
- Bucket lleno.

**Incidencia identificada:**

Se comprobó que el índice mantenido únicamente en memoria no persiste entre conexiones distintas de PostgreSQL debido a su arquitectura de procesos por conexión.

Este hallazgo motivó la implementación de persistencia en la segunda etapa.

### Semana 5 — Inserción y split

Se implementaron los mecanismos de inserción y división dinámica de buckets.

**Implementaciones principales:**

- `eh_split.c`: división de buckets y redistribución de entradas.
- `eh_insert_core.c`: lógica central de inserción y duplicación del directorio.
- `eh_insert.c`: integración de la inserción con PostgreSQL.

Se incorporó un límite de seguridad de 32 iteraciones para evitar ciclos infinitos ante situaciones no previstas.

**Pruebas realizadas:**

- Split local.
- Duplicación del directorio.
- Inserción de claves.
- Recuperación de claves después de los splits.
- Detección de duplicados.
- Casos de overflow.

**Resultado de cierre de la Etapa I:**

```text
insertados = 23
omitidos_duplicado = 0
omitidos_lleno = 0
global_depth = 5
slots = 32
```

Se logró insertar y recuperar correctamente las 23 claves de la tabla `medicamento`.

### Desarrollo de la Etapa II — Evaluación y distribución

Durante la segunda etapa se amplió la implementación con persistencia, sincronización y evaluación experimental.

Los principales trabajos fueron:

- Serialización y recuperación del índice.
- Carga automática al abrir conexiones.
- Sincronización mediante triggers.
- Medición de búsquedas e inserciones.
- Comparación con B-tree y ausencia de índice.
- Generación y validación de datasets.
- Simulación de una arquitectura distribuida de tres nodos.
- Evaluación de fragmentación por rango y por hash.

Los resultados completos se presentan en las secciones 11 y 12 y en el informe final del proyecto.

## 9. Arquitectura e implementación

### 9.1 Módulos principales

| Archivo | Responsabilidad |
|---|---|
| `eh_types.h` | Estructuras Directory, Bucket y Entry; capacidad del bucket. |
| `eh_hash.c` | Función hash. |
| `eh_bucket.c` | Creación, inserción, búsqueda y detección de duplicados. |
| `eh_directory.c` | Creación del directorio, cálculo del slot y duplicación. |
| `eh_split.c` | División de buckets y redistribución. |
| `eh_insert_core.c` | Lógica central de inserción y duplicación. |
| `eh_load_data.c` | Lectura de datos mediante SPI. |
| `eh_build.c` | Construcción del índice y carga automática. |
| `eh_search.c` | Búsqueda desde SQL. |
| `eh_insert.c` | Inserción desde SQL. |
| `eh_persist.c` | Serialización y recuperación del índice. |
| `eh_persist_pg.c` | Integración de persistencia con PostgreSQL. |
| `eh_trigger.c` | Sincronización de nuevas filas. |
| `pg_shim.h` | Sustituto de funciones de PostgreSQL para pruebas independientes. |
| `eh_index--1.0.sql` | Registro de funciones en PostgreSQL. |
| `eh_index.control` | Configuración de la extensión. |

### 9.2 Flujo desde PostgreSQL hacia la estructura

1. El usuario ejecuta una consulta SQL, por ejemplo:

   ```sql
   SELECT eh_search(1);
   ```

2. PostgreSQL identifica la función registrada en `eh_index--1.0.sql`.

3. La función se ejecuta mediante la interfaz C de PostgreSQL (`PG_FUNCTION_INFO_V1`).

4. Durante la construcción, `eh_load_data.c` lee los registros mediante SPI.

5. `eh_build.c` inserta las claves en la estructura.

6. Durante la búsqueda, `eh_search.c` calcula el hash y localiza el bucket correspondiente.

7. Durante la inserción, `eh_insert.c` invoca `eh_directory_insert`, que ejecuta el split y la duplicación cuando es necesario.

### 9.3 Persistencia y sincronización

PostgreSQL utiliza un proceso por conexión. Por ello, un índice mantenido únicamente en memoria no se comparte entre conexiones.

Para resolver este problema se implementaron los siguientes mecanismos:

**Serialización binaria (`eh_save`):**

Guarda el índice en un archivo dentro del volumen persistente.

El formato contiene:

- Número mágico.
- Profundidad global.
- Número de slots.
- Identificador de bucket de cada slot.
- Identificador y profundidad local de cada bucket.
- Cantidad de entradas.
- Entradas almacenadas.

**Carga automática:**

- `_PG_init` permite cargar el índice al abrir una conexión.
- `eh_load()` permite realizar la carga manual.

**Sincronización mediante trigger:**

Se implementó un trigger `AFTER INSERT` sobre la tabla `medicamento`, utilizando `eh_sync_trigger`.

**Parámetro de configuración:**

`eh.autosave` permite controlar el guardado automático del índice.

- `on`: guarda el archivo en cada inserción.
- `off`: permite desactivar el guardado durante las mediciones para aislar el costo del índice en memoria.

**Incidencia corregida:**

Al cargar el índice desde disco, el contador de identificadores de bucket no se actualizaba correctamente. Esto provocaba la reutilización de identificadores durante los splits.

Se corrigió incorporando:

```c
bucket_set_id_counter(max_id + 1);
```

al final de `eh_directory_load`.

### 9.4 Contraste con B-tree y sin índice en PostgreSQL

Para comparar los planes de ejecución:

**Sin índice:**

```bash
docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "SET enable_indexscan=off; SET enable_bitmapscan=off; EXPLAIN ANALYZE SELECT * FROM medicamento WHERE id = 5;"
```

**Crear índice B-tree:**

```bash
docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "CREATE INDEX IF NOT EXISTS idx_med_id_btree ON medicamento(id); SELECT pg_size_pretty(pg_relation_size('idx_med_id_btree'));"
```

**Consultar utilizando B-tree:**

```bash
docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "SET enable_seqscan=off; EXPLAIN ANALYZE SELECT * FROM medicamento WHERE id = 5;"
```

Resultados:

- Sin índice: `Seq Scan`.
- Con B-tree: `Index Scan`.

### 9.5 Ubicación de las funciones principales

| Función | Archivo |
|---|---|
| `h(k)` | `eh_hash.c` |
| `directory_index` | `eh_directory.c` |
| `directory_double` | `eh_directory.c` |
| `bucket_find` | `eh_bucket.c` |
| `bucket_contains` | `eh_bucket.c` |
| `bucket_insert_raw` | `eh_bucket.c` |
| `bucket_split` | `eh_split.c` |
| `eh_directory_insert` | `eh_insert_core.c` |
| `eh_build` | `eh_build.c` |
| `_PG_init` | `eh_build.c` |
| `eh_search` | `eh_search.c` |
| `eh_insert` | `eh_insert.c` |
| `eh_save` | `eh_persist.c` |
| `eh_directory_load` | `eh_persist.c` |
| `eh_sync_trigger` | `eh_trigger.c` |

## 10. Pruebas unitarias

Las pruebas se ejecutan fuera de PostgreSQL mediante `gcc`, utilizando `extension/pg_shim.h`.

Este archivo reemplaza funciones de PostgreSQL como `palloc` y `elog`, permitiendo compilar los tests con `-DEH_STANDALONE`.

La capacidad predeterminada del bucket es 4.

### 10.1 Ejecutar pruebas

```bash
cd extension/tests

gcc -DEH_STANDALONE -I.. test_hash.c ../eh_hash.c -o test_hash && ./test_hash

gcc -DEH_STANDALONE -I.. test_search.c ../eh_hash.c ../eh_bucket.c ../eh_directory.c -o test_search && ./test_search

gcc -DEH_STANDALONE -I.. test_split.c ../eh_hash.c ../eh_bucket.c ../eh_directory.c ../eh_split.c ../eh_insert_core.c -o test_split && ./test_split
```

### 10.2 Cobertura de pruebas

| Prueba | Cobertura |
|---|---|
| `test_hash` | Función hash y distribución de claves. |
| `test_search` | Búsqueda exitosa y no exitosa, duplicados, determinismo y bucket lleno. |
| `test_split` | Inserción de claves, recuperación después de splits y duplicación del directorio. |

**Resultado esperado:** todas las pruebas se aprueban y `test_split` finaliza con profundidad global 5 (32 slots).

## 11. Evaluación experimental

### 11.1 Metodología

Se realizaron experimentos para comparar Extendible Hashing, B-tree y la búsqueda sin índice.

| Aspecto | Descripción |
|---|---|
| Entorno | PostgreSQL 18.6 en Docker. |
| `shared_buffers` | 128 MB. |
| `work_mem` | 4 MB. |
| `max_parallel_workers_per_gather` | 2. |
| Contenedor | 20 CPU y 8,1 GB de RAM. |
| Procesador | Intel Core i9-13900H. |
| Datasets | D1: enteros secuenciales; D2: enteros aleatorios únicos. |
| Tamaños | 100 000, 500 000 y 1 000 000 de claves. |
| W1 | 10 000 búsquedas exitosas. |
| W2 | 10 000 búsquedas de claves ausentes. |
| W3 | Inserciones del 10 % del tamaño base. |
| Escenarios | Sin índice, B-tree y Extendible Hashing. |
| Repeticiones | 5 por medición, utilizando la mediana. |

No se aplicaron W4 y W5 (consultas por rango y prefijo), debido a que Extendible Hashing solo soporta igualdad.

Tampoco se utilizaron D4 y D5 porque la clave implementada es de tipo `INTEGER`.

### 11.2 Resultados principales

| Medida | Resultado |
|---|---|
| Búsqueda (1 000 000 de claves) | B-tree y EH son entre 23 y 39 veces más rápidos que sin índice. |
| Comparación de búsqueda | EH y B-tree presentan resultados similares debido al costo de comunicación cliente-servidor. |
| Construcción | EH es entre 7 y 17 veces más lento que B-tree. |
| Inserción (500 000 y 1 000 000 de claves) | EH es entre 4 % y 8 % más lento que B-tree. |
| Guardado en cada inserción | Entre 7 y 10 veces más costoso que mantener el índice en memoria. |
| Tamaño del índice | EH es entre 25 % y 27 % menor. |

**Consideración sobre el tamaño:** la comparación corresponde al archivo serializado de Extendible Hashing frente a las páginas de PostgreSQL, por lo que no representa una comparación completamente equivalente.

El detalle de las tablas, resultados, discusión y amenazas a la validez se encuentra en el informe final.

## 12. Escenario distribuido

### 12.1 Configuración

Se implementó un escenario distribuido con tres nodos PostgreSQL 18.6 ejecutados en contenedores.

| Conexión | Latencia simulada |
|---|---|
| A–B | 20 ms |
| A–C | 40 ms |
| B–C | 25 ms |

Las latencias se simularon mediante esperas previas a cada consulta remota.

Las consultas que involucran varios nodos se ejecutan en paralelo.

### 12.2 Fragmentación y replicación

| Relación | Tamaño | Estrategia |
|---|---|---|
| `pedido` | 1 000 000 | Fragmentación horizontal por rango o hash. |
| `detalle_pedido` | Aproximadamente 2 000 000 | Se almacena en el mismo nodo que su pedido. |
| `usuario` | 5 000 | Replicada en los tres nodos. |
| `medicamento` | 100 | Replicada en los tres nodos. |

Se utilizaron dos estrategias:

**Fragmentación por rango:**

Los identificadores de pedidos se distribuyen en tres grupos de acuerdo con sus rangos.

**Fragmentación por hash:**

Los identificadores se distribuyen utilizando:

```text
id mod 3
```

### 12.3 Pruebas realizadas

- Carga con 70 % de lecturas y 30 % de escrituras.
- Cambios en la concentración de accesos.
- Consultas de rango.
- Consultas que requieren los tres nodos.
- Simulación de indisponibilidad de un nodo.

Se realizaron cinco repeticiones por medición y se utilizó la mediana.

### 12.4 Resultados

| Medida | RANGO | HASH |
|---|---|---|
| Consulta de rango de 10 000 identificadores (ms) | 62,9 | 81,7 |
| Carga en el nodo más utilizado (accesos concentrados) | 72 % | 35 % |
| Rangos resueltos con el nodo B caído | 67 % | 0 % |
| Lecturas de tablas replicadas con un nodo caído | 100 % | 100 % |

**Consideración:** Extendible Hashing no se desplegó en los nodos distribuidos, ya que solo soporta igualdad, el índice reside en la memoria de cada conexión y no está integrado como método de acceso nativo.

## 13. Estructura del repositorio

```text
Proyecto-final-BD2/
│
├── database/
│   └── schema_postgres.sql
│
├── extension/
│   ├── eh_types.h
│   ├── pg_shim.h
│   ├── eh_hash.c
│   ├── eh_hash.h
│   ├── eh_bucket.c
│   ├── eh_bucket.h
│   ├── eh_directory.c
│   ├── eh_directory.h
│   ├── eh_split.c
│   ├── eh_split.h
│   ├── eh_insert_core.c
│   ├── eh_insert_core.h
│   ├── eh_load_data.c
│   ├── eh_build.c
│   ├── eh_search.c
│   ├── eh_insert.c
│   ├── eh_persist.c
│   ├── eh_persist_pg.c
│   ├── eh_trigger.c
│   ├── eh_index--1.0.sql
│   ├── eh_index.control
│   ├── hello_pg.c
│   ├── Makefile
│   ├── Dockerfile
│   │
│   └── tests/
│       ├── test_hash.c
│       ├── test_search.c
│       └── test_split.c
│
├── diseno/
│   ├── directorio_specs.md
│   ├── buckets_specs.md
│   ├── funcion_hash_specs.md
│   ├── documentacion_tecnica_parcial.md
│   └── casos_edge_semana5.md
│
├── etapa2-evaluacion-distribucion/
│   │
│   ├── datasets/
│   │   ├── generators/
│   │   ├── workloads/
│   │   ├── validate/
│   │   ├── load/
│   │   └── output/
│   │
│   ├── distributed/
│   │
│   └── informe/
│       ├── Informe_Final_Extendible_Hashing.docx
│       └── informe_etapa2.md
│
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Avance por semanas

La tabla resume el avance frente al cronograma de la rúbrica (secciones 5.4 y 6.4). Debajo se detalla cada semana con sus entregables, archivos y evidencia.

| Semana | Objetivo (rúbrica) | Resultado |
|---|---|---|
| 1 | Comprensión y diseño | Propuesta inicial, referencias, representación y plan |
| 2 | Implementación inicial | Entorno Docker, prueba de concepto en C y diseño de las estructuras |
| 3 | Operaciones principales | Hash, buckets, directorio, lectura por SPI y `eh_build` |
| 4 | Integración con PostgreSQL | `eh_search` registrada y probada desde SQL |
| 5 | Parcial práctico | Split, duplicación del directorio y `eh_insert`; 23 de 23 claves |
| 6 | Pruebas de rendimiento | Persistencia, trigger, datos y cargas, benchmark de búsqueda e inserción |
| 7 | Diseño distribuido | Fragmentación, asignación y replicación justificadas |
| 8 | Implementación o simulación | Tres nodos en Docker con 1 000 000 de pedidos y latencias simuladas |
| 9 | Integración y experimentos | Comparación RANGO frente a HASH, carga 70/30 y caída de un nodo |
| 10 | Evaluación final | Informe, repositorio reproducible y defensa |

### Semana 1: Comprensión y diseño

- **Entregable:** propuesta inicial (`Propuesta_Inicial.pdf`).
- **Contenido:** estructura elegida y motivación; referencias (Fagin et al., 1979; Silberschatz et al., 2020; documentación de PostgreSQL 18); representación de la estructura; clave `INTEGER` (`medicamento.id`) con búsqueda por igualdad; integración mediante una extensión en C; riesgos técnicos y plan de trabajo.

### Semana 2: Implementación inicial

- **Entorno:** PostgreSQL 18.6 en Docker. Se tradujo el esquema de MariaDB a PostgreSQL (`int(11)` a `INTEGER`, `decimal` a `NUMERIC`, `enum` a `VARCHAR` con `CHECK`, `AUTO_INCREMENT` a `GENERATED ALWAYS AS IDENTITY`) y se agregó la clave foránea `detalle_pedido.id_medicamento` → `medicamento.id`.
- **Prueba de concepto:** extensión `hello_pg` con la función `hello_pg_add(a, b)`, que valida el ciclo completo (compilación, `.so`, `CREATE EXTENSION`, ejecución desde SQL).
- **Diseño:** directorio, buckets y función hash (`diseno/directorio_specs.md`, `buckets_specs.md`, `funcion_hash_specs.md`).
- **Archivos:** `docker-compose.yml`, `database/schema_postgres.sql`, `extension/hello_pg.*`, `Makefile`, `Dockerfile`.
- **Incidencia:** en PostgreSQL 18 el volumen de datos se monta en `/var/lib/postgresql`; se corrigió en `docker-compose.yml`.

### Semana 3: Operaciones principales

- **Implementado:** `eh_types.h`, `eh_hash.c` (con `test_hash.c`; distribución 5/6/6/6 sobre los 23 registros), `eh_bucket.c`, `eh_directory.c`, `eh_load_data.c` (lectura por SPI) y el esqueleto de `eh_build()`.
- **Verificación:** `eh_build()` registrada en PostgreSQL, con el aviso `gd=2, 4 slots`.
- **Incidencia:** la librería fue rechazada con `missing magic block`; se agregó `PG_MODULE_MAGIC;` en `eh_build.c`.

### Semana 4: Integración con PostgreSQL

- **Implementado:** `eh_search()`, con registro en `eh_index--1.0.sql`.
- **Pruebas:** `tests/test_search.c` (5 casos: búsqueda exitosa y no exitosa, duplicados, determinismo y bucket lleno).
- **Casos límite:** `bucket_contains()` evita duplicados; `bucket_insert_raw()` rechaza la inserción en un bucket lleno.
- **Hallazgo:** el índice en memoria no persiste entre conexiones (un proceso por conexión). Se resolvió en la semana 6.
- **Limitación de esta semana:** sin split, solo 4 de las 23 claves se insertaban; el resto se registraba como advertencia.

### Semana 5: Parcial práctico

- **Implementado:** `eh_split.c` (split local), duplicación del directorio, `eh_insert_core.c` (`eh_directory_insert`, con límite de 32 iteraciones) y `eh_insert()` invocable desde SQL.
- **Pruebas:** `tests/test_split.c` (4 casos) y `diseno/casos_edge_semana5.md`.
- **Resultado:** `eh_build()` inserta las 23 claves, con el directorio creciendo de `gd=2` a `gd=5`.
- **Comparación preliminar con B-tree:** conceptual y mediante `EXPLAIN ANALYZE` (sección 8.4).

### Semana 6: Pruebas de rendimiento

- **Persistencia:** `eh_save` serializa el índice a un archivo; `_PG_init` lo carga al abrir cada conexión; el trigger `eh_sync_trigger` sincroniza `medicamento`; el parámetro `eh.autosave` desactiva el guardado por inserción en las mediciones.
- **Capacidad de bucket configurable:** 4 (demostración) y 64 (mediciones), mediante un `ARG` del Dockerfile.
- **Datos y cargas:** D1 y D2 (semilla 272) con 100 000, 500 000 y 1 000 000 de claves; W1, W2 y W3; verificación con `datasets/validate/`.
- **Benchmark:** `benchmark_runner.py` (búsqueda, construcción y tamaño del índice) y `measure_insertion.py` (inserciones, con controles, orden rotativo y `CHECKPOINT`). Cinco repeticiones y mediana.
- **Resultados:** sección 10.2.
- **Incidencias:**
  - Con buckets de 4 entradas, D2 de 100 000 claves alcanzaba la profundidad límite (20 bits); las mediciones usan 64.
  - Al cargar el índice desde disco, el contador de identificadores de bucket no se ajustaba y se perdían claves; se corrigió con `bucket_set_id_counter` en `eh_directory_load`.

### Semana 7: Diseño distribuido

- **Fragmentación:** `pedido` con dos estrategias, RANGO (tercios de identificadores) y HASH (`id mod 3`); `detalle_pedido` derivada, alojada en el nodo de su pedido.
- **Replicación:** `usuario` y `medicamento` en los tres nodos.
- **Indexación:** B-tree en cada fragmento; Extendible Hashing no se despliega en los nodos (solo igualdad e índice en memoria por conexión).
- **Justificación:** informe final, sección 10.

### Semana 8: Implementación o simulación

- **Entorno:** tres contenedores PostgreSQL (A, B y C) definidos en `docker-compose-distributed.yml`, con `schema_distributed.sql`.
- **Carga:** `fragment_data.py` genera y distribuye 1 000 000 de pedidos y unos 2 000 000 de detalles con la estrategia indicada.
- **Latencias:** `query_router.py` simula A–B = 20 ms, A–C = 40 ms y B–C = 25 ms con una espera previa a cada consulta remota.

### Semana 9: Integración y experimentos

- **Script:** `run_distributed_tests.py`, con un ciclo por estrategia y verificación del layout de los datos.
- **Pruebas:** carga 70 % lecturas y 30 % escrituras; cambio en la concentración de accesos; consultas de rango de 10 000 y 1 000 identificadores; JOIN que involucra los tres nodos; caída del nodo B. Cinco repeticiones y mediana.
- **Resultados:** sección 11 y `resultados_dist_rango.json` / `resultados_dist_hash.json`.

### Semana 10: Evaluación final

- **Informe:** `etapa2-evaluacion-distribucion/informe/`.
- **Repositorio:** README con los modos de ejecución, guía de demostración y dependencias (`requirements.txt`).
- **Reproducibilidad:** verificación mediante clonación en una carpeta limpia y reconstrucción sin caché (`docker compose build --no-cache`).
- **Defensa:** guía de demostración (sección 6) y distribución del trabajo (sección 2).

  
## 14. Limitaciones

- La estructura no está implementada como método de acceso nativo (`CREATE INDEX ... USING`); se invoca mediante funciones SQL.
- No soporta consultas por rango ni ordenamiento.
- No mantiene automáticamente las operaciones `UPDATE` y `DELETE`.
- No incorpora control de concurrencia ni WAL propio.
- El índice reside en la memoria de cada conexión y se carga desde el archivo persistente al abrirla.
- `eh_search` devuelve el valor almacenado (identificador), no la ubicación física real de la fila.
- La profundidad del directorio tiene un límite de 19 bits; se aborta al alcanzar 20.
- Las mediciones se realizaron en un único equipo con Docker.
- En el escenario distribuido, la red se simuló mediante esperas y los clientes fueron secuenciales.
- Extendible Hashing no se desplegó en los nodos del escenario distribuido.

## 15. Recursos externos y uso de herramientas de IA

- Se consultó la documentación oficial de PostgreSQL 18 sobre la API de extensiones en C, `PG_FUNCTION_INFO_V1`, `fmgr.h` y SPI.
- Se utilizaron Docker y Docker Compose para construir un entorno reproducible.
- Se utilizaron bibliotecas estándar de C para implementar la estructura.
- No se reutilizó código de terceros para la implementación de Extendible Hashing; el código de la extensión es desarrollo propio del equipo.
- Durante la Etapa II se utilizó Claude (Anthropic) como apoyo en la revisión del diseño experimental, la escritura y depuración de scripts de medición y simulación distribuida, la localización del error del contador de identificadores de bucket y la redacción de borradores del informe. El código entregado fue ejecutado y revisado por el equipo.

## 16. Referencias

- Fagin, R., Nievergelt, J., Pippenger, N., & Strong, H. R. (1979). *Extendible Hashing—A Fast Access Method for Dynamic Files*. ACM Transactions on Database Systems, 4(3), 315–344.
- Silberschatz, A., Korth, H. F., & Sudarshan, S. (2020). *Database System Concepts* (7.ª ed.).
- PostgreSQL Global Development Group. *PostgreSQL 18 Documentation*: Index Access Method Interface y C-Language Functions.

---

**Proyecto Final de Bases de Datos II — CS272**  
**Universidad Católica San Pablo | 2026-II**
