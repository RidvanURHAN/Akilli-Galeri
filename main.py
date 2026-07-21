from fastapi import FastAPI
from pydantic import BaseModel

# FastAPI'yi başlatıyoruz
app = FastAPI()

# 1. ADIM: Dışarıdan gelecek verinin şablonunu (kalıbını) belirliyoruz
class KullaniciMesaji(BaseModel):
    isim: str
    soru: str

# Önceki yazdığımız GET isteği (Ana sayfa)
@app.get("/")
def ana_sayfa():
    return {"mesaj": "Akilli Galeri projesinin kalbi atmaya basladi!"}

# 2. ADIM: Yeni eklediğimiz POST isteği
@app.post("/soru-sor")
def soru_cevapla(gelen_veri: KullaniciMesaji):
    # Kullanıcının gönderdiği verinin içinden isim ve soru kısımlarını alıyoruz
    islenen_cevap = "Merhaba " + gelen_veri.isim + ", '" + gelen_veri.soru + "' sorunu aldim ama henuz yapay zekaya bagli degilim!"
    
    # Sistemi JSON formatında yanıtlıyoruz
    return {"sistem_yaniti": islenen_cevap}