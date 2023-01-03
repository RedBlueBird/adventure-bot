import os
import sys
import json

import mysql.connector
from mysql.connector import errorcode

db, cur = None, None
config_path = f"{os.path.realpath(os.path.dirname(__file__))}/../config.json"
if not os.path.isfile(config_path):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(config_path) as config_file:
        config = json.load(config_file)


def init():
    global db, cur

    try:
        # print(
        #     f"db_host: {repr(config['db_host'])}\n"
        #     f"db_user: {repr(config['db_user'])}\n"
        #     f"db_pw: {repr(config['db_pw'])}\n"
        #     f"db_db: {repr(config['db_db'])}"
        # )
        # db = mysql.connector.connect(
        #     host=config["db_host"],
        #     user=config["db_user"],
        #     passwd=config["db_pw"],
        #     database=config["db_db"]
        # )
        db = mysql.connector.connect(
            host="10.0.0.214",
            user="SansPapyrus683",
            passwd="megalovania",
            database="DiscordAdventurersBotDB"
        )
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Invalid username/password!")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist!") 
        else:
            print(err)

    cur = db.cursor()


init()
