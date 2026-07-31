from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from PIL import Image
import os
import io

# Kendi proje yapına göre olan importlar
from database import get_db, get_chroma
import models
from ai_service import get_text_embedding, get_image_embedding, gemini_foto_analiz

router = APIRouter()

# ---------------------------------------------------------
# 1. FOTOĞRAF ARAMA ENDPOINT'İ (Yapay Zeka Destekli)
# ---------------------------------------------------------
@router.get("/ara/")
def foto_ara(
    sorgu: str, 
    limit: int = 50, 
    db: Session = Depends(get_db), 
    chroma_collection = Depends(get_chroma)
):
    try:
        # 1. Kullanıcının arama kelimesini çok dilli model ile vektöre çevir
        vektor = get_text_embedding(sorgu)
        
        # 2. Vektör veritabanında (ChromaDB) ara
        chroma_sonuclar = chroma_collection.query(
            query_embeddings=[vektor],
            n_results=limit
        )
        
        if not chroma_sonuclar["ids"] or not chroma_sonuclar["ids"][0]:
            return {"mesaj": "Galeri boş veya sonuç bulunamadı.", "sonuclar": []}
            
        id_listesi = [int(''.join(filter(str.isdigit, id_str))) for id_str in chroma_sonuclar["ids"][0]]
        mesafeler = chroma_sonuclar["distances"][0]
        
        fotograflar = db.query(models.Foto).filter(models.Foto.id.in_(id_listesi)).all()
        
        son_liste = []
        for i, foto_id in enumerate(id_listesi):
            # ChromaDB'nin verdiği Kosinüs Mesafesi (Cosine Distance)
            skor = mesafeler[i] 
            
            # YENİ HESAPLAMA MANTIĞI:
            # 1. Mesafeyi Benzerliğe çevir (Mesafe ne kadar azsa benzerlik o kadar fazladır)
            kosinus_benzerligi = 1.0 - skor
            
            # 2. CLIP modelinin çalışma aralığı olan 0.15 ile 0.32'yi yüzdelik dilime çek
            # Formül: ((Değer - Min) / (Max - Min)) * 100
            gercek_yuzde = ((kosinus_benzerligi - 0.15) / (0.32 - 0.15)) * 100
            
            # 3. Yüzdeyi 0 ile 100 arasına sınırla (Negatif veya %100'ü aşan değerleri engellemek için)
            gercek_yuzde = max(0.0, min(100.0, gercek_yuzde))
            gercek_yuzde = round(gercek_yuzde, 1)

            print(f"🔍 DEBUG | Foto ID: {foto_id} | Benzerlik: {kosinus_benzerligi:.4f} | Yüzde: %{gercek_yuzde}")

            # Sadece %40 barajını geçenleri listeye ekle
            if gercek_yuzde >= 40.0:
                foto = next((f for f in fotograflar if f.id == foto_id), None)
                if foto:
                    son_liste.append({
                        "id": foto.id,
                        "baslik": foto.baslik,
                        "aciklama": foto.aciklama,
                        "dosya_yolu": foto.dosya_yolu,
                        "eslesme_yuzdesi": gercek_yuzde
                    })
                
        # Sonuçları eşleşme yüzdesine göre yüksekten düşüğe doğru sırala
        son_liste.sort(key=lambda x: x["eslesme_yuzdesi"], reverse=True)
        
        if not son_liste:
            return {"mesaj": f"'{sorgu}' araması için yeterince iyi bir eşleşme bulunamadı.", "sonuclar": []}

        return {"aranan_kelime": sorgu, "sonuclar": son_liste}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Arama sırasında hata oluştu: {str(e)}")


@router.post("/gorsel-ara/")
async def gorsel_ile_ara(
    dosya: UploadFile = File(...),
    limit: int = 50,
    db: Session = Depends(get_db),
    chroma_collection = Depends(get_chroma)
):
    try:
        resim_verisi = await dosya.read()
        resim = Image.open(io.BytesIO(resim_verisi)).convert("RGB")
        
        vektor = get_image_embedding(resim)
        
        chroma_sonuclar = chroma_collection.query(
            query_embeddings=[vektor],
            n_results=limit
        )
        
        if not chroma_sonuclar["ids"] or not chroma_sonuclar["ids"][0]:
            return {"mesaj": "Galeri boş veya sonuç bulunamadı.", "sonuclar": []}
            
        id_listesi = [int(''.join(filter(str.isdigit, id_str))) for id_str in chroma_sonuclar["ids"][0]]
        mesafeler = chroma_sonuclar["distances"][0]
        
        fotograflar = db.query(models.Foto).filter(models.Foto.id.in_(id_listesi)).all()
        
        son_liste = []
        for i, foto_id in enumerate(id_listesi):
            # Görsel arama için de aynı yeni matematiksel formülü uyguluyoruz
            skor = mesafeler[i]
            
            kosinus_benzerligi = 1.0 - skor
            
            # Görselden görsele aramalarda (Text'e göre) benzerlik değerleri biraz daha yüksek çıkabilir.
            # Eşik değerlerini 0.15 - 0.32 olarak koruyalım, gerekirse bunu 0.20 - 0.40 olarak değiştirebiliriz.
            gercek_yuzde = ((kosinus_benzerligi - 0.15) / (0.32 - 0.15)) * 100
            gercek_yuzde = max(0.0, min(100.0, gercek_yuzde))
            gercek_yuzde = round(gercek_yuzde, 1)

            # Sadece %40 barajını geçenleri listeye ekle
            if gercek_yuzde >= 40.0:
                foto = next((f for f in fotograflar if f.id == foto_id), None)
                if foto:
                    son_liste.append({
                        "id": foto.id,
                        "baslik": foto.baslik,
                        "aciklama": foto.aciklama,
                        "dosya_yolu": foto.dosya_yolu,
                        "eslesme_yuzdesi": gercek_yuzde
                    })
                
        son_liste.sort(key=lambda x: x["eslesme_yuzdesi"], reverse=True)
        
        if not son_liste:
            return {"mesaj": "Bu görsele yeterince benzeyen bir fotoğraf bulunamadı.", "sonuclar": []}

        return {"aranan_kelime": "Yüklenen Görsel", "sonuclar": son_liste}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Görsel arama sırasında hata oluştu: {str(e)}")

    
# ---------------------------------------------------------
# 2. FOTOĞRAF EKLEME ENDPOINT'İ
# ---------------------------------------------------------
@router.post("/foto-ekle/")
async def foto_ekle(
    dosya: UploadFile = File(...),
    baslik: str = Form(...),
    aciklama: str = Form(""),
    db: Session = Depends(get_db),
    chroma_collection = Depends(get_chroma)
):
    try:
        os.makedirs("uploads", exist_ok=True)
        dosya_yolu = f"uploads/{dosya.filename}"
        with open(dosya_yolu, "wb") as f:
            f.write(await dosya.read())
        
        yeni_foto = models.Foto(baslik=baslik, aciklama=aciklama, dosya_yolu=dosya_yolu)
        db.add(yeni_foto)
        db.commit()
        db.refresh(yeni_foto)
        
        resim = Image.open(dosya_yolu).convert("RGB")
        vektor = get_image_embedding(resim)
        
        chroma_collection.add(
            embeddings=[vektor],
            documents=[aciklama or baslik],
            metadatas=[{"baslik": baslik, "dosya_yolu": dosya_yolu}],
            ids=[str(yeni_foto.id)]
        )
        
        return {"mesaj": "Fotoğraf başarıyla eklendi!", "id": yeni_foto.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fotoğraf eklenirken hata oluştu: {str(e)}")


# ---------------------------------------------------------
# 3. TÜM FOTOĞRAFLARI LİSTELEME ENDPOINT'İ
# ---------------------------------------------------------
@router.get("/fotograflar/")
def fotograflari_getir(db: Session = Depends(get_db)):
    try:
        fotograflar = db.query(models.Foto).all()
        return fotograflar
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fotoğraflar getirilirken hata oluştu: {str(e)}")


# ---------------------------------------------------------
# 4. GEMINI YAPAY ZEKA SOHBET ENDPOINT'İ
# ---------------------------------------------------------
@router.post("/foto-sohbet/{foto_id}")
def foto_sohbet(
    foto_id: int, 
    soru: str = Form(...), 
    db: Session = Depends(get_db)
):
    try:
        foto = db.query(models.Foto).filter(models.Foto.id == foto_id).first()
        
        if not foto:
            raise HTTPException(status_code=404, detail="Fotoğraf bulunamadı.")
            
        print(f"🤖 Gemini'ye soruluyor... Foto Yolu: {foto.dosya_yolu} | Soru: {soru}")
        
        yapay_zeka_cevabi = gemini_foto_analiz(foto.dosya_yolu, soru)
        
        print(f"✅ Gemini Cevabı alındı.")
        
        return {"cevap": yapay_zeka_cevabi}
        
    except Exception as e:
        print(f"❌ SOHBET HATASI: {str(e)}")
        return {"cevap": f"Sunucu hatası oluştu: {str(e)}"}

# ---------------------------------------------------------
# 5. FOTOĞRAF SİLME ENDPOINT'İ
# ---------------------------------------------------------
@router.delete("/foto-sil/{foto_id}")
def fotograf_sil(
    foto_id: int, 
    db: Session = Depends(get_db),
    chroma_collection = Depends(get_chroma)
):
    try:
        foto = db.query(models.Foto).filter(models.Foto.id == foto_id).first()
        if not foto:
            raise HTTPException(status_code=404, detail="Silinecek fotoğraf bulunamadı.")

        if os.path.exists(foto.dosya_yolu):
            os.remove(foto.dosya_yolu)

        try:
            chroma_collection.delete(ids=[str(foto.id)])
        except Exception as e:
            print(f"⚠️ ChromaDB'den silinirken uyarı: {e}")

        db.delete(foto)
        db.commit()

        return {"mesaj": "Fotoğraf tüm sistemlerden başarıyla silindi."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Silme işlemi sırasında hata oluştu: {str(e)}")