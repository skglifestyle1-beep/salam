import requests, json, re, datetime as dt

URL = "https://www.coinglass.com/futures/LiquidationMap/HIFI"
HEAD = {"User-Agent": "Mozilla/5.0"}
RAW = requests.get(URL, headers=HEAD).text

# regex extract the 4 numbers (they're in a JS object)
longLow  = float(re.search(r'"longLiquidationBottom":([\d.]+)', RAW).group(1))
longHigh = float(re.search(r'"longLiquidationTop":([\d.]+)', RAW).group(1))
shortLow = float(re.search(r'"shortLiquidationBottom":([\d.]+)', RAW).group(1))
shortHigh= float(re.search(r'"shortLiquidationTop":([\d.]+)', RAW).group(1))

out = {
    "longLow": longLow,
    "longHigh": longHigh,
    "shortLow": shortLow,
    "shortHigh": shortHigh,
    "updated": dt.datetime.utcnow().isoformat()
}

with open("hifi24h.json", "w") as f:
    json.dump(out, f)
