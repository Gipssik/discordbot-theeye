import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')

HEADERS = {
    'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True'}

CHANNELS = {
    'JS': 902298180689997866,
    'LOG': 902606229480828988,
    'MUSIC': 817446784569442314,
}

DELETE_MESSAGES = {
}

JS_USERS = {
}
