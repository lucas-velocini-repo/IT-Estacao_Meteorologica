#uvicorn servidor:app --reload
#ou
#uvicorn servidor:app --host 0.0.0.0 --port 8000

import os
import sqlite3
import time
from typing import Optional

from fastapi import FastAPI, Query

app = FastAPI()

DB = "banco.db"
SCHEMA_PATH = "../database/schema.sql"

def get_conn():
    return sqlite3.connect(DB)

def ensure_measurement_time_columns():
    conn = get_conn()
    cursor = conn.cursor()

    columns = {
        row[1]
        for row in cursor.execute(
            "PRAGMA table_info(measurements)"
        ).fetchall()
    }

    if "measured_at" not in columns:
        cursor.execute(
            """
            ALTER TABLE measurements
            ADD COLUMN measured_at INTEGER
            """
        )

    if "received_at" not in columns:
        cursor.execute(
            """
            ALTER TABLE measurements
            ADD COLUMN received_at INTEGER
            """
        )

    current_epoch = int(time.time())

    # Migração dos registros antigos.
    # A antiga coluna timestamp foi criada em UTC pelo SQLite.
    if "timestamp" in columns:
        cursor.execute(
            """
            UPDATE measurements
            SET measured_at = COALESCE(
                measured_at,
                CAST(strftime('%s', timestamp) AS INTEGER)
            )
            """
        )

        cursor.execute(
            """
            UPDATE measurements
            SET received_at = COALESCE(
                received_at,
                CAST(strftime('%s', timestamp) AS INTEGER)
            )
            """
        )
    else:
        cursor.execute(
            """
            UPDATE measurements
            SET measured_at = COALESCE(
                measured_at,
                ?
            )
            """,
            (current_epoch,)
        )

        cursor.execute(
            """
            UPDATE measurements
            SET received_at = COALESCE(
                received_at,
                ?
            )
            """,
            (current_epoch,)
        )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_measurements_device_measured_at
        ON measurements(device_id, measured_at)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_measurement_values_measurement
        ON measurement_values(measurement_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_measurement_values_parameter_measurement
        ON measurement_values(parameter, measurement_id)
        """
    )

    conn.commit()
    conn.close()

    print(
        "Colunas de horário e índices verificados."
    )

def normalize_measured_at(
    raw_timestamp,
    received_at: int
):
    try:
        measured_at = int(raw_timestamp)
    except (TypeError, ValueError):
        return received_at, "server"

    # 2020-01-01 UTC.
    # Valores menores normalmente indicam millis()/1000
    # ou relógio ainda não sincronizado.
    minimum_valid_timestamp = 1577836800

    # Aceita pequena diferença de relógio, mas rejeita
    # datas mais de um dia no futuro.
    maximum_valid_timestamp = (
        received_at + 24 * 60 * 60
    )

    if (
        measured_at < minimum_valid_timestamp
        or measured_at > maximum_valid_timestamp
    ):
        return received_at, "server"

    return measured_at, "device"

# Inicialização automática do banco
def init_db():
    conn = sqlite3.connect(DB)

    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())

    conn.close()
    print("Banco criado com sucesso!")

@app.on_event("startup")
def startup():
    if not os.path.exists(DB):
        init_db()

    ensure_measurement_time_columns()

# POST - receber dados 
@app.post("/dados")
async def receber_dados(data: dict):
    conn = get_conn()
    cursor = conn.cursor()

    device_id = data["device_id"]
    device_name = data.get("device_name", "unknown")

    lat = data.get("location", {}).get("lat", 0)
    lon = data.get("location", {}).get("lon", 0)

    received_at = int(time.time())

    measured_at, time_source = (
        normalize_measured_at(
            data.get(
                "measured_at",
                data.get("timestamp")
            ),
            received_at
        )
    )

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
    cursor.execute(
        """
        INSERT INTO measurements (
            device_id,
            measured_at,
            received_at
        )
        VALUES (?, ?, ?)
        """,
        (
            device_id,
            measured_at,
            received_at
        )
    )

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

    return {
        "status": "ok",
        "measurement_id": measurement_id,
        "measured_at": measured_at,
        "received_at": received_at,
        "time_source": time_source
    }

@app.get("/devices")
def get_devices():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM devices")
    rows = cursor.fetchall()

    conn.close()

    return rows

@app.get("/measurements")
def get_measurements():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            m.id,
            m.device_id,
            m.measured_at
        FROM measurements m
        WHERE m.id IN (
            SELECT MAX(id)
            FROM measurements
            GROUP BY device_id
        )
        ORDER BY m.measured_at DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

@app.get("/timeseries")
def get_timeseries(
    device_id: int,
    parameter: str,

    limit: int = Query(
        default=100,
        ge=2,
        le=300
    ),

    start_timestamp: Optional[int] = None,
    end_timestamp: Optional[int] = None
):
    conn = get_conn()
    cursor = conn.cursor()

    conditions = [
        "m.device_id = ?",
        "mv.parameter = ?"
    ]

    params = [
        device_id,
        parameter
    ]

    if start_timestamp is not None:
        conditions.append(
            "m.measured_at >= ?"
        )

        params.append(start_timestamp)

    if end_timestamp is not None:
        conditions.append(
            "m.measured_at <= ?"
        )

        params.append(end_timestamp)

    where_clause = " AND ".join(
        conditions
    )

    query = f"""
        SELECT measured_at, value
        FROM (
            SELECT
                m.measured_at AS measured_at,
                mv.value AS value
            FROM measurement_values mv
            JOIN measurements m
                ON mv.measurement_id = m.id
            WHERE {where_clause}
            ORDER BY m.measured_at DESC
            LIMIT ?
        )
        ORDER BY measured_at ASC
    """

    params.append(limit)

    cursor.execute(
        query,
        params
    )

    rows = cursor.fetchall()

    conn.close()

    return {
        "timestamps": [
            row[0]
            for row in rows
        ],
        "values": [
            row[1]
            for row in rows
        ]
    }

@app.get("/device-measurements/{device_id}")
def get_complete_device_measurements(
    device_id: int,
    limit: int = Query(
        default=50,
        ge=1,
        le=300
    )
):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            m.id,
            m.device_id,
            m.measured_at,
            m.received_at,
            mv.parameter,
            mv.value
        FROM (
            SELECT
                id,
                device_id,
                measured_at,
                received_at
            FROM measurements
            WHERE device_id = ?
            ORDER BY
                measured_at DESC,
                id DESC
            LIMIT ?
        ) AS m
        LEFT JOIN measurement_values mv
            ON mv.measurement_id = m.id
        ORDER BY
            m.measured_at DESC,
            m.id DESC,
            mv.parameter ASC
        """,
        (
            device_id,
            limit
        )
    )

    rows = cursor.fetchall()
    conn.close()

    measurements = {}

    for (
        measurement_id,
        row_device_id,
        measured_at,
        received_at,
        parameter,
        value
    ) in rows:
        if measurement_id not in measurements:
            measurements[measurement_id] = {
                "measurement_id": measurement_id,
                "device_id": row_device_id,

                # Mantemos o nome timestamp no JSON
                # para não precisar alterar mais partes do React.
                "timestamp": measured_at,

                "measured_at": measured_at,
                "received_at": received_at,

                "values": {}
            }

        if parameter is not None:
            measurements[
                measurement_id
            ]["values"][parameter] = value

    return list(
        measurements.values()
    )
