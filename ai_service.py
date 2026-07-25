from sentence_transformers import SentenceTransformer

# 1. GLOBAL YÜKLEME (SINGLETON)
# FastAPI sunucusu (uvicorn) başlatıldığında bu dosya bir kez okunur.
# Model RAM'e sadece bir kere alınır ve hazırda bekletilir.
print("Yapay Zeka Modeli (all-MiniLM-L6-v2) RAM'e yükleniyor... Lütfen bekleyin.")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model başarıyla yüklendi ve kullanıma hazır!")

# 2. SERVİS FONKSİYONU
def get_embedding(metin: str) -> list[float]:
    """
    Kullanıcıdan gelen metni veya fotoğraf açıklamasını alır,
    384 boyutlu vektöre (sayı listesine) çevirip döndürür.
    """
    # model.encode() bize Numpy formatında bir dizi verir.
    # ChromaDB standart Python listesi beklediği için .tolist() ile çeviriyoruz.
    vektor = model.encode(metin).tolist()
    
    return vektor