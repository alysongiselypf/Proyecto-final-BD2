"""
W1: 10,000 búsquedas exitosas por igualdad (claves existentes, muestreo reproducible)
W2: 10,000 búsquedas no exitosas (claves garantizadas ausentes)
W3 (solo D2): inserciones del 10 % del tamaño inicial, claves nuevas aleatorias,
              disjuntas de D2 y de W2 (para D1, W3 lo genera gen_w3.py)
D1 (claves densas 1..N): las ausentes solo pueden estar por encima del máximo.
D2 (claves dispersas): W2 y W3 se muestrean al azar en 1..10N, sin ordenar.
Uso: python gen_w1_w2.py <ruta_dataset_csv> <tamaño_dataset>
"""
import sys, csv, os, random

SEED = 272
N_QUERIES = 10000

def escribir(path, claves):
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id"])
        for k in claves: w.writerow([k])

def generar(csv_path, n, output_prefix):
    with open(csv_path) as f:
        reader = csv.reader(f); next(reader)
        claves = [int(row[0]) for row in reader]

    rng = random.Random(SEED)
    w1 = rng.sample(claves, N_QUERIES)
    escribir(f"{output_prefix}_w1.csv", w1)

    existentes = set(claves)
    denso = (max(claves) == len(claves))   # D1: claves 1..N

    if denso:
        # D1: no hay huecos, las ausentes van por encima del maximo
        ausentes = []
        candidato = max(claves) + 1
        while len(ausentes) < N_QUERIES:
            if candidato not in existentes:
                ausentes.append(candidato)
            candidato += 1
    else:
        # D2: W2 y W3 aleatorias en 1..10N, disjuntas entre si y de D2
        necesarias = N_QUERIES + n // 10
        pool, vistas = [], set()
        while len(pool) < necesarias:
            k = rng.randint(1, 10 * n)
            if k not in existentes and k not in vistas:
                vistas.add(k)
                pool.append(k)
        ausentes = pool[:N_QUERIES]   # W2
        w3 = pool[N_QUERIES:]         # W3
        escribir(f"{output_prefix}_w3.csv", w3)
        print(f"W3: {len(w3)} claves nuevas aleatorias -> {output_prefix}_w3.csv")

    escribir(f"{output_prefix}_w2.csv", ausentes)

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

