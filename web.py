#
# web.py
#
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

# Configurar o path ANTES de importar módulos locais
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

# Agora sim, importar do core.engine e core.ai_provider
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
# Inicialização
# ============================================
app = FastAPI()
ai_provider         = FreeAIProvider()
biblioteca_engaged  = carregar_biblioteca()
conversation_memory = TTLCache(maxsize=200, ttl=3600)

MARCADORES_BLOQUEIO = ["BLOQUEADO", "VAZIO", "BLOCKED", "EMPTY"]

RATE_LIMIT = 10
JANELA_SEG = 60
_contadores: dict = defaultdict(list)
#-------------------------------------------------------------------
def is_mobile(request: Request) -> bool:
    user_agent = request.headers.get("user-agent", "").lower()
    mobile_keywords = [
        'mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone',
        'samsung', 'sm-', 'galaxy', 'nexus', 'xiaomi', 'mi ', 'redmi',
        'oppo', 'vivo', 'huawei', 'honor', 'realme', 'motorola', 'moto',
        'lg-', 'lge', 'sony', 'xperia', 'htc', 'nokia'
    ]
    return any(keyword in user_agent for keyword in mobile_keywords)
#-------------------------------------------------------------------

def checar_rate_limit(ip: str) -> bool:
    agora = time.time()
    _contadores[ip] = [t for t in _contadores[ip] if agora - t < JANELA_SEG]
    if len(_contadores[ip]) >= RATE_LIMIT:
        return False
    _contadores[ip].append(agora)
    return True


PADROES_INJECTION = [
    r"###\s*\w+",
    r"system\s*prompt",
    r"ignore\s+(previous|all|above)",
    r"act as",
    r"jailbreak",
    r"forget\s+(everything|the rules)",
    r"from now on",
    r"pretend\s+that",
    r"no\s+(restrictions|limits|rules)",
    r"repeat\s+(the rules|the instructions)",
]


def sanitizar_pergunta(texto: str) -> str | None:
    texto = texto.strip()
    if len(texto) > 400:
        return None
    for padrao in PADROES_INJECTION:
        if re.search(padrao, texto, re.IGNORECASE):
            return None
    return texto


FRASES_BLOQUEIO = [
    "This question rests in silence.",
    "The teacher holds this in stillness.",
    "Some doors open only from the inside.",
    "Silence is also an answer.",
]


def resposta_bloqueio() -> str:
    return random.choice(FRASES_BLOQUEIO)


def is_bloqueado(texto: str) -> bool:
    t = texto.upper()
    return any(m.upper() in t for m in MARCADORES_BLOQUEIO)


def limpar_resposta(texto: str) -> str:
    return texto.replace("(Silence)", "").replace("(pause)", "").lstrip("#").strip()


# def is_local(request: Request) -> bool:
#     host = request.headers.get("host", "")
#     return host.startswith("localhost") or host.startswith("127.0.0.1") or host.startswith("192.168.") or host.startswith("177.104.74.30")

def is_local(request: Request) -> bool:
    # 1. Pega o IP real de quem está se conectando à API
    client_ip = request.client.host

    # 2. Verifica se o IP de origem é local ou o seu IP externo fixo
    return (
        client_ip in ("127.0.0.1", "::1") or 
        client_ip.startswith("192.168.") or 
        client_ip == "177.104.74.30"
    )

# ============================================
# Arquivos Estáticos
# ============================================
if os.path.exists(os.path.join(BASE_DIR, "static")):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if os.path.exists(os.path.join(BASE_DIR, "legal")):
    app.mount("/legal", StaticFiles(directory="legal", html=True), name="legal")


# ============================================
# Textos da Interface
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


# Gera os cards de autores para desktop
autores_html_desktop = ""
for autor in AUTORES_DISPONIVEIS:
    autores_html_desktop += f"""
    <div class="author-card" data-autor="{autor}">
        <div class="author-name">{autor}</div>
    </div>
    """

# ============================================
# HTML
# ============================================
HTML_PAGE = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chizu: Engaged · Engaged Buddhism & Simple Economics</title>
    <link rel="stylesheet" href="/static/style.css?v=2">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Mono:wght@300;400&display=swap" rel="stylesheet">
    <link rel="icon" type="image/x-icon" href="/static/img/favicon.ico">
    <link rel="apple-touch-icon" sizes="180x180" href="/static/img/apple-touch-icon.png">
    <meta name="theme-color" content="#2c3a26">
</head>
<body>
<div class="layout">

    <!-- SIDEBAR -->
    <aside class="sidebar">
        <div class="sb-header">
            <div class="sb-logo">CHIZU: ENGAGED</div>
            <div class="sb-title">Conversations</div>
        </div>
        <button class="sb-new" onclick="novaConversa()">+ New conversation</button>
        <div class="sb-section">HISTORY</div>
        <div id="historico-lista"></div>
        <div class="sb-footer">
            <a href="/static/legal/how-it-works.html" class="sb-link">How it works<br>a digital guide</a>
            <a href="/static/legal/legal-notice.html" class="sb-link">Legal Notice</a>
            <a href="/static/legal/copyright.html" class="sb-link">Copyright</a>
            <a href="https://chizu.ia.br" class="sb-link">Chizu</a>            
        </div>
    </aside>

    <!-- MAIN -->
    <main class="main">

        <!-- TELA DE TEMAS -->
        <div id="tela-temas" class="tela-temas">
            <div class="hero">
                <p class="kicker">AI Conversations · Guided by Engaged Masters</p>
                <h1 class="hero-title">Engaged Buddhism<br>&amp; <em>Simple Economics</em></h1>
                <p class="chat-callout">Ask a question — get an answer woven from the wisdom of Bernard Glassman, Thich Nhat Hanh, Joanna Macy &amp; others.</p>                
                <p class="hero-sub">Choose a theme or authors — the system selects the voices that speak to it most deeply.</p>
            </div>

            <p class="section-label">CHOOSE A THEME TO BEGIN</p>


            <div class="temas-grid">
                <div class="tema-card selected" data-tema="" onclick="selecionarTema(this)">
                    <p class="tc-name">All Voices</p>
                    <p class="tc-desc">The full chorus — all authors, all themes. Let the wisdom speak freely.</p>
                    <p class="tc-authors">Bernie Glassman · Charles Eisenstein · Thich Nhat Hanh · Joanna Macy · Satish Kumar · Helena Norberg-Hodge · Vicki Robin · Bhikkhu Bodhi · David Loy · Sulak Sivaraksa · Joan Halifax · E.F. Schumacher · Paul Fuller · Buddhist teachers</p>
                </div>
                <div class="tema-card" data-tema="Gift Economy" onclick="selecionarTema(this)">
                    <p class="tc-name">Gift Economy</p>
                    <p class="tc-desc">Money, generosity and sacred exchange as spiritual practice.</p>
                    <p class="tc-authors">Bernie Glassman · Charles Eisenstein · Schumacher</p>
                </div>
                <div class="tema-card" data-tema="Social Action" onclick="selecionarTema(this)">
                    <p class="tc-name">Social Action</p>
                    <p class="tc-desc">Buddhism practiced beyond the cushion — in streets and councils.</p>
                    <p class="tc-authors">Joanna Macy · Sulak Sivaraksa · Thich Nhat Hanh</p>
                </div>
                <div class="tema-card" data-tema="Simple Living" onclick="selecionarTema(this)">
                    <p class="tc-name">Simple Living</p>
                    <p class="tc-desc">Voluntary simplicity as resistance and liberation.</p>
                    <p class="tc-authors">Satish Kumar · Schumacher · Vicki Robin</p>
                </div>
                <div class="tema-card" data-tema="Local Futures" onclick="selecionarTema(this)">
                    <p class="tc-name">Local Futures</p>
                    <p class="tc-desc">Rebuilding community, food systems and place-based economies.</p>
                    <p class="tc-authors">Charles Eisenstein · Helena Norberg-Hodge · Satish Kumar</p>
                </div>
                <div class="tema-card" data-tema="Deep Ecology" onclick="selecionarTema(this)">
                    <p class="tc-name">Deep Ecology</p>
                    <p class="tc-desc">Earth as teacher — soil, soul and the sacred.</p>
                    <p class="tc-authors">Joan Halifax · Joanna Macy · Satish Kumar</p>
                </div>
                <div class="tema-card" data-tema="The Bodhisattva Path" onclick="selecionarTema(this)">
                    <p class="tc-name">The Bodhisattva Path</p>
                    <p class="tc-desc">Compassion in action — the vow to liberate all beings.</p>
                    <p class="tc-authors">Bhikkhu Bodhi · Buddhist teachers · David Loy · Paul Fuller</p>
                </div>
            </div>

            <p class="section-label"></p>

            <div class="section-label">ALL VOICES</div>
            <div class="autores-grid" id="autores-grid-desktop">
                {autores_html_desktop}
            </div>

        </div>

        <!-- TELA DE CHAT -->
        <div id="tela-chat" class="tela-chat" style="display:none;">
            <div class="chat-header">
                <div class="ch-left">
                    <span class="ch-theme" id="chat-tema-label">GIFT ECONOMY</span>
                    <span class="ch-voices" id="chat-vozes-label">Bernie Glassman · Charles Eisenstein · Schumacher</span>
                </div>

            </div>

            <div class="chat-messages" id="chat-messages">
                <div class="msg bot">
                    <div class="msg-bubble">
                        <p>Ask anything about engaged Buddhism, gift economy, simple living or social action.</p>
                    </div>
                </div>
            </div>

            <div class="chat-input-area">
                <input type="text" id="pergunta"
                    placeholder="Ask the teachings..."
                    autocomplete="off" spellcheck="false" maxlength="400">
                <select id="autor-select" title="Filter by author">
                    <option value="">All voices</option>
                </select>                    
                <button id="btn-enviar" onclick="fazerPergunta()">→</button>
            </div>
        </div>

    </main>
</div>

<script>
    window.WAITING_JS  = {json.dumps(WAITING_JS)};
    window.TEMAS_DISPONIVEIS = {json.dumps(TEMAS_DISPONIVEIS)};
    window.AUTORES_DISPONIVEIS = {json.dumps(AUTORES_DISPONIVEIS)};
</script>
<script src="/static/script.js?v=2"></script>
</body>
</html>
"""
#-------------------------------------------------------------------
# Gera os cards de temas dinamicamente
temas_html = ""
for tema, autores in TEMAS_DISPONIVEIS.items():
    autores_str = " · ".join(autores)
    temas_html += f"""
    <div class="theme-card" data-tema="{tema}">
        <div class="theme-name">{tema}</div>
    </div>
    """
# Gera os cards de autores (vozes) individualmente
autores_html = ""
for autor in AUTORES_DISPONIVEIS:
    autores_html += f"""
    <div class="author-card" data-autor="{autor}">
        <div class="author-name">{autor}</div>
    </div>
    """
HTML_PAGE_MOBILE = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>Chizu: Engaged · Mobile</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Mono:wght@300;400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/mobile.css?v=2">
    <link rel="icon" type="image/x-icon" href="/static/img/favicon.ico">
    <link rel="apple-touch-icon" sizes="180x180" href="/static/img/apple-touch-icon.png">    
</head>
<body>
    <div class="mobile-header">
        <h1>Engaged Buddhism<br>&amp; <em>Simple Economics</em></h1>
        <div class="sub">CHOOSE A THEME</div>
    </div>

    <!-- Seção de temas -->
    <div class="section-title">Themes</div>
    <div id="theme-list" class="theme-list">
        <!-- Card All Voices (tema vazio) -->
        <div class="theme-card" data-tema="" onclick="selecionarTemaMobile(this)">
            <div class="theme-name">All Voices</div>
            <div class="theme-desc">All authors, all themes</div>
        </div>
        {temas_html}
    </div>

    <!-- Seção de autores (vozes) -->
    <div class="section-title">Voices</div>
    <div id="author-list" class="author-list">
        {autores_html}
    </div>

    <div class="mobile-footer">Tap a theme or voice to start</div>
    <script src="/static/script-mobile.js?v=2"></script>
</body>
</html>"""

#-------------------------------------------------------------------

# ============================================
# Rotas
# ============================================
#-------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    if is_mobile(request):
        return HTMLResponse(content=HTML_PAGE_MOBILE)
    else:
        return HTMLResponse(content=HTML_PAGE)
#-------------------------------------------------------------------



@app.head("/")
async def head_index():
    return Response(status_code=200)


@app.post("/ask")
async def ask(request: Request):
    DEBUG = is_local(request)
    ip    = request.client.host

    if not checar_rate_limit(ip):
        return JSONResponse(
            {"resposta": "Too many requests. Please wait a moment."},
            status_code=429
        )

    try:
        data         = await request.json()
        pergunta_raw = data.get("pergunta", "").strip()
        pergunta     = sanitizar_pergunta(pergunta_raw)

        if not pergunta:
            return JSONResponse({"resposta": resposta_bloqueio()})

        autor_raw    = data.get("autor", None)
        autor_filtro = autor_raw if autor_raw in AUTORES_DISPONIVEIS else None

        tema_raw    = data.get("tema", None)
        tema_filtro = tema_raw if tema_raw in TEMAS_DISPONIVEIS else None

        session_id        = data.get("session_id", ip)
        historico_usuario = conversation_memory.get(session_id, [])

        provider_nome, provider_cfg = ai_provider.sortear_provider()
        top_k = provider_cfg.get("top_k", 4)

        contexto = buscar_contexto(
            pergunta, biblioteca_engaged,
            top_k=top_k,
            autor_filtro=autor_filtro,
            tema_filtro=tema_filtro
        )

        mensagens_base, perfil_nome, autor_principal = montar_prompt(
            pergunta, contexto,
            autor_filtro=autor_filtro,
            tema_filtro=tema_filtro
        )

        if historico_usuario:
            msgs_hist = []
            for troca in historico_usuario[-3:]:
                msgs_hist.append({"role": "user",      "content": troca["pergunta"]})
                msgs_hist.append({"role": "assistant", "content": troca["resposta"]})
            prompt_completo = [mensagens_base[0]] + msgs_hist + [mensagens_base[-1]]
        else:
            prompt_completo = [mensagens_base[0], mensagens_base[-1]]

        resposta_raw, ia_nome = ai_provider.chat(prompt_completo, provider_nome=provider_nome)
        resposta_limpa        = limpar_resposta(resposta_raw)


        if DEBUG:
            process = psutil.Process(os.getpid())
            
            # Memória
            mem_rss = process.memory_info().rss / 1024 / 1024
            mem_percent = process.memory_percent()
            
            # CPU e Threads (interval=None não trava a requisição assíncrona)
            cpu_percent = process.cpu_percent(interval=None) 
            threads = process.num_threads()

            # Define o tipo do perfil
            if autor_filtro:
                tipo_perfil = "Autor"
                autor_info = f" → selecionado: {autor_filtro}"
            elif tema_filtro:
                tipo_perfil = "Tema"
                autor_info = f" → autor usado: {autor_principal}" if autor_principal else ""
            elif perfil_nome == "Engaged Buddhism" and not tema_filtro and not autor_filtro:
                # Caso especial: All Voices (tema vazio)
                tipo_perfil = "Tema"
                perfil_nome_exibicao = "All Voices"
                autor_info = f" → autores encontrados: {autor_principal}" if autor_principal else ""
            else:
                tipo_perfil = "Perfil"
                autor_info = ""
                perfil_nome_exibicao = perfil_nome

            print("\n" + "=" * 60)

            print(f"IA              : {ia_nome}  ")    
            print(f"tipo_perfil     : {tipo_perfil}  ")
            print(f"perfil_nome     : {perfil_nome}{autor_info}")

            print("-" * 60)
            print(f"MEMÓRIA (RAM)   : {round(mem_rss, 2)} MB ({round(mem_percent, 2)}% do sistema)")
            print(f"CPU / THREADS   : {cpu_percent}% de uso | {threads} threads ativas")
            print(f"SESSÕES ATIVAS  : {len(conversation_memory)}")
            print(f"IPS MONITORADOS : {len(_contadores)}")
            print("-" * 60)
            print(f"QUESTION        : {pergunta}")
            print(f"CONTEXTO (120c) : {contexto[:120]}...")
            print("=" * 60 + "\n")

        if is_bloqueado(resposta_limpa):
            return JSONResponse({"resposta": resposta_bloqueio()})

        # Memória de sessão
        if session_id not in conversation_memory:
            conversation_memory[session_id] = []
        conversation_memory[session_id].append({
            "pergunta": pergunta[:150],
            "resposta": resposta_limpa[:200]
        })

        resposta_exibida = f"{resposta_limpa}\n\n— via {perfil_nome} · {ia_nome}"
        return JSONResponse({"resposta": resposta_exibida})

    except Exception as e:
        print(f"❌ Error: {e}")
        return JSONResponse({"resposta": resposta_bloqueio()}, status_code=500)