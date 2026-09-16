"""
D2: INTEGER aleatorio. Claves enteras aleatorias, unicas, reproducibles.
Semilla documentada: SEED = 272 (fija, curso CS272 - Bases de Datos II).
Uso: python gen_d2_aleatorio.py <tamaño>
"""
import sys
import csv
import os
import random

SEED = 272  # Semilla fija para reproducibilidad, documentada segun rubrica 7.1

def generar_d2(n, output_path):
    rng = random.Random(SEED)
    # Se genera un rango amplio (10x el tamaño) para asegurar unicidad
    # sin colisiones excesivas, y se muestrea sin reemplazo.
    rango_max = n * 10
    claves = rng.sample(range(1, rango_max + 1), n)

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id"])
        for clave in claves:
            writer.writerow([clave])

    print(f"D2 generado: {n} claves aleatorias unicas (seed={SEED}) -> {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python gen_d2_aleatorio.py <tamaño>")
        sys.exit(1)

    n = int(sys.argv[1])
    os.makedirs("../output", exist_ok=True)
    output_path = f"../output/d2_aleatorio_{n}.csv"
    generar_d2(n, output_path)
