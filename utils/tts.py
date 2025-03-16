import os
import asyncio
from typing import Optional, Dict, List
import edge_tts
import tempfile

class TTSManager:
    def __init__(self):
        self.available_voices = None
        self.current_voice = None

    async def _generate_speech(self, text: str, output_path: str, voice: str, rate: str = "+0%", volume: str = "+0%"):
        """Edge TTS ile ses oluştur"""
        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
        await communicate.save(output_path)
        return output_path

    def text_to_speech(self,
                      text: str,
                      output_path: str,
                      language: str = "tr-TR",
                      voice: Optional[str] = None,
                      rate: str = "+0%",
                      volume: str = "+0%") -> Dict[str, str]:
        """Metni sese çevir"""
        try:
            if not voice:
                # Varsayılan Türkçe ses
                voice = "tr-TR-AhmetNeural"
            
            # Asenkron fonksiyonu senkron olarak çalıştır
            asyncio.run(self._generate_speech(text, output_path, voice, rate, volume))
            
            return {
                "status": "success",
                "output_path": output_path,
                "voice_used": voice,
                "language": language
            }
        except Exception as e:
            raise Exception(f"Ses oluşturma başarısız: {str(e)}")

    async def _get_voices(self) -> List[Dict]:
        """Kullanılabilir sesleri getir"""
        return await edge_tts.list_voices()

    def get_available_voices(self) -> List[Dict]:
        """Kullanılabilir sesleri listele"""
        try:
            if self.available_voices is None:
                self.available_voices = asyncio.run(self._get_voices())
            return self.available_voices
        except Exception as e:
            raise Exception(f"Ses listesi alınamadı: {str(e)}")

    def get_voices_by_language(self, language: str) -> List[Dict]:
        """Belirli bir dil için kullanılabilir sesleri getir"""
        voices = self.get_available_voices()
        return [voice for voice in voices if voice["Locale"].startswith(language)]

    def get_supported_languages(self) -> List[str]:
        """Desteklenen dilleri getir"""
        voices = self.get_available_voices()
        return list(set(voice["Locale"] for voice in voices))

    def validate_voice(self, voice: str) -> bool:
        """Ses adının geçerliliğini kontrol et"""
        voices = self.get_available_voices()
        return any(v["ShortName"] == voice for v in voices) 