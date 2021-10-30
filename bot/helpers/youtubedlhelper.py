import os
import wget
import glob
from bot import DOWNLOAD_DIRECTORY, LOGGER

if os.getenv("downloader") == "youtube-dl":
    import youtube_dl as ytdl
    from youtube_dl import DownloadError
else:
    import yt_dlp as ytdl
    from yt_dlp import DownloadError

def ytdl_download(link):
	ydl_opts = {
		'outtmpl' : os.path.join(DOWNLOAD_DIRCTORY, '%(title).50s.%(ext)s'),
		'restrictfilenames' : False,
		'quiet' : True,
		'logger' : LOGGER,
	}
	formats = [
        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio",
        "bestvideo[vcodec^=avc]+bestaudio[acodec^=mp4a]/best[vcodec^=avc]/best",
        ""
    ]
    # TODO it appears twitter download on macOS will fail. Don't know why...Linux's fine.
    for f in formats:
        if f:
            ydl_opts["format"] = f
	with ytdl.YoutubeDL(ydl_opts) as ydl:
	   try:
		ydl.download([link])
	   except DownloadError as e:
		return False, str(e)
	   for path in glob.glob(os.path.join(DOWNLOAD_DIRECTORY, '*')):
      		if path.endswith(('.avi', '.mov', '.flv', '.wmv', '.3gp','.mpeg', '.webm', '.mp4', '.mkv')) and \
          	path.startswith(ytdl.prepare_filename(meta)):
        		return True, path
   	   return False, 'Something went wrong! No video file exists on server.'
