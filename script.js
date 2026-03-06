(() => {
  const NORMAL_QUOTE_INTERVAL_MS = 4000; // safer default 3-5 detik
  const MAX_QUOTE_INTERVAL_MS = 30000;
  const BACKOFF_MULTIPLIER = 2;
  const JITTER_MS = 250;
  const CHART_FRESH_TTL_MS = 60_000;

  const state = {
    symbol: null,
    quoteTimer: null,
    quoteIntervalMs: NORMAL_QUOTE_INTERVAL_MS,
    consecutiveErrors: 0,
    lastQuoteAt: 0,
    chart: {
      symbol: null,
      fetchedAt: 0,
      data: null,
    },
  };

  const refreshInfoEl = document.querySelector('#refreshInfo');

  function setRefreshInfo(message) {
    if (!refreshInfoEl) return;
    refreshInfoEl.textContent = message;
  }

  function buildRefreshMessage() {
    const mode = state.consecutiveErrors > 0 ? 'backoff aktif' : 'normal';
    const sec = (state.quoteIntervalMs / 1000).toFixed(1);
    const errors = state.consecutiveErrors;
    const last = state.lastQuoteAt
      ? `, update terakhir ${Math.round((Date.now() - state.lastQuoteAt) / 1000)} dtk lalu`
      : '';

    return `Refresh quote: ${sec} dtk (${mode}, error beruntun: ${errors}${last})`;
  }

  function updateRefreshInfo() {
    setRefreshInfo(buildRefreshMessage());
  }

  function scheduleNextQuotePoll() {
    clearTimeout(state.quoteTimer);
    const jitter = Math.floor(Math.random() * JITTER_MS);
    state.quoteTimer = setTimeout(fetchQuote, state.quoteIntervalMs + jitter);
    updateRefreshInfo();
  }

  function onPollSuccess() {
    state.lastQuoteAt = Date.now();
    if (state.consecutiveErrors > 0 || state.quoteIntervalMs !== NORMAL_QUOTE_INTERVAL_MS) {
      state.consecutiveErrors = 0;
      state.quoteIntervalMs = NORMAL_QUOTE_INTERVAL_MS;
    }
  }

  function onPollError() {
    state.consecutiveErrors += 1;
    state.quoteIntervalMs = Math.min(
      MAX_QUOTE_INTERVAL_MS,
      Math.max(NORMAL_QUOTE_INTERVAL_MS, state.quoteIntervalMs * BACKOFF_MULTIPLIER),
    );
  }

  async function fetchJson(url) {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  }

  function renderQuote(data) {
    const quoteEl = document.querySelector('#quoteValue');
    if (quoteEl && data) {
      quoteEl.textContent = `${data.price ?? '-'} (${data.symbol ?? state.symbol ?? '-'})`;
    }
  }

  function renderChart(data) {
    const chartEl = document.querySelector('#chartData');
    if (chartEl) {
      chartEl.textContent = JSON.stringify(data ?? {}, null, 2);
    }
  }

  async function fetchQuote() {
    if (!state.symbol) {
      scheduleNextQuotePoll();
      return;
    }

    try {
      const data = await fetchJson(`/api/quote?symbol=${encodeURIComponent(state.symbol)}`);
      renderQuote(data);
      onPollSuccess();
    } catch (error) {
      console.error('Gagal fetch quote:', error);
      onPollError();
    } finally {
      scheduleNextQuotePoll();
    }
  }

  function chartIsFreshForSymbol(symbol) {
    if (!state.chart.data) return false;
    if (state.chart.symbol !== symbol) return false;
    return Date.now() - state.chart.fetchedAt < CHART_FRESH_TTL_MS;
  }

  async function ensureChartData(symbol) {
    if (!symbol) return;

    if (chartIsFreshForSymbol(symbol)) {
      renderChart(state.chart.data);
      return;
    }

    const data = await fetchJson(`/api/chart?symbol=${encodeURIComponent(symbol)}`);
    state.chart = {
      symbol,
      fetchedAt: Date.now(),
      data,
    };
    renderChart(data);
  }

  async function setSymbol(symbol) {
    const normalized = (symbol || '').trim().toUpperCase();
    if (!normalized) return;

    const symbolChanged = normalized !== state.symbol;
    state.symbol = normalized;

    if (symbolChanged) {
      // Immediate quote refresh on symbol change
      clearTimeout(state.quoteTimer);
      await fetchQuote();
    }

    try {
      await ensureChartData(normalized);
    } catch (error) {
      console.error('Gagal fetch chart:', error);
    }
  }

  function bindUI() {
    const symbolInput = document.querySelector('#symbolInput');
    const applyBtn = document.querySelector('#applySymbol');

    if (applyBtn && symbolInput) {
      applyBtn.addEventListener('click', () => setSymbol(symbolInput.value));
    }

    if (symbolInput) {
      symbolInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
          setSymbol(symbolInput.value);
        }
      });
    }
  }

  function bootstrap() {
    bindUI();

    const initialSymbolInput = document.querySelector('#symbolInput');
    const initialSymbol = initialSymbolInput?.value?.trim();
    if (initialSymbol) {
      setSymbol(initialSymbol);
    }

    scheduleNextQuotePoll();
  }

  bootstrap();
})();
