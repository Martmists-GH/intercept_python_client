from intercept import Event

from client.autosuggest import SuggestPart, AltSuggestion


class CommandSuggest(SuggestPart):
    def __init__(self):
        self.commands = {
            "cmds": {
                "client": {},
                "filesystem": {},
                "information": {},
                "misc": {},
                "remote": {},
                "software": {},
                "system": {},
                "web": {},
            },
            "chats": {
                "admin": {},
                "create": {},
                "info": {},
                "join": {},
                "leave": {},
                "list": {},
                "send": {},
                "clear": {},
                "*": {
                    "setpass": {},
                    "users": {},
                    "kick": {},
                }
            },
            "clear": {},
            "vol": {},
            "cat": {},
            "ls": {},
            "mkdir": {},
            "rm": {},
            "rmdir": {},
            "colors": {},
            "help": {},
            "man": {
                "breach": {},
                "connect": {},
                "getpw": {},
                "probe": {},
            },
            "sl": {},
            "connect": {},
            "exit": {},
            "disconnect": {},
            "dc": {},
            "slaves": {
                "list": {},
            },
            "antivirus": {},
            "breach": {},
            "getpw": {},
            "malware": {
                "*": {
                    "scrambler": {},
                    "bitminer": {},
                    "slave": {},
                }
            },
            "probe": {},
            "software": {
                "list": {},
                "transfer": {},
            },
            "trace": {},
            "abandon": {
                "--confirm": {},
            },
            "bits": {
                "balance": {},
                "transfer": {},
            },
            "broadcast": {},
            "hardware": {
                "upgrade_cpu": {
                    "confirm": {}
                },
                "upgrade_ram": {
                    "confirm": {}
                },
                "upgrade_ports": {
                    "confirm": {}
                },
            },
            "jobs": {
                "list": {},
                "kill": {},
            },
            "pass": {
                "see": {},
                "reset": {},
            },
            "ports": {
                "-p": {},
            },
            "scan": {},
            "specs": {},
            "web": {
                "the.net": {},
                "list.the.net": {},
                "armwell.ml": {},
                "atom.net": {},
                "ctrl.atom.net": {},
                "blackweb.xyz": {},
                "contracts.blackweb.xyz": {},
                "forum.blackweb.xyz": {
                    "welcome": {},
                    "proav_release": {},
                    "engineers": {},
                    "atom_bounty": {},
                    "security": {},
                    "new_online_game": {},
                    "botnet": {},
                    "tools": {},
                    "elite_clan": {},
                    "server": {},
                },
                "hive.co": {},
                "bank.hive.co": {},
                "loststar.org": {},
                "admin.loststar.org": {},
                "unity.xyz": {},
                "crawler.unity.xyz": {},
                "void.co": {},
                "ravage.void.co": {},
                "pro-av.com": {
                    "confirm": {},
                },
                "hope.xyz": {},
                "ferretuniverse.us": {},
            },
            "macro": {
                "add": {},
                "remove": {},
            },
            "quit": {},
        }

    def run_command(self, command: str):
        pass

    def get_data(self, event: Event):
        pass

    def get_autocomplete(self, _, document):
        args = document.text.strip().split(" ")

        current = self.commands

        if not any(k.startswith(args[0]) for k in self.commands):
            return

        for arg in args:
            if arg in current:
                current = current[arg]
            elif arg and "*" in current:
                current = current["*"]
            else:
                break

        current = {k: v for k, v in current.items() if (not args[-1]) or k.startswith(args[-1])}

        for key in current.keys():
            if key.startswith(args[-1]) and key != args[-1]:
                return AltSuggestion(key)
