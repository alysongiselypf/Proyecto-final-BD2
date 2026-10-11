"""
Router simple que simula la latencia de red documentada en la rubrica
(A-B=20ms, A-C=40ms, B-C=25ms) mediante time.sleep antes de ejecutar
una consulta en un nodo distinto al 'nodo local' desde donde se origina.
"""
import psycopg2
import time

LATENCIAS_MS = {
    ("A", "B"): 20, ("B", "A"): 20,
    ("A", "C"): 40, ("C", "A"): 40,
    ("B", "C"): 25, ("C", "B"): 25,
}

NODES = {
    "A": {"host": "localhost", "port": 5433, "dbname": "farmacia_db", "user": "farmacia_user", "password": "farmacia_pass"},
    "B": {"host": "localhost", "port": 5434, "dbname": "farmacia_db", "user": "farmacia_user", "password": "farmacia_pass"},
    "C": {"host": "localhost", "port": 5435, "dbname": "farmacia_db", "user": "farmacia_user", "password": "farmacia_pass"},
}

def ejecutar_consulta(nodo_origen, nodo_destino, query, params=None):
    """Ejecuta una consulta en nodo_destino, simulando la latencia de
    red si nodo_origen != nodo_destino (consulta cruzada entre nodos)."""
    if nodo_origen != nodo_destino:
        latencia_s = LATENCIAS_MS[(nodo_origen, nodo_destino)] / 1000.0
        time.sleep(latencia_s)

    conn = psycopg2.connect(**NODES[nodo_destino])
    cur = conn.cursor()
    cur.execute(query, params)
    try:
        resultado = cur.fetchall()
    except psycopg2.ProgrammingError:
        resultado = None
    conn.commit()
    conn.close()
    return resultado

def nodo_por_rango(pedido_id, n_pedidos=1_000_000):
    tercio = n_pedidos // 3
    if pedido_id <= tercio: return "A"
    elif pedido_id <= tercio * 2: return "B"
    else: return "C"

def nodo_por_hash(pedido_id):
    return {0: "A", 1: "B", 2: "C"}[pedido_id % 3]
