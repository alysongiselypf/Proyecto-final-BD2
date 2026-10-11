"""
W1: 10,000 búsquedas exitosas por igualdad (claves existentes, muestreo reproducible)
W2: 10,000 búsquedas no exitosas (claves garantizadas ausentes)
Uso: python gen_w1_w2.py <ruta_dataset_csv> <tamaño_dataset>
"""
import sys, csv, os, random

SEED = 272
N_QUERIES = 10000

def generar(csv_path, n, output_prefix):
    with open(csv_path) as f:
        reader = csv.reader(f); next(reader)
        claves = [int(row[0]) for row in reader]

    rng = random.Random(SEED)
    w1 = rng.sample(claves, N_QUERIES)

    with open(f"{output_prefix}_w1.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id"])
        for k in w1: w.writerow([k])

    existentes = set(claves)
    ausentes = []
    candidato = max(claves) + 1
    while len(ausentes) < N_QUERIES:
        if candidato not in existentes:
            ausentes.append(candidato)
        candidato += 1

    with open(f"{output_prefix}_w2.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id"])
        for k in ausentes: w.writerow([k])

    print(f"W1: {len(w1)} claves existentes -> {output_prefix}_w1.csv")
    print(f"W2: {len(ausentes)} claves ausentes -> {output_prefix}_w2.csv")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python gen_w1_w2.py <csv> <tamaño>")
        sys.exit(1)
    csv_path, n = sys.argv[1], int(sys.argv[2])
    os.makedirs("../output", exist_ok=True)
    prefix = f"../output/workload_{os.path.basename(csv_path).replace('.csv','')}"
    generar(csv_path, n, prefix)
