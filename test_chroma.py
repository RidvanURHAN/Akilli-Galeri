import chromadb
from sentence_transformers import SentenceTransformer

# 1. AI Modelini Yükle
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. ChromaDB'yi Başlat (PersistentClient = Veriyi fiziksel olarak diske kaydeder)
# Proje dizininde "chroma_data" adında bir klasör oluşturup verileri oraya yazacak.
client = chromadb.PersistentClient(path="./chroma_data")

# 3. Koleksiyon (Tablo) Oluştur veya Varsa Getir
koleksiyon = client.get_or_create_collection(name="galeri_hafizasi")

# 4. Kaydedilecek Veriyi Hazırla
metin = "Sahilde oynayan sevimli bir köpek."

# Numpy dizisini ChromaDB'nin anlayabilmesi için standart Python listesine çeviriyoruz (.tolist())
vektor = model.encode(metin).tolist() 

# 5. Vektörü Veritabanına Ekle
koleksiyon.add(
    embeddings=[vektor],           # 384 boyutlu sayı listesi (Neye benzediği)
    documents=[metin],             # Orijinal metin (Kullanıcıya göstermek için)
    metadatas=[{"sqlite_id": 42}], # Köprü: Bu vektör SQLite'taki 42 numaralı fotoğrafa ait!
    ids=["foto_42_vektor"]         # ChromaDB'nin içindeki benzersiz kimliği
)

print("Veri başarıyla ChromaDB'ye kaydedildi! Proje dizininde 'chroma_data' klasörünü görebilirsin.")