import os

import mysql.connector
from mysql.connector import errorcode

mydb, mycursor = None, None


def init():
    global mydb, mycursor

    try:
        # for jeff's local bot hosting
        mydb = mysql.connector.connect(
            host="localhost",
            user="DiscordAdventurersBot",
            passwd="1226JeffreyZhang",
            database="DiscordAdventurersBotDB"
        )

        # mydb = mysql.connector.connect(
        #     host="na01-sql.pebblehost.com",
        #     user="customer_136977_adventurersdb",
        #     passwd="soaZREUDBH24jNkFP9B!",
        #     database="customer_136977_adventurersdb"
        # )
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Invalid username/password!")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist!")
        else:
            print(err)

    mycursor = mydb.cursor()


DATABASE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../database/database.db"
