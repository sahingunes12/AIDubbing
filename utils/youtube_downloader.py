import os
import yt_dlp

class YouTubeDownloader:
    def __init__(self, download_path=None):
        if download_path is None:
            self.download_path = os.path.join(os.getcwd(), "downloads")
        else:
            self.download_path = download_path
        os.makedirs(self.download_path, exist_ok=True)

    def download_video(self, url: str) -> str:
        """YouTube videosunu indirir ve belirtilen dizine kaydeder."""
        try:
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'noplaylist': True  # Sadece tek bir video indir
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info_dict)
            
            return filename
        except Exception as e:
            raise Exception(f"Video indirme işlemi başarısız: {str(e)}")