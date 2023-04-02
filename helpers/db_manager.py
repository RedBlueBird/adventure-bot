import os
import sys
import json
from ast import literal_eval
import datetime as dt

from helpers import util as u

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
    cur.execute(f"SELECT EXISTS(SELECT * FROM players WHERE uid = {uid})")
    return bool(cur.fetchall()[0][0])


def get_id(uid: int) -> int:
    cur.execute(f"SELECT id FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def get_all_uid() -> list[int]:
    cur.execute(f"SELECT uid FROM players")
    return [int(i[0]) for i in cur.fetchall()]


def get_user_level(uid: int) -> int:
    cur.execute(f"SELECT level FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_level(uid: int, value: int):
    cur.execute(f"UPDATE players SET level = {value} WHERE uid = {uid}")
    db.commit()


def get_user_exp(uid: int) -> int:
    cur.execute(f"SELECT exps FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_exp(uid: int, value: int):
    cur.execute(f"UPDATE players SET exps = {value} WHERE uid = {uid}")
    db.commit()


def get_user_coin(uid: int) -> int:
    cur.execute(f"SELECT coins FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_coin(uid: int, value: int):
    cur.execute(f"UPDATE players SET coins = {value} WHERE uid = {uid}")
    db.commit()


def get_user_gem(uid: int) -> int:
    cur.execute(f"SELECT gems FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_gem(uid: int, value: int):
    cur.execute(f"UPDATE players SET gems = {value} WHERE uid = {uid}")
    db.commit()


def get_user_token(uid: int) -> int:
    cur.execute(f"SELECT event_token FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_token(uid: int, value: int):
    cur.execute(f"UPDATE players SET event_token = {value} WHERE uid = {uid}")
    db.commit()


def get_user_medal(uid: int) -> int:
    cur.execute(f"SELECT medals FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_medal(uid: int, value: int):
    cur.execute(f"UPDATE players SET medals = {value} WHERE uid = {uid}")
    db.commit()


def get_user_ticket(uid: int) -> int:
    cur.execute(f"SELECT tickets FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_ticket(uid: int, value: int):
    cur.execute(f"UPDATE players SET tickets = {value} WHERE uid = {uid}")
    db.commit()


def get_user_daily(uid: int) -> dt.datetime:
    cur.execute(f"SELECT daily_date FROM players WHERE uid = {uid}")
    return dt.datetime.combine(cur.fetchall()[0][0], dt.datetime.min.time())


def set_user_daily(uid: int, value: str | dt.date):
    cur.execute(f"UPDATE players SET daily_date = '{value}' WHERE uid = {uid}")
    db.commit()


def get_user_order(uid: int) -> int:
    cur.execute(f"SELECT inventory_order FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_order(uid: int, value: int):
    cur.execute(f"UPDATE players SET inventory_order = {value} WHERE uid = {uid}")
    db.commit()


def get_user_deals(uid: int) -> str:
    cur.execute(f"SELECT deals FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_deals(uid: int, value: str):
    cur.execute(f"UPDATE players SET deals = '{value}' WHERE uid = {uid}")
    db.commit()


def get_user_streak(uid: int) -> int:
    cur.execute(f"SELECT streak FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_streak(uid: int, value: int):
    cur.execute(f"UPDATE players SET streak = {value} WHERE uid = {uid}")
    db.commit()


def get_user_msg_exp(uid: int) -> int:
    cur.execute(f"SELECT msg_exp FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_msg_exp(uid: int, value: int):
    cur.execute(f"UPDATE players SET msg_exp = {value} WHERE uid = {uid}")
    db.commit()


def get_user_battle_command(uid: int) -> str:
    cur.execute(f"SELECT battle_command FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_battle_command(uid: int, value: str):
    cur.execute(f"UPDATE players SET battle_command = '{value}' WHERE uid = {uid}")
    db.commit()


def get_user_deck_slot(uid: int) -> int:
    cur.execute(f"SELECT deck_slot FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_deck_slot(uid: int, value: int):
    cur.execute(f"UPDATE players SET deck_slot = {value} WHERE uid = {uid}")
    db.commit()


def get_user_cards_count(uid: int) -> int:
    cur.execute(f"SELECT COUNT(*) FROM cards WHERE owned_user = {uid}")
    return cur.fetchall()[0][0]


def get_user_deck_count(uid: int, slot: int = 0) -> int:
    slot = get_user_deck_slot(uid) if slot == 0 else slot
    db_deck = f"deck{slot}"
    cur.execute(f"SELECT COUNT(*) FROM cards WHERE owned_user = {uid} AND {db_deck} = 1")
    return cur.fetchall()[0][0]


def get_user_deck(uid: int, slot: int = 0) -> list[tuple[int, str, int]]:
    slot = slot if 1 <= slot <= 6 else get_user_deck_slot(uid)
    db_deck = f"deck{slot}"
    cur.execute(
        f"SELECT id, card_name, card_level FROM cards WHERE "
        f"owned_user = {uid} AND {db_deck} = 1"
    )
    result = cur.fetchall()
    u.sort_cards(result, get_user_order(uid))

    return result


def get_user_deck_ids(uid: int) -> list[int]:
    cur.execute(
        f"SELECT id FROM cards WHERE owned_user = {uid} "
        "AND (deck1 = 1 or deck2 = 1 or deck3 = 1 or deck4 = 1 or deck5 = 1 or deck6 = 1)"
    )
    result = cur.fetchall()
    return [i[0] for i in result]


def get_user_cards(
        uid: int,
        order: int | None = None,
        name: str | None = None,
        level: int | None = None,
        energy: int | None = None,
        rarity: str | None = None,
) -> list[tuple[int, str, int]]:
    conditions = []
    if name is not None:
        conditions.append(f"AND card_name LIKE '%{name}%'")
    if level is not None:
        conditions.append(f"AND card_level = {level}")

    cur.execute(
        f"SELECT id, card_name, card_level FROM cards WHERE "
        f"owned_user = {uid} {' '.join(conditions)}"
    )
    result = cur.fetchall()

    if energy is not None:
        result = [card for card in result if energy == u.cards_dict(card[2], card[1])["cost"]]
    if rarity is not None:
        rarity_terms = {
            "L": "legendary",
            "EX": "exclusive",
            "E": "epic",
            "R": "rare",
            "C": "common",
            "M": "monster"
        }
        result = [
            card for card in result
            if rarity == rarity_terms.get(u.cards_dict(card[2], card[1])["rarity"])
        ]

    if order is None:
        order = get_user_order(uid)
    u.sort_cards(result, order)
    return result


def add_user_cards(cards: list[tuple[int, str, int]]):
    sql = "INSERT INTO cards (owned_user, card_name, card_level) VALUES (%s, %s, %s)"
    cur.executemany(sql, cards)
    db.commit()


def delete_user_cards(cards: list[tuple[int, int]]):
    sql = "DELETE FROM cards WHERE id = (%s) AND owned_user = (%s)"
    cur.executemany(sql, cards)
    db.commit()


def get_card_name(uid: int, cid: int) -> str | None:
    cur.execute(f"SELECT card_name FROM cards WHERE id = {cid} AND owned_user = {uid}")
    result = cur.fetchall()
    return None if not result else result[0][0]


def get_card_level(uid: int, cid: int) -> int | None:
    cur.execute(f"SELECT card_level FROM cards WHERE id = {cid} AND owned_user = {uid}")
    result = cur.fetchall()
    return None if not result else result[0][0]


def set_card_level(cid: int, lvl: int):
    cur.execute(f"UPDATE cards SET card_level = {lvl} WHERE id = {cid}")
    db.commit()


def get_card_owner(cid: int) -> int | None:
    cur.execute(f"SELECT owned_user FROM cards WHERE id = {cid}")
    result = cur.fetchall()
    return None if not result else result[0][0]


def set_card_owner(uid: int, cid: int):
    cur.execute(f"UPDATE cards SET owned_user = {uid} WHERE id = {cid}")
    db.commit()


def get_card_decks(cid: int) -> list[int] | None:
    cur.execute(f"SELECT deck1, deck2, deck3, deck4, deck5, deck6 FROM cards WHERE id = {cid}")
    result = cur.fetchall()
    return None if not result else result[0]


def add_user(uid: int):
    cur.execute(f"INSERT INTO players (uid) VALUES ({uid})")
    db.commit()


def set_user_card_deck(uid: int, slot: int, value: int, cid: int):
    db_deck = f"deck{slot}"
    cur.execute(f"UPDATE cards SET {db_deck} = {value} WHERE id = {cid} AND owned_user = {uid}")
    db.commit()


def get_user_position(uid: int) -> str:
    cur.execute(f"SELECT position FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_position(uid: int, value: str):
    cur.execute(f"UPDATE players SET position = '{value}' WHERE uid = {uid}")
    db.commit()


def get_user_inventory(uid: int) -> dict:
    cur.execute(f"SELECT inventory FROM players WHERE uid = {uid}")
    return literal_eval(cur.fetchall()[0][0])


def set_user_inventory(uid: int, value: str | dict):
    value = value if isinstance(value, str) else json.dumps(value)
    cur.execute(f"UPDATE players SET inventory = '{value}' WHERE uid = {uid}")
    db.commit()


def get_user_storage(uid: int) -> dict:
    cur.execute(f"SELECT storage FROM players WHERE uid = {uid}")
    return literal_eval(cur.fetchall()[0][0])


def set_user_storage(uid: int, value: str | dict):
    value = value if isinstance(value, str) else json.dumps(value)
    cur.execute(f"UPDATE players SET storage = '{value}' WHERE uid = {uid}")
    db.commit()


def get_user_map(uid: int) -> bool:
    cur.execute(f"SELECT display_map FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_map(uid: int, value: bool):
    cur.execute(f"UPDATE players SET display_map = {value} WHERE uid = {uid}")
    db.commit()


def get_user_badge(uid: int) -> int:
    cur.execute(f"SELECT all_badges FROM players WHERE uid = {uid}")
    return cur.fetchall()[0][0]


def set_user_badge(uid: int, value: int):
    cur.execute(f"UPDATE players SET all_badges = {value} WHERE uid = {uid}")
    db.commit()


def get_user_register_date(uid: int) -> dt.datetime:
    cur.execute(f"SELECT creation_date FROM players WHERE uid = {uid}")
    return dt.datetime.combine(cur.fetchall()[0][0], dt.datetime.min.time())


def set_user_register_date(uid: int, value: dt.datetime):
    cur.execute(f"UPDATE players SET creation_date = '{value}' WHERE uid = {uid}")
    db.commit()


def get_user_premium(uid: int) -> dt.datetime:
    cur.execute(f"SELECT premium_account FROM players WHERE uid = {uid}")
    return dt.datetime.combine(cur.fetchall()[0][0], dt.datetime.min.time())


def has_premium(uid: int) -> bool:
    return get_user_premium(uid) > dt.datetime.now(dt.timezone.utc)


def set_user_premium(uid: int, value: dt.datetime):
    cur.execute(f"UPDATE players SET premium_account = '{value}' WHERE uid = {uid}")
    db.commit()


def get_leaderboard(
        order_by: str, limit: int
) -> list[tuple[int, str, int] | tuple[int, str, int, int]]:
    select = []
    order = []
    if order_by == "XP":
        select = ["id", "uid", "level", "exps"]
        order = ["level DESC", "exps DESC"]
    elif order_by == "Golden Coins":
        select = ["id", "uid", "coins", "gems"]
        order = ["coins DESC", "gems DESC"]
    elif order_by == "Shiny Gems":
        select = ["id", "uid", "gems", "coins"]
        order = ["gems DESC", "coins DESC"]
    elif order_by == "Medals":
        select = ["id", "uid", "medals"]
        order = ["medals DESC"]
    elif order_by == "Tokens":
        select = ["id", "uid", "event_token"]
        order = ["event_token DESC"]

    cur.execute(
        f"SELECT {','.join(select)} FROM players "
        f"ORDER BY {','.join(order)} LIMIT {limit}"
    )
    return cur.fetchall()


def get_user_quests(uid: int, quest_type: int = -1) -> list[tuple[int, int, int, int, int]]:
    operation = "SELECT id, quest_type, reward_type, rarity, progress FROM quest WHERE uid = %s"
    params = (uid,)
    if quest_type != -1:
        operation += " AND quest_type = %s"
        params = (uid, quest_type)
    cur.execute(operation, params)
    return cur.fetchall()


def get_user_quests_count(uid: int) -> int:
    operation = "SELECT COUNT(*) FROM quest WHERE uid = %s"
    cur.execute(operation, (uid,))
    return cur.fetchall()[0][0]


def add_user_quests(quests: list[tuple[int, int, int, int, int]]):
    operation = "INSERT INTO quest (uid, quest_type, reward_type, rarity, progress) VALUES (%s, %s, %s, %s, %s)"
    cur.executemany(operation, quests)
    db.commit()

def delete_user_quest(quest_id: int):
    params = (quest_id,)
    operation = "DELETE FROM quest WHERE id = %s"
    cur.execute(operation, params)
    db.commit()

def set_user_quest_progress(quest_id: int, progress: int):
    params = (progress, quest_id)
    operation = "UPDATE quest SET progress = %s WHERE id = %s"
    cur.execute(operation, params)
    db.commit()

def get_user_next_quest(uid: int) -> dt.datetime | None:
    operation = "SELECT next_quest FROM players WHERE uid = %s"
    cur.execute(operation, (uid,))
    return cur.fetchall()[0][0]

def set_user_next_quest(uid: int, next_quest: dt.datetime | None):
    operation = "UPDATE players SET next_quest = %s WHERE uid = %s"
    cur.execute(operation, (next_quest, uid))
    db.commit()


if __name__ == "__main__":
    init()
    print(get_all_uid())
