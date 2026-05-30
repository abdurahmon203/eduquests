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

function appendMessage(role, content) {
  const container = document.getElementById('ai-chat-messages');
  if (!container) return;

  const isUser = role === 'user';
  const wrap = document.createElement('div');
  wrap.className = `ai-msg ${isUser ? 'ai-msg-user' : 'ai-msg-assistant'}`;

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

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('ai-chat-form');
  const input = document.getElementById('ai-question-input');
  const sendBtn = document.getElementById('ai-send-btn');
  const historyEl = document.getElementById('chat-history-data');

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

      const data = await resp.json();
      setTyping(false);

      if (!resp.ok) {
        appendMessage('assistant', data.error || 'Something went wrong. Please try again.');
        return;
      }

      appendMessage('assistant', data.answer);
    } catch {
      setTyping(false);
      appendMessage('assistant', 'Network error. Check your connection and try again.');
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
