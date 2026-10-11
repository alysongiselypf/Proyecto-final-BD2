"""
D1: INTEGER secuencial. Claves unicas 1..N.
Uso: python gen_d1_secuencial.py <tamaño>
Ejemplo: python gen_d1_secuencial.py 100000
"""
import sys
import csv
import os

def generar_d1(n, output_path):
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id"])
        for i in range(1, n + 1):
            writer.writerow([i])
    print(f"D1 generado: {n} claves secuenciales -> {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python gen_d1_secuencial.py <tamaño>")
        sys.exit(1)

    n = int(sys.argv[1])
    os.makedirs("../output", exist_ok=True)
    output_path = f"../output/d1_secuencial_{n}.csv"
    generar_d1(n, output_path)
