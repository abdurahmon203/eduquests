function getCsrfToken() {
  const input = document.querySelector('[name=csrfmiddlewaretoken]');
  if (input) return input.value;
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}

function renderFriendAction(container, data, userId, incomingRequestId) {
  if (!container || !data.ok) return;

  const rel = data.relationship;
  if (rel === 'friends') {
    container.innerHTML = '<span class="friend-status-pill friends">Already Friends</span>';
  } else if (rel === 'pending_outgoing') {
    container.innerHTML = '<span class="friend-status-pill pending">Request Sent</span>';
  } else if (rel === 'pending_incoming' && (data.incoming_request_id || incomingRequestId)) {
    const rid = data.incoming_request_id || incomingRequestId;
    container.innerHTML = `
      <form method="POST" action="/friends/accept/${rid}/" class="ajax-friend-form" data-user-id="${userId}">
        <input type="hidden" name="csrfmiddlewaretoken" value="${getCsrfToken()}">
        <button type="submit" class="btn btn-primary btn-sm">Accept Request</button>
      </form>`;
    bindAjaxForms(document.getElementById('friends-search-results'));
  }
}

function bindAjaxForms(root) {
  if (!root) return;
  root.querySelectorAll('.ajax-friend-form').forEach((form) => {
    if (form.dataset.bound) return;
    form.dataset.bound = '1';
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const card = form.closest('[data-user-id]');
      const container = form.closest('[data-action-container]') || form.parentElement;
      const userId = card?.dataset.userId || form.dataset.userId;

      const fd = new FormData(form);
      try {
        const resp = await fetch(form.action, {
          method: 'POST',
          body: fd,
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        const data = await resp.json();
        if (!data.ok) {
          alert(data.error || 'Something went wrong');
          return;
        }
        renderFriendAction(container, data, userId, data.incoming_request_id);
      } catch {
        alert('Network error. Please try again.');
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('friends-search-input');
  const results = document.getElementById('friends-search-results');
  const hint = document.getElementById('friends-search-hint');
  let timer = null;

  if (results) bindAjaxForms(results);

  if (!input || !results) return;

  const fetchResults = (query) => {
    const url = new URL(window.location.href);
    url.searchParams.set('q', query);
    url.searchParams.set('partial', '1');
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then((r) => r.text())
      .then((html) => {
        results.innerHTML = html;
        bindAjaxForms(results);
        if (hint) hint.classList.toggle('hidden', query.length > 0);
      })
      .catch(() => {});
  };

  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => fetchResults(input.value.trim()), 280);
  });
});
