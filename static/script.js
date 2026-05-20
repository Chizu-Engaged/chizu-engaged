// ============================================
// CHIZU: ENGAGED — /static/script.js
// ============================================

const SESSION_ID = Math.random().toString(36).slice(2) + Date.now();

let temaAtivo  = "Gift Economy";
let historico  = [];
let idxAtivo   = 0;
const TEMAS    = window.TEMAS_DISPONIVEIS || {};

function atualizarSelectAutores(tema) {
    const select = document.getElementById('autor-select');
    if (!select) return;
    let autores = [];
    if (tema === "") {
        autores = window.AUTORES_DISPONIVEIS || [];
    } else {
        autores = (window.TEMAS_DISPONIVEIS && window.TEMAS_DISPONIVEIS[tema]) || [];
    }
    const allVoicesText = (window.UI_STRINGS && window.UI_STRINGS.select_all_voices) || "All voices";
    select.innerHTML = `<option value="">${allVoicesText}</option>` +
        autores.map(a => `<option value="${a}">${a}</option>`).join('');
}

function selecionarTema(el) {
    document.querySelectorAll('.tema-card').forEach(c => c.classList.remove('selected'));
    el.classList.add('selected');
    temaAtivo = el.dataset.tema;
    iniciarConversa();
}

function iniciarConversa() {
    document.getElementById('tela-temas').style.display = 'none';
    document.getElementById('tela-chat').style.display  = 'flex';

    const ui = window.UI_STRINGS || {};
    const allVoicesLabel = ui.all_voices_label || "All Voices";
    const welcomeAll = ui.welcome_prompt_all_voices || "Ask anything to the full chorus of engaged Buddhism & simple economics.";
    const welcomeGeneral = ui.welcome_prompt_general || "What would you like to explore today?";

    if (temaAtivo === "") {
        document.getElementById('chat-tema-label').textContent = allVoicesLabel.toUpperCase();
        const todosAutores = window.AUTORES_DISPONIVEIS || [];
        document.getElementById('chat-vozes-label').textContent = todosAutores.join(' · ');
    } else {
        document.getElementById('chat-tema-label').textContent = temaAtivo.toUpperCase();
        document.getElementById('chat-vozes-label').textContent = (window.TEMAS_DISPONIVEIS[temaAtivo] || []).join(' · ');
    }

    document.getElementById('pergunta').focus();
    const msgs = document.getElementById('chat-messages');
    msgs.innerHTML = `<div class="msg bot"><div class="msg-bubble"><p>${temaAtivo === "" ? welcomeAll : welcomeGeneral}</p></div></div>`;

    adicionarHistorico(temaAtivo);
    setTimeout(() => atualizarSelectAutores(temaAtivo), 100);
}

function novaConversa() {
    document.getElementById('tela-temas').style.display = '';
    document.getElementById('tela-chat').style.display  = 'none';
    document.querySelectorAll('.tema-card').forEach(c => c.classList.remove('selected'));
    const hint = document.getElementById('start-hint');
    if (hint) hint.textContent = '';
    temaAtivo = 'Gift Economy';
}

function adicionarHistorico(tema) {
    let tituloExibido = tema;
    if (tema === "") tituloExibido = "All Voices";
    const ts = new Date().toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' });
    historico.unshift({ tema: tituloExibido, temaOriginal: tema, ts, mensagens: [] });
    if (historico.length > 10) historico.pop();
    idxAtivo = 0;
    renderHistorico();
}

function salvarMensagemHistorico(role, html) {
    if (historico.length > 0) {
        historico[idxAtivo].mensagens.push({ role, html });
    }
}

function renderHistorico() {
    const lista = document.getElementById('historico-lista');
    lista.innerHTML = historico.slice(0, 10).map((h, i) => `
        <div class="sb-item ${i === idxAtivo ? 'active' : ''}" onclick="abrirHistorico(${i})">
            <div class="sb-item-theme">${h.tema.toUpperCase()}</div>
            <div class="sb-item-date">${h.ts}</div>
        </div>
    `).join('');
}

function abrirHistorico(idx) {
    const h = historico[idx];
    if (!h) return;
    idxAtivo = idx;
    document.querySelectorAll('.sb-item').forEach((el, i) => {
        el.classList.toggle('active', i === idx);
    });

    if (h.temaOriginal !== undefined && h.temaOriginal === "") {
        temaAtivo = "";
    } else {
        temaAtivo = h.tema;
    }

    document.getElementById('tela-temas').style.display = 'none';
    document.getElementById('tela-chat').style.display = 'flex';

    const ui = window.UI_STRINGS || {};
    const allVoicesLabel = ui.all_voices_label || "All Voices";
    const welcomeAll = ui.welcome_prompt_all_voices || "Ask anything to the full chorus of engaged Buddhism & simple economics.";

    if (temaAtivo === "") {
        document.getElementById('chat-tema-label').textContent = allVoicesLabel.toUpperCase();
        const todosAutores = window.AUTORES_DISPONIVEIS || [];
        document.getElementById('chat-vozes-label').textContent = todosAutores.join(' · ');
    } else {
        document.getElementById('chat-tema-label').textContent = h.tema.toUpperCase();
        document.getElementById('chat-vozes-label').textContent = (window.TEMAS_DISPONIVEIS[h.tema] || []).join(' · ');
    }

    const msgs = document.getElementById('chat-messages');
    if (h.mensagens && h.mensagens.length > 0) {
        msgs.innerHTML = h.mensagens.map(m => `<div class="msg ${m.role}"><div class="msg-bubble"><p>${m.html}</p></div></div>`).join('');
    } else {
        if (temaAtivo === "") {
            msgs.innerHTML = `<div class="msg bot"><div class="msg-bubble"><p>${welcomeAll}</p></div></div>`;
        } else {
            const themeWelcome = (ui.welcome_prompt_theme || "Ask anything about {theme}").replace("{theme}", h.tema);
            msgs.innerHTML = `<div class="msg bot"><div class="msg-bubble"><p>${themeWelcome}</p></div></div>`;
        }
    }
    msgs.scrollTop = msgs.scrollHeight;
    document.getElementById('pergunta').focus();
    atualizarSelectAutores(temaAtivo);
}

let autorSelecionado = null;
function iniciarConversaAutor(autor) {
    autorSelecionado = autor;
    temaAtivo = "";
    document.getElementById('tela-temas').style.display = 'none';
    document.getElementById('tela-chat').style.display = 'flex';
    const ui = window.UI_STRINGS || {};
    const voicePrefix = ui.voice_prefix || "VOICE: ";
    const inspired = ui.inspired_by_writings || "Answers inspired by their writings.";
    const welcomeGeneral = ui.welcome_prompt_general || "What would you like to explore today?";
    document.getElementById('chat-tema-label').textContent = voicePrefix + autor.toUpperCase();
    document.getElementById('chat-vozes-label').innerHTML = `<span class="voice-note" style="font-size:0.85rem; opacity:0.7;">${inspired}</span>`;
    const select = document.getElementById('autor-select');
    if (select) select.style.display = 'none';
    document.getElementById('pergunta').focus();
    const msgs = document.getElementById('chat-messages');
    msgs.innerHTML = `<div class="msg bot"><div class="msg-bubble"><p>${welcomeGeneral}</p></div></div>`;
    adicionarHistorico("Voice: " + autor);
}

async function fazerPergunta() {
    const input = document.getElementById('pergunta');
    const textoRaw = input.value.trim();
    if (!textoRaw) return;

    const autorSelect = document.getElementById('autor-select');
    const autorFiltro = autorSelect ? autorSelect.value : '';

    adicionarMensagem('user', textoRaw);
    input.value = '';
    input.disabled = true;

    const msgs = document.getElementById('chat-messages');
    const waiting = document.createElement('div');
    waiting.className = 'msg bot waiting';
    waiting.innerHTML = '<div class="msg-bubble"><em>Listening to the teachings...</em></div>';
    msgs.appendChild(waiting);
    msgs.scrollTop = msgs.scrollHeight;

    const _wmsgs = [...(window.WAITING_JS || ['Consulting the teachings...'])];
    let _idx = 0;
    const _rot = setInterval(() => {
        _idx = (_idx + 1) % _wmsgs.length;
        if (waiting.querySelector('.msg-bubble')) {
            waiting.querySelector('.msg-bubble').innerHTML = `<em>${_wmsgs[_idx]}</em>`;
        }
    }, 2500);

    try {
        const payload = { pergunta: textoRaw, session_id: SESSION_ID, tema: temaAtivo };
        if (autorFiltro) payload.autor = autorFiltro;
        const r = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await r.json();
        clearInterval(_rot);
        waiting.remove();
        adicionarMensagem('bot', data.resposta);
    } catch (e) {
        clearInterval(_rot);
        waiting.remove();
        adicionarMensagem('bot', 'The silence holds this question for now.');
    } finally {
        input.disabled = false;
        input.focus();
    }
}

function adicionarMensagem(role, texto) {
    const msgs = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `msg ${role}`;
    const html = texto
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
    let bubbleContent = `<div class="msg-bubble"><p>${html}</p></div>`;
    if (role === 'bot') {
        const msgId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 6);
        div.id = msgId;
        bubbleContent = `
            <div style="display: flex; align-items: center; justify-content: flex-start; gap: 10px;">
                <div class="msg-bubble" style="flex: 1;"><p>${html}</p></div>
                <button class="share-wpp-btn" data-msg-id="${msgId}" title="Share this message on WhatsApp" aria-label="Share on WhatsApp" style="background: none; border: none; cursor: pointer; color: #6b7c5e; font-size: 1.2rem; transition: opacity 0.2s;">
                    <i class="fas fa-share-square"></i>
                </button>
            </div>
        `;
    }
    div.innerHTML = bubbleContent;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    if (role === 'user' || role === 'bot') salvarMensagemHistorico(role, html);

    if (role === 'bot') {
        const shareBtn = div.querySelector('.share-wpp-btn');
        if (shareBtn) {
            shareBtn.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
                const bubbleTextElem = div.querySelector('.msg-bubble p');
                let resposta = bubbleTextElem ? bubbleTextElem.innerText : '';
                const viaIndex = resposta.indexOf('— via');
                if (viaIndex !== -1) resposta = resposta.substring(0, viaIndex).trim();
                const intro = "地図 A wisdom from Chizu: Engaged —\n\n";
                const footer = "\n\n— Shared from https://engaged.chizu.ia.br/";
                const mensagemWhatsApp = intro + resposta + footer;
                compartilharWhatsApp(mensagemWhatsApp);
            });
        }
    }
}

function compartilharWhatsApp(texto) {
    if (!texto) return;
    const mensagem = encodeURIComponent(texto);
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const urlWhatsApp = isMobile ? `whatsapp://send?text=${mensagem}` : `https://web.whatsapp.com/send?text=${mensagem}`;
    window.open(urlWhatsApp, '_blank');
}

window.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.author-card').forEach(card => {
        card.addEventListener('click', () => {
            const autor = card.getAttribute('data-autor');
            iniciarConversaAutor(autor);
        });
    });
    const inputChat = document.getElementById('pergunta');
    if (inputChat) {
        inputChat.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') fazerPergunta();
        });
    }
});