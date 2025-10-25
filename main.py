from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hola Liliana 🌞, tu API Bot-ito está viva!"}

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hola Liliana 🌞, Bot-ito API ahora está actualizada correctamente."}
