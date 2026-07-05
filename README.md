# gmaps-scrap-act

Google Maps scraper using BrowserAct CLI. Extracts: name, rating, category, address, phone, website.

## Files

- `scraper-ba.py` — Main scraper using BrowserAct CLI
- `scraper.py` — Legacy scraper using Selenium
- `template-pesan.md` — Message templates for promotion

## Usage

```bash
python3 scraper-ba.py "cafe di Padang" --max 50
python3 scraper-ba.py "cafe di Padang" "perusahaan di Padang" --max 100
```

## Requirements

- Python 3.12+
- BrowserAct CLI (`uv tool install browser-act-cli --python 3.12`)
- Google Chrome
