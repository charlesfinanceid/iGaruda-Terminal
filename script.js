function ensureProviderBadge() {
  let badge = document.getElementById("provider-badge");
  if (!badge) {
    badge = document.createElement("div");
    badge.id = "provider-badge";
    badge.style.cssText = "position:fixed;right:12px;bottom:12px;padding:6px 10px;background:#111;color:#fff;border-radius:999px;font:12px/1.2 sans-serif;z-index:9999;";
    document.body.appendChild(badge);
  }
  return badge;
}

function setProviderBadge(meta) {
  const badge = ensureProviderBadge();
  const provider = meta?.provider || "unavailable";
  const fallback = meta?.fallbackUsed ? " (fallback)" : "";
  const cached = meta?.cached ? " • cache" : "";
  badge.textContent = `Source: ${provider}${fallback}${cached}`;
}

async function fetchQuotes(symbols = ["AAPL", "MSFT"]) {
  const query = encodeURIComponent(symbols.join(","));
  const response = await fetch(`/api/quotes?symbols=${query}`);
  const result = await response.json();
  setProviderBadge(result.meta);
  return result;
}

async function fetchChart(ticker) {
  const response = await fetch(`/api/chart/${encodeURIComponent(ticker)}`);
  const result = await response.json();
  setProviderBadge(result.meta);
  return result;
}

async function fetchCompany(ticker) {
  const response = await fetch(`/api/company/${encodeURIComponent(ticker)}`);
  const result = await response.json();
  setProviderBadge(result.meta);
  return result;
}
