import os
import whisper
from moviepy.editor import VideoFileClip
import numpy as np
import torch
import librosa
import soundfile as sf
import tempfile
import subprocess
import speech_recognition as sr
from pydub import AudioSegment
from pytube import YouTube

class AudioProcessor:
    def __init__(self):
        self.whisper_model = None
        self.temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")
        self.ffprobe_path = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffprobe.exe")
    
    def _check_ffmpeg(self) -> bool:
        """FFmpeg'in yüklü olup olmadığını kontrol et"""
        try:
            if not os.path.exists(self.ffmpeg_path) or not os.path.exists(self.ffprobe_path):
                return False
            subprocess.run([self.ffmpeg_path, '-version'], capture_output=True, check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def load_whisper_model(self):
        """Whisper modelini yükle"""
        if self.whisper_model is None:
            try:
                self.whisper_model = whisper.load_model("base")
            except Exception as e:
                raise Exception(f"Whisper modeli yüklenemedi: {str(e)}")
        return self.whisper_model

    def extract_audio(self, video_path: str, output_audio_path: str = None) -> str:
        """Videodan ses dosyasını çıkar"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video dosyası bulunamadı: {video_path}")

        if output_audio_path is None:
            output_audio_path = os.path.join(self.temp_dir, "extracted_audio.wav")
        
        try:
            # Çıktı dizininin varlığını kontrol et
            os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
            
            # FFmpeg ile ses çıkarma
            command = [
                self.ffmpeg_path,
                "-i", video_path,  # Girdi olarak video dosyasını al
                "-vn",  # Görüntüyü kaldır
                "-acodec", "pcm_s16le",  # WAV formatına çevir
                "-ar", "16000",  # 16 kHz örnekleme hızı
                "-ac", "1",  # Mono kanal
                "-y",  # Varolan dosyanın üzerine yaz
                output_audio_path
            ]
            
            # FFmpeg komutunu çalıştır
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg hatası: {result.stderr}")
            
            # Çıktı dosyasını kontrol et
            if not os.path.exists(output_audio_path) or os.path.getsize(output_audio_path) == 0:
                raise Exception("Ses dosyası oluşturulamadı veya boş")
            
            return output_audio_path
            
        except subprocess.SubprocessError as e:
            # FFmpeg başarısız olursa MoviePy ile dene
            try:
                video = VideoFileClip(video_path)
                if video.audio is None:
                    raise Exception("Video dosyasında ses bulunamadı")
                
                video.audio.write_audiofile(
                    output_audio_path,
                    codec='pcm_s16le',
                    fps=16000,
                    verbose=False,
                    logger=None
                )
                video.close()
                return output_audio_path
                
            except Exception as e:
                # Son çare olarak pydub ile dene
                try:
                    audio_segment = AudioSegment.from_file(video_path)
                    audio_segment.export(output_audio_path, format="wav")
                    return output_audio_path
                except Exception as e:
                    raise Exception(f"Ses çıkarma işlemi başarısız: {str(e)}")

    def speech_to_text(self, audio_path: str, language: str = "en-US") -> dict:
        """Sesi metne çevir"""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Ses dosyası bulunamadı: {audio_path}")
        
        if os.path.getsize(audio_path) == 0:
            raise Exception("Ses dosyası boş")
        
        try:
            # Google Speech Recognition ile ses tanıma
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source)  # Ses verisini oku
                text = recognizer.recognize_google(audio_data, language=language)  # Google API ile tanıma yap
            
            return {
                "text": text,
                "language": language,
                "method": "google"
            }
        
        except Exception as e:
            raise Exception(f"Ses tanıma işlemi başarısız: {str(e)}")

    def get_audio_duration(self, audio_path: str) -> float:
        """Ses dosyasının süresini döndür"""
        try:
            audio = VideoFileClip(audio_path)
            duration = audio.duration
            audio.close()
            return duration
        except Exception as e:
            raise Exception(f"Ses süresi hesaplanamadı: {str(e)}")

    def analyze_audio(self, audio_path: str) -> dict:
        """Ses dosyasının temel özelliklerini analiz et"""
        try:
            y, sr = librosa.load(audio_path)
            duration = librosa.get_duration(y=y, sr=sr)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            
            return {
                "duration": duration,
                "sample_rate": sr,
                "tempo": tempo
            }
        except Exception as e:
            raise Exception(f"Ses analizi başarısız: {str(e)}")

    def extract_audio_from_video(self, video_path, output_path=None):
        """Video dosyasından ses çıkarma"""
        try:
            if output_path is None:
                output_path = os.path.join(self.temp_dir, "extracted_audio.wav")

            video = VideoFileClip(video_path)
            audio = video.audio
            audio.write_audiofile(output_path)
            video.close()
            
            return output_path
        except Exception as e:
            raise Exception(f"Ses çıkarma işlemi başarısız: {str(e)}")

    def split_audio(self, audio_path, segments):
        """Ses dosyasını segmentlere ayırma"""
        try:
            y, sr = librosa.load(audio_path)
            split_files = []
            
            for i, (start, end) in enumerate(segments):
                start_sample = int(start * sr)
                end_sample = int(end * sr)
                segment = y[start_sample:end_sample]
                
                output_path = os.path.join(self.temp_dir, f"segment_{i}.wav")
                sf.write(output_path, segment, sr)
                split_files.append(output_path)
            
            return split_files
        except Exception as e:
            raise Exception(f"Ses bölme işlemi başarısız: {str(e)}")

    def cleanup(self):
        """Geçici dosyaları temizleme"""
        try:
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"Temizleme işlemi sırasında hata: {str(e)}")

    def download_video(self, url: str) -> str:
        """YouTube videosunu indirir ve belirtilen dizine kaydeder."""
        try:
            yt = YouTube(url)
            video = yt.streams.filter(progressive=True, file_extension='mp4').first()
            if video is None:
                raise Exception("İndirilecek uygun bir video bulunamadı.")
            
            video.download(self.download_path)
            return os.path.join(self.download_path, video.default_filename)
        except Exception as e:
            raise Exception(f"Video indirme işlemi başarısız: {str(e)}") 