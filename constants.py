import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
LOCAL = bool(int(os.getenv('LOCAL')))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
IP = os.getenv('IP')
PORT = int(os.getenv('PORT'))
LANG_ID = int(os.getenv('LANG_ID'))

SUBSCRIBE_KEYWORD = 'subscribe_'
UNSUBSCRIBE_KEYWORD = 'unsubscribe_'