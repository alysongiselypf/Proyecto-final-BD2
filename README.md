# Extendible Hashing sobre PostgreSQL — Proyecto Final BD2

**Curso:** CS272 – Bases de Datos II | 2026-II
**Universidad Católica San Pablo**

Implementación de Extendible Hashing como estructura de indexación
alternativa a B-tree, integrada como extensión nativa en C dentro de
PostgreSQL 18.6, con evaluación experimental comparativa y diseño de
distribución en 3 nodos.

## Integrantes

- Fiorella Flores
- Ruth Benique
- Edison Cama
- Rodrigo Sierra
- Alyson Perez

## Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo
- Python 3.10+ con `pip`
- Git

## Estructura del repositorio

```
farmacia-bd2/
├── database/
│   └── schema_postgres.sql       # Esquema base (7 tablas), traducido de MariaDB
├── extension/                    # Extension en C: Extendible Hashing
│   ├── eh_types.h                # Structs compartidos (Directory, Bucket, Entry)
│   ├── eh_hash.c/.h              # Funcion hash multiplicativa (Knuth)
│   ├── eh_bucket.c/.h            # Operaciones sobre buckets
│   ├── eh_directory.c/.h         # Operaciones sobre el directorio
│   ├── eh_split.c/.h             # Split de bucket + reasignacion de slots
│   ├── eh_insert_core.c/.h       # Logica de insercion con split/duplicacion
│   ├── eh_build.c                # eh_build(), eh_build_table(), _PG_init()
│   ├── eh_search.c               # eh_search()
│   ├── eh_insert.c               # eh_insert()
│   ├── eh_persist.c              # Serializacion binaria a disco
│   ├── eh_persist_pg.c           # eh_save(), eh_load(), eh_index_size()
│   ├── eh_trigger.c              # Trigger AFTER INSERT (sincronizacion)
│   ├── eh_load_data.c            # Lectura de datos via SPI
│   ├── eh_index--1.0.sql         # Registro de funciones en PostgreSQL
│   ├── eh_index.control
│   ├── hello_pg.c/.control/.sql  # Prueba de concepto inicial (C -> PostgreSQL)
│   ├── 02_create_extension.sql
│   ├── 03_create_eh_extension.sql
│   ├── 04_create_trigger.sql
│   ├── Makefile
│   ├── Dockerfile
│   └── tests/                    # Tests unitarios en C puro (sin PostgreSQL)
│       ├── test_hash.c
│       ├── test_search.c
│       ├── test_split.c
│       └── test_persist.c
├── datasets/
│   ├── generators/                # Generadores D1-D5 (reproducibles, seed=272)
│   ├── load/                      # Carga masiva via COPY
│   ├── validate/                  # Validacion de integridad
│   ├── workloads/                 # W1-W3, benchmark runner, graficos
│   └── output/                    # CSVs y resultados generados (no versionado, ver .gitignore)
├── distributed/                   # Escenario distribuido (3 nodos, seccion 6.3)
│   ├── docker-compose-distributed.yml
│   ├── schema_distributed.sql
│   ├── fragment_data.py
│   ├── query_router.py
│   └── run_distributed_tests.py
├── diseno/                        # Documentos de diseño por semana
├── informe/                       # Secciones del informe final
├── docker-compose.yml             # Entorno principal (1 nodo)
└── README.md
```

## Cómo levantar el entorno desde cero

### 1. Entorno principal (indexación, Etapa I)

```bash
git clone <URL-del-repositorio>
cd farmacia-bd2
docker compose up -d --build
```

Esto construye la imagen de PostgreSQL 18.6 con la extensión `eh_index` compilada, carga el esquema base y los datos de ejemplo de `medicamento` (23 registros).

**Verificar que todo funciona:**
```bash
docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "SELECT eh_build();"
docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "SELECT eh_search(1);"
```

### 2. Generar datasets y ejecutar benchmarks (Etapa II)

```bash
cd datasets/generators
pip install numpy
python gen_d1_secuencial.py 100000
python gen_d1_secuencial.py 500000
python gen_d1_secuencial.py 1000000
python gen_d2_aleatorio.py 100000
python gen_d2_aleatorio.py 500000
python gen_d2_aleatorio.py 1000000

cd ../load
pip install psycopg2-binary
python load_dataset.py ../output/d1_secuencial_100000.csv bench_d1_100000
python load_dataset.py ../output/d1_secuencial_500000.csv bench_d1_500000
python load_dataset.py ../output/d1_secuencial_1000000.csv bench_d1_1000000
python load_dataset.py ../output/d2_aleatorio_100000.csv bench_d2_100000
python load_dataset.py ../output/d2_aleatorio_500000.csv bench_d2_500000
python load_dataset.py ../output/d2_aleatorio_1000000.csv bench_d2_1000000

cd ../workloads
python gen_w1_w2.py ../output/d1_secuencial_100000.csv 100000
# (repetir para cada combinacion dataset/tamaño, ver detalle en datasets/workloads/README.md)

python benchmark_runner.py       # Comparacion sin_indice vs B-tree vs Extendible Hashing
python measure_insertion.py      # W3: comportamiento de insercion
python resumen_benchmark.py      # Consolida metricas en tabla
python generar_graficos.py       # Genera PNGs en ../output/graficos/
```

### 3. Escenario distribuido (3 nodos)

```bash
cd distributed
docker compose -f docker-compose-distributed.yml up -d
pip install psycopg2-binary
python fragment_data.py          # Genera y fragmenta 1,000,000+ registros
python run_distributed_tests.py  # Carga 70/30, nodo caido, cambio de concentracion
```

## Resumen de lo implementado

### Etapa I — Indexación (Extendible Hashing)

- **Estructura:** directorio dinámico (arreglo de punteros a buckets, indexado por bits menos significativos del hash) + buckets de capacidad fija (`BUCKET_CAPACITY=64`).
- **Función hash:** multiplicativa de Knuth (`hash = clave * 2654435761 mod 2^32`), determinística.
- **Operaciones implementadas:** construcción (`eh_build`, `eh_build_table`), búsqueda (`eh_search`), inserción con split y duplicación de directorio (`eh_insert`), persistencia a disco con carga automática (`_PG_init`), trigger de sincronización (`AFTER INSERT`).
- **Integración con PostgreSQL:** extensión nativa en C, compilada como `.so`, registrada vía `CREATE EXTENSION`. Las funciones se invocan directamente desde SQL.

### Etapa II — Evaluación y distribución

- **Datasets generados:** D1 (secuencial), D2 (aleatorio), D3 (sesgado, Zipf), D4/D5 (VARCHAR, generados por completitud, no aplicables a Extendible Hashing según su diseño de solo-igualdad).
- **Workloads:** W1 (búsqueda exitosa), W2 (búsqueda no exitosa), W3 (inserción 10%). W4/W5 no aplican (estructura solo soporta igualdad).
- **Benchmark:** comparación sin_índice / B-tree / Extendible Hashing, 3 tamaños (100k/500k/1M), 5 repeticiones por experimento, datasets D1 y D2.
- **Escenario distribuido:** 3 nodos PostgreSQL (A, B, C) en Docker, latencias simuladas (A-B=20ms, A-C=40ms, B-C=25ms), esquema con 4 relaciones vinculadas, ≥1,000,000 registros en la relación principal (`pedido`), 2 estrategias de fragmentación comparadas (rango vs hash), replicación completa de tablas pequeñas (`usuario`, `medicamento`).

## Resultados principales (ver `informe/resultados.md` para el detalle completo)

| Métrica | B-tree | Extendible Hashing |
|---|---|---|
| Tamaño en disco (1M registros) | 21,960 KB | 16,073 KB (~27% menor) |
| Tiempo de construcción (1M) | ~0.7s | ~11-14s |
| Tiempo de inserción W3 (100k filas nuevas) | 119.5s | 127-131s (+~7-10%) |

## Recursos externos utilizados

- PostgreSQL 18.6 — documentación oficial de la API de extensiones en C (`PG_FUNCTION_INFO_V1`, `fmgr.h`, SPI).
- Docker / Docker Compose para el entorno reproducible.
- Bibliotecas estándar de C (sin dependencias externas para la lógica del índice).
- Python: `psycopg2`, `numpy`, `matplotlib` (solo para scripts auxiliares de generación de datos, carga y análisis — no forman parte de la extensión en C).

No se reutilizó código de terceros para la implementación de Extendible Hashing; el código de la estructura es desarrollo propio del equipo.

## Referencias

- Fagin, R., Nievergelt, J., Pippenger, N., & Strong, H. R. (1979). Extendible Hashing—A Fast Access Method for Dynamic Files. *ACM Transactions on Database Systems*, 4(3), 315-344.
- Silberschatz, A., Korth, H. F., & Sudarshan, S. (2020). *Database System Concepts* (7ª ed.).
- Documentación oficial de PostgreSQL 18 — Index Access Method Interface, C-Language Functions.
