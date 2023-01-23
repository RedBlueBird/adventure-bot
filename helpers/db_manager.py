import os
import sys
import json
import datetime as dt

import util as u

import mysql.connector
import mysql.connector.cursor_cext
from mysql.connector import errorcode

config_path = f"{os.path.realpath(os.path.dirname(__file__))}/../config.json"
if not os.path.isfile(config_path):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(config_path) as config_file:
        config = json.load(config_file)

db: mysql.connector.connection_cext.CMySQLConnection | None = None
cur: mysql.connector.cursor_cext.CMySQLCursor | None = None
queues = {}


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


def is_registered(uid: int) -> bool:
    cur.execute(f"SELECT * FROM temp2 WHERE userid = {uid}")
    return bool(cur.fetchall())

def get_user_id(uid: int) -> int:
    cur.execute(f"SELECT id FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def get_user_cooldown(uid: int) -> int:
    cur.execute(f"SELECT cooldown FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_cooldown(value: int, uid: int):
    cur.execute(f"UPDATE temp2 SET cooldown = {value} WHERE userid = {uid}")
    db.commit()


def get_user_level(uid: int) -> int:
    cur.execute(f"SELECT level FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_level(value: int, uid: int):
    cur.execute(f"UPDATE temp2 SET level = {value} WHERE userid = {uid}")
    db.commit()


def get_user_exp(uid: int) -> int:
    cur.execute(f"SELECT exps FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_exp(value: int, uid: int):
    cur.execute(f"UPDATE temp2 SET exp = {value} WHERE userid = {uid}")
    db.commit()


def get_user_coin(uid: int) -> int:
    cur.execute(f"SELECT coins FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_coin(value: int, uid: int):
    cur.execute(f"UPDATE temp2 SET coins = {value} WHERE userid = {uid}")
    db.commit()


def get_user_gem(uid: int) -> int:
    cur.execute(f"SELECT gems FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_gem(value: int, uid: int):
    cur.execute(f"UPDATE temp2 SET gems = {value} WHERE userid = {uid}")
    db.commit()


def get_user_token(uid: int) -> int:
    cur.execute(f"SELECT event_token FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_token(value: int, uid: int):
    cur.execute(f"UPDATE temp2 SET event_token = {value} WHERE userid = {uid}")
    db.commit()


def get_user_medal(uid: int) -> int:
    cur.execute(f"SELECT medals FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_medal(value: int, uid: int):
    cur.execute(f"UPDATE temp2 SET medals = {value} WHERE userid = {uid}")
    db.commit()


def get_user_ticket(uid: int) -> int:
    cur.execute(f"SELECT tickets FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_ticket(value: int, uid: int):
    cur.execute(f"UPDATE temp2 SET tickets = {value} WHERE userid = {uid}")
    db.commit()


def get_user_daily(uid: int) -> str:
    cur.execute(f"SELECT daily_date FROM temp2 WHERE userid = {uid}")
    return dt.datetime.combine(cur.fetchall()[0][0], dt.datetime.min.time())

def set_user_daily(value: str, uid: int):
    cur.execute(f"UPDATE temp2 SET daily_date = {value} WHERE userid = {uid}")
    db.commit()


def get_user_order(uid: int) -> int:
    cur.execute(f"SELECT inventory_order FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_order(value: int, uid: int):
    cur.execute(f"UPDATE temp2 SET inventory_order = {value} WHERE userid = {uid}")
    db.commit()


def get_user_deals(uid: int) -> str:
    cur.execute(f"SELECT deals FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_deals(value: str, uid: int):
    cur.execute(f"UPDATE temp2 SET deals = {value} WHERE userid = {uid}")
    db.commit()


def get_user_streak(uid: int) -> int:
    cur.execute(f"SELECT streak FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_streak(value: int, uid: int):
    cur.execute(f"UPDATE temp2 SET streak = {value} WHERE userid = {uid}")
    db.commit()


def get_user_quest(uid: int) -> str:
    cur.execute(f"SELECT quests FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_quest(value: str, uid: int):
    cur.execute(f"UPDATE temp2 SET quests = {value} WHERE userid = {uid}")
    db.commit()

def log_quest(quest_type: int, value: int, userid):
    cur.execute(f"select quests from playersinfo where userid = {userid}")
    quests = cur.fetchall()[0][0].split(",")
    for x in range(len(quests) - 1):
        if quests[x].split(".")[1] == str(quest_type):
            quests[x] = ".".join(quests[x].split(".")[0:2]) + "." + str(int(quests[x].split(".")[2]) + value)
            break
    cur.execute(f"update playersinfo set quests = '{','.join(quests[:])}' where userid = {userid}")
    db.commit()


def get_user_msg_exp(uid: int) -> int:
    cur.execute(f"SELECT msg_exp FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_msg_exp(value: int, uid: int):
    cur.execute(f"UPDATE temp2 SET msg_exp = {value} WHERE userid = {uid}")
    db.commit()


def get_user_deck_slot(uid: int) -> int:
    cur.execute(f"SELECT deck_slot FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_deck_slot(value: int, uid: int):
    cur.execute(f"UPDATE temp2 SET deck_slot = {value} WHERE userid = {uid}")
    db.commit()


def get_user_cards_count(uid: int) -> int:
    cur.execute(f"SELECT COUNT(*) FROM temp_cards WHERE owned_user = {uid}")
    return cur.fetchall()[0][0]

def get_user_deck_count(slot: int, uid: int) -> int:
    cur.execute(f"SELECT COUNT(*) FROM temp_cards WHERE owned_user = {uid} AND deck{slot} = 1")
    return cur.fetchall()[0][0]


def get_user_deck(slot: int, order: int, uid: int) -> 'deck':
    order_by = ""
    if order == 1:
        order_by = "card_level, card_name"
    elif order in [2, 7, 8, 9, 10]:
        order_by = "card_level desc, card_name"
    elif order == 3:
        order_by = "card_name"
    elif order == 4:
        order_by = "card_name desc"
    elif order == 5:
        order_by = "id, card_name"
    elif order == 6:
        order_by = "id desc, card_name"
    cur.execute(f"SELECT id, card_name, card_level FROM temp_cards WHERE owned_user = {uid} AND deck{slot} = 1 ORDER BY {order_by}")
    result = cur.fetchall()
    if order in [7, 8]:
        result = u.order_by_rarity(result, 1)
        result = u.order_by_cost(result, order - 7)
    if order in [9, 10]:
        result = u.order_by_cost(result, 1)
        result = u.order_by_rarity(result, order - 9)
    return result

def get_user_cards(start: int, length: int, order: int, uid: int, add_rules: str = "") -> 'cards':
    order_by = ""
    if order == 1:
        order_by = "card_level, card_name"
    elif order in [2, 7, 8, 9, 10]:
        order_by = "card_level desc, card_name"
    elif order == 3:
        order_by = "card_name"
    elif order == 4:
        order_by = "card_name desc"
    elif order == 5:
        order_by = "id, card_name"
    elif order == 6:
        order_by = "id desc, card_name"
    cur.execute(f"SELECT id, card_name, card_level FROM temp_cards WHERE owned_user = {uid} {add_rules} ORDER BY {order_by}")
    result = cur.fetchall()
    if order in [7, 8]:
        result = u.order_by_rarity(result, 1)
        result = u.order_by_cost(result, order - 7)
    if order in [9, 10]:
        result = u.order_by_cost(result, 1)
        result = u.order_by_rarity(result, order - 9)
    return result[start:start+length]

def add_user_cards(cards):
    sql = "INSERT INTO temp_cards (owned_user, card_name, card_level) VALUES (%s, %s, %s)"
    val = [(c[0], c[1], c[2]) for c in cards]
    cur.executemany(sql, val)
    db.commit()

def add_user(uid: int):
    sql = "INSERT INTO temp2 (userid) VALUES (%s)"
    val = [uid]
    cur.execute(sql, val)
    db.commit()

def set_user_card_deck(slot: int, value: int, id: int, uid: int):
    cur.execute(f"UPDATE temp_cards SET deck{slot} = {value} WHERE id = {id} AND owned_user = {uid}")
    db.commit()


def get_user_position(uid: int) -> str:
    cur.execute(f"SELECT position FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_position(value: str, uid: int):
    cur.execute(f"UPDATE temp2 SET position = {value} WHERE userid = {uid}")
    db.commit()


def get_user_inventory(uid: int) -> str:
    cur.execute(f"SELECT inventory FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_inventory(value: str, uid: int):
    cur.execute(f"UPDATE temp2 SET inventory = {value} WHERE userid = {uid}")
    db.commit()


def get_user_storage(uid: int) -> str:
    cur.execute(f"SELECT storage FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_storage(value: str, uid: int):
    cur.execute(f"UPDATE temp2 SET storage = {value} WHERE userid = {uid}")
    db.commit()


def get_user_map(uid: int) -> bool:
    cur.execute(f"SELECT display_map FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_map(value: bool, uid: int):
    cur.execute(f"UPDATE temp2 SET display_map = {value} WHERE userid = {uid}")
    db.commit()


def get_user_badge(uid: int) -> int:
    cur.execute(f"SELECT all_badges FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]

def set_user_badge(value: int, uid: int):
    cur.execute(f"UPDATE temp2 SET all_badges = {value} WHERE userid = {uid}")
    db.commit()


def get_user_register_date(uid: int) -> str:
    cur.execute(f"SELECT creation_date FROM temp2 WHERE userid = {uid}")
    return dt.datetime.combine(cur.fetchall()[0][0], dt.datetime.min.time())

def set_user_register_date(value: str, uid: int):
    cur.execute(f"UPDATE temp2 SET creation_date = {value} WHERE userid = {uid}")
    db.commit()


def get_user_premium(uid: int) -> str:
    cur.execute(f"SELECT premium_account FROM temp2 WHERE userid = {uid}")
    return dt.datetime.combine(cur.fetchall()[0][0], dt.datetime.min.time())

def set_user_premium(value: str, uid: int):
    cur.execute(f"UPDATE temp2 SET premium_account = {value} WHERE userid = {uid}")
    db.commit()


def get_leaderboard(type: str, limit: int) -> "players":
    select = []
    order = []
    if type == "XP":
        selection = ["id","userid","level","exps"]
        order = ["level DESC", "exps DESC"]
    elif type == "Golden Coins":
        selection = ["id","userid","coins","gems"]
        order = ["coins DESC","gems DESC"]
    elif type == "Shiny Gems":
        selection = ["id","userid","gems","coins"]
        order = ["gems DESC", "coins DESC"]
    elif type == "Medals":
        selection = ["id","userid","medals"]
        order = ["medals DESC"]
    elif type == "Tokens":
        selection = ["id","userid","event_token"]
        order = ["event_token DESC"]
    cur.execute(f"SELECT {','.join(selection)} FROM playersinfo ORDER BY {','.join(order)} LIMIT {limit}")
    return cur.fetchall()