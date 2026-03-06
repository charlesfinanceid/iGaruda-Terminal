const appState = {
  lastQuotes: null,
  lastChart: null,
  lastCompany: null,
  lastSuccessfulUpdate: null,
  errorState: {
    quote: null,
    chart: null,
    company: null,
  },
};

function formatTimestamp(date) {
  if (!date) return "";
  return new Intl.DateTimeFormat("id-ID", {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(date);
}

function setRibbonState(mode, message) {
  const dataMode = document.getElementById("dataMode");
  if (!dataMode) return;

  dataMode.classList.remove("ok", "warning", "error");
  dataMode.classList.add(mode);
  dataMode.textContent = message;
}

function renderLastSuccessfulUpdate() {
  const tsNode = document.getElementById("lastSuccessfulUpdate");
  if (!tsNode) return;

  if (!appState.lastSuccessfulUpdate) {
    tsNode.textContent = "";
    return;
  }

  tsNode.textContent = `Last successful update: ${formatTimestamp(appState.lastSuccessfulUpdate)}`;
}

function renderQuotePanel(quotes) {
  const node = document.getElementById("watchlistPanel");
  if (!node || !quotes) return;
  node.textContent = JSON.stringify(quotes);
}

function renderChartPanel(chart) {
  const node = document.getElementById("chartPanel");
  if (!node || !chart) return;
  node.textContent = JSON.stringify(chart);
}

function renderCompanyPanel(company) {
  const node = document.getElementById("companySnapshotPanel");
  if (!node || !company) return;
  node.textContent = JSON.stringify(company);
}

function renderUnavailable(panel, message) {
  // Tidak lagi menghapus semua panel; hanya memperbarui panel yang gagal.
  if (panel === "quote") {
    const quoteError = document.getElementById("quoteError");
    if (quoteError) quoteError.textContent = message;

    if (appState.lastQuotes) {
      renderQuotePanel(appState.lastQuotes);
    }
  }

  if (panel === "chart") {
    const chartError = document.getElementById("chartError");
    if (chartError) chartError.textContent = message;

    if (appState.lastChart) {
      renderChartPanel(appState.lastChart);
    }
  }

  if (panel === "company") {
    const companyError = document.getElementById("companyError");
    if (companyError) companyError.textContent = message;

    if (appState.lastCompany) {
      renderCompanyPanel(appState.lastCompany);
    }
  }

  const ribbonMessage = `Sebagian data tidak tersedia: ${message}`;
  setRibbonState("error", ribbonMessage);
  renderLastSuccessfulUpdate();
}

function handleQuotesSuccess(quotes) {
  appState.lastQuotes = quotes;
  appState.errorState.quote = null;
  appState.lastSuccessfulUpdate = new Date();

  renderQuotePanel(quotes);
  setRibbonState("ok", "Data mode: realtime");
  renderLastSuccessfulUpdate();
}

function handleChartSuccess(chart) {
  appState.lastChart = chart;
  appState.errorState.chart = null;
  appState.lastSuccessfulUpdate = new Date();

  renderChartPanel(chart);
  setRibbonState("ok", "Data mode: realtime");
  renderLastSuccessfulUpdate();
}

function handleCompanySuccess(company) {
  appState.lastCompany = company;
  appState.errorState.company = null;
  appState.lastSuccessfulUpdate = new Date();

  renderCompanyPanel(company);
  setRibbonState("ok", "Data mode: realtime");
  renderLastSuccessfulUpdate();
}

function handleQuotesError(error) {
  appState.errorState.quote = error;
  renderUnavailable("quote", error.message || "Watchlist/heatmap gagal dimuat.");
}

function handleChartError(error) {
  appState.errorState.chart = error;
  renderUnavailable("chart", error.message || "Chart gagal dimuat.");
}

function handleCompanyError(error) {
  appState.errorState.company = error;
  renderUnavailable("company", error.message || "Snapshot perusahaan gagal dimuat.");
}

if (typeof module !== "undefined") {
  module.exports = {
    appState,
    renderUnavailable,
    handleQuotesSuccess,
    handleChartSuccess,
    handleCompanySuccess,
    handleQuotesError,
    handleChartError,
    handleCompanyError,
  };
}
