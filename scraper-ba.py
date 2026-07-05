#!/usr/bin/env python3
"""
Google Maps Scraper using BrowserAct CLI
Scrapes: name, rating, category, address, phone, website
"""
import subprocess, json, csv, os, sys, time, re
from urllib.parse import quote

SESSION = "gmaps"
BROWSER_ID = "direct_local_104111605563785390"
OUT_DIR = "hasil-scrape"
CLEAN_RE = re.compile(r'[^\x20-\x7E\xC0-\xFF\xA0-\xFF.,\w\s\(\)\-]')

def ba(*args, timeout=120):
    cmd = ["browser-act", "--session", SESSION] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        err = r.stderr.strip()[:300]
        if err:
            print(f"    [BA ERR] {' '.join(args[:2])}: {err}")
        return None
    return r.stdout.strip()

def ba_raw(*args, timeout=30):
    cmd = ["browser-act"] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        err = r.stderr.strip()[:200]
        if err and 'not found' not in err:
            print(f"    [BA ERR] {' '.join(args[:2])}: {err}")
    return r.stdout.strip() if r.returncode == 0 else None

def open_session():
    print("Opening Chrome session via BrowserAct...")
    ba_raw("session", "close", SESSION, timeout=5)
    # Kill stale Chrome on debugging port
    import subprocess as sp
    sp.run("fuser -k 9222/tcp 2>/dev/null", shell=True, timeout=5)
    time.sleep(1)
    for attempt in range(3):
        r = ba_raw("--session", SESSION, "browser", "open", BROWSER_ID,
                   "https://www.google.com/maps", "--allow-restart-chrome", timeout=60)
        if r:
            print("  Session ready.")
            return
        print(f"  Retry {attempt+1}...")
        time.sleep(3)
    print("  Failed to open session!")
    sys.exit(1)

def close_session():
    ba_raw("session", "close", SESSION, timeout=10)
    print("Session closed.")

def eval_js(js, timeout=120):
    return ba("eval", js, timeout=timeout)

def crawl_search(query, max_results=50):
    url = f"https://www.google.com/maps/search/{quote(query)}/"
    print(f"  Navigate to search...")
    ba("navigate", url, timeout=20)
    time.sleep(5)

    count = eval_js("document.querySelectorAll('[role=\"feed\"] > div > div').length", timeout=10)
    print(f"  Initial items: {count or 0}")

    print("  Scrolling feed...")
    eval_js("""
    (async () => {
      const feed = document.querySelector('[role="feed"]');
      if (!feed) return;
      let prev = 0;
      for (let i = 0; i < 25; i++) {
        feed.scrollTop = feed.scrollHeight;
        await new Promise(r => setTimeout(r, 1200));
        if (feed.scrollTop === prev) break;
        prev = feed.scrollTop;
      }
    })()
    """, timeout=90)

    result = eval_js(f"""
    (async () => {{
      await new Promise(r => setTimeout(r, 1000));
      const items = [];
      const seen = new Set();
      document.querySelectorAll('[role="feed"] > div > div').forEach(el => {{
        const a = el.querySelector('a');
        if (!a) return;
        const name = a.textContent.trim();
        if (!name || seen.has(name)) return;
        seen.add(name);
        const href = a.getAttribute('href') || '';
        const lines = el.innerText.split('\\n').filter(l => l.trim());
        items.push({{name, href, lines}});
      }});
      return JSON.stringify(items.slice(0, {max_results}));
    }})()
    """, timeout=30)

    if not result:
        print("  No items extracted!")
        return []
    items = json.loads(result)
    print(f"  Found {len(items)} results")
    return items

def parse_item(item):
    raw_name = item["name"]
    lines = item["lines"]
    rating = ""
    category = ""
    address = ""

    if len(lines) > 2:
        rating_raw = lines[2]
        parts = rating_raw.split("(")
        if parts:
            rating = parts[0].strip().replace(",", ".")
        if "Tidak ada ulasan" in rating or not rating:
            rating = ""

    if len(lines) > 3:
        parts = [p.strip() for p in lines[3].split("·") if p.strip()]
        if parts:
            category = parts[0]
            addr = parts[-1]
            if addr.startswith(raw_name):
                addr = addr[len(raw_name):].strip().lstrip(",").strip()
            address = addr

    return {
        "name": raw_name,
        "rating": rating,
        "category": category,
        "address": address,
        "phone": "",
        "website": ""
    }

def extract_place_details(href):
    ba("navigate", href, timeout=20)
    time.sleep(4)

    result = eval_js("""
    (async () => {
      await new Promise(r => setTimeout(r, 2000));
      let phone = '';
      const tel = document.querySelector('a[href^="tel:"]');
      if (tel) phone = tel.href.replace('tel:', '').trim();
      if (!phone) {
        const text = document.body.innerText;
        const m = text.match(/(\\+62[\\d\\s\\-\\(\\)]{7,}|0\\d{2,3}[\\d\\s\\-\\(\\)]{7,})/);
        if (m) phone = m[0].trim();
      }
      let website = '';
      const links = document.querySelectorAll('a[href^="http"]');
      for (const a of links) {
        const h = a.href;
        if (h.includes('google') || h.includes('maps')) continue;
        if (h.includes('facebook') || h.includes('instagram') || h.includes('twitter')) continue;
        website = h; break;
      }
      phone = phone.replace(/[\\s\\-\\(\\)]/g, ' ').replace(/\\s+/g, ' ').trim();
      return JSON.stringify({phone, website});
    })()
    """, timeout=20)

    if result:
        try:
            return json.loads(result)
        except:
            pass
    return {"phone": "", "website": ""}

def scrape(query, max_results=50):
    print(f"\n=== Scraping: {query} ===")
    items = crawl_search(query, max_results)
    if not items:
        return []

    results = []
    for idx, item in enumerate(items):
        r = parse_item(item)
        name_short = r['name'][:45]
        print(f"  [{idx+1}/{len(items)}] {name_short}... ", end="", flush=True)

        if item.get("href"):
            try:
                detail = extract_place_details(item["href"])
                r["phone"] = detail["phone"]
                r["website"] = detail["website"]
                p = detail["phone"][:25] if detail["phone"] else "-"
                w = detail["website"][:30] if detail["website"] else "-"
                print(f"tel:{p} web:{w}")
            except Exception as e:
                print(f"ERR:{str(e)[:30]}")
        else:
            print("(no href)")

        r["source_query"] = query
        results.append(r)

    return results

def save_csv(data, filepath):
    keys = ["name", "rating", "category", "address", "phone", "website", "source_query"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(data)
    print(f"\nSaved {len(data)} rows to {filepath}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Google Maps Scraper (BrowserAct)")
    parser.add_argument("queries", nargs="*", default=["cafe di Padang"])
    parser.add_argument("--max", type=int, default=50, help="Max results per query")
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    open_session()

    try:
        for q in args.queries:
            data = scrape(q, max_results=args.max)
            if data:
                fname = q.lower().replace(" ", "-")[:40] + ".csv"
                save_csv(data, os.path.join(OUT_DIR, fname))
    finally:
        close_session()
        print("Done.")
