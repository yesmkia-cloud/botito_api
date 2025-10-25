
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import re, unicodedata

app = FastAPI(title="Bot-ito API", version="0.2.0")

# --- CORS (para que clientes web puedan llamarte) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # cuando vendas, cámbialo a dominios de tus clientes
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Key simple (para planes de pago) ---
REQUIRED_API_KEY = os.getenv("API_KEY")  # si no está, no exigimos key (modo demo)

def check_key(x_api_key: str | None):
    if REQUIRED_API_KEY and x_api_key != REQUIRED_API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")

# --- MODELOS ---
class EchoIn(BaseModel):
    text: str

# --- ENDPOINT raíz (ping) ---
@app.get("/")
def read_root():
    return {"message": "Hola Liliana 🌞, Bot-ito API ahora está actualizada correctamente."}

# 1) ECHO (POST) ---------------------------------------------------------------
@app.post("/echo")
def echo(payload: EchoIn, x_api_key: str | None = Header(default=None)):
    check_key(x_api_key)
    return {"echo": payload.text}

# 2) SENTIMIENTO NAIVE (POST) --------------------------------------------------
@app.post("/sentiment")
def sentiment(payload: EchoIn, x_api_key: str | None = Header(default=None)):
    check_key(x_api_key)
    t = payload.text.lower()
    score = (t.count("bien") + t.count("feliz") + t.count("gracias") + t.count("😊")) \
            - (t.count("mal") + t.count("triste") + t.count("odio") + t.count("😢"))
    label = "positivo" if score > 0 else "negativo" if score < 0 else "neutral"
    return {"label": label, "score": score}

# 3) SLUG (POST) ---------------------------------------------------------------
@app.post("/slug")
def slugify(payload: EchoIn, x_api_key: str | None = Header(default=None)):
    check_key(x_api_key)
    t = unicodedata.normalize('NFKD', payload.text).encode("ascii", "ignore").decode("ascii")
    t = re.sub(r"[^a-zA-Z0-9\s-]", "", t).strip().lower()
    t = re.sub(r"[\s-]+", "-", t)
    return {"slug": t}

# 4) HEALTH (GET) --------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
