const messagesDiv = document.getElementById('messages');
const input = document.getElementById('input');
const sendBtn = document.getElementById('send');
const sourcesPanel = document.getElementById('sources');
const sourcesList = document.getElementById('sources-list');

let history = [];

sendBtn.addEventListener('click', sendMessage);
input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    appendMessage('user', text);
    input.value = '';
    sendBtn.disabled = true;
    history.push({ role: 'user', content: text });

    const loadingId = appendLoading();

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, history: history })
        });
        const data = await res.json();
        removeLoading(loadingId);
        appendMessage('bot', data.answer);
        history.push({ role: 'assistant', content: data.answer });
        renderSources(data.sources);
    } catch (err) {
        removeLoading(loadingId);
        appendMessage('bot', 'Ошибка соединения с сервером.');
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

function appendMessage(role, text) {
    const div = document.createElement('div');
    div.className = `msg ${role}`;
    div.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function appendLoading() {
    const id = 'load-' + Date.now();
    const div = document.createElement('div');
    div.className = 'msg bot';
    div.id = id;
    div.innerHTML = `<div class="bubble">Печатаю...</div>`;
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return id;
}

function removeLoading(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function renderSources(sources) {
    if (!sources || sources.length === 0) {
        sourcesPanel.classList.add('hidden');
        return;
    }
    sourcesPanel.classList.remove('hidden');
    sourcesList.innerHTML = '';
    sources.forEach(s => {
        const item = document.createElement('div');
        item.className = 'source-item';
        const page = s.page ? `, стр. ${s.page}` : '';
        item.innerHTML = `
            <div class="source-title">${escapeHtml(s.source)}${escapeHtml(page)}</div>
            <div class="source-text">${escapeHtml(s.text)}...</div>
        `;
        sourcesList.appendChild(item);
    });
}

function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
}