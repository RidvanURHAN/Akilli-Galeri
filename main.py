from fastapi import FastAPI
import models
from database import engine
from routers import sorular

# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=engine)

# FastAPI'yi başlatıyoruz
app = FastAPI()

# Router'ı ana uygulamaya bağla
app.include_router(sorular.router)