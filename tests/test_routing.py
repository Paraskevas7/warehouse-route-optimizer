import random
import unittest

import numpy as np

from warehouse_routing import (Warehouse, random_order, distance_matrix, route_cost, nearest_neighbour, s_shape,
                               two_opt, or_opt, local_search, genetic_algorithm, held_karp, solve, ALGORITHMS)
from warehouse_routing.algorithms import order_crossover


def make(n, seed=1, aisles=6, rows=10):
    wh = Warehouse(aisles, rows)
    rng = np.random.default_rng(seed)
    picks = random_order(wh, n, rng)
    return wh, picks, distance_matrix(wh, picks)


class LayoutTests(unittest.TestCase):
    def test_sizes(self):
        wh = Warehouse(4, 5)
        self.assertEqual(len(wh.locations), 2 * 3 * 5)
        self.assertEqual(wh.depot, (6, 0))

    def test_access_cells_walkable(self):
        wh = Warehouse(5, 7)
        for l in wh.locations:
            self.assertTrue(wh.grid[l.access])
            self.assertFalse(wh.grid[l.cell])

    def test_bfs_path_length_matches(self):
        wh = Warehouse(5, 7)
        a, b = wh.depot, wh.locations[10].access
        dist, _ = wh.bfs(a)
        self.assertEqual(len(wh.shortest_path(a, b)) - 1, dist[b])

    def test_invalid(self):
        with self.assertRaises(ValueError):
            Warehouse(1, 5)


class DistanceTests(unittest.TestCase):
    def test_symmetric_zero_diagonal_triangle(self):
        _, _, d = make(8)
        self.assertTrue((d == d.T).all())
        self.assertTrue((np.diag(d) == 0).all())
        n = len(d)
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    self.assertLessEqual(d[i][j], d[i][k] + d[k][j])


class AlgorithmTests(unittest.TestCase):
    def check_perm(self, route, n):
        self.assertEqual(sorted(route), list(range(1, n + 1)))

    def test_all_algorithms_valid(self):
        wh, picks, d = make(12)
        for name in ALGORITHMS:
            self.check_perm(solve(name, d, picks), 12)

    def test_two_opt_never_worse(self):
        for seed in range(5):
            _, picks, d = make(15, seed)
            r = nearest_neighbour(d)
            self.assertLessEqual(route_cost(d, two_opt(d, r)), route_cost(d, r))
            self.check_perm(two_opt(d, r), 15)

    def test_or_opt_never_worse(self):
        _, picks, d = make(15, 3)
        r = list(range(1, 16))
        o = or_opt(d, r)
        self.check_perm(o, 15)
        self.assertLessEqual(route_cost(d, o), route_cost(d, r))

    def test_local_search_never_worse(self):
        _, _, d = make(20, 4)
        r = nearest_neighbour(d)
        self.assertLessEqual(route_cost(d, local_search(d, r)), route_cost(d, r))

    def test_held_karp_optimal_vs_bruteforce(self):
        from itertools import permutations
        _, _, d = make(7, 2)
        best = min(route_cost(d, p) for p in permutations(range(1, 8)))
        route, cost = held_karp(d)
        self.assertEqual(cost, best)
        self.assertEqual(route_cost(d, route), best)

    def test_heuristics_not_better_than_optimal(self):
        for seed in range(4):
            _, picks, d = make(10, seed)
            opt = held_karp(d)[1]
            for name in ALGORITHMS:
                self.assertGreaterEqual(route_cost(d, solve(name, d, picks)), opt)

    def test_held_karp_limit(self):
        _, _, d = make(16)
        with self.assertRaises(ValueError):
            held_karp(d)

    def test_ga_valid_and_monotone(self):
        _, picks, d = make(14)
        best, hist = genetic_algorithm(d, population=30, generations=40, seed=1)
        self.check_perm(best, 14)
        costs = [c for _, _, c in hist]
        self.assertTrue(all(a >= b for a, b in zip(costs, costs[1:])))

    def test_ga_deterministic(self):
        _, _, d = make(12)
        a, _ = genetic_algorithm(d, population=20, generations=20, seed=7)
        b, _ = genetic_algorithm(d, population=20, generations=20, seed=7)
        self.assertEqual(a, b)

    def test_order_crossover_is_permutation(self):
        rng = random.Random(0)
        p1 = list(range(1, 11)); p2 = p1[::-1]
        for _ in range(50):
            self.check_perm(order_crossover(p1, p2, rng), 10)

    def test_s_shape_visits_all(self):
        _, picks, _ = make(25)
        self.check_perm(s_shape(picks), 25)

    def test_tiny_orders(self):
        for n in (1, 2):
            _, picks, d = make(n)
            for name in ALGORITHMS:
                self.check_perm(solve(name, d, picks), n)

    def test_cost_example(self):
        d = [[0, 1, 2], [1, 0, 3], [2, 3, 0]]
        self.assertEqual(route_cost(d, [1, 2]), 1 + 3 + 2)


if __name__ == "__main__":
    unittest.main()
