import os
import json
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "sent_jobs.json"

# İlgisiz başlıkları ve haberleri elenecek kara liste
EXCLUDE_WORDS = [
    "yazılım", "lisansı alımı", "ihale", "konferans", "programı'na katıldı", 
    "duyuru", "haber", "istatistik", "mevzuat", "kurum dışı kamu", "çözümü lisansı"
]

# Gerçek işe alımı temsil eden kelimeler
INCLUDE_WORDS = [
    "lisans", "kpss", "ziraat", "mühendis", "memur alımı", "personel alımı", 
    "sözleşmeli personel", "uzman yardımcısı", "müfettiş yardımcısı", "zabıta", "büro personeli"
]

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

def is_valid_job(title):
    title_lower = title.lower()
    
    # Kara listedeki kelimeler varsa direkt ele
    if any(ex in title_lower for ex in EXCLUDE_WORDS):
        return False
        
    # Aradığımız iş/lisans kelimeleri varsa kabul et
    if any(inc in title_lower for inc in INCLUDE_WORDS):
        return True
        
    return False

def scrape_sbb():
    """SBB Kamu İlan Portalı"""
    jobs = []
    url = "https://kamuilan.sbb.gov.tr/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, "html.parser")
        
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            link = a["href"]
            
            # Sadece gerçek ilan detay linkleri ve geçerli ilanlar
            if is_valid_job(text) and len(text) > 15:
                if not link.startswith("http"):
                    link = "https://kamuilan.sbb.gov.tr/" + link.lstrip("/")
                jobs.append((f"🏛️ <b>SBB Kamu İlan</b>\n\n📌 {text}\n\n🔗 <a href='{link}'>İlan Detayı</a>", link))
    except Exception as e:
        print(f"SBB hatası: {e}")
    return jobs

def scrape_resmi_gazete():
    """Resmî Gazete Çeşitli İlanlar"""
    jobs = []
    url = "https://www.resmigazete.gov.tr/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, "html.parser")
        
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            link = a["href"]
            
            if "ilan" in link.lower() and is_valid_job(text) and len(text) > 15:
                if not link.startswith("http"):
                    link = "https://www.resmigazete.gov.tr/" + link.lstrip("/")
                jobs.append((f"📜 <b>Resmî Gazete İlanı</b>\n\n📌 {text}\n\n🔗 <a href='{link}'>İlan Detayı</a>", link))
    except Exception as e:
        print(f"Resmi Gazete hatası: {e}")
    return jobs

def scrape_ilan_gov():
    """İlan.gov.tr Personel Alımı"""
    jobs = []
    url = "https://www.ilan.gov.tr/kategori/personel-alimi"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, "html.parser")
        
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            link = a["href"]
            
            if "/detail/" in link or "/ilan/" in link:
                if is_valid_job(text) and len(text) > 15:
                    if not link.startswith("http"):
                        link = "https://www.ilan.gov.tr" + link
                    jobs.append((f"📢 <b>İlan.gov.tr</b>\n\n📌 {text}\n\n🔗 <a href='{link}'>İlan Detayı</a>", link))
    except Exception as e:
        print(f"İlan.gov.tr hatası: {e}")
    return jobs

def check_all_sources():
    sent_jobs = load_sent_jobs()
    all_jobs = []
    
    all_jobs.extend(scrape_sbb())
    all_jobs.extend(scrape_resmi_gazete())
    all_jobs.extend(scrape_ilan_gov())
    
    new_jobs_count = 0
    for msg, link in all_jobs:
        if link not in sent_jobs:
            send_telegram(msg)
            sent_jobs.add(link)
            new_jobs_count += 1
            
    save_sent_jobs(sent_jobs)
    print(f"Nokta atışı tarama bitti. {new_jobs_count} yeni gerçek ilan bildirildi.")

if __name__ == "__main__":
    check_all_sources()
