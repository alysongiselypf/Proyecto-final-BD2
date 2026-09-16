"""
W3: mide comportamiento de insercion (10% adicional) en los 3 escenarios,
y consolida las metricas minimas exigidas (seccion 6.2): tiempo de
construccion, tiempo de busqueda, comportamiento de insercion, tamaño.
"""
import psycopg2, time, csv, json

DB_CONFIG = {
    "host": "localhost", "port": 5432,
    "dbname": "farmacia_db", "user": "farmacia_user", "password": "farmacia_pass",
}

def cargar_workload(path):
    with open(path) as f:
        reader = csv.reader(f); next(reader)
        return [int(row[0]) for row in reader]

def medir_insercion_sql(conn, tabla, claves):
    cur = conn.cursor()
    inicio = time.perf_counter()
    for k in claves:
        cur.execute(f"INSERT INTO {tabla} (id) VALUES (%s);", (k,))
    conn.commit()
    return time.perf_counter() - inicio

def medir_insercion_eh(conn, claves):
    cur = conn.cursor()
    inicio = time.perf_counter()
    for k in claves:
        cur.execute("SELECT eh_insert(%s);", (k,))
    conn.commit()
    return time.perf_counter() - inicio

def correr(dataset_base, tabla_prefix, n):
    tabla = f"bench_{tabla_prefix}_{n}"
    w3 = cargar_workload(f"../output/workload_{dataset_base}_{n}_w3.csv")
    conn = psycopg2.connect(**DB_CONFIG)

    t_sin_indice = medir_insercion_sql(conn, tabla, w3)
    print(f"[{tabla}] insercion sin indice: {t_sin_indice:.3f}s para {len(w3)} filas")

    cur = conn.cursor()
    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{tabla}_btree ON {tabla} (id);")
    conn.commit()

    cur.execute("SELECT eh_build_table(%s, %s);", (tabla, "id"))
    conn.commit()
    t_eh = medir_insercion_eh(conn, w3)
    print(f"[{tabla}] insercion Extendible Hashing: {t_eh:.3f}s para {len(w3)} filas")

    conn.close()
    return {"tabla": tabla, "sin_indice": t_sin_indice, "eh": t_eh, "n_insertadas": len(w3)}

if __name__ == "__main__":
    resultados = []
    for dataset_base, tabla_prefix in [("d1_secuencial", "d1"), ("d2_aleatorio", "d2")]:
        for n in [100000, 500000, 1000000]:
            resultados.append(correr(dataset_base, tabla_prefix, n))

    with open("../output/resultados_insercion.json", "w") as f:
        json.dump(resultados, f, indent=2)
    print("\nGuardado en ../output/resultados_insercion.json")
