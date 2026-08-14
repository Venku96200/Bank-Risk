const api = location.origin;
let riskChart;

const $ = selector => document.querySelector(selector);
const escapeHtml = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

function setMessage(message, type = '') {
  const node = $('#intakeMessage');
  if (!node) return;
  node.textContent = message;
  node.className = `message ${type}`;
}

async function request(path, options) {
  const response = await fetch(api + path, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

function detail(id) {
  window.location.href = `alert-detail.html?id=${id}`;
}

async function clearAlerts() {
  if (!confirm('Clear all alerts from the dashboard?')) return;
  try {
    const result = await request('/alerts', { method: 'DELETE' });
    setMessage(`${result.cleared} alert${result.cleared === 1 ? '' : 's'} cleared.`, 'success');
    await load();
  } catch (error) {
    setMessage(`Alerts could not be cleared: ${error.message}`, 'error');
  }
}

async function clearTransactions() {
  if (!confirm('This removes all transaction and alert data from the database. Continue?')) return;
  try {
    const result = await request('/transactions', { method: 'DELETE' });
    setMessage(`${result.deleted} transaction${result.deleted === 1 ? '' : 's'} cleared from the database.`, 'success');
    await load();
  } catch (error) {
    setMessage(`Transactions could not be cleared: ${error.message}`, 'error');
  }
}

async function load() {
  try {
    const [summary, trends, alerts] = await Promise.all([request('/dashboard/summary'), request('/dashboard/trends'), request('/alerts')]);
    $('#kpis').innerHTML = Object.entries(summary).map(([key, value]) => `<div><small>${escapeHtml(key.replace('_', ' '))}</small><div class="number">${value}</div></div>`).join('');
    if (riskChart) riskChart.destroy();
    riskChart = new Chart($('#riskChart'), { type: 'doughnut', data: { labels: Object.keys(trends.distribution), datasets: [{ data: Object.values(trends.distribution), backgroundColor: ['#51cf66','#ffd43b','#ff922b','#ff6b6b'] }] }});
    $('#alerts').innerHTML = alerts.map(alert => `<tr><td>${alert.id}</td><td class="${escapeHtml(alert.level)}">${escapeHtml(alert.level)}</td><td>${escapeHtml(alert.status)}</td><td>${alert.score}</td><td><button type="button" onclick="detail(${alert.id})">Inspect</button></td></tr>`).join('') || '<tr><td colspan="5">No high-risk or critical alerts yet.</td></tr>';
    const clearButton = $('#clearAlertsBtn');
    if (clearButton) clearButton.onclick = clearAlerts;
    const clearTransactionsButton = $('#clearTransactionsBtn');
    if (clearTransactionsButton) clearTransactionsButton.onclick = clearTransactions;
  } catch (error) { setMessage(`Dashboard could not load: ${error.message}`, 'error'); }
}

function transactionPayload(form) {
  const data = Object.fromEntries(new FormData(form));
  data.amount = Number(data.amount); data.account_age_days = Number(data.account_age_days);
  return data;
}

$('#transactionForm').addEventListener('submit', async event => {
  event.preventDefault(); const form = event.currentTarget; const button = event.submitter; button.disabled = true; setMessage('Assessing transaction...');
  try {
    const transaction = await request('/transactions', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(transactionPayload(form)) });
    setMessage(`Transaction ${transaction.transaction_id} assessed as ${transaction.risk_level} (score ${transaction.final_score}).`, 'success');
    form.reset(); setDefaultFormValues(); await load();
  } catch (error) { setMessage(`Transaction was not submitted: ${error.message}`, 'error'); }
  finally { button.disabled = false; }
});

$('#bulkForm').addEventListener('submit', async event => {
  event.preventDefault(); const form = event.currentTarget; const button = event.submitter; button.disabled = true; setMessage('Uploading and assessing CSV...');
  try {
    const result = await request('/transactions/bulk', { method: 'POST', body: new FormData(form) });
    setMessage(`${result.created.length} transaction${result.created.length === 1 ? '' : 's'} assessed successfully.`, 'success');
    form.reset(); await load();
  } catch (error) { setMessage(`CSV was not imported: ${error.message}`, 'error'); }
  finally { button.disabled = false; }
});

function setDefaultFormValues() {
  const now = new Date(); now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  $('[name="timestamp"]').value = now.toISOString().slice(0, 16);
  $('[name="transaction_id"]').value = `WEB-${Date.now()}`;
}

setDefaultFormValues();
load();
