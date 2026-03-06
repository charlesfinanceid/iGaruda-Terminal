const DEFAULT_TICKERS = ['BBCA.JK', 'BBRI.JK', 'BMRI.JK', 'TLKM.JK', 'ASII.JK', 'ANTM.JK', 'ADRO.JK', 'GOTO.JK', 'ICBP.JK', 'UNVR.JK'];
const QUOTE_REFRESH_MS = 1000;
const CHART_REFRESH_MS = 15000;

let currentSymbol = 'BBCA.JK';
let lastChartFetch = 0;
let lastQuotes = [];

function fmtNumber(n) {
  return Number.isFinite(n) ? n.toLocaleString('id-ID') : '-';
}

function fmtCompact(n) {
  return Number.isFinite(n)
    ? Intl.NumberFormat('id-ID', { notation: 'compact', maximumFractionDigits: 1 }).format(n)
    : '-';
}

function colorClass(num) {
  return num >= 0 ? 'up' : 'down';
}

async function fetchJSON(url) {
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

function renderUnavailable(message) {
  document.getElementById('watchlist').innerHTML = `<li>LIVE FEED ERROR: ${message}</li>`;
  document.getElementById('heatmap').innerHTML = `<div class="heat-cell danger">${message}</div>`;
  document.getElementById('tickerTape').textContent = `LIVE FEED ERROR • ${message}`;
  document.getElementById('dataMode').textContent = 'LIVE FEED ERROR';
  document.getElementById('dataSource').textContent = 'Unavailable';
  document.getElementById('marketStatus').textContent = 'Upstream Failure';
}

function buildSectorRows(results) {
  const sectors = new Map();
  for (const q of results) {
    const sector = q.sector || 'Unclassified';
    const entry = sectors.get(sector) || { sum: 0, count: 0, leaders: [] };
    const change = q.regularMarketChangePercent ?? 0;
    entry.sum += change;
    entry.count += 1;
    entry.leaders.push([q.symbol, change]);
    sectors.set(sector, entry);
  }

  return [...sectors.entries()].slice(0, 8).map(([name, data]) => {
    const avg = data.count ? data.sum / data.count : 0;
    const leaders = data.leaders.sort((a, b) => b[1] - a[1]).slice(0, 2).map((v) => v[0].replace('.JK', '')).join(' / ');
    return `<tr><td>${name}</td><td class="${colorClass(avg)}">${avg >= 0 ? '+' : ''}${avg.toFixed(2)}%</td><td>${leaders || '-'}</td><td>${Math.abs(avg).toFixed(2)}</td></tr>`;
  }).join('');
}

function renderQuotes(payload) {
  const results = payload.results || [];
  if (!results.length) {
    renderUnavailable('No data returned from upstream');
    return;
  }

  lastQuotes = results;
  document.getElementById('marketStatus').textContent = 'Live Monitoring';
  document.getElementById('dataMode').textContent = payload.mode === 'live' ? 'LIVE DATA' : payload.mode;
  document.getElementById('dataSource').textContent = payload.source;

  const watchlist = results.slice(0, 10).map((item) => {
    const change = item.regularMarketChangePercent ?? 0;
    return `<li>${item.symbol.replace('.JK', '')} <strong>${fmtNumber(item.regularMarketPrice)}</strong> <span class="${colorClass(change)}">${change >= 0 ? '+' : ''}${change.toFixed(2)}%</span></li>`;
  }).join('');
  document.getElementById('watchlist').innerHTML = watchlist;

  const heatmapHtml = results.map((item) => {
    const change = item.regularMarketChangePercent ?? 0;
    const alpha = Math.min(Math.abs(change) / 4, 0.9);
    const bg = change >= 0 ? `rgba(30,184,120,${alpha})` : `rgba(227,81,105,${alpha})`;
    return `<div class="heat-cell" style="background:${bg}"><strong>${item.symbol.replace('.JK', '')}</strong><br>${change >= 0 ? '+' : ''}${change.toFixed(2)}%<br>Vol ${fmtCompact(item.regularMarketVolume)}</div>`;
  }).join('');
  document.getElementById('heatmap').innerHTML = heatmapHtml;

  const sortedUp = [...results].sort((a, b) => (b.regularMarketChangePercent ?? 0) - (a.regularMarketChangePercent ?? 0));
  const topMoversHtml = sortedUp.slice(0, 3).concat(sortedUp.slice(-2)).map((item) => {
    const change = item.regularMarketChangePercent ?? 0;
    return `<li>${item.symbol.replace('.JK', '')} <strong class="${colorClass(change)}">${change >= 0 ? '+' : ''}${change.toFixed(2)}%</strong> <small>Vol ${fmtCompact(item.regularMarketVolume)}</small></li>`;
  }).join('');
  document.getElementById('topMovers').innerHTML = topMoversHtml;

  const adv = results.filter((q) => (q.regularMarketChangePercent ?? 0) > 0).length;
  const dec = results.filter((q) => (q.regularMarketChangePercent ?? 0) < 0).length;
  const unchanged = results.length - adv - dec;
  const totalVolume = results.reduce((acc, q) => acc + (q.regularMarketVolume || 0), 0);

  document.getElementById('breadthList').innerHTML = [
    `<li>Advance / Decline: <strong>${adv} / ${dec}</strong></li>`,
    `<li>Unchanged: <strong>${unchanged}</strong></li>`,
    `<li>AD Ratio: <strong>${dec === 0 ? '∞' : (adv / dec).toFixed(2)}</strong></li>`,
    `<li>Total Sample Volume: <strong>${fmtCompact(totalVolume)}</strong></li>`,
  ].join('');

  document.getElementById('flowList').innerHTML = [
    `<li>Net buying pressure: <strong class="${adv >= dec ? 'up' : 'down'}">${adv >= dec ? 'Positive' : 'Negative'}</strong></li>`,
    `<li>Most active: <strong>${[...results].sort((a, b) => (b.regularMarketVolume ?? 0) - (a.regularMarketVolume ?? 0))[0]?.symbol.replace('.JK', '') || '-'}</strong></li>`,
    `<li>High beta proxy: <strong>${sortedUp[0]?.symbol.replace('.JK', '') || '-'}</strong></li>`,
    `<li>Defensive laggard: <strong>${sortedUp[sortedUp.length - 1]?.symbol.replace('.JK', '') || '-'}</strong></li>`,
  ].join('');

  document.getElementById('screenerBody').innerHTML = [...results]
    .filter((q) => (q.marketCap || 0) > 10_000_000_000)
    .sort((a, b) => (b.regularMarketChangePercent ?? 0) - (a.regularMarketChangePercent ?? 0))
    .slice(0, 7)
    .map((q) => {
      const change = q.regularMarketChangePercent ?? 0;
      return `<tr><td>${q.symbol.replace('.JK', '')}</td><td>${fmtNumber(q.regularMarketPrice)}</td><td class="${colorClass(change)}">${change >= 0 ? '+' : ''}${change.toFixed(2)}%</td><td>${fmtCompact(q.regularMarketVolume)}</td></tr>`;
    }).join('');

  document.getElementById('sectorTable').innerHTML = buildSectorRows(results);

  const topGainers = sortedUp.slice(0, 3).map((q) => `${q.symbol.replace('.JK', '')} ${q.regularMarketChangePercent >= 0 ? '+' : ''}${(q.regularMarketChangePercent ?? 0).toFixed(2)}%`).join(' | ');
  const topLosers = sortedUp.slice(-3).map((q) => `${q.symbol.replace('.JK', '')} ${(q.regularMarketChangePercent ?? 0).toFixed(2)}%`).join(' | ');
  document.getElementById('tickerTape').textContent = `LIVE • ${payload.source} • TOP GAINERS ${topGainers} • TOP LOSERS ${topLosers}`;
}

async function renderChart(symbol) {
  const payload = await fetchJSON(`/api/chart/${encodeURIComponent(symbol)}?range=1d&interval=1m`);
  const result = payload?.data?.chart?.result?.[0];
  const closes = result?.indicators?.quote?.[0]?.close?.filter((v) => Number.isFinite(v)) ?? [];
  if (!closes.length) {
    throw new Error('No chart points available');
  }

  const low = Math.min(...closes);
  const high = Math.max(...closes);
  const points = closes.map((p, i) => {
    const x = (i / (closes.length - 1 || 1)) * 600;
    const y = 210 - ((p - low) / ((high - low) || 1)) * 170;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  document.getElementById('chartLine').setAttribute('points', points);
  document.getElementById('chartTitle').textContent = `Price Chart — ${symbol}`;

  const last = closes[closes.length - 1];
  const first = closes[0];
  const change = ((last - first) / (first || 1)) * 100;

  document.getElementById('chartMetrics').innerHTML = [
    ['Last', fmtNumber(last)],
    ['Day High', fmtNumber(high)],
    ['Day Low', fmtNumber(low)],
    ['Intraday %', `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`],
  ].map(([k, v]) => `<div class="metric">${k}<strong class="${k === 'Intraday %' ? colorClass(change) : ''}">${v}</strong></div>`).join('');

  lastChartFetch = Date.now();
}

async function renderCompanySnapshot(symbol) {
  try {
    const payload = await fetchJSON(`/api/company/${encodeURIComponent(symbol)}`);
    const d = payload.company;
    document.getElementById('companySnapshot').innerHTML = [
      `<li>Symbol: <strong>${d.symbol}</strong></li>`,
      `<li>Name: <strong>${d.name || '-'}</strong></li>`,
      `<li>Price: <strong>${fmtNumber(d.price)}</strong></li>`,
      `<li>Market Cap: <strong>${fmtCompact(d.marketCap)}</strong></li>`,
      `<li>52W Range: <strong>${fmtNumber(d.fiftyTwoWeekLow)} - ${fmtNumber(d.fiftyTwoWeekHigh)}</strong></li>`,
      `<li>Volume: <strong>${fmtCompact(d.volume)}</strong></li>`,
    ].join('');
  } catch (err) {
    document.getElementById('companySnapshot').innerHTML = `<li>Company snapshot unavailable: ${err.message}</li>`;
  }
}

async function refreshQuotes() {
  const payload = await fetchJSON(`/api/quotes?symbols=${encodeURIComponent(DEFAULT_TICKERS.join(','))}`);
  renderQuotes(payload);
}

async function refreshAll() {
  await refreshQuotes();
  if (Date.now() - lastChartFetch > CHART_REFRESH_MS) {
    await renderChart(currentSymbol);
  }
}

function tickClock() {
  const now = new Date();
  document.getElementById('clock').textContent = now.toLocaleTimeString('en-GB', { hour12: false, timeZone: 'Asia/Jakarta' });
}

function renderNews() {
  document.getElementById('newsFeed').innerHTML = [
    'IDX: Pantau keterbukaan informasi emiten melalui website resmi BEI.',
    'OJK: Cek pembaruan regulasi pasar modal untuk compliance.',
    'Bank Indonesia: Review data makro terbaru untuk bias sektor.',
    'Issuer calendar: monitor jadwal earnings, dividen, dan corporate action.',
  ].map((i) => `<li>${i}</li>`).join('');
}

async function setSymbol(symbol) {
  currentSymbol = symbol.endsWith('.JK') ? symbol : `${symbol}.JK`;
  await renderChart(currentSymbol);
  await renderCompanySnapshot(currentSymbol);
}

function bindInteractions() {
  const search = document.getElementById('globalSearch');
  const command = document.getElementById('commandInput');

  search.addEventListener('keydown', async (event) => {
    if (event.key !== 'Enter') return;
    const symbol = search.value.trim().toUpperCase();
    if (!symbol) return;
    try {
      await setSymbol(symbol);
      command.value = `${symbol} chart`;
    } catch (err) {
      renderUnavailable(err.message);
    }
  });

  command.addEventListener('keydown', async (event) => {
    if (event.key !== 'Enter') return;
    const raw = command.value.trim().toLowerCase();
    try {
      if (raw.includes('top gainers')) {
        document.getElementById('topMovers').scrollIntoView({ behavior: 'smooth' });
        return;
      }
      if (raw.includes('refresh')) {
        await refreshAll();
        return;
      }
      const token = raw.split(' ')[0].toUpperCase();
      if (token.length >= 4) {
        await setSymbol(token);
      }
    } catch (err) {
      renderUnavailable(err.message);
    }
  });
}

async function bootstrap() {
  renderNews();
  tickClock();
  bindInteractions();
  document.getElementById('refreshInfo').textContent = `${QUOTE_REFRESH_MS / 1000}s quote / ${CHART_REFRESH_MS / 1000}s chart`;

  try {
    await refreshAll();
    await renderCompanySnapshot(currentSymbol);
  } catch (err) {
    renderUnavailable(err.message);
  }

  setInterval(tickClock, 1000);
  setInterval(async () => {
    try {
      await refreshAll();
    } catch (err) {
      renderUnavailable(err.message);
    }
  }, QUOTE_REFRESH_MS);
}

bootstrap();
