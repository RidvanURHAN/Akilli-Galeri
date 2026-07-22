from pydantic import BaseModel

class KullaniciMesaji(BaseModel):
    isim: str
    soru: str

class CevapMesaji(BaseModel):
    cevap: str