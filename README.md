TextAdventure
=============

A text adventure game made to remember how to program (also because text adventures are cool).

THE STORY
You play as a lowly nerd who must get out of the basement because you are 
really hungry.  Little do you know that 3 months have past by while you were 
playing Skyrim and surviving off old pizza and red bull.  In those three 
months a lot has changed and in fact your dog is now a zombie, also, so is your 
neigbour and most other people.  You must meeet a friend and together  
escape to an anti-zombie base.

GAME FIGHTING MECHANICS
Each of the characters have an attack, defense and health meter.  The attack value of the attacker is divided by the defense value of victim.  The product of this  is what is subtracted from the health meter of the victim.  There is also a probability for a "super attack" which increases the players attack value by a factor. Also, there is a probability of the zombie hitting the player.  Further, fighting is  turn based.  Note that at any one time you may fight several enemies.

DEVELOPMENT
===========
The game logic lives in the `game` package; `textAdventure.py` is only the
entry point.  All narrative text is unchanged from the original game.

    game/state.py    game-wide state (GameState).  Global state is
                     INITIALISED in `new_game()` and CLEANED UP in
                     `reset_game(state)`, which `game/engine.py:main()`
                     calls in a `finally` block at the end of every game.
    game/world.py    rooms, legal moves between them, maps, per-location loot
    game/items.py    inventory checks (quantity-aware `check_items`)
    game/party.py    party membership checks
    game/search.py   searching (per-location loot pools)
    game/combat.py   fighting; returns "win"/"lose"/"run" to the engine
    game/story.py    story dialog (text byte-identical to the original)
    game/engine.py   main loop and command dispatch
    game/io.py       console I/O plus scripted I/O for tests

Tests (fixed input sequences + state snapshots):

    python3 -m unittest discover -s tests

Bug reproductions against the preserved original (`legacy/textAdventure.py`):

    python3 reproduce_bugs.py
