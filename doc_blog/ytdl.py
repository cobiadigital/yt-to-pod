import json
import yt_dlp

class YTDLogger:
    def debug(self, msg):
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        print(msg)

def ytd_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now post-processing ...')


def get_yt_info(url):
    ydl_opts = {
        'logger': YTDLogger(),
        'progress_hooks': [ytd_hook],
        'nocheckcertificate': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info



def get_yt_download(url, file_name):
    ydl_opts = {
        'nocheckcertificate': True,
        'format': 'mp3/bestaudio/best',
        'outtmpl': file_name,
        'restrict-filenames': True,
        'paths': {
            'temp': 'temp',
            'home': 'downloads',
        },
    # 'postprocessors': [{  # Extract audio using ffmpeg
    #     'key': 'FFmpegExtractAudio',
    #     'preferredcodec': 'mp3',
    # }]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error = ydl.download(url)
        return error


