"""Compare the algorithms on many random orders."""
from __future__ import annotations

import time
from typing import Dict, List

import numpy as np

from .algorithms import ALGORITHMS, held_karp, route_cost, solve
from .layout import Warehouse
from .orders import distance_matrix, random_order


def compare(n_picks: int, trials: int = 20, aisles: int = 8, rows: int = 20, seed: int = 0,
            algorithms=ALGORITHMS, optimal: bool = False) -> Dict[str, Dict[str, float]]:
    """Average cost and run time per algorithm. With ``optimal=True`` also gives the gap to the exact optimum."""
    wh = Warehouse(aisles, rows)
    rng = np.random.default_rng(seed)
    costs: Dict[str, List[int]] = {a: [] for a in algorithms}
    times: Dict[str, List[float]] = {a: [] for a in algorithms}
    opts: List[int] = []
    for t in range(trials):
        picks = random_order(wh, n_picks, rng)
        d = distance_matrix(wh, picks)
        if optimal:
            opts.append(held_karp(d)[1])
        for a in algorithms:
            t0 = time.perf_counter()
            r = solve(a, d, picks, seed=t)
            times[a].append(time.perf_counter() - t0)
            costs[a].append(route_cost(d, r))
    out = {}
    for a in algorithms:
        row = {"mean_cost": float(np.mean(costs[a])), "mean_seconds": float(np.mean(times[a]))}
        if optimal:
            row["gap_pct"] = float(np.mean([(c - o) / o * 100 for c, o in zip(costs[a], opts)]))
        out[a] = row
    if optimal:
        out["optimal"] = {"mean_cost": float(np.mean(opts)), "mean_seconds": float("nan"), "gap_pct": 0.0}
    return out


def format_table(res: Dict[str, Dict[str, float]]) -> str:
    has_gap = any("gap_pct" in r for r in res.values())
    head = f"{'algorithm':<14}{'avg steps':>11}{'avg sec':>10}" + (f"{'gap vs opt':>12}" if has_gap else "")
    lines = [head, "-" * len(head)]
    for a, r in res.items():
        sec = "-" if r["mean_seconds"] != r["mean_seconds"] else f"{r['mean_seconds']:.3f}"
        line = f"{a:<14}{r['mean_cost']:>11.1f}{sec:>10}"
        if has_gap:
            line += f"{r['gap_pct']:>11.1f}%"
        lines.append(line)
    return "\n".join(lines)
