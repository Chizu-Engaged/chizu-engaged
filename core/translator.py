# core/translator.py
import os
import requests
from functools import lru_cache

# ============================================
# Serviço DeepL (primeira prioridade)
# ============================================
def _deepl(texto, de, para):
    api_key = os.getenv("DEEPL_API_KEY")
    # if not api_key:
    #     print("[DeepL] Chave não configurada")
    #     return None

    de_upper = de.upper()
    para_upper = para.upper()

    url = "https://api-free.deepl.com/v2/translate"
    headers = {
        "Authorization": f"DeepL-Auth-Key {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": [texto],
        "source_lang": de_upper,
        "target_lang": para_upper
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            resultado = r.json()["translations"][0]["text"]
            # print(f"[DeepL] OK - {len(texto)} caracteres -> {len(resultado)}")
            return resultado
        # else:
        #     print(f"[DeepL] Erro HTTP {r.status_code}: {r.text[:200]}")
        #     return None
    except Exception as e:
        print(f"[DeepL] Exceção: {e}")
        return None
        
# ============================================
# Serviço MyMemory (fallback gratuito)
# ============================================
def _mymemory(texto, de, para):
    """MyMemory com texto completo (até 5000 caracteres) e e-mail para maior limite."""
    url = "https://api.mymemory.translated.net/get"
    params = {
        "q": texto,  # sem fatiamento – envia o texto integral
        "langpair": f"{de}|{para}",
        "de": "chizu.engaged@outlook.com"   # e-mail válido para aumentar limites
    }
    try:
        r = requests.get(url, params=params, timeout=10)  # timeout um pouco maior
        data = r.json()
        traduzido = data["responseData"]["translatedText"]
        if "MYMEMORY WARNING" in traduzido or "YOU USED ALL AVAILABLE FREE TRANSLATIONS" in traduzido:
            print("[MyMemory] Aviso de limite excedido ou restrição")
            return None
        # MyMemory às vezes retorna o próprio texto quando não consegue traduzir
        if traduzido == texto:
            print("[MyMemory] Tradução vazia ou igual ao original")
            return None
        return traduzido
    except Exception as e:
        print(f"[MyMemory] Exceção: {e}")
        return None
# ============================================
# Serviço Lingva Translate (segundo fallback)
# ============================================
def _lingva(texto, de, para):
    """Lingva Translate — gratuito, sem key, usa GET com texto na URL."""
    try:
        from urllib.parse import quote
        texto_encoded = quote(texto[:500])  # também limitado a 500 caracteres
        url = f"https://lingva.ml/api/v1/{de}/{para}/{texto_encoded}"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            traduzido = data.get("translation", "")
            if traduzido:
                print(f"[Lingva] OK - {len(texto)} -> {len(traduzido)}")
                return traduzido
        print(f"[Lingva] Erro HTTP {r.status_code}")
        return None
    except Exception as e:
        print(f"[Lingva] Exceção: {e}")
        return None

# ============================================
# Pool principal com cache
# ============================================
@lru_cache(maxsize=200)
def traduzir(texto: str, de: str, para: str):
    """
    Traduz usando DeepL → MyMemory → Lingva.
    Retorna (texto_traduzido, fonte) onde fonte é None se não houve tradução.
    """

    # print("\n" + "=" * 60)    

    if de == para or not texto.strip():
        print(f"[Traduzir] Mesmo idioma ou texto vazio. Retornando original.")
        return texto, None

    # print(f"\n[Traduzir] Iniciando tradução: {len(texto)} caracteres, {de} -> {para}")
    # print(f"  Texto: {texto[:100]}{'...' if len(texto)>100 else ''}")

    # Tenta DeepL (melhor qualidade)
    resultado = _deepl(texto, de, para)
    if resultado:
        return resultado, "DeepL"

    # Fallback: MyMemory
    resultado = _mymemory(texto, de, para)
    if resultado:
        return resultado, "MyMemory"

    # Fallback: Lingva Translate
    resultado = _lingva(texto, de, para)
    if resultado:
        return resultado, "Lingva"

    # Último recurso: texto original sem tradução
    # print("[Traduzir] Nenhum serviço disponível. Retornando original.")
    return texto, None