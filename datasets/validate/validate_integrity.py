"""
Valida la integridad de los datasets generados antes de usarlos en
pruebas: verifica unicidad de claves, tamaño exacto esperado, y
(para D3) que la distribucion de consultas efectivamente sea sesgada
y no uniforme.

Uso: python validate_integrity.py <ruta_csv> <tamaño_esperado>
"""
import sys
import csv
from collections import Counter

def validar(csv_path, tamaño_esperado):
    valores = []
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        next(reader)  # header
        for row in reader:
            valores.append(row[0])

    total = len(valores)
    unicos = len(set(valores))

    print(f"--- Validacion: {csv_path} ---")
    print(f"Total de filas: {total} (esperado: {tamaño_esperado})")
    print(f"Valores unicos: {unicos}")

    if total != tamaño_esperado:
        print(f"  [FALLO] El tamaño no coincide con lo esperado")
    else:
        print(f"  [OK] Tamaño correcto")

    es_workload = "id_consultado" in open(csv_path).readline()

    if not es_workload:
        if unicos != total:
            print(f"  [FALLO] Hay {total - unicos} valores duplicados (se esperaban claves unicas)")
        else:
            print(f"  [OK] Todas las claves son unicas")
    else:
        # Para D3 (carga de consultas), los duplicados son ESPERADOS
        # (es justamente lo que produce el sesgo Zipf)
        contador = Counter(valores)
        top5 = contador.most_common(5)
        print(f"  [INFO] Dataset de workload sesgado - duplicados esperados")
        print(f"  Top 5 claves mas consultadas: {top5}")
        concentracion = sum(c for _, c in top5) / total * 100
        print(f"  Las 5 claves mas populares concentran el {concentracion:.1f}% de las consultas")
        if concentracion < 5:
            print(f"  [ADVERTENCIA] Concentracion baja, revisar si el sesgo Zipf se aplico correctamente")
        else:
            print(f"  [OK] Distribucion efectivamente sesgada")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python validate_integrity.py <ruta_csv> <tamaño_esperado>")
        sys.exit(1)

    validar(sys.argv[1], int(sys.argv[2]))
