# Stdlib
from typing import Dict, List, Union

# External Libraries
from intercept import Event
from prompt_toolkit.auto_suggest import Suggestion, AutoSuggestFromHistory


def short_suggestion(func):
    def inner(self, buf, document):
        all_args = document.text.split(" ")
        text = func(self, buf, document)
        if not text:
            return
        if isinstance(text, AltSuggestion):
            text.text = text.text[len(all_args[-1]):]
        return text

    return inner


class AltSuggestion(Suggestion):
    pass


class SuggestPart:
    @staticmethod
    def parse(document):
        a, *b = document.text.split(" ")
        if document.text.endswith(" "):
            b.append("")
        return a, b

    def run_command(self, command: str):
        raise NotImplementedError

    def get_data(self, event: Event):
        raise NotImplementedError

    def get_autocomplete(self, buffer, document) -> Union[AltSuggestion, None]:
        raise NotImplementedError


class AutoSuggestFromLogs(AutoSuggestFromHistory):
    def __init__(self, parts: List[SuggestPart]):
        super().__init__()
        self.parts = parts

    def last_command(self, command: str):
        for part in self.parts:
            part.run_command(command)

    def set_last_items(self, event: Event):
        for part in self.parts:
            part.get_data(event)

    @short_suggestion
    def get_suggestion(self, buffer, document):
        for part in self.parts:
            x = part.get_autocomplete(buffer, document)
            if x is not None:
                return x

        x = super().get_suggestion(buffer, document)
        if x is not None:
            return x

        return x
