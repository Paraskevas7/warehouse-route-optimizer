"""Orders (the list of locations a picker has to visit) and the distance matrix between them."""
from __future__ import annotations

from typing import List, Optional, Sequence

import numpy as np

from .layout import Location, Warehouse


def random_order(wh: Warehouse, n_picks: int, rng: np.random.Generator, skew: Optional[float] = None) -> List[Location]:
    """``n_picks`` different locations.

    With ``skew=None`` every shelf slot is equally likely. With ``skew`` between 0 and 1, popular items sit near the
    front: the weight of a slot falls off with its distance from the depot (``skew=0.9`` is a strong ABC-style layout).
    """
    locs = wh.locations
    if not 1 <= n_picks <= len(locs):
        raise ValueError(f"n_picks must be between 1 and {len(locs)}")
    if skew is None:
        p = None
    else:
        if not 0 <= skew < 1:
            raise ValueError("skew must be in [0, 1)")
        dist, _ = wh.bfs(wh.depot)
        d = np.array([dist[l.access] for l in locs], dtype=float)
        w = (1.0 - skew) + skew * (1.0 - d / d.max())
        p = w / w.sum()
    idx = rng.choice(len(locs), size=n_picks, replace=False, p=p)
    return [locs[i] for i in sorted(idx)]


def distance_matrix(wh: Warehouse, picks: Sequence[Location]) -> np.ndarray:
    """Walking distance in steps between the depot (index 0) and every pick (indexes 1..n)."""
    cells = [wh.depot] + [p.access for p in picks]
    d = np.zeros((len(cells), len(cells)), dtype=np.int64)
    for i, src in enumerate(cells):
        dist, _ = wh.bfs(src)
        for j, dst in enumerate(cells):
            d[i, j] = dist[dst]
    return d
