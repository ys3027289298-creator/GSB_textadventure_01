"""Input/output abstraction so the engine can run on a console or on a
fixed scripted input sequence (used by the tests and bug reproductions)."""


class ConsoleIO:
    def say(self, text=""):
        print(text)

    def ask(self, prompt=""):
        return input(prompt)


class ScriptedIO:
    """Feeds a fixed sequence of answers and records everything printed."""

    def __init__(self, lines=()):
        self._lines = list(lines)
        self.transcript = []

    def say(self, text=""):
        self.transcript.append(str(text) + "\n")

    def ask(self, prompt=""):
        if prompt:
            self.transcript.append(str(prompt))
        if not self._lines:
            raise StopIteration("scripted input exhausted")
        return self._lines.pop(0)

    def text(self):
        return "".join(self.transcript)
