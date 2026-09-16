"""
Genera 1,000,000+ registros de 'pedido' (relacion principal) y los
distribuye en 3 nodos usando dos estrategias distintas, para comparar
segun la seccion 6.3 de la rubrica.

Estrategia 1 (RANGO/horizontal): pedido.id 1..333333 -> nodeA
                                   333334..666666 -> nodeB
                                   666667..1000000 -> nodeC

Estrategia 2 (HASH): pedido.id % 3 == 0 -> nodeA
                       pedido.id % 3 == 1 -> nodeB
                       pedido.id % 3 == 2 -> nodeC

Replicacion: 'medicamento' (tabla pequeña, muy consultada) se replica
COMPLETA en los 3 nodos, para que las consultas de detalle_pedido
JOIN medicamento puedan resolverse localmente sin cruzar nodos.
'usuario' tambien se replica completa (pequeña, referenciada por pedido).

Requiere: pip install psycopg2-binary
"""
import psycopg2
import random
import time

SEED = 272
N_PEDIDOS = 1_000_000
N_USUARIOS = 5_000
N_MEDICAMENTOS = 100

NODES = {
    "A": {"host": "localhost", "port": 5433, "dbname": "farmacia_db", "user": "farmacia_user", "password": "farmacia_pass"},
    "B": {"host": "localhost", "port": 5434, "dbname": "farmacia_db", "user": "farmacia_user", "password": "farmacia_pass"},
    "C": {"host": "localhost", "port": 5435, "dbname": "farmacia_db", "user": "farmacia_user", "password": "farmacia_pass"},
}

def conectar(node):
    return psycopg2.connect(**NODES[node])

def replicar_tabla_completa(tabla, filas, columnas):
    """Inserta las mismas filas en los 3 nodos (replicacion completa)."""
    for node in ["A", "B", "C"]:
        conn = conectar(node)
        cur = conn.cursor()
        cols = ", ".join(columnas)
        placeholders = ", ".join(["%s"] * len(columnas))
        cur.executemany(f"INSERT INTO {tabla} ({cols}) VALUES ({placeholders})", filas)
        conn.commit()
        conn.close()
    print(f"Replicado '{tabla}': {len(filas)} filas en los 3 nodos")

def generar_usuarios_y_medicamentos():
    rng = random.Random(SEED)
    usuarios = [(i, f"Nombre{i}", f"Apellido{i}") for i in range(1, N_USUARIOS + 1)]
    medicamentos = [(i, f"Medicamento{i}", round(rng.uniform(5, 100), 2)) for i in range(1, N_MEDICAMENTOS + 1)]
    replicar_tabla_completa("usuario", usuarios, ["id", "nombres", "apellidos"])
    replicar_tabla_completa("medicamento", medicamentos, ["id", "nombre", "precio"])

def fragmentar_por_rango():
    """Estrategia 1: fragmentacion horizontal por rango de id."""
    rng = random.Random(SEED)
    tercio = N_PEDIDOS // 3
    asignaciones = {"A": [], "B": [], "C": []}

    for pid in range(1, N_PEDIDOS + 1):
        id_usuario = rng.randint(1, N_USUARIOS)
        total = round(rng.uniform(10, 500), 2)
        fila = (pid, id_usuario, "2026-01-01", total)
        if pid <= tercio:
            asignaciones["A"].append(fila)
        elif pid <= tercio * 2:
            asignaciones["B"].append(fila)
        else:
            asignaciones["C"].append(fila)

    for node, filas in asignaciones.items():
        conn = conectar(node)
        cur = conn.cursor()
        cur.execute("DELETE FROM pedido;")
        cur.executemany("INSERT INTO pedido (id, id_usuario, fecha, total) VALUES (%s,%s,%s,%s)", filas)
        conn.commit()
        conn.close()
        print(f"[RANGO] Node {node}: {len(filas)} pedidos")

def fragmentar_por_hash():
    """Estrategia 2: fragmentacion por hash (modulo 3)."""
    rng = random.Random(SEED)
    asignaciones = {"A": [], "B": [], "C": []}
    node_por_mod = {0: "A", 1: "B", 2: "C"}

    for pid in range(1, N_PEDIDOS + 1):
        id_usuario = rng.randint(1, N_USUARIOS)
        total = round(rng.uniform(10, 500), 2)
        fila = (pid, id_usuario, "2026-01-01", total)
        node = node_por_mod[pid % 3]
        asignaciones[node].append(fila)

    for node, filas in asignaciones.items():
        conn = conectar(node)
        cur = conn.cursor()
        cur.execute("DELETE FROM pedido;")
        cur.executemany("INSERT INTO pedido (id, id_usuario, fecha, total) VALUES (%s,%s,%s,%s)", filas)
        conn.commit()
        conn.close()
        print(f"[HASH] Node {node}: {len(filas)} pedidos")

if __name__ == "__main__":
    print("--- Replicando usuario y medicamento (tablas pequeñas) ---")
    generar_usuarios_y_medicamentos()

    print("\n--- Estrategia 1: fragmentacion por RANGO ---")
    fragmentar_por_rango()

    print("\n--- Estrategia 2: fragmentacion por HASH ---")
    print("(Nota: esto sobrescribe 'pedido'; correr esta funcion SOLA si se quiere probar Hash en vez de Rango)")
