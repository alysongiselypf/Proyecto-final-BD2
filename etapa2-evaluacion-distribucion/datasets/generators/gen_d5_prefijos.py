"""
D5: VARCHAR con prefijos compartidos. Cadenas agrupadas por prefijos,
reproducibles.

Nota de alcance: igual que D4, no es requisito obligatorio para
Extendible Hashing segun la rubrica (7.1) — se genera por completitud.

Semilla documentada: SEED = 272.
Se generan PREFIJOS_BASE prefijos distintos, y cada clave se arma
concatenando un prefijo elegido al azar + un sufijo aleatorio corto,
simulando datos con estructura jerarquica compartida (ej: codigos de
producto por categoria).

Uso: python gen_d5_prefijos.py <tamaño>
"""
import sys
import csv
import os
import random
import string

SEED = 272
PREFIJOS_BASE = 20
LARGO_PREFIJO = 4
LARGO_SUFIJO = 8

def generar_d5(n, output_path):
    rng = random.Random(SEED)
    alfabeto = string.ascii_lowercase

    prefijos = [
        "".join(rng.choices(alfabeto, k=LARGO_PREFIJO))
        for _ in range(PREFIJOS_BASE)
    ]

    vistos = set()
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["valor"])
        while len(vistos) < n:
            prefijo = rng.choice(prefijos)
            sufijo = "".join(rng.choices(alfabeto + string.digits, k=LARGO_SUFIJO))
            cadena = prefijo + sufijo
            if cadena not in vistos:
                vistos.add(cadena)
                writer.writerow([cadena])

    print(f"D5 generado: {n} cadenas con {PREFIJOS_BASE} prefijos compartidos (seed={SEED}) -> {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python gen_d5_prefijos.py <tamaño>")
        sys.exit(1)

    n = int(sys.argv[1])
    os.makedirs("../output", exist_ok=True)
    output_path = f"../output/d5_prefijos_{n}.csv"
    generar_d5(n, output_path)
