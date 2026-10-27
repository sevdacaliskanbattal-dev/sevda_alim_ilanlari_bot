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

def scrape_site(url, site_name, base_url, keywords=None):
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
                
            if not link.startswith("http"):
                link = base_url.rstrip("/") + "/" + link.lstrip("/")
                
            # Eğer özel kelime filtresi varsa ona göre bak, yoksa genel tarama yap
            if keywords:
                if any(k in text.lower() for k in keywords):
                    found_jobs.append((text, link))
            else:
                found_jobs.append((text, link))
                
    except Exception as e:
        print(f"{site_name} bağlantı hatası: {e}")
    return found_jobs

def check_all_sources():
    sent_jobs = load_sent_jobs()
    new_jobs_count = 0

    # Tarama Kaynakları Listesi (Verdiğin Tüm Yeni Linkler)
    sources = [
        # 1. SBB Kamu İlan
        {
            "name": "🏛️ SBB Kamu İlan",
            "url": "https://kamuilan.sbb.gov.tr/",
            "base": "https://kamuilan.sbb.gov.tr",
            "keywords": ["lisans", "kpss", "ziraat", "mühendis", "personel", "memur"]
        },
        # 2. Resmî Gazete
        {
            "name": "📜 Resmî Gazete",
            "url": "https://www.resmigazete.gov.tr/",
            "base": "https://www.resmigazete.gov.tr",
            "keywords": ["lisans", "alımı", "personel", "memur"]
        },
        # 3. İŞKUR Kamu Memur Alım İlanları
        {
            "name": "💼 İŞKUR Kamu Memur Alımı",
            "url": "https://www.iskur.gov.tr/ilanlar/kamu-memur-alim-ilanlari/",
            "base": "https://www.iskur.gov.tr",
            "keywords": None
        },
        # 4. İŞKUR Kurum Dışı Kamu İşçi Alımı
        {
            "name": "💼 İŞKUR Kurum Dışı Kamu İşçi",
            "url": "https://www.iskur.gov.tr/ilanlar/kurumdisi-kamu-isci-alim-ilanlari/",
            "base": "https://www.iskur.gov.tr",
            "keywords": None
        },
        # 5. Kariyer Kapısı
        {
            "name": "🎯 Kariyer Kapısı",
            "url": "https://kariyerkapisi.gov.tr/isealim",
            "base": "https://kariyerkapisi.gov.tr",
            "keywords": ["lisans", "başvuru", "alım", "personel"]
        },
        # 6. Yerel Yönetimler Duyurular
        {
            "name": "🏢 Yerel Yönetimler Duyurular",
            "url": "https://yerelyonetimler.csb.gov.tr/duyurular",
            "base": "https://yerelyonetimler.csb.gov.tr",
            "keywords": None
        },
        # 7. Yerel Yönetimler Haberler
        {
            "name": "🏢 Yerel Yönetimler Haberler",
            "url": "https://yerelyonetimler.csb.gov.tr/haberler",
            "base": "https://yerelyonetimler.csb.gov.tr",
            "keywords": ["personel", "alımı", "zabıta", "memur", "lisans"]
        },
        # 8. Eskişehir Büyükşehir Belediyesi
        {
            "name": "🏙️ Eskişehir BŞB Duyurular",
            "url": "https://www.eskisehir.bel.tr/tum-duyurular",
            "base": "https://www.eskisehir.bel.tr",
            "keywords": None
        },
        # 9. Odunpazarı Belediyesi
        {
            "name": "🏘️ Odunpazarı Bel. Duyurular",
            "url": "https://www.odunpazari.bel.tr/guncel/duyurular",
            "base": "https://www.odunpazari.bel.tr",
            "keywords": None
        },
        # 10. Tepebaşı Belediyesi
        {
            "name": "🏡 Tepebaşı Bel. Duyuru",
            "url": "https://www.tepebasi.bel.tr/Duyuru",
            "base": "https://www.tepebasi.bel.tr",
            "keywords": None
        },
        # 11. Alpu Belediyesi
        {
            "name": "🌾 Alpu Bel. Duyurular",
            "url": "https://www.alpu.bel.tr/duyurular",
            "base": "https://www.alpu.bel.tr",
            "keywords": None
        },
        # 12. Beylikova Belediyesi
        {
            "name": "🚜 Beylikova Bel. Duyurular",
            "url": "https://www.beylikova.bel.tr/duyurular",
            "base": "https://www.beylikova.bel.tr",
            "keywords": None
        },
        # 13. Çifteler Belediyesi
        {
            "name": "🏞️ Çifteler Bel. Duyurular",
            "url": "https://www.cifteler.bel.tr/HOME/INDEX/HABERLER/DUYURULAR",
            "base": "https://www.cifteler.bel.tr",
            "keywords": None
        },
        # 14. Han Belediyesi
        {
            "name": "🏰 Han Bel. Duyurular",
            "url": "https://han.bel.tr/guncel/duyurular",
            "base": "https://han.bel.tr",
            "keywords": None
        },
        # 15. Mihalgazi Belediyesi
        {
            "name": "🌿 Mihalgazi Bel. Duyurular",
            "url": "https://mihalgazi.bel.tr/duyurular/",
            "base": "https://mihalgazi.bel.tr",
            "keywords": None
        },
        # 16. Seyitgazi Kaymakamlığı / Bel.
        {
            "name": "⛰️ Seyitgazi Duyurular",
            "url": "https://www.seyitgazi.gov.tr/duyurular",
            "base": "https://www.seyitgazi.gov.tr",
            "keywords": None
        },
        # 17. Kamu İlan Takvimi
        {
            "name": "📅 Kamu İlan Takvimi",
            "url": "https://www.kamuilantakvimi.com/ilanlar",
            "base": "https://www.kamuilantakvimi.com",
            "keywords": None
        }
    ]

    for src in sources:
        results = scrape_site(src["url"], src["name"], src["base"], src["keywords"])
        for title, link in results:
            if link not in sent_jobs:
                msg = f"{src['name']}\n\n📌 {title}\n\n🔗 <a href='{link}'>İlan/Duyuru Detayı</a>"
                send_telegram(msg)
                sent_jobs.add(link)
                new_jobs_count += 1

    save_sent_jobs(sent_jobs)
    print(f"Tarama bitti. {new_jobs_count} yeni bildirim atıldı.")

if __name__ == "__main__":
    check_all_sources()
