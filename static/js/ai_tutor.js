function getCsrfToken() {
  const input = document.querySelector('[name=csrfmiddlewaretoken]');
  if (input) return input.value;
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatAssistantText(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}

function appendMessage(role, content, extraClass = '') {
  const container = document.getElementById('ai-chat-messages');
  if (!container) return;

  const isUser = role === 'user';
  const wrap = document.createElement('div');
  wrap.className = `ai-msg ${isUser ? 'ai-msg-user' : 'ai-msg-assistant'} ${extraClass}`.trim();

  const avatar = document.createElement('div');
  avatar.className = 'ai-msg-avatar';
  avatar.textContent = isUser ? '🙂' : '🎓';

  const bubble = document.createElement('div');
  bubble.className = 'ai-msg-bubble';
  if (isUser) {
    bubble.innerHTML = `<p>${escapeHtml(content)}</p>`;
  } else {
    bubble.innerHTML = `<div class="ai-formatted">${formatAssistantText(content)}</div>`;
  }

  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  container.appendChild(wrap);
  container.scrollTop = container.scrollHeight;
}

function setTyping(visible) {
  const el = document.getElementById('ai-typing');
  const container = document.getElementById('ai-chat-messages');
  if (!el) return;
  el.classList.toggle('hidden', !visible);
  if (visible && container) {
    container.scrollTop = container.scrollHeight;
  }
}

function showSettingsMessage(text, isError = false) {
  const el = document.getElementById('ai-settings-message');
  if (!el) return;
  el.hidden = false;
  el.textContent = text;
  el.className = `ai-settings-message ${isError ? 'ai-settings-error' : 'ai-settings-ok'}`;
}

function updateStatusBanner(configured, hasSessionKey) {
  const banner = document.getElementById('ai-status-banner');
  if (!banner) return;
  banner.classList.remove('ai-status-ok', 'ai-status-warn');
  if (configured) {
    banner.classList.add('ai-status-ok');
    banner.textContent = hasSessionKey
      ? 'Using key saved in this browser.'
      : 'API key loaded from server (.env).';
  } else {
    banner.classList.add('ai-status-warn');
    banner.textContent = 'No API key — paste one below or add GEMINI_API_KEY to .env';
  }
}

async function saveApiKey(test = true) {
  const keyInput = document.getElementById('ai-api-key');
  const apiKey = keyInput?.value.trim() || '';
  if (!apiKey) {
    showSettingsMessage('Paste your Gemini API key first.', true);
    return;
  }

  const saveBtn = document.getElementById('ai-save-key-btn');
  if (saveBtn) saveBtn.disabled = true;
  showSettingsMessage('Testing connection…', false);

  try {
    const resp = await fetch('/ai/settings/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify({ api_key: apiKey, test }),
    });
    const data = await resp.json();

    if (!resp.ok) {
      showSettingsMessage(data.error || 'Could not save API key.', true);
      return;
    }

    updateStatusBanner(true, true);
    showSettingsMessage(
      data.test_answer
        ? `Connected! Test reply: ${data.test_answer.slice(0, 120)}…`
        : 'API key saved.',
      false
    );
    if (keyInput) keyInput.value = '';
  } catch {
    showSettingsMessage('Network error while saving key.', true);
  } finally {
    if (saveBtn) saveBtn.disabled = false;
  }
}

async function clearApiKey() {
  try {
    await fetch('/ai/settings/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify({ action: 'clear' }),
    });
    const statusResp = await fetch('/ai/status/');
    const status = await statusResp.json();
    updateStatusBanner(status.configured, status.has_session_key);
    showSettingsMessage('Session key cleared.', false);
  } catch {
    showSettingsMessage('Could not clear key.', true);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('ai-chat-form');
  const input = document.getElementById('ai-question-input');
  const sendBtn = document.getElementById('ai-send-btn');
  const historyEl = document.getElementById('chat-history-data');

  document.getElementById('ai-save-key-btn')?.addEventListener('click', () => saveApiKey(true));
  document.getElementById('ai-clear-key-btn')?.addEventListener('click', clearApiKey);

  if (historyEl) {
    try {
      const history = JSON.parse(historyEl.textContent);
      history.forEach((msg) => appendMessage(msg.role, msg.content));
    } catch {
      /* ignore */
    }
  }

  if (!form || !input) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const question = input.value.trim();
    if (!question) return;

    const subject = document.getElementById('ai-subject')?.value.trim() || '';
    const level = document.getElementById('ai-level')?.value.trim() || '';

    appendMessage('user', question);
    input.value = '';
    input.style.height = 'auto';
    sendBtn.disabled = true;
    setTyping(true);

    try {
      const resp = await fetch('/ai/ask/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ question, subject, level }),
      });

      let data = {};
      try {
        data = await resp.json();
      } catch {
        data = {};
      }
      setTyping(false);

      if (!resp.ok) {
        appendMessage(
          'assistant',
          data.error || 'Something went wrong. Open Gemini settings on the left and save a valid API key.',
          'ai-msg-error'
        );
        return;
      }

      appendMessage('assistant', data.answer);
      if (data.source === 'offline') {
        appendMessage(
          'assistant',
          'Tip: Gemini quota may be exceeded. Save a fresh API key in settings (left) or set GEMINI_MODEL=gemini-2.5-flash-lite in .env',
          'ai-msg-hint'
        );
      }
    } catch {
      setTyping(false);
      appendMessage('assistant', 'Network error. Check your connection and try again.', 'ai-msg-error');
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.requestSubmit();
    }
  });

  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
  });
});
