import re
import json
from httplib2 import Http
from bot import LOGGER, G_DRIVE_CLIENT_ID, G_DRIVE_CLIENT_SECRET
from bot.config import Messages,BotCommands
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from oauth2client.client import OAuth2WebServerFlow, FlowExchangeError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bot.helpers.sql_helper import gDriveDB
from bot.helpers.utils import CustomFilters
from bot.helpers.gdrive_utils import GoogleDrive
from bot.helpers.sql_helper import idsDB
from bot import LOGGER


OAUTH_SCOPE = "https://www.googleapis.com/auth/drive"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"

flow = None

@Client.on_message(filters.private & filters.incoming & filters.command(BotCommands.Authorize))
async def _auth(client, message):
  user_id = message.from_user.id
  creds = gDriveDB.search(user_id)
  if creds is not None:
    creds.refresh(Http())
    gDriveDB._set(user_id, creds)
    await message.reply_text(Messages.ALREADY_AUTH, quote=True)
  else:
    global flow
    try:
      flow = OAuth2WebServerFlow(
              G_DRIVE_CLIENT_ID,
              G_DRIVE_CLIENT_SECRET,
              OAUTH_SCOPE,
              redirect_uri=REDIRECT_URI
      )
      auth_url = flow.step1_get_authorize_url()
      LOGGER.info(f'AuthURL:{user_id}')
      await message.reply_text(
        text=Messages.AUTH_TEXT.format(auth_url),
        quote=True,
        reply_markup=InlineKeyboardMarkup(
                  [[InlineKeyboardButton("Authorization URL", url=auth_url)]]
              )
        )
    except Exception as e:
      await message.reply_text(f"**ERROR:** ```{e}```", quote=True)

@Client.on_message(filters.private & filters.incoming & filters.command(BotCommands.Revoke) & CustomFilters.auth_users)
def _revoke(client, message):
  user_id = message.from_user.id
  try:
    gDriveDB._clear(user_id)
    LOGGER.info(f'Revoked:{user_id}')
    message.reply_text(Messages.REVOKED, quote=True)
  except Exception as e:
    message.reply_text(f"**ERROR:** ```{e}```", quote=True)


@Client.on_message(filters.private & filters.incoming & filters.text & ~CustomFilters.auth_users)
async def _token(client, message):
  token = message.text.split()[-1]
  WORD = len(token)
  if WORD == 62 and token[1] == "/":
    creds = None
    global flow
    if flow:
      try:
        user_id = message.from_user.id
        sent_message = await message.reply_text("🕵️**Checking received code...**", quote=True)
        creds = flow.step2_exchange(message.text)
        gDriveDB._set(user_id, creds)
        LOGGER.info(f'AuthSuccess: {user_id}')
        await sent_message.edit(Messages.AUTH_SUCCESSFULLY)
        flow = None
      except FlowExchangeError:
        await sent_message.edit(Messages.INVALID_AUTH_CODE)
      except Exception as e:
        await sent_message.edit(f"**ERROR:** ```{e}```")
    else:
        await message.reply_text(Messages.FLOW_IS_NONE, quote=True)

@Client.on_message(filters.private & filters.incoming & filters.command(BotCommands.SetFolder) & CustomFilters.auth_users)
def _set_parent(client, message):
  user_id = message.from_user.id
  if len(message.command) > 1:
    link = message.command[1]
    if not 'clear' in link:
      sent_message = message.reply_text('🕵️**Checking Link...**', quote=True)
      gdrive = GoogleDrive(user_id)
      try:
        result, file_id = gdrive.checkFolderLink(link)
        if result:
          idsDB._set(user_id, file_id)
          LOGGER.info(f'SetParent:{user_id}: {file_id}')
          sent_message.edit(Messages.PARENT_SET_SUCCESS.format(file_id, BotCommands.SetFolder[0]))
        else:
          sent_message.edit(file_id)
      except IndexError:
        sent_message.edit(Messages.INVALID_GDRIVE_URL)
    else:
      idsDB._clear(user_id)
      message.reply_text(Messages.PARENT_CLEAR_SUCCESS, quote=True)
  else:
    message.reply_text(Messages.CURRENT_PARENT.format(idsDB.search_parent(user_id), BotCommands.SetFolder[0]), quote=True)

@Client.on_message(filters.private & filters.incoming & filters.command(BotCommands.Clone) & CustomFilters.auth_users)
def _clone(client, message):
  user_id = message.from_user.id
  if len(message.command) > 1:
    link = message.command[1]
    LOGGER.info(f'Copy:{user_id}: {link}')
    sent_message = message.reply_text(Messages.CLONING.format(link), quote=True)
    msg = GoogleDrive(user_id).clone(link)
    sent_message.edit(msg)
  else:
    message.reply_text(Messages.PROVIDE_GDRIVE_URL.format(BotCommands.Clone[0]))

