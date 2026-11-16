"""
Genera pedido (1 000 000 filas) y detalle_pedido (1 a 3 lineas por pedido)
y los distribuye en 3 nodos con la estrategia indicada. Usa COPY.
  RANGO: id 1..333333 -> A, 333334..666666 -> B, 666667..1000000 -> C
  HASH : id % 3 == 0 -> A, 1 -> B, 2 -> C
detalle_pedido sigue siempre el nodo de su pedido (JOIN local).
usuario y medicamento se replican completos en los 3 nodos.
Cada ejecucion vacia las tablas de los 3 nodos antes de cargar.
Uso: python fragment_data.py [rango|hash]
"""
import sys, io, random, time
import psycopg2

SEED = 272
N_PEDIDOS = 1_000_000
N_USUARIOS = 5_000
N_MEDICAMENTOS = 100

NODES = {
    "A": {"host": "localhost", "port": 5433},
    "B": {"host": "localhost", "port": 5434},
    "C": {"host": "localhost", "port": 5435},
}
for cfg in NODES.values():
    cfg.update(dbname="farmacia_db", user="farmacia_user", password="farmacia_pass")

def nodo_rango(pid):
    t = N_PEDIDOS // 3
    return "A" if pid <= t else ("B" if pid <= 2 * t else "C")

def nodo_hash(pid):
    return ("A", "B", "C")[pid % 3]

ESTRATEGIAS = {"rango": nodo_rango, "hash": nodo_hash}

def copiar(cur, tabla, columnas, buf):
    buf.seek(0)
    cur.copy_expert(f"COPY {tabla} ({', '.join(columnas)}) FROM STDIN WITH CSV", buf)

def main(estrategia):
    asignar = ESTRATEGIAS[estrategia]
    rng = random.Random(SEED)
    t0 = time.time()

    conns = {n: psycopg2.connect(**cfg) for n, cfg in NODES.items()}
    for c in conns.values():
        c.cursor().execute("TRUNCATE detalle_pedido, pedido, medicamento, usuario CASCADE;")
        c.commit()

    # Tablas replicadas (mismo contenido en los 3 nodos)
    usuarios = [(i, f"Nombre{i}", f"Apellido{i}") for i in range(1, N_USUARIOS + 1)]
    meds = [(i, f"Medicamento{i}", round(rng.uniform(5, 100), 2)) for i in range(1, N_MEDICAMENTOS + 1)]
    precio = {m[0]: m[2] for m in meds}
    for c in conns.values():
        cur = c.cursor()
        b = io.StringIO(); [b.write(f"{u[0]},{u[1]},{u[2]}\n") for u in usuarios]
        copiar(cur, "usuario", ["id", "nombres", "apellidos"], b)
        b = io.StringIO(); [b.write(f"{m[0]},{m[1]},{m[2]}\n") for m in meds]
        copiar(cur, "medicamento", ["id", "nombre", "precio"], b)
        c.commit()

    # Tablas fragmentadas
    bp = {n: io.StringIO() for n in NODES}
    bd = {n: io.StringIO() for n in NODES}
    did = 0
    for pid in range(1, N_PEDIDOS + 1):
        nodo = asignar(pid)
        id_usuario = rng.randint(1, N_USUARIOS)
        total = 0.0
        for _ in range(rng.randint(1, 3)):
            did += 1
            med = rng.randint(1, N_MEDICAMENTOS)
            cant = rng.randint(1, 5)
            sub = round(precio[med] * cant, 2)
            total += sub
            bd[nodo].write(f"{did},{pid},{med},{cant},{sub}\n")
        bp[nodo].write(f"{pid},{id_usuario},2026-01-01,{round(total, 2)}\n")

    for n, c in conns.items():
        cur = c.cursor()
        copiar(cur, "pedido", ["id", "id_usuario", "fecha", "total"], bp[n])
        copiar(cur, "detalle_pedido", ["id", "id_pedido", "id_medicamento", "cantidad", "subtotal"], bd[n])
        c.commit()
        cur.execute("SELECT count(*), min(id), max(id) FROM pedido;")
        p = cur.fetchone()
        cur.execute("SELECT count(*) FROM detalle_pedido;")
        print(f"[{estrategia.upper()}] nodo {n}: pedidos={p[0]} (id {p[1]}..{p[2]}) detalles={cur.fetchone()[0]}")
        c.close()
    print(f"Listo en {time.time() - t0:.1f}s")

if __name__ == "__main__":
    est = sys.argv[1] if len(sys.argv) > 1 else "rango"
    if est not in ESTRATEGIAS:
        print("Uso: python fragment_data.py [rango|hash]"); sys.exit(1)
    main(est)


