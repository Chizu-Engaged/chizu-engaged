// ============================================
// CHIZU: ENGAGED — /statics/script.js
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
    iniciarConversa();
}

function iniciarConversa() {
    document.getElementById('tela-temas').style.display = 'none';
    document.getElementById('tela-chat').style.display  = 'flex';

    if (temaAtivo === "") {
        document.getElementById('chat-tema-label').textContent = "ALL VOICES";
        const todosAutores = window.AUTORES_DISPONIVEIS || [];
        document.getElementById('chat-vozes-label').textContent = todosAutores.join(' · ');
    } else {
        document.getElementById('chat-tema-label').textContent = temaAtivo.toUpperCase();
        document.getElementById('chat-vozes-label').textContent = (window.TEMAS_DISPONIVEIS[temaAtivo] || []).join(' · ');
    }

    document.getElementById('pergunta').focus();

    const msgs = document.getElementById('chat-messages');
    if (temaAtivo === "") {
        msgs.innerHTML = `<div class="msg bot"><div class="msg-bubble"><p>Ask anything to the full chorus of engaged Buddhism & simple economics.</p></div></div>`;
    } else {
        msgs.innerHTML = `<div class="msg bot"><div class="msg-bubble"><p>What would you like to explore today?</p></div></div>`;
    }
    
    adicionarHistorico(temaAtivo);  // ← agora trata "" corretamente
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
    // Converte tema vazio para "All Voices" no título exibido
    let tituloExibido = tema;
    if (tema === "") tituloExibido = "All Voices";
    
    const ts = new Date().toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' });
    historico.unshift({ 
        tema: tituloExibido,      // para exibição
        temaOriginal: tema,       // guarda "" ou o tema real
        ts, 
        mensagens: [] 
    });
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

    // Marca ativo na sidebar
    document.querySelectorAll('.sb-item').forEach((el, i) => {
        el.classList.toggle('active', i === idx);
    });

    // Restaura o temaAtivo (usa temaOriginal se existir, senão h.tema)
    if (h.temaOriginal !== undefined && h.temaOriginal === "") {
        temaAtivo = "";
    } else {
        temaAtivo = h.tema;
    }

    // Vai para tela de chat
    document.getElementById('tela-temas').style.display = 'none';
    document.getElementById('tela-chat').style.display = 'flex';

    // Define cabeçalho do chat
    if (temaAtivo === "") {
        // Caso All Voices
        document.getElementById('chat-tema-label').textContent = "ALL VOICES";
        const todosAutores = window.AUTORES_DISPONIVEIS || [];
        document.getElementById('chat-vozes-label').textContent = todosAutores.join(' · ');
    } else {
        document.getElementById('chat-tema-label').textContent = h.tema.toUpperCase();
        document.getElementById('chat-vozes-label').textContent = (window.TEMAS_DISPONIVEIS[h.tema] || []).join(' · ');
    }

    // Restaura mensagens salvas
    const msgs = document.getElementById('chat-messages');
    if (h.mensagens && h.mensagens.length > 0) {
        msgs.innerHTML = h.mensagens.map(m =>
            `<div class="msg ${m.role}"><div class="msg-bubble"><p>${m.html}</p></div></div>`
        ).join('');
    } else {
        if (temaAtivo === "") {
            msgs.innerHTML = `<div class="msg bot"><div class="msg-bubble"><p>Ask anything to the full chorus of engaged Buddhism & simple economics.</p></div></div>`;
        } else {
            msgs.innerHTML = `<div class="msg bot"><div class="msg-bubble"><p>Ask anything about <em>${h.tema}</em>.</p></div></div>`;
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
    document.getElementById('chat-tema-label').textContent = "VOICE: " + autor.toUpperCase();
    document.getElementById('chat-vozes-label').innerHTML = '<span class="voice-note" style="font-size:0.85rem; opacity:0.7;">Answers inspired by their writings.</span>';
    const select = document.getElementById('autor-select');
    if (select) select.style.display = 'none';
    document.getElementById('pergunta').focus();
    const msgs = document.getElementById('chat-messages');
    msgs.innerHTML = `<div class="msg bot"><div class="msg-bubble"><p>What would you like to explore today?</p></div></div>`;
    adicionarHistorico("Voice: " + autor); // título amigável
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

    // Processa o texto da mensagem (markdown simples)
    const html = texto
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');

    // Estrutura do conteúdo da mensagem
    let bubbleContent = `<div class="msg-bubble"><p>${html}</p></div>`;

    // Adiciona o botão de compartilhar APENAS para mensagens do bot
    if (role === 'bot') {
        // Cria um ID único para a mensagem, para referenciar no futuro
        const msgId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 6);
        div.id = msgId;
        
        // A seta (ícone de reply) será adicionada ao lado da bolha
        bubbleContent = `
            <div style="display: flex; align-items: center; justify-content: flex-start; gap: 10px;">
                <div class="msg-bubble" style="flex: 1;"> 
                    <p>${html}</p>
                </div>
                <button class="share-wpp-btn" data-msg-id="${msgId}" title="Share this message on WhatsApp" aria-label="Share on WhatsApp" style="background: none; border: none; cursor: pointer; color: #6b7c5e; font-size: 1.2rem; transition: opacity 0.2s;">
                    <i class="fas fa-share-square"></i>
                </button>
            </div>
        `;
    }
    
    div.innerHTML = bubbleContent;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;

    // Salva no histórico
    if (role === 'user' || role === 'bot') {
        salvarMensagemHistorico(role, html);
    }
    

    if (role === 'bot') {
        const shareBtn = div.querySelector('.share-wpp-btn');
        if (shareBtn) {
            shareBtn.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
                
                // Obtém o texto da mensagem (resposta pura, sem o botão)
                const bubbleTextElem = div.querySelector('.msg-bubble p');
                let resposta = bubbleTextElem ? bubbleTextElem.innerText : '';
                
                // Remove o rodapé interno (ex: "— via Engaged Buddhism · Llama...")
                // Isso evita duplicar informação no WhatsApp
                const viaIndex = resposta.indexOf('— via');
                if (viaIndex !== -1) {
                    resposta = resposta.substring(0, viaIndex).trim();
                }
                
                // Constrói a mensagem final para o WhatsApp
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

    // Codifica o texto para ser usado em uma URL
    const mensagem = encodeURIComponent(texto);
    
    // Detecta se o dispositivo é mobile ou desktop
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    
    let urlWhatsApp;
    if (isMobile) {
        // Em dispositivos móveis, usa o esquema `whatsapp://` para abrir o app
        urlWhatsApp = `whatsapp://send?text=${mensagem}`;
    } else {
        // Em desktop, abre o WhatsApp Web em uma nova aba
        urlWhatsApp = `https://web.whatsapp.com/send?text=${mensagem}`;
    }

    // Abre o link (ou tenta)
    window.open(urlWhatsApp, '_blank');
}

// ============================================
// INICIALIZAÇÃO
// ============================================
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