"""Tests for the refactored game.

All playthroughs are driven with FIXED input sequences (ScriptedIO) and
scripted RNGs, and verified with state snapshots.  The fixed playthrough
walks every legal exit and every blocked exit, proving each location only
allows legal transitions.
"""
import builtins
import contextlib
import io
import os
import unittest

from game import combat, engine, items, party, search, story, world
from game.io import ScriptedIO
from game.state import new_game, reset_game

HERE = os.path.dirname(os.path.abspath(__file__))
LEGACY = os.path.join(HERE, "..", "legacy", "textAdventure.py")


class MinRng:
    """Every randint call returns its lower bound -> no random fights."""
    def randint(self, a, b):
        return a


class ScriptedRng:
    """Returns a fixed queue of randint results, then `default`."""
    def __init__(self, values=(), default=None):
        self.values = list(values)
        self.default = default

    def randint(self, a, b):
        if self.values:
            return self.values.pop(0)
        return a if self.default is None else self.default


def snapshot(state):
    return (
        tuple(state.stuffs),
        tuple(state.party),
        state.pos_x,
        state.pos_y,
        state.you_hp,
        tuple(sorted(state.scenes_seen)),
        tuple(sorted((loc, tuple(pool)) for loc, pool in state.loot.items())),
        state.game_over,
    )


def step(state, command, script_io, rng=None):
    """One player command followed by the scene check, as in the main loop."""
    keep_going = engine.handle_command(state, command, script_io, rng or MinRng())
    world.trigger_scenes(state, script_io)
    return keep_going


class StateTests(unittest.TestCase):
    def test_initial_state_is_created_in_one_place(self):
        state = new_game()
        self.assertEqual(state.stuffs,
                         ['ps3 controller', 'pliers', 'foam nunchuks', 'water', 'food'])
        self.assertEqual(state.party, ['you'])
        self.assertEqual((state.pos_x, state.pos_y), (0, 1))
        self.assertEqual(state.you_hp, 15.0)
        self.assertFalse(state.game_over)
        self.assertEqual(sorted(state.loot), sorted(world.LOCATION_LOOT))

    def test_cleanup_restores_initial_state(self):
        state = new_game()
        state.stuffs.append("stick")
        party.add_member(state, "fred")
        state.pos_x, state.pos_y, state.you_hp = 8, 2, 1.0
        state.scenes_seen.add("park")
        state.loot["park"].clear()
        state.game_over = True
        reset_game(state)
        self.assertEqual(snapshot(state), snapshot(new_game()))


class MovementTests(unittest.TestCase):
    def test_every_location_only_allows_legal_transitions(self):
        for (x, y), name in sorted(world.ROOMS.items()):
            for direction, (dx, dy) in world.DIRECTIONS.items():
                state = new_game()
                state.pos_x, state.pos_y = x, y
                script = ScriptedIO()
                legal = (x + dx, y + dy) in world.ROOMS
                moved = world.move(state, direction, script)
                if legal:
                    self.assertTrue(
                        moved, f"{name} -> {direction} should be legal")
                    self.assertEqual((state.pos_x, state.pos_y),
                                     (x + dx, y + dy))
                    self.assertNotIn("You can't go that way.", script.text())
                else:
                    self.assertFalse(
                        moved, f"{name} -> {direction} should be blocked")
                    self.assertEqual((state.pos_x, state.pos_y), (x, y))
                    self.assertIn("You can't go that way.", script.text())

    def test_illegal_command_does_not_change_state(self):
        state = new_game()
        script = ScriptedIO()
        before = snapshot(state)
        keep_going = step(state, "fly through walls", script)
        self.assertTrue(keep_going)
        self.assertEqual(snapshot(state), before)
        self.assertIn('what is this "fly through walls" nonsense',
                      script.text())

    def test_fixed_playthrough_snapshots(self):
        # Fixed input sequence: full house walkthrough, every blocked exit,
        # then the road to the park and back.  Blank lines answer the story
        # prompts (2 for d_outside, 1 for d_park).
        commands = [
            "down",            # -> bathroom (0,0)
            "left",            # blocked
            "up",              # -> downstairs (0,1)
            "right",           # -> bedroom (1,1)
            "up",              # -> upstairs (1,2)
            "up",              # -> upstairs (1,3)
            "up",              # blocked
            "down",            # -> upstairs (1,2)
            "right",           # -> outside (2,2): d_outside
            "right", "right", "right", "right", "right", "right",
            # (3,2) road ... (8,2) park: d_park + Fred joins
            "left",            # -> (7,2)
            "right",           # -> (8,2) park again: scene must NOT refire
            "check items", "health", "pos x", "pos y", "map",
            "quit",
        ]
        expected_positions = [
            (0, 0), (0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (1, 3),
            (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2),
            (8, 2), (7, 2), (8, 2), (8, 2), (8, 2), (8, 2), (8, 2),
            (8, 2), (8, 2),
        ]
        state = new_game()
        script = ScriptedIO(["", "", ""])
        snapshots = []
        for command in commands:
            self.assertTrue(step(state, command, script)
                            or command == "quit")
            snapshots.append((state.pos_x, state.pos_y))
        self.assertEqual(snapshots, expected_positions)
        # Scenes fire exactly once.
        text = script.text()
        self.assertEqual(text.count("There is nobody outside"), 1)
        self.assertEqual(text.count("END PART I"), 1)
        self.assertEqual(text.count("You can't go that way."), 2)
        # The story beat updates the party and the check sees the new state.
        self.assertEqual(state.party, ["you", "fred"])
        self.assertTrue(party.check_party(state, "fred"))

    def test_map_descriptions(self):
        cases = {
            (4, 2): (world.map_outside, "you are infront of gram's house"),
            (1, 3): (world.map_base, "you are upstairs"),
            (2, 2): (world.map_base, "you are outside"),
        }
        for (x, y), (map_text, line) in cases.items():
            state = new_game()
            state.pos_x, state.pos_y = x, y
            script = ScriptedIO()
            world.show_map(state, script)
            self.assertIn(map_text, script.text())
            self.assertIn(line, script.text())


class SearchTests(unittest.TestCase):
    def test_search_is_per_location_without_duplicates(self):
        state = new_game()
        state.pos_x, state.pos_y = 0, 0    # bathroom
        script = ScriptedIO()
        self.assertEqual(search.search(state, script, MinRng()), "water")
        self.assertEqual(search.search(state, script, MinRng()), "pillow")
        state.stuffs.pop(0)              # stay under the 7-item carry cap
        self.assertIsNone(search.search(state, script, MinRng()))
        self.assertIn("You found nothing", script.text())
        self.assertEqual(state.stuffs.count("water"), 2)   # starting + found
        self.assertEqual(state.stuffs.count("pillow"), 1)

        # Downstairs loot is untouched by the bathroom searches.
        state.pos_x, state.pos_y = 0, 1
        self.assertEqual(search.search(state, script, MinRng()), "food")
        self.assertEqual(state.loot["downstairs"], ["water"])

    def test_carry_cap_does_not_touch_location_state(self):
        state = new_game()
        state.stuffs.extend(["x", "x"])    # 5 -> 7 items
        before = snapshot(state)
        script = ScriptedIO()
        search.search(state, script, MinRng())
        self.assertIn("You can't carry anything else", script.text())
        self.assertEqual(len(state.stuffs), 7)
        self.assertEqual(snapshot(state), before)


class ItemsAndPartyTests(unittest.TestCase):
    def test_check_items_reports_quantity(self):
        state = new_game()
        self.assertEqual(items.check_items(state, "water"), 1)
        items.add_item(state, "water")
        self.assertEqual(items.check_items(state, "water"), 2)
        items.remove_item(state, "water")
        self.assertEqual(items.check_items(state, "water"), 1)
        self.assertEqual(items.check_items(state, "unicorn"), 0)

    def test_party_changes_are_visible_immediately(self):
        state = new_game()
        self.assertFalse(party.check_party(state, "fred"))
        party.add_member(state, "fred")
        self.assertTrue(party.check_party(state, "fred"))
        reset_game(state)
        self.assertFalse(party.check_party(state, "fred"))

    def test_drink_and_eat_consume_one_copy(self):
        state = new_game()
        script = ScriptedIO()
        step(state, "drink", script)
        self.assertEqual(state.you_hp, 17.0)      # +2 with MinRng
        self.assertEqual(items.check_items(state, "water"), 0)
        step(state, "drink", script)
        self.assertIn("you don't have any water", script.text())
        step(state, "eat", script)
        self.assertEqual(state.you_hp, 21.0)      # +4 with MinRng
        self.assertEqual(items.check_items(state, "food"), 0)
        step(state, "eat", script)
        self.assertIn("you don't have any food...", script.text())


class CombatTests(unittest.TestCase):
    def test_win_returns_win_and_keeps_game_running(self):
        state = new_game()
        rng = ScriptedRng([1] + [5, 4, 3] * 6)
        script = ScriptedIO(["yes", "1"] * 6)
        outcome = combat.fight(state, script, rng)
        self.assertEqual(outcome, combat.WIN)
        self.assertFalse(state.game_over)
        self.assertIn("you defeted the brain sucker", script.text())

    def test_run_away(self):
        state = new_game()
        script = ScriptedIO(["run"])
        outcome = combat.fight(state, script, ScriptedRng([1, 5, 0]))
        self.assertEqual(outcome, combat.RUN)
        self.assertIn("you got away", script.text())
        self.assertFalse(state.game_over)

    def test_loss_sets_game_over(self):
        state = new_game()
        state.you_hp = 2.0
        script = ScriptedIO(["no"])
        outcome = combat.fight(state, script, ScriptedRng([1, 5, 1, 1]))
        self.assertEqual(outcome, combat.LOSE)
        self.assertTrue(state.game_over)
        self.assertIn("FAILed, no banana bread for you", script.text())

    def test_engine_stops_the_story_after_a_loss(self):
        state = new_game()
        state.you_hp = 2.0
        script = ScriptedIO([""] * 7 + ["no"])
        returned = engine.main(script, ScriptedRng([3, 1, 5, 1, 1]), state)
        text = script.text()
        self.assertIn("FAILed, no banana bread for you", text)
        self.assertNotIn("what are you going to do", text)
        # Cleanup runs even after game over.
        self.assertEqual(snapshot(returned), snapshot(new_game()))

    def test_engine_quit_path_resets_state(self):
        state = new_game()
        script = ScriptedIO([""] * 7 + ["quit"])
        returned = engine.main(script, MinRng(), state)
        self.assertEqual(snapshot(returned), snapshot(new_game()))
        self.assertIn("You are in a basement", script.text())
        self.assertNotIn("END PART I", script.text())


class NarrativeFidelityTests(unittest.TestCase):
    """Story strings must be byte-identical to the legacy game."""

    @staticmethod
    def _legacy_namespace(lines):
        src = open(LEGACY, encoding="utf-8").read()
        answers = iter(lines)
        ns = {"__name__": "__legacy_narrative__"}
        original_input = builtins.input
        buf = io.StringIO()
        builtins.input = lambda prompt="": next(answers)
        try:
            with contextlib.redirect_stdout(buf):
                exec(compile(src, LEGACY, "exec"), ns)
        finally:
            builtins.input = original_input
        return ns, buf.getvalue()

    def test_welcome_and_not_understood_unchanged(self):
        _, output = self._legacy_namespace(["nope"])
        self.assertEqual(output,
                         story.WELCOME + "\n" + story.NOT_UNDERSTOOD + "\n")

    def test_how_to_play_unchanged(self):
        _, output = self._legacy_namespace(["how to play", "nope", "nope"])
        self.assertEqual(output,
                         story.WELCOME + "\n" + story.HOW_TO_PLAY + "\n")

    def test_scene_dialog_unchanged(self):
        ns, _ = self._legacy_namespace(["nope"])
        for name, blanks in (("d_intro", 7), ("d_outside", 2), ("d_park", 1)):
            answers = iter([""] * blanks)
            original_input = builtins.input
            builtins.input = lambda prompt="": next(answers)
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    ns[name]()
            finally:
                builtins.input = original_input
            script = ScriptedIO([""] * blanks)
            getattr(story, name)(script)
            self.assertEqual(script.text(), buf.getvalue(), msg=name)

    def test_maps_unchanged(self):
        ns, _ = self._legacy_namespace(["nope"])
        self.assertEqual(world.map_base, ns["map_base"])
        self.assertEqual(world.map_outside, ns["map_outside"])


if __name__ == "__main__":
    unittest.main()
