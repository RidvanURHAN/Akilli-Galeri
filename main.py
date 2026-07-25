from fastapi import FastAPI
import models
from database import engine
from routers import sorular
from routers import galeri
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=engine)

# FastAPI'yi başlatıyoruz
app = FastAPI()

# Router'ı ana uygulamaya bağla
app.include_router(sorular.router)
app.include_router(galeri.router)

# Eğer 'uploads' adında bir klasör yoksa otomatik oluştur
os.makedirs("uploads", exist_ok=True)

# Bu klasörü dış dünyaya aç (Böylece tarayıcıdan resimler görüntülenebilir)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/", response_class=HTMLResponse)
def anasayfa():
    # Dosyayı Python ile kendimiz okuyup zorla HTML olarak gönderiyoruz
    with open("static/index.html", "r", encoding="utf-8") as f:
        html_icerik = f.read()
    return html_icerik