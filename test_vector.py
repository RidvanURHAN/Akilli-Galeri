from sentence_transformers import SentenceTransformer

# 1. Modeli Yükle: "all-MiniLM-L6-v2" çok hafif ve hızlı bir modeldir.
# Not: Kodu ilk çalıştırdığında modeli internetten (yaklaşık 80MB) indirir.
# Sonraki çalışmalarda direkt bilgisayarından okur, internet istemez.
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Anlamını bulmak istediğimiz metin
metin = "Sahilde oynayan sevimli bir köpek."

# 3. Metni Vektöre (sayılara) Çevir (İşte sihir burada gerçekleşiyor)
vektor = model.encode(metin)

# Sonuçları görelim
print(f"Orijinal Metin: '{metin}'")
print(f"Vektör Uzunluğu: Bu metin {len(vektor)} farklı boyutta/açıdan sayılara çevrildi.")
print(f"Vektörün İlk 5 Değeri (Koordinatları): {vektor[:5]}")