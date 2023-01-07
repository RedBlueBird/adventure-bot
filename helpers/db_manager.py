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
        #for jeff's local bot hosting
        mydb = mysql.connector.connect(host="192.9.147.237", user="BlueBird", passwd="73FFr3y2h@^9",
                                       database="DiscordAdventurersBotDB")
        
        # mydb = mysql.connector.connect(host="na01-sql.pebblehost.com", user="customer_136977_adventurersdb", passwd="soaZREUDBH24jNkFP9B!",
        #                                database="customer_136977_adventurersdb")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Invalid username/password!")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist!") 
        else:
            print(err)

    cur = db.cursor()
