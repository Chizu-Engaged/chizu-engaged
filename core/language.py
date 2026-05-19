# core/language.py
import requests
from langdetect import detect, LangDetectException

LINGUAS_SUPORTADAS = ["pt", "en", "fr", "de"]

def idioma_por_accept_language(accept_header: str) -> str | None:
    """Extrai o primeiro idioma válido do Accept-Language (ex: 'pt-BR,pt;q=0.9,en;q=0.8')"""
    if not accept_header:
        return None
    primeiro = accept_header.split(",")[0].split(";")[0].strip()
    codigo = primeiro.split("-")[0].lower()
    return codigo if codigo in LINGUAS_SUPORTADAS else None

def idioma_por_ip(ip: str) -> str:
    """Consulta ip-api.com para obter o código do país e mapeia para idioma."""
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
        data = r.json()
        if data["status"] == "success":
            pais = data["countryCode"]  # BR, US, FR, DE, etc.
            mapa = {"BR": "pt", "US": "en", "GB": "en", "FR": "fr", "DE": "de"}
            return mapa.get(pais, "en")
    except Exception:
        pass
    return "en"  # fallback

def obter_idioma_usuario(request) -> str:
    """Função principal: tenta Accept-Language, depois IP, depois inglês."""
    accept = request.headers.get("Accept-Language")
    idioma = idioma_por_accept_language(accept)
    if idioma:
        return idioma
    # Fallback por IP (usa o IP do cliente)
    cliente_ip = request.client.host
    return idioma_por_ip(cliente_ip)

def detectar_idioma_texto(texto: str) -> str:
    try:
        from langdetect import detect
        return detect(texto)
    except Exception:
        return "en"


