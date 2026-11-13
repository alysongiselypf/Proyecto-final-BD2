"""Valida D1, D2, W1-W3 y D3 segun la rubrica (7.1 y 7.2).

Uso (desde datasets\\validate\\):
    python check_workloads.py                 # usa ..\\output
    python check_workloads.py <ruta_output>   # otra carpeta
"""
import collections
import os
import sys

BASE = (sys.argv[1] if len(sys.argv) > 1 else
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output"))
SIZES = [100000, 500000, 1000000]
N_W1 = N_W2 = N_D3 = 10000
fallos = 0


def leer(nombre):
    """Lee enteros de un CSV de una columna (ignora cabecera y CRLF)."""
    ruta = os.path.join(BASE, nombre)
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        return [int(t) for t in f.read().split() if t.lstrip("-").isdigit()]


def chk(cond, msg):
    global fallos
    print(("  OK     " if cond else "  FALLA  ") + msg)
    if not cond:
        fallos += 1


for ds in ("d1_secuencial", "d2_aleatorio"):
    for n in SIZES:
        print(f"\n== {ds}  N={n}")
        datos = leer(f"{ds}_{n}.csv")
        if datos is None:
            chk(False, "falta el dataset")
            continue
        s = set(datos)
        chk(len(datos) == n and len(s) == n,
            f"{len(datos)} filas, {len(s)} claves unicas (esperado {n})")
        if ds == "d1_secuencial":
            chk(min(datos) == 1 and max(datos) == n, f"rango 1..{n} (real {min(datos)}..{max(datos)})")
        else:
            print(f"  info    rango de claves {min(datos)}..{max(datos)}")

        # W1: busquedas exitosas
        w1 = leer(f"workload_{ds}_{n}_w1.csv")
        if w1 is None:
            chk(False, "falta W1")
        else:
            chk(len(w1) == N_W1, f"W1 tiene {len(w1)} claves (esperado {N_W1})")
            chk(all(k in s for k in w1), "W1: todas las claves existen en el dataset")

        # W2: busquedas no exitosas
        w2 = leer(f"workload_{ds}_{n}_w2.csv")
        if w2 is None:
            chk(False, "falta W2")
        else:
            chk(len(w2) == N_W2, f"W2 tiene {len(w2)} claves (esperado {N_W2})")
            chk(not any(k in s for k in w2), "W2: ninguna clave existe en el dataset")
            print(f"  info    W2 rango {min(w2)}..{max(w2)}  (dataset max = {max(datos)})")

        # W3: inserciones (10% del tamano inicial)
        w3 = leer(f"workload_{ds}_{n}_w3.csv")
        if w3 is None:
            chk(False, "falta W3")
        else:
            chk(len(w3) == n // 10, f"W3 tiene {len(w3)} claves (esperado {n // 10})")
            chk(len(set(w3)) == len(w3), "W3: sin claves repetidas")
            chk(not any(k in s for k in w3), "W3: ninguna clave ya existe en el dataset")

        # D3: consultas sesgadas sobre los datos de D2
        if ds == "d2_aleatorio":
            d3 = leer(f"d3_sesgado_{n}_{N_D3}.csv")
            if d3 is None:
                chk(False, "falta D3")
            else:
                c = collections.Counter(d3)
                chk(len(d3) == N_D3, f"D3 tiene {len(d3)} consultas (esperado {N_D3})")
                chk(all(k in s for k in d3), "D3: todas las claves pertenecen a D2")
                chk(len(c) < len(d3), f"D3 es sesgado: {len(c)} claves distintas de {len(d3)} consultas")
                print(f"  info    D3 top-5 frecuencias: {c.most_common(5)}")

print("\n" + ("TODO OK" if fallos == 0 else f"{fallos} comprobacion(es) FALLARON"))
sys.exit(1 if fallos else 0)


