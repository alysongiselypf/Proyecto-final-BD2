# Metodología experimental

## Entorno de pruebas
Todos los experimentos se ejecutaron sobre PostgreSQL 18.6 corriendo en
un contenedor Docker Linux, con el esquema de datos definido en la
Etapa I y las tablas de benchmark cargadas mediante el mecanismo
`COPY` nativo de PostgreSQL (ver Semana 8). Las mediciones se
realizaron desde un script cliente en Python (`psycopg2`), conectado
al contenedor vía `localhost:5432`.

## Datasets utilizados
Se emplearon dos familias de datos, ambas obligatorias según la
sección 7.1 de la rúbrica para estructuras orientadas a claves
numéricas:

- **D1 (INTEGER secuencial):** claves únicas en el rango 1..N,
  representando una carga de trabajo "neutra" u ordenada.
- **D2 (INTEGER aleatorio):** claves enteras únicas generadas con
  semilla fija (`SEED=272`), representando una carga de trabajo
  "favorable" para evaluar sensibilidad a la distribución de claves.

Se generaron los tres tamaños obligatorios: 100,000, 500,000 y
1,000,000 de registros, para cada familia de datos.

## Cargas de trabajo (workloads)
- **W1:** 10,000 búsquedas exitosas, muestreadas reproduciblemente
  del dataset base.
- **W2:** 10,000 búsquedas no exitosas, con claves garantizadas
  ausentes.
- **W3:** inserciones equivalentes al 10% del tamaño base del
  dataset, con claves nuevas garantizadas ausentes.

## Escenarios comparados
Siguiendo la sección 6.2 de la rúbrica, se compararon los tres
escenarios obligatorios: acceso sin índice (escaneo secuencial vía
`WHERE id = ANY(array)`), B-tree nativo de PostgreSQL
(`CREATE INDEX ... USING btree`), y la estructura de Extendible
Hashing desarrollada por el grupo (funciones `eh_build_table`,
`eh_search`, `eh_insert`).

## Repeticiones y medida central
Cada experimento de búsqueda se repitió **5 veces**, tal como exige
la sección 8 de la rúbrica. Se reportó la **mediana** de las 5
repeticiones como medida central, en lugar de la media, por su mayor
robustez frente a valores atípicos ocasionales (por ejemplo,
variabilidad puntual del sistema operativo o del planificador de
Docker), que podrían distorsionar el promedio sin representar el
comportamiento típico del sistema.

## Métricas recolectadas
Para cada combinación de dataset, tamaño y escenario, se midieron las
métricas mínimas exigidas por la sección 6.2: tiempo de construcción
del índice, tiempo de búsqueda (exitosa y no exitosa), tamaño del
índice en disco, y comportamiento de inserción.
