
URL = 'https://www.youtube.com/playlist?list=PLLrbs8Zy9pRj5lGPiex8qGjvc0asc3qUP'

# ℹ️ See help(yt_dlp.YoutubeDL) for a list of available options and public functions
ydl_opts = {
    'nocheckcertificate': True,
}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(URL, download=False)

    # ℹ️ ydl.sanitize_info makes the info json-serializable
    print(json.dumps(ydl.sanitize_info(info)))


import json
import yt_dlp

URL = 'https://www.youtube.com/watch?v=mo-YL-lv3RY'

# ℹ️ See help(yt_dlp.YoutubeDL) for a list of available options and public functions
ydl_opts = {
    'nocheckcertificate': True,
    'format': 'm4A/bestaudio/best',
    'restrict-filenames': True,
    'paths': {
        'temp': 'temp',
        'home': 'downloads',
    },
    # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
    'postprocessors': [{  # Extract audio using ffmpeg
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'm4A',
    }]
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    #error = ydl.download(URL)
    info = ydl.extract_info(URL)
    print(json.dumps(ydl.sanitize_info(info)))

info['title']
info['display_id']
print(info['description'])
info['duration']
info['upload_date']
info
#info['thumbnails'][-1]