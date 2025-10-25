
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import unicodedata, re

# ------------------------------------------
# Inicialización de la app
# ------------------------------------------
app = FastAPI(title="Bot-ito API", description="Mini API de texto con control de uso")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------
# Variables globales (temporales)
# ------------------------------------------
API_KEY = "BOTITO_2025_SUPER"
USAGE_LIMIT = 100  # límite temporal por API Key
usage_counter = {}  # guardará conteos de llamadas

# ------------------------------------------
# Modelos
# ------------------------------------------
class EchoIn(BaseModel):
    text: str

# ------------------------------------------
# Funciones auxiliares
# ------------------------------------------
def check_key(x_api_key: str | None):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida o ausente")

def register_usage(x_api_key: str):
    if x_api_key not in usage_counter:
        usage_counter[x_api_key] = 0
    usage_counter[x_api_key] += 1
    if usage_counter[x_api_key] > USAGE_LIMIT:
        raise HTTPException(status_code=402, detail="Límite de uso alcanzado")
    return usage_counter[x_api_key]

# ------------------------------------------
# 1) ROOT (GET)
# ------------------------------------------
@app.get("/")
def read_root():
    return {"message": "Hola Liliana 🦋, tu API Bot-ito sigue viva y ahora mide su uso."}

# ------------------------------------------
# 2) ECHO (POST)
# ------------------------------------------
@app.post("/echo")
def echo(payload: EchoIn, x_api_key: str | None = Header(default=None)):
    check_key(x_api_key)
    register_usage(x_api_key)
    return {"echo": payload.text}

# ------------------------------------------
# 3) SENTIMENT (POST)
# ------------------------------------------
@app.post("/sentiment")
def sentiment(payload: EchoIn, x_api_key: str | None = Header(default=None)):
    check_key(x_api_key)
    register_usage(x_api_key)
    text = payload.text.lower()
    positive = ["feliz", "excelente", "bien", "contento", "genial"]
    negative = ["mal", "triste", "horrible", "enojado", "terrible"]
    score = "neutral"
    if any(p in text for p in positive):
        score = "positivo"
    elif any(n in text for n in negative):
        score = "negativo"
    return {"sentimiento": score}

# ------------------------------------------
# 4) SLUG (POST)
# ------------------------------------------
@app.post("/slug")
def slugify(payload: EchoIn, x_api_key: str | None = Header(default=None)):
    check_key(x_api_key)
    register_usage(x_api_key)
    t = unicodedata.normalize('NFKD', payload.text).encode('ascii', 'ignore').decode('ascii')
    t = re.sub(r'[^a-zA-Z0-9\s-]', '', t).strip().lower()
    t = re.sub(r'[\s-]+', '-', t)
    return {"slug": t}

# ------------------------------------------
# 5) USAGE (GET)
# ------------------------------------------
@app.get("/usage")
def usage(x_api_key: str | None = Header(default=None)):
    check_key(x_api_key)
    count = usage_counter.get(x_api_key, 0)
    remaining = USAGE_LIMIT - count
    return {
        "api_key": x_api_key,
        "requests_used": count,
        "limit": USAGE_LIMIT,
        "remaining": remaining,
        "status": "activo" if remaining > 0 else "bloqueado"
    }

# ------------------------------------------
# 6) HEALTH (GET)
# ------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
