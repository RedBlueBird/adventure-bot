import os
import sys
import json

import mysql.connector
import mysql.connector.cursor_cext
from mysql.connector import errorcode

db: mysql.connector.connection_cext.CMySQLConnection | None = None
cur: mysql.connector.cursor_cext.CMySQLCursor | None = None
config_path = f"{os.path.realpath(os.path.dirname(__file__))}/../config.json"
if not os.path.isfile(config_path):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(config_path) as config_file:
        config = json.load(config_file)


def init():
    global db, cur

    try:
        db = mysql.connector.connect(
            host=config["db_host"],
            user=config["db_user"],
            passwd=config["db_pw"],
            database=config["db_db"]
        )
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Invalid username/password!")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist!") 
        else:
            print(err)

    cur = db.cursor()


def is_blacklisted(uid: int) -> bool:
    return False


def is_registered(uid: int) -> bool:
    cur.execute(f"SELECT * FROM playersinfo WHERE userid = {uid}")
    return bool(cur.fetchall())


def get_user_level(uid: int) -> int:
    cur.execute(f"SELECT level FROM playersinfo WHERE userid = {uid}")
    return cur.fetchall()[0][0]
