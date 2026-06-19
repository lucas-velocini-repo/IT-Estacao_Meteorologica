# uvicorn servidor:app --reload

import os
import sqlite3
from fastapi import FastAPI
from datetime import datetime, timedelta

app = FastAPI()

DB = "banco.db"
SCHEMA_PATH = "../database/schema.sql"


def get_conn():
    return sqlite3.connect(DB)


# Inicialização automática do banco
def init_db():
    conn = sqlite3.connect(DB)

    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())

    conn.close()
    print("Banco criado com sucesso!")


# Executa ao iniciar o servidor
@app.on_event("startup")
def startup():
    if not os.path.exists(DB):
        init_db()


# POST - receber dados (seu código)
@app.post("/dados")
async def receber_dados(data: dict):
    conn = get_conn()
    cursor = conn.cursor()

    device_id = data["device_id"]
    device_name = data.get("device_name", "unknown")

    lat = data.get("location", {}).get("lat", 0)
    lon = data.get("location", {}).get("lon", 0)

    # insere ou atualiza
    cursor.execute("""
        INSERT INTO devices (id, name, latitude, longitude)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            latitude=excluded.latitude,
            longitude=excluded.longitude
    """, (device_id, device_name, lat, lon))

    # cria medição
    cursor.execute("""
        INSERT INTO measurements (device_id)
        VALUES (?)
    """, (device_id,))

    measurement_id = cursor.lastrowid

    def save_param(prefix, obj):
        for key, value in obj.items():
            param_name = f"{prefix}_{key}".replace(".", "_")
            cursor.execute("""
                INSERT INTO measurement_values (measurement_id, parameter, value)
                VALUES (?, ?, ?)
            """, (measurement_id, param_name, float(value)))

    if "pm" in data:
        save_param("pm", data["pm"])

    if "nc" in data:
        save_param("nc", data["nc"])

    direct_fields = [
        "typical_size",
        "light",
        "temperature",
        "humidity",
        "pressure"
    ]

    for field in direct_fields:
        if field in data:
            cursor.execute("""
                INSERT INTO measurement_values (measurement_id, parameter, value)
                VALUES (?, ?, ?)
            """, (measurement_id, field, float(data[field])))

    conn.commit()
    conn.close()

    return {"status": "ok"}


# GET - listar dispositivos
@app.get("/devices")
def get_devices():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM devices")
    rows = cursor.fetchall()

    conn.close()

    return rows


# GET - últimas medições
@app.get("/measurements")
def get_measurements():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.id, m.device_id, m.timestamp
        FROM measurements m
        WHERE m.id IN (
            SELECT MAX(id)
            FROM measurements
            GROUP BY device_id
        )
        ORDER BY m.timestamp DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


# GET - valores de uma medição específica
@app.get("/measurement/{measurement_id}")
def get_measurement_values(measurement_id: int):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT parameter, value
        FROM measurement_values
        WHERE measurement_id = ?
    """, (measurement_id,))

    rows = cursor.fetchall()

    conn.close()

    return rows


@app.get("/timeseries")
def get_timeseries(device_id: int, parameter: str, limit: int = 100, start_date: str = None, end_date: str = None):
    conn = get_conn()
    cursor = conn.cursor()

    query = """
        SELECT m.timestamp, mv.value
        FROM measurement_values mv
        JOIN measurements m ON mv.measurement_id = m.id
        WHERE m.device_id = ? AND mv.parameter = ?
    """
    params = [device_id, parameter]

    # Se start_date é "today", usa a data de hoje
    if start_date == "today":
        today = datetime.now().date()
        start_date = f"{today} 00:00:00"
        end_date = f"{today} 23:59:59"
    
    if start_date:
        query += " AND m.timestamp >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND m.timestamp <= ?"
        params.append(end_date)

    query += f" ORDER BY m.timestamp ASC LIMIT {limit}"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    timestamps = [r[0] for r in rows]
    values = [r[1] for r in rows]

    return {
        "timestamps": timestamps,
        "values": values
    }

# GET - medições de um dispositivo específico (para histórico)
@app.get("/measurements-by-device/{device_id}")
def get_measurements_by_device(device_id: int, limit: int = 50):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.id, m.device_id, m.timestamp
        FROM measurements m
        WHERE m.device_id = ?
        ORDER BY m.timestamp DESC
        LIMIT ?
    """, (device_id, limit))

    rows = cursor.fetchall()
    conn.close()

    return rows