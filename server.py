import os
import random
import time
from typing import Any, Dict, Optional

import requests

DEFAULT_TIMEOUT_MS = 5000
DEFAULT_MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 0.5
MAX_BACKOFF_SECONDS = 8.0


def _error(provider: str, status: Optional[int], message: str, retryable: bool) -> Dict[str, Any]:
    return {
        "provider": provider,
        "status": status,
        "message": message,
        "retryable": retryable,
    }


def _read_timeout_ms(timeout_ms: Optional[int]) -> int:
    if timeout_ms is not None:
        return timeout_ms

    raw = os.getenv("UPSTREAM_TIMEOUT_MS", str(DEFAULT_TIMEOUT_MS)).strip()
    try:
        parsed = int(raw)
    except ValueError:
        return DEFAULT_TIMEOUT_MS

    return parsed if parsed > 0 else DEFAULT_TIMEOUT_MS


def fetch_json(
    url: str,
    provider: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout_ms: Optional[int] = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> Dict[str, Any]:
    """
    Fetch JSON from upstream endpoint.

    Returns:
      - Parsed JSON payload on success.
      - Structured error object on failure:
        {provider, status, message, retryable}
    """
    resolved_timeout_ms = _read_timeout_ms(timeout_ms)
    timeout_seconds = resolved_timeout_ms / 1000.0
    attempts = max(1, max_retries)

    for attempt in range(attempts):
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout_seconds,
            )

            status = response.status_code
            if 200 <= status < 300:
                try:
                    return response.json()
                except ValueError:
                    return _error(
                        provider=provider,
                        status=status,
                        message="Invalid JSON received from upstream provider",
                        retryable=False,
                    )

            if status in (401, 403):
                return _error(
                    provider=provider,
                    status=status,
                    message="Authentication/authorization issue when calling upstream provider",
                    retryable=False,
                )

            retryable = status == 429 or 500 <= status < 600
            message = f"Upstream provider returned HTTP {status}"

            if not retryable or attempt == attempts - 1:
                return _error(
                    provider=provider,
                    status=status,
                    message=message,
                    retryable=retryable,
                )

        except requests.Timeout:
            if attempt == attempts - 1:
                return _error(
                    provider=provider,
                    status=None,
                    message=(
                        f"Timed out after {resolved_timeout_ms}ms while calling upstream provider"
                    ),
                    retryable=True,
                )

        except requests.RequestException as exc:
            # Network-level errors are generally safe to retry with bounded attempts.
            if attempt == attempts - 1:
                return _error(
                    provider=provider,
                    status=None,
                    message=f"Network error while calling upstream provider: {exc}",
                    retryable=True,
                )

        backoff = min(MAX_BACKOFF_SECONDS, BASE_BACKOFF_SECONDS * (2**attempt))
        jitter = random.uniform(0, backoff * 0.25)
        time.sleep(backoff + jitter)

    return _error(
        provider=provider,
        status=None,
        message="Unknown upstream error",
        retryable=False,
    )
