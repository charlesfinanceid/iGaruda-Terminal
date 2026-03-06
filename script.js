const TICKERS = ['BBCA.JK', 'BBRI.JK', 'BMRI.JK', 'TLKM.JK', 'ASII.JK', 'ANTM.JK', 'ADRO.JK', 'GOTO.JK'];

const sectors = [
  ['Banking', '-', '-', 'BBCA / BBRI / BMRI'],
  ['Energy', '-', '-', 'ADRO / MEDC'],
  ['Mining', '-', '-', 'ANTM / INCO'],
  ['Technology', '-', '-', 'GOTO / BUKA'],
  ['Consumer Goods', '-', '-', 'ICBP / UNVR'],
  ['Telecommunications', '-', '-', 'TLKM / EXCL'],
];

function fmtNumber(n) {
  return Number.isFinite(n) ? n.toLocaleString('id-ID') : '-';
}

function colorClass(num) {
  return num >= 0 ? 'up' : 'down';
}

async function fetchJSON(url) {
  const r = await fetch(url);
  const payload = await r.json();
  if (!r.ok) {
    throw new Error(payload.error || `HTTP ${r.status}`);
  }
  return payload;
}

function renderUnavailable(message) {
  document.getElementById('watchlist').innerHTML = `<li>Live feed unavailable</li>`;
  document.getElementById('heatmap').innerHTML = `<div class="heat-cell">${message}</div>`;
  document.getElementById('tickerTape').textContent = `LIVE FEED ERROR • ${message}`;
  document.getElementById('dataMode').textContent = 'LIVE FEED ERROR';
  document.getElementById('dataSource').textContent = message;
}

function renderQuotes(payload) {
  const results = payload.results || [];
  if (!results.length) {
    renderUnavailable('No data returned from upstream.');
    return;
  }

  const top = results.slice(0, 5);
  document.getElementById('watchlist').innerHTML = top.map((s) => {
    const chg = s.regularMarketChangePercent ?? 0;
    return `<li>${s.symbol.replace('.JK', '')} <strong>${fmtNumber(s.regularMarketPrice)}</strong> <span class="${colorClass(chg)}">${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%</span></li>`;
  }).join('');

  document.getElementById('heatmap').innerHTML = results.map((s) => {
    const chg = s.regularMarketChangePercent ?? 0;
    const alpha = Math.min(Math.abs(chg) / 3, 0.95).toFixed(2);
    const bg = chg >= 0 ? `rgba(27, 180, 106, ${alpha})` : `rgba(221, 64, 97, ${alpha})`;
    return `<div class="heat-cell" style="background:${bg}"><strong>${s.symbol.replace('.JK', '')}</strong><br>${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%<br>Vol: ${fmtNumber(s.regularMarketVolume)}</div>`;
  }).join('');

  const gainers = [...results].sort((a, b) => (b.regularMarketChangePercent ?? 0) - (a.regularMarketChangePercent ?? 0)).slice(0, 3);
  const losers = [...results].sort((a, b) => (a.regularMarketChangePercent ?? 0) - (b.regularMarketChangePercent ?? 0)).slice(0, 2);
  document.getElementById('tickerTape').textContent = `Mode: ${payload.mode.toUpperCase()} • Source: ${payload.source} • Top Gainers: ${gainers.map((g) => `${g.symbol.replace('.JK', '')} ${g.regularMarketChangePercent >= 0 ? '+' : ''}${(g.regularMarketChangePercent ?? 0).toFixed(2)}%`).join(', ')} • Top Losers: ${losers.map((l) => `${l.symbol.replace('.JK', '')} ${(l.regularMarketChangePercent ?? 0).toFixed(2)}%`).join(', ')}`;

  document.getElementById('dataMode').textContent = 'LIVE DATA';
  document.getElementById('dataSource').textContent = payload.source;
}

function renderSectorTable() {
  document.getElementById('sectorTable').innerHTML = sectors
    .map((s) => `<tr><td>${s[0]}</td><td>${s[1]}</td><td>${s[2]}</td><td>${s[3]}</td></tr>`)
    .join('');
}

async function renderChart(symbol = 'BBCA.JK') {
  const payload = await fetchJSON(`/api/chart/${encodeURIComponent(symbol)}?range=1d&interval=1m`);
  const result = payload?.data?.chart?.result?.[0];
  const points = result?.indicators?.quote?.[0]?.close?.filter((x) => Number.isFinite(x)) ?? [];
  if (!points.length) throw new Error('No valid chart points from upstream.');

  const min = Math.min(...points);
  const max = Math.max(...points);
  const norm = points.map((p, i) => {
    const x = (i / (points.length - 1 || 1)) * 600;
    const y = 200 - ((p - min) / ((max - min) || 1)) * 150;
    return `${x.toFixed(1)},${(y + 10).toFixed(1)}`;
  }).join(' ');

  document.getElementById('chartLine').setAttribute('points', norm);
  document.getElementById('chartMetrics').innerHTML = [
    ['Last', points[points.length - 1]?.toFixed(2) || '-'],
    ['High', max.toFixed(2)],
    ['Low', min.toFixed(2)],
    ['Points', String(points.length)],
  ].map(([k, v]) => `<div class="metric">${k}<strong>${v}</strong></div>`).join('');
}

function tickClock() {
  const now = new Date();
  document.getElementById('clock').textContent = now.toLocaleTimeString('en-GB', { hour12: false, timeZone: 'Asia/Jakarta' });
}

async function refreshAll() {
  try {
    const quotes = await fetchJSON(`/api/quotes?symbols=${encodeURIComponent(TICKERS.join(','))}`);
    renderQuotes(quotes);
    await renderChart((quotes.results?.[0]?.symbol) || 'BBCA.JK');
  } catch (err) {
    renderUnavailable(err.message);
  }
}

function bindInteractions() {
  const search = document.getElementById('globalSearch');
  const command = document.getElementById('commandInput');

  search.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
      const input = search.value.trim().toUpperCase();
      const symbol = input.endsWith('.JK') ? input : `${input}.JK`;
      command.value = `${symbol} chart loaded`;
      try {
        await renderChart(symbol);
      } catch (err) {
        renderUnavailable(err.message);
      }
    }
  });

  command.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') await refreshAll();
  });
}

renderSectorTable();
bindInteractions();
refreshAll();
tickClock();
setInterval(tickClock, 1000);
setInterval(refreshAll, 1000);
