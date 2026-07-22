from sqlalchemy import Column, Integer, String
from database import Base

# database.py içindeki Base kalıbını kullanarak bir tablo tasarlıyoruz
class KullaniciSorusu(Base):
    # 1. Veritabanındaki tablonun gerçek adı
    __tablename__ = "kullanici_sorulari"

    # 2. Sütunlarımız
    id = Column(Integer, primary_key=True, index=True) # Her soruya özel bir TC Kimlik No gibi eşsiz numara
    isim = Column(String, index=True)                  # Kullanıcının adı
    soru = Column(String)                              # Sorduğu soru
    cevap = Column(String, nullable=True)              # Sistemin vereceği cevap (Başlangıçta boş olabilir)