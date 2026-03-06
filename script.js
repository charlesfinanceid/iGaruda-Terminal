const watchlist = [
  { ticker: 'BBCA', price: 10175, chg: 1.35 },
  { ticker: 'BBRI', price: 5475, chg: -0.72 },
  { ticker: 'TLKM', price: 4210, chg: 0.95 },
  { ticker: 'ASII', price: 5075, chg: 0.43 },
  { ticker: 'ANTM', price: 1810, chg: 2.21 },
];

const sectors = [
  ['Banking', '+1.18%', '1.24', 'BBCA / BBRI'],
  ['Energy', '+2.04%', '1.36', 'ADRO / MEDC'],
  ['Mining', '+1.43%', '1.15', 'ANTM / INCO'],
  ['Technology', '-0.34%', '0.82', 'GOTO / BUKA'],
  ['Consumer Goods', '+0.61%', '1.03', 'ICBP / UNVR'],
  ['Telecommunications', '+0.74%', '1.09', 'TLKM / EXCL'],
];

const screenerRows = [
  ['ITMG', '25,450', '8.7', '13.2%', '7.8%', 'Strong'],
  ['BMRI', '6,325', '11.2', '9.5%', '5.1%', 'Positive'],
  ['ADRO', '3,010', '7.9', '11.8%', '6.4%', 'Strong'],
  ['BBTN', '1,490', '6.8', '14.1%', '4.7%', 'Positive'],
  ['AKRA', '1,735', '14.3', '8.2%', '4.2%', 'Neutral'],
];

const newsItems = [
  'IDX reports improved liquidity as banking stocks lead turnover.',
  'Bank Indonesia signals stable policy rate amid resilient rupiah.',
  'Major coal producers announce revised dividend distribution schedules.',
  'OJK releases updated disclosure guidance for listed technology issuers.',
  'Consumer sector earnings previews point to margin normalization in Q3.',
];

const flow = [
  ['Foreign Net Buy', 'IDR 512B'],
  ['Block Trades', 'IDR 1.12T'],
  ['Dominant Side', 'Aggressive Buyers'],
  ['Liquidity Score', '8.4 / 10'],
];

function populate() {
  document.getElementById('watchlist').innerHTML = watchlist
    .map((s) => `<li>${s.ticker} <strong>${s.price.toLocaleString()}</strong> <span class="${s.chg > 0 ? 'up' : 'down'}">${s.chg > 0 ? '+' : ''}${s.chg}%</span></li>`)
    .join('');

  document.getElementById('chartMetrics').innerHTML = [
    ['VWAP', '5,488'],
    ['RSI (14)', '58.3'],
    ['MACD', 'Bullish'],
    ['Bollinger', 'Upper Break'],
  ].map(([k, v]) => `<div class="metric">${k}<strong>${v}</strong></div>`).join('');

  document.getElementById('heatmap').innerHTML = watchlist
    .concat([
      { ticker: 'GOTO', price: 78, chg: -1.2 },
      { ticker: 'MDKA', price: 2390, chg: 1.8 },
      { ticker: 'INDF', price: 6390, chg: 0.9 },
    ])
    .map((s) => {
      const alpha = Math.min(Math.abs(s.chg) / 3, 0.95).toFixed(2);
      const bg = s.chg >= 0 ? `rgba(27, 180, 106, ${alpha})` : `rgba(221, 64, 97, ${alpha})`;
      return `<div class="heat-cell" style="background:${bg}"><strong>${s.ticker}</strong><br>${s.chg > 0 ? '+' : ''}${s.chg}%<br>Vol: ${(Math.random() * 9 + 1).toFixed(1)}M</div>`;
    })
    .join('');

  document.getElementById('sectorTable').innerHTML = sectors
    .map((s) => `<tr><td>${s[0]}</td><td class="${s[1].startsWith('+') ? 'up' : 'down'}">${s[1]}</td><td>${s[2]}</td><td>${s[3]}</td></tr>`)
    .join('');

  document.getElementById('screenerTable').innerHTML = screenerRows
    .map((r) => `<tr><td>${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td><td>${r[3]}</td><td>${r[4]}</td><td>${r[5]}</td></tr>`)
    .join('');

  document.getElementById('newsFeed').innerHTML = newsItems.map((n) => `<li>${n}</li>`).join('');
  document.getElementById('orderFlow').innerHTML = flow.map(([k, v]) => `<div class="metric">${k}<strong>${v}</strong></div>`).join('');

  document.getElementById('tickerTape').textContent =
    'IDX Composite +0.84% • LQ45 +1.12% • Top Gainers: ANTM +2.21%, ADRO +2.04%, BBCA +1.35% • Top Losers: GOTO -1.20%, BBRI -0.72% • USD/IDR 15,520';
}

function bindInteractions() {
  const search = document.getElementById('globalSearch');
  const command = document.getElementById('commandInput');

  search.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const q = search.value.toLowerCase();
      const hit = watchlist.find((s) => s.ticker.toLowerCase() === q) || sectors.find((s) => s[0].toLowerCase().includes(q));
      command.value = hit ? `${search.value} opened in workspace` : 'No exact match, showing broader IDX results';
    }
  });

  command.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const q = command.value.toLowerCase();
      if (q.includes('top gainers')) {
        newsItems.unshift('Command: Top gainers view focused on ANTM, ADRO, MDKA.');
      } else if (q.includes('banking')) {
        document.getElementById('adRatio').textContent = '238 / 152';
      } else if (q.includes('heatmap')) {
        document.getElementById('tickerTape').textContent = 'Heatmap mode enabled • Sector concentration highlights banking and energy leadership';
      }
      populate();
    }
  });
}

function tickClock() {
  const now = new Date();
  document.getElementById('clock').textContent = now.toLocaleTimeString('en-GB', { hour12: false, timeZone: 'Asia/Jakarta' });
}

populate();
bindInteractions();
tickClock();
setInterval(tickClock, 1000);
