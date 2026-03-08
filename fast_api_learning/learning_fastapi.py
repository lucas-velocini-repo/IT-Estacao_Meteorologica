# cd D:\Documentos\Lucas\Atalhos\Unicamp\Programas\IT-Iniciacao_Tecnologica\fast_api_learning
# uvicorn learning_fastapi:app --reload 

# http://127.0.0.1:8000/docs#/
# http://127.0.0.1:8000/redoc

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    text: str = None
    is_done: bool = False

items = []

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/items")
def create_item(item: Item):
    items.append(item)
    return items

@app.get("/items")
def list_items(limit: int = 10):
    return items[0:limit]

@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int) -> Item:
    if item_id < len(items):
        item = items[item_id]
        return item
    else:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found.")