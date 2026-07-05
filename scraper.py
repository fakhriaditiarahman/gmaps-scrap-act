#!/usr/bin/env python3
import sys, csv, time, os, json, re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

OUT_DIR = "hasil-scrape"
CLEAN_RE = re.compile(r'[^\x20-\x7E\xC0-\xFF\xA0-\xFF.,\w\s\(\)\-]')

EXTRACT_JS = """
const items = [];
document.querySelectorAll('[role="feed"] > div > div').forEach(el => {
  const a = el.querySelector('a');
  if (!a) return;
  const name = a.textContent.trim();
  if (!name) return;
  const href = a.getAttribute('href') || '';
  const lines = el.innerText.split('\\n').filter(l => l.trim());
  items.push({name, href, lines});
});
return JSON.stringify(items);
"""

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

def do_login(driver):
    driver.get("https://accounts.google.com/Login")
    input("Login ke Google di browser, tekan ENTER setelah selesai...")

def clean(s):
    return CLEAN_RE.sub('', s).strip()

def search(driver, query):
    driver.get("https://www.google.com/maps")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[role="combobox"]'))
    )
    box = driver.find_element(By.CSS_SELECTOR, 'input[role="combobox"]')
    box.clear()
    box.send_keys(query)
    box.send_keys(Keys.ENTER)
    time.sleep(4)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[role="feed"]'))
    )

def scroll_feed(driver, scrolls=15):
    feed = driver.find_element(By.CSS_SELECTOR, '[role="feed"]')
    for i in range(scrolls):
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
        time.sleep(1.5)

def parse_item(item):
    raw_name = item["name"]
    lines = item["lines"]
    rating_raw = lines[2] if len(lines) > 2 else ""
    rating = rating_raw.split("(")[0].strip().replace(",", ".") if rating_raw else ""
    if rating == "Tidak ada ulasan" or rating == "":
        rating = ""
    category = ""
    address = ""

    if len(lines) > 3:
        parts = [p.strip() for p in lines[3].split("·")
                 if p.strip() and not any(ord(c) > 0xFFFC for c in p.strip())]
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

def scrape(driver, query, max_results=50, with_detail=False):
    search(driver, query)
    scroll_feed(driver)

    raw = driver.execute_script(EXTRACT_JS)
    items = json.loads(raw)[:max_results]
    print(f"  Found {len(items)} results")

    results = [parse_item(it) for it in items]

    if with_detail:
        feed_divs = driver.find_elements(By.CSS_SELECTOR, '[role="feed"] > div > div')
        for idx, r in enumerate(results):
            if idx < len(feed_divs):
                try:
                    driver.execute_script("arguments[0].click();", feed_divs[idx])
                    time.sleep(2.5)
                    text = driver.execute_script("return document.body.innerText")
                    # Extract phone & website from detail text
                    for line in text.split("\n"):
                        for pat in [r'(\+62[\d\s\-\(\)]{8,})', r'(0\d[\d\s\-\(\)]{8,})']:
                            m = re.search(pat, line)
                            if m and m.group():
                                r["phone"] = m.group().strip()
                        if "http" in line and "google" not in line:
                            urls = re.findall(r'(https?://[^\s]+)', line)
                            if urls:
                                r["website"] = urls[0].rstrip(".,)")
                except:
                    pass

            print(f"  [{idx+1}/{len(results)}] {r['name'][:40]}")
    else:
        for idx, r in enumerate(results):
            print(f"  [{idx+1}/{len(results)}] {r['name'][:40]}")

    for r in results:
        r["source_query"] = query

    return results

def save_csv(data, filepath):
    keys = ["name", "rating", "category", "address", "phone", "website", "source_query"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(data)
    print(f"Saved {len(data)} rows to {filepath}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Google Maps Scraper")
    parser.add_argument("queries", nargs="*", default=["cafe di Padang", "perusahaan di Padang"],
                        help="Search queries")
    parser.add_argument("--max", type=int, default=50, help="Max results per query")
    parser.add_argument("--login", action="store_true", help="Login to Google first (for phone/website)")
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    driver = init_driver()

    try:
        if args.login:
            do_login(driver)

        for q in args.queries:
            print(f"\n=== Scraping: {q} ===")
            data = scrape(driver, q, max_results=args.max, with_detail=args.login)
            fname = q.lower().replace(" ", "-")[:40] + ".csv"
            save_csv(data, os.path.join(OUT_DIR, fname))
    finally:
        driver.quit()
        print("\nDone.")
