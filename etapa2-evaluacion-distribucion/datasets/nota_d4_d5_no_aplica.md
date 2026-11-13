# D4 y D5: no aplican al benchmark

D4 (VARCHAR) y D5 (prefijos) se generaron y validaron con 100 000 registros, pero no se evaluan en este proyecto: la estructura implementada (Extendible Hashing) indexa claves INTEGER y solo soporta busqueda por igualdad. D5 esta pensado para prefijos, que un hash no puede resolver. Su ausencia en los resultados es una decision de alcance, no un pendiente.
