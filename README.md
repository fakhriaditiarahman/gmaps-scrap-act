<div align="center">

# 🗺️ Gmaps Scrap Act

**Google Maps scraper otomatis — dapatkan nama, rating, kategori, alamat, nomor telepon, dan website bisnis dari hasil pencarian Google Maps.**

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![BrowserAct](https://img.shields.io/badge/browser--act-0.1.30-green)](https://www.browseract.com)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)]()

</div>

---

## ✨ Fitur

- **Scrape daftar tempat** dari Google Maps — nama, rating, kategori, alamat
- **Nomor telepon** — otomatis di-extract dari halaman detail tiap tempat
- **Website** — otomatis di-extract (jika tersedia)
- **Anti-bot bypass** — menggunakan BrowserAct stealth engine
- **Batch query** — scrape banyak kata kunci sekaligus
- **Output CSV** — siap pakai untuk spreadsheet / CRM

## 📦 Instalasi

```bash
# 1. Install BrowserAct CLI
uv tool install browser-act-cli --python 3.12

# 2. Clone repo
git clone https://github.com/fakhriaditiarahman/gmaps-scrap-act.git
cd gmaps-scrap-act

# 3. Jalankan
python3 scraper-ba.py "cafe di Padang" --max 50
```

> **Catatan:** Chrome akan direstart dengan remote debugging saat pertama kali dijalankan. Simpan pekerjaan Anda sebelumnya.

## 🚀 Penggunaan

### Scrape satu kata kunci

```bash
python3 scraper-ba.py "cafe di Padang" --max 100
```

### Scrape banyak kata kunci sekaligus

```bash
python3 scraper-ba.py "cafe di Padang" "perusahaan di Padang" "restoran di Padang" --max 50
```

### Opsi

| Argumen | Default | Deskripsi |
|---------|---------|-----------|
| `queries` | `["cafe di Padang"]` | Kata kunci pencarian |
| `--max` | `50` | Maksimal hasil per query |

## 📄 Output CSV

Hasil disimpan di folder `hasil-scrape/` dengan format:

| name | rating | category | address | phone | website | source_query |
|------|--------|----------|---------|-------|---------|-------------|
| Kolabora Coffee & Eatery | 4.6 | Kedai Kopi | Jl. Raya Kalumbuk No.2 | 08116633350 | | cafe di Padang |
| Rimbun Espresso & Brew Bar | 4.6 | Kedai Kopi | Jl. KIS. Mangunsarkoro | 081378542165 | https://ngopikitalagi.com/menu | cafe di Padang |

## 📋 File

| File | Deskripsi |
|------|-----------|
| `scraper-ba.py` | Scraper utama — menggunakan **BrowserAct CLI** ✅ |
| `scraper.py` | Scraper lama — menggunakan Selenium (tanpa nomor telepon) |
| `template-pesan.md` | Template WA/Email untuk promosi ke hasil scrape |
| `hasil-scrape/` | Folder output CSV |

## 🧠 Cara Kerja

1. BrowserAct membuka Google Maps dengan Chrome
2. Navigasi ke pencarian sesuai query
3. Scroll feed untuk memuat hasil
4. Ekstrak data dasar (nama, rating, kategori, alamat) dari hasil pencarian
5. Untuk tiap tempat, buka halaman detail → extract nomor telepon & website
6. Simpan semua data ke CSV

## 🆚 Perbandingan scraper

| Fitur | `scraper.py` (Selenium) | `scraper-ba.py` (BrowserAct) |
|-------|:-----------------------:|:----------------------------:|
| Nomor telepon | ❌ Kosong | ✅ Terisi |
| Website | ❌ Kosong | ✅ Terisi |
| Anti-bot detection | ❌ Mudah terdeteksi | ✅ Stealth bypass |
| Login Google | Diperlukan | Tidak diperlukan |
| Output CSV | ✅ | ✅ |

## 📝 Template Promosi

Lihat `template-pesan.md` untuk template WhatsApp dan Email yang bisa langsung digunakan untuk menghubungi pemilik bisnis hasil scraping.

---

<div align="center">

Dibuat dengan ❤️ untuk kebutuhan riset & pengembangan bisnis

</div>
