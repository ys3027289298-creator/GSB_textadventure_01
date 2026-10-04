#!/usr/bin/env python3
"""Reproduce the six known bugs in legacy/textAdventure.py.

Each bug is driven with a FIXED input sequence and a scripted RNG, so the
evidence is deterministic.  The legacy file is executed inside a controlled
namespace: builtins.input is scripted, random.randint is replaced, and stdout
is captured.
"""
import builtins
import contextlib
import io
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEGACY = os.path.join(HERE, "legacy", "textAdventure.py")
SRC = open(LEGACY, encoding="utf-8").read()

INTRO_KEYS = 7  # number of input() prompts inside d_intro()


class ScriptedInput:
    def __init__(self, lines):
        self._lines = list(lines)
        self.calls = 0

    def __call__(self, prompt=""):
        self.calls += 1
        if prompt:
            sys.stdout.write(str(prompt))
        if not self._lines:
            raise StopIteration("scripted input exhausted")
        return self._lines.pop(0)


def run_legacy(lines, randint_fn=None, quit_fn=None, first_input=None):
    """Exec the legacy module with scripted input.

    Returns (namespace, captured_output).  StopIteration from the exhausted
    input script is caught so partial runs still yield evidence.
    """
    script = ScriptedInput(lines if first_input is None else [first_input] + lines)
    original_input = builtins.input
    original_randint = random.randint
    original_quit = builtins.__dict__.get("quit")
    buf = io.StringIO()
    ns = {"__name__": "__legacy_repro__"}
    builtins.input = script
    if randint_fn is not None:
        random.randint = randint_fn
    if quit_fn is not None:
        builtins.quit = quit_fn
    try:
        with contextlib.redirect_stdout(buf):
            try:
                exec(compile(SRC, LEGACY, "exec"), ns)
            except StopIteration:
                pass
    finally:
        builtins.input = original_input
        random.randint = original_randint
        if original_quit is not None:
            builtins.quit = original_quit
        elif "quit" in builtins.__dict__:
            del builtins.quit
    return ns, buf.getvalue(), script


def min_randint(a, b):
    return a


def const_randint(value):
    """Return `value` for every roll except the main-loop zombie check."""
    def fn(a, b):
        if (a, b) == (0, 3):
            return 0
        return value
    return fn


def report(num, title, evidence, check):
    ok = bool(check)
    print("=" * 72)
    print(f"BUG {num}: {title}")
    print("-" * 72)
    print(evidence.rstrip())
    print("-" * 72)
    print("REPRODUCED" if ok else "NOT REPRODUCED")
    print()
    return ok


def main():
    results = []

    # BUG 1: illegal input/illegal moves walk through walls into story scenes.
    lines = ["start"] + [""] * INTRO_KEYS
    lines += ["right", "right", "", ""]          # enter (2,1): outside scene
    lines += ["right"] * 6 + ["", ""]            # walk straight to the park
    lines += ["quit"]
    ns, out, _ = run_legacy(lines, randint_fn=min_randint)
    evidence = (
        "fixed sequence: start, intro, then ONLY 'right' x8 from start (0,1)\n"
        "(path stays on y=1; (2,1)/(8,1) are not rooms). Scenes triggered:\n"
        f"  outside scene present: {'There is nobody outside' in out}\n"
        f"  park scene present   : {'END PART I' in out}\n"
        f"  final pos_x,pos_y    : {ns['pos_x']},{ns['pos_y']} (park should be 8,2)"
    )
    results.append(report(
        1, "illegal input/move enters the wrong scene (no move validation)",
        evidence, "END PART I" in out and "There is nobody outside" in out
        and ns["pos_x"] == 8 and ns["pos_y"] == 1))

    # BUG 2: repeated search always yields water and duplicates stack up.
    lines = ["start"] + [""] * INTRO_KEYS + ["search"] * 3 + ["check items", "quit"]
    ns, out, _ = run_legacy(lines, randint_fn=min_randint)
    forced3_ns, forced3_out, _ = run_legacy(
        ["start"] + [""] * INTRO_KEYS + ["search", "quit"],
        randint_fn=const_randint(3))
    waters = ns["stuffs"].count("water")
    found_lines = out.count("you found water")
    evidence = (
        "fixed sequence: 'search' x3 then 'check items' (3rd search hits the\n"
        "shared 7-item cap, so only 2 searches succeed)\n"
        f"  'you found water' lines : {found_lines}\n"
        f"  water count in inventory: {waters} (started with 1)\n"
        f"  any other loot found?   : {'food, TASTY' in out or 'you found a stick' in out}\n"
        "with search roll forced to i=3, `if i == 0 or 3:` is still truthy:\n"
        f"  'you found water' printed for i==3: {'you found water' in forced3_out}"
    )
    results.append(report(
        2, "repeated search gives duplicate items (and always water)",
        evidence, waters == 3 and found_lines == 2
        and "you found water" in forced3_out))

    # BUG 3: check_items only answers True/False, quantity is invisible.
    ns, out, _ = run_legacy([], randint_fn=min_randint, first_input="nope")
    one = ns["check_items"]("water")
    ns["stuffs"].append("water")
    two = ns["check_items"]("water")
    evidence = (
        "check_items('water') with 1 water : {0!r} ({1})\n"
        "check_items('water') with 2 waters: {2!r} ({3})\n"
        "both answers are identical booleans; the function cannot see counts."
    ).format(one, type(one).__name__, two, type(two).__name__)
    results.append(report(
        3, "check_items does not inspect quantity", evidence,
        one is True and two is True))

    # BUG 4: after the park scene, Fred has joined the story but not `party`.
    ns, out, _ = run_legacy(
        ["start"] + [""] * INTRO_KEYS
        + ["right", "right", "", ""] + ["right"] * 6 + ["", "quit"],
        randint_fn=min_randint)
    in_party = ns["check_party"]("fred")
    evidence = (
        "after d_park() ('lets go'), Fred never gets added to `party`.\n"
        f"  party value          : {ns['party']}\n"
        f"  check_party('fred')  : {in_party}\n"
        "the story state changed but the check function keeps returning the\n"
        "old result because no state transition ever happens."
    )
    results.append(report(
        4, "party check returns stale result after the story changes",
        evidence, ns["party"] == ["you"] and in_party is False))

    # BUG 5: losing a fight does not return any outcome; the loop has no
    # game-over exit and relies entirely on quit() killing the process.
    ns, out, _ = run_legacy([], randint_fn=min_randint, first_input="nope")
    quit_calls = []
    ns["you_hp"] = 1.0
    values = [1, 5, 1, 1]  # num_zomb, player super roll, zombie att, zombie super

    def scripted_randint(a, b):
        return values.pop(0) if values else a

    script = ScriptedInput(["no", "no"])
    original_input = builtins.input
    original_randint = random.randint
    buf = io.StringIO()
    builtins.input = script
    random.randint = scripted_randint
    builtins.quit = lambda *a: quit_calls.append(1)
    try:
        with contextlib.redirect_stdout(buf):
            try:
                ns["fight"]()
            except StopIteration:
                pass
    finally:
        builtins.input = original_input
        random.randint = original_randint
    out = buf.getvalue()
    fail_positions = [i for i in range(len(out)) if out.startswith(
        "FAILed, no banana bread for you", i)]
    prompt_after_fail = ("do you wish to attack" in out[fail_positions[0]:]
                         if fail_positions else False)
    evidence = (
        "you_hp forced to 1.0; player answers 'no'; one zombie hit kills.\n"
        f"  FAIL lines printed   : {len(fail_positions)} (loop never exits on death)\n"
        f"  'do you wish to attack' seen after the first FAIL: {prompt_after_fail}\n"
        f"  quit() calls (process-kill side effect): {len(quit_calls)}\n"
        "fight() has no return value, so main() cannot tell win/lose/flee apart;\n"
        "without the quit() side effect the fight (and the story) continues dead."
    )
    results.append(report(
        5, "story/fight continues after the player loses", evidence,
        len(fail_positions) >= 2 and prompt_after_fail))

    # BUG 6: search uses one global inventory/cap regardless of location.
    lines = ["start"] + [""] * INTRO_KEYS
    lines += ["search", "search"]                    # downstairs: inventory -> 7
    lines += ["right", "right", "", ""] + ["right"] * 6 + [""]  # reach park
    lines += ["search"]                              # search AT the park
    lines += [""]                                    # d_park re-fires (no once-only guard)
    lines += ["quit"]
    ns, out, _ = run_legacy(lines, randint_fn=min_randint)
    blocked = "You can't carry anything else" in out[out.find("END PART I"):]
    evidence = (
        "search x2 while downstairs (fills the shared inventory to 7), then\n"
        "walk to the park and search there.  Park search output:\n"
        f"  blocked by downstairs loot: {blocked}\n"
        "there is one global `stuffs` list and no per-location state, so\n"
        "searching one place changes what happens in every other place."
    )
    results.append(report(
        6, "search in one location pollutes every other location",
        evidence, blocked))

    print("=" * 72)
    print(f"{sum(results)}/6 legacy bugs reproduced against legacy/textAdventure.py")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
