"""
Carga un dataset CSV generado en datasets/output/ a una tabla temporal
en PostgreSQL, usando COPY (carga masiva nativa, mucho mas rapida que
INSERT fila por fila).

Requiere: pip install psycopg2-binary
Uso: python load_dataset.py <ruta_csv> <nombre_tabla>
Ejemplo: python load_dataset.py ../output/d1_secuencial_100000.csv bench_d1_100000
"""
import sys
import csv
import psycopg2
import time

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "farmacia_db",
    "user": "farmacia_user",
    "password": "farmacia_pass",
}

def cargar_csv(csv_path, tabla):
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        columna = header[0]

    tipo_sql = "INTEGER" if columna in ("id", "id_consultado") else "VARCHAR(64)"

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute(f"DROP TABLE IF EXISTS {tabla};")
    cur.execute(f"CREATE TABLE {tabla} ({columna} {tipo_sql});")
    conn.commit()

    inicio = time.time()
    with open(csv_path, "r") as f:
        next(f)  # saltar header
        cur.copy_expert(f"COPY {tabla} ({columna}) FROM STDIN WITH CSV", f)
    conn.commit()
    duracion = time.time() - inicio

    cur.execute(f"SELECT COUNT(*) FROM {tabla};")
    total = cur.fetchone()[0]

    cur.close()
    conn.close()

    print(f"Cargados {total} registros en '{tabla}' en {duracion:.2f} segundos (via COPY)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python load_dataset.py <ruta_csv> <nombre_tabla>")
        sys.exit(1)

    csv_path = sys.argv[1]
    tabla = sys.argv[2]
    cargar_csv(csv_path, tabla)

