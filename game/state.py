"""Global game state.

INITIALISATION: `new_game()` is the single place where every piece of
global state (inventory, party, position, health, per-location loot, seen
scenes, game-over flag) is created.  It is called by `game.engine.main()`
at the start of each game.

CLEANUP: `reset_game(state)` restores a state object to the initial
values.  `game.engine.main()` calls it in a `finally` block, so no state
leaks between games, and tests can always start from a clean slate.
"""
from dataclasses import dataclass, field

from game.world import LOCATION_LOOT

# The items that the player starts the game with
STARTING_STUFFS = ['ps3 controller', 'pliers', 'foam nunchuks', 'water', 'food']
STARTING_PARTY = ['you']      # People you are travelling with
START_X = 0                   # Your starting position in the x axis
START_Y = 1                   # Your starting position in the y axis
START_HP = 15.0               # Your health


@dataclass
class GameState:
    stuffs: list = field(default_factory=lambda: list(STARTING_STUFFS))
    party: list = field(default_factory=lambda: list(STARTING_PARTY))
    pos_x: int = START_X
    pos_y: int = START_Y
    you_hp: float = START_HP
    loot: dict = field(default_factory=lambda: {
        location: list(items) for location, items in LOCATION_LOOT.items()})
    scenes_seen: set = field(default_factory=set)
    game_over: bool = False


def new_game():
    """Create a fresh, fully initialised game state."""
    return GameState()


def reset_game(state):
    """Clean up: restore `state` to the initial values in place."""
    state.stuffs = list(STARTING_STUFFS)
    state.party = list(STARTING_PARTY)
    state.pos_x = START_X
    state.pos_y = START_Y
    state.you_hp = START_HP
    state.loot = {location: list(items) for location, items in LOCATION_LOOT.items()}
    state.scenes_seen = set()
    state.game_over = False
