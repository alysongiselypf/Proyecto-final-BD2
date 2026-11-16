"""
Graficos de W3 (inserciones) a partir de ../output/resultados_insercion.json.
Reemplaza la parte de inserciones de generar_graficos.py (formato anterior, con 'tabla').
Ejecutar desde datasets/workloads. Genera en ../output/graficos:
  insercion_d1_secuencial.png, insercion_d2_aleatorio.png, insercion_autosave.png
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ENTRADA = "../output/resultados_insercion.json"
SALIDA = "../output/graficos"
# (clave, etiqueta, color, rayado). Rayado = misma forma de sentencia que EH (WITH ... INSERT ... RETURNING)
ESCENARIOS = [
    ("sin_indice", "Sin índice", "#9e9e9e", ""),
    ("btree", "B-tree", "#4c78a8", ""),
    ("sin_indice_cte", "Sin índice (CTE)", "#9e9e9e", "//"),
    ("btree_cte", "B-tree (CTE)", "#4c78a8", "//"),
    ("eh", "Extendible Hashing", "#e45756", "//"),
]
NOMBRES = {"d1_secuencial": "D1 (secuencial)", "d2_aleatorio": "D2 (aleatorio)"}


def stats(x):
    t = x["tiempos"]
    return x["mediana"], min(t), max(t)


def main():
    with open(ENTRADA, encoding="utf-8") as f:
        datos = [x for x in json.load(f) if "error" not in x]
    os.makedirs(SALIDA, exist_ok=True)

    for ds in sorted({x["dataset"] for x in datos}):
        filas = sorted((x for x in datos if x["dataset"] == ds), key=lambda x: x["tamaño"])
        fig, ejes = plt.subplots(1, len(filas), figsize=(4.2 * len(filas), 4.6), squeeze=False)
        for ax, fila in zip(ejes[0], filas):
            for i, (clave, etiqueta, color, rayado) in enumerate(ESCENARIOS):
                if clave not in fila:
                    continue
                med, lo, hi = stats(fila[clave])
                ax.bar(i, med, color=color, hatch=rayado, edgecolor="white", linewidth=0.5,
                       yerr=[[med - lo], [hi - med]], capsize=3, label=etiqueta)
                ax.text(i, hi, f"{med:.1f}", ha="center", va="bottom", fontsize=8)
            ax.set_xticks([])
            ax.set_ylim(0, None)
            ax.set_title(f"base de {fila['tamaño']:,}".replace(",", " ") +
                         f" claves\n(+{fila['n_insertadas']:,} inserciones)".replace(",", " "), fontsize=10)
            ax.set_ylabel("Tiempo de las inserciones (s)")
            ax.grid(axis="y", alpha=0.3)
        h, l = ejes[0][0].get_legend_handles_labels()
        fig.legend(h, l, loc="lower center", ncol=5, fontsize=8, frameon=False)
        fig.suptitle(f"W3: inserciones, {NOMBRES.get(ds, ds)}. Barra = mediana de 5 repeticiones; "
                     "línea = mínimo–máximo.\nRayado = misma forma de sentencia que EH "
                     "(comparar EH solo con las barras rayadas).", fontsize=9)
        fig.tight_layout(rect=(0, 0.08, 1, 0.92))
        ruta = os.path.join(SALIDA, f"insercion_{ds}.png")
        fig.savefig(ruta, dpi=150); plt.close(fig)
        print("Guardado:", os.path.basename(ruta))

    # costo de la durabilidad por insercion (solo existe para la base de 100 000)
    con_auto = [x for x in datos if "eh_autosave" in x and "eh" in x]
    if con_auto:
        fig, ax = plt.subplots(figsize=(6.5, 4.6))
        ancho = 0.38
        for j, x in enumerate(sorted(con_auto, key=lambda x: x["dataset"])):
            for k, (clave, etiqueta, color) in enumerate((("eh", "EH en memoria (sin guardar)", "#e45756"),
                                                          ("eh_autosave", "EH guardando el índice en cada inserción", "#7a1f1e"))):
                med, lo, hi = stats(x[clave])
                ax.bar(j + (k - 0.5) * ancho, med, ancho, color=color, yerr=[[med - lo], [hi - med]],
                       capsize=3, label=etiqueta if j == 0 else None)
                ax.text(j + (k - 0.5) * ancho, hi, f"{med:.0f}", ha="center", va="bottom", fontsize=8)
        ax.set_xticks(range(len(con_auto)))
        ax.set_xticklabels([NOMBRES.get(x["dataset"], x["dataset"]) for x in sorted(con_auto, key=lambda x: x["dataset"])])
        ax.set_yscale("log")
        ax.set_ylabel("Tiempo de 10 000 inserciones (s, escala log)")
        ax.set_title("Costo de la durabilidad inmediata (base de 100 000 claves)", fontsize=10)
        ax.grid(axis="y", alpha=0.3)
        h, l = ax.get_legend_handles_labels()
        fig.legend(h, l, loc="lower center", ncol=2, fontsize=8, frameon=False)
        fig.tight_layout(rect=(0, 0.07, 1, 1))
        ruta = os.path.join(SALIDA, "insercion_autosave.png")
        fig.savefig(ruta, dpi=150); plt.close(fig)
        print("Guardado:", os.path.basename(ruta))


if __name__ == "__main__":
    main()


    