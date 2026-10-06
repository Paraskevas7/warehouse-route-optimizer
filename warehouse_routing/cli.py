import argparse

import numpy as np

from .algorithms import ALGORITHMS, genetic_algorithm, nearest_neighbour, route_cost, s_shape, solve
from .experiments import compare, format_table
from .layout import Warehouse
from .orders import distance_matrix, random_order


def main(argv=None):
    p = argparse.ArgumentParser(prog="warehouse_routing", description="Warehouse order-picking route optimizer")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("solve", "compare", "animate"):
        s = sub.add_parser(name)
        s.add_argument("--aisles", type=int, default=8)
        s.add_argument("--rows", type=int, default=20)
        s.add_argument("--picks", type=int, default=30)
        s.add_argument("--seed", type=int, default=0)
        if name == "solve":
            s.add_argument("--algorithm", choices=list(ALGORITHMS) + ["optimal"], default="nearest+2opt")
            s.add_argument("--plot", metavar="PNG", help="save a picture of the route")
        if name == "compare":
            s.add_argument("--trials", type=int, default=20)
            s.add_argument("--optimal", action="store_true", help="also compute the exact optimum (<= 15 picks)")
        if name == "animate":
            s.add_argument("--out", default="ga.gif")
    a = p.parse_args(argv)

    if a.cmd == "compare":
        print(format_table(compare(a.picks, a.trials, a.aisles, a.rows, a.seed, optimal=a.optimal)))
        return 0
    wh = Warehouse(a.aisles, a.rows)
    picks = random_order(wh, a.picks, np.random.default_rng(a.seed))
    d = distance_matrix(wh, picks)
    if a.cmd == "solve":
        r = solve(a.algorithm, d, picks, seed=a.seed)
        print(f"{a.algorithm}: {route_cost(d, r)} steps, route {r}")
        if a.plot:
            from .viz import plot_route
            plot_route(wh, picks, r, d, a.plot, a.algorithm)
            print("saved", a.plot)
    else:
        from .viz import animate_ga
        _, hist = genetic_algorithm(d, seed=a.seed, generations=250, population=80)
        animate_ga(wh, picks, d, hist, a.out)
        print("saved", a.out, f"({hist[0][2]} -> {hist[-1][2]} steps)")
    return 0
