// ============================================
// CHIZU ENGAGED — script.js
// ============================================

const SESSION_ID = Math.random().toString(36).slice(2) + Date.now();


let temaAtivo  = "Gift Economy";
let historico  = [];
let idxAtivo   = 0;
const TEMAS    = window.TEMAS_DISPONIVEIS || {};

function atualizarSelectAutores(tema) {
    const select = document.getElementById('autor-select');
    if (!select) return;
    const autores = (window.TEMAS_DISPONIVEIS && window.TEMAS_DISPONIVEIS[tema]) || [];
    select.innerHTML = '<option value="">All voices</option>' +
        autores.map(a => `<option value="${a}">${a}</option>`).join('');
}

// ============================================
// SELEÇÃO DE TEMA
// ============================================
function selecionarTema(el) {
    document.querySelectorAll('.tema-card').forEach(c => c.classList.remove('selected'));
    el.classList.add('selected');
    temaAtivo = el.dataset.tema;
    document.getElementById('start-hint').textContent = temaAtivo + ' selected';
}

function iniciarConversa() {
    document.getElementById('tela-temas').style.display = 'none';
    document.getElementById('tela-chat').style.display  = 'flex';
    document.getElementById('chat-tema-label').textContent  = temaAtivo.toUpperCase();
    document.getElementById('chat-vozes-label').textContent = (window.TEMAS_DISPONIVEIS[temaAtivo] || []).join(' · ');
    document.getElementById('pergunta').focus();

    const msgs = document.getElementById('chat-messages');
    msgs.innerHTML = `<div class="msg bot"><div class="msg-bubble"><p>Ask anything about <em>${temaAtivo}</em>.</p></div></div>`;
    adicionarHistorico(temaAtivo);
    setTimeout(() => atualizarSelectAutores(temaAtivo), 100);
}

function novaConversa() {
    // Volta para tela de temas
    document.getElementById('tela-temas').style.display = '';
    document.getElementById('tela-chat').style.display  = 'none';

    // Limpa seleção de tema
    document.querySelectorAll('.tema-card').forEach(c => c.classList.remove('selected'));
    const hint = document.getElementById('start-hint');
    if (hint) hint.textContent = '';

    // Reset tema ativo
    temaAtivo = 'Gift Economy';
}

// ============================================
// HISTÓRICO (sidebar)
// ============================================
function adicionarHistorico(tema) {
    const ts = new Date().toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' });
    historico.unshift({ tema, ts, mensagens: [] });
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

    // Marca ativo na sidebar
    document.querySelectorAll('.sb-item').forEach((el, i) => {
        el.classList.toggle('active', i === idx);
    });

    // Vai para tela de chat com o tema
    temaAtivo = h.tema;
    document.getElementById('tela-temas').style.display = 'none';
    document.getElementById('tela-chat').style.display  = 'flex';
    document.getElementById('chat-tema-label').textContent  = h.tema.toUpperCase();
    document.getElementById('chat-vozes-label').textContent = (window.TEMAS_DISPONIVEIS[h.tema] || []).join(' · ');

    // Restaura mensagens salvas
    const msgs = document.getElementById('chat-messages');
    if (h.mensagens && h.mensagens.length > 0) {
        msgs.innerHTML = h.mensagens.map(m =>
            `<div class="msg ${m.role}"><div class="msg-bubble"><p>${m.html}</p></div></div>`
        ).join('');
    } else {
        msgs.innerHTML = `<div class="msg bot"><div class="msg-bubble"><p>Ask anything about <em>${h.tema}</em>.</p></div></div>`;
    }
    msgs.scrollTop = msgs.scrollHeight;
    document.getElementById('pergunta').focus();
    atualizarSelectAutores(h.tema);
}

// ============================================
// ENVIO DE PERGUNTA
// ============================================
async function fazerPergunta() {
    const input    = document.getElementById('pergunta');
    const textoRaw = input.value.trim();
    if (!textoRaw) return;

    const autorSelect = document.getElementById('autor-select');
    const autorFiltro = autorSelect ? autorSelect.value : '';

    adicionarMensagem('user', textoRaw);
    input.value    = '';
    input.disabled = true;

    // Placeholder de espera
    const msgs    = document.getElementById('chat-messages');
    const waiting = document.createElement('div');
    waiting.className = 'msg bot waiting';
    waiting.innerHTML = '<div class="msg-bubble"><em>Listening to the teachings...</em></div>';
    msgs.appendChild(waiting);
    msgs.scrollTop = msgs.scrollHeight;

    // Rotação de mensagens de espera
    const _wmsgs = [...(window.WAITING_JS || ['Consulting the teachings...'])].sort(() => Math.random() - 0.5);
    let _idx = 0;
    const _rot = setInterval(() => {
        _idx = (_idx + 1) % _wmsgs.length;
        waiting.querySelector('.msg-bubble').innerHTML = `<em>${_wmsgs[_idx]}</em>`;
    }, 2500);

    try {
        const payload = { pergunta: textoRaw, session_id: SESSION_ID, tema: temaAtivo };
        if (autorFiltro) payload.autor = autorFiltro;

        const r    = await fetch('/ask', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(payload)
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

// ============================================
// RENDERIZAR MENSAGEM
// ============================================
function adicionarMensagem(role, texto) {
    const msgs = document.getElementById('chat-messages');
    const div  = document.createElement('div');
    div.className = `msg ${role}`;

    const html = texto
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');

    div.innerHTML = `<div class="msg-bubble"><p>${html}</p></div>`;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;

    // Salva no histórico
    if (role === 'user' || role === 'bot') {
        salvarMensagemHistorico(role, html);
    }
}

// ============================================
// UTILITÁRIOS
// ============================================
function randomMsg(arr) {
    if (!arr || arr.length === 0) return 'Consulting the teachings...';
    return arr[Math.floor(Math.random() * arr.length)];
}

// ============================================
// SÍNTESE DE VOZ (TTS)
// ============================================
let falando = false;

function falar(texto) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const fala  = new SpeechSynthesisUtterance(limparParaVoz(texto));
    fala.lang   = 'en-US';
    fala.rate   = 0.9;
    fala.pitch  = 1.0;
    fala.onstart = () => { falando = true; };
    fala.onend   = () => { falando = false; };
    window.speechSynthesis.speak(fala);
}

function limparParaVoz(texto) {
    return texto
        .replace(/— via .*$/gm, '')
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/#{1,6}\s/g, '')
        .replace(/<[^>]+>/g, '')
        .trim();
}

// ============================================
// MICROFONE
// ============================================
let reconhecendo = false;
let recognition  = null;
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;

function iniciarMicrofone() {
    if (!SR || reconhecendo) return;
    const btnMic = document.getElementById('btn-mic');

    recognition = new SR();
    recognition.lang            = 'en-US';
    recognition.interimResults  = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
        reconhecendo = true;
        btnMic.classList.add('ouvindo');
        btnMic.title = 'Release to send';
        document.getElementById('pergunta').placeholder = 'Listening...';
    };

    recognition.onresult = (e) => {
        document.getElementById('pergunta').value = e.results[0][0].transcript;
    };

    recognition.onerror = () => {
        reconhecendo = false;
        btnMic.classList.remove('ouvindo');
        document.getElementById('pergunta').placeholder = 'Ask the teachings...';
    };

    recognition.onend = () => {
        reconhecendo = false;
        btnMic.classList.remove('ouvindo');
        document.getElementById('pergunta').placeholder = 'Ask the teachings...';
        if (document.getElementById('pergunta').value.trim()) fazerPergunta();
    };

    recognition.start();
}

function pararMicrofone(e) {
    if (e) e.preventDefault();
    if (recognition && reconhecendo) recognition.stop();
}

// ============================================
// INICIALIZAÇÃO
// ============================================
window.addEventListener('DOMContentLoaded', () => {
    const btnMic = document.getElementById('btn-mic');
    if (btnMic && SR) {
        btnMic.addEventListener('mousedown',  iniciarMicrofone);
        btnMic.addEventListener('mouseup',    pararMicrofone);
        btnMic.addEventListener('touchstart', (e) => { e.preventDefault(); iniciarMicrofone(); }, { passive: false });
        btnMic.addEventListener('touchend',   pararMicrofone);
    }

    const inputChat = document.getElementById('pergunta');
    if (inputChat) {
        inputChat.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') fazerPergunta();
        });
    }
});