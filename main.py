
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
# 2) SENTIMENT (POST) ------------------------------------------
from typing import Optional
import unicodedata, re

POS = {
    "feliz","contento","contenta","genial","excelente","maravilloso","increible",
    "fantastico","bueno","bien","alegre","emocionado","entusiasmado","tranquilo",
    "agradecido","mejor","exito","logre","logrado"
}
NEG = {
    "enojado","enojada","enoja","enojar","molesto","molesta","triste","furioso",
    "furiosa","frustrado","frustrada","estresado","estresada","mal","horrible",
    "terrible","miedo","ansioso","ansiosa","deprimido","deprimida","fatal","odio",
    "enfado","rabia","cansado","cansada","dolor","preocupado","preocupada","estres"
}

def _normalize_es(text: str) -> str:
    t = unicodedata.normalize("NFKD", text).encode("ascii","ignore").decode("ascii")
    t = t.lower()
    # deja solo letras y espacios
    t = re.sub(r"[^a-z\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

@app.post("/sentiment")
def sentiment(payload: EchoIn, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)

    t = _normalize_es(payload.text)
    tokens = t.split()

    pos = sum(1 for w in tokens if w in POS)
    neg = sum(1 for w in tokens if w in NEG)

    # Intensificadores sencillos
    if "muy" in tokens:
        if any(w in NEG for w in tokens): neg += 1
        if any(w in POS for w in tokens): pos += 1

    if neg > pos:
        s = "negativo"
    elif pos > neg:
        s = "positivo"
    else:
        s = "neutral"

    return {"sentimiento": s, "pos": pos, "neg": neg}


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
