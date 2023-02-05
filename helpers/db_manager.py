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


def log_quest(quest_type: int, value: int, userid):
    cur.execute(f"select quests from playersinfo where userid = {userid}")
    quests = cur.fetchall()[0][0].split(",")
    for x in range(len(quests) - 1):
        if quests[x].split(".")[1] == str(quest_type):
            quests[x] = ".".join(quests[x].split(".")[0:2]) + "." + str(int(quests[x].split(".")[2]) + value)
            break
    cur.execute(f"update playersinfo set quests = '{','.join(quests[:])}' where userid = {userid}")
    db.commit()


def get_id(uid: int) -> int:
    cur.execute(f"SELECT id FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def get_all_userid() -> list[int]:
    cur.execute(f"SELECT userid FROM temp2")
    return [int(i[0]) for i in cur.fetchall()]


def get_user_level(uid: int) -> int:
    cur.execute(f"SELECT level FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_level(uid: int, value: int):
    cur.execute(f"UPDATE temp2 SET level = {value} WHERE userid = {uid}")
    db.commit()


def get_user_exp(uid: int) -> int:
    cur.execute(f"SELECT exps FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_exp(uid: int, value: int):
    cur.execute(f"UPDATE temp2 SET exps = {value} WHERE userid = {uid}")
    db.commit()


def get_user_coin(uid: int) -> int:
    cur.execute(f"SELECT coins FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_coin(uid: int, value: int):
    cur.execute(f"UPDATE temp2 SET coins = {value} WHERE userid = {uid}")
    db.commit()


def get_user_gem(uid: int) -> int:
    cur.execute(f"SELECT gems FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_gem(uid: int, value: int):
    cur.execute(f"UPDATE temp2 SET gems = {value} WHERE userid = {uid}")
    db.commit()


def get_user_token(uid: int) -> int:
    cur.execute(f"SELECT event_token FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_token(uid: int, value: int):
    cur.execute(f"UPDATE temp2 SET event_token = {value} WHERE userid = {uid}")
    db.commit()


def get_user_medal(uid: int) -> int:
    cur.execute(f"SELECT medals FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_medal(uid: int, value: int):
    cur.execute(f"UPDATE temp2 SET medals = {value} WHERE userid = {uid}")
    db.commit()


def get_user_ticket(uid: int) -> int:
    cur.execute(f"SELECT tickets FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_ticket(uid: int, value: int):
    cur.execute(f"UPDATE temp2 SET tickets = {value} WHERE userid = {uid}")
    db.commit()


def get_user_daily(uid: int) -> dt.datetime:
    cur.execute(f"SELECT daily_date FROM temp2 WHERE userid = {uid}")
    return dt.datetime.combine(cur.fetchall()[0][0], dt.datetime.min.time())


def set_user_daily(uid: int, value: str):
    cur.execute(f"UPDATE temp2 SET daily_date = '{value}' WHERE userid = {uid}")
    db.commit()


def get_user_order(uid: int) -> int:
    cur.execute(f"SELECT inventory_order FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_order(uid: int, value: int):
    cur.execute(f"UPDATE temp2 SET inventory_order = {value} WHERE userid = {uid}")
    db.commit()


def get_user_deals(uid: int) -> str:
    cur.execute(f"SELECT deals FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_deals(uid: int, value: str):
    cur.execute(f"UPDATE temp2 SET deals = '{value}' WHERE userid = {uid}")
    db.commit()


def get_user_streak(uid: int) -> int:
    cur.execute(f"SELECT streak FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_streak(uid: int, value: int):
    cur.execute(f"UPDATE temp2 SET streak = {value} WHERE userid = {uid}")
    db.commit()


def get_user_quest(uid: int) -> str:
    cur.execute(f"SELECT quests FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_quest(uid: int, value: str):
    cur.execute(f"UPDATE temp2 SET quests = '{value}' WHERE userid = {uid}")
    db.commit()


def get_user_msg_exp(uid: int) -> int:
    cur.execute(f"SELECT msg_exp FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_msg_exp(uid: int, value: int):
    cur.execute(f"UPDATE temp2 SET msg_exp = {value} WHERE userid = {uid}")
    db.commit()


def get_user_deck_slot(uid: int) -> int:
    cur.execute(f"SELECT deck_slot FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_deck_slot(uid: int, value: int):
    cur.execute(f"UPDATE temp2 SET deck_slot = {value} WHERE userid = {uid}")
    db.commit()


def get_user_cards_count(uid: int) -> int:
    cur.execute(f"SELECT COUNT(*) FROM temp_cards WHERE owned_user = {uid}")
    return cur.fetchall()[0][0]


def get_user_deck_count(uid: int, slot: int) -> int:
    db_deck = f"deck{slot}"
    cur.execute(f"SELECT COUNT(*) FROM temp_cards WHERE owned_user = {uid} AND {db_deck} = 1")
    return cur.fetchall()[0][0]


def get_user_deck(uid: int, slot: int) -> list[tuple[int, str, int]]:
    order = get_user_order(uid)

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

    cur.execute(
        f"SELECT id, card_name, card_level FROM temp_cards WHERE "
        f"owned_user = {uid} AND deck{slot} = 1 ORDER BY {order_by}"
    )
    result = cur.fetchall()
    if order in [7, 8]:
        result = u.order_by_rarity(result, 1)
        result = u.order_by_cost(result, order - 7)
    if order in [9, 10]:
        result = u.order_by_cost(result, 1)
        result = u.order_by_rarity(result, order - 9)
    return result


def get_user_cards(
        uid: int, order: int | None = None, add_rules: str = "",
        start: int = 0, length: int = -1,
) -> list[tuple[int, str, int]]:
    order_by = ""
    order = get_user_order(uid) if order is None else order
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

    cur.execute(
        f"SELECT id, card_name, card_level FROM temp_cards WHERE "
        f"owned_user = {uid} {add_rules} ORDER BY {order_by}"
    )

    result = cur.fetchall()
    if order in [7, 8]:
        result = u.order_by_rarity(result, 1)
        result = u.order_by_cost(result, order - 7)
    if order in [9, 10]:
        result = u.order_by_cost(result, 1)
        result = u.order_by_rarity(result, order - 9)

    return result[start:] if length < 0 else result[start:start + length]


def add_user_cards(cards: list[tuple[str | int, str, int]]):
    sql = "INSERT INTO temp_cards (owned_user, card_name, card_level) VALUES (%s, %s, %s)"
    val = [(c[0], c[1], c[2]) for c in cards]
    cur.executemany(sql, val)
    db.commit()


def delete_user_cards(cards: list[int, int]):
    sql = "DELETE FROM temp_cards WHERE id = (%s) AND owned_user = (%s)"
    val = [(i[0], i[1]) for i in cards]
    cur.executemany(sql, val)
    db.commit()


def get_card_name(uid: int, id: int) -> str:
    cur.execute(f"SELECT card_name FROM temp_cards WHERE id = {id} AND owned_user = {uid}")
    result = cur.fetchall()
    return None if len(result) == 0 else result[0][0]

def get_card_level(uid: int, id: int) -> int:
    cur.execute(f"SELECT card_level FROM temp_cards WHERE id = {id} AND owned_user = {uid}")
    result = cur.fetchall()
    return None if len(result) == 0 else result[0][0]


def get_card_decks(id: int) -> list[int]:
    cur.execute(f"SELECT deck1, deck2, deck3, deck4, deck5, deck6 FROM temp_cards WHERE id = {id}")
    result = cur.fetchall()
    return None if len(result) == 0 else result[0]

def add_user(uid: int):
    cur.execute(f"INSERT INTO temp2 (userid) VALUES ({uid})")
    db.commit()


def set_user_card_deck(uid: int, slot: int, value: int, id: int):
    db_deck = f"deck{slot}"
    cur.execute(f"UPDATE temp_cards SET {db_deck} = {value} WHERE id = {id} AND owned_user = {uid}")
    db.commit()


def get_user_position(uid: int) -> str:
    cur.execute(f"SELECT position FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_position(uid: int, value: str):
    cur.execute(f"UPDATE temp2 SET position = '{value}' WHERE userid = {uid}")
    db.commit()


def get_user_inventory(uid: int) -> str:
    cur.execute(f"SELECT inventory FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_inventory(uid: int, value: str):
    cur.execute(f"UPDATE temp2 SET inventory = '{value}' WHERE userid = {uid}")
    db.commit()


def get_user_storage(uid: int) -> str:
    cur.execute(f"SELECT storage FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_storage(uid: int, value: str):
    cur.execute(f"UPDATE temp2 SET storage = '{value}' WHERE userid = {uid}")
    db.commit()


def get_user_map(uid: int) -> bool:
    cur.execute(f"SELECT display_map FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_map(uid: int, value: bool):
    cur.execute(f"UPDATE temp2 SET display_map = {value} WHERE userid = {uid}")
    db.commit()


def get_user_badge(uid: int | str) -> int:
    cur.execute(f"SELECT all_badges FROM temp2 WHERE userid = {uid}")
    return cur.fetchall()[0][0]


def set_user_badge(uid: int, value: int):
    cur.execute(f"UPDATE temp2 SET all_badges = {value} WHERE userid = {uid}")
    db.commit()


def get_user_register_date(uid: int) -> dt.datetime:
    cur.execute(f"SELECT creation_date FROM temp2 WHERE userid = {uid}")
    return dt.datetime.combine(cur.fetchall()[0][0], dt.datetime.min.time())


def set_user_register_date(uid: int, value: dt.datetime):
    cur.execute(f"UPDATE temp2 SET creation_date = '{value}' WHERE userid = {uid}")
    db.commit()


def get_user_premium(uid: int) -> dt.datetime:
    cur.execute(f"SELECT premium_account FROM temp2 WHERE userid = {uid}")
    return dt.datetime.combine(cur.fetchall()[0][0], dt.datetime.min.time())


def has_premium(uid: int) -> bool:
    return get_user_premium(uid) > dt.datetime.today()


def set_user_premium(uid: int, value: dt.datetime):
    cur.execute(f"UPDATE temp2 SET premium_account = '{value}' WHERE userid = {uid}")
    db.commit()


def get_leaderboard(order_by: str, limit: int) -> list[tuple[int, str, int] | tuple[int, str, int, int]]:
    select = []
    order = []
    if order_by == "XP":
        select = ["id", "userid", "level", "exps"]
        order = ["level DESC", "exps DESC"]
    elif order_by == "Golden Coins":
        select = ["id", "userid", "coins", "gems"]
        order = ["coins DESC", "gems DESC"]
    elif order_by == "Shiny Gems":
        select = ["id", "userid", "gems", "coins"]
        order = ["gems DESC", "coins DESC"]
    elif order_by == "Medals":
        select = ["id", "userid", "medals"]
        order = ["medals DESC"]
    elif order_by == "Tokens":
        select = ["id", "userid", "event_token"]
        order = ["event_token DESC"]
    cur.execute(f"SELECT {','.join(select)} FROM playersinfo ORDER BY {','.join(order)} LIMIT {limit}")
    return cur.fetchall()


if __name__ == "__main__":
    init()
    print(get_all_userid())
