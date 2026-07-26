from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
import shutil # Dosyayı kaydetmek için Python'un yerleşik kütüphanesi
import os
import time
from sqlalchemy.orm import Session

# Senin yapına göre importlar (ai_service ana dizinde olduğu için direkt çağırıyoruz)
from database import get_db, get_chroma
from ai_service import get_embedding
import models, schemas

router = APIRouter() # İçinde prefix olmasın

@router.post("/foto-ekle/")
def foto_ekle(
    baslik: str = Form(...), 
    aciklama: str = Form(...), 
    dosya: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    chroma_collection = Depends(get_chroma)
):
    # 1. Dosyayı Bilgisayara Kaydet
    # Aynı isimli dosyalar çakışmasın diye ismin başına zaman damgası ekliyoruz
    zaman_damgasi = int(time.time())
    yeni_dosya_adi = f"{zaman_damgasi}_{dosya.filename}"
    dosya_yolu = f"uploads/{yeni_dosya_adi}"
    
    # Dosyayı fiziksel olarak uploads klasörüne yazıyoruz
    with open(dosya_yolu, "wb") as buffer:
        shutil.copyfileobj(dosya.file, buffer)

    # 2. SQLite'a Kayıt (Artık gerçek dosya yolunu kaydediyoruz)
    yeni_foto = models.Foto(
        baslik=baslik, 
        aciklama=aciklama, 
        dosya_yolu=dosya_yolu # Örn: uploads/16912345_kopek.jpg
    )
    db.add(yeni_foto)
    db.commit()
    db.refresh(yeni_foto) 
    
    try:
        # 3. Vektör Üretimi
        vektor = get_embedding(aciklama)
        
        # 4. ChromaDB'ye Kayıt
        chroma_collection.add(
            ids=[str(yeni_foto.id)], 
            embeddings=[vektor],
            documents=[aciklama],
            metadatas=[{"sqlite_id": yeni_foto.id, "baslik": baslik, "dosya_yolu": dosya_yolu}]
        )
    except Exception as e:
        # Hata olursa SQLite kaydını ve diske kaydettiğimiz resmi sil
        db.delete(yeni_foto)
        db.commit()
        if os.path.exists(dosya_yolu):
            os.remove(dosya_yolu)
        raise HTTPException(status_code=500, detail=f"Vektör hatası: {str(e)}")

    return {
        "mesaj": "Fotoğraf başarıyla yüklendi ve yapay zeka tarafından işlendi!", 
        "id": yeni_foto.id,
        "url": f"/{dosya_yolu}" # Kullanıcıya resmin linkini de veriyoruz
    }

@router.get("/ara/")
def foto_ara(
    sorgu: str, 
    limit: int = 3, 
    db: Session = Depends(get_db), 
    chroma_collection = Depends(get_chroma)
):
    try:
        # 1. Kullanıcının arama kelimesini (örn: "sahil") yapay zeka ile vektöre çevir
        vektor = get_embedding(sorgu)
        
        # 2. Vektör veritabanında bu anlama en yakın 'limit' kadar (varsayılan 3) sonucu ara
        chroma_sonuclar = chroma_collection.query(
            query_embeddings=[vektor],
            n_results=limit
        )
        
        # Eğer galeri tamamen boşsa
        if not chroma_sonuclar["ids"][0]:
            return {"mesaj": "Galeri boş veya sonuç bulunamadı.", "sonuclar": []}
            
        # 3. Bulunan ID'leri alıp SQLite veritabanından tam detayları (dosya yolu vs.) çekiyoruz
        # ChromaDB ID'leri string olarak saklıyordu, SQLite için onları tekrar sayıya (integer) çeviriyoruz
        # ChromaDB ID'leri string olarak saklıyordu, SQLite için onları tekrar sayıya (integer) çeviriyoruz
        id_listesi = [int(''.join(filter(str.isdigit, id_str))) for id_str in chroma_sonuclar["ids"][0]]
        mesafeler = chroma_sonuclar["distances"][0]
        
        # Fotoğrafları klasik veritabanından toplu olarak getir
        fotograflar = db.query(models.Foto).filter(models.Foto.id.in_(id_listesi)).all()
        
        # 4. Sonuçları ChromaDB'nin belirlediği "benzerlik" sırasına göre paketle
        son_liste = []
        for i, foto_id in enumerate(id_listesi):
            # Önce skoru hesapla
            skor = round(mesafeler[i], 4)
            
            # SADECE skor 1.0'dan küçükse (alakalıysa) işlemlere devam et
            if skor < 1.0:
                # İlgili fotoğrafı SQLite'tan gelen listeden bul
                foto = next((f for f in fotograflar if f.id == foto_id), None)
                if foto:
                    son_liste.append({
                        "id": foto.id,
                        "baslik": foto.baslik,
                        "aciklama": foto.aciklama,
                        "dosya_yolu": foto.dosya_yolu,
                        "uzaklik_skoru": skor
                    })
                
        return {"aranan_kelime": sorgu, "sonuclar": son_liste}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Arama sırasında hata oluştu: {str(e)}")

@router.get("/fotograflar/")
def tum_fotograflari_getir(db: Session = Depends(get_db)):
    # Veritabanındaki tüm fotoğrafları listele
    fotolar = db.query(models.Foto).all()
    return fotolar

@router.delete("/foto-sil/{foto_id}")
def foto_sil(
    foto_id: int, 
    db: Session = Depends(get_db), 
    chroma_collection = Depends(get_chroma)
):
    # 1. Fotoğrafı SQLite veritabanında bul
    foto = db.query(models.Foto).filter(models.Foto.id == foto_id).first()
    
    if not foto:
        raise HTTPException(status_code=404, detail="Silinmek istenen fotoğraf bulunamadı.")
        
    dosya_yolu = foto.dosya_yolu
    
    try:
        # 2. Fiziksel dosyayı bilgisayardan (uploads klasöründen) sil
        if os.path.exists(dosya_yolu):
            os.remove(dosya_yolu)
            
        # 3. Yapay Zeka hafızasından (ChromaDB) sil
        # Ekleme yaparken ID'yi string'e çevirerek kaydetmiştik ( str(yeni_foto.id) ), silerken de aynı formatı kullanıyoruz.
        chroma_collection.delete(
            ids=[str(foto.id)]
        )
        
        # 4. Klasik veritabanından (SQLite) sil
        db.delete(foto)
        db.commit()
        
        return {"mesaj": f"ID'si {foto_id} olan fotoğraf sistemden tamamen temizlendi."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Silme işlemi sırasında hata oluştu: {str(e)}")