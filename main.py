import os
import streamlit as st
from utils.audio_processing import AudioProcessor
from utils.translation import TranslationManager
from utils.tts import TTSManager
from utils.video_processing import VideoProcessor
import tempfile
import hydralit_components as hc
from streamlit_option_menu import option_menu
from utils.youtube_downloader import YouTubeDownloader

# Sayfa yapılandırması
st.set_page_config(
    page_title="AI Dubbing Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Stilleri
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
    }
    .stButton>button:hover {
        background-color: #FF2B2B;
    }
    div[data-testid="stExpander"] {
        border: none;
        border-radius: 0.5rem;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important;
    }
    .sidebar-content {
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Başlık ve açıklama
with hc.HyLoader('AI Dubbing Studio',hc.Loaders.standard_loaders,index=3):
    st.title("🎬 AI Dubbing Studio")

st.markdown("""
<div style='background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-bottom: 2rem;'>
    <h4>🤖 Yapay Zeka Destekli Video Dublaj Sistemi</h4>
    <p>Bu uygulama, yapay zeka teknolojilerini kullanarak videolarınızı otomatik olarak dublaj yapmanıza olanak sağlar.</p>
</div>
""", unsafe_allow_html=True)

# Sınıf örneklerini oluştur
@st.cache_resource
def load_processors():
    return {
        "audio": AudioProcessor(),
        "translation": TranslationManager(),
        "tts": TTSManager(),
        "video": VideoProcessor()
    }

processors = load_processors()

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/video-editing.png", width=100)
    
    with st.container():
        st.markdown("### ⚙️ Ayarlar")
        
        # Sekmeler
        selected_tab = option_menu(
            menu_title=None,
            options=["Çeviri", "Ses", "Video"],
            icons=["translate", "mic", "camera-video"],
            default_index=0,
            orientation="horizontal",
        )
        
        st.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)
        
        if selected_tab == "Çeviri":
            # Çeviri ayarları
            translation_method = st.radio(
                "🌐 Çeviri Yöntemi",
                ["Google Translate", "DeepL API"],
                help="Çeviri için kullanılacak servisi seçin"
            )

            # Dil listesini al
            languages = processors["translation"].get_language_list()
            language_options = {lang["name"]: lang["code"] for lang in languages}
            
            # Kaynak dil seçimi
            source_lang_name = st.selectbox(
                "🔤 Kaynak Dil",
                ["Otomatik Algıla"] + list(language_options.keys()),
                help="Video içeriğinin dilini seçin"
            )
            source_lang = None if source_lang_name == "Otomatik Algıla" else language_options[source_lang_name]

            # Hedef dil seçimi
            target_lang_name = st.selectbox(
                "🎯 Hedef Dil",
                list(language_options.keys()),
                index=list(language_options.keys()).index("İngilizce"),
                help="Çeviri yapılacak dili seçin"
            )
            target_lang = language_options[target_lang_name]

            # Gemini AI düzeltme seçeneği
            use_gemini = st.checkbox(
                "🤖 Gemini AI ile Çeviriyi İyileştir",
                value=True,
                help="Google AI Studio'yu kullanarak çeviriyi daha doğal hale getirir"
            )

            if translation_method == "DeepL API":
                deepl_key = st.text_input(
                    "🔑 DeepL API Anahtarı",
                    type="password",
                    help="DeepL API anahtarınızı girin"
                )
                if deepl_key:
                    os.environ["DEEPL_API_KEY"] = deepl_key
        
        elif selected_tab == "Ses":
            # TTS ayarları
            available_voices = processors["tts"].get_voices_by_language("tr-TR")
            voice_names = [voice["ShortName"] for voice in available_voices]

            selected_voice = st.selectbox(
                "🎤 TTS Sesi",
                voice_names,
                index=voice_names.index("tr-TR-AhmetNeural") if "tr-TR-AhmetNeural" in voice_names else 0,
                help="Seslendirme için kullanılacak sesi seçin"
            )

            voice_speed = st.slider(
                "⚡ Konuşma Hızı",
                min_value=-50,
                max_value=50,
                value=0,
                help="Konuşma hızını ayarlayın (-50: yavaş, +50: hızlı)"
            )

            voice_volume = st.slider(
                "🔊 Ses Seviyesi",
                min_value=-50,
                max_value=50,
                value=0,
                help="Ses seviyesini ayarlayın (-50: kısık, +50: yüksek)"
            )
        
        elif selected_tab == "Video":
            # Video ayarları
            st.markdown("#### 📹 Video Ayarları")
            video_quality = st.select_slider(
                "Video Kalitesi",
                options=["Düşük", "Orta", "Yüksek"],
                value="Orta",
                help="Çıktı video kalitesini seçin"
            )
            
            keep_original_audio = st.checkbox(
                "Orijinal Sesi Koru",
                value=False,
                help="Orijinal ses ile dublajı karıştır"
            )
            
            if keep_original_audio:
                original_volume = st.slider(
                    "Orijinal Ses Seviyesi",
                    min_value=0,
                    max_value=100,
                    value=20,
                    help="Orijinal sesin seviyesini ayarlayın"
                )
        
        st.markdown("</div>", unsafe_allow_html=True)

# Ana panel
uploaded_file = st.file_uploader(
    "📁 Video Yükle",
    type=["mp4", "mov", "avi"],
    help="Dublaj yapılacak videoyu seçin"
)

# YouTube video indirme kısmı
st.header("YouTube Video İndirme")
youtube_url = st.text_input("YouTube Video Linki Girin:")

if st.button("Videoyu İndir"):
    if youtube_url:
        downloader = YouTubeDownloader()
        try:
            video_path = downloader.download_video(youtube_url)
            st.success(f"Video başarıyla indirildi: {video_path}")
            # İndirilen videoyu önizleme
            st.video(video_path)
        except Exception as e:
            st.error(f"İndirme hatası: {str(e)}")
    else:
        st.warning("Lütfen geçerli bir YouTube linki girin.")

if uploaded_file:
    try:
        # Geçici dizin oluştur
        temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Video dosyası için geçici yol
        video_path = os.path.join(temp_dir, "input_video.mp4")
        
        # Dosyayı kaydet
        with open(video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            f.flush()
            os.fsync(f.fileno())
        
        # Dosyanın var olduğunu kontrol et
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video dosyası kaydedilemedi: {video_path}")
            
        # Video önizleme
        st.video(video_path)
        
        try:
            # Video analizi
            with st.expander("📊 Video Analizi", expanded=False):
                video_info = processors["video"].analyze_video(video_path)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("##### 📹 Video Bilgileri")
                    st.write(f"▶️ Süre: {video_info['duration']:.2f} saniye")
                    st.write(f"🎞️ FPS: {video_info['fps']:.2f}")
                    st.write(f"📐 Boyut: {video_info['size'][0]}x{video_info['size'][1]}")
                    st.write(f"📺 Format: {video_info['format']}")
                
                with col2:
                    st.markdown("##### 🎥 Video Detayları")
                    st.write(f"🎬 Video Codec: {video_info['codec']}")
                    st.write(f"📊 Video Bitrate: {int(video_info['bitrate'])/1000:.0f} Kbps")
                    st.write(f"🎨 Pixel Format: {video_info['pixel_format']}")
                
                if 'audio_codec' in video_info:
                    with col3:
                        st.markdown("##### 🔊 Ses Detayları")
                        st.write(f"🎵 Ses Codec: {video_info['audio_codec']}")
                        st.write(f"🎧 Ses Kanalları: {video_info['audio_channels']}")
                        st.write(f"📊 Örnekleme Hızı: {video_info['audio_sample_rate']} Hz")
                        if video_info['audio_bitrate'] != '0':
                            st.write(f"📊 Ses Bitrate: {int(video_info['audio_bitrate'])/1000:.0f} Kbps")
        except Exception as e:
            st.warning(f"⚠️ Video analizi yapılamadı: {str(e)}")
            st.info("Video işlemeye devam edebilirsiniz.")
        
        # İşlem adımları
        if st.button("🎯 Dublaj Sürecini Başlat", help="Tıklayarak dublaj işlemini başlatın"):
            with st.spinner("🔄 İşlem yapılıyor..."):
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # 1. Ses çıkarma
                    status_text.write("1️⃣ Ses dosyası çıkarılıyor...")
                    audio_path = os.path.join(temp_dir, "extracted_audio.wav")
                    audio_path = processors["audio"].extract_audio(video_path, audio_path)
                    progress_bar.progress(20)
                    
                    # 2. Konuşma tanıma
                    status_text.write("2️⃣ Konuşma metne çevriliyor...")
                    speech_result = processors["audio"].speech_to_text(audio_path)
                    progress_bar.progress(40)
                    
                    with st.expander("📝 Algılanan Metin", expanded=True):
                        st.write(speech_result["text"])
                    
                    # 3. Çeviri
                    status_text.write("3️⃣ Metin çevriliyor...")
                    translation_result = processors["translation"].translate_text(
                        speech_result["text"],
                        target_lang=target_lang,
                        source_lang=source_lang,
                        method="deepl" if translation_method == "DeepL API" else "google",
                        improve_with_gemini=use_gemini
                    )
                    progress_bar.progress(60)
                    
                    with st.expander("🌐 Çeviri Sonuçları", expanded=True):
                        st.markdown("##### 📝 Kaynak Metin")
                        st.write(f"**Dil:** {translation_result['source_lang_name']} ({translation_result['source_lang']})")
                        st.write(speech_result["text"])
                        
                        st.markdown("##### 🎯 Çeviri")
                        st.write(f"**Dil:** {translation_result['target_lang_name']} ({translation_result['target_lang']})")
                        st.write(f"**Metod:** {translation_result['method']}")
                        
                        if translation_result.get('original_translation'):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Google Translate Çevirisi:**")
                                st.write(translation_result['original_translation'])
                            with col2:
                                st.markdown("**Gemini ile İyileştirilmiş Çeviri:**")
                                st.write(translation_result['translated_text'])
                        else:
                            st.write(translation_result['translated_text'])
                    
                    # 4. TTS
                    status_text.write("4️⃣ Metin seslendiriliyor...")
                    tts_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
                    tts_result = processors["tts"].text_to_speech(
                        translation_result["translated_text"],
                        tts_output,
                        voice=selected_voice,
                        rate=f"{voice_speed:+d}%",
                        volume=f"{voice_volume:+d}%"
                    )
                    progress_bar.progress(80)
                    
                    # 5. Video birleştirme
                    status_text.write("5️⃣ Video ve ses birleştiriliyor...")
                    output_path = "dubbed_video.mp4"
                    merge_result = processors["video"].merge_audio_video(
                        video_path,
                        tts_result["output_path"],
                        output_path
                    )
                    progress_bar.progress(100)
                    status_text.empty()
                    
                    # Sonuç gösterimi
                    st.success("✅ Dublaj işlemi tamamlandı!")
                    st.video(output_path)
                    
                    # İndirme butonu
                    with open(output_path, "rb") as file:
                        st.download_button(
                            label="📥 Dublajlı Videoyu İndir",
                            data=file,
                            file_name="dubbed_video.mp4",
                            mime="video/mp4"
                        )
                    
                except Exception as e:
                    st.error(f"❌ Hata oluştu: {str(e)}")
                
                finally:
                    # Geçici dosyaları temizle
                    try:
                        import shutil
                        shutil.rmtree(temp_dir)
                    except:
                        pass
    except Exception as e:
        st.error(f"❌ Video yükleme hatası: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🎥 <strong>AI Dubbing Studio</strong> | Yapay Zeka Destekli Video Dublaj Sistemi</p>
    <p style='font-size: 0.8em;'>Powered by OpenAI Whisper, Edge TTS, and DeepL</p>
</div>
""", unsafe_allow_html=True) 