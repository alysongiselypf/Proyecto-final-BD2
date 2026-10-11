"""
Extrae y muestra las metricas completas del benchmark: tiempo de
construccion y tamaño en disco de B-tree vs Extendible Hashing,
ademas de los tiempos de busqueda ya vistos en consola.
"""
import json

with open("../output/resultados_benchmark.json") as f:
    resultados = json.load(f)

print(f"{'Dataset':<15} {'n':>9} {'btree_build':>12} {'btree_size':>12} {'eh_build':>12} {'eh_size':>12}")
print("-" * 80)

for r in resultados:
    dataset = r["dataset"]
    n = r["tamaño"]
    btree_build = float(r["btree_build_time"])
    btree_size = int(r["btree_size_bytes"])
    eh_build = float(r["eh_build_time"])
    eh_size = int(r["eh_size_bytes"])

    print(f"{dataset:<15} {n:>9} {btree_build:>10.3f}s {btree_size/1024:>10.1f}KB "
          f"{eh_build:>10.3f}s {eh_size/1024:>10.1f}KB")

print("\n--- Detalle W1/W2 (busqueda exitosa / no exitosa) ---\n")
for r in resultados:
    print(f"{r['dataset']} n={r['tamaño']}")
    print(f"  sin_indice: W1={r['sin_indice_w1']['mediana']:.3f}s  W2={r['sin_indice_w2']['mediana']:.3f}s")
    print(f"  btree:      W1={r['btree_w1']['mediana']:.3f}s  W2={r['btree_w2']['mediana']:.3f}s")
    print(f"  eh:         W1={r['eh_w1']['mediana']:.3f}s  W2={r['eh_w2']['mediana']:.3f}s")
    print()
