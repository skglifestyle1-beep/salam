import requests, re, datetime as dt

URL = "https://www.coinglass.com/futures/LiquidationMap/HIFI"
HEAD = {"User-Agent": "Mozilla/5.0"}
RAW = requests.get(URL, headers=HEAD).text

# Extract 4 values from page HTML/JS
longLow  = float(re.search(r'"longLiquidationBottom":([\d.]+)', RAW).group(1))
longHigh = float(re.search(r'"longLiquidationTop":([\d.]+)', RAW).group(1))
shortLow = float(re.search(r'"shortLiquidationBottom":([\d.]+)', RAW).group(1))
shortHigh= float(re.search(r'"shortLiquidationTop":([\d.]+)', RAW).group(1))

# Build a TradingView-friendly flat line
# Each key=value; separated by semicolons, no braces or quotes
out_line = f"longLow={longLow};longHigh={longHigh};shortLow={shortLow};shortHigh={shortHigh};updated={dt.datetime.utcnow().isoformat()}"

# Write to file that GitHub Pages can host
with open("hifi24h.json", "w") as f:
    f.write(out_line)
