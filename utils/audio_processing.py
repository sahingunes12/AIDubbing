import os
import whisper
from moviepy.editor import VideoFileClip
import numpy as np
import torch
import librosa
import soundfile as sf
import tempfile
import subprocess

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
            # FFmpeg kontrolü
            if not self._check_ffmpeg():
                raise Exception("FFmpeg yüklü değil veya bulunamıyor")

            # Çıktı dizininin varlığını kontrol et
            os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
            
            try:
                # FFmpeg ile ses çıkarma
                cmd = [
                    self.ffmpeg_path,
                    '-y',  # Varolan dosyanın üzerine yaz
                    '-i', video_path,  # Girdi dosyası
                    '-vn',  # Video akışını devre dışı bırak
                    '-acodec', 'pcm_s16le',  # Ses codec'i
                    '-ar', '16000',  # Örnekleme hızı
                    '-ac', '1',  # Tek kanal (mono)
                    output_audio_path  # Çıktı dosyası
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                
                # Dosyanın oluşturulduğunu ve boyutunun > 0 olduğunu kontrol et
                if not os.path.exists(output_audio_path) or os.path.getsize(output_audio_path) == 0:
                    raise Exception("Ses dosyası oluşturulamadı veya boş")
                
            except (subprocess.SubprocessError, Exception) as e:
                print(f"FFmpeg ses çıkarma hatası: {str(e)}")
                # FFmpeg başarısız olursa MoviePy ile dene
                video = VideoFileClip(video_path)
                if video.audio is None:
                    raise Exception("Video dosyasında ses bulunamadı")
                try:
                    video.audio.write_audiofile(
                        output_audio_path,
                        codec='pcm_s16le',
                        fps=16000,
                        verbose=False,
                        logger=None
                    )
                finally:
                    video.close()
            
            # Son kontrol
            if not os.path.exists(output_audio_path) or os.path.getsize(output_audio_path) == 0:
                raise Exception("Ses dosyası oluşturulamadı veya boş")
            
            return output_audio_path
            
        except Exception as e:
            # Hata durumunda temizlik yap
            if 'video' in locals():
                try:
                    video.close()
                except:
                    pass
            raise Exception(f"Ses çıkarma işlemi başarısız: {str(e)}")

    def speech_to_text(self, audio_path: str, language: str = None) -> dict:
        """Sesi metne çevir"""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Ses dosyası bulunamadı: {audio_path}")
            
        if os.path.getsize(audio_path) == 0:
            raise Exception("Ses dosyası boş")
            
        try:
            # Whisper modelini yükle
            if self.whisper_model is None:
                print("Whisper modeli yükleniyor...")
                self.whisper_model = whisper.load_model("base")
                print("Whisper modeli yüklendi")
            
            # Ses dosyasını kontrol et
            try:
                y, sr = librosa.load(audio_path, sr=None)
                if len(y) == 0:
                    raise Exception("Ses verisi boş")
            except Exception as e:
                print(f"Ses dosyası kontrolü başarısız: {str(e)}")
                # Alternatif yöntem: FFmpeg ile ses dosyasını yeniden kodla
                temp_audio = os.path.join(self.temp_dir, "temp_audio.wav")
                cmd = [
                    self.ffmpeg_path,
                    '-y',
                    '-i', audio_path,
                    '-acodec', 'pcm_s16le',
                    '-ar', '16000',
                    '-ac', '1',
                    temp_audio
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                audio_path = temp_audio
            
            # Konuşma tanıma
            print(f"Konuşma tanıma başlıyor... (Dil: {language if language else 'otomatik'})")
            result = self.whisper_model.transcribe(
                audio_path,
                language=language,
                verbose=True
            )
            print("Konuşma tanıma tamamlandı")
            
            return {
                "text": result["text"],
                "segments": result["segments"],
                "language": result["language"]
            }
        except Exception as e:
            raise Exception(f"Konuşma tanıma işlemi başarısız: {str(e)}")

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