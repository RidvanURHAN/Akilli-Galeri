from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import chromadb # Yeni ekledik

# ==========================================
# 1. MOTOR: KLASİK VERİTABANI (SQLITE)
# ==========================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./galeri.db"

# SQLite için engine ve session ayarları
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI Router'ları için SQLite Bağımlılığı (Dependency)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 2. MOTOR: VEKTÖR VERİTABANI (CHROMADB)
# ==========================================
# PersistentClient sunucu ayağa kalktığında bir kez çalışır ve diske bağlanır.
# Bu sayede her istekte veritabanına baştan bağlanıp sistemi yormayız.
chroma_client = chromadb.PersistentClient(path="./chroma_data")

# Koleksiyonumuzu global olarak oluşturuyoruz (yoksa yaratır, varsa getirir)
chroma_collection = chroma_client.get_or_create_collection(name="galeri_hafizasi")

# FastAPI Router'ları için ChromaDB Bağımlılığı (Dependency)
def get_chroma():
    # Bu fonksiyon sayesinde router'larda Depends(get_chroma) diyerek
    # koleksiyonu çok temiz bir şekilde çağırabileceğiz.
    return chroma_collection