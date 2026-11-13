"""
W3 (solo D1, claves densas 1..N): Inserciones - 10% adicional respecto al tamaño inicial.
Claves nuevas, ausentes del dataset y disjuntas de W2 (que ocupa max+1..max+10000).
Para D2 las inserciones las genera gen_w1_w2.py (aleatorias en 1..10N).
Uso: python gen_w3.py <ruta_dataset_csv> <tamaño_dataset>
"""
import sys, csv, os

N_QUERIES_W2 = 10000   # tamaño del bloque de W2 que hay que saltar

def generar(csv_path, n, output_path):
    with open(csv_path) as f:
        reader = csv.reader(f); next(reader)
        claves = set(int(row[0]) for row in reader)

    if max(claves) != len(claves):
        print("Este script es solo para datasets densos (D1). "
              "Para D2, W3 lo genera gen_w1_w2.py.")
        sys.exit(1)

    n_nuevas = n // 10
    inicio = max(claves) + N_QUERIES_W2 + 1      # salta el bloque de W2
    nuevas = list(range(inicio, inicio + n_nuevas))

    with open(output_path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id"])
        for k in nuevas: w.writerow([k])

    print(f"W3: {len(nuevas)} claves nuevas (10% de {n}) -> {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python gen_w3.py <csv> <tamaño>")
        sys.exit(1)
    csv_path, n = sys.argv[1], int(sys.argv[2])
    os.makedirs("../output", exist_ok=True)
    output_path = f"../output/workload_{os.path.basename(csv_path).replace('.csv','')}_w3.csv"
    generar(csv_path, n, output_path)


