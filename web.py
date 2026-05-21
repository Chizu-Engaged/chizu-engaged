 # ============================================
# CHIZU: ENGAGED — web.py
# ============================================
import sys
import os
import random
import json
import re
import time
import psutil
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from collections import defaultdict
from cachetools import TTLCache
from core.language import obter_idioma_usuario, detectar_idioma_texto
from core.translator import traduzir

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

try:
    from core.ai_provider import FreeAIProvider
    from core.engine import (
        carregar_biblioteca, buscar_contexto, montar_prompt,
        AUTORES_DISPONIVEIS, TEMAS_DISPONIVEIS
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# ============================================
# Carregar traduções da interface
# ============================================
TRANSLATIONS_FILE = os.path.join(BASE_DIR, "data", "ui_translations.json")

try:
    with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
        UI_TRANSLATIONS = json.load(f)
    print(f"✅ Traduções carregadas: {list(UI_TRANSLATIONS.keys())}")
except FileNotFoundError:
    print(f"⚠️ Arquivo de traduções não encontrado. Usando apenas inglês.")
    UI_TRANSLATIONS = {"en": {}}
except json.JSONDecodeError as e:
    print(f"❌ Erro no JSON: {e}")
    UI_TRANSLATIONS = {"en": {}}

# ============================================
# Inicialização
# ============================================
app = FastAPI()
ai_provider = FreeAIProvider()
biblioteca_engaged = carregar_biblioteca()
conversation_memory = TTLCache(maxsize=200, ttl=3600)

MARCADORES_BLOQUEIO = ["BLOQUEADO", "VAZIO", "BLOCKED", "EMPTY"]
RATE_LIMIT = 10
JANELA_SEG = 60
_contadores: dict = defaultdict(list)

# ============================================
# Mensagens de espera padrão (inglês)
# ============================================
WAITING_JS = [
    "Listening to the teachings...",
    "Drawing from the sources...",
    "The wisdom surfaces...",
    "Breathing with the question...",
    "Turning the wheel of dharma...",
    "Cultivating right intention...",
    "Walking the path together...",
    "Mindfully attending...",
    "Interbeing reveals...",
    "Transforming suffering...",
    "Engaged practice awakens...",
    "Right view emerges...",
]

# -------------------------------------------------------------------
def is_mobile(request: Request) -> bool:
    ua = request.headers.get("user-agent", "").lower()
    keywords = ['mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone',
                'samsung', 'galaxy', 'nexus', 'xiaomi', 'redmi', 'oppo', 'vivo', 'huawei',
                'honor', 'realme', 'motorola', 'lg-', 'sony', 'xperia', 'htc', 'nokia']
    return any(k in ua for k in keywords)

def checar_rate_limit(ip: str) -> bool:
    agora = time.time()
    _contadores[ip] = [t for t in _contadores[ip] if agora - t < JANELA_SEG]
    if len(_contadores[ip]) >= RATE_LIMIT:
        return False
    _contadores[ip].append(agora)
    return True

PADROES_INJECTION = [
    r"###\s*\w+", r"system\s*prompt", r"ignore\s+(previous|all|above)",
    r"act as", r"jailbreak", r"forget\s+(everything|the rules)", r"from now on",
    r"pretend\s+that", r"no\s+(restrictions|limits|rules)", r"repeat\s+(the rules|the instructions)",
]

def sanitizar_pergunta(texto: str) -> str | None:
    texto = texto.strip()
    if len(texto) > 400: return None
    for padrao in PADROES_INJECTION:
        if re.search(padrao, texto, re.IGNORECASE): return None
    return texto

def resposta_bloqueio(idioma: str = "en") -> str:
    trad = UI_TRANSLATIONS.get(idioma, UI_TRANSLATIONS.get("en", {}))
    frases = trad.get("blocked_phrases", [
        "This question rests in silence.",
        "The teacher holds this in stillness.",
        "Some doors open only from the inside.",
        "Silence is also an answer."
    ])
    return random.choice(frases)

def is_bloqueado(texto: str) -> bool:
    t = texto.upper()
    return any(m.upper() in t for m in MARCADORES_BLOQUEIO)

def limpar_resposta(texto: str) -> str:
    return texto.replace("(Silence)", "").replace("(pause)", "").lstrip("#").strip()

def is_local(request: Request) -> bool:
    ip = request.client.host
    return ip in ("127.0.0.1", "::1") or ip.startswith("192.168.") or ip == "177.104.74.30"

# ============================================
# Arquivos estáticos
# ============================================
if os.path.exists(os.path.join(BASE_DIR, "static")):
    app.mount("/static", StaticFiles(directory="static"), name="static")
if os.path.exists(os.path.join(BASE_DIR, "legal")):
    app.mount("/legal", StaticFiles(directory="legal", html=True), name="legal")

# ============================================
# Geração de HTML (placeholders)
# ============================================
autores_html_desktop = "".join(f"""
    <div class="author-card" data-autor="{autor}">
        <div class="author-name">{autor}</div>
    </div>
""" for autor in AUTORES_DISPONIVEIS)

HTML_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chizu: Engaged · Engaged Buddhism & Simple Economics</title>
    <link rel="stylesheet" href="/static/style.css?v=1">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="icon" type="image/x-icon" href="/static/img/favicon.ico">
    <link rel="apple-touch-icon" sizes="180x180" href="/static/img/apple-touch-icon.png">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Mono:wght@300;400&display=swap" rel="stylesheet">
    <meta name="theme-color" content="#2c3a26">
</head>
<body>
<script>
    window.WAITING_JS = {waiting_js_json};
    window.TEMAS_DISPONIVEIS = {temas_json};
    window.AUTORES_DISPONIVEIS = {autores_json};
    window.UI_STRINGS = {ui_strings_json};
    window.TEMAS_TRADUZIDOS = {temas_traduzidos_json};
</script>
<div class="layout">
    <aside class="sidebar">
        <div class="sb-header">
            <div class="sb-logo">{{LOGO}}</div>
            <div class="sb-title">{{SIDEBAR_TITLE}}</div>
        </div>
        <button class="sb-new" onclick="novaConversa()">{{NEW_CONVERSATION}}</button>
        <div class="sb-section">{{HISTORY_LABEL}}</div>
        <div id="historico-lista"></div>
        <div class="sb-footer">
            <a href="/static/legal/how-it-works.html" class="sb-link">{{HOW_IT_WORKS}}</a>
            <a href="/static/legal/legal-notice.html" class="sb-link">{{LEGAL_NOTICE}}</a>
            <a href="/static/legal/copyright.html" class="sb-link">{{COPYRIGHT}}</a>
            <a href="https://chizu.ia.br" class="sb-link">{{CHIZU_LINK}}</a>
        </div>
    </aside>
    <main class="main">
        <div id="tela-temas" class="tela-temas">
            <div class="hero">
                <p class="kicker">{{KICKER}}</p>
                <h1 class="hero-title">{{HERO_TITLE}}</h1>
                <p class="chat-callout">{{CHAT_CALLOUT}}</p>
                <p class="hero-sub">{{HERO_SUB}}</p>
            </div>
            <p class="section-label">{{SECTION_THEME}}</p>
            <div class="temas-grid">
                <div class="tema-card selected" data-tema="" onclick="selecionarTema(this)">
                    <p class="tc-name">{{ALL_VOICES_TITLE}}</p>
                    <p class="tc-desc">{{ALL_VOICES_DESC}}</p>
                    <p class="tc-authors">Bernie Glassman · Charles Eisenstein · Thich Nhat Hanh · Joanna Macy · Satish Kumar · Helena Norberg-Hodge · Vicki Robin · Bhikkhu Bodhi · David Loy · Sulak Sivaraksa · Joan Halifax · E.F. Schumacher · Paul Fuller · Buddhist teachers</p>
                </div>
                <div class="tema-card" data-tema="Gift Economy" onclick="selecionarTema(this)">
                    <p class="tc-name">{{GIFT_ECONOMY_TITLE}}</p>
                    <p class="tc-desc">{{GIFT_ECONOMY_DESC}}</p>
                    <p class="tc-authors">Bernie Glassman · Charles Eisenstein · Schumacher</p>
                </div>
                <div class="tema-card" data-tema="Social Action" onclick="selecionarTema(this)">
                    <p class="tc-name">{{SOCIAL_ACTION_TITLE}}</p>
                    <p class="tc-desc">{{SOCIAL_ACTION_DESC}}</p>
                    <p class="tc-authors">Joanna Macy · Sulak Sivaraksa · Thich Nhat Hanh</p>
                </div>
                <div class="tema-card" data-tema="Simple Living" onclick="selecionarTema(this)">
                    <p class="tc-name">{{SIMPLE_LIVING_TITLE}}</p>
                    <p class="tc-desc">{{SIMPLE_LIVING_DESC}}</p>
                    <p class="tc-authors">Satish Kumar · Schumacher · Vicki Robin</p>
                </div>
                <div class="tema-card" data-tema="Local Futures" onclick="selecionarTema(this)">
                    <p class="tc-name">{{LOCAL_FUTURES_TITLE}}</p>
                    <p class="tc-desc">{{LOCAL_FUTURES_DESC}}</p>
                    <p class="tc-authors">Charles Eisenstein · Helena Norberg-Hodge · Satish Kumar</p>
                </div>
                <div class="tema-card" data-tema="Deep Ecology" onclick="selecionarTema(this)">
                    <p class="tc-name">{{DEEP_ECOLOGY_TITLE}}</p>
                    <p class="tc-desc">{{DEEP_ECOLOGY_DESC}}</p>
                    <p class="tc-authors">Joan Halifax · Joanna Macy · Satish Kumar</p>
                </div>
                <div class="tema-card" data-tema="The Bodhisattva Path" onclick="selecionarTema(this)">
                    <p class="tc-name">{{BODHISATTVA_TITLE}}</p>
                    <p class="tc-desc">{{BODHISATTVA_DESC}}</p>
                    <p class="tc-authors">Bhikkhu Bodhi · Buddhist teachers · David Loy · Paul Fuller</p>
                </div>
            </div>
            <div class="section-label">{{ALL_VOICES_SECTION}}</div>
            <div class="autores-grid" id="autores-grid-desktop">
                {autores_html_desktop}
            </div>
        </div>
        <div id="tela-chat" class="tela-chat" style="display:none;">
            <div class="chat-header">
                <div class="ch-left">
                    <span class="ch-theme" id="chat-tema-label">GIFT ECONOMY</span>
                    <span class="ch-voices" id="chat-vozes-label">Bernie Glassman · Charles Eisenstein · Schumacher</span>
                </div>
            </div>
            <div class="chat-messages" id="chat-messages">
                <div class="msg bot">
                    <div class="msg-bubble"><p>{{WELCOME_MSG}}</p></div>
                </div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="pergunta" placeholder="{{INPUT_PLACEHOLDER}}" autocomplete="off" spellcheck="false" maxlength="400">
                <select id="autor-select" title="{{FILTER_AUTHOR_TITLE}}">
                    <option value="">{{SELECT_ALL_VOICES}}</option>
                </select>
                <button id="btn-enviar" onclick="fazerPergunta()">→</button>
            </div>
        </div>
    </main>
</div>
<script src="/static/script.js?v=1"></script>
</body>
</html>"""

HTML_PAGE_MOBILE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>Chizu: Engaged · Mobile</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Mono:wght@300;400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/mobile.css?v=1">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link rel="icon" type="image/x-icon" href="/static/img/favicon.ico">
    <link rel="apple-touch-icon" sizes="180x180" href="/static/img/apple-touch-icon.png">
</head>
<body>
    <div class="mobile-header">
        <h1>{{HERO_TITLE}}</h1>
        <div class="sub">{{MOBILE_SUB}}</div>
    </div>
    <div class="section-title">{{MOBILE_THEMES_TITLE}}</div>
    <div id="theme-list" class="theme-list">
        <div class="theme-card" data-tema="">
            <div class="theme-name">{{ALL_VOICES_TITLE}}</div>
            <div class="theme-desc">{{MOBILE_ALL_VOICES_DESC}}</div>
        </div>
        {temas_html}
    </div>
    <div class="section-title">{{MOBILE_VOICES_TITLE}}</div>
    <div id="author-list" class="author-list">
        {autores_html}
    </div>
    <div class="mobile-footer">{{MOBILE_FOOTER}}</div>
    <script>
        window.WAITING_JS = {waiting_js_json};
        window.TEMAS_DISPONIVEIS = {temas_json};
        window.AUTORES_DISPONIVEIS = {autores_json};
        window.UI_STRINGS = {ui_strings_json};
        window.TEMAS_TRADUZIDOS = {temas_traduzidos_json};
    </script>
    <script src="/static/script-mobile.js?v=1"></script>
</body>
</html>"""

# ============================================
# Rotas
# ============================================
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    # Força espanhol para teste; troque por obter_idioma_usuario(request) depois
    # idioma = "fr" # ['en', 'pt', 'es', 'fr', 'de']
    idioma = obter_idioma_usuario(request)
    #print(f"🌐 Idioma detectado: {idioma}")
    trad = UI_TRANSLATIONS.get(idioma, UI_TRANSLATIONS.get("en", {}))

    temas_traduzidos = trad.get("themes", {})
    temas_traduzidos_json = json.dumps(temas_traduzidos, ensure_ascii=False)

    def aplicar_traducoes(template: str, t: dict) -> str:
        subs = {
            "{{LOGO}}": t.get("logo", "CHIZU: ENGAGED"),
            "{{SIDEBAR_TITLE}}": t.get("sidebar_title", "Conversations"),
            "{{NEW_CONVERSATION}}": t.get("new_conversation", "+ New conversation"),
            "{{HISTORY_LABEL}}": t.get("history_label", "HISTORY"),
            "{{HOW_IT_WORKS}}": t.get("how_it_works", "How it works<br>a digital guide"),
            "{{LEGAL_NOTICE}}": t.get("legal_notice", "Legal Notice"),
            "{{COPYRIGHT}}": t.get("copyright", "Copyright"),
            "{{CHIZU_LINK}}": t.get("chizu_link", "Chizu"),
            "{{KICKER}}": t.get("kicker", "AI Conversations · Guided by Engaged Masters"),
            "{{HERO_TITLE}}": t.get("hero_title", "Engaged Buddhism<br>&amp; <em>Simple Economics</em>"),
            "{{CHAT_CALLOUT}}": t.get("chat_callout", "Ask a question — get an answer woven from the wisdom of Bernard Glassman, Thich Nhat Hanh, Joanna Macy &amp; others."),
            "{{HERO_SUB}}": t.get("hero_sub", "Choose a theme or authors — the system selects the voices that speak to it most deeply."),
            "{{SECTION_THEME}}": t.get("section_theme", "CHOOSE A THEME TO BEGIN"),
            "{{ALL_VOICES_TITLE}}": t.get("all_voices_title", "All Voices"),
            "{{ALL_VOICES_DESC}}": t.get("all_voices_desc", "The full chorus — all authors, all themes. Let the wisdom speak freely."),
            "{{GIFT_ECONOMY_TITLE}}": t.get("gift_economy_title", "Gift Economy"),
            "{{GIFT_ECONOMY_DESC}}": t.get("gift_economy_desc", "Money, generosity and sacred exchange as spiritual practice."),
            "{{SOCIAL_ACTION_TITLE}}": t.get("social_action_title", "Social Action"),
            "{{SOCIAL_ACTION_DESC}}": t.get("social_action_desc", "Buddhism practiced beyond the cushion — in streets and councils."),
            "{{SIMPLE_LIVING_TITLE}}": t.get("simple_living_title", "Simple Living"),
            "{{SIMPLE_LIVING_DESC}}": t.get("simple_living_desc", "Voluntary simplicity as resistance and liberation."),
            "{{LOCAL_FUTURES_TITLE}}": t.get("local_futures_title", "Local Futures"),
            "{{LOCAL_FUTURES_DESC}}": t.get("local_futures_desc", "Rebuilding community, food systems and place-based economies."),
            "{{DEEP_ECOLOGY_TITLE}}": t.get("deep_ecology_title", "Deep Ecology"),
            "{{DEEP_ECOLOGY_DESC}}": t.get("deep_ecology_desc", "Earth as teacher — soil, soul and the sacred."),
            "{{BODHISATTVA_TITLE}}": t.get("bodhisattva_title", "The Bodhisattva Path"),
            "{{BODHISATTVA_DESC}}": t.get("bodhisattva_desc", "Compassion in action — the vow to liberate all beings."),
            "{{ALL_VOICES_SECTION}}": t.get("all_voices_section", "ALL VOICES"),
            "{{WELCOME_MSG}}": t.get("welcome_msg", "Ask anything about engaged Buddhism, gift economy, simple living or social action."),
            "{{INPUT_PLACEHOLDER}}": t.get("input_placeholder", "Ask the teachings..."),
            "{{FILTER_AUTHOR_TITLE}}": t.get("filter_author_title", "Filter by author"),
            "{{SELECT_ALL_VOICES}}": t.get("select_all_voices", "All voices"),
            "{{MOBILE_SUB}}": t.get("mobile_sub", "CHOOSE A THEME"),
            "{{MOBILE_THEMES_TITLE}}": t.get("mobile_themes_title", "Themes"),
            "{{MOBILE_VOICES_TITLE}}": t.get("mobile_voices_title", "Voices"),
            "{{MOBILE_FOOTER}}": t.get("mobile_footer", "Tap a theme or voice to start"),
            "{{MOBILE_ALL_VOICES_DESC}}": t.get("mobile_all_voices_desc", "All authors, all themes"),
        }
        for ph, val in subs.items():
            template = template.replace(ph, val)
        return template

    # UI_STRINGS para o front-end
    ui_strings = {
        "voice_prefix": trad.get("voice_prefix", "VOICE: "),
        "inspired_by_writings": trad.get("inspired_by_writings", "Answers inspired by their writings."),
        "welcome_prompt_general": trad.get("welcome_prompt_general", "What would you like to explore today?"),
        "welcome_prompt_all_voices": trad.get("welcome_prompt_all_voices", "Ask anything to the full chorus of engaged Buddhism & simple economics."),
        "welcome_prompt_theme": trad.get("welcome_prompt_theme", "Ask anything about {theme}"),
        "all_voices_label": trad.get("all_voices_label", "All Voices"),
        "select_all_voices": trad.get("select_all_voices", "All voices"),
    }
    ui_strings_json = json.dumps(ui_strings, ensure_ascii=False)

    waiting_js_traduzido = trad.get("waiting_msgs", WAITING_JS)
    waiting_json = json.dumps(waiting_js_traduzido, ensure_ascii=False)

    temas_json = json.dumps(TEMAS_DISPONIVEIS, ensure_ascii=False)
    autores_json = json.dumps(AUTORES_DISPONIVEIS, ensure_ascii=False)

    temas_html = "".join(f"""
    <div class="theme-card" data-tema="{tema}">
        <div class="theme-name">{tema}</div>
    </div>""" for tema in TEMAS_DISPONIVEIS)
    autores_html = "".join(f"""
    <div class="author-card" data-autor="{autor}">
        <div class="author-name">{autor}</div>
    </div>""" for autor in AUTORES_DISPONIVEIS)

    html_desktop = aplicar_traducoes(HTML_PAGE_TEMPLATE, trad)
    html_desktop = html_desktop.replace("{autores_html_desktop}", autores_html_desktop)
    html_desktop = html_desktop.replace("{waiting_js_json}", waiting_json)
    html_desktop = html_desktop.replace("{temas_json}", temas_json)
    html_desktop = html_desktop.replace("{autores_json}", autores_json)
    html_desktop = html_desktop.replace("{ui_strings_json}", ui_strings_json)
    html_desktop = html_desktop.replace("{temas_traduzidos_json}", temas_traduzidos_json)

    html_mobile = aplicar_traducoes(HTML_PAGE_MOBILE_TEMPLATE, trad)
    html_mobile = html_mobile.replace("{temas_html}", temas_html)
    html_mobile = html_mobile.replace("{autores_html}", autores_html)
    html_mobile = html_mobile.replace("{waiting_js_json}", waiting_json)
    html_mobile = html_mobile.replace("{temas_json}", temas_json)
    html_mobile = html_mobile.replace("{autores_json}", autores_json)
    html_mobile = html_mobile.replace("{ui_strings_json}", ui_strings_json)
    html_mobile = html_mobile.replace("{temas_traduzidos_json}", temas_traduzidos_json)

    if is_mobile(request):
        return HTMLResponse(content=html_mobile)
    else:
        return HTMLResponse(content=html_desktop)


@app.post("/ask")
async def ask(request: Request):
    start_time = time.time()
    DEBUG = is_local(request)
    ip = request.client.host

    if not checar_rate_limit(ip):
        return JSONResponse({"resposta": "Too many requests. Please wait a moment."}, status_code=429)

    try:
        data = await request.json()
        pergunta_raw = data.get("pergunta", "").strip()
        pergunta = sanitizar_pergunta(pergunta_raw)
        idioma_pergunta = detectar_idioma_texto(pergunta)

        if not pergunta:
            return JSONResponse({"resposta": resposta_bloqueio(idioma_pergunta)})

        pergunta_original = pergunta
        fonte_traducao = None
        if idioma_pergunta != "en":
            pergunta, _ = traduzir(pergunta, idioma_pergunta, "en")

        autor_raw = data.get("autor", None)
        autor_filtro = autor_raw if autor_raw in AUTORES_DISPONIVEIS else None
        tema_raw = data.get("tema", None)
        tema_filtro = tema_raw if tema_raw in TEMAS_DISPONIVEIS else None

        session_id = data.get("session_id", ip)
        historico_usuario = conversation_memory.get(session_id, [])

        provider_nome, provider_cfg = ai_provider.sortear_provider()
        top_k = provider_cfg.get("top_k", 4)

        contexto = buscar_contexto(pergunta, biblioteca_engaged, top_k=top_k,
                                   autor_filtro=autor_filtro, tema_filtro=tema_filtro)

        mensagens_base, perfil_nome, autor_principal = montar_prompt(
            pergunta, contexto, autor_filtro=autor_filtro, tema_filtro=tema_filtro
        )

        if historico_usuario:
            msgs_hist = []
            for troca in historico_usuario[-3:]:
                msgs_hist.append({"role": "user", "content": troca["pergunta"]})
                msgs_hist.append({"role": "assistant", "content": troca["resposta"]})
            prompt_completo = [mensagens_base[0]] + msgs_hist + [mensagens_base[-1]]
        else:
            prompt_completo = [mensagens_base[0], mensagens_base[-1]]

        resposta_raw, ia_nome = ai_provider.chat(prompt_completo, provider_nome=provider_nome)
        resposta_limpa = limpar_resposta(resposta_raw)

        if is_bloqueado(resposta_limpa):
            return JSONResponse({"resposta": resposta_bloqueio(idioma_pergunta)})

        if idioma_pergunta != "en":
            resposta_limpa, fonte_traducao = traduzir(resposta_limpa, de="en", para=idioma_pergunta)

        if DEBUG:
            elapsed_total = time.time() - start_time
            process = psutil.Process(os.getpid())
            mem_rss = process.memory_info().rss / 1024 / 1024
            mem_percent = process.memory_percent()
            cpu_percent = process.cpu_percent(interval=None)
            threads = process.num_threads()

            if autor_filtro:
                tipo_perfil = "Autor"
                autor_info = f" → selecionado: {autor_filtro}"
            elif tema_filtro:
                tipo_perfil = "Tema"
                autor_info = f" → autor usado: {autor_principal}" if autor_principal else ""
            elif perfil_nome == "Engaged Buddhism" and not tema_filtro and not autor_filtro:
                tipo_perfil = "Tema"
                autor_info = f" → autores encontrados: {autor_principal}" if autor_principal else ""
            else:
                tipo_perfil = "Perfil"
                autor_info = ""

            print("\n" + "=" * 60)
            print(f"Idioma          : {idioma_pergunta} - Texto: {pergunta_original[:80]}")
            print(f"IA              : {ia_nome}")
            print(f"tipo_perfil     : {tipo_perfil}")
            print(f"perfil_nome     : {perfil_nome}{autor_info}")
            print("-" * 60)
            print(f"QUESTION        : {pergunta}")
            print(f"CONTEXTO (120c) : {contexto[:120]}...")
            print("-" * 60)
            print(f"MEMÓRIA (RAM)   : {round(mem_rss, 2)} MB ({round(mem_percent, 2)}% do sistema)")
            print(f"CPU / THREADS   : {cpu_percent}% de uso | {threads} threads ativas")
            print(f"SESSÕES ATIVAS  : {len(conversation_memory)}")
            print(f"IPS MONITORADOS : {len(_contadores)}")
            print(f"TEMPO TOTAL     : {elapsed_total:.2f} segundos")
            print("=" * 60 + "\n")

        if session_id not in conversation_memory:
            conversation_memory[session_id] = []
        conversation_memory[session_id].append({
            "pergunta": pergunta[:150],
            "resposta": resposta_limpa[:200]
        })

        traducao_info = f" · {fonte_traducao}" if fonte_traducao else ""
        resposta_exibida = f"{resposta_limpa}\n\n— via {perfil_nome} · {ia_nome}{traducao_info}"
        return JSONResponse({"resposta": resposta_exibida})

    except Exception as e:
        print(f"❌ Error: {e}")
        return JSONResponse({"resposta": resposta_bloqueio()}, status_code=500)