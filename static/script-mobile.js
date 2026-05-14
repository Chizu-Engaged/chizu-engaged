// static/script-mobile.js
let chatAtivo = null;      // { tipo, valor, autoresList }
let mensagens = [];        // histórico local de mensagens

function iniciarChat(tipo, valor, autoresList = []) {
    // Oculta a tela de seleção
    document.body.innerHTML = ''; // limpa tudo (ou melhor, esconde os elementos existentes)
    // Mas vamos criar a estrutura do chat
    criarInterfaceChat(tipo, valor, autoresList);
}

function criarInterfaceChat(tipo, valor, autoresList) {
    document.body.innerHTML = '';
    document.body.style.margin = '0';
    document.body.style.padding = '0';
    document.body.style.height = '100vh';
    document.body.style.overflow = 'hidden';

    const container = document.createElement('div');
    container.className = 'mobile-chat-container';
    container.style.cssText = `
        display: flex;
        flex-direction: column;
        height: 100%;
        width: 100%;
        background: var(--paper, #f5f0e8);
    `;

    // Cabeçalho
    const header = document.createElement('div');
    header.className = 'chat-header';
    header.style.cssText = `
        display: flex;
        align-items: center;
        padding: 12px 16px;
        background: var(--beige-mid, #ede8de);
        border-bottom: 1px solid var(--mist, #c8bfae);
        flex-shrink: 0;
    `;
    header.innerHTML = `
        <button class="back-btn" style="background:none; border:none; font-size:1.5rem; cursor:pointer; margin-right:12px; color:var(--sage, #6b7c5e);">←</button>
        <div class="chat-title" style="font-size:1rem; font-weight:500;">${tipo === 'tema' ? 'Theme: ' + valor : 'Voice: ' + valor}</div>
    `;
    header.querySelector('.back-btn').onclick = () => voltarParaSelecao();

    // Área de mensagens
    const messagesDiv = document.createElement('div');
    messagesDiv.className = 'chat-messages';
    messagesDiv.id = 'chat-messages-mobile';
    messagesDiv.style.cssText = `
        flex: 1;
        overflow-y: auto;
        padding: 12px;
        display: flex;
        flex-direction: column;
        gap: 8px;
    `;

    // Área de input (apenas input + botão)
    const inputArea = document.createElement('div');
    inputArea.className = 'chat-input-area';
    inputArea.style.cssText = `
        display: flex;
        gap: 8px;
        padding: 12px;
        background: var(--paper, #f5f0e8);
        border-top: 1px solid var(--mist, #c8bfae);
        flex-shrink: 0;
    `;

    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Ask the teachings...';
    input.id = 'pergunta-mobile';
    input.autocomplete = 'off';
    input.style.cssText = `
        flex: 1;
        padding: 12px;
        border: 1px solid var(--mist, #c8bfae);
        border-radius: 30px;
        font-family: var(--font-serif, 'Cormorant Garamond', serif);
        font-size: 16px;
        background: white;
    `;

    const button = document.createElement('button');
    button.textContent = '→';
    button.id = 'btn-enviar-mobile';
    button.style.cssText = `
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: var(--sage, #6b7c5e);
        color: white;
        border: none;
        font-size: 1.2rem;
        cursor: pointer;
        flex-shrink: 0;
    `;
    button.onclick = () => enviarPerguntaMobile(tipo, valor);

    // Guarda informações extras (autor fixo, se for o caso)
    if (tipo === 'autor') {
        const hiddenAutor = document.createElement('input');
        hiddenAutor.type = 'hidden';
        hiddenAutor.id = 'autor-fixo';
        hiddenAutor.value = valor;
        inputArea.appendChild(hiddenAutor);
    }

    inputArea.appendChild(input);
    inputArea.appendChild(button);
    container.appendChild(header);
    container.appendChild(messagesDiv);
    container.appendChild(inputArea);
    document.body.appendChild(container);

    // Evento Enter
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') enviarPerguntaMobile(tipo, valor);
    });

    // Mensagem de boas-vindas
    let boasVindas = '';
    if (tipo === 'tema') {
        boasVindas = `Ask anything about <em>${valor}</em>.`;
    } else {
        boasVindas = `Ask anything to <strong>${valor}</strong>.`;
    }
    adicionarMensagemMobile('bot', boasVindas);

    setTimeout(() => input.focus(), 200);
}


async function enviarPerguntaMobile(tipo, valor) {
    const input = document.getElementById('pergunta-mobile');
    if (!input) return;
    const texto = input.value.trim();
    if (!texto) return;

    let autorFiltro = '';
    if (tipo === 'autor') {
        autorFiltro = valor;
    }
    // Para tema, autorFiltro permanece vazio

    adicionarMensagemMobile('user', texto);
    input.value = '';
    input.disabled = true;

    // Cria mensagem de espera com classe 'waiting'
    const waitingId = adicionarMensagemMobile('bot', '<em>Listening to the teachings...</em>', true);
    const waitingElem = document.getElementById(waitingId);
    
    // Rotação de mensagens de espera (igual ao desktop)
    const _wmsgs = [...(window.WAITING_JS || ['Consulting the teachings...'])].sort(() => Math.random() - 0.5);
    let _idx = 0;
    const _rot = setInterval(() => {
        if (!waitingElem || !waitingElem.isConnected) {
            clearInterval(_rot);
            return;
        }
        _idx = (_idx + 1) % _wmsgs.length;
        const bubble = waitingElem.querySelector('.msg-bubble');
        if (bubble) bubble.innerHTML = `<em>${_wmsgs[_idx]}</em>`;
    }, 2500);

    try {
        const payload = {
            pergunta: texto,
            session_id: 'mobile-' + Date.now(),
            tema: tipo === 'tema' ? valor : null,
            autor: autorFiltro || null
        };
        const response = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        clearInterval(_rot);
        if (waitingElem && waitingElem.isConnected) waitingElem.remove();
        adicionarMensagemMobile('bot', data.resposta);
    } catch (err) {
        clearInterval(_rot);
        if (waitingElem && waitingElem.isConnected) waitingElem.remove();
        adicionarMensagemMobile('bot', 'The silence holds this question for now.');
    } finally {
        input.disabled = false;
        input.value = '';
        setTimeout(() => input.focus(), 100);
    }
}

function adicionarMensagemMobile(role, html, isWaiting = false) {
    const messagesDiv = document.getElementById('chat-messages-mobile');
    if (!messagesDiv) return null;
    
    const msgDiv = document.createElement('div');
    msgDiv.className = `msg ${role}`;
    if (isWaiting) msgDiv.id = 'waiting-msg-' + Date.now();
    msgDiv.innerHTML = `<div class="msg-bubble"><p>${html}</p></div>`;
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return msgDiv.id;
}

function voltarParaSelecao() {
    // Recarrega a página original (versão mobile)
    window.location.reload();
}


// No DOMContentLoaded, em vez de apenas alert, chamamos iniciarChat com os dados
document.addEventListener('DOMContentLoaded', () => {
    // Clique nos cards de tema
    document.querySelectorAll('.theme-card').forEach(card => {
        card.addEventListener('click', () => {
            const tema = card.getAttribute('data-tema');
            // Extrair lista de autores do atributo ou do texto
            const autoresElem = card.querySelector('.theme-authors');
            let autoresList = [];
            if (autoresElem) {
                autoresList = autoresElem.textContent.split(' · ');
            }
            iniciarChat('tema', tema, autoresList);
        });
    });
    // Clique nos cards de autor
    document.querySelectorAll('.author-card').forEach(card => {
        card.addEventListener('click', () => {
            const autor = card.getAttribute('data-autor');
            iniciarChat('autor', autor, []);
        });
    });
});