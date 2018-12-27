from typing import Dict, Tuple

try:
    import ujson as json
except ImportError:
    import json


class MacroHolder:
    def __init__(self):
        self.macros: Dict[str, str] = {}
        try:
            self.load()
        except FileNotFoundError:
            pass

    def save(self):
        with open("macros.json", "w") as f:
            json.dump(self.macros, f)

    def load(self):
        with open("macros.json") as f:
            self.macros = json.load(f)

    def __iadd__(self, other: Tuple[str, str]):
        name, value = other
        if name not in self.macros:
            self.macros[name] = value
            self.save()

    def __isub__(self, other: str):
        if other in self.macros:
            del self.macros[other]
            self.save()

    def __getitem__(self, item):
        return self.macros[item]

    def __iter__(self):
        return iter(sorted(self.macros, key=lambda k: -len(self.macros[k])))

    def parse(self, line: str) -> str:
        for name in self:
            line = line.replace(f"${name}", self[name])
        return line
