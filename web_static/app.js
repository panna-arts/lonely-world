const API_BASE = '';

const el = (id) => document.getElementById(id);
const messagesEl = el('messages');
const inputEl = el('message-input');
const sendBtn = el('send-btn');
const charSelect = el('character-select');
const modelInfo = el('model-info');
const storyToggle = el('story-append-toggle');
const charStateEl = el('char-state');
const worldInfoEl = el('world-info');
const worldModal = el('world-modal');
const worldStepEl = el('world-step');
const worldAnswerEl = el('world-answer');
const worldSubmitBtn = el('world-submit');
const newCharModal = el('new-char-modal');
const newCharNameEl = el('new-char-name');
const newCharErrorEl = el('new-char-error');
const worldErrorEl = el('world-error');

let isThinking = false;

async function api(path, body) {
    const res = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    return res.json();
}

async function apiGet(path) {
    const res = await fetch(`${API_BASE}${path}`);
    return res.json();
}

function appendMessage(role, text, name) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    if (role === 'assistant' && name) {
        div.innerHTML = `<div class="name">${escapeHtml(name)}</div><div>${markdownToHtml(text)}</div>`;
    } else if (role === 'system' || role === 'error') {
        div.textContent = text;
    } else {
        div.innerHTML = markdownToHtml(text);
    }
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function markdownToHtml(text) {
    // very lightweight markdown: code blocks, inline code, bold, italic
    return escapeHtml(text)
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

function showThinking() {
    const div = document.createElement('div');
    div.className = 'message-thinking';
    div.id = 'thinking-indicator';
    div.innerHTML = '<span class="dots">正在构思故事</span>';
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function hideThinking() {
    const t = el('thinking-indicator');
    if (t) t.remove();
}

async function init() {
    const config = await apiGet('/api/config');
    if (!config.ok) {
        modelInfo.textContent = '配置错误';
        modelInfo.title = config.error || '未知错误';
        appendMessage('error', `服务器配置错误：${config.error}`);
        return;
    }
    modelInfo.textContent = `${config.provider} / ${config.model}`;
    storyToggle.checked = config.enable_story_append;
    await loadCharacters();
}

async function loadCharacters() {
    const data = await apiGet('/api/characters');
    const current = charSelect.value;
    charSelect.innerHTML = '<option value="">选择角色</option>';
    data.characters.forEach(name => {
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = name;
        charSelect.appendChild(opt);
    });
    if (current && data.characters.includes(current)) {
        charSelect.value = current;
    }
    if (data.characters.length === 0) {
        // First-time onboarding: auto prompt to create character
        newCharModal.classList.remove('hidden');
        newCharNameEl.focus();
    }
}

async function selectCharacter(name) {
    messagesEl.innerHTML = '';
    const data = await api('/api/load', { name });
    if (!data.ok) {
        appendMessage('error', data.error);
        return;
    }
    renderCharacter(data.character);
    data.conversation.forEach(m => {
        appendMessage(m.role, m.content, m.role === 'assistant' ? data.character.name : '');
    });
    appendMessage('system', '已进入游戏。输入 help 查看命令。');
}

function renderCharacter(character) {
    const s = character.state || {};
    const lines = [
        `<div class="state-line"><span class="state-label">名称：</span>${escapeHtml(character.name)}</div>`,
        `<div class="state-line"><span class="state-label">状态：</span>${escapeHtml(s.status || '—')}</div>`,
        `<div class="state-line"><span class="state-label">物品：</span>${(s.items || []).join('、') || '—'}</div>`,
        `<div class="state-line"><span class="state-label">技能：</span>${(s.skills || []).join('、') || '—'}</div>`,
        `<div class="state-line"><span class="state-label">性格：</span>${escapeHtml(s.personality || '—')}</div>`,
    ];
    charStateEl.innerHTML = lines.join('');

    const w = character.world || {};
    worldInfoEl.innerHTML = `
        <div class="state-line"><span class="state-label">时间：</span>${escapeHtml(w.time || '—')}</div>
        <div class="state-line"><span class="state-label">地点：</span>${escapeHtml(w.place || '—')}</div>
        <div class="state-line"><span class="state-label">人物：</span>${(w.people || []).join('、') || '—'}</div>
        <div class="state-line"><span class="state-label">基调：</span>${escapeHtml(w.tone || '—')}</div>
    `;
}

async function startNewCharacter() {
    const name = newCharNameEl.value.trim();
    if (!name) return;
    const confirmBtn = el('new-char-confirm');
    const originalText = confirmBtn.textContent;
    confirmBtn.disabled = true;
    confirmBtn.textContent = '创建中…';
    newCharErrorEl.classList.add('hidden');
    newCharErrorEl.textContent = '';

    try {
        const data = await api('/api/create', { name });
        if (!data.ok) {
            newCharErrorEl.textContent = data.error || '创建失败，请重试';
            newCharErrorEl.classList.remove('hidden');
            confirmBtn.disabled = false;
            confirmBtn.textContent = originalText;
            return;
        }
        newCharModal.classList.add('hidden');
        confirmBtn.disabled = false;
        confirmBtn.textContent = originalText;
        worldStepEl.textContent = data.question;
        worldAnswerEl.value = '';
        worldModal.classList.remove('hidden');
        worldAnswerEl.focus();
    } catch (err) {
        newCharErrorEl.textContent = '网络或服务器错误，请检查控制台日志后重试';
        newCharErrorEl.classList.remove('hidden');
        confirmBtn.disabled = false;
        confirmBtn.textContent = originalText;
    }
}

async function submitWorldAnswer() {
    const answer = worldAnswerEl.value.trim();
    if (!answer) return;
    worldSubmitBtn.disabled = true;
    worldErrorEl.classList.add('hidden');
    worldErrorEl.textContent = '';

    try {
        const data = await api('/api/world/answer', { answer });
        worldSubmitBtn.disabled = false;
        if (!data.ok) {
            worldErrorEl.textContent = data.error || '提交失败，请重试';
            worldErrorEl.classList.remove('hidden');
            return;
        }
        if (data.complete) {
            worldModal.classList.add('hidden');
            appendMessage('system', '世界观构建完成，角色已创建。');
            renderCharacter(data.character);
            // Auto-load into engine
            const name = data.character.name;
            await loadCharacters();
            charSelect.value = name;
            await selectCharacter(name);
            return;
        }
        worldStepEl.textContent = data.question;
        worldAnswerEl.value = '';
        worldAnswerEl.focus();
    } catch (err) {
        worldSubmitBtn.disabled = false;
        worldErrorEl.textContent = '网络或服务器错误，请检查控制台日志后重试';
        worldErrorEl.classList.remove('hidden');
    }
}

async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || isThinking) return;
    inputEl.value = '';
    appendMessage('user', text);
    isThinking = true;
    showThinking();

    const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let assistantDiv = null;
    let assistantText = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const event = JSON.parse(line.slice(6));
            if (event.type === 'thinking') {
                hideThinking();
                assistantDiv = appendMessage('assistant', '', '');
            } else if (event.type === 'chunk') {
                hideThinking();
                if (!assistantDiv) assistantDiv = appendMessage('assistant', '', '');
                assistantText += event.text;
                assistantDiv.innerHTML = markdownToHtml(assistantText);
            } else if (event.type === 'system') {
                hideThinking();
                appendMessage('system', event.message);
            } else if (event.type === 'error') {
                hideThinking();
                appendMessage('error', event.message);
            } else if (event.type === 'done') {
                hideThinking();
                if (event.reply && assistantDiv) {
                    assistantText = event.reply;
                    assistantDiv.innerHTML = markdownToHtml(assistantText);
                }
                // Update state display if changed
                if (event.state_updated || event.world_updated) {
                    // reload character state from backend implicitly next load,
                    // but for now we can’t easily get it without an extra call.
                    // Just show a subtle hint.
                }
            }
        }
    }
    isThinking = false;
}

async function doAction(action) {
    if (action === 'help') {
        appendMessage('system',
            '可用命令：help / undo / story / export / export-role / quit');
        return;
    }
    if (action === 'undo') {
        const data = await api('/api/undo', {});
        if (data.ok) {
            appendMessage('system', '已撤回上一轮操作。');
            messagesEl.lastElementChild?.remove();
            messagesEl.lastElementChild?.remove();
        } else {
            appendMessage('error', '没有可撤回的操作。');
        }
        return;
    }
    if (action === 'story') {
        const res = await fetch(`${API_BASE}/api/story`);
        const text = await res.text();
        appendMessage('system', `故事片段：\n${text}`);
        return;
    }
    if (action === 'export-story') {
        const data = await api('/api/export/story', {});
        appendMessage('system', data.ok ? `故事已导出：${data.path}` : '导出失败');
        return;
    }
    if (action === 'export-role') {
        const data = await api('/api/export/role', {});
        appendMessage('system', data.ok ? `角色已导出：${data.path}` : '导出失败');
        return;
    }
}

// Event bindings
sendBtn.addEventListener('click', sendMessage);
inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendMessage();
});

charSelect.addEventListener('change', () => {
    const name = charSelect.value;
    if (name) selectCharacter(name);
});

el('new-char-btn').addEventListener('click', () => {
    newCharModal.classList.remove('hidden');
    newCharNameEl.value = '';
    newCharErrorEl.classList.add('hidden');
    newCharErrorEl.textContent = '';
    newCharNameEl.focus();
});

el('new-char-cancel').addEventListener('click', () => {
    newCharModal.classList.add('hidden');
    newCharErrorEl.classList.add('hidden');
    newCharErrorEl.textContent = '';
});

el('new-char-confirm').addEventListener('click', startNewCharacter);
newCharNameEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') startNewCharacter();
});

worldSubmitBtn.addEventListener('click', submitWorldAnswer);
worldAnswerEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') submitWorldAnswer();
});

document.querySelectorAll('.actions button').forEach(btn => {
    btn.addEventListener('click', () => doAction(btn.dataset.action));
});

storyToggle.addEventListener('change', async () => {
    await api('/api/toggle-story-append', { enabled: storyToggle.checked });
});

init();
