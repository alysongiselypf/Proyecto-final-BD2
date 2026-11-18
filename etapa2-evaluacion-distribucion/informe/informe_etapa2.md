# Informe de la Etapa II: evaluación experimental y distribución de datos

Este documento reemplaza a `metodologia.md` y `resultados.md`. La introducción, los fundamentos de
Extendible Hashing, el diseño e implementación y la integración con PostgreSQL están en el informe del
parcial y en `implementacion.md`.

## 1. Metodología experimental

### 1.1 Entorno
- PostgreSQL 18.6 (Debian) en Docker; `shared_buffers` = 128 MB, `work_mem` = 4 MB y
  `max_parallel_workers_per_gather` = 2.
- Docker con 20 CPU y 8,1 GB de RAM sobre un Intel Core i9-13900H (14 núcleos, 20 hilos).
- Extensión `eh_index` compilada con buckets de **64 entradas** para las mediciones (la demostración
  usa 4, para que los splits se vean con 23 filas).
- Cliente Python con `psycopg2` conectado a `localhost`.

### 1.2 Datos y cargas de trabajo
- **D1** (enteros secuenciales 1..N) y **D2** (enteros aleatorios únicos, semilla 272), con
  N = 100 000, 500 000 y 1 000 000. Cada generador usa semilla fija y está en el repositorio.
- **W1**: 10 000 búsquedas de claves existentes. **W2**: 10 000 búsquedas de claves ausentes.
  **W3**: inserciones del 10 % del tamaño base, con claves nuevas.
- **W4 y W5** (rango y prefijo) no se aplican: Extendible Hashing solo soporta igualdad.
- D3 (consultas con distribución Zipf, α = 1,5) se generó y se validó, pero **no se incluyó en las
  mediciones**. D4 y D5 no se evalúan porque la clave es `INTEGER`.
- Carga favorable: búsqueda por igualdad (W1 y W2). Carga no favorable: inserciones (W3) y la
  construcción del índice. Los rangos no son soportados.

### 1.3 Escenarios y forma de medir
- Tres escenarios: sin índice (se comprobó con `EXPLAIN` que usa recorrido secuencial paralelo),
  B-tree de PostgreSQL (recorrido solo por índice) y Extendible Hashing.
- Los tres usan la misma forma de invocación: **una consulta por clave** desde el cliente.
- **Repeticiones:** cada medición se repitió 5 veces. Se reporta la **mediana** y el rango
  mínimo–máximo. Se eligió la mediana porque hay valores atípicos: en D2 con 1 000 000 de claves, sin
  índice, el mínimo fue 438,7 s, la mediana 449,8 s y el máximo 1 448 s.
- **Búsqueda:** los escenarios corrieron siempre en el orden sin índice, B-tree, EH.
- **Inserción:** el orden de los escenarios **rota** en cada repetición (cuadrado latino) y se fuerza
  un `CHECKPOINT` antes de medir. Como EH necesita una sentencia distinta (`WITH ... INSERT ...
  RETURNING` más la llamada a `eh_insert`, para una sola ida y vuelta), se agregaron dos controles con
  la misma forma de sentencia y sin llamar a `eh_insert` (sin índice y B-tree). EH solo se compara con
  ellos. En la medición principal el guardado a disco por inserción está desactivado
  (`eh.autosave = off`); se mide aparte con guardado en cada inserción.

### 1.4 Cómo reproducir
- Demostración (buckets de 4): `docker compose up -d --build` y `SELECT eh_build();`, que debe dar
  `gd=5, slots=32`.
- Mediciones (buckets de 64): definir `BUCKET_CAPACITY=64`, reconstruir con `docker compose down -v`,
  `docker compose build` y `docker compose up -d --wait`. Debe dar `gd=2, slots=4`.
- Datos y cargas: generadores en `datasets/generators` y `datasets/workloads`; verificación con
  `datasets/validate/check_workloads.py`.
- Búsqueda: `benchmark_runner.py`. Inserción: `measure_insertion.py`. Gráficos:
  `generar_graficos.py` y `graficos_insercion.py`.
- Distribuido (carpeta `distributed`): `docker compose -f docker-compose-distributed.yml up -d --wait`,
  `python fragment_data.py rango`, `python run_distributed_tests.py rango`, lo mismo con `hash` y
  `python run_distributed_tests.py comparar`.

## 2. Resultados del benchmark

### 2.1 Búsqueda (W1, mediana de 10 000 búsquedas, en segundos)

| Dataset | n | Sin índice | B-tree | EH | EH / B-tree |
|---|---|---|---|---|---|
| D1 | 100 000 | 75,4 | 11,4 | 10,7 | 0,94 |
| D1 | 500 000 | 312,3 | 13,6 | 12,0 | 0,88 |
| D1 | 1 000 000 | 312,9 | 13,5 | 11,9 | 0,88 |
| D2 | 100 000 | 94,2 | 13,7 | 13,6 | 0,99 |
| D2 | 500 000 | 317,0 | 10,4 | 8,7 | 0,84 |
| D2 | 1 000 000 | 449,8 | 13,2 | 11,6 | 0,88 |

- Con 1 000 000 de claves, los dos índices son entre 23 y 39 veces más rápidos que no tener índice.
- EH sale entre un 1 y un 16 % más rápido que B-tree, pero esa diferencia **no debe atribuirse al
  algoritmo** (sección 5.1). El B-tree de D2 fue más lento con 100 000 filas que con 500 000, lo que
  muestra que los niveles absolutos varían entre sesiones: solo se comparan escenarios de un mismo
  experimento.
- W2 (claves ausentes) da tiempos equivalentes a W1 en todos los casos.

### 2.2 Construcción y tamaño del índice

| Dataset | n | Construcción B-tree (s) | Construcción EH (s) | Tamaño B-tree (MB) | Tamaño EH (MB) | EH más pequeño |
|---|---|---|---|---|---|---|
| D1 | 100 000 | 0,07 | 0,73 | 2,26 | 1,66 | 26,7 % |
| D1 | 500 000 | 0,32 | 5,49 | 11,26 | 8,23 | 26,9 % |
| D1 | 1 000 000 | 0,87 | 13,12 | 22,49 | 16,46 | 26,8 % |
| D2 | 100 000 | 0,14 | 1,01 | 2,26 | 1,69 | 25,2 % |
| D2 | 500 000 | 0,37 | 4,48 | 11,26 | 8,39 | 25,4 % |
| D2 | 1 000 000 | 1,13 | 14,41 | 22,49 | 16,78 | 25,4 % |

- Construir EH es entre 7 y 17 veces más lento. El tiempo crece algo más que lineal en D1 (×18 con
  ×10 de datos).
- La ventaja de tamaño de EH es estable, pero **no es una comparación equivalente** (sección 6): el
  tamaño de EH es el del archivo serializado y el de B-tree incluye páginas de 8 KB y cabeceras.

### 2.3 Inserción (W3, mediana en segundos, 10 % de inserciones nuevas)

| Dataset | n | Sin índice | B-tree | Sin índice (CTE) | B-tree (CTE) | EH | EH − B-tree (CTE) | EH más lento en |
|---|---|---|---|---|---|---|---|---|
| D1 | 100 000 | 9,96 | 10,36 | 11,35 | 6,90 | 12,23 | +1,20 | 4 de 5 |
| D1 | 500 000 | 60,43 | 61,33 | 66,26 | 67,11 | 72,43 | +5,54 | 5 de 5 |
| D1 | 1 000 000 | 122,46 | 127,27 | 134,04 | 136,42 | 147,38 | +11,27 | 5 de 5 |
| D2 | 100 000 | 10,53 | 10,77 | 11,62 | 12,49 | 12,81 | +0,48 | 5 de 5 |
| D2 | 500 000 | 60,71 | 62,23 | 66,73 | 68,48 | 71,97 | +3,49 | 5 de 5 |
| D2 | 1 000 000 | 123,62 | 130,05 | 138,97 | 143,61 | 149,74 | +7,25 | 3 de 5 |

- Mantener un B-tree cuesta poco: entre un 1 y un 5 % sobre el `INSERT` simple.
- La forma de sentencia con CTE cuesta cerca de un 10 % más y por eso EH se compara con los controles.
- **Con 500 000 y 1 000 000 de claves, EH es entre un 4 y un 8 % más lento que B-tree** de su misma
  forma. Es el resultado más robusto: salvo D2 con 1 000 000 (3 de 5), fue más lento en las 5
  repeticiones. El sobrecosto es de unos 0,07 a 0,14 ms por inserción y no crece con el tamaño.
- Con 100 000 claves, las repeticiones fueron inestables (por ejemplo, entre 3,4 y 12,5 s en un mismo
  escenario), por lo que esas magnitudes no son fiables.
- Una prueba dentro del servidor mostró que 10 000 llamadas a `eh_insert` en una sola sentencia tardan
  117 ms (unos 12 µs cada una), de modo que el costo de la estructura en memoria es pequeño frente al
  de invocar una función por sentencia.

### 2.4 Costo de la durabilidad por inserción
Con 100 000 claves base, guardar el índice completo en cada inserción tardó 101,9 s en D1 (rango
77,3–157,6 s) y 125,1 s en D2 (98,5–132,9 s), frente a unos 12 s con EH en memoria: entre 7 y 10
veces más. Esta variante se midió solo con 100 000 claves y antes de introducir la rotación y el
`CHECKPOINT`. Al reescribirse el archivo completo en cada inserción, su costo crece con el tamaño del
índice (no se midió con tamaños mayores).

## 3. Diseño distribuido

### 3.1 Escenario
Tres nodos PostgreSQL 18.6 en contenedores (A, B y C) con las latencias de la rúbrica: A-B = 20 ms,
A-C = 40 ms y B-C = 25 ms. Los nodos comparten equipo, así que antes de cada consulta a un nodo
distinto del origen del cliente se espera la latencia del par, una vez por consulta. Las consultas que
necesitan varios nodos se lanzan en paralelo y cuestan la mayor de sus latencias. El origen del cliente
se sortea entre A, B y C en cada operación.

Esquema de cuatro relaciones: `pedido` (1 000 000 de filas), `detalle_pedido` (≈ 2 000 000, entre 1 y
3 líneas por pedido), `usuario` (5 000) y `medicamento` (100).

### 3.2 Fragmentación, asignación y replicación
- **`pedido`**: fragmentación horizontal por `id`, con dos estrategias:
  - **RANGO**: A guarda 1–333 333, B 333 334–666 666 y C 666 667–1 000 000.
  - **HASH**: `id mod 3` = 0 en A, 1 en B y 2 en C.
- **`detalle_pedido`**: fragmentación derivada. Cada detalle se guarda en el nodo de su pedido, de modo
  que el JOIN pedido–detalle es local y la clave foránea se comprueba en el propio nodo.
- **`usuario` y `medicamento`**: replicadas completas en los tres nodos. Son pequeñas, son tablas de
  referencia que usan todas las operaciones y todas las claves foráneas apuntan a ellas; con réplica
  local la lectura no paga latencia y, si un nodo cae, se lee de otro.
- No se replican `pedido` ni `detalle_pedido`: triplicarían el almacenamiento y el costo de cada
  escritura. A cambio, si un nodo cae, sus fragmentos dejan de estar disponibles.
- Una escritura sobre una tabla replicada va a los tres nodos en paralelo, sin protocolo de
  confirmación: si un nodo no responde, queda parcial.

### 3.3 Indexación
- **B-tree en cada fragmento** (claves primarias): resuelve igualdad y rangos, que son las consultas de
  la carga.
- **Extendible Hashing no se despliega en los nodos.** Solo soporta igualdad, el índice de la Etapa I
  vive en la memoria de cada conexión y se carga desde un archivo al abrirla (el router abre una
  conexión por consulta) y no está integrado como método de acceso.

### 3.4 Carga de prueba
- Mezcla de 70 % lecturas y 30 % escrituras; el 80 % de las operaciones sobre `pedido` y el 20 % sobre
  `medicamento` (replicada). Las escrituras no cambian los datos. 1 000 operaciones por repetición.
- **Cambio de concentración:** el 80 % de las operaciones sobre `pedido` va al 10 % de ids más recientes.
- **Consultas de varios nodos:** rango de 10 000 ids (agregado en el nodo), rango de 1 000 ids (trae
  las filas) y un JOIN pedido–detalle filtrado por usuario, que necesita los tres nodos.
- **Caída de un nodo:** se detiene B con `docker stop`, se ejecuta la mezcla y las consultas de rango, y
  se reinicia midiendo el tiempo de recuperación.
- Semilla 272 más el número de repetición; las operaciones son las mismas para ambas estrategias, 5
  repeticiones y mediana.

## 4. Resultados del escenario distribuido

Datos cargados: 333 333 o 333 334 pedidos y unos 666 000 detalles por nodo en ambas estrategias. La
carga de datos tardó 83 s (RANGO) y 191 s (HASH).

| Medida (mediana de 5 repeticiones) | RANGO | HASH |
|---|---|---|
| Mezcla 70/30 uniforme, ms por operación | 55,9 | 55,4 |
| Operaciones locales (ms) | 35,7 | 37,6 |
| Operaciones remotas (ms) | 68,5 | 67,0 |
| Fracción de operaciones locales | 0,39 | 0,41 |
| Mezcla concentrada, ms por operación | 58,0 | 55,3 |
| Parte de la carga en el nodo más cargado | 0,72 | 0,35 |
| Rango de 10 000 ids, ms | 62,9 | 81,7 |
| Nodos consultados en ese rango | 1,02 | 3 |
| Rango de 1 000 ids (trae filas), ms | 59,0 | 79,0 |
| Filas recibidas | 1 000 | 1 000 |
| JOIN que usa los tres nodos, ms | 152,8 | 154,1 |
| Nodo B caído: operaciones exitosas | 0,72 | 0,73 |
| Lecturas de pedido | 0,65 | 0,66 |
| Escrituras de pedido | 0,66 | 0,69 |
| Lecturas de tabla replicada | 1,00 | 1,00 |
| Escrituras de tabla replicada (con algún nodo) | 1,00 | 1,00 |
| Escrituras replicadas solo parciales | 53 | 53 |
| Consultas de rango exitosas | 0,67 | 0,00 |
| Recuperación del nodo (s) | 1,69 | 1,66 |

- La mezcla 70/30 no distingue las estrategias: la diferencia (55,9 frente a 55,4) es menor que la
  variación entre repeticiones (42 a 60 ms).
- **Consultas de rango:** HASH es un 30 % más lento (+19 ms) porque necesita los tres nodos; en las 5
  repeticiones fue más lento que RANGO. La transferencia es la misma (1 000 filas).
- **Concentración de carga:** RANGO manda el 72 % del tráfico al nodo C y HASH lo reparte (35 %), pero
  la latencia casi no cambia (58,0 frente a 55,3 ms) porque los clientes son secuenciales.
- **Caída de B:** en ambas estrategias falla cerca de la tercera parte de las operaciones sobre
  `pedido`. Las tablas replicadas se siguen leyendo, pero todas las escrituras replicadas (53 por
  prueba) se aplicaron solo en 2 de 3 nodos. Con RANGO, el 67 % de los rangos sigue funcionando; con
  HASH, ninguno.
- **JOIN multinodo:** cuesta lo mismo en ambas (≈ 153 ms) porque el JOIN es local en cada nodo. Es lento
  porque no hay índice sobre `pedido.id_usuario` y cada nodo recorre su fragmento.
- Una operación local cuesta ≈ 36 ms. Se atribuye principalmente a abrir una conexión por consulta (no se
  midió por separado); es comparable con las latencias simuladas y diluye las diferencias relativas.

## 5. Discusión

### 5.1 Cuándo funciona mejor o peor Extendible Hashing frente a B-tree
- **Búsqueda por igualdad.** Los dos índices superan por mucho a no tener índice (23 a 39 veces con 1 000
  000 de claves). Entre ellos, la diferencia medida desde el cliente (EH entre 1 y 16 % más rápido) no
  es atribuible al algoritmo: cada consulta cuesta entre 1,1 y 1,4 ms, casi todo de ida y vuelta
  cliente-servidor, mientras que EH resuelve la búsqueda en memoria en microsegundos.
- **Construcción e inserción.** EH es peor: construir tarda entre 7 y 17 veces más y, al insertar, es
  entre un 4 y un 8 % más lento que B-tree con 500 000 y 1 000 000 de claves. La construcción pasa por
  el ciclo completo de hash, localización y posible split para cada clave, sin carga masiva optimizada;
  la causa exacta del crecimiento algo más que lineal no se midió (una hipótesis es el recorrido del
  directorio completo en cada split).
- **Durabilidad.** Mantener el índice persistido en cada inserción cuesta entre 7 y 10 veces más, porque
  se reescribe el archivo completo. Un método de acceso real lo evitaría con el WAL.
- **Rangos.** EH no los soporta; un B-tree sí.
- **Tamaño.** EH ocupa un 25 a 27 % menos, pero en su forma serializada (sección 6).
- **Dónde convendría EH:** lecturas puntuales por clave exacta sobre datos que casi no cambian, con
  conexiones de larga duración. **Dónde no:** consultas de rango, cargas con muchas inserciones o
  actualizaciones, o conexiones que se abren y cierran por consulta.

### 5.2 Estrategias de distribución
- **RANGO** conviene cuando hay consultas por ventanas de ids (las resuelve en un nodo) y cuando
  importa que una caída no deje sin servicio todas las consultas de rango. Su riesgo es la concentración:
  si los accesos se centran en los ids recientes, un nodo recibe cerca del 72 % del tráfico. Con
  clientes secuenciales no se vio efecto en la latencia, pero con carga concurrente un nodo podría
  saturarse (no se midió).
- **HASH** reparte la carga (35 % en el nodo más cargado), pero cada consulta de rango necesita los tres
  nodos: es un 30 % más lenta y falla por completo si cae uno solo.
- Para operaciones puntuales y para el JOIN colocalizado, las estrategias son equivalentes.
- **Replicación:** replicar las tablas pequeñas de referencia mantuvo las lecturas disponibles con un
  nodo caído y eliminó la latencia de lectura. El costo es que las escrituras con un nodo caído dejan las
  réplicas divergentes, sin reconciliación.
- Para esta carga (operaciones puntuales con consultas de rango ocasionales), **RANGO es la opción más
  razonable**, salvo que se esperen accesos fuertemente concentrados bajo carga concurrente.

### 5.3 Dónde usar B-tree y la estructura propia en el escenario distribuido
Se usa B-tree en todos los nodos: la carga incluye consultas de rango y el JOIN filtrado por usuario se
beneficiaría de un índice de igualdad sobre `pedido.id_usuario` (no creado). EH solo sería adecuado para
esa igualdad, con conexiones persistentes y sin actualizaciones. No se desplegó en los nodos, de modo que
esta recomendación se apoya en las mediciones de la Etapa I y en la arquitectura de la implementación, no
en una prueba distribuida.

## 6. Limitaciones y amenazas a la validez

### Estructura de indexación
- No es un método de acceso: se invoca con funciones SQL, el planificador no la elige y no se mantiene con
  `UPDATE` ni `DELETE`. No hay concurrencia ni WAL propio (sección 5.3 de la rúbrica).
- El índice vive en la memoria de cada conexión y se carga desde un archivo al abrirla; una modificación
  sin guardar no la ven las demás conexiones.
- `eh_search` devuelve el valor de la clave almacenada, no la ubicación real de la fila.
- La profundidad del directorio tiene un tope de 19 bits (se aborta al llegar a 20). Con buckets de 4
  entradas, D2 de 100 000 claves lo alcanza, por eso las mediciones usan 64.
- **Tamaño:** el de EH es el del archivo serializado (solo entradas ocupadas, unos 16,5 bytes por clave);
  el de B-tree es `pg_relation_size`, con páginas y cabeceras. Una estructura paginada de EH con buckets
  parcialmente llenos ocuparía más.
- **Tiempos:** se midieron desde un cliente, con 1,1 a 1,4 ms por consulta dominados por la ida y vuelta;
  las diferencias de búsqueda entre B-tree y EH no son atribuibles al algoritmo.
- **Orden:** en búsqueda el orden fue fijo (EH al final); en inserción rotó. Con tamaño base de 100 000
  hubo un tramo con tiempos de 2 a 3 veces menores en todos los escenarios, sin causa comprobada
  (hipótesis: gestión de energía del equipo); las conclusiones de inserción se apoyan en 500 000 y
  1 000 000.
- **Sentencia:** la forma con CTE cuesta cerca de un 10 % más, por eso EH se compara solo con sus controles.
- `eh_autosave` se midió solo con 100 000 claves y en condiciones anteriores a la rotación y al
  `CHECKPOINT`; para tamaños mayores es una extrapolación.
- Los datos caben en memoria (`shared_buffers` de 128 MB y 8 GB de RAM para Docker): se mide CPU y no lectura
  de disco. D3 no se midió. Con cinco repeticiones no se pueden afirmar diferencias menores al 5 %.
  Todo corrió en un solo equipo con Docker en Windows.

### Escenario distribuido
- **Red simulada:** los tres nodos comparten equipo, CPU y disco; las latencias se simulan con esperas
  y no hay pérdida de paquetes, límite de ancho de banda ni contención de red.
- **Costo base:** se abre una conexión por consulta (≈ 36 ms por operación local), comparable con las
  latencias simuladas; no se usó un pool.
- **Clientes secuenciales:** la concentración se mide como reparto de operaciones, no como saturación.
- **Sin transacciones distribuidas:** las escrituras replicadas pueden quedar parciales y las réplicas
  divergir; no hay reconciliación.
- **Caída de un nodo:** se simula con `docker stop` (la conexión se rechaza de inmediato); no se modelan
  esperas, reintentos ni conmutación automática.
- **Datos sintéticos:** ids y usuarios uniformes, entre 1 y 3 líneas por pedido y escrituras que no
  modifican el contenido. Solo se evaluó fragmentar por el id del pedido.
- **EH no desplegado en los nodos.**

## 7. Conclusiones

1. **Estructura:** Extendible Hashing (directorio de punteros, buckets de capacidad fija, split local y
   duplicación del directorio) quedó implementado en C como extensión de PostgreSQL, con construcción,
   búsqueda, inserción y persistencia, y se invoca desde SQL.
2. **Integración:** el código se ejecuta dentro del servidor. Para hacerlo utilizable hubo que resolver
   que el índice vive en memoria por conexión (persistencia en archivo y trigger de sincronización).
3. **Rendimiento:** frente a no tener índice, EH acelera la búsqueda por igualdad entre 7 y 39 veces,
   igual que B-tree. Frente a B-tree no hay una ventaja medible en búsqueda, es 7 a 17 veces más lento al
   construir y entre un 4 y un 8 % más lento al insertar con tamaños grandes; no soporta rangos. Su único
   punto a favor medido es el tamaño del archivo serializado (25 a 27 % menor), con las salvedades de la
   sección 6. Encontrar estos casos desfavorables es un resultado válido (sección 11 de la rúbrica).
4. **Durabilidad:** guardar el índice en cada inserción multiplica el costo entre 7 y 10 veces, lo que
   justifica que un método de acceso real use WAL.
5. **Distribución:** RANGO es preferible para esta carga (rangos un 30 % más rápidos y resistentes a la caída
   de un nodo), con el riesgo de concentrar el tráfico en un nodo; HASH reparte la carga pero depende de los
   tres nodos para cada rango. Replicar las tablas de referencia mantiene las lecturas disponibles a costa
   de escrituras parciales con un nodo caído.
6. **Limitaciones:** la red es simulada, los clientes son secuenciales, EH no se desplegó en los nodos y las
   mediciones corren en un solo equipo.

## 8. Referencias y repositorio
- Fagin, R., Nievergelt, J., Pippenger, N., & Strong, H. R. (1979). Extendible Hashing: A Fast Access
  Method for Dynamic Files. ACM Transactions on Database Systems, 4(3), 315–344.
- Silberschatz, A., Korth, H. F., & Sudarshan, S. (2020). Database System Concepts (7.ª ed.).
- Documentación de PostgreSQL 18: Index Access Method Interface y C-Language Functions.
- Repositorio: https://github.com/alysongiselypf/Proyecto-final-BD2


