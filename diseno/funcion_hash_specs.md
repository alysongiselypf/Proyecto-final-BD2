# Diseño de la Función Hash — Extendible Hashing

## Requisito
La clave es `medicamento.id` (INTEGER de PostgreSQL, 4 bytes con signo).

## Función elegida
Multiplicativa simple (Knuth), buena distribución, barata de calcular,
determinística (importante para reproducibilidad según la rúbrica).
FUNCION hash_function(clave: INTEGER) -> UINT32:
// Constante de Knuth: 2^32 * (razón áurea)
A = 2654435761 (uint32)
h = (clave * A) mod 2^32
RETORNAR h

## En C

```c
uint32_t hash_function(int32_t key) {
    uint32_t k = (uint32_t)key;
    return k * 2654435761u;   // overflow de uint32 es comportamiento definido
                               // (wrap-around), actúa como mod 2^32
}
```

## Extracción de bits para indexar (usada por el directorio)
FUNCION get_bits(h: UINT32, n_bits: INTEGER) -> INTEGER:
RETORNAR h AND ((1 << n_bits) - 1) // toma los n_bits menos significativos

## Por qué bits menos significativos (LSB) y no MSB
Es la convención estándar en Extendible Hashing (Fagin et al. 1979, la
referencia ya citada en la propuesta) porque permite que al duplicar el
directorio, los slots viejos conserven su posición y solo se agreguen los
nuevos, sin tener que reordenar el arreglo completo — solo se le agrega
prefijo por el lado del bit más significativo del índice.

## Casos límite a documentar en los tests unitarios (Semana 3)
- Claves negativas (no debería haberlas en `medicamento.id`, pero conviene
  validar que `PG_GETARG_INT32` no las deje pasar sin control, o documentar
  que se asume `id > 0`).
- Clave `0` (caso borde de la multiplicación).
- Distribución: correr el hash sobre los 23 medicamentos actuales de la tabla
  y verificar visualmente que no caen todos en el mismo bucket.
