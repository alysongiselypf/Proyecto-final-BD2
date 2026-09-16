# Extendible Hashing sobre PostgreSQL — Proyecto Final BD2

**Curso:** CS272 – Bases de Datos II | 2026-II
**Universidad Católica San Pablo**
**Estructura elegida:** Extendible Hashing (hashing dinámico mediante directorio y buckets)

Implementación de Extendible Hashing como estructura de indexación
alternativa a B-tree, integrada como extensión nativa en C dentro de
PostgreSQL 18.6.

Este README documenta el trabajo de la **Etapa I — Indexación**
(Semanas 1 a 5), correspondiente al alcance evaluado en el examen
parcial práctico según la sección 5 de la rúbrica del curso.

## Integrantes

| Integrante | Rol principal en el proyecto |
|---|---|
| Fiorella Flores | Entorno Docker, `eh_build()`, integración general |
| Ruth Benique | Prueba de concepto en C, lectura de datos vía SPI, registro de funciones en PostgreSQL |
| Edison Cama | Estructura de directorio, `eh_insert()` |
| Rodrigo Sierra | Estructura de buckets, tests unitarios |
| Alyson Perez | Función hash, documentación técnica, casos edge |

## Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo (verificar con `docker --version`)
- Git

## Cómo levantar el entorno desde cero

```bash
git clone <URL-del-repositorio>
cd farmacia-bd2
docker compose up -d --build
```

Esto construye la imagen de PostgreSQL 18.6 con la extensión `eh_index`
compilada e instalada, y carga automáticamente el esquema base junto
con los datos de ejemplo (23 medicamentos).

**Verificación rápida:**
```bash
docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "SELECT eh_build();"
docker exec -it farmacia_pg psql -U farmacia_user -d farmacia_db -c "SELECT eh_search(1);"
```
`eh_build()` debe responder `t`. `eh_search(1)` debe devolver el TID de una clave existente.

---

## Semana 1 — Propuesta inicial (entregada)

Se definió la estructura elegida (Extendible Hashing) y se entregó la
propuesta formal, incluyendo: motivación, referencias (Fagin et al.
1979; Silberschatz et al. 2020), representación de la estructura
(directorio + buckets), tipo de clave (`INTEGER`, específicamente
`medicamento.id`), estrategia de integración con PostgreSQL (extensión
en C), riesgos técnicos identificados y plan de trabajo semanal del
equipo.

**Archivo:** `Propuesta_Inicial.pdf` *(no forma parte del código, entregado por separado)*

---

## Semana 2 — Entorno + Prueba de concepto en C + Diseño de estructuras

### Entorno de trabajo (Fiorella)
Se configuró un proyecto Docker separado del repositorio de Software 2,
con PostgreSQL 18.6 sobre contenedor Linux (cumpliendo la sección 8 de
la rúbrica). Se tradujo el esquema original de MariaDB a PostgreSQL,
ajustando tipos (`int(11)→INTEGER`, `decimal→NUMERIC`,
`enum→VARCHAR+CHECK`, `AUTO_INCREMENT→GENERATED ALWAYS AS IDENTITY`) y
agregando una FK que no existía originalmente
(`detalle_pedido.id_medicamento → medicamento.id`).

**Incidencia resuelta:** el volumen de datos de Postgres 18 usa una
convención de montaje distinta a versiones anteriores
(`/var/lib/postgresql` en vez de `/var/lib/postgresql/data`); se
corrigió en `docker-compose.yml`.

**Archivos:** `docker-compose.yml`, `database/schema_postgres.sql`

### Prueba de concepto: función en C dentro de PostgreSQL (Ruth)
Se implementó y verificó el mecanismo completo de extensión en C:
compilación dentro del contenedor → generación de `.so` → registro
vía `CREATE EXTENSION` → ejecución desde SQL. Función de prueba:
`hello_pg_add(a, b)`, verificada con `SELECT hello_pg_add(2,3) = 5`.

**Archivos:** `extension/hello_pg.c`, `hello_pg.control`, `hello_pg--1.0.sql`, `Makefile`, `Dockerfile`

### Diseño de estructuras (Edison, Rodrigo, Alyson)
Se documentó en detalle, antes de escribir código, el diseño de:
- **Directorio** (Edison): arreglo de punteros a buckets, indexado por
  los `global_depth` bits menos significativos del hash; mecanismo de
  duplicación (`directory_double`).
- **Buckets** (Rodrigo): páginas de capacidad fija con pares
  clave-TID, `local_depth` propio, lógica de split.
- **Función hash** (Alyson): función multiplicativa de Knuth
  (`hash = clave * 2654435761 mod 2^32`), justificación de uso de bits
  menos significativos según la convención de Fagin et al. (1979).

**Archivos:** `diseno/directorio_specs.md`, `diseno/buckets_specs.md`, `diseno/funcion_hash_specs.md`

---

## Semana 3 — Construcción del índice

Se implementó en C el núcleo de la estructura, compilable e integrable:

- **`eh_types.h`**: structs compartidos (`Directory`, `Bucket`, `Entry`).
- **`eh_hash.c/.h`** (Alyson): función hash implementada, validada con
  tests unitarios en C puro (`tests/test_hash.c`, corrido sin
  PostgreSQL vía `gcc`), incluyendo verificación de distribución real
  sobre los 23 medicamentos del dataset (resultado: 5/6/6/6 entre 4 slots).
- **`eh_bucket.c/.h`** (Rodrigo): `bucket_create`, `bucket_is_full`,
  `bucket_insert_raw`, `bucket_find`.
- **`eh_directory.c/.h`** (Edison): `directory_create`,
  `directory_index`, `directory_double`.
- **`eh_load_data.c`** (Ruth): lectura de datos reales desde
  PostgreSQL vía SPI (`eh_count_source_rows`), verificada contra la
  tabla `medicamento` (23 filas leídas correctamente).
- **`eh_build.c`** (Fiorella): esqueleto de `eh_build()`, registrado en
  PostgreSQL, verificado con `NOTICE: gd=2, 4 slots`.

**Incidencia resuelta:** PostgreSQL rechazó inicialmente la librería
compilada (`missing magic block`) por falta de la macro
`PG_MODULE_MAGIC;`, requerida una vez por módulo; se agregó en
`eh_build.c`.

---

## Semana 4 — Búsqueda

- **`eh_search()`** (Fiorella): implementada, calcula hash, localiza
  slot y bucket, retorna TID o `NULL`.
- **Registro formal en PostgreSQL** (Ruth): `eh_index--1.0.sql`
  actualizado con `CREATE FUNCTION eh_search`.
- **Tests unitarios de búsqueda** (Edison): `tests/test_search.c`,
  5 casos (búsqueda exitosa/no exitosa, duplicados, determinismo,
  bucket lleno).
- **Manejo de colisiones/edge cases** (Rodrigo): `bucket_contains()`
  para evitar duplicados; `bucket_insert_raw()` rechaza inserción en
  bucket lleno de forma controlada.
- **Documentación técnica parcial** (Alyson):
  `diseno/documentacion_tecnica_parcial.md`.

**Hallazgo documentado:** se identificó que el índice en memoria no
persiste entre conexiones distintas de PostgreSQL (arquitectura
*process-per-connection*), confirmando en la práctica uno de los
riesgos anticipados en la propuesta inicial, y motivando el trabajo de
persistencia de la Semana 6.

**Limitación esperada de esta semana:** con el bucket compartido inicial
(sin split aún implementado), solo 4 de 23 claves lograban insertarse;
el resto se registraba como `WARNING`, documentado explícitamente como
comportamiento esperado en esta etapa del desarrollo.

---

## Semana 5 — Inserción + split

- **Split de bucket, caso `local_depth < global_depth`** (Fiorella):
  `eh_split.c`, redistribuye entradas según el bit adicional del hash,
  actualiza únicamente los slots del directorio que correspondían al
  bucket dividido.
- **Duplicación de directorio, caso `local_depth == global_depth`**
  (Ruth): `eh_insert_core.c`, función central `eh_directory_insert()`
  que decide si duplicar el directorio antes de hacer el split,
  con límite de seguridad de 32 iteraciones para evitar loops
  infinitos ante bugs no previstos.
- **`eh_insert()` integración** (Edison): registrada en PostgreSQL,
  invocable desde SQL.
- **Tests de split/duplicación** (Rodrigo): `tests/test_split.c`,
  4 casos, incluyendo verificación de que las 23 claves se insertan
  completas (vs. las 4 de la Semana 4) y son recuperables tras los
  splits.
- **Casos edge: overflow y duplicados** (Alyson):
  `diseno/casos_edge_semana5.md`.

**Resultado de cierre de la Etapa I:** `eh_build()` sobre las 23 claves
de `medicamento` reporta `insertados=23, omitidos_duplicado=0,
omitidos_lleno=0`, con el directorio creciendo dinámicamente de `gd=2`
a `gd=5` según fue necesario.

---

## Checklist de alcance del examen parcial (sección 5.2 de la rúbrica)

| Requisito | Cumplido |
|---|---|
| Explicar organización, operaciones, complejidad, ventajas, limitaciones | Sí — `diseno/*.md` |
| Código propio para la estructura | Sí |
| Construcción, búsqueda, inserción, split (mínimo exigido para Extendible Hashing) | Sí |
| Integración real con PostgreSQL (no solo programa externo) | Sí — Extensión en C, `CREATE FUNCTION ... LANGUAGE C` |
| Demostrar con datos de prueba que la estructura funciona | Sí — Verificado sobre `medicamento` (23 registros) |
| Código muestra dónde ocurren las operaciones y el flujo desde PostgreSQL | Sí — Módulos separados por responsabilidad |
| Primera comparación con B-tree | Sí |

## Estructura del código (Etapa I)

```
farmacia-bd2/
├── database/
│   └── schema_postgres.sql        # Esquema base (7 tablas)
├── extension/
│   ├── eh_types.h                  # Structs: Directory, Bucket, Entry
│   ├── eh_hash.c / eh_hash.h       # Funcion hash (Semana 3)
│   ├── eh_bucket.c / eh_bucket.h   # Operaciones sobre buckets (Semana 3)
│   ├── eh_directory.c / eh_directory.h  # Operaciones sobre directorio (Semana 3)
│   ├── eh_load_data.c              # Lectura via SPI (Semana 3)
│   ├── eh_build.c                  # eh_build() (Semana 3)
│   ├── eh_search.c                 # eh_search() (Semana 4)
│   ├── eh_split.c / eh_split.h     # Split de bucket (Semana 5)
│   ├── eh_insert_core.c / eh_insert_core.h  # Insercion + duplicacion (Semana 5)
│   ├── eh_insert.c                 # eh_insert() (Semana 5)
│   ├── eh_index--1.0.sql           # Registro de funciones en PostgreSQL
│   ├── eh_index.control
│   ├── hello_pg.c / .control / .sql  # Prueba de concepto inicial (Semana 2)
│   ├── 02_create_extension.sql
│   ├── Makefile
│   ├── Dockerfile
│   └── tests/                      # Tests unitarios en C puro (sin PostgreSQL)
│       ├── test_hash.c             # Semana 3
│       ├── test_search.c           # Semana 4
│       └── test_split.c            # Semana 5
├── diseno/                         # Documentos de diseño por semana
│   ├── directorio_specs.md
│   ├── buckets_specs.md
│   ├── funcion_hash_specs.md
│   ├── documentacion_tecnica_parcial.md
│   └── casos_edge_semana5.md
├── docker-compose.yml
└── README.md
```

## Cómo correr los tests unitarios (sin Docker, C puro)

```bash
cd extension/tests
gcc test_hash.c ../eh_hash.c -o test_hash && ./test_hash
gcc test_search.c ../eh_hash.c ../eh_bucket.c ../eh_directory.c -o test_search && ./test_search
gcc test_split.c ../eh_hash.c ../eh_bucket.c ../eh_directory.c ../eh_split.c ../eh_insert_core.c -o test_split && ./test_split
```

## Recursos externos utilizados

- PostgreSQL 18.6 — documentación oficial de la API de extensiones en
  C (`PG_FUNCTION_INFO_V1`, `fmgr.h`, SPI).
- Docker / Docker Compose para el entorno reproducible.
- Bibliotecas estándar de C — sin dependencias externas para la lógica
  del índice.

No se reutilizó código de terceros para la implementación de
Extendible Hashing; el código de la estructura es desarrollo propio
del equipo.

## Referencias

- Fagin, R., Nievergelt, J., Pippenger, N., & Strong, H. R. (1979).
  Extendible Hashing—A Fast Access Method for Dynamic Files. *ACM
  Transactions on Database Systems*, 4(3), 315-344.
- Silberschatz, A., Korth, H. F., & Sudarshan, S. (2020). *Database
  System Concepts* (7ª ed.).
- Documentación oficial de PostgreSQL 18 — Index Access Method
  Interface, C-Language Functions.
