# Stdlib
import asyncio
import re
import sys

# External Libraries
from asyncio import get_event_loop

import anyio
import colorama
from colorama import Fore
from intercept import Client, ChatEvent, Event, MessageEvent, DataFormat
from intercept.events import ErrorEvent, BroadcastEvent
from intercept.utils import converted_color_codes
from prompt_toolkit import ANSI, Application, prompt
from prompt_toolkit.document import Document
from prompt_toolkit.eventloop import use_asyncio_event_loop
from prompt_toolkit.filters import has_focus
from prompt_toolkit.formatted_text import to_formatted_text
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import (Float, HSplit, Layout, VSplit, Window, WindowAlign, BufferControl, FloatContainer,
                                   FormattedTextControl)
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.widgets import Frame, TextArea

from client.alt_buffer import Buffer_, FormatText
from client.autosuggest import AutoSuggestFromLogs
from client.macros import MacroHolder
from client.suggesters import CommandSuggest


class UI(Client):
    def __init__(self, username: str, password: str):
        super().__init__(username, password, handle_data=DataFormat.ANSI)

        self.commands = []

        self.output_buffer = Buffer_()
        self.cursor_pos = 0

        self.chat_buffer = Buffer_()

        self.output = BufferControl(self.output_buffer,
                                    input_processors=[FormatText()],
                                    include_default_input_processors=True)

        self.chat = BufferControl(self.chat_buffer,
                                  input_processors=[FormatText()],
                                  include_default_input_processors=True)

        self.hide_ip = "--hide-ip" in sys.argv

        self.suggest = AutoSuggestFromLogs([
            CommandSuggest(),
        ])

        self.input = TextArea(height=1,
                              prompt=" >> ",
                              multiline=False,
                              wrap_lines=False,
                              accept_handler=self.accept,
                              auto_suggest=self.suggest,
                              dont_extend_width=True)

        self.host_ip = FormattedTextControl(ANSI(""))

        self.chat_float = Float(Frame(Window(self.chat, wrap_lines=True)),
                                right=1, top=0,
                                width=40, height=12,
                                hide_when_covering_content=True)

        self.text = ""
        self.chat_text = ""

        def set_frame_size(fn):
            def inner(*args):
                size = self.app.output.get_size()
                self.chat_float.width = size.columns // 3
                self.chat_float.height = size.rows // 2
                return fn(*args)

            return inner

        self.out_window = Window(self.output, wrap_lines=True)

        kb = KeyBindings()

        @kb.add('c-c')
        @kb.add('c-q')
        def _(_):
            self.app.exit()
            self._loop = False
            self.run_again = False

        @kb.add('c-i', filter=has_focus(self.input))
        def __(_):
            fut = self.suggest.get_suggestion_future(self.input.buffer, self.input.document)
            text = self.input.text

            def set_input(fut_2):
                res = fut_2.result()
                if res is not None:
                    self.input.text = text + res.text
                    self.input.document = Document(self.input.text,
                                                   cursor_position=len(self.input.text))

            fut.add_done_callback(set_input)

        @kb.add(Keys.ScrollUp)
        def sup(_):
            self.output_buffer.cursor_up(1)
            self.out_window._scroll_up()  # pylint: disable=protected-access

        @kb.add(Keys.ScrollDown)
        def sdown(_):
            self.output_buffer.cursor_down(1)
            self.out_window._scroll_down()  # pylint: disable=protected-access

        self.app = Application(
            layout=Layout(
                container=HSplit([
                    Frame(FloatContainer(
                        self.out_window,
                        floats=[
                            self.chat_float
                        ]
                    )),
                    Frame(
                        VSplit(
                            [
                                self.input,
                                Window(self.host_ip, align=WindowAlign.RIGHT, dont_extend_width=True)
                            ]
                        )
                    )
                ]),
                focused_element=self.input,
            ),
            full_screen=True,
            mouse_support=True,
            enable_page_navigation_bindings=True,
            key_bindings=merge_key_bindings([kb]),
            paste_mode=True,
        )

        self.app._on_resize = set_frame_size(self.app._on_resize)  # pylint: disable=protected-access

        self.run_again = True
        self.loop = get_event_loop()
        self._loop = False

        self.own_pass = ""
        self.own_ip = ""
        self.current_ip = ""

        # patch_stdout()

    @classmethod
    def create(cls) -> 'UI':
        user = prompt("Username: ", async_=False)
        pw = prompt("Password: ", is_password=True, async_=False)

        return cls(user, pw)

    def event_chat(self, e: ChatEvent):
        self.set_chat_output(converted_color_codes(e.msg))

    def on_event(self, e: Event):
        # self.set_output(str(e))
        self.suggest.set_last_items(e)
        if isinstance(e, MessageEvent) and not isinstance(e, ChatEvent):
            if isinstance(e, BroadcastEvent):
                self.set_output(f"{Fore.BLUE}[BROADCAST]{Fore.RESET} {converted_color_codes(e.msg)}")
            else:
                self.set_output(converted_color_codes(e.msg))

    def event_error(self, e: ErrorEvent):
        self.err(e.error)

    @staticmethod
    def sanitize(arg: str) -> ANSI:
        return to_formatted_text(ANSI(arg))

    def err(self, message: str):
        self.set_output(f"{Fore.RED}{converted_color_codes(message)}{Fore.RESET}")

    def set_chat_output(self, text: str):
        new_text = (self.chat_text + "\n" + text).strip()
        self.chat_buffer.set_text(new_text)
        self.chat_text = new_text.replace("\t", " ")

    def set_output(self, text: str):
        new_text = (self.text + "\n" + text).strip()
        self.output_buffer.set_text(new_text)
        self.text = new_text.replace("\t", " ")
        self.cursor_pos = len(self.text)

    def clear_chat(self):
        self.chat_buffer.set_text("")
        self.chat_text = ""

    def clear(self):
        self.output_buffer.set_text("")
        self.text = ""

    def accept(self, _):
        if self.input.text.strip():
            self.set_output(f"\n>> {self.input.text}")
            self.commands.append(self.input.text)
            self.suggest.last_command(self.input.text)
            self.input.text = ""

    async def get_host_data(self):
        data = await self.command("pass see -l")
        self.own_pass = data.msg
        sys_info = await self.command('specs -l')
        self.current_ip = self.own_ip = re.search(r"(?P<ip>\d{1,3}(\.\d{1,3}){3,4})", sys_info.msg).group("ip")

    def launch(self):
        colorama.init()
        use_asyncio_event_loop()
        patch_stdout()

        while self.run_again:
            self.run_again = False
            self._loop = True

            self.loop.create_task(self.start())
            try:
                self.loop.run_until_complete(self.app.run_async().to_asyncio_future())
            except KeyboardInterrupt:
                if self.current_ip != self.own_ip:
                    self.loop.run_until_complete(self.command("dc"))

    async def event_ready(self):
        o_text = self.output_buffer.text

        await self.get_host_data()

        text = ((f"{Fore.YELLOW}{self.own_ip} - {self.own_pass}{Fore.RESET} "
                 if self.own_ip == self.current_ip
                 else f"{Fore.YELLOW}{self.current_ip} / {self.own_ip} - {self.own_pass}{Fore.RESET} ")
                if not self.hide_ip else "")
        self.host_ip.text = self.sanitize(text)

        self.clear()

        self.set_output(o_text)

        macros = MacroHolder()

        while self._loop:
            # TODO: Update these when they change
            macros.macros["self"] = self.own_ip
            macros.macros["pass"] = self.own_pass

            while not self.commands:
                await asyncio.sleep(0.1)

            try:
                line = self.commands.pop(0).strip()
                line = macros.parse(line)
                command, *args = line.split()

                if command == "chats":
                    if len(args) == 1 and args[0] == "clear":
                        self.clear_chat()
                    else:
                        await self.command(" ".join([command, *args]))

                elif command == "macro":
                    if args and args[0] in ("add", "remove", "list"):
                        sub = args.pop(0)
                        if sub == "add":
                            if len(args) >= 2:
                                macros += args[0], " ".join(args[1:])
                            else:
                                self.set_output("Usage: macro add <name> <value>")
                        elif sub == "remove":
                            if args:
                                macros -= args[0]
                            else:
                                self.set_output("Usage: macro remove <name>")
                        else:
                            self.set_output("Macros:")
                            for key in sorted(list(macros)):
                                self.set_output(f"${key} -> {macros[key]}")

                    else:
                        self.set_output("Usage: macro [add/remove/list] ...")

                elif command == "clear":
                    self.clear()

                elif command == "quit":
                    self._loop = False
                    self.run_again = False
                    self.stop()
                    self.app.exit()

                else:
                    await self.command(" ".join([command, *args]))

            except Exception as e:  # pylint: disable=broad-except
                self.err(repr(e))
