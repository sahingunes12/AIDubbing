import os
from typing import Dict, Optional, List, Tuple
import deepl
from googletrans import Translator, LANGUAGES
from dotenv import load_dotenv
import requests
import json
from langdetect import detect

load_dotenv()

class TranslationManager:
    def __init__(self):
        self.deepl_api_key = os.getenv("DEEPL_API_KEY")
        self.gemini_api_key = "AIzaSyCwO-DY5GEBJyanvtQGKCWHI-xbrDeDMqU"
        self.deepl_translator = None
        self.google_translator = None
        # Dil isimlerini Türkçe'ye çevir
        self.language_names_tr = {
            'af': 'Afrikaanca', 'sq': 'Arnavutça', 'am': 'Amharca', 'ar': 'Arapça',
            'hy': 'Ermenice', 'az': 'Azerice', 'eu': 'Baskça', 'be': 'Belarusça',
            'bn': 'Bengalce', 'bs': 'Boşnakça', 'bg': 'Bulgarca', 'ca': 'Katalanca',
            'ceb': 'Cebuano', 'ny': 'Chichewa', 'zh-cn': 'Çince (Basit)', 
            'zh-tw': 'Çince (Geleneksel)', 'co': 'Korsikaca', 'hr': 'Hırvatça',
            'cs': 'Çekçe', 'da': 'Danca', 'nl': 'Hollandaca', 'en': 'İngilizce',
            'eo': 'Esperanto', 'et': 'Estonca', 'tl': 'Filipino', 'fi': 'Fince',
            'fr': 'Fransızca', 'fy': 'Frizce', 'gl': 'Galiçyaca', 'ka': 'Gürcüce',
            'de': 'Almanca', 'el': 'Yunanca', 'gu': 'Güceratça', 'ht': 'Haiti Kreolü',
            'ha': 'Hausa', 'haw': 'Hawaii Dili', 'iw': 'İbranice', 'hi': 'Hintçe',
            'hmn': 'Hmong', 'hu': 'Macarca', 'is': 'İzlandaca', 'ig': 'İgbo',
            'id': 'Endonezce', 'ga': 'İrlandaca', 'it': 'İtalyanca', 'ja': 'Japonca',
            'jw': 'Cava Dili', 'kn': 'Kannada', 'kk': 'Kazakça', 'km': 'Kmerce',
            'ko': 'Korece', 'ku': 'Kürtçe', 'ky': 'Kırgızca', 'lo': 'Laoca',
            'la': 'Latince', 'lv': 'Letonca', 'lt': 'Litvanca', 'lb': 'Lüksemburgca',
            'mk': 'Makedonca', 'mg': 'Malgaşça', 'ms': 'Malayca', 'ml': 'Malayalam',
            'mt': 'Maltaca', 'mi': 'Maori', 'mr': 'Marathi', 'mn': 'Moğolca',
            'my': 'Myanmar', 'ne': 'Nepalce', 'no': 'Norveççe', 'ps': 'Peştuca',
            'fa': 'Farsça', 'pl': 'Lehçe', 'pt': 'Portekizce', 'pa': 'Pencapça',
            'ro': 'Romence', 'ru': 'Rusça', 'sm': 'Samoa Dili', 'gd': 'İskoç Gal Dili',
            'sr': 'Sırpça', 'st': 'Sesotho', 'sn': 'Shona', 'sd': 'Sindhi',
            'si': 'Sinhala', 'sk': 'Slovakça', 'sl': 'Slovence', 'so': 'Somalice',
            'es': 'İspanyolca', 'su': 'Sundanca', 'sw': 'Svahili', 'sv': 'İsveççe',
            'tg': 'Tacikçe', 'ta': 'Tamilce', 'te': 'Telugu', 'th': 'Tayca',
            'tr': 'Türkçe', 'uk': 'Ukraynaca', 'ur': 'Urduca', 'uz': 'Özbekçe',
            'vi': 'Vietnamca', 'cy': 'Galce', 'xh': 'Xhosa', 'yi': 'Yidiş',
            'yo': 'Yoruba', 'zu': 'Zulu'
        }

    def _init_deepl(self):
        """DeepL çevirmen nesnesini başlat"""
        if not self.deepl_translator and self.deepl_api_key:
            self.deepl_translator = deepl.Translator(self.deepl_api_key)
        elif not self.deepl_api_key:
            raise ValueError("DeepL API anahtarı bulunamadı!")

    def _init_google(self):
        """Google çevirmen nesnesini başlat"""
        if not self.google_translator:
            self.google_translator = Translator()

    def _improve_with_gemini(self, text: str, translated_text: str, target_lang: str) -> str:
        """Gemini API ile çeviriyi düzelt ve iyileştir"""
        try:
            prompt = f"""Aşağıdaki çeviriyi kontrol et ve gerekirse düzelt. Çeviri daha doğal ve akıcı olmalı:

Orijinal Metin: {text}
Mevcut Çeviri: {translated_text}
Hedef Dil: {target_lang}

Lütfen sadece düzeltilmiş çeviriyi döndür, başka açıklama ekleme."""

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"
            headers = {'Content-Type': 'application/json'}
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

            if 'candidates' in result and len(result['candidates']) > 0:
                improved_text = result['candidates'][0]['content']['parts'][0]['text']
                return improved_text.strip()
            else:
                return translated_text

        except Exception as e:
            print(f"Gemini düzeltme hatası (orijinal çeviri kullanılacak): {str(e)}")
            return translated_text

    def detect_language(self, text: str) -> Tuple[str, str]:
        """Metnin dilini tespit et"""
        try:
            detected = detect(text)
            return detected, self.language_names_tr.get(detected, LANGUAGES.get(detected, detected))
        except Exception as e:
            raise Exception(f"Dil tespiti başarısız: {str(e)}")

    def get_language_list(self) -> List[Dict[str, str]]:
        """Desteklenen dillerin listesini döndür"""
        return [
            {"code": code, "name": self.language_names_tr.get(code, name)}
            for code, name in LANGUAGES.items()
        ]

    def translate_text(self, 
                      text: str, 
                      target_lang: str = "en",
                      source_lang: Optional[str] = None,
                      method: str = "google",
                      improve_with_gemini: bool = True) -> Dict[str, str]:
        """Metni çevir ve opsiyonel olarak Gemini ile düzelt"""
        try:
            # Kaynak dil belirtilmemişse tespit et
            if not source_lang:
                detected_lang, detected_name = self.detect_language(text)
                source_lang = detected_lang

            if method.lower() == "deepl":
                self._init_deepl()
                result = self.deepl_translator.translate_text(
                    text,
                    target_lang=target_lang.upper(),
                    source_lang=source_lang.upper() if source_lang else None
                )
                translated_text = result.text
                detected_source = result.detected_source_lang.lower()
            else:
                self._init_google()
                result = self.google_translator.translate(
                    text,
                    dest=target_lang,
                    src=source_lang if source_lang else 'auto'
                )
                translated_text = result.text
                detected_source = result.src

            # Gemini ile düzeltme yap
            if improve_with_gemini:
                improved_text = self._improve_with_gemini(text, translated_text, target_lang)
                final_text = improved_text
            else:
                final_text = translated_text

            return {
                "translated_text": final_text,
                "original_translation": translated_text if improve_with_gemini else None,
                "source_lang": detected_source,
                "source_lang_name": self.language_names_tr.get(detected_source, LANGUAGES.get(detected_source, detected_source)),
                "target_lang": target_lang,
                "target_lang_name": self.language_names_tr.get(target_lang, LANGUAGES.get(target_lang, target_lang)),
                "method": f"{method}{' + gemini' if improve_with_gemini else ''}"
            }

        except Exception as e:
            raise Exception(f"Çeviri işlemi başarısız: {str(e)}")

    def validate_language_code(self, 
                             lang_code: str, 
                             method: str = "google") -> bool:
        """Dil kodunun geçerliliğini kontrol et"""
        if method.lower() == "gemini":
            return True
            
        if method.lower() == "deepl":
            self._init_deepl()
            supported = self.deepl_translator.get_target_languages()
            return any(lang.code.lower() == lang_code.lower() for lang in supported)
        else:
            return lang_code.lower() in LANGUAGES 