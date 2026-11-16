"""
W3: inserciones (10 % del tamaño inicial). Antes de cada medicion se recarga la tabla
limpia y se fuerza un CHECKPOINT (para que el trabajo de disco pendiente de la carga no
caiga dentro del tiempo medido). El orden de los escenarios ROTA en cada repeticion
(cuadrado latino): con 5 escenarios y 5 repeticiones, cada escenario pasa exactamente una
vez por cada posicion, asi una deriva del sistema en el tiempo afecta a todos por igual.

Los 3 escenarios hacen UNA ida y vuelta al servidor por clave insertada:
en EH, el INSERT en la tabla y la llamada a eh_insert van en la misma
sentencia (WITH ... INSERT ... RETURNING), asi no pagan el doble de red.

Escenario "eh": eh_insert SIN autoguardado a disco (eh.autosave = off), es decir,
solo el costo de mantener el indice en memoria. El guardado se hace al final de
cada repeticion, fuera del tiempo medido.
Escenario "eh_autosave": eh_insert guardando el archivo completo en CADA insercion
(durabilidad inmediata). Reescribe todo el indice por clave, por eso solo se mide
hasta AUTOSAVE_MAX_N claves base. NO entra en la rotacion (su carga de disco contaminaria
al escenario siguiente): se mide aparte con SOLO="eh_autosave".

Escenarios "sin_indice_cte" y "btree_cte": CONTROLES. Misma forma de sentencia que EH
(WITH ... INSERT ... RETURNING ... SELECT) pero sin llamar a eh_insert, para separar el costo
de la forma de la sentencia del costo del indice. La comparacion justa con EH es contra estos.

Uso: python measure_insertion.py [tamaños...]   (ej: python measure_insertion.py 100000)
Variable opcional SOLO="eh_autosave" (o una lista separada por comas): mide solo esos
escenarios y los agrega a lo ya guardado para ese tamaño (sin borrar el resto).
Ejecutar desde datasets/workloads. Acumula resultados entre corridas.
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
ESCENARIOS = ("sin_indice", "btree", "eh")          # nucleo: una entrada previa debe tenerlos
CONTROL = ("sin_indice_cte", "btree_cte")
SOLO = tuple(e.strip() for e in os.environ.get("SOLO", "").split(",") if e.strip())
AUTOSAVE_MAX_N = 100000     # eh_autosave solo hasta este tamaño base
BUCKET_CAPACITY = int(os.environ.get("BUCKET_CAPACITY", 4))
OUT_RESUMEN = "../output/resultados_insercion.json"
OUT_REPS = "../output/resultados_insercion_reps.json"


def escenarios_de(n):
    """Escenarios que se miden para un tamaño base n (en la rotacion, sin eh_autosave)."""
    if SOLO:
        return tuple(e for e in ESCENARIOS + CONTROL + ("eh_autosave",)
                     if e in SOLO and (e != "eh_autosave" or n <= AUTOSAVE_MAX_N))
    return ESCENARIOS + CONTROL


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


def insertar(conn, tabla, claves, modo):
    """modo: 'plano' (INSERT simple), 'cte' (control, misma forma que EH) o 'eh'.
    Devuelve (segundos, cantidad de claves que eh_insert no acepto)."""
    cur = conn.cursor()
    rechazadas = 0
    if modo == "eh":
        sql = (f"WITH i AS (INSERT INTO {tabla} (id) VALUES (%s) RETURNING id) "
               "SELECT eh_insert(id) FROM i;")
    elif modo == "cte":
        sql = (f"WITH i AS (INSERT INTO {tabla} (id) VALUES (%s) RETURNING id) "
               "SELECT id FROM i;")
    else:
        sql = f"INSERT INTO {tabla} (id) VALUES (%s);"
    t0 = time.perf_counter()
    for k in claves:
        cur.execute(sql, (k,))
        if modo == "eh":
            if cur.fetchone()[0] is not True:
                rechazadas += 1
        elif modo == "cte":
            cur.fetchall()
    conn.commit()
    return time.perf_counter() - t0, rechazadas


def exigir_guc(cur):
    """eh.autosave debe estar definido por la extension; si no, SET lo aceptaria
    en silencio como un parametro cualquiera y el autoguardado seguiria activo."""
    cur.execute("SELECT eh_index_size();"); cur.fetchone()      # fuerza a cargar la libreria
    cur.execute("SELECT vartype FROM pg_settings WHERE name = 'eh.autosave';")
    fila = cur.fetchone()
    if not fila or fila[0] != "bool":
        raise RuntimeError("eh.autosave no esta definido en la extension: aplica el "
                           "parche de eh_insert.c / eh_build.c y reconstruye la imagen")


def una_corrida(csv_ds, tabla, w3, escenario):
    cargar_csv(csv_ds, tabla)          # tabla limpia, sin indice
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    con_eh = escenario in ("eh", "eh_autosave")
    if escenario in ("btree", "btree_cte"):
        cur.execute(f"CREATE INDEX idx_{tabla}_btree ON {tabla} (id);"); conn.commit()
    elif con_eh:
        exigir_guc(cur)
        cur.execute("SELECT eh_build_table(%s, %s);", (tabla, "id")); conn.commit()
        autosave = "on" if escenario == "eh_autosave" else "off"
        cur.execute("SELECT set_config('eh.autosave', %s, false);", (autosave,)); cur.fetchone()
    cur.execute("CHECKPOINT;"); conn.commit()      # estado de disco comparable; fuera del tiempo medido
    modo = "eh" if con_eh else ("cte" if escenario.endswith("_cte") else "plano")
    t, rechazadas = insertar(conn, tabla, w3, modo)
    if escenario == "eh":
        cur.execute("SELECT eh_save();"); cur.fetchone(); conn.commit()   # fuera del tiempo medido
    cur.execute(f"SELECT count(*) FROM {tabla};")
    total = cur.fetchone()[0]
    conn.close()
    return t, total, rechazadas


def completo(x):
    """Una entrada previa solo se conserva si es comparable con esta corrida."""
    return (all(e in x for e in ESCENARIOS)
            and x.get("bucket_capacity") == BUCKET_CAPACITY)


if __name__ == "__main__":
    os.makedirs("../output", exist_ok=True)
    c = psycopg2.connect(**DB_CONFIG); cur = c.cursor()
    cur.execute("SHOW server_version;"); pgver = cur.fetchone()[0]
    cur.execute("SHOW shared_buffers;"); shared_buffers = cur.fetchone()[0]
    c.close()
    config = {"pg": pgver, "shared_buffers": shared_buffers,
              "bucket_capacity": BUCKET_CAPACITY, "repeticiones": REPETICIONES,
              "tamaños": TAMAÑOS, "orden": "rotativo (cuadrado latino)",
              "checkpoint_antes_de_medir": True,
              "inicio": time.strftime("%Y-%m-%d %H:%M:%S")}

    # Conserva lo medido antes (si es comparable); reemplaza los tamaños de esta corrida
    previo = cargar_json(OUT_RESUMEN, [])
    resultados = [x for x in previo if x.get("tamaño") not in TAMAÑOS and completo(x)]
    # de un (dataset, tamaño) ya medido se conservan los escenarios que NO se vuelven a medir
    previos_n = {(x["dataset"], x["tamaño"]): x for x in previo
                 if "error" not in x and completo(x)}
    prev_reps = cargar_json(OUT_REPS, {})
    filas = [x for x in prev_reps.get("repeticiones", [])
             if x.get("bucket_capacity") == BUCKET_CAPACITY
             and not (x.get("n") in TAMAÑOS and x.get("escenario") in escenarios_de(x["n"]))]
    configs = prev_reps.get("configs", []) + [config]

    def guardar():
        orden = {d: i for i, (d, _) in enumerate(DATASETS)}
        res = sorted(resultados, key=lambda x: (orden.get(x.get("dataset"), 99), x.get("tamaño", 0)))
        with open(OUT_RESUMEN, "w") as f:
            json.dump(res, f, indent=2, default=str)
        with open(OUT_REPS, "w") as f:
            json.dump({"configs": configs, "repeticiones": filas}, f, indent=2, default=str)

    for ds, pref in DATASETS:
        for n in TAMAÑOS:
            print(f"--- {ds}, n={n} ---", flush=True)
            t_exp = time.perf_counter()
            try:
                tabla = f"bench_{pref}_{n}"
                w3 = cargar_workload(f"../output/workload_{ds}_{n}_w3.csv")
                r = dict(previos_n.get((ds, n), {}))
                r.update({"dataset": ds, "tamaño": n, "n_insertadas": len(w3),
                          "bucket_capacity": BUCKET_CAPACITY})
                escenarios = escenarios_de(n)
                if not escenarios:
                    raise ValueError(f"SOLO={SOLO} no corresponde a ningun escenario para n={n}")
                tiempos = {e: [] for e in escenarios}
                rechazadas = {e: 0 for e in escenarios}
                for i in range(REPETICIONES):
                    k = i % len(escenarios)
                    orden = escenarios[k:] + escenarios[:k]      # rotacion por repeticion
                    for pos, esc in enumerate(orden, 1):
                        t, total, rech = una_corrida(f"../output/{ds}_{n}.csv", tabla, w3, esc)
                        assert total == n + len(w3), f"count={total}"
                        tiempos[esc].append(t); rechazadas[esc] += rech
                        filas.append({"dataset": ds, "n": n, "escenario": esc, "rep": i + 1,
                                      "pos": pos, "segundos": t, "pg": pgver,
                                      "bucket_capacity": BUCKET_CAPACITY})
                for esc in escenarios:
                    r[esc] = {"tiempos": tiempos[esc], "mediana": statistics.median(tiempos[esc]),
                              "media": statistics.mean(tiempos[esc])}
                    if esc.startswith("eh"):
                        r[f"{esc}_rechazadas"] = rechazadas[esc]
                        if rechazadas[esc]:
                            print(f"  AVISO: {esc} rechazo {rechazadas[esc]} claves", flush=True)
                    print(f"  [{ds} {n}] {esc}: mediana {r[esc]['mediana']:.2f}s", flush=True)
                r["duracion_s"] = time.perf_counter() - t_exp
                resultados.append(r)
            except Exception as e:
                print(f"  ERROR en {ds} n={n}: {e}", flush=True)
                resultados.append({"dataset": ds, "tamaño": n, "error": str(e)})
            guardar()   # guarda tras cada experimento: un fallo no pierde lo anterior

    print(f"\nGuardado en {OUT_RESUMEN} y {OUT_REPS}")





