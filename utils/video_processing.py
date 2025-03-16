import os
from typing import Dict, Optional
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
import ffmpeg
import mediapipe as mp
import numpy as np
import subprocess

class VideoProcessor:
    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
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

    def analyze_video(self, video_path: str) -> Dict[str, any]:
        """Video özelliklerini analiz et"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video dosyası bulunamadı: {video_path}")

        try:
            video_info = {}
            
            # MoviePy ile temel bilgileri al
            try:
                with VideoFileClip(video_path) as video:
                    video_info.update({
                        "duration": video.duration,
                        "fps": video.fps,
                        "size": video.size,
                        "path": video_path
                    })
            except Exception as e:
                print(f"MoviePy ile analiz hatası: {str(e)}")
                video_info.update({
                    "duration": 0,
                    "fps": 0,
                    "size": (0, 0),
                    "path": video_path
                })

            # FFmpeg kontrolü
            if not self._check_ffmpeg():
                raise Exception("FFmpeg yüklü değil veya bulunamıyor")

            # FFmpeg ile detaylı bilgileri al
            try:
                # FFprobe komutunu doğrudan çalıştır
                cmd = [
                    self.ffprobe_path,
                    '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_format',
                    '-show_streams',
                    video_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                probe = eval(result.stdout)  # JSON string'i dict'e çevir

                video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
                audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
                
                if video_stream:
                    # Video akışı bilgileri
                    video_info.update({
                        "codec": video_stream.get('codec_name', 'unknown'),
                        "bitrate": video_stream.get('bit_rate', '0'),
                        "format": probe['format'].get('format_name', 'unknown'),
                        "pixel_format": video_stream.get('pix_fmt', 'unknown')
                    })
                    
                    # Eğer MoviePy başarısız olduysa, FFmpeg'den al
                    if video_info["fps"] == 0:
                        video_info["fps"] = eval(video_stream.get('r_frame_rate', '0/1'))
                    if video_info["size"] == (0, 0):
                        video_info["size"] = (
                            int(video_stream.get('width', 0)),
                            int(video_stream.get('height', 0))
                        )
                    if video_info["duration"] == 0:
                        video_info["duration"] = float(probe['format'].get('duration', 0))

                if audio_stream:
                    # Ses akışı bilgileri
                    video_info.update({
                        "audio_codec": audio_stream.get('codec_name', 'unknown'),
                        "audio_channels": audio_stream.get('channels', 0),
                        "audio_sample_rate": audio_stream.get('sample_rate', '0'),
                        "audio_bitrate": audio_stream.get('bit_rate', '0')
                    })

            except subprocess.SubprocessError as e:
                print(f"FFprobe komutu hatası: {str(e)}")
                if "codec" not in video_info:
                    video_info.update({
                        "codec": "unknown",
                        "bitrate": "0",
                        "format": "unknown",
                        "pixel_format": "unknown"
                    })
            except Exception as e:
                print(f"FFmpeg ile analiz hatası: {str(e)}")
                if "codec" not in video_info:
                    video_info.update({
                        "codec": "unknown",
                        "bitrate": "0",
                        "format": "unknown",
                        "pixel_format": "unknown"
                    })

            # Birim dönüşümleri ve düzenlemeler
            try:
                # Bitrate'i sayısal değere çevir
                video_info["bitrate"] = int(float(video_info.get("bitrate", "0")))
                if video_info["bitrate"] == 0 and "format" in probe:
                    video_info["bitrate"] = int(float(probe["format"].get("bit_rate", "0")))
                
                # FPS'i düzelt
                if isinstance(video_info["fps"], str) and '/' in video_info["fps"]:
                    num, den = map(int, video_info["fps"].split('/'))
                    video_info["fps"] = num / den if den != 0 else 0
                
                # Süreyi düzelt
                video_info["duration"] = float(video_info["duration"])
                
            except Exception as e:
                print(f"Birim dönüşümü hatası: {str(e)}")

            return video_info

        except Exception as e:
            raise Exception(f"Video analizi başarısız: {str(e)}")

    def merge_audio_video(self,
                         video_path: str,
                         audio_path: str,
                         output_path: str,
                         sync_offset: float = 0.0,
                         original_audio: bool = False,
                         original_volume: float = 0.2) -> Dict[str, str]:
        """Video ve ses dosyasını birleştir"""
        try:
            video = VideoFileClip(video_path)
            dubbed_audio = AudioFileClip(audio_path)
            
            # Ses senkronizasyonu için offset uygula
            if sync_offset != 0:
                dubbed_audio = dubbed_audio.set_start(sync_offset)
            
            if original_audio:
                # Orijinal sesi al ve sesini kıs
                original_audio = video.audio.volumex(original_volume)
                # İki sesi birleştir
                final_audio = CompositeVideoClip([dubbed_audio, original_audio])
                # Video ve birleştirilmiş sesi birleştir
                final_video = video.set_audio(final_audio)
            else:
                # Sadece dublaj sesini kullan
                final_video = video.set_audio(dubbed_audio)
            
            # Videoyu kaydet
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Kaynakları temizle
            video.close()
            dubbed_audio.close()
            
            return {
                "status": "success",
                "output_path": output_path,
                "duration": final_video.duration
            }
        except Exception as e:
            raise Exception(f"Video birleştirme başarısız: {str(e)}")

    def extract_face_landmarks(self, video_path: str) -> Dict[str, list]:
        """Videodan yüz işaretlerini çıkar"""
        try:
            video = VideoFileClip(video_path)
            landmarks_data = []
            
            for frame in video.iter_frames():
                results = self.face_mesh.process(frame)
                if results.multi_face_landmarks:
                    landmarks = results.multi_face_landmarks[0]
                    landmarks_data.append([
                        [(point.x, point.y, point.z) for point in landmarks.landmark]
                    ])
            
            video.close()
            
            return {
                "status": "success",
                "landmarks": landmarks_data,
                "frame_count": len(landmarks_data)
            }
        except Exception as e:
            raise Exception(f"Yüz işaretleri çıkarma başarısız: {str(e)}")

    def resize_video(self,
                    video_path: str,
                    output_path: str,
                    width: Optional[int] = None,
                    height: Optional[int] = None) -> Dict[str, str]:
        """Video boyutunu değiştir"""
        try:
            video = VideoFileClip(video_path)
            
            if width and height:
                resized_video = video.resize(newsize=(width, height))
            elif width:
                resized_video = video.resize(width=width)
            elif height:
                resized_video = video.resize(height=height)
            
            resized_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac'
            )
            
            video.close()
            resized_video.close()
            
            return {
                "status": "success",
                "output_path": output_path,
                "new_size": (width, height)
            }
        except Exception as e:
            raise Exception(f"Video yeniden boyutlandırma başarısız: {str(e)}")

    def extract_frames(self,
                      video_path: str,
                      output_dir: str,
                      fps: Optional[int] = None) -> Dict[str, any]:
        """Videodan kareleri çıkar"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            video = VideoFileClip(video_path)
            
            if fps is None:
                fps = video.fps
            
            frame_count = 0
            for i, frame in enumerate(video.iter_frames(fps=fps)):
                frame_path = os.path.join(output_dir, f"frame_{i:04d}.jpg")
                frame_image = np.array(frame)
                VideoFileClip._write_frame(frame_image, frame_path)
                frame_count += 1
            
            video.close()
            
            return {
                "status": "success",
                "output_dir": output_dir,
                "frame_count": frame_count,
                "fps": fps
            }
        except Exception as e:
            raise Exception(f"Kare çıkarma başarısız: {str(e)}") 