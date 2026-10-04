"""Searching.  Loot belongs to a location: each search removes the found
item from that location's pool, so searches can never produce duplicates
and one location's searches never affect another location."""
from game import items, world

MAX_CARRY = 7

FOUND_MESSAGES = {
    "water": "you found water... in a reusable bottle... so eco friendly",
    "food": "you found food, TASTY!",
    "foam nunchuks": "you found foam nunchuks",
    "stick": "you found a stick",
    "pillow": "you found a pillow",
}


def search(state, io, rng):
    # Determines if you have too much stuff
    if len(state.stuffs) >= MAX_CARRY:
        io.say("You can't carry anything else.  If you want to pick something up, you need to drop something.")
        return None
    location = world.location_name(state)
    pool = state.loot.get(location, [])
    if not pool:
        io.say("You found nothing")
        return None
    index = rng.randint(0, len(pool) - 1)
    item = pool.pop(index)
    items.add_item(state, item)
    io.say(FOUND_MESSAGES[item])
    return item
