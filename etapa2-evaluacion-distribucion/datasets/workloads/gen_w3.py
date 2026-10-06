"""
W3: Inserciones - 10% adicional respecto al tamaño inicial del dataset.
Claves nuevas, garantizadas ausentes en el dataset original.
Uso: python gen_w3.py <ruta_dataset_csv> <tamaño_dataset>
"""
import sys, csv, os

def generar(csv_path, n, output_path):
    with open(csv_path) as f:
        reader = csv.reader(f); next(reader)
        claves = set(int(row[0]) for row in reader)

    n_nuevas = int(n * 0.10)
    nuevas = []
    candidato = max(claves) + 1
    while len(nuevas) < n_nuevas:
        if candidato not in claves:
            nuevas.append(candidato)
        candidato += 1

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
