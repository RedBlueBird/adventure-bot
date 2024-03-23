import os
import datetime as dt
from dotenv import load_dotenv

from playhouse.mysql_ext import *

from .fields import *
from .types import *

load_dotenv()

db = MySQLDatabase(
    os.environ["DB_DB"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PW"],
    host=os.environ["DB_HOST"],
    # https://stackoverflow.com/a/55617654/12128483
    ssl={"fake_flag_to_enable_tls": True},
)


class BaseModel(Model):
    class Meta:
        database = db


class Player(BaseModel):
    id = BigIntegerField(primary_key=True)

    level = IntegerField(default=1)
    xp = IntegerField(default=0)
    coins = IntegerField(default=250)
    gems = IntegerField(default=5)
    event_tokens = IntegerField(default=0)
    medals = IntegerField(default=0)
    raid_tickets = IntegerField(default=0)

    card_order = IntegerField(default=1)
    deck = IntegerField(default=1)

    position = CharField(default="enchanted forest")
    show_map = BooleanField(default=True)
    inventory = JSONField(default=dict)
    storage = JSONField(default=dict)

    badges = IntegerField(default=0)

    creation_date = DateField(default=dt.date.today)
    daily_date = DateField(default=lambda: dt.date.today() - dt.timedelta(days=1))
    premium_acc = DateField(default=dt.date.today)
    streak = IntegerField(default=0)

    def has_premium(self):
        return self.premium_acc >= dt.datetime.now().date()


class Deck(BaseModel):
    owner = ForeignKeyField(Player, backref="decks", on_delete="CASCADE")
    slot = IntegerField()

    class Meta:
        indexes = [(("owner", "slot"), True)]


class Card(BaseModel):
    owner = ForeignKeyField(Player, backref="cards", on_delete="CASCADE")
    name = CharField()
    level = IntegerField()


class DeckCard(BaseModel):
    deck = ForeignKeyField(Deck, backref="cards", on_delete="CASCADE")
    card = ForeignKeyField(Card, backref="decks", on_delete="CASCADE")

    class Meta:
        primary_key = CompositeKey("deck", "card")


class Quest(BaseModel):
    player = ForeignKeyField(Player, backref="quests", on_delete="CASCADE")
    quest_type = EnumField(QuestType)
    reward_type = EnumField(RewardType)
    rarity = EnumField(QuestRarity)
    progress = IntegerField(default=0)

    def description(self):
        return [
            "Kill {amount} opponents while adventuring",
            "Accumulate items of weight over {amount} while adventuring",
            "Adventure {amount} meters",
            "Win {amount} non-friendly PvP battles",
            "Earn {amount} coins adventuring",
            "Earn {amount} medals in PvP battles",
            "Merge {amount} pairs of cards",
            "Catch {amount} fish in the public boat",
        ][self.quest_type.value].format(amount=self.requirement())

    def requirement(self):
        return [
            [5, 10, 20, 50],  # Kill mobs
            [10, 20, 40, 60],  # Collect items
            [500, 1000, 2000, 5000],  # Travel a certain distance
            [1, 3, 5, 10],  # Battle
            [100, 200, 500, 1000],  # Collect coins
            [5, 10, 25, 50],  # Collect medals
            [1, 2, 5, 10],  # Merge cards
            [3, 5, 10, 20],  # Catch fish
        ][self.quest_type.value][self.rarity.value]

    def reward(self):
        reward_arr = None
        match self.reward_type:
            case RewardType.COINS:
                reward_arr = [200, 500, 1000, 2500]
            case RewardType.GEMS:
                reward_arr = [0, 1, 2, 4]
        return reward_arr[self.rarity.value]

    def xp_reward(self):
        return [25, 50, 100, 200, 250][self.rarity.value]


class Deal(BaseModel):
    player = ForeignKeyField(Player, backref="deals", on_delete="CASCADE")
    sold = BooleanField(default=False)
    c_name = CharField()
    c_level = IntegerField()
