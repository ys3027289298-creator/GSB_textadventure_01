"""Inventory checks.  `check_items` reports the QUANTITY carried, not just
a yes/no answer, so callers can tell one water bottle from three."""


def check_items(state, item):
    """Return how many copies of `item` the player carries (0 if none)."""
    return state.stuffs.count(item)


def add_item(state, item):
    state.stuffs.append(item)


def remove_item(state, item):
    """Remove one copy of `item`; return False if there was none."""
    if check_items(state, item) > 0:
        state.stuffs.remove(item)
        return True
    return False
