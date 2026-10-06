"""
D3: INTEGER con acceso sesgado. Usa las claves de D2 (deben generarse
primero) y crea una CARGA DE CONSULTAS con distribucion Zipf sobre
esas claves, simulando que algunas son mucho mas populares que otras
(ej: los medicamentos mas vendidos se consultan con mas frecuencia).

Parametros documentados:
- SEED = 272 (misma semilla base del proyecto, para reproducibilidad)
- ALPHA = 1.5 (parametro de sesgo de la distribucion Zipf; valores
  mas altos concentran mas las consultas en pocas claves "populares")

Uso: python gen_d3_sesgado.py <tamaño> <num_consultas>
Ejemplo: python gen_d3_sesgado.py 100000 10000
"""
import sys
import csv
import os
import random
import numpy as np

SEED = 272
ALPHA = 1.5  # parametro de sesgo Zipf, documentado segun rubrica 7.1

def cargar_claves_d2(n):
    path = f"../output/d2_aleatorio_{n}.csv"
    if not os.path.exists(path):
        print(f"ERROR: no se encontro {path}. Ejecute primero gen_d2_aleatorio.py {n}")
        sys.exit(1)
    claves = []
    with open(path, "r") as f:
        reader = csv.reader(f)
        next(reader)  # saltar header
        for row in reader:
            claves.append(int(row[0]))
    return claves

def generar_d3(n, num_consultas, output_path):
    claves = cargar_claves_d2(n)
    rng = np.random.default_rng(SEED)

    # Distribucion Zipf: genera rangos (1 = mas popular) y los mapea
    # a indices dentro del arreglo de claves de D2.
    rangos_zipf = rng.zipf(ALPHA, size=num_consultas)
    # Recortar valores fuera de rango (Zipf puede generar numeros muy grandes)
    indices = np.clip(rangos_zipf - 1, 0, n - 1)

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id_consultado"])
        for idx in indices:
            writer.writerow([claves[idx]])

    print(f"D3 generado: {num_consultas} consultas sesgadas (Zipf alpha={ALPHA}, seed={SEED}) -> {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python gen_d3_sesgado.py <tamaño> <num_consultas>")
        sys.exit(1)

    n = int(sys.argv[1])
    num_consultas = int(sys.argv[2])
    os.makedirs("../output", exist_ok=True)
    output_path = f"../output/d3_sesgado_{n}_{num_consultas}.csv"
    generar_d3(n, num_consultas, output_path)
