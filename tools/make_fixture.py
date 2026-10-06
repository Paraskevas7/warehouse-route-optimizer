"""Writes test/fixture.json from the Python implementation so the JavaScript port can be checked against it."""
import json
import numpy as np
from warehouse_routing import (Warehouse, random_order, distance_matrix, nearest_neighbour, s_shape, two_opt,
                               local_search, route_cost, held_karp)

cases = []
for seed, (a, r, n) in enumerate([(6, 10, 9), (8, 20, 12), (5, 8, 7), (8, 20, 30)]):
    wh = Warehouse(a, r)
    picks = random_order(wh, n, np.random.default_rng(seed))
    d = distance_matrix(wh, picks)
    nn = nearest_neighbour(d)
    case = dict(aisles=a, rows=r, picks=[p.id for p in picks], matrix=d.tolist(), nearest=nn, s_shape=s_shape(picks),
                two_opt=two_opt(d, nn), two_opt_cost=route_cost(d, two_opt(d, nn)),
                local_search_cost=route_cost(d, local_search(d, nn)))
    if n <= 12:
        case["optimal_cost"] = held_karp(d)[1]
    cases.append(case)
json.dump(cases, open("test/fixture.json", "w"))
print("cases:", len(cases))
