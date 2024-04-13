# adventure bot!

it's adventurin' time

## project structure

### `cogs`

this contains the actual logic of the bot, and all of these are loaded in accordingly

you can run `a.help` when the bot is running to see all of the available commands

### `db`

contains the orm and the connection settings

`lock.py` makes sure a player isn't, say, upgrading a card while going on an adventure,
it helps prevent things from going out of sync

### `helpers`

this one has a ton of stuff

* `battle` contains all the classes need to simulate a battle- we're currently
  renovating that with new game mechanics and everything, so it probably won't work for a very long time
* `resources` loads all the resources in with pydantic
* `util` is just a ton of utility functions
* `checks` contains all the checks that are used for commands, like if a player is high enough level or whatever
* `json_loader` just contains some functions that load in json, it saves some lines of code i suppose

### `views`

this one contains all the ui elements

`adventure` is for the adventure part of the game, `battle` is for battling, all the others are general-use
