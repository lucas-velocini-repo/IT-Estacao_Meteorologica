# cd .\servidor_fastapi\
# uvicorn servidor:app --reload --host 0.0.0.0 --port 8000

from fastapi import FastAPI
from pydantic import BaseModel, Field
import sqlite3

app = FastAPI()

# CAMINHO DO BANCO
DB_PATH = r"C:\Users\Lucas Velocini\Desktop\Atalhos\Unicamp\IT-Estacao_Meteorologica\servidor_fastapi\DB\monitoramento_ambiental.db"

# ---------------------------
# MODELOS Pydantic
# ---------------------------

class PMModel(BaseModel):
    pm_1_0: float = Field(..., alias="1.0")
    pm_2_5: float = Field(..., alias="2.5")
    pm_4_0: float = Field(..., alias="4.0")
    pm_10_0: float = Field(..., alias="10.0")

    class Config:
        populate_by_name = True

class NCModel(BaseModel):
    nc_0_5: float = Field(..., alias="0.5")
    nc_1_0: float = Field(..., alias="1.0")
    nc_2_5: float = Field(..., alias="2.5")
    nc_4_0: float = Field(..., alias="4.0")
    nc_10_0: float = Field(..., alias="10.0")

    class Config:
        populate_by_name = True

class DadosModel(BaseModel):
    device_name: str
    pm: PMModel
    nc: NCModel
    typical_size: float
    light: float
    temperature: float
    humidity: float
    pressure: float


# ---------------------------
# FUNÇÕES AUXILIARES
# ---------------------------

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def get_or_create_device(conn, device_name):
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM devices WHERE name = ?",
        (device_name,)
    )
    result = cursor.fetchone()

    if result:
        return result[0]

    cursor.execute(
        "INSERT INTO devices (name) VALUES (?)",
        (device_name,)
    )
    conn.commit()

    return cursor.lastrowid


# ---------------------------
# ROTAS
# ---------------------------

@app.get("/esp")
def esp():
    return {"status": "ok"}


@app.post("/dados")
def receber_dados(dados: DadosModel):
    conn = get_connection()
    cursor = conn.cursor()

    # 1️⃣ DEVICE
    device_id = get_or_create_device(conn, dados.device_name)

    # 2️⃣ MEASUREMENT
    cursor.execute("""
        INSERT INTO measurements 
        (device_id, typical_size, light, temperature, humidity, pressure)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        device_id,
        dados.typical_size,
        dados.light,
        dados.temperature,
        dados.humidity,
        dados.pressure
    ))

    measurement_id = cursor.lastrowid

    # 3️⃣ PM DATA
    pm_dict = dados.pm.model_dump(by_alias=True)

    for size, value in pm_dict.items():
        cursor.execute("""
            INSERT INTO pm_data (measurement_id, size, value)
            VALUES (?, ?, ?)
        """, (measurement_id, float(size), value))

    # 4️⃣ NC DATA
    nc_dict = dados.nc.model_dump(by_alias=True)

    for size, value in nc_dict.items():
        cursor.execute("""
            INSERT INTO nc_data (measurement_id, size, value)
            VALUES (?, ?, ?)
        """, (measurement_id, float(size), value))

    conn.commit()
    conn.close()

    return {
        "status": "ok",
        "device_id": device_id,
        "measurement_id": measurement_id
    }


@app.get("/dados")
def obter_dados():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.id, d.name, m.timestamp, m.temperature, m.humidity
        FROM measurements m
        JOIN devices d ON m.device_id = d.id
        ORDER BY m.timestamp DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows

@app.get("/devices")
def listar_devices():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM devices")
    rows = cursor.fetchall()
    conn.close()

    return [{"id": r[0], "name": r[1]} for r in rows]

@app.get("/dados/{device_id}")
def obter_dados_por_device(device_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, typical_size, light, temperature, humidity, pressure
        FROM measurements
        WHERE device_id = ?
        ORDER BY timestamp DESC
        LIMIT 50
    """, (device_id,))

    measurements = cursor.fetchall()

    dados = []

    for m in measurements:
        measurement_id = m[0]

        # PM
        cursor.execute("SELECT size, value FROM pm_data WHERE measurement_id = ?", (measurement_id,))
        pm = {str(row[0]): row[1] for row in cursor.fetchall()}

        # NC
        cursor.execute("SELECT size, value FROM nc_data WHERE measurement_id = ?", (measurement_id,))
        nc = {str(row[0]): row[1] for row in cursor.fetchall()}

        dados.append({
            "timestamp": m[1],
            "typical_size": m[2],
            "light": m[3],
            "temperature": m[4],
            "humidity": m[5],
            "pressure": m[6],
            "pm": pm,
            "nc": nc
        })

    conn.close()
    return dados[::-1]  # ordem cronológica