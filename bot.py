import os
import json
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "sent_jobs.json"

def load_sent_jobs():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_sent_jobs(sent_jobs):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(list(sent_jobs), f, ensure_ascii=False, indent=2)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram hatası: {e}")

def scrape_site(url, site_name, parser_type="html.parser"):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        return BeautifulSoup(resp.text, parser_type)
    except Exception as e:
        print(f"{site_name} bağlantı hatası: {e}")
        return None

def check_all_sources():
    sent_jobs = load_sent_jobs()
    new_jobs_count = 0

    # 1. SBB Kamu İlan
    soup = scrape_site("https://kamuilan.sbb.gov.tr/", "SBB Kamu İlan")
    if soup:
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            link = a["href"]
            if not link.startswith("http"):
                link = "https://kamuilan.sbb.gov.tr/" + link.lstrip("/")
            
            if any(k in text.lower() for k in ["lisans", "kpss p3", "ziraat", "mühendis"]) and link not in sent_jobs:
                send_telegram(f"🏛️ <b>SBB Kamu İlan</b>\n\n📌 {text}\n\n🔗 <a href='{link}'>İlan Linki</a>")
                sent_jobs.add(link)
                new_jobs_count += 1

    # 2. Resmî Gazete
    soup = scrape_site("https://www.resmigazete.gov.tr/", "Resmi Gazete")
    if soup:
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            link = a["href"]
            if ("ilan" in link.lower() or "personel" in text.lower()) and any(k in text.lower() for k in ["lisans", "alımı", "personel"]):
                if not link.startswith("http"):
                    link = "https://www.resmigazete.gov.tr/" + link.lstrip("/")
                if link not in sent_jobs:
                    send_telegram(f"📜 <b>Resmî Gazete İlanı</b>\n\n📌 {text}\n\n🔗 <a href='{link}'>İlan Linki</a>")
                    sent_jobs.add(link)
                    new_jobs_count += 1

    # 3. İlan.gov.tr (BİK)
    soup = scrape_site("https://www.ilan.gov.tr/kategori/personel-alimi", "İlan.gov.tr")
    if soup:
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            link = a["href"]
            if not link.startswith("http"):
                link = "https://www.ilan.gov.tr" + link
            if any(k in text.lower() for k in ["lisans", "memur", "personel"]) and link not in sent_jobs:
                send_telegram(f"📢 <b>İlan.gov.tr</b>\n\n📌 {text}\n\n🔗 <a href='{link}'>İlan Linki</a>")
                sent_jobs.add(link)
                new_jobs_count += 1

    # 4. Çevre ve Şehircilik Yerel Yönetimler
    soup = scrape_site("https://yerelyonetimler.csb.gov.tr/", "Yerel Yönetimler")
    if soup:
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            link = a["href"]
            if any(k in text.lower() for k in ["lisans", "alımı", "zabıta", "memur"]) and link not in sent_jobs:
                if not link.startswith("http"):
                    link = "https://yerelyonetimler.csb.gov.tr/" + link.lstrip("/")
                send_telegram(f"🏢 <b>Yerel Yönetimler İlanı</b>\n\n📌 {text}\n\n🔗 <a href='{link}'>İlan Linki</a>")
                sent_jobs.add(link)
                new_jobs_count += 1

    # 5. İŞKUR
    soup = scrape_site("https://www.iskur.gov.tr/", "İŞKUR")
    if soup:
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            link = a["href"]
            if ("kamu" in text.lower() or "lisans" in text.lower()) and link not in sent_jobs:
                if not link.startswith("http"):
                    link = "https://www.iskur.gov.tr/" + link.lstrip("/")
                send_telegram(f"💼 <b>İŞKUR İlanı</b>\n\n📌 {text}\n\n🔗 <a href='{link}'>İlan Linki</a>")
                sent_jobs.add(link)
                new_jobs_count += 1

    # 6. Kariyer Kapısı
    soup = scrape_site("https://kariyerkapisi.gov.tr/isealim", "Kariyer Kapısı")
    if soup:
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            link = a["href"]
            if any(k in text.lower() for k in ["lisans", "başvuru", "alim"]) and link not in sent_jobs:
                if not link.startswith("http"):
                    link = "https://kariyerkapisi.gov.tr" + link
                send_telegram(f"🎯 <b>Kariyer Kapısı İlanı</b>\n\n📌 {text}\n\n🔗 <a href='{link}'>İlan Linki</a>")
                sent_jobs.add(link)
                new_jobs_count += 1

    save_sent_jobs(sent_jobs)
    print(f"Tarama bitti. {new_jobs_count} yeni bildirim atıldı.")

if __name__ == "__main__":
    check_all_sources()
