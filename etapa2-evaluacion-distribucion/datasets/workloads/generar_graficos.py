"""
Genera los graficos comparativos a partir de resultados_benchmark.json
y resultados_insercion.json. Guarda PNGs en ../output/graficos/

Requiere: pip install matplotlib
"""
import json
import os
import matplotlib.pyplot as plt

os.makedirs("../output/graficos", exist_ok=True)

with open("../output/resultados_benchmark.json") as f:
    bench = json.load(f)

with open("../output/resultados_insercion.json") as f:
    insert = json.load(f)

def por_dataset(datos, dataset):
    return sorted([r for r in datos if r["dataset"] == dataset], key=lambda r: r["tamaño"])

# --- Grafico 1: Tiempo de busqueda W1 (sin_indice vs btree vs eh) ---
for dataset in ["d1_secuencial", "d2_aleatorio"]:
    filas = por_dataset(bench, dataset)
    tamaños = [r["tamaño"] for r in filas]
    sin_idx = [r["sin_indice_w1"]["mediana"] for r in filas]
    btree = [r["btree_w1"]["mediana"] for r in filas]
    eh = [r["eh_w1"]["mediana"] for r in filas]

    plt.figure(figsize=(7, 5))
    plt.plot(tamaños, sin_idx, marker="o", label="Sin indice")
    plt.plot(tamaños, btree, marker="o", label="B-tree")
    plt.plot(tamaños, eh, marker="o", label="Extendible Hashing")
    plt.xlabel("Tamaño del dataset")
    plt.ylabel("Tiempo mediana (s) - 10,000 busquedas")
    plt.title(f"Tiempo de busqueda W1 - {dataset}")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"../output/graficos/busqueda_w1_{dataset}.png", dpi=150)
    plt.close()
    print(f"Guardado: busqueda_w1_{dataset}.png")

# --- Grafico 2: Tamaño del indice en disco (btree vs eh) ---
for dataset in ["d1_secuencial", "d2_aleatorio"]:
    filas = por_dataset(bench, dataset)
    tamaños = [r["tamaño"] for r in filas]
    btree_kb = [int(r["btree_size_bytes"]) / 1024 for r in filas]
    eh_kb = [int(r["eh_size_bytes"]) / 1024 for r in filas]

    plt.figure(figsize=(7, 5))
    plt.plot(tamaños, btree_kb, marker="o", label="B-tree")
    plt.plot(tamaños, eh_kb, marker="o", label="Extendible Hashing")
    plt.xlabel("Tamaño del dataset")
    plt.ylabel("Tamaño del indice (KB)")
    plt.title(f"Tamaño del indice en disco - {dataset}")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"../output/graficos/tamaño_indice_{dataset}.png", dpi=150)
    plt.close()
    print(f"Guardado: tamaño_indice_{dataset}.png")

# --- Grafico 3: Tiempo de construccion (btree vs eh) ---
for dataset in ["d1_secuencial", "d2_aleatorio"]:
    filas = por_dataset(bench, dataset)
    tamaños = [r["tamaño"] for r in filas]
    btree_t = [float(r["btree_build_time"]) for r in filas]
    eh_t = [float(r["eh_build_time"]) for r in filas]

    plt.figure(figsize=(7, 5))
    plt.plot(tamaños, btree_t, marker="o", label="B-tree")
    plt.plot(tamaños, eh_t, marker="o", label="Extendible Hashing")
    plt.xlabel("Tamaño del dataset")
    plt.ylabel("Tiempo de construccion (s)")
    plt.title(f"Tiempo de construccion del indice - {dataset}")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"../output/graficos/construccion_{dataset}.png", dpi=150)
    plt.close()
    print(f"Guardado: construccion_{dataset}.png")

# --- Grafico 4: Tiempo de insercion (sin indice vs eh) ---
for dataset_base in ["d1_secuencial", "d2_aleatorio"]:
    prefix = "d1" if dataset_base == "d1_secuencial" else "d2"
    filas = sorted(
        [r for r in insert if r["tabla"].startswith(f"bench_{prefix}_")],
        key=lambda r: int(r["tabla"].split("_")[-1])
    )
    tamaños = [int(r["tabla"].split("_")[-1]) for r in filas]
    sin_idx = [r["sin_indice"] for r in filas]
    eh = [r["eh"] for r in filas]

    plt.figure(figsize=(7, 5))
    plt.plot(tamaños, sin_idx, marker="o", label="Sin indice (insercion directa)")
    plt.plot(tamaños, eh, marker="o", label="Extendible Hashing (eh_insert)")
    plt.xlabel("Tamaño base del dataset")
    plt.ylabel("Tiempo de insercion del 10% adicional (s)")
    plt.title(f"Tiempo de insercion (W3) - {dataset_base}")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"../output/graficos/insercion_{dataset_base}.png", dpi=150)
    plt.close()
    print(f"Guardado: insercion_{dataset_base}.png")

print("\nTodos los graficos generados en ../output/graficos/")
