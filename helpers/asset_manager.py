import datetime as dt
import random
import math
import json
import copy
from string import Template
from typing import Union, List
import discord

from helpers import db_manager as dm

with open('txts/icons.json') as json_file:
    icon = json.load(json_file)
with open('txts/admins.json') as json_file:
    admins = json.load(json_file)


converter = {
    "burn": icon['burn'],
    "poison": icon['pois'],
    "recover": icon['rec'],
    "curse": icon['curs'],
    "stun": icon['stun'],
    "bullseye": icon['eye'],
    "berserk": icon['bers'],
    "freeze": icon['frez'],
    "chill": icon['chil'],
    "restore": icon["rest"],
    "seriate": icon['seri'],
    "feeble": icon['feeb']
}

deck = {
    '[♠ Ace]': 11, '[♠ Two]': 2, '[♠ Three]': 3, '[♠ Four]': 4, '[♠ Five]': 5,
    '[♠ Six]': 6, '[♠ Seven]': 7, '[♠ Eight]': 8, '[♠ Nine]': 9, '[♠ Ten]': 10,
    '[♠ Jack]': 10, '[♠ Queen]': 10, '[♠ King]': 10, '[♥ Ace]': 11, '[♥ Two]': 2,
    '[♥ Three]': 3, '[♥ Four]': 4, '[♥ Five]': 5, '[♥ Six]': 6, '[♥ Seven]': 7,
    '[♥ Eight]': 8, '[♥ Nine]': 9, '[♥ Ten]': 10, '[♥ Jack]': 10, '[♥ Queen]': 10,
    '[♥ King]': 10, '[♦ Ace]': 11, '[♦ Two]': 2, '[♦ Three]': 3, '[♦ Four]': 4,
    '[♦ Five]': 5, '[♦ Six]': 6, '[♦ Seven]': 7, '[♦ Eight]': 8, '[♦ Nine]': 9,
    '[♦ Ten]': 10, '[♦ Jack]': 10, '[♦ Queen]': 10, '[♦ King]': 10, '[♣ Ace]': 11,
    '[♣ Two]': 2, '[♣ Three]': 3, '[♣ Four]': 4, '[♣ Five]': 5, '[♣ Six]': 6,
    '[♣ Seven]': 7, '[♣ Eight]': 8, '[♣ Nine]': 9, '[♣ Ten]': 10, '[♣ Jack]': 10,
    '[♣ Queen]': 10, '[♣ King]': 10
}
aces = [f'[{s} Ace]' for s in ['♠', '♥', '♦', '♣']]

queues, scale, prefix = {}, [50, 1.05], "a."

def init(bot):
    global queues, scale


def reply_check(valid_replies: List[str],
                valid_authors: List[discord.User],
                valid_channels: List[discord.TextChannel]):
    def _reaction_check(msg: discord.Message):
        if msg.channel not in valid_channels:
            return False
        if msg.author not in valid_authors:
            return False
        return any(msg.content.lower().startswith(f'a.{s}') for s in valid_replies)

    return _reaction_check


def reaction_check(valid_reactions: List[str],
                   valid_reactors: List[discord.User],
                   valid_messages: List[discord.Message]):
    def _reaction_check(rct: discord.Reaction, author: discord.User):
        if str(rct.emoji) not in valid_reactions:
            return False
        if author not in valid_reactors:
            return False
        return rct.message.id in [m.id for m in valid_messages]

    return _reaction_check


# =========================== Dictionary functions ===========================
# Loads in all the necessary json files as dictionaries
with open('txts/cards.json') as json_file:
    all_cards = json.load(json_file)
with open('txts/item_abbreviations.json') as json_file:
    all_items_abb = json.load(json_file)
with open('txts/items.json') as json_file:
    all_items = json.load(json_file)
with open('txts/mobs.json') as json_file:
    all_mobs = json.load(json_file)
with open('txts/effects.json') as json_file:
    all_eff = json.load(json_file)


def cards_dict(card_level, card_name):
    level = int(card_level)
    card_level = scale[1] ** (level - 1) * scale[0]
    inverse_level = 1.01 ** (level * -1 + 1) * scale[0]

    if card_name.lower() not in all_cards:
        return {"name": "Glitched", "cost": 0, "rarity": "NA", "self_damage": 4500, "eff_acc": 100, "attacks": 10,
                "acc": 100, "crit": 100, "mod": {}, "description": "None", "requirement": "None",
                "brief": "Created from this bot's glitches"}

    card = copy.deepcopy(all_cards[card_name.lower()])
    for i in card:
        if i in ["block", "absorb", "heal", "tramp", "damage", "self_damage", "crush", "revenge", "lich_revenge"]:
            card[i] = round(card[i] * card_level)
        elif i == "eff_app":
            card[i][0] = round(card[i][0] * card_level)
        elif i == "inverse_damage":
            card[i] = round(card[i] * inverse_level)
        elif i == "on_hand":
            for k in card[i]:
                if k in ["block", "absorb", "heal", "tramp", "damage",
                         "self_damage", "crush", "revenge", "lich_revenge"]:
                    card[i][k] = round(card[i][k] * card_level)
                elif k == "eff_app":
                    card[i][k][0] = round(card[i][k][0] * card_level)
    return card


def items_dict(item_name, max_stat=100 * scale[0]):
    item_name = all_items_abb.get(item_name.lower(), item_name.lower())
    if item_name not in all_items:
        return {"name": "Glitching", "rarity": "NA", "weight": 0, "attacks": 1, "acc": 100, "crit": 0, "eff_acc": 100,
                "one_use": "False", "in_battle": "False", "abb": "glitching", "sta_gaom": 1, "mod": {},
                "description": "None", "brief": "Summons a violent wormhole capable of ending all life as we know it."}

    item = copy.deepcopy(all_items[item_name])
    for i in item:
        if i in ["block", "absorb", "heal", "tramp", "damage", "self_damage", "crush", "revenge", "lich_revenge"]:
            item[i] = round(item[i] * max_stat / 100)
        elif i == "eff_app":
            item[i][0] = round(item[i][0] * max_stat / 100)
    return item


def mobs_dict(mob_level: Union[str, int], mob_name: str):
    mob_level = int(mob_level)
    mob_level = scale[1] ** (int(mob_level) - 1) * scale[0]

    if mob_name.lower() not in all_mobs:
        return {"name": "Glitcher", "rarity": "NA", "health": -1, "energy_lag": 0, "stamina": -1,
                "death reward": {"coins": 0, "exps": 0},
                "deck": ["Glitched", "Glitched", "Glitched", "Glitched", "Glitched", "Glitched", "Glitched", "Glitched",
                         "Glitched", "Glitched"],
                "brief": "A man in a big white van."}
    mob = copy.deepcopy(all_mobs[mob_name.lower()])
    mob["health"] = round(mob["health"] * mob_level)
    return mob


def effs_dict(eff_name):
    if eff_name.lower() not in all_eff:
        return {"name": "Glitch",
                "description": "Anyone who ever has this effect immediately dies a horrible death."}
    return copy.deepcopy(all_eff[eff_name.lower()])


def quest_index(index: str) -> List[Union[str, int]]:
    """
    Returns the information for a quest given an index.
    Information for all_indices:
        1- Kill mobs
        2- Collect items
        3- Travel a certain distance
        4- Do battles
        5- Collect golden coins
        6- Collect medals
        7- Merge pairs of cards
        8- Catch fish
    :param index: The quest to get in the form of a string
    :return: A list of strings and ints representing the info about this quest
    """
    indices = index.split(".")[:2]
    all_indices = {
        "1": [5, 10, 20, 50],
        "2": [10, 20, 40, 60],
        "3": [500, 1000, 2000, 5000],
        "4": [1, 3, 5, 10],
        "5": [100, 200, 500, 1000],
        "6": [5, 10, 25, 50],
        "7": [1, 2, 5, 10],
        "8": [3, 5, 10, 20]
    }
    all_rewards = {
        "1": [200, 500, 1000, 2500],
        "2": [0, 1, 2, 4]
    }
    reward_units = {"1": icon["coin"], "2": icon["gem"]}
    exp_rewards = {"0": 25, "1": 50, "2": 100, "3": 200, "4": 250}
    all_rarities = {"0": "{C}", "1": "{R}", "2": "{E}", "3": "{L}", "4": "{EX}"}

    # requirements, type rewards, rarity, reward unit, exp rewards
    return [all_indices[indices[1]][int(indices[0][0])], str(all_rewards[indices[0][1]][int(indices[0][0])]),
            all_rarities[indices[0][0]], reward_units[indices[0][1]], exp_rewards[indices[0][0]]]


def quest_str_rep(quest_type: Union[str, int], amt: Union[str, int]):
    """
    Gives a string representation of a quest given the type and the extend to do it to.
    :param quest_type: The type of quest. (types can be found in quest_index's docstring)
    :param amount: The extent to do it to
    :return: A string representation of the quest.
    """
    return {
        1: f"Kill {amt} opponents while adventuring",
        2: f"Accumulate enough items that they have a total weight of {amt} while adventuring",
        3: f"Travel {amt} meters while adventuring",
        4: f"Win {amt} non-friendly PvP battles",
        5: f"Earn {amt} golden coins while adventuring",
        6: f"Earn {amt} medals in PvP battles",
        7: f"Merge {amt} pairs of cards",
        8: f"Catch {amt} fish in the fishing mini-game"
    }[int(quest_type)]


def log_quest(quest_type: int, value: int, userid):
    dm.cur.execute(f"select quests from playersinfo where userid = {userid}")
    quests = dm.cur.fetchall()[0][0].split(",")
    for x in range(len(quests) - 1):
        if quests[x].split(".")[1] == str(quest_type):
            quests[x] = ".".join(quests[x].split(".")[0:2]) + "." + str(int(quests[x].split(".")[2]) + value)
            break
    dm.cur.execute(f"update playersinfo set quests = '{','.join(quests[:])}' where userid = {userid}")
    dm.db.commit()


# =========================== Special Card Functions ===========================
with open("txts/card_list.json") as json_file:
    card_list = json.load(json_file)


def fill_args(card, level):
    all_param = [
        "block", "absorb", "heal", "tramp", "damage", "self_damage", "crush",
        "revenge", "lich_revenge", "eff_app", "inverse_damage", "on_hand_block",
        "on_hand_absorb", "on_hand_heal", "on_hand_tramp", "on_hand_damage",
        "on_hand_self_damage", "on_hand_crush", "on_hand_revenge",
        "on_hand_lich_revenge", "on_hand_eff_app", "on_hand_inverse_damage"
    ]
    param = [
        "block", "absorb", "heal", "tramp", "damage", "self_damage",
        "crush", "revenge", "lich_revenge", "eff_app",
        "inverse_damage"
    ]

    args = {"level": level}
    for i in card:
        if i in param:
            args[all_param[param.index(i)]] = card[i]
            if i == "eff_app":
                args[all_param[param.index(i)]] = card[i][0]
        if i == "on_hand":
            for k in card[i]:
                if k in param:
                    args[all_param[param.index(k) + 11]] = card[i][k]
                    if k == "eff_app":
                        args[all_param[param.index(k) + 11]] = card[i][k][0]
    return Template(card['description']).safe_substitute(args)


def add_a_card(player_lvl, userid=None):
    if userid != "344292024486330371":
        energy_cost = log_level_gen(
            random.randint(2 ** (max(0, 5 - (player_lvl // 4))),
            2 ** (10 - math.floor(player_lvl / 10)))
        )
        return f"{energy_cost}.{random_card(energy_cost, 'normal')}"
    else:
        return f"{random.randint(3, 10)}.Snowball"


def random_card(energy: int, edition: str) -> str:
    """
    Returns a random card for the enemy AI.
    :param energy: The amount of energy the enemy has, as to not overspend.
    :param edition: The type of card which to choose.
    :return: The name of the card which the enemy is to play.
    """
    cards = card_list["cards"]
    fire = card_list["fire"]
    evil = card_list["evil"]
    electric = card_list["electric"]
    defensive = card_list["defensive"]
    monster = card_list["monster"]

    finished = False
    if edition == "fire":
        for x in fire:
            if not finished and random.randint(1, 2) == 1 and energy >= int(x):
                return random.choice(fire[x])
    elif edition == "evil":
        for x in evil:
            if not finished and random.randint(1, 2) == 1 and energy >= int(x):
                return random.choice(evil[x])
    elif edition == "electric":
        for x in electric:
            if not finished and random.randint(1, 2) == 1 and energy >= int(x):
                return random.choice(electric[x])
    elif edition == "defensive":
        for x in defensive:
            if not finished and random.randint(1, 2) == 1 and energy >= int(x):
                return random.choice(defensive[x])
    elif edition == "monster":
        return random.choice(monster["1"])
    
    for x in cards:
        if not finished and random.randint(1, 4) == 1 and energy >= int(x):
            return random.choice(cards[x])
    if not finished:
        return random.choice(cards["1"])


def order_by_cost(cards, direction):
    cards_by_cost = {}
    for x in cards:
        if cards_dict(x[4], x[3])["cost"] not in cards_by_cost:
            cards_by_cost[cards_dict(x[4], x[3])["cost"]] = []
        cards_by_cost[cards_dict(x[4], x[3])["cost"]].append(x)
    cards = []
    cost_order = list(cards_by_cost.keys())
    if direction == 0:
        cost_order.sort()
    else:
        cost_order.sort(reverse=True)
    for x in cost_order:
        cards += cards_by_cost[x]
    return cards


def order_by_rarity(cards, direction):
    cards_by_rarity = {r: [] for r in ["EX", "L", "E", "R", "C", "M", "NA"]}
    for x in cards:
        cards_by_rarity[cards_dict(x[4], x[3])["rarity"]].append(x)
    cards = []
    rarity_order = list(cards_by_rarity.keys())
    if direction == 0:
        rarity_order.reverse()
    for x in rarity_order:
        cards += cards_by_rarity[x]
    return cards


def rarity_cost(card_name):
    card = cards_dict(1, str(card_name))
    return card["rarity"] + "/" + str(card["cost"])


def price_factor(card_name):
    return {
        r: v + 2 for v, r in enumerate(["R", "E", "L", "EX"])
    }.get(cards_dict(1, card_name)["rarity"], 1)


def log_level_gen(i: int) -> int:
    """
    Spits out a number given an i from 1 to 10.
    Since this function is logarithmic, i has to increase dramatically to go from, say, 5 to 6,
    and even more so from 8 to 9.
    :param i: Any positive number.
    :return: An integer between 1 and 10, inclusive.
    """
    return min(10, max(1, (10 - math.floor(math.log(i - 1) / math.log(2))))) if i > 1 else 10


# =========================== Utilities ===========================
def time_converter(seconds: Union[str, int]) -> str:
    """
    Returns a string representation of the amount of time given in seconds.
    :param seconds: The amount of seconds to convert.
    :return: A string representation of how many days, hours, etc. that is.
    """
    seconds = int(seconds)
    if seconds >= 0:
        days = math.floor(seconds / 86400)
        hours = math.floor((seconds - days * 86400) / 3600)
        minutes = math.floor((seconds - days * 86400 - hours * 3600) / 60)
        seconds = seconds - (days * 86400) - (hours * 3600) - (minutes * 60)
        if days != 0:
            return f"{days}d, {hours}h, {minutes}m, and {seconds}s"
        if hours != 0:
            return f"{hours}h, {minutes}m, and {seconds}s"
        elif minutes != 0:
            return f"{minutes}m, and {seconds}s"
        elif seconds > 0:
            return f"{seconds}s"
        else:
            return "Right Now"
    return "Right Now"


def remain_time():
    dts = dt.datetime.now()
    dts = str(time_converter(((24 - dts.hour - 1) * 60 * 60) + ((60 - dts.minute - 1) * 60) + (60 - dts.second)))
    return dts


def is_registered(author_id):
    dm.cur.execute("select userid from playersinfo")
    registered_users = dm.cur.fetchall()
    for x in registered_users:
        if x[0] == author_id:
            dm.cur.execute(f"select cooldown from playersinfo where userid = {author_id}")
            result = dm.cur.fetchall()
            if result[0][0] == 0:
                sql = "update playersinfo set cooldown = %s where userid = %s"
                value = (0, str(author_id))
                dm.cur.execute(sql, value)
                return True
            else:
                return f"You have to wait {time_converter(result[0][0])} before you can send another command!"

    return f"Send `{prefix}register` to play this bot!"


def author_username(username):
    the_username = str(username)
    username_length = len(the_username) - 5
    return str(the_username[0:username_length])


def userid_converter(username):
    if len(username) > 10:
        if username[2] == "!":
            return username[3: len(username) - 1]
        else:
            return username[2: len(username) - 1]
    return username


def get_user(user, msg: discord.Message):
    
    if user is not None:
        if "@<" not in str(user) and ">" not in str(user):
            author_id = str(user)
        else:
            author_id = userid_converter(str(user))
    else:
        author_id = str(msg.author.id)

    if msg.guild is None:
        return msg.author

    try:
        member = msg.guild.get_member(int(author_id))
        if member is not None:
            return member
    except:
        pass

    for mem in msg.guild.members:
        if mem.display_name.lower().startswith(user.lower()):
            return mem
        elif mem.name.lower().startswith(user.lower()):
            return mem

    return msg.author


# =========================== Backpack functions ===========================
def get_bp_weight(i):  # bp will stand for backpack
    storage = 0
    for x in i:
        if not i[x]["items"] == "x":
            storage += items_dict(x)["weight"] * i[x]["items"]
    return storage


def clear_bp(i):
    inv_delete = []
    for x in i:
        if i[x]["items"] == 0:
            inv_delete.append(x)
    for x in inv_delete:
        del i[x]
    return i


def fulfill_requirement(i, p_inv):
    req_fulfill = True
    req_items_to_take = {}
    pre_message = None
    if len(i) == 4:
        for x in i[3]["req"]:
            if not req_fulfill:
                break
            if x == "item":
                for y in i[3]["req"][x]:
                    if y.lower() in p_inv:
                        if i[3]["req"][x][y][0] <= p_inv[y.lower()]["items"] and req_fulfill:
                            if i[3]["req"][x][y][1] == "taken":
                                req_items_to_take[y.lower()] = i[3]["req"][x][y][0]
                        else:
                            req_fulfill = False
                            break
                    else:
                        req_fulfill = False
                        break
    if req_fulfill:
        for x in req_items_to_take:
            p_inv[x]["items"] -= req_items_to_take[x]
        p_inv = clear_bp(p_inv)
    else:
        pre_message = "You don't have the items needed to do this!"
    return [req_fulfill, p_inv, pre_message]


def chest_storage(level):
    storage = {7: 100, 13: 150, 19: 175, 25: 200, 30: 225, 100: 250}
    for i in storage:
        if level < i:
            return storage[i]


def display_backpack(store: dict, user: discord.User, container: str, padding=None, level=1):
    inventory = ["*" * 30]
    # [[f"{{{'-' * 28}}}"],  ["_" * 30]]   # <-- other possible markers
    capacity = 100 if container == "Backpack" else chest_storage(level)
    if store == {}:
        if padding is None:
            inventory.insert(len(inventory), f"Empty {container}!")
        else:
            inventory.insert(len(inventory), "You lost nothing!")
    else:
        for x in store:
            if store[x]["items"] != "x":
                inventory.insert(len(inventory), f"[{items_dict(x)['rarity']}/{items_dict(x)['weight']}] {x.title()} - {store[x]['items']} ")
            else:
                inventory.insert(len(inventory), f"[{items_dict(x)['rarity']}/{items_dict(x)['weight']}] {x.title()} - ∞ ")

    inventory.insert(len(inventory), "------------------------------")
    inventory.insert(len(inventory), f"{container} Storage used - {get_bp_weight(store)}/{capacity}")
    inventory.insert(len(inventory), "******************************")
    embed = discord.Embed(title=f"Your {container}:", description="```" + "\n".join(inventory) + "```")
    embed.set_thumbnail(url=user.avatar_url)

    if padding is None:
        return embed
    else:
        return "\n".join(inventory[padding[0]: padding[1]])
