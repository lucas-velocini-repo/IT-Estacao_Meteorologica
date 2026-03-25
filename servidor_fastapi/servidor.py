# cd C:\Users\Lucas Velocini\Desktop\Atalhos\Unicamp\IT-Estacao_Meteorologica\fastapi_esp_test
# uvicorn fastapi_esp:app --reload --host 0.0.0.0 --port 8000

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

# MODELOS Pydantic
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
    pm: PMModel
    nc: NCModel
    typical_size: float
    light: float
    temperature: float
    humidity: float
    pressure: float

# "BANCO" EM MEMÓRIA
ultimo_dado: DadosModel | None = None

# ROTAS
@app.get("/esp")
def esp():
    return {"status": "ok"}

@app.post("/dados")
def receber_dados(dados: DadosModel):
    global ultimo_dado
    ultimo_dado = dados
    return ultimo_dado

@app.get("/dados")
def obter_ultimo_dado():
    if ultimo_dado is None:
        return {"status": "nenhum dado recebido ainda"}
    return ultimo_dado
