from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import unicodedata, re

# =========================
# Configuración general
# =========================
app = FastAPI(title="Bot-ito API", version="0.4.0", description="API de utilidades de texto con análisis de sentimiento en ES")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # cámbialo a dominios de clientes cuando vendas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = "BOTITO_2025_SUPER"
USAGE_LIMIT = 100
usage_counter: Dict[str, int] = {}

class EchoIn(BaseModel):
    text: str

def check_key(x_api_key: Optional[str]):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida o ausente")

def register_usage(x_api_key: str):
    usage_counter[x_api_key] = usage_counter.get(x_api_key, 0) + 1
    if usage_counter[x_api_key] > USAGE_LIMIT:
        raise HTTPException(status_code=402, detail="Límite de uso alcanzado")
    return usage_counter[x_api_key]

# =========================
# Utilidades de texto
# =========================
# ========= Sentiment v0.5 (ES) =========
import unicodedata, re, math
from typing import Optional
from fastapi import Header

# --- utilidades ---
def _normalize(text: str) -> str:
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9#\+\-\_\s]", "", t.lower())

def _tokens(text: str) -> list[str]:
    # separa por espacios y signos -_+#
    return [t for t in re.split(r"[\s\-\_]+", text) if t]

def _tanh(x: float) -> float:
    # normaliza soft entre -1..1
    return math.tanh(x)

def _color_from_score(s: float) -> str:
    # verde positivo, ámbar neutro, rojo negativo
    if s >  0.25: return "#00c851"
    if s < -0.25: return "#ff4444"
    return "#f1c40f"

# --- diccionarios base (puedes ampliarlos cuando quieras) ---
POS = {
    "bien","excelente","feliz","felices","contento","contenta","genial","maravilloso","maravillosa",
    "fantastico","fantastica","increible","recomendado","recomendadisimo","mejor","perfecto","perfecta",
    "encanta","encanto","encantado","encantada","amo","love","wow","brutal","rapido","barato","agradecido","gracias"
}
NEG = {
    "mal","malo","pesimo","horrible","terrible","triste","tristes","enojado","enojada","molesto","molesta",
    "furioso","furiosa","decepcionado","decepcionada","asco","asqueroso","asquerosa","lento","tarde",
    "cancelado","caro","fraude","estafa","error","fallo","bug","crash","odio","odiar"
}
# categorías emocionales (conteos en 'detalles')
CAT = {
    "alegria": {"feliz","contento","contenta","encanta","encanto","genial","maravilloso","maravillosa","fantastico","fantastica","increible","amo","love","gracias","wow"},
    "enojo":   {"enojado","enojada","molesto","molesta","furioso","furiosa","odio"},
    "tristea": {"triste","tristes","decepcionado","decepcionada"},
    "miedo":   {"miedo","temor","asusta","asustado","asustada"},
    "asco":    {"asco","asqueroso","asquerosa"},
    "sorpresa":{"sorprendido","sorprendida","wow","increible","brutal"}
}
# emojis (se evalúan antes de tokens)
EMO_POS = {"😀","😄","😁","🙂","😊","😍","🥰","👍","✨","🎉","🔥"}
EMO_NEG = {"😡","🤬","😤","😞","😢","😭","👎","💔","🤢","🤮"}

INTENS = {  # intensificadores -> multiplicador
    "muy":1.5, "super":2.0, "súper":2.0, "bastante":1.3, "recontra":2.0, "mega":1.7, "hiper":1.7
}
NEGA = {"no","nunca","jamas","jamás","ni"}

def _apply_window_modifiers(idx: int, toks: list[str], base: float) -> float:
    # mira 2 tokens hacia atrás para intensificadores/negaciones
    start = max(0, idx-2)
    window = toks[start:idx]
    mult = 1.0
    flip = False
    for w in window:
        if w in INTENS: mult *= INTENS[w]
        if w in NEGA:  flip = not flip
    return -base*mult if flip else base*mult

def analyze_sentiment_v05(text: str) -> dict:
    raw = text
    # cuenta emojis rápido
    emoji_pos = sum(1 for c in raw if c in EMO_POS)
    emoji_neg = sum(1 for c in raw if c in EMO_NEG)

    s = _normalize(raw)
    toks = _tokens(s)

    score = 0.0
    pos_hits = 0
    neg_hits = 0

    detalles = {"alegria":0,"enojo":0,"tristeza":0,"miedo":0,"asco":0,"sorpresa":0}

    # emojis pesan 1 cada uno
    score += emoji_pos * 1.0
    score -= emoji_neg * 1.0

    for i, t in enumerate(toks):
        base = 0.0
        if t in POS:
            base = +1.0
            pos_hits += 1
        elif t in NEG:
            base = -1.0
            neg_hits += 1

        if base != 0.0:
            score += _apply_window_modifiers(i, toks, base)

        # conteo por categorías
        for cat, words in CAT.items():
            if t in words:
                # normaliza nombre "tristea" -> "tristeza"
                key = "tristeza" if cat == "tristea" else cat
                detalles[key] += 1

    # normalización suave por magnitud (evita crecer infinito)
    norm = _tanh(score / 3.0)
    if norm >  0.1: label = "positivo"
    elif norm < -0.1: label = "negativo"
    else: label = "neutral"

    return {
        "sentimiento": label,
        "score": round(norm, 3),
        "color": _color_from_score(norm),
        "detalles": detalles,
        "tokens": toks[:100]  # por si quieres inspección rápida
    }

# --- endpoint protegido ---
@app.post("/sentiment")
def sentiment(payload: EchoIn, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)  # tu función de seguridad existente
    return analyze_sentiment_v05(payload.text)
# ========= /Sentiment v0.5 =========


# =========================
# ENDPOINTS
# =========================
@app.get("/")
def read_root():
    return {"message": "Hola Liliana 🌈, Bot-ito v0.4 con sentimiento avanzado y colores."}

@app.post("/echo")
def echo(payload: EchoIn, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    register_usage(x_api_key)
    return {"echo": payload.text}

@app.post("/sentiment")
def sentiment(payload: EchoIn, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    register_usage(x_api_key)
    return sentiment_analyze(payload.text)

@app.post("/slug")
def slugify(payload: EchoIn, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    register_usage(x_api_key)
    t = unicodedata.normalize('NFKD', payload.text).encode('ascii', 'ignore').decode('ascii')
    t = re.sub(r'[^a-zA-Z0-9\s-]', '', t).strip().lower()
    t = re.sub(r'[\s-]+', '-', t)
    return {"slug": t}

@app.get("/usage")
def usage(x_api_key: Optional[str] = Header(default=None)):
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

@app.get("/health")
def health():
    return {"status": "ok"}

