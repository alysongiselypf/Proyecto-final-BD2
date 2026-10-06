"""
Benchmark comparativo: sin indice vs B-tree vs Extendible Hashing.
Cumple seccion 6.2: 3 escenarios obligatorios, 3 tamaños, >=5
repeticiones por experimento, carga favorable (D2) y neutra (D1).

Requiere: pip install psycopg2-binary
Uso: python benchmark_runner.py
"""
import psycopg2, time, statistics, csv, json

DB_CONFIG = {
    "host": "localhost", "port": 5432,
    "dbname": "farmacia_db", "user": "farmacia_user", "password": "farmacia_pass",
}

TAMAÑOS = [100000, 500000, 1000000]
DATASETS = [
    ("d1_secuencial", "d1"),
    ("d2_aleatorio", "d2"),
]
REPETICIONES = 5
N_QUERIES_TEST = 10000

def conectar():
    return psycopg2.connect(**DB_CONFIG)

def cargar_workload(path):
    with open(path) as f:
        reader = csv.reader(f); next(reader)
        return [int(row[0]) for row in reader]

def medir_busqueda_sql(conn, tabla, claves):
    cur = conn.cursor()
    inicio = time.perf_counter()
    cur.execute(f"SELECT id FROM {tabla} WHERE id = ANY(%s);", (claves,))
    cur.fetchall()
    conn.commit()
    return time.perf_counter() - inicio

def medir_busqueda_eh(conn, claves):
    cur = conn.cursor()
    inicio = time.perf_counter()
    for k in claves:
        cur.execute("SELECT eh_search(%s);", (k,))
    conn.commit()
    return time.perf_counter() - inicio

def crear_btree(conn, tabla):
    cur = conn.cursor()
    cur.execute(f"DROP INDEX IF EXISTS idx_{tabla}_btree;")
    inicio = time.perf_counter()
    cur.execute(f"CREATE INDEX idx_{tabla}_btree ON {tabla} (id);")
    conn.commit()
    duracion = time.perf_counter() - inicio
    cur.execute(f"SELECT pg_relation_size('idx_{tabla}_btree');")
    return duracion, cur.fetchone()[0]

def eliminar_btree(conn, tabla):
    cur = conn.cursor()
    cur.execute(f"DROP INDEX IF EXISTS idx_{tabla}_btree;")
    conn.commit()

def construir_eh(conn, tabla):
    cur = conn.cursor()
    inicio = time.perf_counter()
    cur.execute("SELECT eh_build_table(%s, %s);", (tabla, "id"))
    conn.commit()
    duracion = time.perf_counter() - inicio
    cur.execute("SELECT eh_index_size();")
    return duracion, cur.fetchone()[0]

def repetir(func, n=REPETICIONES):
    tiempos = [func() for _ in range(n)]
    return {"tiempos": tiempos, "mediana": statistics.median(tiempos), "media": statistics.mean(tiempos)}

def correr_experimento(dataset_base, tabla_prefix, n):
    tabla = f"bench_{tabla_prefix}_{n}"
    w1 = cargar_workload(f"../output/workload_{dataset_base}_{n}_w1.csv")
    w2 = cargar_workload(f"../output/workload_{dataset_base}_{n}_w2.csv")
    w1 = w1[:N_QUERIES_TEST]   # <-- nueva línea, recorte para prueba
    w2 = w2[:N_QUERIES_TEST]   # <-- nueva línea, recorte para prueba
    resultado = {"dataset": dataset_base, "tamaño": n, "tabla": tabla}
    conn = conectar()

    eliminar_btree(conn, tabla)
    resultado["sin_indice_w1"] = repetir(lambda: medir_busqueda_sql(conn, tabla, w1))
    resultado["sin_indice_w2"] = repetir(lambda: medir_busqueda_sql(conn, tabla, w2))

    t_build, tam = crear_btree(conn, tabla)
    resultado["btree_build_time"] = t_build
    resultado["btree_size_bytes"] = tam
    resultado["btree_w1"] = repetir(lambda: medir_busqueda_sql(conn, tabla, w1))
    resultado["btree_w2"] = repetir(lambda: medir_busqueda_sql(conn, tabla, w2))
    eliminar_btree(conn, tabla)

    t_build_eh, tam_eh = construir_eh(conn, tabla)
    resultado["eh_build_time"] = t_build_eh
    resultado["eh_size_bytes"] = tam_eh
    resultado["eh_w1"] = repetir(lambda: medir_busqueda_eh(conn, w1))
    resultado["eh_w2"] = repetir(lambda: medir_busqueda_eh(conn, w2))

    conn.close()
    return resultado

if __name__ == "__main__":
    resultados = []
    for dataset_base, tabla_prefix in DATASETS:
        for n in TAMAÑOS:
            print(f"--- Ejecutando: {dataset_base}, n={n} ---")
            r = correr_experimento(dataset_base, tabla_prefix, n)
            resultados.append(r)
            print(f"  sin_indice W1 mediana={r['sin_indice_w1']['mediana']:.3f}s | "
                  f"btree W1 mediana={r['btree_w1']['mediana']:.3f}s | "
                  f"eh W1 mediana={r['eh_w1']['mediana']:.3f}s")

    with open("../output/resultados_benchmark.json", "w") as f:
        json.dump(resultados, f, indent=2, default=str)
    print("\nGuardado en ../output/resultados_benchmark.json")
