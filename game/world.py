"""World geometry: rooms, legal moves between them, maps and the loot each
location holds.  A move is only applied when the target cell is a room, so
every location can only be left through its legal exits."""

from game import party, story

map_base = '\n                    ----------------\n                    |              |__\n                    | upstairs     |__  outside\n                 == |              |\n--------------- ==  ------|   |-----\n|             |==         |   | \n|downstairs   |       ----     ----\n|             |------| bedroom     |\n--  -----------       -------------\n  |  |\n--|  |-------\n| bathroom  |\n-------------\n'

map_outside = "\n              ----------\n              | gram's |           \n              | house  |           \n              |__    __|          ________\n/\\/\\/\\/\\/\\/\\/\\/\\/|  | /\\/\\//\\/\\/ /    /|\\ \\ \n---------------------------------      |   |\n                                      /|\\  |\n---------------------------------  (park)  |   \n/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\___  ___/\n                                     | |\n            (misc houses)                        \n"

# The only cells that exist; anything else is not a place you can be.
ROOMS = {
    (0, 0): "bathroom",
    (0, 1): "downstairs",
    (0, 2): "downstairs",
    (1, 1): "bedroom",
    (1, 2): "upstairs",
    (1, 3): "upstairs",
    (2, 2): "outside",
    (3, 2): "road",
    (4, 2): "gram's house",
    (5, 2): "road",
    (6, 2): "road",
    (7, 2): "road",
    (8, 2): "park",
}

DIRECTIONS = {
    "left": (-1, 0),
    "right": (1, 0),
    "up": (0, 1),
    "down": (0, -1),
}

# Loot that physically lives in each location.  Searching one location can
# never change what another location holds.
LOCATION_LOOT = {
    "bathroom": ["water", "pillow"],
    "downstairs": ["food", "water"],
    "bedroom": ["foam nunchuks", "stick"],
    "upstairs": ["water", "food"],
    "outside": ["stick"],
    "road": ["water"],
    "gram's house": ["food"],
    "park": ["stick"],
}

_BASE_MAP_LOCATIONS = {"bathroom", "downstairs", "bedroom", "upstairs", "outside"}

_DESCRIPTIONS = {
    "bathroom": ["you are in the bathroom"],
    "downstairs": ["you are downstairs"],
    "bedroom": ["you are in the bedroom"],
    "upstairs": ["you are upstairs"],
    "outside": ["you are outside"],
    "road": ["you are on the road to the park"],
    "gram's house": ["you are on the road to the park",
                     "you are infront of gram's house"],
    "park": ["you are in the park"],
}


def location_name(state):
    return ROOMS[(state.pos_x, state.pos_y)]


def can_move(state, direction):
    dx, dy = DIRECTIONS[direction]
    return (state.pos_x + dx, state.pos_y + dy) in ROOMS


def move(state, direction, io):
    """Apply a legal move; reject anything that is not a real exit."""
    dx, dy = DIRECTIONS[direction]
    if can_move(state, direction):
        state.pos_x += dx
        state.pos_y += dy
        return True
    io.say("You can't go that way.")
    return False


def show_map(state, io):
    location = location_name(state)
    if location in _BASE_MAP_LOCATIONS:
        io.say(map_base)
    else:
        io.say(map_outside)
    for line in _DESCRIPTIONS[location]:
        io.say(line)


def trigger_scenes(state, io):
    """Fire each story scene once, when its location is first entered."""
    location = location_name(state)
    if location == "outside" and "outside" not in state.scenes_seen:
        state.scenes_seen.add("outside")
        story.d_outside(io)
    elif location == "park" and "park" not in state.scenes_seen:
        state.scenes_seen.add("park")
        story.d_park(io)
        party.add_member(state, "fred")
