# Introducción y motivación

Este proyecto implementa Extendible Hashing como estructura de
indexación alternativa a B-tree dentro de PostgreSQL 18.6, en el
marco del curso CS272 - Bases de Datos II. El objetivo es comprender
en profundidad el funcionamiento interno de una estructura de
indexación dinámica basada en hashing, integrarla de forma funcional
con un sistema gestor de bases de datos real, y evaluar
experimentalmente su comportamiento frente a las alternativas
estándar (acceso sin índice y B-tree nativo).

Se eligió Extendible Hashing por su alcance operacional manejable
dentro del tiempo disponible, su enfoque en consultas de igualdad —
permitiendo concentrar el esfuerzo de integración en el ciclo
construcción-búsqueda-inserción sin la complejidad adicional de
soporte de rangos —, y por representar un caso de estudio interesante
de crecimiento dinámico (duplicación de directorio y split de
buckets) comparable al comportamiento de B-tree ante volúmenes
crecientes de datos.

# Conclusiones

El desarrollo del proyecto permitió comprobar, en la práctica, varias
afirmaciones teóricas sobre Extendible Hashing: su eficiencia en
espacio de almacenamiento frente a B-tree se confirmó
experimentalmente (aproximadamente 26-27% menos espacio en disco en
todos los tamaños evaluados), consistente con la ausencia de overhead
estructural propio de los árboles balanceados.

Al mismo tiempo, el proceso reveló limitaciones reales de una
implementación académica frente a un motor de producción como
PostgreSQL: el tiempo de construcción resultó significativamente
mayor que B-tree, principalmente por la ausencia de un mecanismo de
carga masiva optimizado — una limitación de implementación, no del
algoritmo en sí, y coherente con el alcance definido por la rúbrica
para un semestre académico (sección 5.3: "no un método de acceso
completo de PostgreSQL").

El proceso de depuración durante la Semana 9 —que incluyó la
identificación y corrección de un crecimiento cuadrático en el
algoritmo de split, un problema de compatibilidad de formato de
archivo, una fuga de memoria, y un error de correctitud en la
reasignación de punteros tras la duplicación del directorio— resultó
formativo en sí mismo: expuso al equipo a un ciclo real de
diagnóstico de sistemas (monitoreo de procesos, análisis de logs del
servidor, razonamiento sobre complejidad algorítmica) que trasciende
la implementación inicial del algoritmo y reflejó el tipo de trabajo
esperado en el manejo de estructuras de datos persistentes a escala.

Como trabajo futuro, se identifican dos extensiones naturales: la
implementación de un modo de carga masiva para `eh_build_table()`
que reduzca la brecha de tiempo de construcción frente a B-tree, y
el manejo de eliminación de registros (`DELETE`), actualmente no
soportado por el trigger de sincronización existente, que solo
reacciona a inserciones.

# Referencias

- Fagin, R., Nievergelt, J., Pippenger, N., & Strong, H. R. (1979).
  Extendible Hashing—A Fast Access Method for Dynamic Files. ACM
  Transactions on Database Systems, 4(3), 315-344.
- Silberschatz, A., Korth, H. F., & Sudarshan, S. (2020). Database
  System Concepts (7ª ed.), capítulo de organización de índices
  basados en hashing dinámico.
- Documentación oficial de PostgreSQL 18 — "Index Access Method
  Interface Definition" y "C-Language Functions".
- Repositorio del proyecto: [enlace al repositorio Git del grupo]
