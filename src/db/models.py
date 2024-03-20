import os
import datetime as dt

from playhouse.mysql_ext import *

from .fields import *
from .types import *

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
    uid = BigIntegerField(primary_key=True)

    level = IntegerField()
    xp = IntegerField()
    coins = IntegerField()
    gems = IntegerField()
    event_tokens = IntegerField()
    medals = IntegerField()
    raid_tickets = IntegerField()

    deals = CharField()
    quests = CharField()

    card_order = IntegerField()
    deck = IntegerField()

    position = CharField()
    display_map = BooleanField()
    inventory = JSONField()
    storage = JSONField()

    badges = IntegerField()

    creation_date = DateField()
    daily_date = DateField()
    premium_acc = DateField()
    streak = IntegerField()

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
    level = IntegerField()
    progress = IntegerField()
