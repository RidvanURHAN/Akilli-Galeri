from pydantic import BaseModel

class KullaniciMesaji(BaseModel):
    isim: str
    soru: str

class CevapMesaji(BaseModel):
    cevap: str

class FotoOlustur(BaseModel):
    baslik: str
    aciklama: str
    dosya_yolu: str