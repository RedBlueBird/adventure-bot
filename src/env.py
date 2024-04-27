import os

import dotenv

dotenv.load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
APP_ID = os.environ["APP_ID"]
APP_PERMS = int(os.environ["APP_PERMS"])

DB_HOST = os.environ["DB_HOST"]
DB_USER = os.environ["DB_USER"]
DB_PW = os.environ["DB_PW"]
DB_DB = os.environ["DB_DB"]

SYNC_CMD_GLOBALLY = os.environ["SYNC_CMD_GLOBALLY"].lower() in ("true", "1", "t")
