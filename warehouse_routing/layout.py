"""A simple parallel-aisle warehouse on a grid.

Picture (k = 4 aisles, 3 shelf rows). ``|`` is a walkable aisle cell, ``#`` is a shelf cell,
``=`` is the front/back cross aisle, ``D`` is the depot (where every route starts and ends)::

    = = = = = = = = = = =      row 0              (back cross aisle)
    | # # | # # | # # |
    | # # | # # | # # |        shelf rows 1..R
    | # # | # # | # # |
    D = = = = = = = = = =      row R + 1          (front cross aisle)

Shelves come in back-to-back pairs between two aisles. The left shelf of a pair is reached from the aisle
on its left, the right shelf from the aisle on its right. A picker stands in the aisle cell next to the shelf
(the *access cell*) to pick an item.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

Cell = Tuple[int, int]  # (row, column)


@dataclass(frozen=True)
class Location:
    """One shelf slot that can hold an item."""
    id: int
    cell: Cell      # the shelf cell itself
    access: Cell    # the aisle cell the picker stands on
    aisle: int      # index of that aisle, counted from the left


class Warehouse:
    def __init__(self, n_aisles: int = 8, shelf_rows: int = 20):
        if n_aisles < 2:
            raise ValueError("a warehouse needs at least 2 aisles")
        if shelf_rows < 1:
            raise ValueError("a warehouse needs at least 1 shelf row")
        self.n_aisles = n_aisles
        self.shelf_rows = shelf_rows
        self.rows = shelf_rows + 2
        self.cols = 3 * n_aisles - 2
        grid = np.zeros((self.rows, self.cols), dtype=bool)  # True = walkable
        grid[0, :] = True
        grid[-1, :] = True
        for a in range(n_aisles):
            grid[:, 3 * a] = True
        self.grid = grid
        self.depot: Cell = (self.rows - 1, 0)
        self.locations: List[Location] = []
        for block in range(n_aisles - 1):
            left, right = 3 * block + 1, 3 * block + 2
            for r in range(1, shelf_rows + 1):
                self.locations.append(Location(len(self.locations), (r, left), (r, left - 1), block))
                self.locations.append(Location(len(self.locations), (r, right), (r, right + 1), block + 1))

    # ----- shortest paths on the grid (breadth-first search) -----
    def neighbours(self, cell: Cell):
        r, c = cell
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nr, nc]:
                yield (nr, nc)

    def bfs(self, source: Cell) -> Tuple[np.ndarray, Dict[Cell, Cell]]:
        """Distances (in steps) from ``source`` to every walkable cell, and the parent of each cell."""
        dist = np.full(self.grid.shape, -1, dtype=np.int32)
        dist[source] = 0
        parent: Dict[Cell, Cell] = {}
        queue = deque([source])
        while queue:
            cur = queue.popleft()
            for nxt in self.neighbours(cur):
                if dist[nxt] < 0:
                    dist[nxt] = dist[cur] + 1
                    parent[nxt] = cur
                    queue.append(nxt)
        return dist, parent

    def shortest_path(self, a: Cell, b: Cell) -> List[Cell]:
        """A shortest walkable path from ``a`` to ``b`` (both included)."""
        _, parent = self.bfs(a)
        path = [b]
        while path[-1] != a:
            path.append(parent[path[-1]])
        return path[::-1]
