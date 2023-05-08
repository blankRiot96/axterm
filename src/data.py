from pathlib import Path

from src.shared import Shared


def get_path(loc: str) -> Path:
    path = Path(loc)
    if path.exists():
        return path
    if loc[-1] == "/":
        path.mkdir()
    else:
        path.touch()
    return path


def read_text_file(file_path: Path) -> list[str]:
    return file_path.read_text().splitlines()


def write_text_file(file_path: Path, data: list[str]) -> None:
    with open(file_path, "w") as f:
        f.write("\n".join(data))


def exact_match(command_history, command):
    for c in command_history[::-1]:
        if c.startswith(command):
            return c

    return None


class DataManager:
    DATA_FOLDER = get_path("assets/data/")
    COMMAND_HISTORY_FILE = get_path("assets/data/command-history.txt")
    HISTORY_LIMIT = 50

    def __init__(self) -> None:
        self.shared = Shared()
        self.command_history = read_text_file(self.COMMAND_HISTORY_FILE)
        self.__current_index = len(self.command_history) - 1
        self.current_line = self.command_history[self.__current_index]

    @property
    def current_index(self):
        return self.__current_index

    @current_index.setter
    def current_index(self, val):
        c_len = len(self.command_history)
        if val >= c_len:
            val = 0
        if val < 0:
            val = c_len - 1
        self.__current_index = val

        self.current_line = self.command_history[self.__current_index]

    def cap_history(self):
        c_len = len(self.command_history)
        if c_len > self.HISTORY_LIMIT:
            self.command_history = self.command_history[c_len - self.HISTORY_LIMIT :]

    def on_exit(self):
        self.cap_history()
        write_text_file(self.COMMAND_HISTORY_FILE, self.command_history)
