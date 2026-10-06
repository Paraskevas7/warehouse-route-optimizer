"""Regenerates docs/figures/* and results/results.md (takes a minute or two)."""
import numpy as np
from warehouse_routing import Warehouse, random_order, distance_matrix, nearest_neighbour, s_shape, local_search, genetic_algorithm
from warehouse_routing.viz import plot_compare, animate_ga
from warehouse_routing.experiments import compare, format_table

wh = Warehouse(8, 20)
picks = random_order(wh, 30, np.random.default_rng(3))
d = distance_matrix(wh, picks)
ga, hist = genetic_algorithm(d, population=80, generations=250, seed=1,
                             seeds=[nearest_neighbour(d), s_shape(picks)])
plot_compare(wh, picks, d, {"S-shape": s_shape(picks), "Nearest neighbour": nearest_neighbour(d),
                            "Nearest + 2-opt/or-opt": local_search(d, nearest_neighbour(d)), "Genetic": ga},
             "docs/figures/routes.png")
animate_ga(wh, picks, d, hist, "docs/figures/ga.gif")
small = format_table(compare(10, 20, optimal=True))
large = format_table(compare(40, 10, seed=1))
open("results/results.md", "w").write(
    "## 10 picks, 20 random orders (exact optimum known)\n\n```\n" + small +
    "\n```\n\n## 40 picks, 10 random orders\n\n```\n" + large + "\n```\n")
print(small); print(large)
