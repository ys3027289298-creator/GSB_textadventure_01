"""Deterministic regression/reproduction tests for textAdventure.py.

Every test drives the game with a FIXED input sequence and asserts against
exact STATE SNAPSHOTS (position, stuffs, party, hp) instead of relying on
timing or real stdin.  ``random.seed(...)`` makes every branch reproducible.

GLOBAL STATE: WHERE IT IS INITIALIZED AND CLEANED
-------------------------------------------------
All mutable game state is module-level global, initialized exactly once at
import time at the top of textAdventure.py:

    stuffs (L32), party (L33), pos_x (L34), pos_y (L35), you_hp (L36)

There is no cleanup anywhere in the game: "quit" from the main loop merely
ends the loop, ``fight()`` death handling calls ``quit()`` which raises
SystemExit (process termination), and starting ``main()`` again reuses the
stale globals.  Tests therefore reset the state explicitly in
``reset_state()`` (or reload the module in the state-lifecycle test).

The tests below document six defects.  They assert the CURRENT (buggy)
behaviour so the suite is green and can be flipped into expectations after a
fix; the one desired invariant the engine cannot meet today (illegal moves
must be rejected) is marked expectedFailure.
"""

import builtins
import contextlib
import importlib
import io
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importing the module runs its top-level menu and blocks on input(); answer
# with a value that is neither 'start' nor 'how to play' so import completes.
_real_input = builtins.input
builtins.input = lambda *a, **k: "bogus"
import textAdventure as ta  # noqa: E402
builtins.input = _real_input

_real_fight = ta.fight

INITIAL_STUFFS = ["ps3 controller", "pliers", "foam nunchuks", "water", "food"]
INTRO_INPUTS = [""] * 7  # d_intro() calls input() seven times


def reset_state():
    """The cleanup the game never performs; tests must do it manually."""
    ta.stuffs[:] = list(INITIAL_STUFFS)
    ta.party[:] = ["you"]
    ta.pos_x = 0
    ta.pos_y = 1
    ta.you_hp = 15.0


def snapshot():
    """Immutable copy of the whole game state at one point in time."""
    return {
        "pos": (ta.pos_x, ta.pos_y),
        "stuffs": list(ta.stuffs),
        "party": list(ta.party),
        "you_hp": ta.you_hp,
    }


def run_game(commands, seed=0, start_pos=None, stub_fight=True):
    """Run main() with a fixed input sequence; return (stdout, snapshot)."""
    reset_state()
    if start_pos is not None:
        ta.pos_x, ta.pos_y = start_pos
    random.seed(seed)
    if stub_fight:
        ta.fight = lambda: None  # isolate movement/story tests from combat

    # check_pos() fires scene dialogs (which consume input()) as soon as an
    # iteration starts at pos_x == 2 or 8, so pad for the teleport target.
    dialog_pads = 2 if ta.pos_x == 2 else (1 if ta.pos_x == 8 else 0)
    scripted = INTRO_INPUTS + [""] * dialog_pads + list(commands)

    def scripted_input(prompt=""):
        return scripted.pop(0) if scripted else "quit"

    builtins.input = scripted_input
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            ta.main()
    finally:
        builtins.input = _real_input
    return buf.getvalue(), snapshot()


class BugReproductionTests(unittest.TestCase):
    def setUp(self):
        reset_state()
        ta.fight = _real_fight
        ta.__dict__.pop("quit", None)  # restore builtin quit() lookup

    def tearDown(self):
        builtins.input = _real_input
        ta.__dict__.pop("quit", None)

    # -- defect 1: illegal input/moves reach the wrong scene ---------------
    def test_illegal_movement_reaches_off_map_position(self):
        # Moving 'up' from downstairs is never bounded; (0,5) is no location.
        out, snap = run_game(["up", "up", "up", "up", "map"])
        self.assertEqual(snap["pos"], (0, 5))
        self.assertIn("no map", out)

    def test_outside_scene_fires_at_wrong_coordinates(self):
        # check_pos() tests pos_x alone: (2,1) is the bedroom row, not
        # outside, yet the outside scene plays there.
        out, snap = run_game(["right", "right", "", ""])
        self.assertEqual(snap["pos"], (2, 1))
        self.assertIn("There is nobody outside", out)

    def test_map_reports_outside_anywhere_on_column_x2(self):
        # The map command's 'elif pos_x == 2:' ignores pos_y.
        out, snap = run_game(["right", "right", "", "", "map"])
        self.assertEqual(snap["pos"], (2, 1))
        self.assertIn("you are outside", out)

    # -- defect 2: repeated search grants duplicate items -----------------
    def test_repeated_search_appends_duplicate_items(self):
        random.seed(0)
        before = snapshot()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ta.search()
            ta.search()
        after = snapshot()
        self.assertEqual(after["stuffs"], before["stuffs"] + ["water", "water"])
        self.assertEqual(buf.getvalue().count("you found water"), 2)

    def test_search_always_finds_water_dead_branch(self):
        # 'if i == 0 or 3:' is always truthy, so food/weapon/nothing are
        # dead branches; every search at any seed yields water.
        for seed in range(10):
            reset_state()
            random.seed(seed)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                ta.search()
            self.assertEqual(snapshot()["stuffs"][-1], "water", seed)

    # -- defect 3: item checks do not inspect quantity ---------------------
    def test_check_items_cannot_distinguish_quantity(self):
        ta.stuffs[:] = ["water", "water"]
        self.assertEqual(ta.stuffs.count("water"), 2)
        result_with_two = ta.check_items("water")
        ta.stuffs.remove("water")  # e.g. one 'drink'
        self.assertEqual(ta.stuffs.count("water"), 1)
        result_with_one = ta.check_items("water")
        self.assertEqual(result_with_two, result_with_one)  # True == True

    # -- defect 4: party checks stay stale after story state changes -------
    def test_party_check_stale_after_fred_joins_at_park(self):
        # Reach the park: outside dialog (2 inputs) fires at x=2, the park
        # dialog (1 input) fires at x=8.  Narratively Fred joins the party
        # ("lets go"), but party/check_party keep their pre-scene result.
        commands = ["right", "right", "", "",
                    "right", "right", "right", "right", "right", "right", ""]
        out, snap = run_game(commands)
        self.assertIn("END PART I", out)
        self.assertEqual(snap["pos"], (8, 1))
        self.assertEqual(snap["party"], ["you"])
        self.assertFalse(ta.check_party("fred"))

    # -- defect 5: story can continue after a failed fight -----------------
    def test_death_only_stops_story_via_process_exit(self):
        # Today the sole failure mechanism is quit() -> SystemExit: there is
        # no game-over state and fight() returns no outcome to main().
        ta.you_hp = 1.0
        random.seed(0)
        builtins.input = lambda *a, **k: "no"
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stdout(io.StringIO()):
                ta.fight()
        self.assertLessEqual(ta.you_hp, 0)

    def test_story_continues_after_failed_fight(self):
        # When quit() does not terminate the process (SystemExit caught by a
        # wrapper, or quit unavailable such as python -S), fight() keeps
        # looping: the player is told FAILed, then escapes dead, and fight()
        # returns normally with negative hp, so main() would keep running.
        ta.you_hp = 1.0
        random.seed(0)
        replies = iter(["run"] * 60)
        builtins.input = lambda *a, **k: next(replies)
        ta.quit = lambda: None
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ta.fight()  # returns instead of ending the game
        out = buf.getvalue()
        self.assertIn("FAILed", out)
        self.assertIn("you got away", out)
        self.assertLess(out.index("FAILed"), out.index("you got away"))
        self.assertLessEqual(ta.you_hp, 0)

    # -- defect 6: searches pollute other locations ------------------------
    def test_search_result_is_identical_at_every_location(self):
        reset_state()
        ta.pos_x, ta.pos_y = 0, 1
        random.seed(7)
        with contextlib.redirect_stdout(io.StringIO()):
            ta.search()
        at_home = snapshot()

        reset_state()
        ta.pos_x, ta.pos_y = 8, 2
        random.seed(7)
        with contextlib.redirect_stdout(io.StringIO()):
            ta.search()
        at_park = snapshot()

        # search() never reads position: no per-location loot/state exists.
        self.assertEqual(at_home["stuffs"], at_park["stuffs"])

    def test_searching_at_home_blocks_search_at_park(self):
        ta.pos_x, ta.pos_y = 0, 1
        random.seed(0)
        with contextlib.redirect_stdout(io.StringIO()):
            ta.search()
            ta.search()  # carry limit (7) now reached, using global stuffs
        self.assertEqual(len(snapshot()["stuffs"]), 7)

        ta.pos_x, ta.pos_y = 8, 2
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ta.search()
        self.assertIn("can't carry", buf.getvalue())
        self.assertEqual(snapshot()["pos"], (8, 2))


# Locations encoded by the two maps: (x, y)
LEGAL_POSITIONS = {
    (0, 0), (0, 1), (0, 2),          # bathroom, downstairs
    (1, 1), (1, 2), (1, 3),          # bedroom, upstairs
    (2, 2),                           # outside
    (3, 2), (4, 2), (5, 2), (6, 2), (7, 2),  # road to the park
    (8, 2),                           # park
}
DIRECTIONS = {"left": (-1, 0), "right": (1, 0),
              "up": (0, 1), "down": (0, -1)}


class LocationTransitionTests(unittest.TestCase):
    def setUp(self):
        reset_state()
        ta.fight = lambda: None

    def test_legal_transitions_only(self):
        # Every move between adjacent legal coordinates must be accepted and
        # must land exactly on the target.
        for pos in sorted(LEGAL_POSITIONS):
            for direction, delta in sorted(DIRECTIONS.items()):
                target = (pos[0] + delta[0], pos[1] + delta[1])
                if target not in LEGAL_POSITIONS:
                    continue
                with self.subTest(pos=pos, direction=direction):
                    _, snap = run_game([direction], start_pos=pos)
                    self.assertEqual(snap["pos"], target)

    @unittest.expectedFailure
    def test_illegal_transitions_are_rejected(self):
        # Desired invariant: from a legal location, a move whose target is
        # not legal must leave the player at that legal location.  The engine
        # performs no validation (only negative coords are nudged), so this
        # currently fails.
        for pos in sorted(LEGAL_POSITIONS):
            for direction, delta in sorted(DIRECTIONS.items()):
                target = (pos[0] + delta[0], pos[1] + delta[1])
                if target in LEGAL_POSITIONS:
                    continue
                with self.subTest(pos=pos, direction=direction):
                    _, snap = run_game([direction], start_pos=pos)
                    self.assertIn(snap["pos"], LEGAL_POSITIONS)


class GlobalStateLifecycleTests(unittest.TestCase):
    def test_state_is_initialized_at_import_time(self):
        builtins.input = lambda *a, **k: "bogus"
        try:
            importlib.reload(ta)
        finally:
            builtins.input = _real_input
        self.assertEqual(ta.stuffs, INITIAL_STUFFS)
        self.assertEqual(ta.party, ["you"])
        self.assertEqual((ta.pos_x, ta.pos_y), (0, 1))
        self.assertEqual(ta.you_hp, 15.0)

    def test_state_is_never_cleaned_up_after_a_game(self):
        # After main() ends the globals keep their mutated values; nothing
        # resets them for a hypothetical second play-through.
        _, snap = run_game(["right"])
        self.assertEqual(snap["pos"], (1, 1))
        self.assertEqual((ta.pos_x, ta.pos_y), (1, 1))
        reset_state()  # explicit cleanup only exists in the tests
        self.assertEqual((ta.pos_x, ta.pos_y), (0, 1))


if __name__ == "__main__":
    unittest.main()
