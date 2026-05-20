// static/script-mobile.js
let chatAtivo = null;
let mensagens = [];

function iniciarChat(tipo, valor, autoresList = []) {
    if (tipo === 'tema' && valor === "") {
        valor = "All Voices";
        autoresList = window.AUTORES_DISPONIVEIS || [];
    }
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
    container.style.cssText = `display: flex; flex-direction: column; height: 100%; width: 100%; background: var(--paper, #f5f0e8);`;

    const header = document.createElement('div');
    header.className = 'chat-header';
    header.style.cssText = `display: flex; align-items: center; padding: 12px 16px; background: var(--beige-mid, #ede8de); border-bottom: 1px solid var(--mist, #c8bfae); flex-shrink: 0;`;

    const ui = window.UI_STRINGS || {};
    const allVoicesLabel = ui.all_voices_label || "All Voices";
    const voicePrefix = ui.voice_prefix || "VOICE: ";

    let titulo = '';
    if (tipo === 'tema') {
        titulo = valor === "All Voices" ? allVoicesLabel.toUpperCase() : `Theme: ${valor}`;
    } else {
        titulo = `${voicePrefix}${valor}`;
    }
    header.innerHTML = `
        <button class="back-btn" style="background:none; border:none; font-size:1.5rem; cursor:pointer; margin-right:12px; color:var(--sage, #6b7c5e);">←</button>
        <div class="chat-title" style="font-size:1rem; font-weight:500;">${titulo}</div>
    `;
    header.querySelector('.back-btn').onclick = () => voltarParaSelecao();

    const messagesDiv = document.createElement('div');
    messagesDiv.className = 'chat-messages';
    messagesDiv.id = 'chat-messages-mobile';
    messagesDiv.style.cssText = `flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 8px;`;

    const inputArea = document.createElement('div');
    inputArea.className = 'chat-input-area';
    inputArea.style.cssText = `display: flex; gap: 8px; padding: 12px; background: var(--paper, #f5f0e8); border-top: 1px solid var(--mist, #c8bfae); flex-shrink: 0;`;

    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = ui.input_placeholder || "Ask the teachings...";
    input.id = 'pergunta-mobile';
    input.autocomplete = 'off';
    input.style.cssText = `flex: 1; padding: 12px; border: 1px solid var(--mist, #c8bfae); border-radius: 30px; font-family: var(--font-serif, 'Cormorant Garamond', serif); font-size: 16px; background: white;`;

    const button = document.createElement('button');
    button.textContent = '→';
    button.id = 'btn-enviar-mobile';
    button.style.cssText = `width: 48px; height: 48px; border-radius: 50%; background: var(--sage, #6b7c5e); color: white; border: none; font-size: 1.2rem; cursor: pointer; flex-shrink: 0;`;
    button.onclick = () => enviarPerguntaMobile(tipo, valor === "All Voices" ? "" : valor, autoresList);

    inputArea.appendChild(input);
    inputArea.appendChild(button);
    container.appendChild(header);
    container.appendChild(messagesDiv);
    container.appendChild(inputArea);
    document.body.appendChild(container);

    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') enviarPerguntaMobile(tipo, valor === "All Voices" ? "" : valor, autoresList);
    });

    let boasVindas = '';
    const welcomeAll = ui.welcome_prompt_all_voices || "Ask anything to the full chorus of engaged Buddhism & simple economics.";
    const welcomeTheme = ui.welcome_prompt_theme || "Ask anything about {theme}";
    const welcomeAuthor = ui.welcome_prompt_general || "What would you like to explore today?";
    if (tipo === 'tema') {
        if (valor === "All Voices") {
            boasVindas = welcomeAll;
        } else {
            boasVindas = welcomeTheme.replace("{theme}", valor);
        }
    } else {
        boasVindas = `${welcomeAuthor} (${valor})`;
    }
    adicionarMensagemMobile('bot', boasVindas);
    setTimeout(() => input.focus(), 200);
}

async function enviarPerguntaMobile(tipo, valor, autoresList = []) {
    const input = document.getElementById('pergunta-mobile');
    if (!input) return;
    const texto = input.value.trim();
    if (!texto) return;

    let autorFiltro = null;
    let temaFiltro = null;
    if (tipo === 'autor') {
        autorFiltro = valor;
    } else if (tipo === 'tema') {
        temaFiltro = (valor === "" || valor === "All Voices") ? null : valor;
    }

    adicionarMensagemMobile('user', texto);
    input.value = '';
    input.disabled = true;

    const waitingId = adicionarMensagemMobile('bot', '<em>Listening to the teachings...</em>', true);
    const waitingElem = document.getElementById(waitingId);
    const _wmsgs = [...(window.WAITING_JS || ['Consulting the teachings...'])];
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
            tema: temaFiltro,
            autor: autorFiltro
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
    window.location.reload();
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.theme-card').forEach(card => {
        card.addEventListener('click', () => {
            let tema = card.getAttribute('data-tema');
            if (tema === null) {
                const themeNameElem = card.querySelector('.theme-name');
                tema = themeNameElem ? themeNameElem.innerText : '';
            }
            let autoresList = [];
            if (tema === "" || tema === "All Voices") {
                autoresList = window.AUTORES_DISPONIVEIS || [];
            }
            iniciarChat('tema', tema, autoresList);
        });
    });
    document.querySelectorAll('.author-card').forEach(card => {
        card.addEventListener('click', () => {
            const autor = card.getAttribute('data-autor');
            if (autor) iniciarChat('autor', autor, []);
        });
    });
});