"""
Pruebas de la parte distribuida (rubrica 6.3). Un ciclo por estrategia:

  python fragment_data.py rango          # vacia y recarga los 3 nodos con esa estrategia
  python run_distributed_tests.py rango
  python fragment_data.py hash
  python run_distributed_tests.py hash
  python run_distributed_tests.py comparar

El script comprueba que los datos cargados correspondan a la estrategia pedida
(si no, se detiene). Cada prueba se repite REPS veces (5) y se reporta la mediana.

Modelo de red: antes de cada consulta a un nodo distinto del origen del cliente se
espera la latencia configurada (A-B 20 ms, A-C 40 ms, B-C 25 ms), una vez por consulta.
Las consultas a varios nodos se lanzan en paralelo, asi que cuestan la mayor de sus
latencias. El origen del cliente (A, B o C) se sortea en cada operacion.

Variables de entorno (para pruebas rapidas): REPS, N_OPS, N_RANGOS, N_JOINS,
LATENCIA_ESCALA (por ejemplo 0.05 acorta todas las esperas simuladas).
"""
import sys, os, json, time, random, statistics, subprocess, collections
from concurrent.futures import ThreadPoolExecutor
import psycopg2
from query_router import NODES, LATENCIAS_MS

SEED = 272
N_PEDIDOS = 1_000_000
N_USUARIOS = 5_000
N_MEDICAMENTOS = 100
REPS = int(os.environ.get("REPS", 5))
N_OPS = int(os.environ.get("N_OPS", 1000))
N_RANGOS = int(os.environ.get("N_RANGOS", 200))
N_JOINS = int(os.environ.get("N_JOINS", 100))
ESCALA = float(os.environ.get("LATENCIA_ESCALA", 1.0))
ANCHO_RANGO_AGG = 10_000      # 1 % de los ids
ANCHO_RANGO_FILAS = 1_000
FRACCION_HOT, P_HOT = 0.10, 0.80   # 80 % de los accesos al 10 % de ids mas recientes
P_LECTURA, P_REPLICADA = 0.70, 0.20
CONTENEDOR_CAIDO, NODO_CAIDO = "farmacia_nodeB", "B"
TERCIO = N_PEDIDOS // 3
INTERVALOS = {"A": (1, TERCIO), "B": (TERCIO + 1, 2 * TERCIO), "C": (2 * TERCIO + 1, N_PEDIDOS)}
AQUI = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- estrategias
def nodo_rango(pid):
    return "A" if pid <= TERCIO else ("B" if pid <= 2 * TERCIO else "C")


def nodo_hash(pid):
    return "ABC"[pid % 3]


ASIGNAR = {"rango": nodo_rango, "hash": nodo_hash}


def nodos_de_rango(est, a, b):
    """Nodos que guardan algun id del intervalo [a, b]."""
    if est == "rango":
        return [n for n, (lo, hi) in INTERVALOS.items() if a <= hi and b >= lo]
    return sorted({nodo_hash(i) for i in range(a, min(b, a + 2) + 1)})


# ---------------------------------------------------------------- red y consultas
def latencia(origen, destino):
    return 0.0 if origen == destino else LATENCIAS_MS[(origen, destino)] / 1000.0 * ESCALA


def conectar(nodo):
    c = psycopg2.connect(connect_timeout=3, **NODES[nodo])
    c.autocommit = True
    return c


def consultar(origen, destino, sql, params=None):
    """Espera la latencia y ejecuta en destino. Devuelve las filas (None si no hay resultado)."""
    time.sleep(latencia(origen, destino))
    conn = conectar(destino)
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall() if cur.description else None
    finally:
        conn.close()


def consultar_varios(origen, destinos, sql, params=None):
    """Lanza la consulta en paralelo. Devuelve ({nodo: filas}, [nodos que fallaron])."""
    def uno(n):
        try:
            return n, consultar(origen, n, sql, params), None
        except Exception as e:           # nodo caido, timeout, etc.
            return n, None, e
    res, fallidos = {}, []
    with ThreadPoolExecutor(max_workers=len(destinos)) as ex:
        for n, r, e in ex.map(uno, destinos):
            if e is None:
                res[n] = r
            else:
                fallidos.append(n)
    return res, fallidos


def docker(accion, contenedor):
    r = subprocess.run(["docker", accion, contenedor], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"docker {accion} {contenedor}: {r.stderr.strip()}")


def esperar_nodo(nodo, limite_s=120):
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < limite_s:
        try:
            c = conectar(nodo); c.cursor().execute("SELECT 1"); c.close()
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError(f"el nodo {nodo} no volvio a responder en {limite_s} s")


def verificar_layout(est):
    """Aborta si los datos cargados no corresponden a la estrategia pedida."""
    total = 0
    for k, n in enumerate("ABC"):
        c = conectar(n)
        cur = c.cursor()
        cur.execute("SELECT count(*), min(id), max(id), "
                    "count(*) FILTER (WHERE id %% 3 <> %s) FROM pedido;", (k,))
        cnt, mn, mx, fuera = cur.fetchone()
        c.close()
        total += cnt
        if est == "rango":
            lo, hi = INTERVALOS[n]
            ok = cnt > 0 and mn >= lo and mx <= hi
        else:
            ok = cnt > 0 and fuera == 0
        print(f"  nodo {n}: pedidos={cnt} (id {mn}..{mx})")
        if not ok:
            sys.exit(f"ERROR: el nodo {n} no tiene el layout '{est}'. Ejecuta antes "
                     f"'python fragment_data.py {est}'.")
    if total != N_PEDIDOS:
        sys.exit(f"ERROR: hay {total} pedidos en total, se esperaban {N_PEDIDOS}.")


# ---------------------------------------------------------------- carga de trabajo
def generar_ops(rng, n, concentrada=False):
    """Operaciones independientes de la estrategia: (origen, lectura, replicada, id)."""
    ops = []
    for _ in range(n):
        origen = rng.choice("ABC")
        lectura = rng.random() < P_LECTURA
        replicada = rng.random() < P_REPLICADA
        if replicada:
            oid = rng.randint(1, N_MEDICAMENTOS)
        elif concentrada and rng.random() < P_HOT:
            oid = rng.randint(int(N_PEDIDOS * (1 - FRACCION_HOT)) + 1, N_PEDIDOS)
        else:
            oid = rng.randint(1, N_PEDIDOS)
        ops.append((origen, lectura, replicada, oid))
    return ops


def ejecutar_op(est, op):
    origen, lectura, replicada, oid = op
    ok, parcial = True, False
    if replicada and lectura:
        destinos = [origen]            # lectura en la replica local
    elif replicada:
        destinos = list("ABC")         # escritura en las tres replicas
    else:
        destinos = [ASIGNAR[est](oid)]
    t0 = time.perf_counter()
    try:
        if replicada and lectura:
            ok = False
            vecinos = sorted((n for n in "ABC" if n != origen), key=lambda n: LATENCIAS_MS[(origen, n)])
            for n in [origen] + vecinos:        # si la replica local cae, el vecino mas cercano
                try:
                    consultar(origen, n, "SELECT id, precio FROM medicamento WHERE id = %s;", (oid,))
                    ok = True
                    break
                except psycopg2.OperationalError:
                    continue
        elif replicada:
            res, fallidos = consultar_varios(origen, destinos,
                                             "UPDATE medicamento SET precio = precio WHERE id = %s;", (oid,))
            ok = bool(res)
            parcial = bool(res) and bool(fallidos)
        elif lectura:
            consultar(origen, destinos[0], "SELECT id, total FROM pedido WHERE id = %s;", (oid,))
        else:
            consultar(origen, destinos[0], "UPDATE pedido SET total = total WHERE id = %s;", (oid,))
    except psycopg2.Error:
        ok = False
    return {"seg": time.perf_counter() - t0, "ok": ok, "parcial": parcial,
            "destinos": destinos, "local": all(d == origen for d in destinos),
            "lectura": lectura, "replicada": replicada}


def media(v):
    return statistics.mean(v) if v else 0.0


def ms(x):
    return round(x * 1000, 3)


def resumir_ops(res, duracion):
    oks = [r for r in res if r["ok"]]
    seg = sorted(r["seg"] for r in oks)
    carga = collections.Counter(d for r in res for d in r["destinos"])
    total = sum(carga.values()) or 1
    out = {"ops": len(res), "ok": len(oks) / len(res),
           "parciales": sum(1 for r in res if r["parcial"]),
           "media_ms": ms(media(seg)), "p95_ms": ms(seg[int(0.95 * (len(seg) - 1))]) if seg else 0.0,
           "frac_local": sum(1 for r in oks if r["local"]) / len(oks) if oks else 0.0,
           "media_local_ms": ms(media([r["seg"] for r in oks if r["local"]])),
           "media_remota_ms": ms(media([r["seg"] for r in oks if not r["local"]])),
           "ops_por_s": round(len(res) / duracion, 2),
           "max_share": round(max(carga.values()) / total, 4) if carga else 0.0}
    for n in "ABC":
        out[f"carga_{n}"] = round(carga.get(n, 0) / total, 4)
    return out


def prueba_mezcla(est, rep, concentrada):
    ops = generar_ops(random.Random(SEED + rep + (1000 if concentrada else 0)), N_OPS, concentrada)
    t0 = time.perf_counter()
    res = [ejecutar_op(est, op) for op in ops]
    return resumir_ops(res, time.perf_counter() - t0)


def prueba_rangos(est, rep, ancho, traer_filas, n, extra_seed=0):
    rng = random.Random(SEED + rep + 2000 + ancho + extra_seed)
    seg, nodos, filas, oks, incorrectas = [], [], [], 0, 0
    for _ in range(n):
        origen = rng.choice("ABC")
        a = rng.randint(1, N_PEDIDOS - ancho + 1)
        b = a + ancho - 1
        destinos = nodos_de_rango(est, a, b)
        sql = ("SELECT id, total FROM pedido WHERE id BETWEEN %s AND %s;" if traer_filas else
               "SELECT count(*), COALESCE(sum(total), 0) FROM pedido WHERE id BETWEEN %s AND %s;")
        t0 = time.perf_counter()
        res, fallidos = consultar_varios(origen, destinos, sql, (a, b))
        t = time.perf_counter() - t0
        if fallidos:
            continue
        oks += 1
        seg.append(t); nodos.append(len(destinos)); filas.append(sum(len(v) for v in res.values()))
        recibidos = len(res) and (sum(len(v) for v in res.values()) if traer_filas
                                  else sum(v[0][0] for v in res.values()))
        if recibidos != ancho:           # control de integridad: el rango debe estar completo
            incorrectas += 1
    return {"consultas": n, "ok": oks / n, "incorrectas": incorrectas,
            "media_ms": ms(media(seg)),
            "p95_ms": ms(sorted(seg)[int(0.95 * (len(seg) - 1))]) if seg else 0.0,
            "nodos_media": round(media(nodos), 3), "filas_recibidas_media": round(media(filas), 1)}


def prueba_join(est, rep):
    """Consulta que necesita los 3 nodos: el JOIN pedido-detalle es local en cada nodo
    porque detalle_pedido sigue al pedido; el cliente suma los resultados."""
    rng = random.Random(SEED + rep + 4000)
    seg, oks = [], 0
    for _ in range(N_JOINS):
        origen = rng.choice("ABC")
        uid = rng.randint(1, N_USUARIOS)
        t0 = time.perf_counter()
        res, fallidos = consultar_varios(
            origen, list("ABC"),
            "SELECT count(*), COALESCE(sum(d.subtotal), 0) FROM pedido p "
            "JOIN detalle_pedido d ON d.id_pedido = p.id WHERE p.id_usuario = %s;", (uid,))
        if not fallidos:
            oks += 1
            seg.append(time.perf_counter() - t0)
    return {"consultas": N_JOINS, "ok": oks / N_JOINS, "media_ms": ms(media(seg))}


def prueba_caida(est, rep):
    """Detiene un nodo con docker y mide que fraccion de la carga sigue funcionando."""
    docker("stop", CONTENEDOR_CAIDO)
    rec = None
    try:
        time.sleep(2)
        ops = generar_ops(random.Random(SEED + rep + 3000), N_OPS)
        t0 = time.perf_counter()
        res = [ejecutar_op(est, op) for op in ops]
        out = resumir_ops(res, time.perf_counter() - t0)
        clases = collections.defaultdict(list)
        for r in res:
            k = ("replicada" if r["replicada"] else "pedido") + "_" + ("lectura" if r["lectura"] else "escritura")
            clases[k].append(r["ok"])
        for k, v in sorted(clases.items()):
            out[f"ok_{k}"] = round(sum(v) / len(v), 4)
        out["rango_agregado"] = prueba_rangos(est, rep, ANCHO_RANGO_AGG, False, max(N_RANGOS // 2, 1), 500)
    finally:
        t0 = time.perf_counter()
        docker("start", CONTENEDOR_CAIDO)
        esperar_nodo(NODO_CAIDO)
        rec = time.perf_counter() - t0
    out["recuperacion_s"] = round(rec, 2)
    return out


# ---------------------------------------------------------------- resumen
def mediana_hojas(items):
    """Mediana entre repeticiones de cada valor numerico (recursivo)."""
    out = {}
    for k, v in items[0].items():
        vals = [it[k] for it in items if k in it]
        if isinstance(v, dict):
            out[k] = mediana_hojas(vals)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out[k] = round(statistics.median(vals), 4)
    return out


def main(est):
    print(f"Verificando que los nodos tengan el layout '{est}'...")
    verificar_layout(est)
    c = conectar("A"); cur = c.cursor(); cur.execute("SHOW server_version;")
    pg = cur.fetchone()[0]; c.close()
    config = {"estrategia": est, "pg": pg, "reps": REPS, "n_ops": N_OPS, "n_rangos": N_RANGOS,
              "n_joins": N_JOINS, "seed": SEED, "latencias_ms": {f"{a}-{b}": v for (a, b), v in LATENCIAS_MS.items() if a < b},
              "latencia_escala": ESCALA, "p_lectura": P_LECTURA, "p_replicada": P_REPLICADA,
              "hotspot": {"fraccion_ids": FRACCION_HOT, "p_acceso": P_HOT},
              "ancho_rango_agg": ANCHO_RANGO_AGG, "ancho_rango_filas": ANCHO_RANGO_FILAS,
              "inicio": time.strftime("%Y-%m-%d %H:%M:%S")}
    ruta = os.path.join(AQUI, f"resultados_dist_{est}.json")
    reps = []
    for rep in range(1, REPS + 1):
        print(f"--- repeticion {rep}/{REPS} ({est}) ---", flush=True)
        r = {"rep": rep}
        r["mezcla_uniforme"] = prueba_mezcla(est, rep, False)
        r["mezcla_concentrada"] = prueba_mezcla(est, rep, True)
        r["rango_agregado"] = prueba_rangos(est, rep, ANCHO_RANGO_AGG, False, N_RANGOS)
        r["rango_filas"] = prueba_rangos(est, rep, ANCHO_RANGO_FILAS, True, N_RANGOS)
        r["join_multinodo"] = prueba_join(est, rep)
        r["nodo_caido"] = prueba_caida(est, rep)
        reps.append(r)
        print(f"  mezcla 70/30: {r['mezcla_uniforme']['media_ms']} ms/op | concentrada: "
              f"{r['mezcla_concentrada']['media_ms']} ms/op (max nodo {r['mezcla_concentrada']['max_share']:.0%}) | "
              f"rango: {r['rango_agregado']['media_ms']} ms ({r['rango_agregado']['nodos_media']} nodos) | "
              f"caida: ok={r['nodo_caido']['ok']:.0%}", flush=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump({"config": config, "repeticiones": reps,
                       "resumen_mediana": mediana_hojas(reps)}, f, indent=2, ensure_ascii=False)
    print(f"\nGuardado en {ruta}")


def comparar():
    datos = {}
    for est in ("rango", "hash"):
        p = os.path.join(AQUI, f"resultados_dist_{est}.json")
        if not os.path.exists(p):
            sys.exit(f"Falta {p}: ejecuta el ciclo de '{est}' primero.")
        with open(p, encoding="utf-8") as f:
            datos[est] = json.load(f)["resumen_mediana"]

    def g(est, ruta):
        v = datos[est]
        for k in ruta.split("."):
            v = v.get(k) if isinstance(v, dict) else None
        return v

    filas = [
        ("Mezcla 70/30 uniforme: ms por operacion", "mezcla_uniforme.media_ms"),
        ("  operaciones locales (ms)", "mezcla_uniforme.media_local_ms"),
        ("  operaciones remotas (ms)", "mezcla_uniforme.media_remota_ms"),
        ("  fraccion local", "mezcla_uniforme.frac_local"),
        ("Mezcla concentrada (80 % en ids recientes): ms por operacion", "mezcla_concentrada.media_ms"),
        ("  parte de la carga en el nodo mas cargado", "mezcla_concentrada.max_share"),
        ("Rango de 10 000 ids (agregado): ms", "rango_agregado.media_ms"),
        ("  nodos consultados", "rango_agregado.nodos_media"),
        ("Rango de 1 000 ids (trae filas): ms", "rango_filas.media_ms"),
        ("  filas recibidas", "rango_filas.filas_recibidas_media"),
        ("JOIN multinodo (3 nodos): ms", "join_multinodo.media_ms"),
        ("Nodo B caido: operaciones exitosas", "nodo_caido.ok"),
        ("  lecturas de pedido", "nodo_caido.ok_pedido_lectura"),
        ("  escrituras de pedido", "nodo_caido.ok_pedido_escritura"),
        ("  lecturas de tabla replicada", "nodo_caido.ok_replicada_lectura"),
        ("  escrituras de tabla replicada (con algun nodo)", "nodo_caido.ok_replicada_escritura"),
        ("  escrituras replicadas solo parciales", "nodo_caido.parciales"),
        ("  consultas de rango exitosas", "nodo_caido.rango_agregado.ok"),
        ("  recuperacion del nodo (s)", "nodo_caido.recuperacion_s"),
    ]
    print(f"{'Medida (mediana de las repeticiones)':<66}{'RANGO':>10}{'HASH':>10}")
    for etiqueta, ruta in filas:
        a, b = g("rango", ruta), g("hash", ruta)
        print(f"{etiqueta:<66}{'-' if a is None else a:>10}{'-' if b is None else b:>10}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg in ASIGNAR:
        main(arg)
    elif arg == "comparar":
        comparar()
    else:
        sys.exit("Uso: python run_distributed_tests.py [rango|hash|comparar]")

