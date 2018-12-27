# External Libraries
from prompt_toolkit import ANSI
from prompt_toolkit.application import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.formatted_text import to_formatted_text, fragment_list_to_text
from prompt_toolkit.layout.processors import Processor, Transformation


class FormatText(Processor):
    def apply_transformation(self, transformation_input):
        fragments = to_formatted_text(ANSI(fragment_list_to_text(transformation_input.fragments)))
        return Transformation(fragments)


class Buffer_(Buffer):
    def set_text(self, data):
        self.text = data

        if not get_app().layout.has_focus(self):
            self.cursor_position = len(self.text)
