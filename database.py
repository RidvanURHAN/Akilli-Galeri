from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Veritabanımızın adresi (SQLite kullanacağımız için bilgisayardaki bir dosya yolu)
SQLALCHEMY_DATABASE_URL = "sqlite:///./galeri.db"

# 2. Motor (Engine): Python ile veritabanı arasındaki köprüyü kurar
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Oturum (Session): Veritabanıyla her konuşmak istediğimizde açacağımız geçici bağlantı
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Temel Kalıp (Base): İleride oluşturacağımız tabloların (örn: Kullanıcılar, Fotoğraflar) şablonu
Base = declarative_base()