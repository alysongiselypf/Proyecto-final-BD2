# Extendible Hashing sobre PostgreSQL

**Proyecto Final de Bases de Datos II (CS272), 2026-II**
Universidad Católica San Pablo · Ciencia de la Computación
**Docente:** Regina Paola Ticona Herrera
**Estructura de indexación implementada:** Extendible Hashing (hashing dinámico mediante directorio y buckets)

---

## Contenido

1. [Descripción general](#1-descripción-general)
2. [Equipo](#2-equipo)
3. [Requisitos](#3-requisitos)
4. [Instalación y verificación](#4-instalación-y-verificación)
5. [Modos de ejecución](#5-modos-de-ejecución)
6. [Guía de demostración](#6-guía-de-demostración)
7. [Fundamentos de la estructura](#7-fundamentos-de-la-estructura)
8. [Arquitectura e implementación](#8-arquitectura-e-implementación)
9. [Pruebas unitarias](#9-pruebas-unitarias)
10. [Evaluación experimental](#10-evaluación-experimental)
11. [Escenario distribuido](#11-escenario-distribuido)
12. [Estructura del repositorio](#12-estructura-del-repositorio)
13. [Limitaciones](#13-limitaciones)
14. [Recursos externos y uso de herramientas de IA](#14-recursos-externos-y-uso-de-herramientas-de-ia)
15. [Referencias](#15-referencias)

---

## 1. Descripción general

Este proyecto implementa **Extendible Hashing** como estructura de indexación alternativa a B-tree. La estructura se desarrolló íntegramente en C y se integró en PostgreSQL 18.6 como **extensión nativa**, invocable desde SQL mediante `CREATE FUNCTION ... LANGUAGE C`. El código se ejecuta dentro del proceso del servidor y obtiene los datos de las tablas a través de SPI.

El trabajo se organiza en dos etapas:

| Etapa | Semanas | Resultado |
|---|---|---|
| I. Indexación | 1 a 5 | Estructura implementada e integrada con PostgreSQL; demostración reproducible |
| II. Evaluación y distribución | 6 a 10 | Persistencia del índice; comparación experimental frente a "sin índice" y B-tree; diseño y pruebas de un escenario distribuido de tres nodos |

El informe final se encuentra en `etapa2-evaluacion-distribucion/informe/` (`Informe_Final_Extendible_Hashing.docx` e `informe_etapa2.md`).

## 2. Equipo

| Integrante | Área principal |
|---|---|
| Alyson Perez Flores | Entorno, integración con PostgreSQL, persistencia y benchmark de búsqueda |
| Rodrigo Sierra Huaracha | Núcleo de la estructura, generación y validación de datos |
| Ruth Benique Huaman | Inserción y split, medición de inserciones y parte distribuida |

## 3. Requisitos

| Componente | Uso |
|---|---|
| Docker Desktop (contenedores Linux) | Obligatorio; verificar con `docker --version` |
| Git | Obligatorio |
| Python 3.10 o superior | Benchmarks y parte distribuida; `pip install -r requirements.txt` |
| `gcc` | Solo para los tests unitarios fuera de Docker |

## 4. Instalación y verificación

```bash
git clone https://github.com/alysongiselypf/Proyecto-final-BD2.git
cd Proyecto-final-BD2
docker compose up -d --build
```

El comando construye la imagen de PostgreSQL 18.6, compila e instala la extensión `eh_index` y carga el esquema base con 23 registros en la tabla `medicamento`.

**Verificación.**

```bash
docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "SELECT eh_build();"
docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "SELECT eh_search(1);"
docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "SELECT eh_search(9999);"
```

| Consulta | Resultado esperado |
|---|---|
| `eh_build()` | `t`, con el aviso `gd=5, slots=32, insertados=23, omitidos_duplicado=0, fallidos=0` |
| `eh_search(1)` | `1`: el valor almacenado (el identificador de la fila), no la ubicación física del registro |
| `eh_search(9999)` | vacío (`NULL`): la clave no existe |

## 5. Modos de ejecución

El tamaño de bucket es un parámetro de compilación. Su valor por defecto es **4** (modo demostración, que permite observar los splits con 23 registros); las mediciones se realizan con **64**.

### 5.1 Modo demostración (buckets de 4 entradas)

Es el procedimiento de la sección 4. `eh_build()` produce `gd=5, slots=32`.

### 5.2 Modo mediciones (buckets de 64 entradas)

```powershell
$env:BUCKET_CAPACITY = 64          # PowerShell   (bash: export BUCKET_CAPACITY=64)
docker compose down -v
docker compose build
docker compose up -d --wait
```

Con 64, `SELECT eh_build();` produce `gd=2, slots=4`. A continuación, desde `etapa2-evaluacion-distribucion/datasets/workloads`:

```bash
pip install -r requirements.txt
python benchmark_runner.py 100000 500000 1000000     # búsqueda, construcción y tamaño del índice
python measure_insertion.py 100000 500000 1000000    # inserciones (W3)
```

- Los datos de entrada se generan con los scripts de `datasets/generators` y `datasets/workloads` (semilla 272) y se validan con `datasets/validate/check_workloads.py`. Los archivos CSV no se versionan.
- Los resultados se almacenan en `datasets/output/resultados_*.json`.
- Los scripts deben ejecutarse desde `datasets/workloads`, ya que emplean rutas relativas.
- Las corridas completas son prolongadas; en particular, el escenario sin índice con 1 000 000 de claves requiere varias horas.

Para retornar al modo demostración, se elimina la variable (`Remove-Item Env:BUCKET_CAPACITY`) y se reconstruye con `docker compose down -v` y `docker compose build`.

### 5.3 Escenario distribuido

Desde `etapa2-evaluacion-distribucion/distributed`:

```bash
docker compose -f docker-compose-distributed.yml up -d --wait
python fragment_data.py rango            # carga 1 000 000 de pedidos con fragmentación por rango
python run_distributed_tests.py rango
python fragment_data.py hash             # recarga con fragmentación por hash
python run_distributed_tests.py hash
python run_distributed_tests.py comparar
```

Para una prueba rápida con esperas reducidas, definir antes `LATENCIA_ESCALA=0.05`, `REPS=1` y `N_OPS=100`.

## 6. Guía de demostración

Cada comando se ejecuta en una conexión nueva, de modo que se evidencia que el índice es compartido y persistente entre conexiones.

| Solicitud | Procedimiento | Resultado |
|---|---|---|
| Construir el índice | `SELECT eh_build();` | `t`; `gd=5, slots=32, insertados=23` |
| Buscar una clave existente | `SELECT eh_search(1);` | `1` |
| Buscar una clave inexistente | `SELECT eh_search(9999);` | vacío (`NULL`) |
| Insertar y recuperar | `SELECT eh_insert(200);` y, en otra conexión, `SELECT eh_search(200);` | `t` y `200` |
| Insertar un duplicado | `SELECT eh_insert(200);` nuevamente | `f` y aviso de clave existente |
| Verificar persistencia | `docker restart farmacia_pg`, esperar 5 s, `SELECT eh_search(200);` | `200`, sin reconstruir el índice |
| Reiniciar el entorno | `docker compose down -v`; `docker compose up -d --build`; `SELECT eh_build();` | retorna a `gd=5` |
| Verificar el trigger | `INSERT INTO medicamento (nombre, precio) VALUES ('x', 1.50) RETURNING id;` y `SELECT eh_search(<id>);` | aviso «sincronizado y persistido»; la clave se recupera |
| Consultar el archivo del índice | `SELECT eh_index_size();` | tamaño en bytes (crece al insertar) |
| Modificar la capacidad de bucket | Procedimiento de la sección 5.2 | `eh_build()` pasa de `gd=5` a `gd=2` |
| Ejecutar los tests | Sección 9 | todos aprobados; `test_split` termina en `gd=5` |
| Contrastar con B-tree | Sección 8.4 | `Seq Scan` frente a `Index Scan` |
| Inspeccionar los nodos | `docker exec farmacia_nodeA psql -U farmacia_user -d farmacia_db -c "SELECT count(*), min(id), max(id) FROM pedido;"` (también `farmacia_nodeB` y `farmacia_nodeC`) | aproximadamente 333 333 pedidos por nodo; el rango de identificadores depende de la estrategia cargada |
| Simular la caída de un nodo | `docker stop farmacia_nodeB`; consultar B (falla) y A (responde); `docker start farmacia_nodeB` | solo el nodo detenido deja de responder |

**Observaciones.**
- Tras `docker compose down -v` debe ejecutarse `SELECT eh_build();` antes de insertar o buscar.
- Si se inserta una clave ya registrada anteriormente, el resultado es `f`, porque el índice persiste. Debe utilizarse una clave nueva.
- El trigger cubre únicamente `INSERT`. Si se elimina la fila de la tabla, la clave permanece en el índice hasta reconstruirlo con `eh_build()`.

## 7. Fundamentos de la estructura

Extendible Hashing (Fagin et al., 1979) mantiene un **directorio** de 2^gd punteros, donde *gd* es la profundidad global. Cada puntero referencia un **bucket**, una página de capacidad fija con pares clave–valor. El slot se determina con los *gd* bits menos significativos del hash de la clave. Cada bucket posee una profundidad local (*ld*); varios slots pueden apuntar al mismo bucket cuando *ld* < *gd*.

```
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

### 7.1 Operaciones

| Operación | Descripción |
|---|---|
| Búsqueda | Se calcula el hash, se obtiene el slot con los *gd* bits menos significativos, se accede al bucket y se recorre su contenido. |
| Inserción | Se localiza el bucket; si tiene espacio se inserta, de lo contrario se produce un split. |
| Split local (*ld* < *gd*) | El bucket se divide en dos; sus entradas se redistribuyen según el bit adicional del hash y solo se actualizan los slots que lo referenciaban. |
| Duplicación del directorio (*ld* = *gd*) | El directorio duplica su tamaño (2^gd → 2^(gd+1)), los slots nuevos copian los punteros de los anteriores y a continuación se realiza el split local. |

### 7.2 Función hash

Se utiliza la función multiplicativa de Knuth, `h(k) = k × 2654435761 mod 2^32`, y se emplean los bits menos significativos para indexar el directorio, siguiendo la convención de Fagin et al. Sobre los 23 registros de `medicamento`, la distribución en cuatro slots es 5/6/6/6.

### 7.3 Pseudocódigo

```
BUSCAR(k):
  b = directorio[slot(k)]
  para cada entrada e en b: si e.clave == k: devolver e.valor
  devolver NULL

INSERTAR(k, v):
  si BUSCAR(k) != NULL: rechazar (duplicado)
  repetir (máximo 32 iteraciones):
    b = directorio[slot(k)]
    si b no está lleno: agregar (k, v) a b; terminar
    si b.ld == gd: DUPLICAR_DIRECTORIO()
    SPLIT(b)
  si se agotan las iteraciones: reportar bucket lleno
```

### 7.4 Comparación conceptual con B-tree

| Criterio | Extendible Hashing | B-tree |
|---|---|---|
| Consultas soportadas | Solo igualdad (=) | Igualdad y rango |
| Búsqueda | O(1) promedio; peor caso O(capacidad del bucket) | O(log n) garantizado |
| Inserción | O(1) amortizado; mayor costo con splits en cadena | O(log n) |
| Crecimiento | Dinámico: split y duplicación solo cuando es necesario | Balanceo en cada inserción |
| Orden de las claves | No se mantiene | Orden total |
| Caso de uso ideal | Acceso puntual por clave exacta | Rangos, ordenamiento y mayor flexibilidad |

## 8. Arquitectura e implementación

### 8.1 Módulos

| Archivo | Responsabilidad |
|---|---|
| `eh_types.h` | Estructuras `Directory`, `Bucket` y `Entry`; `BUCKET_CAPACITY` |
| `eh_hash.c` | Función hash |
| `eh_bucket.c` | Creación, inserción, búsqueda y detección de duplicados en buckets; contador de identificadores |
| `eh_directory.c` | Creación del directorio, cálculo del slot y duplicación |
| `eh_split.c` | Split de bucket con redistribución según el bit adicional |
| `eh_insert_core.c` | `eh_directory_insert`: decide entre split y duplicación; límite de 32 iteraciones |
| `eh_load_data.c` | Lectura de la tabla por SPI |
| `eh_build.c` | `eh_build`, `eh_build_table` y `_PG_init` (carga automática del índice y definición de `eh.autosave`); contiene `PG_MODULE_MAGIC` |
| `eh_search.c`, `eh_insert.c` | Funciones SQL de búsqueda e inserción |
| `eh_persist.c`, `eh_persist_pg.c` | Serialización y carga del índice (`eh_save`, `eh_load`, `eh_index_size`) |
| `eh_trigger.c` | `eh_sync_trigger`: indexa y guarda cada fila nueva de `medicamento` |
| `pg_shim.h` | Sustituto de `postgres.h` para compilar y probar sin PostgreSQL (`-DEH_STANDALONE`) |
| `eh_index--1.0.sql`, `eh_index.control` | Registro de las funciones en PostgreSQL |

### 8.2 Flujo desde PostgreSQL hacia la estructura

1. El usuario ejecuta una consulta SQL, por ejemplo `SELECT eh_search(1);`.
2. PostgreSQL resuelve la función registrada en `eh_index--1.0.sql` y la despacha a la función C correspondiente (`PG_FUNCTION_INFO_V1`).
3. En la construcción, `eh_load_data.c` lee las filas por SPI y `eh_build.c` inserta cada clave.
4. En la búsqueda, `eh_search.c` calcula el hash, `directory_index` selecciona el slot y `bucket_find` localiza la clave.
5. En la inserción, `eh_insert.c` invoca `eh_directory_insert`, que inserta y, si el bucket está lleno, ejecuta el split y, de ser necesario, la duplicación del directorio.

### 8.3 Persistencia y sincronización

PostgreSQL crea un proceso por conexión; un índice mantenido únicamente en memoria no se comparte entre conexiones. La solución adoptada comprende:

- **Serialización binaria** (`eh_save`) a un archivo en el volumen persistente. El formato contiene un número mágico, la profundidad global, el número de slots, el identificador de bucket de cada slot y, por cada bucket único, su identificador, profundidad local, cantidad de entradas y entradas.
- **Carga automática** en `_PG_init`, al abrirse cada conexión. También existe `eh_load()` para la carga manual.
- **Trigger** `AFTER INSERT` sobre `medicamento` (`eh_sync_trigger`), que indexa la fila nueva y guarda el índice.
- **Parámetro `eh.autosave`**: con valor `on` (por defecto), `eh_insert` guarda el archivo en cada inserción; en las mediciones se desactiva para aislar el costo del índice en memoria.

**Incidencia corregida.** Al cargar el índice desde disco en una conexión nueva, el contador de identificadores de bucket no se ajustaba. El split siguiente reutilizaba un identificador existente y, al guardar, se perdían entradas (21 de 24 claves recuperables). Se corrigió incorporando `bucket_set_id_counter(max_id + 1)` al final de `eh_directory_load`.

### 8.4 Contraste con B-tree y sin índice en PostgreSQL

```bash
docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "SET enable_indexscan=off; SET enable_bitmapscan=off; EXPLAIN ANALYZE SELECT * FROM medicamento WHERE id = 5;"
docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "CREATE INDEX IF NOT EXISTS idx_med_id_btree ON medicamento(id); SELECT pg_size_pretty(pg_relation_size('idx_med_id_btree'));"
docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "SET enable_seqscan=off; EXPLAIN ANALYZE SELECT * FROM medicamento WHERE id = 5;"
```

La primera consulta produce un `Seq Scan`; la tercera, un `Index Scan`.

### 8.5 Ubicación de las funciones principales

| Función | Archivo |
|---|---|
| `h(k)` | `eh_hash.c` |
| `directory_index`, `directory_double` | `eh_directory.c` |
| `bucket_find`, `bucket_contains`, `bucket_insert_raw` | `eh_bucket.c` |
| `bucket_split` | `eh_split.c` |
| `eh_directory_insert` | `eh_insert_core.c` |
| `eh_build`, `_PG_init` | `eh_build.c` |
| `eh_search`, `eh_insert` | `eh_search.c`, `eh_insert.c` |
| `eh_save`, `eh_directory_load` | `eh_persist.c` |
| `eh_sync_trigger` | `eh_trigger.c` |

## 9. Pruebas unitarias

Las pruebas se ejecutan fuera de PostgreSQL, con `gcc`, mediante `extension/pg_shim.h` (`-DEH_STANDALONE`). La capacidad de bucket por defecto es 4.

```bash
cd extension/tests
gcc -DEH_STANDALONE -I.. test_hash.c ../eh_hash.c -o test_hash && ./test_hash
gcc -DEH_STANDALONE -I.. test_search.c ../eh_hash.c ../eh_bucket.c ../eh_directory.c -o test_search && ./test_search
gcc -DEH_STANDALONE -I.. test_split.c ../eh_hash.c ../eh_bucket.c ../eh_directory.c ../eh_split.c ../eh_insert_core.c -o test_split && ./test_split
```

| Prueba | Cobertura |
|---|---|
| `test_hash` | Función hash y distribución sobre los 23 registros |
| `test_search` | Búsqueda exitosa y no exitosa, duplicados, determinismo y bucket lleno |
| `test_split` | Inserción de las 23 claves, recuperación tras los splits y duplicación del directorio |

Resultado esperado: todas las pruebas se aprueban y `test_split` finaliza con profundidad global 5 (32 slots).

## 10. Evaluación experimental

### 10.1 Metodología

| Aspecto | Descripción |
|---|---|
| Entorno | PostgreSQL 18.6 en Docker; `shared_buffers` = 128 MB, `work_mem` = 4 MB, `max_parallel_workers_per_gather` = 2; contenedor con 20 CPU y 8,1 GB de RAM; Intel Core i9-13900H |
| Datos | D1 (enteros secuenciales) y D2 (enteros aleatorios únicos, semilla 272), con 100 000, 500 000 y 1 000 000 de claves |
| Cargas | W1: 10 000 búsquedas exitosas; W2: 10 000 búsquedas de claves ausentes; W3: inserciones del 10 % del tamaño base |
| Escenarios | Sin índice (verificado con `EXPLAIN` como recorrido secuencial), B-tree de PostgreSQL y Extendible Hashing, con una consulta por clave en los tres |
| Repeticiones | 5 por medición; se reporta la mediana, por la presencia de valores atípicos |
| Inserción | Orden de escenarios rotativo, `CHECKPOINT` previo y controles con la misma forma de sentencia que EH |
| No aplicables | W4 y W5 (rango y prefijo), porque la estructura solo soporta igualdad; D4 y D5, porque la clave es `INTEGER` |

Cada experimento registra la versión de PostgreSQL, la configuración relevante, el tamaño del dataset y el número de repeticiones en los archivos `resultados_*.json`.

### 10.2 Resultados principales

| Medida | Resultado |
|---|---|
| Búsqueda (1 000 000 de claves) | B-tree y EH son entre 23 y 39 veces más rápidos que sin índice; entre sí no se distinguen, ya que el tiempo lo domina la ida y vuelta cliente–servidor (1,1 a 1,4 ms por consulta) |
| Construcción | EH es entre 7 y 17 veces más lento que B-tree |
| Inserción (500 000 y 1 000 000 de claves) | EH es entre 4 % y 8 % más lento que B-tree con la misma forma de sentencia |
| Guardado del índice en cada inserción | Entre 7 y 10 veces más costoso que mantenerlo en memoria |
| Tamaño del índice | EH es 25–27 % menor; corresponde al archivo serializado frente a páginas de PostgreSQL, por lo que no es una comparación equivalente |

El detalle de tablas, la discusión y las amenazas a la validez se encuentran en el informe final.

## 11. Escenario distribuido

**Configuración.** Tres nodos PostgreSQL 18.6 en contenedores (A, B y C) con latencias A–B = 20 ms, A–C = 40 ms y B–C = 25 ms, simuladas mediante esperas previas a cada consulta remota. Las consultas que involucran varios nodos se ejecutan en paralelo y su costo equivale a la mayor latencia.

| Relación | Tamaño | Fragmentación y replicación |
|---|---|---|
| `pedido` | 1 000 000 | Horizontal por `id`: **RANGO** (tercios de identificadores) o **HASH** (`id mod 3`) |
| `detalle_pedido` | ≈ 2 000 000 | Derivada: cada detalle se aloja en el nodo de su pedido, de modo que el JOIN es local |
| `usuario` | 5 000 | Replicada en los tres nodos |
| `medicamento` | 100 | Replicada en los tres nodos |

**Pruebas.** Carga con 70 % de lecturas y 30 % de escrituras; cambio en la concentración de accesos; consultas de rango y consultas que requieren los tres nodos; indisponibilidad de un nodo. Cinco repeticiones y mediana.

| Medida | RANGO | HASH |
|---|---|---|
| Consulta de rango de 10 000 identificadores (ms) | 62,9 | 81,7 |
| Parte de la carga en el nodo más cargado (accesos concentrados) | 72 % | 35 % |
| Rangos resueltos con el nodo B caído | 67 % | 0 % |
| Lecturas de tablas replicadas con un nodo caído | 100 % | 100 % |

Extendible Hashing no se desplegó en los nodos: solo soporta igualdad, el índice reside en la memoria de cada conexión y no está integrado como método de acceso.

## 12. Estructura del repositorio

```
Proyecto-final-BD2/
├── database/schema_postgres.sql        # Esquema base (7 tablas)
├── extension/                          # Extensión en C
│   ├── eh_types.h, pg_shim.h
│   ├── eh_hash.*, eh_bucket.*, eh_directory.*, eh_split.*, eh_insert_core.*
│   ├── eh_load_data.c, eh_build.c, eh_search.c, eh_insert.c
│   ├── eh_persist.*, eh_persist_pg.c, eh_trigger.c
│   ├── eh_index--1.0.sql, eh_index.control, hello_pg.*
│   ├── Makefile, Dockerfile
│   └── tests/                          # test_hash.c, test_search.c, test_split.c
├── diseno/                             # Documentos de diseño por semana
├── etapa2-evaluacion-distribucion/
│   ├── datasets/generators/            # Generadores de datos (D1 a D5)
│   ├── datasets/workloads/             # W1 a W3, benchmark_runner.py, measure_insertion.py, gráficos
│   ├── datasets/validate/, datasets/load/
│   ├── datasets/output/                # resultados_*.json
│   ├── distributed/                    # Nodos, fragmentación, router y pruebas distribuidas
│   └── informe/                        # Informe final
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 13. Limitaciones

- La estructura no es un método de acceso (`CREATE INDEX ... USING`): se invoca mediante funciones SQL y el planificador no la selecciona.
- No mantiene `UPDATE` ni `DELETE`; no incorpora control de concurrencia ni WAL propio.
- El índice reside en la memoria de cada conexión y se carga desde el archivo al abrirla.
- `eh_search` devuelve el valor almacenado (el identificador), no la ubicación real de la fila.
- La profundidad del directorio tiene un tope de 19 bits (se aborta al alcanzar 20).
- Las mediciones se realizaron en un único equipo con Docker; en el escenario distribuido la red es simulada y los clientes son secuenciales.
- Extendible Hashing no se desplegó en los nodos del escenario distribuido.

## 14. Recursos externos y uso de herramientas de IA

- Se consultó la documentación oficial de PostgreSQL 18 (API de extensiones en C y SPI) y se emplearon Docker, Docker Compose y la biblioteca estándar de C.
- No se reutilizó código de terceros para la estructura: el código de la extensión es desarrollo propio del equipo.
- En la Etapa II se utilizó un asistente de inteligencia artificial (Claude, de Anthropic) como apoyo en la revisión del diseño experimental, la escritura y depuración de scripts de medición y de simulación distribuida, la localización del error del contador de identificadores de bucket y la redacción de borradores del informe. El código entregado fue ejecutado y revisado por el equipo.

## 15. Referencias

- Fagin, R., Nievergelt, J., Pippenger, N., & Strong, H. R. (1979). Extendible Hashing—A Fast Access Method for Dynamic Files. *ACM Transactions on Database Systems*, 4(3), 315–344.
- Silberschatz, A., Korth, H. F., & Sudarshan, S. (2020). *Database System Concepts* (7.ª ed.).
- PostgreSQL Global Development Group. *PostgreSQL 18 Documentation*: Index Access Method Interface y C-Language Functions.
