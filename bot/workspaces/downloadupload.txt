import os
import re
import json
import lk21
import requests
import wget
import urllib.parse
from lk21.extractors.bypasser import Bypass
from bs4 import BeautifulSoup
from time import sleep
from pyrogram import Client, filters
from bot.helpers.sql_helper import gDriveDB, idsDB
from bot.helpers.utils import CustomFilters, humanbytes
from bot.helpers.youtubdlhelper import ytdl_download
from bot.helpers.gdrive_utils import GoogleDrive 
from bot import DOWNLOAD_DIRECTORY, LOGGER
from bot.config import Messages, BotCommands
from pyrogram.errors import FloodWait, RPCError

@Client.on_message(filters.private & filters.incoming & filters.text & (filters.command(BotCommands.Download) | filters.regex('^(ht|f)tp*')) & CustomFilters.auth_users)
def _download(client, message):
  user_id = message.from_user.id
  if not message.media:
    sent_message = message.reply_text('🕵️**Checking link...**', quote=True)
    if message.command:
      link = message.command[1]
    else:
      link = message.text
    if 'drive.google.com' in link:
      sent_message.edit(Messages.CLONING.format(link))
      LOGGER.info(f'Copy:{user_id}: {link}')
      msg = GoogleDrive(user_id).clone(link)
      sent_message.edit(msg)
    if 'youtu' in link:
      link = message.text
      LOGGER.info(f'YTDL:{user_id}: {link}')
      sent_message.edit(Messages.DOWNLOADING.format(link))
      result, file_path = ytdl_download(link)
      if result:
        sent_message.edit(Messages.DOWNLOADED_SUCCESSFULLY.format(os.path.basename(file_path), humanbytes(os.path.getsize(file_path))))
        msg = GoogleDrive(user_id).upload_file(file_path)
        sent_message.edit(msg)
        LOGGER.info(f'Deleteing: {file_path}')
        os.remove(file_path)
      else:
        sent_message = message.reply_text('🕵️**PORNHUB ERROR**', quote=True)

@Client.on_message(filters.private & filters.incoming & (filters.document | filters.audio | filters.video | filters.photo) & CustomFilters.auth_users)
def _telegram_file(client, message):
  user_id = message.from_user.id
  sent_message = message.reply_text('🕵️**...ဖိုင်ကိုစစ်ဆေးနေပါသည်....**', quote=True)
  if message.document:
    file = message.document
  elif message.video:
    file = message.video
  elif message.audio:
    file = message.audio
  elif message.photo:
  	file = message.photo
  	file.mime_type = "images/png"
  	file.file_name = f"IMG-{user_id}-{message.message_id}.png"
  sent_message.edit(Messages.DOWNLOAD_TG_FILE.format(file.file_name, humanbytes(file.file_size), file.mime_type))
  LOGGER.info(f'Download:{user_id}: {file.file_id}')
  try:
    file_path = message.download(file_name=DOWNLOAD_DIRECTORY)
    sent_message.edit(Messages.DOWNLOADED_SUCCESSFULLY.format(os.path.basename(file_path), humanbytes(os.path.getsize(file_path))))
    msg = GoogleDrive(user_id).upload_file(file_path, file.mime_type)
    sent_message.reply_text(msg,quote=True)
  except RPCError:
    sent_message.edit(Messages.WENT_WRONG)
  LOGGER.info(f'Deleteing: {file_path}')
  os.remove(file_path)