(function () {
  const configEl = document.getElementById('chat-config');
  if (!configEl) return;

  const config = JSON.parse(configEl.textContent);
  const L = config.labels;

  const messagesEl = document.getElementById('chat-messages');
  const emptyHint = document.getElementById('chat-empty-hint');
  const inputEl = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send-btn');
  const typingEl = document.getElementById('chat-typing');
  const connectionEl = document.getElementById('chat-connection');
  const presenceLabel = document.getElementById('chat-presence-label');
  const emojiBtn = document.getElementById('chat-emoji-btn');
  const emojiPicker = document.getElementById('chat-emoji-picker');
  const searchBtn = document.getElementById('chat-search-btn');
  const searchPanel = document.getElementById('chat-search-panel');
  const searchInput = document.getElementById('chat-search-input');
  const searchResults = document.getElementById('chat-search-results');

  let socket = null;
  let typingTimeout = null;
  let isTypingSent = false;
  const messageIds = new Set();

  const EMOJIS = [
    '😀', '😂', '🥰', '😎', '🤔', '👍', '👏', '🙌', '🔥', '⭐',
    '❤️', '💯', '🎉', '🚀', '📚', '✅', '❌', '💪', '🙏', '😊',
    '🤩', '😢', '😡', '🎮', '🏆', '✨', '💡', '📝', '⏰', '🌟',
  ];

  function getCsrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : '';
  }

  function wsUrl() {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${window.location.host}${config.wsPath}`;
  }

  function formatTime(iso) {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function formatLastSeen(iso) {
    const d = new Date(iso);
    const diff = (Date.now() - d.getTime()) / 1000;
    if (diff < 60) return L.lastSeen + ' — ' + (config.labels.justNow || 'now');
    if (diff < 3600) return L.lastSeen + ' — ' + Math.floor(diff / 60) + 'm';
    return L.lastSeen + ' — ' + d.toLocaleString();
  }

  function updatePresence(payload) {
    if (!presenceLabel || payload.user_id !== config.friendId) return;
    if (payload.is_online) {
      presenceLabel.textContent = L.online;
      presenceLabel.dataset.online = '1';
    } else {
      presenceLabel.textContent = formatLastSeen(payload.last_seen);
      presenceLabel.dataset.online = '0';
    }
  }

  function scrollToBottom(smooth) {
    messagesEl.scrollTo({
      top: messagesEl.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto',
    });
  }

  function hideEmptyHint() {
    if (emptyHint) emptyHint.classList.add('hidden');
  }

  function buildMessageEl(msg) {
    if (messageIds.has(msg.id)) {
      const existing = messagesEl.querySelector(`[data-msg-id="${msg.id}"]`);
      if (existing) existing.remove();
    }
    messageIds.add(msg.id);

    const wrap = document.createElement('div');
    wrap.className = `friend-chat-bubble-wrap ${msg.is_mine ? 'mine' : 'theirs'} chat-msg-enter`;
    wrap.dataset.msgId = msg.id;

    const bubble = document.createElement('div');
    bubble.className = 'friend-chat-bubble';

    if (msg.is_deleted) {
      bubble.innerHTML = `<p class="deleted-msg">${escapeHtml(L.deleted)}</p>`;
    } else {
      bubble.innerHTML = `<p class="msg-text">${escapeHtml(msg.content)}</p>`;
    }

    const meta = document.createElement('div');
    meta.className = 'friend-chat-meta';
    let metaText = formatTime(msg.created_at);
    if (msg.is_edited && !msg.is_deleted) metaText += ' · ' + L.edited;
    meta.innerHTML = `<span>${metaText}</span>`;

    if (msg.is_mine && !msg.is_deleted) {
      const actions = document.createElement('div');
      actions.className = 'friend-chat-msg-actions';
      actions.innerHTML = `
        <button type="button" class="msg-action-btn" data-action="edit" data-id="${msg.id}">${escapeHtml(L.edit)}</button>
        <button type="button" class="msg-action-btn" data-action="delete" data-id="${msg.id}">${escapeHtml(L.delete)}</button>
      `;
      meta.appendChild(actions);
    }

    wrap.appendChild(bubble);
    wrap.appendChild(meta);
    return wrap;
  }

  function escapeHtml(t) {
    const d = document.createElement('div');
    d.textContent = t;
    return d.innerHTML;
  }

  function appendMessage(msg, scroll) {
    hideEmptyHint();
    const el = buildMessageEl(msg);
    messagesEl.appendChild(el);
    if (scroll !== false) scrollToBottom(true);
  }

  function updateMessage(msg) {
    const existing = messagesEl.querySelector(`[data-msg-id="${msg.id}"]`);
    if (existing) existing.remove();
    messageIds.delete(msg.id);
    appendMessage(msg, false);
  }

  function connect() {
    setConnection(L.connecting);
    socket = new WebSocket(wsUrl());

    socket.onopen = () => {
      setConnection(L.connected);
      socket.send(JSON.stringify({ type: 'chat.read' }));
    };

    socket.onclose = () => {
      setConnection(L.disconnected);
      setTimeout(connect, 2500);
    };

    socket.onerror = () => setConnection(L.disconnected);

    socket.onmessage = (e) => {
      let data;
      try {
        data = JSON.parse(e.data);
      } catch {
        return;
      }
      handleEvent(data);
    };
  }

  function setConnection(text) {
    if (connectionEl) connectionEl.textContent = text;
  }

  function handleEvent(data) {
    if (data.type === 'chat.message' && data.message) {
      appendMessage(data.message);
      if (!data.message.is_mine) {
        socket.send(JSON.stringify({ type: 'chat.read' }));
      }
    } else if (data.type === 'chat.message_update' && data.message) {
      updateMessage(data.message);
    } else if (data.type === 'chat.typing') {
      if (data.is_typing) {
        typingEl.classList.remove('hidden');
        scrollToBottom(true);
      } else {
        typingEl.classList.add('hidden');
      }
    } else if (data.type === 'chat.presence') {
      updatePresence(data);
    } else if (data.type === 'chat.error') {
      console.warn(data.error);
    }
  }

  function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || !socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ type: 'chat.message', content: text }));
    inputEl.value = '';
    inputEl.style.height = 'auto';
    stopTypingSignal();
  }

  function sendTypingSignal(typing) {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ type: 'chat.typing', is_typing: typing }));
  }

  function stopTypingSignal() {
    if (isTypingSent) {
      sendTypingSignal(false);
      isTypingSent = false;
    }
  }

  inputEl.addEventListener('input', () => {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
    if (!isTypingSent) {
      sendTypingSignal(true);
      isTypingSent = true;
    }
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(stopTypingSignal, 2000);
  });

  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  sendBtn.addEventListener('click', sendMessage);

  messagesEl.addEventListener('click', async (e) => {
    const btn = e.target.closest('.msg-action-btn');
    if (!btn) return;
    const id = btn.dataset.id;
    const action = btn.dataset.action;
    if (action === 'delete') {
      if (!confirm(L.deleteConfirm)) return;
      await fetch(`/friends/chat/message/${id}/delete/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrf() },
      });
    } else if (action === 'edit') {
      const wrap = messagesEl.querySelector(`[data-msg-id="${id}"]`);
      const textEl = wrap?.querySelector('.msg-text');
      if (!textEl) return;
      const newText = prompt(L.edit, textEl.textContent);
      if (newText === null) return;
      await fetch(`/friends/chat/message/${id}/edit/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrf(),
        },
        body: JSON.stringify({ content: newText }),
      });
    }
  });

  function initEmojiPicker() {
    EMOJIS.forEach((em) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = em;
      b.addEventListener('click', () => {
        inputEl.value += em;
        inputEl.focus();
        emojiPicker.classList.add('hidden');
      });
      emojiPicker.appendChild(b);
    });
    emojiBtn.addEventListener('click', () => {
      emojiPicker.classList.toggle('hidden');
    });
    document.addEventListener('click', (e) => {
      if (!emojiPicker.contains(e.target) && e.target !== emojiBtn) {
        emojiPicker.classList.add('hidden');
      }
    });
  }

  searchBtn.addEventListener('click', () => {
    searchPanel.classList.toggle('hidden');
    if (!searchPanel.classList.contains('hidden')) searchInput.focus();
  });

  let searchDebounce;
  searchInput.addEventListener('input', () => {
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(async () => {
      const q = searchInput.value.trim();
      if (!q) {
        searchResults.innerHTML = '';
        return;
      }
      const resp = await fetch(`/friends/chat/room/${config.roomId}/search/?q=${encodeURIComponent(q)}`);
      const data = await resp.json();
      searchResults.innerHTML = '';
      if (!data.results?.length) {
        searchResults.innerHTML = `<p class="search-empty">${escapeHtml(L.noResults)}</p>`;
        return;
      }
      data.results.forEach((msg) => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'search-result-item';
        item.innerHTML = `<strong>${escapeHtml(msg.sender_username)}</strong><span>${escapeHtml(msg.content.slice(0, 80))}</span>`;
        item.addEventListener('click', () => {
          const el = messagesEl.querySelector(`[data-msg-id="${msg.id}"]`);
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            el.classList.add('highlight-flash');
            setTimeout(() => el.classList.remove('highlight-flash'), 1500);
          }
          searchPanel.classList.add('hidden');
        });
        searchResults.appendChild(item);
      });
    }, 300);
  });

  (config.initialMessages || []).forEach((m) => appendMessage(m, false));
  if (config.initialMessages?.length) {
    hideEmptyHint();
    scrollToBottom(false);
  }

  initEmojiPicker();
  connect();
})();
