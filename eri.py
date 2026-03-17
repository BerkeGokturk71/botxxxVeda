
import time
from dotenv import load_dotenv
import os

from telegram_bot import telegram_gonder

load_dotenv()
import engineio.packet
import re
import requests
import socketio
import urllib3
import logging

load_dotenv()

kadi = os.getenv("KADI")
sifre = os.getenv("SIFRE")
base_url = os.getenv("BASE_URL")
socket_url = os.getenv("SOCKET_URL")
server = os.getenv("SERVER")
domain = os.getenv("DOMAIN")
# --- ENGINE.IO PATCH ---
def patched_decode(self, encoded_packet):
    try:
        clean_data = re.sub(r'^\d+:', '', encoded_packet)
        return original_decode(self, clean_data)
    except Exception:
        return original_decode(self, encoded_packet)

original_decode = engineio.packet.Packet.decode
engineio.packet.Packet.decode = patched_decode
# ----------------------------------


logging.basicConfig(level=logging.ERROR)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
session.verify = False

# --- 1. LOGIN ---
headers = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest"
}

print("🚀 Oturum işlemleri başlatılıyor...")

session.post(
    f"{base_url}/app/ajax/giris/login.php",
    data={"kadi": kadi, "sifre": sifre},
    headers=headers
)

session.post(
    f"{base_url}/app/ajax/giris/sw_sec.php",
    data={"sw_url": "Veda"},
    headers=headers
)

session.get(f"{base_url}/sunucular", headers=headers)
session.get(f"{base_url}/oyun/Veda", headers=headers)
session.post(
    f"{base_url}/app/ajax/kullanici.php",
    data={"sayfa_yeri": "oyun"},
    headers=headers
)
secili_mulk = "18228"
headers_veda = {
    "Host": domain,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Referer": f"{base_url}/oyun/Veda",
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Connection": "keep-alive"
}

session.get(f"{base_url}/oyun/Veda",headers=headers_veda)

php_sess_id = session.cookies.get("PHPSESSID")

session.cookies.set("PHPSESSID", php_sess_id, domain=domain)
session.cookies.set("secili_mulk_id", secili_mulk, domain=domain)
session.cookies.set("koy_secim_sayisi", "2", domain=domain)

session.get(f"{base_url}/koy/Veda", headers=headers_veda)

# --- 2. BINA POPUP POST ---
def bina_popup_ac():

    url = f"{base_url}/app/ajax/popup/bina_ozellikleri.php"

    payload = {
        "kurulan_bina_id": "26"
    }

    popup_headers = {
       "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": f"{base_url}",
        "Referer": f"{base_url}/koy/Veda",
        "Accept": "text/html, */*; q=0.01"
    }

    try:

        r = session.post(
            url,
            data=payload,
            headers=popup_headers
        )

        print("🏢 Bina popup status:", r.status_code)

        if r.status_code == 200:
            print("✅ Bina popup açıldı")

        else:
            print("❌ Popup açılmadı")

    except Exception as e:
        print("Popup Hatası:", e)
def koy_degistir_get(mulk_id, koy_sayisi):

    session.cookies.set("secili_mulk_id", mulk_id, domain=domain)
    session.cookies.set("koy_secim_sayisi", koy_sayisi, domain=domain)
    print(session.cookies.get_dict())
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Referer": f"{base_url}/koy/Veda",
        "Accept": "text/html,application/xhtml+xml"
    }

    r = session.get(
        f"{base_url}/koy/Veda",
        headers=headers
    )
    time.sleep(5)

    print(f"🏘️ Köy değişti -> {mulk_id}")
# --- 3. SOCKETIO ---
engineio.client.MAX_DECODE_PACKETS = 10000000
engineio.payload.Payload.max_decode_packets = 10000000

sio = socketio.Client(
    http_session=session,
    ssl_verify=False,
    request_timeout=120,
    reconnection=True,
    reconnection_attempts=0,
    reconnection_delay=1,
     logger=True,
    engineio_logger=True
)

def hisar_callback(*args):
    print("📩 HISAR ACK GELDİ:")
    print(args)

import random
import time

mulk_list = [
    ("15939k", "0"),
    ("15619k", "1"),
    ("18228", "2")
    
]
def send_hisar():

    max_retry = 2  # maksimum deneme sayısı
    retry_count = 0

    while retry_count < max_retry:

        sio = socketio.Client(http_session=session,
    ssl_verify=False,
    request_timeout=120,
    reconnection=True,
    reconnection_attempts=0,
    reconnection_delay=1,
     logger=True,
    engineio_logger=True)

        sio.connect(
            socket_url,
            headers={
                "Origin": f"{base_url}",
                "Referer": f"{base_url}/oyun/Veda"
            },
            socketio_path="/socket.io",
            transports=["polling","websocket"]
        )

        result = {}

        def hisar_callback(*args):
            nonlocal result
            result['msg'] = args[0]  # callback içindeki mesajı kaydet
        time.sleep(3)
        sio.emit("hisar_gonder", {"gorev_id": "1"}, callback=hisar_callback)

        # server cevap verene kadar bekle
        timeout = 10
        waited = 0
        while 'msg' not in result and waited < timeout:
            time.sleep(0.5)
            waited += 0.5

        sio.disconnect()

        if 'msg' not in result:

            print("⚠️ HISAR callback gelmedi -> LOGIN reset")

            telegram_gonder("⚠️ HISAR callback gelmedi -> LOGIN reset")

            login()  # yeniden login

            retry_count += 1
            time.sleep(3)

            continue

        msg = result['msg']

        if isinstance(msg, str) and "tekrar dene" in msg:
            print(f"⚠️ HISAR hazır değil: {msg}, {retry_count+1}. deneme")
            telegram_gonder(f"⚠️ HISAR hazır değil: {msg}, {retry_count+1}. deneme")
            retry_count += 1
            time.sleep(2)
            continue
        else:
            print("📩 HISAR ACK GELDİ:", result)
            telegram_gonder(f"📩 HISAR ACK GELDİ:, {result}")
            break
import random
def bot_loop():

    while True:

        for mulk_id, koy_sayisi in mulk_list:

            koy_degistir_get(mulk_id, koy_sayisi)

            print(f"🏠 İşleniyor -> mulk_id={mulk_id}")
            telegram_gonder(f"🏠 İşleniyor -> mulk_id={mulk_id}")


            session.cookies.set("secili_mulk_id", mulk_id, domain=domain)
            session.cookies.set("koy_secim_sayisi", koy_sayisi, domain=domain)

            bina_popup_ac()

            time.sleep(3)

            send_hisar()

            time.sleep(3)

        wait_time = random.uniform(180, 190)
        print(f"⏳ {wait_time:.2f} saniye bekleniyor...")
        telegram_gonder(f"⏳ {wait_time:.2f} saniye bekleniyor...")
        time.sleep(wait_time)
def login():

    print("🔑 LOGIN tekrar yapılıyor...")

    session.post(
        f"{base_url}/app/ajax/giris/login.php",
        data={"kadi": kadi, "sifre": sifre},
        headers=headers
    )

    session.post(
        f"{base_url}/app/ajax/giris/sw_sec.php",
        data={"sw_url": server},
        headers=headers
    )

    session.get(f"{base_url}/sunucular", headers=headers)
    session.get(f"{base_url}/oyun/{server}", headers=headers)

    session.post(
        f"{base_url}/app/ajax/kullanici.php",
        data={"sayfa_yeri": "oyun"},
        headers=headers
    )

    session.get(f"{base_url}/koy/{server}", headers=headers)

    print("✅ LOGIN tamamlandı")
bot_loop()
