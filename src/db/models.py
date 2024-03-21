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
    id = BigIntegerField(primary_key=True)

    level = IntegerField(default=1)
    xp = IntegerField(default=0)
    coins = IntegerField(default=250)
    gems = IntegerField(default=5)
    event_tokens = IntegerField(default=0)
    medals = IntegerField(default=0)
    raid_tickets = IntegerField(default=0)

    deals = CharField(default="")
    card_order = IntegerField(default=1)
    deck = IntegerField(default=1)

    position = CharField(default="enchanted forest")
    display_map = BooleanField(default=True)
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
    level = IntegerField()
    progress = IntegerField()
