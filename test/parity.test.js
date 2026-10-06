// Checks that the JavaScript port gives the same answers as the Python package (fixture made by tools/make_fixture.py).
const test = require('node:test');
const assert = require('node:assert');
const R = require('../docs/routing.js');
const cases = require('./fixture.json');

cases.forEach((c, i) => test(`case ${i}: ${c.aisles} aisles x ${c.rows} rows, ${c.picks.length} picks`, () => {
  const wh = new R.Warehouse(c.aisles, c.rows);
  const picks = c.picks.map((id) => wh.locations[id]);
  const d = R.distanceMatrix(wh, picks);
  assert.deepStrictEqual(d.map((r) => Array.from(r)), c.matrix);
  assert.deepStrictEqual(R.nearestNeighbour(d), c.nearest);
  assert.deepStrictEqual(R.sShape(picks), c.s_shape);
  const tw = R.twoOpt(d, R.nearestNeighbour(d));
  assert.deepStrictEqual(tw, c.two_opt);
  assert.strictEqual(R.routeCost(d, tw), c.two_opt_cost);
  assert.strictEqual(R.routeCost(d, R.localSearch(d, R.nearestNeighbour(d))), c.local_search_cost);
  if (c.optimal_cost !== undefined) assert.strictEqual(R.heldKarp(d).cost, c.optimal_cost);
}));

test('genetic algorithm gives a valid, never-worse route', () => {
  const wh = new R.Warehouse(6, 10), picks = R.randomOrder(wh, 15, R.mulberry32(5));
  const d = R.distanceMatrix(wh, picks), nn = R.nearestNeighbour(d);
  const { route, history } = R.geneticAlgorithm(d, { population: 40, generations: 60, seeds: [nn] });
  assert.deepStrictEqual(route.slice().sort((a, b) => a - b), picks.map((_, i) => i + 1));
  assert.ok(R.routeCost(d, route) <= R.routeCost(d, nn));
  for (let k = 1; k < history.length; k++) assert.ok(history[k].cost <= history[k - 1].cost);
});
