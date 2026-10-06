# W4 y W5 — No aplicables a Extendible Hashing

Según la propuesta inicial (sección 4), Extendible Hashing soporta
únicamente consultas por igualdad, no por rango ni por prefijo. La
rúbrica (sección 7.2) confirma que W4 (búsquedas por rango) aplica
"cuando la estructura soporte naturalmente esta operación" y W5
(búsquedas por prefijo) aplica "para Radix Tree y estructuras donde
corresponda". Ninguno de los dos es un requisito para este grupo.

Esta limitación es consistente con el diseño de la estructura elegida
desde la propuesta, y se retoma en el análisis final (Semana 10) al
discutir las ventajas y limitaciones de Extendible Hashing frente a
B-tree, que sí soporta ambos tipos de consulta de forma nativa.
