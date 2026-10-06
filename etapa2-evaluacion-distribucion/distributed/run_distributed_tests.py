"""
Ejecuta las pruebas obligatorias de la seccion 6.3:
- Carga 70% lectura / 30% escritura
- Consultas locales vs consultas que cruzan nodos
- Comparacion RANGO vs HASH
- Simulacion de caida de un nodo
- Cambio de concentracion de carga entre nodos
"""
import time
import random
import psycopg2
from query_router import ejecutar_consulta, nodo_por_rango, nodo_por_hash, NODES

SEED = 272
N_OPS = 1000  # numero de operaciones de prueba

def prueba_carga_70_30(estrategia_fn, nombre_estrategia):
    rng = random.Random(SEED)
    inicio = time.perf_counter()
    lecturas, escrituras = 0, 0

    for i in range(N_OPS):
        pedido_id = rng.randint(1, 1_000_000)
        nodo_destino = estrategia_fn(pedido_id)
        nodo_origen = "A"  # asumimos que el cliente "vive" cerca del nodo A

        if rng.random() < 0.70:
            ejecutar_consulta(nodo_origen, nodo_destino,
                               "SELECT * FROM pedido WHERE id = %s", (pedido_id,))
            lecturas += 1
        else:
            ejecutar_consulta(nodo_origen, nodo_destino,
                               "UPDATE pedido SET total = total + 1 WHERE id = %s", (pedido_id,))
            escrituras += 1

    duracion = time.perf_counter() - inicio
    print(f"[{nombre_estrategia}] {N_OPS} ops (70/30): {duracion:.2f}s "
          f"(lecturas={lecturas}, escrituras={escrituras})")
    return duracion

def prueba_consulta_cruzada():
    """Consulta que necesita datos de mas de un nodo: pedidos de 2
    fragmentos distintos (RANGO), agregados en el cliente."""
    inicio = time.perf_counter()
    r1 = ejecutar_consulta("A", "A", "SELECT count(*) FROM pedido;")
    r2 = ejecutar_consulta("A", "B", "SELECT count(*) FROM pedido;")
    r3 = ejecutar_consulta("A", "C", "SELECT count(*) FROM pedido;")
    total = r1[0][0] + r2[0][0] + r3[0][0]
    duracion = time.perf_counter() - inicio
    print(f"Consulta cruzada (3 nodos, agregada en cliente): {duracion:.3f}s, total={total}")

def prueba_consulta_local():
    inicio = time.perf_counter()
    ejecutar_consulta("A", "A", "SELECT count(*) FROM pedido;")
    duracion = time.perf_counter() - inicio
    print(f"Consulta local (mismo nodo, sin latencia simulada): {duracion:.3f}s")

def prueba_nodo_caido():
    """Simula la indisponibilidad del nodo B deteniendolo con Docker,
    y verifica el comportamiento de una consulta dirigida a el."""
    import subprocess
    print("Deteniendo nodeB (docker stop)...")
    subprocess.run(["docker", "stop", "farmacia_nodeB"])
    time.sleep(2)
    try:
        ejecutar_consulta("A", "B", "SELECT count(*) FROM pedido;")
        print("ERROR: se esperaba una excepcion, el nodo deberia estar caido")
    except Exception as e:
        print(f"Comportamiento esperado: consulta a nodo caido fallo -> {type(e).__name__}: {e}")
    finally:
        print("Reiniciando nodeB...")
        subprocess.run(["docker", "start", "farmacia_nodeB"])
        time.sleep(5)

def prueba_cambio_concentracion():
    """Simula un cambio en la carga: en vez de distribuir uniforme,
    80% de las consultas se concentran en el nodo A (hotspot)."""
    rng = random.Random(SEED)
    inicio = time.perf_counter()
    for i in range(N_OPS):
        if rng.random() < 0.80:
            nodo_destino = "A"
        else:
            nodo_destino = rng.choice(["B", "C"])
        ejecutar_consulta("A", nodo_destino, "SELECT count(*) FROM pedido;")
    duracion = time.perf_counter() - inicio
    print(f"Carga concentrada 80% en nodeA ({N_OPS} ops): {duracion:.2f}s")

if __name__ == "__main__":
    print("=== Prueba de consulta local vs cruzada ===")
    prueba_consulta_local()
    prueba_consulta_cruzada()

    print("\n=== Comparacion de estrategias bajo carga 70/30 ===")
    t_rango = prueba_carga_70_30(nodo_por_rango, "RANGO")
    t_hash = prueba_carga_70_30(nodo_por_hash, "HASH")
    print(f"\nDiferencia: {'RANGO' if t_rango < t_hash else 'HASH'} fue mas rapido "
          f"({abs(t_rango - t_hash):.2f}s de diferencia)")

    print("\n=== Prueba de cambio de concentracion de carga ===")
    prueba_cambio_concentracion()

    print("\n=== Prueba de indisponibilidad de nodo ===")
    prueba_nodo_caido()
