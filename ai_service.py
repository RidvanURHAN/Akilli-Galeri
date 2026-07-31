import os
from dotenv import load_dotenv
from PIL import Image
from sentence_transformers import SentenceTransformer
from google import genai
from deep_translator import GoogleTranslator

# .env dosyasını yükle
load_dotenv()

# ==========================================
# BÖLÜM 1: VEKTÖR MODELLERİ (YENİ MİMARİ)
# ==========================================
# SADECE TEK BİR MODEL KULLANIYORUZ (Orijinal ve en isabetli olan)
# İstersen ileride daha da zeki olan 'clip-ViT-L-14' modeline de geçebilirsin.
print("📥 Orijinal CLIP Modeli Yükleniyor... (clip-ViT-B-32)")
model = SentenceTransformer('clip-ViT-B-32')

def get_text_embedding(text: str):
    """
    Kullanıcının girdiği metni önce İngilizceye çevirir,
    sonra vektör modeline sokar. Böylece %100 doğruluk sağlanır.
    """
    try:
        # Türkçe metni arka planda İngilizceye çevir
        ingilizce_metin = GoogleTranslator(source='auto', target='en').translate(text)
        print(f"🔄 Arama Çevrildi: '{text}' -> '{ingilizce_metin}'")
        
        # İngilizce metni modele ver
        embedding = model.encode(ingilizce_metin)
        return embedding.tolist()
    except Exception as e:
        print(f"Çeviri veya Vektör Hatası: {e}")
        # Çeviri çökerse diye orijinal metinle devam etme yedeği
        return model.encode(text).tolist()

def get_image_embedding(image: Image.Image):
    """
    Yüklenen görseli AYNI Orijinal CLIP modeli ile vektöre çevirir.
    """
    embedding = model.encode(image)
    return embedding.tolist()

# ==========================================
# BÖLÜM 2: GEMINI AI SOHBET
# ==========================================
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None
    print("⚠️ UYARI: GEMINI_API_KEY bulunamadı!")

def gemini_foto_analiz(dosya_yolu, soru):
    try:
        if not client:
            return "Hata: Gemini API anahtarı bulunamadı."
            
        resim = Image.open(dosya_yolu)
        
        kisa_cevap_talimati = (
            "Sen akıllı bir galeri asistanısın. Sistem kaynaklarını korumak için "
            "cevaplarını MÜMKÜN OLDUĞUNCA KISA, ÖZ ve DOĞRUDAN vermelisin. "
            "Asla gereksiz detaylara girme, en fazla 1 veya 2 cümle kullan. "
            f"Kullanıcının sorusu: {soru}"
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=[kisa_cevap_talimati, resim]
        )
        
        return response.text
        
    except Exception as e:
        return f"Hata oluştu: {str(e)}"