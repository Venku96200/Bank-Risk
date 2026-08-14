const api = location.origin;
const params = new URLSearchParams(window.location.search);
const alertId = params.get('id');
const $ = selector => document.querySelector(selector);
const escapeHtml = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

async function request(path, options) {
  const response = await fetch(api + path, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

async function loadAlert() {
  if (!alertId) {
    $('#alertDetail').innerHTML = '<div class="detail-card"><h2>Missing alert</h2><p>No alert ID was supplied.</p></div>';
    return;
  }

  try {
    const alert = await request(`/alerts/${alertId}`);
    const explanation = await request(`/alerts/${alertId}/explain`);
    const transaction = alert.transaction || {};
    const reasons = Array.isArray(alert.reasons) ? alert.reasons : [];
    const policies = Array.isArray(explanation.policies) ? explanation.policies : [];

    $('#alertDetail').innerHTML = `
      <section class="detail-card">
        <h2>Alert #${alert.id}</h2>
        <p class="status-line"><strong>Status:</strong> ${escapeHtml(alert.status)} &nbsp; <strong>Level:</strong> <span class="${escapeHtml(alert.level)}">${escapeHtml(alert.level)}</span> &nbsp; <strong>Score:</strong> ${alert.score}</p>
        <div class="decision">
          <strong>Record analyst decision</strong>
          <textarea id="reviewNotes" maxlength="2000" placeholder="Optional investigation notes"></textarea>
          <div class="decision-actions">
            <button type="button" onclick="review(${alert.id}, 'REVIEWED')">Reviewed</button>
            <button type="button" class="danger" onclick="review(${alert.id}, 'FALSE_POSITIVE')">False positive</button>
            <button type="button" class="warn" onclick="review(${alert.id}, 'ESCALATED')">Escalate</button>
          </div>
        </div>
      </section>

      <section class="detail-card">
        <h3>Transaction details</h3>
        <div class="key-value-grid">
          <div class="key-value"><small>Transaction ID</small>${escapeHtml(transaction.transaction_id || '—')}</div>
          <div class="key-value"><small>Customer</small>${escapeHtml(transaction.customer_id || '—')}</div>
          <div class="key-value"><small>Amount</small>${escapeHtml(transaction.amount ?? '—')}</div>
          <div class="key-value"><small>Final score</small>${escapeHtml(transaction.final_score ?? '—')}</div>
          <div class="key-value"><small>Risk level</small>${escapeHtml(transaction.risk_level || '—')}</div>
          <div class="key-value"><small>Timestamp</small>${escapeHtml(transaction.timestamp ? new Date(transaction.timestamp).toLocaleString() : '—')}</div>
          <div class="key-value"><small>Merchant category</small>${escapeHtml(transaction.merchant_category || '—')}</div>
          <div class="key-value"><small>Location</small>${escapeHtml(transaction.location || '—')}</div>
          <div class="key-value"><small>Device</small>${escapeHtml(transaction.device_id || '—')}</div>
          <div class="key-value"><small>Type</small>${escapeHtml(transaction.transaction_type || '—')}</div>
          <div class="key-value"><small>Account age</small>${escapeHtml(transaction.account_age_days ?? '—')}</div>
          <div class="key-value"><small>Customer average</small>${escapeHtml(transaction.customer_average ?? '—')}</div>
          <div class="key-value"><small>Rule score</small>${escapeHtml(transaction.rule_score ?? '—')}</div>
          <div class="key-value"><small>ML score</small>${escapeHtml(transaction.ml_score ?? '—')}</div>
        </div>
      </section>

      <section class="detail-card">
        <h3>Risk reasons</h3>
        <div class="reason-list">${reasons.length ? reasons.map(reason => `<div class="detail-block">${escapeHtml(reason)}</div>`).join('') : '<div class="detail-block">Model anomaly</div>'}</div>

        <h3>Policy evidence</h3>
        <div class="rag">
          <strong>Retrieved policy explanation</strong><br>
          ${escapeHtml(explanation.explanation || 'No policy explanation available.')}
        </div>
        <ul class="rag-list">
          ${policies.map(policy => `<li><strong>${escapeHtml(policy.policy)}</strong><br>${escapeHtml(policy.text)}</li>`).join('') || '<li>No policy matches were retrieved.</li>'}
        </ul>
      </section>
    `;
  } catch (error) {
    $('#alertDetail').innerHTML = `<div class="detail-card"><h2>Unable to load alert</h2><p>${escapeHtml(error.message)}</p></div>`;
  }
}

async function review(id, action) {
  if (action === 'ESCALATED' && !confirm('Escalate this alert for fraud-operations follow-up?')) return;
  try {
    const notes = $('#reviewNotes')?.value.trim() || null;
    await request(`/alerts/${id}/review`, { method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ action, notes }) });
    alert('Alert updated.');
    window.location.href = 'index.html';
  } catch (error) {
    alert(`Alert update failed: ${error.message}`);
  }
}

window.review = review;
loadAlert();
