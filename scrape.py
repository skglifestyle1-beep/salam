import requests
import json
import re
import datetime as dt
import logging
import sys
import os
import tempfile
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL = "https://www.coinglass.com/futures/LiquidationMap/HIFI"
HEAD = {"User-Agent": "Mozilla/5.0"}
OUTPUT_FILE = "hifi24h.json"
REQUEST_TIMEOUT = (5, 15)  # (connect, read) seconds

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")


def requests_session_with_retries(total_retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]),
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def extract_floats(raw: str) -> dict:
    patterns = {
        "longLow": r'"longLiquidationBottom":\s*([\d.]+)',
        "longHigh": r'"longLiquidationTop":\s*([\d.]+)',
        "shortLow": r'"shortLiquidationBottom":\s*([\d.]+)',
        "shortHigh": r'"shortLiquidationTop":\s*([\d.]+)',
    }

    result = {}
    for key, pat in patterns.items():
        m = re.search(pat, raw)
        if not m:
            raise ValueError(f"Could not find pattern for {key}: {pat}")
        try:
            result[key] = float(m.group(1))
        except ValueError as e:
            raise ValueError(f"Failed to parse float for {key}: {m.group(1)}") from e

    return result


def atomic_write_json(path: str, data: dict) -> None:
    dirpath = os.path.dirname(os.path.abspath(path)) or "."
    # Use NamedTemporaryFile in same directory to ensure atomic replace works across filesystems
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", dir=dirpath)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=None)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)  # atomic on most POSIX systems
    except Exception:
        # If something goes wrong, ensure temp file is removed
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise


def main() -> int:
    logging.info("Starting scrape of %s", URL)
    session = requests_session_with_retries()

    try:
        resp = session.get(URL, headers=HEAD, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error("HTTP request failed: %s", e)
        return 2

    raw = resp.text

    try:
        values = extract_floats(raw)
    except ValueError as e:
        logging.error("Failed to extract values: %s", e)
        return 3

    out = {
        "longLow": values["longLow"],
        "longHigh": values["longHigh"],
        "shortLow": values["shortLow"],
        "shortHigh": values["shortHigh"],
        "updated": dt.datetime.utcnow().isoformat() + "Z",
    }

    try:
        atomic_write_json(OUTPUT_FILE, out)
    except Exception as e:
        logging.error("Failed to write output file %s: %s", OUTPUT_FILE, e)
        return 4

    logging.info("Wrote %s successfully (updated=%s)", OUTPUT_FILE, out["updated"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
