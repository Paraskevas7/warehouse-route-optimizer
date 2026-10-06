"""Routing algorithms.

A *route* is a list with the numbers 1..n (the picks) in the order they are visited. The picker starts at the depot
(index 0 of the distance matrix), visits every pick once, and walks back to the depot.
"""
from __future__ import annotations

import random
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .layout import Location

Route = List[int]


def route_cost(d, route: Sequence[int]) -> int:
    """Total walking distance of a route (depot -> picks -> depot)."""
    if not route:
        return 0
    total = d[0][route[0]] + d[route[-1]][0]
    for a, b in zip(route, route[1:]):
        total += d[a][b]
    return int(total)


# ----------------------------------------------------------------- simple heuristics
def random_route(n: int, rng: random.Random) -> Route:
    route = list(range(1, n + 1))
    rng.shuffle(route)
    return route


def nearest_neighbour(d) -> Route:
    """Always walk to the closest pick that is still to do."""
    n = len(d) - 1
    left, cur, route = set(range(1, n + 1)), 0, []
    while left:
        nxt = min(left, key=lambda j: (d[cur][j], j))
        route.append(nxt)
        left.remove(nxt)
        cur = nxt
    return route


def s_shape(picks: Sequence[Location]) -> Route:
    """The classic warehouse rule of thumb: sweep the aisles from left to right, going up one aisle and down the next
    (skipping aisles with nothing to pick). Picks inside an aisle are taken in walking order."""
    by_aisle: Dict[int, List[Tuple[int, int]]] = {}
    for i, p in enumerate(picks, start=1):
        by_aisle.setdefault(p.aisle, []).append((p.access[0], i))
    route: Route = []
    going_up = True  # the depot is at the front (bottom), so the first aisle is walked towards the back (up)
    for aisle in sorted(by_aisle):
        items = sorted(by_aisle[aisle], reverse=going_up)  # bigger row number = nearer the front
        route.extend(i for _, i in items)
        going_up = not going_up
    return route


# ----------------------------------------------------------------- local search
def two_opt(d, route: Route) -> Route:
    """Repeat 'reverse a piece of the route' while it makes the route shorter."""
    full = [0] + list(route)
    m = len(full)
    improved = True
    while improved:
        improved = False
        for i in range(1, m - 1):
            for j in range(i + 1, m):
                a, b, c = full[i - 1], full[i], full[j]
                e = full[j + 1] if j + 1 < m else full[0]
                if d[a][c] + d[b][e] < d[a][b] + d[c][e]:
                    full[i:j + 1] = reversed(full[i:j + 1])
                    improved = True
    return full[1:]


def or_opt(d, route: Route, max_segment: int = 3) -> Route:
    """Repeat 'cut out 1 to 3 picks in a row and put them somewhere better' while it helps."""
    full = [0] + list(route)
    improved = True
    while improved:
        improved = False
        m = len(full)
        for seg in range(1, max_segment + 1):
            for i in range(1, m - seg + 1):
                prev, first, last = full[i - 1], full[i], full[i + seg - 1]
                nxt = full[(i + seg) % m]
                removed = d[prev][first] + d[last][nxt] - d[prev][nxt]
                rest = full[:i] + full[i + seg:]
                piece = full[i:i + seg]
                best_gain, best_k, best_rev = 0, None, False
                for k in range(len(rest)):
                    u, v = rest[k], rest[(k + 1) % len(rest)]
                    for rev in (False, True):
                        p0, p1 = (piece[-1], piece[0]) if rev else (piece[0], piece[-1])
                        added = d[u][p0] + d[p1][v] - d[u][v]
                        if removed - added > best_gain:
                            best_gain, best_k, best_rev = removed - added, k, rev
                if best_k is not None:
                    piece = piece[::-1] if best_rev else piece
                    full = rest[:best_k + 1] + piece + rest[best_k + 1:]
                    improved = True
                    break
            if improved:
                break
    return full[1:]


def local_search(d, route: Route) -> Route:
    """2-opt and or-opt, one after the other, until neither finds an improvement."""
    best = list(route)
    while True:
        cand = or_opt(d, two_opt(d, best))
        if route_cost(d, cand) >= route_cost(d, best):
            return best if route_cost(d, best) <= route_cost(d, cand) else cand
        best = cand


# ----------------------------------------------------------------- genetic algorithm
def order_crossover(p1: Route, p2: Route, rng: random.Random) -> Route:
    """OX: keep a slice of parent 1, fill the rest in the order the picks appear in parent 2."""
    n = len(p1)
    if n < 2:
        return list(p1)
    i, j = sorted(rng.sample(range(n), 2))
    child: List[Optional[int]] = [None] * n
    child[i:j + 1] = p1[i:j + 1]
    taken = set(p1[i:j + 1])
    fill = [g for g in p2 if g not in taken]
    it = iter(fill)
    for k in range(n):
        if child[k] is None:
            child[k] = next(it)
    return child  # type: ignore[return-value]


def mutate(route: Route, rng: random.Random) -> Route:
    r = list(route)
    if len(r) < 2:
        return r
    i, j = sorted(rng.sample(range(len(r)), 2))
    if rng.random() < 0.5:
        r[i], r[j] = r[j], r[i]                  # swap two picks
    else:
        r[i:j + 1] = reversed(r[i:j + 1])        # reverse a piece
    return r


def genetic_algorithm(d, population: int = 100, generations: int = 300, seed: int = 0, mutation_rate: float = 0.25,
                      elite: int = 2, tournament: int = 3, memetic: bool = False,
                      seeds: Sequence[Route] = ()) -> Tuple[Route, List[Tuple[int, Route, int]]]:
    """A genetic algorithm. Returns the best route and a history ``[(generation, best route, cost), ...]``.

    ``seeds`` are routes added to the first population (for example the nearest-neighbour route).
    ``memetic=True`` improves each generation's best route with 2-opt (a 'genetic + local search' hybrid).
    """
    n = len(d) - 1
    rng = random.Random(seed)
    if n <= 2:
        best = nearest_neighbour(d)
        return best, [(0, best, route_cost(d, best))]
    pop: List[Route] = [list(s) for s in seeds][:population]
    while len(pop) < population:
        pop.append(random_route(n, rng))
    cost = lambda r: route_cost(d, r)  # noqa: E731
    history: List[Tuple[int, Route, int]] = []
    best = min(pop, key=cost)
    best_cost = cost(best)
    history.append((0, list(best), best_cost))
    for gen in range(1, generations + 1):
        scored = sorted(pop, key=cost)
        nxt = [list(r) for r in scored[:elite]]
        while len(nxt) < population:
            a = min(rng.sample(pop, tournament), key=cost)
            b = min(rng.sample(pop, tournament), key=cost)
            child = order_crossover(a, b, rng)
            if rng.random() < mutation_rate:
                child = mutate(child, rng)
            nxt.append(child)
        if memetic:
            nxt[0] = two_opt(d, nxt[0])
        pop = nxt
        cand = min(pop, key=cost)
        if cost(cand) < best_cost:
            best, best_cost = list(cand), cost(cand)
        history.append((gen, list(best), best_cost))
    return best, history


# ----------------------------------------------------------------- exact solution
def held_karp(d, max_picks: int = 15) -> Tuple[Route, int]:
    """The optimal route by dynamic programming over subsets. Time grows like 2^n * n^2, so n is capped."""
    n = len(d) - 1
    if n > max_picks:
        raise ValueError(f"held_karp is only for up to {max_picks} picks (got {n})")
    if n == 0:
        return [], 0
    D = np.asarray(d, dtype=np.int64)
    INF = np.iinfo(np.int64).max // 4
    size = 1 << n
    dp = np.full((size, n), INF, dtype=np.int64)
    parent = np.full((size, n), -1, dtype=np.int16)
    for j in range(n):
        dp[1 << j, j] = D[0, j + 1]
    inner = D[1:, 1:]
    for mask in range(1, size):
        row = dp[mask]
        for j in range(n):
            cur = row[j]
            if cur >= INF or not (mask >> j) & 1:
                continue
            cand = cur + inner[j]
            for k in range(n):
                if (mask >> k) & 1:
                    continue
                nm = mask | (1 << k)
                if cand[k] < dp[nm, k]:
                    dp[nm, k] = cand[k]
                    parent[nm, k] = j
    full = size - 1
    ends = dp[full] + D[1:, 0]
    j = int(np.argmin(ends))
    best = int(ends[j])
    route, mask = [], full
    while j != -1:
        route.append(j + 1)
        pj = int(parent[mask, j])
        mask ^= 1 << j
        j = pj
    return route[::-1], best


ALGORITHMS = ("random", "nearest", "s-shape", "nearest+2opt", "genetic", "memetic")


def solve(name: str, d, picks: Sequence[Location], seed: int = 0) -> Route:
    """Run one algorithm by name (see ``ALGORITHMS``; ``optimal`` runs the exact method)."""
    n = len(d) - 1
    if name == "random":
        return random_route(n, random.Random(seed))
    if name == "nearest":
        return nearest_neighbour(d)
    if name == "s-shape":
        return s_shape(picks)
    if name == "nearest+2opt":
        return local_search(d, nearest_neighbour(d))
    if name in ("genetic", "memetic"):
        seeds = [nearest_neighbour(d), s_shape(picks)]
        best, _ = genetic_algorithm(d, seed=seed, memetic=(name == "memetic"), seeds=seeds)
        return best
    if name == "optimal":
        return held_karp(d)[0]
    raise ValueError(f"unknown algorithm: {name}")
