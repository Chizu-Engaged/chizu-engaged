# core/translator.py
import requests

def traduzir(texto: str, de: str, para: str) -> str:
    """
    Traduz um texto usando MyMemory.
    Parâmetros:
        texto: str
        de: código do idioma de origem (ex: 'pt', 'en', 'fr', 'de')
        para: código do idioma de destino
    Retorna o texto original em caso de falha.
    """
    if not texto.strip() or de == para:
        return texto

    try:
        url = "https://api.mymemory.translated.net/get"
        params = {
            "q": texto[:500],  # limite seguro
            "langpair": f"{de}|{para}"
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        traduzido = data["responseData"]["translatedText"]
        return traduzido
    except Exception as e:
        print(f"⚠️ Erro na tradução: {e}")
        return texto