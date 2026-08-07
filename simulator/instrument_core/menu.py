from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass
class MenuWindow:
    first: int
    last: int
    page: int
    pages: int
    has_more_up: bool
    has_more_down: bool


class MenuEngine:
    def __init__(self, rows: int = 12):
        self.rows = max(1, int(rows))
        self.first = 0

    def sync(self, selected: int, count: int) -> MenuWindow:
        if count <= self.rows:
            self.first = 0
        else:
            if selected < self.first:
                self.first = selected
            elif selected >= self.first + self.rows:
                self.first = selected - self.rows + 1
            self.first = max(0, min(self.first, count - self.rows))
        last = min(count, self.first + self.rows)
        pages = max(1, (count + self.rows - 1) // self.rows)
        page = min(pages, self.first // self.rows + 1)
        return MenuWindow(self.first, last, page, pages, self.first > 0, last < count)

    def reset(self) -> None:
        self.first = 0
