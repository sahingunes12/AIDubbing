# 🎬 AI Dubbing Studio

AI Dubbing Studio, yapay zeka teknolojilerini kullanarak videoları otomatik olarak farklı dillere çeviren ve dublaj yapan bir Python uygulamasıdır.

## 🚀 Özellikler

- 🎥 Video yükleme ve önizleme
- 🔊 Otomatik ses çıkarma
- 📝 Konuşma tanıma (Speech-to-Text)
- 🌐 Çoklu dil desteği ile çeviri (DeepL & Google Translate)
- 🗣️ AI destekli seslendirme (TTS)
- 🎯 Otomatik ses-video senkronizasyonu
- 📊 Detaylı video analizi
- 🎨 Kullanıcı dostu Streamlit arayüzü

## 🛠️ Teknolojiler

- **Frontend:** Streamlit
- **Ses İşleme:** moviepy, ffmpeg-python
- **Konuşma Tanıma:** OpenAI Whisper
- **Çeviri:** DeepL API, Google Translate
- **Seslendirme:** Coqui TTS, Edge TTS
- **Video İşleme:** MoviePy, FFmpeg
- **Yüz Analizi:** MediaPipe

## ⚙️ Kurulum

1. Gerekli Python paketlerini yükleyin:
```bash
pip install -r requirements.txt
```

2. (Opsiyonel) DeepL API anahtarınızı ayarlayın:
```bash
export DEEPL_API_KEY="your-api-key"
```

3. Uygulamayı başlatın:
```bash
streamlit run main.py
```

## 📝 Kullanım

1. Tarayıcınızda `http://localhost:8501` adresine gidin
2. Bir video dosyası yükleyin (MP4, MOV veya AVI)
3. Çeviri yöntemini seçin (DeepL veya Google Translate)
4. TTS modelini seçin
5. "Dublaj Sürecini Başlat" butonuna tıklayın
6. İşlem tamamlandığında dublajlı videoyu indirin

## 🔧 Konfigürasyon

- `utils/audio_processing.py`: Ses işleme ayarları
- `utils/translation.py`: Çeviri servisi ayarları
- `utils/tts.py`: TTS model ayarları
- `utils/video_processing.py`: Video işleme ayarları

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🤝 Katkıda Bulunma

1. Bu depoyu fork edin
2. Yeni bir branch oluşturun (`git checkout -b feature/amazing`)
3. Değişikliklerinizi commit edin (`git commit -m 'Harika özellik eklendi'`)
4. Branch'inizi push edin (`git push origin feature/amazing`)
5. Bir Pull Request oluşturun

## 📞 İletişim

Sorularınız veya önerileriniz için bir Issue açabilirsiniz. 