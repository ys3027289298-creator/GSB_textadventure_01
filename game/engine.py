"""Main game loop and command dispatch.

State lifecycle: `main()` INITIALISES the global state with
`state = new_game()` and CLEANS IT UP with `reset_game(state)` in a
`finally` block, so every game (and every test) starts from a clean slate.
"""
import random

from game import combat, items, party, search, story, world
from game.io import ConsoleIO
from game.state import new_game, reset_game


def handle_command(state, dev, io, rng):
    """Run one player command.  Returns False when the game should stop."""
    # Quits the game
    if dev == "quit":
        return False
    # For moving around
    elif dev in world.DIRECTIONS:
        world.move(state, dev, io)
    # Tells the player respective x and y positions
    elif dev == 'pos x':
        io.say(state.pos_x)
    elif dev == 'pos y':
        io.say(state.pos_y)
    # Prints a map base on position
    elif dev == "map":
        world.show_map(state, io)
    # Misc commands
    elif dev == "check items":    # Displays items in stuffs
        io.say(state.stuffs)
    elif dev == "health":         # Shows how many health points you have
        io.say(state.you_hp)
    elif dev == "drink":          # You want to drink to inrease hp
        if items.check_items(state, "water"):
            hp_up = rng.randint(2, 5)
            state.you_hp += hp_up
            items.remove_item(state, "water")
            io.say("your hp increased by " + str(hp_up))
        else:
            io.say("you don't have any water... sucks your you, I'll just drink this nice water here.")
    elif dev == "eat":            # You want to eat to inrease hp
        if items.check_items(state, "food"):
            hp_up = rng.randint(4, 7)
            state.you_hp += hp_up
            items.remove_item(state, "food")
            io.say("your hp increased by " + str(hp_up))
        else:
            io.say("you don't have any food...")
    elif dev == "search":         # Search for stuff
        search.search(state, io, rng)
    elif dev == "drop":           # Drops stuff
        io.say(state.stuffs)
        drop_item = io.ask("\nEnter the index of the item you want to drop (use number keys and the first item is index 0)")
        state.stuffs.pop(int(drop_item))
    else:
        io.say("what is this \"" + dev + "\" nonsense")
    return True


def main(io=None, rng=None, state=None):
    io = io or ConsoleIO()
    rng = rng or random
    state = state if state is not None else new_game()
    try:
        story.d_intro(io)

        game = True
        while game and not state.game_over:
            z = rng.randint(0, 3)    # Randomly decides if player fights zombie
            if z == 3:
                outcome = combat.fight(state, io, rng)
                if outcome == combat.LOSE:
                    break
            world.trigger_scenes(state, io)
            dev = io.ask("\nwhat are you going to do\n").lower()
            game = handle_command(state, dev, io, rng)
    finally:
        reset_game(state)
    return state
