from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from database import engine, SessionLocal

# Bu sihirli komut, eğer 'galeri.db' yoksa oluşturur ve içindeki tabloları çizer
models.Base.metadata.create_all(bind=engine)

# FastAPI'yi başlatıyoruz
app = FastAPI()
# Veritabanı bağlantısını açıp kapatan güvenli tünel
def get_db():
    db = SessionLocal()
    try:
        yield db  # İşlem bitene kadar bağlantıyı açık tut
    finally:
        db.close() # İşlem bitince (veya hata çıkarsa) kapıyı kesinlikle kapat
# 1. ADIM: Dışarıdan gelecek verinin şablonunu (kalıbını) belirliyoruz
class KullaniciMesaji(BaseModel):
    isim: str
    soru: str

    # 2. ADIM: Dışarıdan gelecek cevap verisinin şablonu
class CevapMesaji(BaseModel):
    cevap: str

# Önceki yazdığımız GET isteği (Ana sayfa)
@app.get("/")
def ana_sayfa():
    return {"mesaj": "Akilli Galeri projesinin kalbi atmaya basladi!"}

# 2. ADIM: Yeni eklediğimiz POST isteği
@app.post("/soru_sor/")
def soru_kaydet(mesaj: KullaniciMesaji, db: Session = Depends(get_db)):
    # 1. Pydantic'ten gelen onaylı veriyi al, SQLAlchemy modeline (kalıbına) dök
    yeni_soru = models.KullaniciSorusu(isim=mesaj.isim, soru=mesaj.soru)
    
    # 2. Hazırlanan veriyi veritabanı oturumuna (hafızaya) ekle
    db.add(yeni_soru)
    
    # 3. Değişiklikleri kalıcı olarak kaydet (Çelik kasaya kilitle)
    db.commit()
    
    # 4. Veritabanının otomatik verdiği ID numarasını görebilmek için veriyi yenile
    db.refresh(yeni_soru)
    
    return {"bilgi": "Soru başarıyla veritabanına kaydedildi!", "kayit": yeni_soru}

@app.get("/sorular/")
def sorulari_getir(db: Session = Depends(get_db)):
    # SQLAlchemy'den 'KullaniciSorusu' tablosuna bakmasını ve her şeyi (.all) getirmesini istiyoruz
    tum_sorular = db.query(models.KullaniciSorusu).all()
    
    return tum_sorular

@app.put("/cevapla/{soru_id}")
def soruyu_cevapla(soru_id: int, mesaj: CevapMesaji, db: Session = Depends(get_db)):
    # 1. Veritabanında o 'id' numarasına sahip soruyu ara ve ilk bulduğunu getir (.first())
    bulunan_soru = db.query(models.KullaniciSorusu).filter(models.KullaniciSorusu.id == soru_id).first()
    
    # 2. Eğer o numarada bir soru yoksa, işlemi durdur ve 404 hatası ver
    if not bulunan_soru:
        raise HTTPException(status_code=404, detail="Bu ID numarasına sahip bir soru bulunamadı!")
    
    # 3. Soru bulunduysa, 'cevap' kısmını kullanıcının gönderdiği yeni mesajla güncelle
    bulunan_soru.cevap = mesaj.cevap
    
    # 4. Değişikliği kasaya kilitle ve veriyi yenile
    db.commit()
    db.refresh(bulunan_soru)
    
    return {"bilgi": "Cevap başarıyla eklendi!", "kayit": bulunan_soru}

@app.delete("/soru_sil/{soru_id}")
def soruyu_sil(soru_id: int, db: Session = Depends(get_db)):
    # 1. Önce silinecek soruyu veritabanında ara
    bulunan_soru = db.query(models.KullaniciSorusu).filter(models.KullaniciSorusu.id == soru_id).first()
    
    # 2. Eğer o numarada bir soru yoksa, işlemi durdur ve 404 hatası ver
    if not bulunan_soru:
        raise HTTPException(status_code=404, detail="Silinmek istenen soru bulunamadı!")
    
    # 3. Soru bulunduysa, SQLAlchemy'ye bu kaydı silmesini söyle
    db.delete(bulunan_soru)
    
    # 4. Değişikliği (silme işlemini) kalıcı olarak kaydet
    db.commit()
    
    return {"bilgi": f"{soru_id} numaralı soru başarıyla silindi!"}