import os
import json
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "sent_jobs.json"

# Sadece bu kelimeleri içeren duyurular/ilanlar işleme alınacak
TARGET_KEYWORDS = [
    "personel", "memur", "alım", "alımı", "kpss", "lisans", 
    "işçi", "sözleşmeli", "zabıta", "mühendis", "ziraat", "kadro"
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

def scrape_site(url, site_name, base_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    found_jobs = []
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, "html.parser")
        
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            link = a["href"]
            
            if len(text) < 5:
                continue
                
            # Sadece hedef kelimeleri barındıran alım duyurularını filtrele
            text_lower = text.lower()
            if any(k in text_lower for k in TARGET_KEYWORDS):
                if not link.startswith("http"):
                    link = base_url.rstrip("/") + "/" + link.lstrip("/")
                found_jobs.append((text, link))
                
    except Exception as e:
        print(f"{site_name} bağlantı hatası: {e}")
    return found_jobs

def check_all_sources():
    sent_jobs = load_sent_jobs()
    is_first_run = len(sent_jobs) == 0  # İlk kez çalışıyorsa hafıza boştur
    
    sources = [
        {"name": "🏛️ SBB Kamu İlan", "url": "https://kamuilan.sbb.gov.tr/", "base": "https://kamuilan.sbb.gov.tr"},
        {"name": "📜 Resmî Gazete", "url": "https://www.resmigazete.gov.tr/", "base": "https://www.resmigazete.gov.tr"},
        {"name": "💼 İŞKUR Kamu Memur Alımı", "url": "https://www.iskur.gov.tr/ilanlar/kamu-memur-alim-ilanlari/", "base": "https://www.iskur.gov.tr"},
        {"name": "💼 İŞKUR Kurum Dışı Kamu İşçi", "url": "https://www.iskur.gov.tr/ilanlar/kurumdisi-kamu-isci-alim-ilanlari/", "base": "https://www.iskur.gov.tr"},
        {"name": "🎯 Kariyer Kapısı", "url": "https://kariyerkapisi.gov.tr/isealim", "base": "https://kariyerkapisi.gov.tr"},
        {"name": "🏢 Yerel Yönetimler Duyurular", "url": "https://yerelyonetimler.csb.gov.tr/duyurular", "base": "https://yerelyonetimler.csb.gov.tr"},
        {"name": "🏢 Yerel Yönetimler Haberler", "url": "https://yerelyonetimler.csb.gov.tr/haberler", "base": "https://yerelyonetimler.csb.gov.tr"},
        {"name": "🏙️ Eskişehir BŞB Duyurular", "url": "https://www.eskisehir.bel.tr/tum-duyurular", "base": "https://www.eskisehir.bel.tr"},
        {"name": "🏘️ Odunpazarı Bel. Duyurular", "url": "https://www.odunpazari.bel.tr/guncel/duyurular", "base": "https://www.odunpazari.bel.tr"},
        {"name": "🏡 Tepebaşı Bel. Duyuru", "url": "https://www.tepebasi.bel.tr/Duyuru", "base": "https://www.tepebasi.bel.tr"},
        {"name": "🌾 Alpu Bel. Duyurular", "url": "https://www.alpu.bel.tr/duyurular", "base": "https://www.alpu.bel.tr"},
        {"name": "🚜 Beylikova Bel. Duyurular", "url": "https://www.beylikova.bel.tr/duyurular", "base": "https://www.beylikova.bel.tr"},
        {"name": "🏞️ Çifteler Bel. Duyurular", "url": "https://www.cifteler.bel.tr/HOME/INDEX/HABERLER/DUYURULAR", "base": "https://www.cifteler.bel.tr"},
        {"name": "🏰 Han Bel. Duyurular", "url": "https://han.bel.tr/guncel/duyurular", "base": "https://han.bel.tr"},
        {"name": "🌿 Mihalgazi Bel. Duyurular", "url": "https://mihalgazi.bel.tr/duyurular/", "base": "https://mihalgazi.bel.tr"},
        {"name": "⛰️ Seyitgazi Duyurular", "url": "https://www.seyitgazi.gov.tr/duyurular", "base": "https://www.seyitgazi.gov.tr"},
        {"name": "📅 Kamu İlan Takvimi", "url": "https://www.kamuilantakvimi.com/ilanlar", "base": "https://www.kamuilantakvimi.com"}
    ]

    new_jobs_count = 0
    for src in sources:
        results = scrape_site(src["url"], src["name"], src["base"])
        for title, link in results:
            if link not in sent_jobs:
                # Eğer ilk çalıştırma ise Telegram'a mesaj atma, sadece hafızaya ekle (eski ilanları süpürür)
                if not is_first_run:
                    msg = f"{src['name']}\n\n📌 {title}\n\n🔗 <a href='{link}'>İlan/Duyuru Detayı</a>"
                    send_telegram(msg)
                    new_jobs_count += 1
                sent_jobs.add(link)

    save_sent_jobs(sent_jobs)
    
    if is_first_run:
        print("Sistemin ilk kurulumu yapıldı. Mevcut tüm eski ilanlar hafızaya alındı, Telegram'a gönderilmedi.")
    else:
        print(f"Tarama bitti. {new_jobs_count} yeni bildirim atıldı.")

if __name__ == "__main__":
    check_all_sources()
