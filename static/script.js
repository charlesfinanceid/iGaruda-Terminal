const statusEl = document.getElementById('status');
const quoteEl = document.getElementById('quote');
const refreshBtn = document.getElementById('refreshBtn');

async function loadQuote() {
  statusEl.textContent = 'Loading quote...';
  try {
    const resp = await fetch('/api/quote');
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || 'Unknown error');

    quoteEl.textContent = data.data.content || JSON.stringify(data.data);
    statusEl.textContent = `Source: ${data.source}, age: ${data.age_ms}ms`;
  } catch (err) {
    statusEl.textContent = `Failed to load quote: ${err.message}`;
  }
}

refreshBtn.addEventListener('click', loadQuote);
loadQuote();
