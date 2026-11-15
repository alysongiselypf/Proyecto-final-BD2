"""
Busqueda W1 (existentes) y W2 (ausentes): sin indice vs B-tree vs Extendible Hashing.
Los 3 escenarios usan la misma forma de invocacion: una consulta por clave.
Uso: python benchmark_runner.py [tamaños...]   (ej: python benchmark_runner.py 100000)
Ejecutar desde la carpeta datasets/workloads (las rutas ../output son relativas).

Cada corrida conserva los tamaños medidos antes y reemplaza solo los que se
vuelven a ejecutar, asi se puede correr un tamaño por vez sin perder resultados.
"""
import sys, os, csv, json, time, statistics
import psycopg2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "load"))
from load_dataset import cargar_csv

DB_CONFIG = {"host": "localhost", "port": 5432, "dbname": "farmacia_db",
             "user": "farmacia_user", "password": "farmacia_pass"}
TAMAÑOS = [int(a) for a in sys.argv[1:]] or [100000, 500000, 1000000]
DATASETS = [("d1_secuencial", "d1"), ("d2_aleatorio", "d2")]
REPETICIONES = 5
OUT_RESUMEN = "../output/resultados_benchmark.json"
OUT_REPS = "../output/resultados_benchmark_reps.json"


def cargar_workload(path):
    with open(path) as f:
        r = csv.reader(f); next(r)
        return [int(row[0]) for row in r]


def cargar_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def medir_sql(conn, tabla, claves):
    cur = conn.cursor()
    t0 = time.perf_counter()
    for k in claves:
        cur.execute(f"SELECT id FROM {tabla} WHERE id = %s;", (k,))
        cur.fetchall()
    conn.commit()
    return time.perf_counter() - t0


def medir_eh(conn, claves):
    cur = conn.cursor()
    t0 = time.perf_counter()
    for k in claves:
        cur.execute("SELECT eh_search(%s);", (k,))
        cur.fetchall()
    conn.commit()
    return time.perf_counter() - t0


def plan(conn, tabla, clave):
    cur = conn.cursor()
    cur.execute(f"EXPLAIN SELECT id FROM {tabla} WHERE id = %s;", (clave,))
    return " | ".join(r[0] for r in cur.fetchall())


def set_scan(conn, activo):
    v = "on" if activo else "off"
    cur = conn.cursor()
    cur.execute(f"SET enable_indexscan = {v}; SET enable_bitmapscan = {v};")
    conn.commit()


def repetir(f, nombre, filas, base):
    tiempos = []
    for i in range(REPETICIONES):
        t = f(); tiempos.append(t)
        filas.append({**base, "escenario_workload": nombre, "rep": i + 1, "segundos": t})
    return {"tiempos": tiempos, "mediana": statistics.median(tiempos),
            "media": statistics.mean(tiempos)}


def experimento(dataset_base, prefijo, n, filas, pgver):
    tabla = f"bench_{prefijo}_{n}"
    w1 = cargar_workload(f"../output/workload_{dataset_base}_{n}_w1.csv")
    w2 = cargar_workload(f"../output/workload_{dataset_base}_{n}_w2.csv")
    cargar_csv(f"../output/{dataset_base}_{n}.csv", tabla)   # tabla limpia, sin indice
    base = {"dataset": dataset_base, "n": n, "pg": pgver,
            "bucket_capacity": int(os.environ.get("BUCKET_CAPACITY", 4))}
    r = {"dataset": dataset_base, "tamaño": n, "tabla": tabla}
    r["bucket_capacity"] = base["bucket_capacity"]
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(f"ANALYZE {tabla};"); conn.commit()

    # 1) sin indice
    set_scan(conn, False)
    r["plan_sin_indice"] = plan(conn, tabla, w1[0])
    assert "Seq Scan" in r["plan_sin_indice"], r["plan_sin_indice"]
    r["sin_indice_w1"] = repetir(lambda: medir_sql(conn, tabla, w1), "sin_indice_w1", filas, base)
    r["sin_indice_w2"] = repetir(lambda: medir_sql(conn, tabla, w2), "sin_indice_w2", filas, base)
    set_scan(conn, True)

    # 2) B-tree
    t0 = time.perf_counter()
    cur.execute(f"CREATE INDEX idx_{tabla}_btree ON {tabla} (id);"); conn.commit()
    r["btree_build_time"] = time.perf_counter() - t0
    cur.execute(f"ANALYZE {tabla};"); conn.commit()
    cur.execute(f"SELECT pg_relation_size('idx_{tabla}_btree');")
    r["btree_size_bytes"] = cur.fetchone()[0]
    r["plan_btree"] = plan(conn, tabla, w1[0])
    assert "Index" in r["plan_btree"], r["plan_btree"]
    r["btree_w1"] = repetir(lambda: medir_sql(conn, tabla, w1), "btree_w1", filas, base)
    r["btree_w2"] = repetir(lambda: medir_sql(conn, tabla, w2), "btree_w2", filas, base)
    cur.execute(f"DROP INDEX idx_{tabla}_btree;"); conn.commit()

    # 3) Extendible Hashing
    t0 = time.perf_counter()
    cur.execute("SELECT eh_build_table(%s, %s);", (tabla, "id")); conn.commit()
    r["eh_build_time"] = time.perf_counter() - t0
    cur.execute("SELECT eh_index_size();")
    r["eh_size_bytes"] = cur.fetchone()[0]
    r["eh_w1"] = repetir(lambda: medir_eh(conn, w1), "eh_w1", filas, base)
    r["eh_w2"] = repetir(lambda: medir_eh(conn, w2), "eh_w2", filas, base)
    conn.close()
    return r


if __name__ == "__main__":
    os.makedirs("../output", exist_ok=True)
    c = psycopg2.connect(**DB_CONFIG); cur = c.cursor()
    cur.execute("SHOW server_version;"); pgver = cur.fetchone()[0]
    cur.execute("SHOW shared_buffers;"); shared_buffers = cur.fetchone()[0]
    c.close()
    config = {"pg": pgver, "shared_buffers": shared_buffers,
              "bucket_capacity": int(os.environ.get("BUCKET_CAPACITY", 4)),
              "repeticiones": REPETICIONES, "tamaños": TAMAÑOS,
              "inicio": time.strftime("%Y-%m-%d %H:%M:%S")}
    # Conserva lo medido antes; reemplaza solo los tamaños de esta corrida
    prev = cargar_json(OUT_RESUMEN, [])
    resultados = [x for x in prev if x.get("tamaño") not in TAMAÑOS]
    prev_reps = cargar_json(OUT_REPS, {})
    filas = [x for x in prev_reps.get("repeticiones", []) if x.get("n") not in TAMAÑOS]
    configs = prev_reps.get("configs", []) + [config]

    def guardar():
        orden = {d: i for i, (d, _) in enumerate(DATASETS)}
        res = sorted(resultados, key=lambda x: (orden.get(x.get("dataset"), 99), x.get("tamaño", 0)))
        with open(OUT_RESUMEN, "w") as f:
            json.dump(res, f, indent=2, default=str)
        with open(OUT_REPS, "w") as f:
            json.dump({"configs": configs, "repeticiones": filas}, f, indent=2, default=str)

    for dataset_base, prefijo in DATASETS:
        for n in TAMAÑOS:
            print(f"--- {dataset_base}, n={n} ---", flush=True)
            t_exp = time.perf_counter()
            try:
                r = experimento(dataset_base, prefijo, n, filas, pgver)
                r["duracion_s"] = time.perf_counter() - t_exp
                resultados.append(r)
                print(f"  W1 mediana: sin_indice={r['sin_indice_w1']['mediana']:.3f}s | "
                      f"btree={r['btree_w1']['mediana']:.3f}s | "
                      f"eh={r['eh_w1']['mediana']:.3f}s "
                      f"(total {r['duracion_s']:.0f}s)", flush=True)
            except Exception as e:
                print(f"  ERROR en {dataset_base} n={n}: {e}", flush=True)
                resultados.append({"dataset": dataset_base, "tamaño": n, "error": str(e)})
            guardar()   # guarda tras cada experimento: un fallo no pierde lo anterior
    print(f"\nGuardado en {OUT_RESUMEN} y {OUT_REPS}")
