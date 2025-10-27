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
EMOJI_POS = {"😀","😄","😁","😊","🙂","😍","🥰","🤩","👍","✨","💖","😎"}
EMOJI_NEG = {"😠","😡","🤬","😞","😢","😭","😰","😨","👎","💔","😫","😩","🤢"}

INTENSIFICADORES = {"muy","super","súper","re","mega","ultra","demasiado","tan"}
ATENUADORES = {"poco","apenas","algo","ligeramente"}
NEGADORES = {"no","nunca","jamas","jamás","sin"}

# Diccionarios (puedes seguir ampliando)
ALEGRIA = {
    "feliz","contento","contenta","alegre","entusiasmado","entusiasmada","emocionado","emocionada",
    "bien","genial","excelente","maravilloso","fantastico","fantástica","fantástico","increible",
    "agradecido","agradecida","satisfecho","satisfecha","optimista","motivado","motivada"
}
ENOJO = {
    "enojado","enojada","furioso","furiosa","molesto","molesta","irritado","irritada","fastidiado",
    "fastidiada","indignado","indignada","rabia","enojo","colera","cólera","odio"
}
TRISTEZA = {
    "triste","deprimido","deprimida","melancolico","melancólica","decaido","decaída","apagado","apagada",
    "desanimado","desanimada","llorando","llanto","pena","nostalgia"
}
MIEDO = {
    "miedo","temor","asustado","asustada","ansioso","ansiosa","nervioso","nerviosa","preocupado","preocupada",
    "panico","pánico","inseguro","insegura"
}
ASCO = {
    "asco","repugnante","asqueroso","asquerosa","desagradable","me-da-asco","guacala","guácala","vomitivo","repulsivo"
}
SORPRESA = {
    "sorprendido","sorprendida","impresionado","impresionada","asombrado","asombrada","wow","vaya"
}

CATEGORIAS = {
    "alegria": ALEGRIA,
    "enojo": ENOJO,
    "tristeza": TRISTEZA,
    "miedo": MIEDO,
    "asco": ASCO,
    "sorpresa": SORPRESA,
}

def normalize_es(text: str) -> str:
    t = unicodedata.normalize("NFKD", text).encode("ascii","ignore").decode("ascii")
    t = t.lower()
    t = re.sub(r"[^a-z0-9\s\!\?\.\,]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def tokenize(text: str) -> List[str]:
    return text.split()

def emoji_score(raw: str) -> int:
    pos = sum(1 for ch in raw if ch in EMOJI_POS)
    neg = sum(1 for ch in raw if ch in EMOJI_NEG)
    return pos - neg

def window_has(tokens: List[str], index: int, vocab: set, w: int = 2) -> bool:
    i0 = max(0, index - w)
    i1 = min(len(tokens), index + w + 1)
    return any(tok in vocab for tok in tokens[i0:i1])

def sentiment_analyze(raw_text: str):
    # 1) Normaliza y tokeniza
    norm = normalize_es(raw_text)
    tokens = tokenize(norm)

    # 2) Conteo por categoría
    cat_counts = {k: 0 for k in CATEGORIAS.keys()}
    base_score = 0

    for idx, tok in enumerate(tokens):
        for cat, vocab in CATEGORIAS.items():
            if tok in vocab:
                # peso base
                weight = 1
                # intensificadores/atenuadores cercanos
                if window_has(tokens, idx, INTENSIFICADORES, 2): weight += 1
                if window_has(tokens, idx, ATENUADORES, 2):      weight -= 0.5
                # negación cercana invierte
                negated = window_has(tokens, idx, NEGADORES, 2)

                # asigna signo por polaridad de la categoría
                polarity = 0
                if cat == "alegria":
                    polarity = 1
                elif cat in {"enojo","tristeza","miedo","asco"}:
                    polarity = -1
                elif cat == "sorpresa":
                    polarity = 0.3  # sorpresa leve positiva por defecto

                val = polarity * weight
                if negated:
                    val = -val  # invierte

                cat_counts[cat] += weight if polarity >= 0 else weight  # para estadística simple
                base_score += val

    # 3) Emojis (a partir del texto original, no normalizado)
    e_score = emoji_score(raw_text)
    base_score += e_score * 0.8  # emojis pesan, pero menos que palabras

    # 4) Clamp & color
    # score final aproximado entre -5 y +5; normalizamos a -1..+1
    score_raw = max(-5.0, min(5.0, base_score))
    score = round(score_raw / 5.0, 3)

    if score > 0.15:
        label, color = "positivo", "#2ecc71"   # verde
    elif score < -0.15:
        label, color = "negativo", "#e74c3c"   # rojo
    else:
        label, color = "neutral",  "#f1c40f"   # amarillo

    return {
        "sentimiento": label,
        "score": score,           # -1..+1
        "color": color,           # hex
        "detalles": cat_counts,   # conteo bruto por categoría
        "tokens": tokens[:50],    # debug limitado
    }

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

