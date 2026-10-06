# Documentación técnica parcial — Semana 4

## Estado del índice al cierre de la Semana 4

- Directorio inicializado con profundidad global fija (gd = 2, 4 slots).
- Todos los slots del directorio apuntan actualmente al mismo bucket
  compartido (capacidad fija = 4 entradas). La separación real en
  buckets independientes por slot, junto con el split dinámico, se
  implementa en la Semana 5.
- `eh_build()` lee la tabla `medicamento` completa vía SPI, calcula el
  hash de cada `id`, y lo inserta en el bucket correspondiente. Como el
  bucket compartido tiene capacidad 4, solo las primeras 4 claves
  procesadas se insertan correctamente; el resto se registra como
  advertencia (`WARNING`) en los logs, documentando explícitamente esta
  limitación conocida hasta que el split esté implementado.
- `eh_search(id)` calcula el hash de la clave buscada, localiza el slot
  vía `directory_index`, y busca linealmente dentro del bucket
  correspondiente. Retorna el TID si la clave existe, o `NULL` si no.

## Manejo de edge cases (Semana 4)

- **Duplicados:** `bucket_contains()` se usa dentro de `eh_build()` para
  evitar insertar la misma clave dos veces si el proceso se ejecuta
  repetidamente sin reiniciar el índice.
- **Bucket lleno:** `bucket_insert_raw()` retorna `false` de forma
  controlada (sin crash) cuando el bucket alcanza su capacidad,
  permitiendo que `eh_build()` continúe procesando el resto de las
  filas sin interrumpirse.
- **Índice no construido:** `eh_search()` valida que `g_index` no sea
  `NULL` antes de operar, y lanza un error SQL descriptivo
  (`elog(ERROR, ...)`) si se llama antes de ejecutar `eh_build()`.
- **Clave inexistente:** `eh_search()` retorna `NULL` de forma explícita
  (vía `PG_RETURN_NULL()`) en lugar de fallar, permitiendo diferenciarlo
  de una búsqueda exitosa.

## Limitación conocida y plan de resolución (Semana 5)

El bucket compartido inicial se satura rápidamente porque el directorio
aún no distribuye claves en buckets separados por slot. Esto es
esperado en esta etapa: la Semana 5 implementa la lógica de split
(`ld < gd` → split local; `ld == gd` → duplicación de directorio +
split), que separará las claves en buckets independientes y permitirá
insertar el dataset completo sin pérdidas.
