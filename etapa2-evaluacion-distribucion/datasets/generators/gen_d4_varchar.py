"""
D4: VARCHAR aleatorio. Cadenas alfanumericas reproducibles, longitud
fija.

Nota de alcance: Extendible Hashing (nuestra estructura) solo indexa
claves INTEGER segun la propuesta inicial. D4 no es un requisito
obligatorio para nuestra estructura segun la seccion 7.1 de la
rubrica (aplica a estructuras orientadas a texto, como Radix Tree).
Se genera igualmente por completitud del repositorio y como insumo
potencial para comparaciones adicionales, no para indexarlo con EH.

Semilla documentada: SEED = 272.
Longitud fija: LONGITUD = 12 caracteres.

Uso: python gen_d4_varchar.py <tamaño>
"""
import sys
import csv
import os
import random
import string

SEED = 272
LONGITUD = 12

def generar_d4(n, output_path):
    rng = random.Random(SEED)
    alfabeto = string.ascii_lowercase + string.digits
    vistos = set()

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["valor"])
        while len(vistos) < n:
            cadena = "".join(rng.choices(alfabeto, k=LONGITUD))
            if cadena not in vistos:
                vistos.add(cadena)
                writer.writerow([cadena])

    print(f"D4 generado: {n} cadenas VARCHAR unicas (longitud={LONGITUD}, seed={SEED}) -> {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python gen_d4_varchar.py <tamaño>")
        sys.exit(1)

    n = int(sys.argv[1])
    os.makedirs("../output", exist_ok=True)
    output_path = f"../output/d4_varchar_{n}.csv"
    generar_d4(n, output_path)
