"""Probe which employers expose a no-login JSON job board on Greenhouse, Lever, or Ashby."""
import json, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

URLS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{s}/jobs",
    "lever": "https://api.lever.co/v0/postings/{s}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{s}",
}
# employer -> candidate slugs
EMPLOYERS = {
 "Stripe": ["stripe"], "Robinhood": ["robinhood"], "Coinbase": ["coinbase"], "SoFi": ["sofi"],
 "Affirm": ["affirm"], "Chime": ["chime"], "Brex": ["brex"], "Toast": ["toast", "toasttab"],
 "Plaid": ["plaid"], "Ramp": ["ramp"],
 "Mercury": ["mercury"], "Marqeta": ["marqeta"], "Block": ["block", "square"], "Carta": ["carta"],
 "Gusto": ["gusto"], "Wealthfront": ["wealthfront"], "Betterment": ["betterment"], "Upstart": ["upstart"],
 "Addepar": ["addepar"], "Navan": ["navan", "tripactions"], "Bill.com": ["bill", "billcom"],
 "Flywire": ["flywire"], "Remitly": ["remitly"], "Adyen": ["adyen"], "Klarna": ["klarna"],
 "Checkout.com": ["checkoutcom", "checkout"], "Airwallex": ["airwallex"], "Wise": ["wise", "transferwise"],
 "Monzo": ["monzo"], "Nubank": ["nubank"], "Dave": ["dave"], "MoneyLion": ["moneylion"],
 "Opendoor": ["opendoor"], "Lending Club": ["lendingclub"], "Blend": ["blend"], "Mercury Fin": ["mercuryfinancial"],
 "Circle": ["circle"], "Kraken": ["kraken", "kraken-digital-asset-exchange"], "Gemini": ["gemini"],
 "Bitgo": ["bitgo"], "Fireblocks": ["fireblocks"], "Anchorage": ["anchorage"], "Ripple": ["ripple"],
 "Melio": ["melio"], "Navan2": ["navan"], "Rippling": ["rippling"], "Deel": ["deel"], "Pilot": ["pilot"],
 "Tipalti": ["tipalti"], "Paylocity": ["paylocity"], "Sardine": ["sardine"], "Alloy": ["alloy"],
 "Imprint": ["imprint"], "Found": ["found"], "Lithic": ["lithic"], "Modern Treasury": ["moderntreasury"],
 "Oscilar": ["oscilar"], "Column": ["column"], "Public.com": ["public"], "Acorns": ["acorns"],
 "Stash": ["stash"], "Varo": ["varo"], "Current": ["current"], "Greenlight": ["greenlight"],
 "Payoneer": ["payoneer"], "Bolt": ["bolt"], "Zip": ["zip", "ziphq"], "Vanta": ["vanta"],
 "Verition": ["verition"], "Two Sigma": ["twosigma"], "Jane Street": ["janestreet"],
 "Citadel": ["citadel"], "Point72": ["point72"], "Datadog": ["datadog"], "Airbnb": ["airbnb"],
 "Dropbox": ["dropbox"], "Figma": ["figma"], "Notion": ["notion"], "OpenAI": ["openai"],
}

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "job-watcher-probe/0.1", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read()
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return str(type(e).__name__), b""

def count(system, data):
    if system == "greenhouse": return len(data["jobs"])
    if system == "lever": return len(data)
    if system == "ashby": return len(data["jobs"])

def probe(task):
    emp, system, slug = task
    url = URLS[system].format(s=slug)
    status, body = get(url)
    n = None
    if status == 200:
        try: n = count(system, json.loads(body))
        except Exception: status = "200-notjson"
    return dict(employer=emp, system=system, slug=slug, url=url, status=status, count=n)

if __name__ == "__main__":
    tasks = [(e, sy, sl) for e, sls in EMPLOYERS.items() for sl in sls for sy in URLS]
    with ThreadPoolExecutor(12) as ex:
        res = list(ex.map(probe, tasks))
    json.dump(res, open("probe_results.json", "w"), indent=1)
    for r in res:
        if r["status"] == 200 or r["employer"] in ("Stripe","Robinhood","Coinbase","SoFi","Affirm","Chime","Brex","Toast","Plaid","Ramp"):
            print(f'{r["employer"]:16}{r["system"]:11}{r["status"]!s:12}{r["count"]!s:6}{r["url"]}')
